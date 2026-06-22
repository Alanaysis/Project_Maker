"""
Data Parallel Training
=======================

Data Parallelism is the most common parallelism strategy for distributed training.

Core Idea:
    - Split the DATA across GPUs (each GPU sees different mini-batch)
    - Each GPU has a FULL COPY of the model
    - Each GPU computes gradients independently
    - Gradients are synchronized via AllReduce
    - All GPUs apply the same update

Training Loop:
    for each batch:
        1. Shard data: split batch into N chunks (one per GPU)
        2. Forward pass: each GPU computes loss on its chunk
        3. Backward pass: each GPU computes gradients
        4. AllReduce: sum/average gradients across GPUs
        5. Update: each GPU applies the same gradient update

Why Data Parallelism?
    - Linear speedup: N GPUs -> ~N times faster
    - Simple to implement
    - Works well when model fits in single GPU memory
    - Communication only at gradient sync step

Limitations:
    - Model must fit in single GPU memory
    - Communication overhead increases with model size
    - Batch size per GPU affects convergence

Key Implementation Details:
    - Gradient accumulation for large batches
    - Overlapping computation with communication
    - Learning rate scaling (linear scaling rule)
"""

from typing import List, Optional, Callable, Tuple, Dict, Any
from .tensor import GPUTensor, Device, get_device
from .communicator import Communicator, SimulationCommunicator, create_communicator
from .allreduce import AllReduce, RingAllReduce, create_allreduce
import numpy as np
import logging
import time

logger = logging.getLogger(__name__)


class SimpleLayer:
    """
    A simple fully-connected layer for demonstration.

    This simulates a neural network layer with:
    - Forward: y = x @ W + b
    - Backward: dW = x.T @ dy, db = sum(dy), dx = dy @ W.T

    In a real framework, this would be part of an autograd system.
    """

    def __init__(self, in_features: int, out_features: int, device: Optional[Device] = None):
        self.device = device
        # Xavier initialization
        scale = np.sqrt(2.0 / (in_features + out_features))
        self.weight = GPUTensor(
            np.random.randn(in_features, out_features).astype(np.float32) * scale,
            device,
        )
        self.bias = GPUTensor(np.zeros(out_features, dtype=np.float32), device)

        # Gradient storage
        self.weight_grad: Optional[GPUTensor] = None
        self.bias_grad: Optional[GPUTensor] = None

        # Cache for backward pass
        self._input: Optional[GPUTensor] = None

    def forward(self, x: GPUTensor) -> GPUTensor:
        """Forward pass: y = x @ W + b"""
        self._input = x
        output = x @ self.weight
        # Add bias (broadcast)
        output._data = output._data + self.bias._data
        return output

    def backward(self, grad_output: GPUTensor) -> GPUTensor:
        """
        Backward pass: compute gradients.

        Args:
            grad_output: Gradient of loss w.r.t. output

        Returns:
            Gradient of loss w.r.t. input
        """
        # dW = x.T @ grad_output
        self.weight_grad = GPUTensor(
            self._input._data.T @ grad_output._data,
            self.device,
        )
        # db = sum(grad_output, axis=0)
        self.bias_grad = GPUTensor(
            grad_output._data.sum(axis=0),
            self.device,
        )
        # dx = grad_output @ W.T
        grad_input = GPUTensor(
            grad_output._data @ self.weight._data.T,
            self.device,
        )
        return grad_input

    def get_params_and_grads(self) -> List[Tuple[GPUTensor, Optional[GPUTensor]]]:
        """Get parameters and their gradients."""
        return [
            (self.weight, self.weight_grad),
            (self.bias, self.bias_grad),
        ]

    def zero_grad(self):
        """Clear gradients."""
        self.weight_grad = None
        self.bias_grad = None


class SimpleModel:
    """
    A simple multi-layer model for demonstration.

    Architecture: Input -> Linear -> ReLU -> Linear -> Output
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int,
        output_dim: int,
        device: Optional[Device] = None,
    ):
        self.layer1 = SimpleLayer(input_dim, hidden_dim, device)
        self.layer2 = SimpleLayer(hidden_dim, output_dim, device)
        self.layers = [self.layer1, self.layer2]
        self.device = device

    def forward(self, x: GPUTensor) -> GPUTensor:
        """Forward pass through the network."""
        h = self.layer1.forward(x)
        # ReLU activation
        h._data = np.maximum(0, h._data)
        output = self.layer2.forward(h)
        return output

    def backward(self, grad_output: GPUTensor):
        """Backward pass through the network."""
        grad = self.layer2.backward(grad_output)
        # ReLU backward
        grad._data = grad._data * (self.layer1._input._data > 0).astype(np.float32)
        self.layer1.backward(grad)

    def get_params_and_grads(self) -> List[Tuple[GPUTensor, Optional[GPUTensor]]]:
        """Get all parameters and gradients."""
        params = []
        for layer in self.layers:
            params.extend(layer.get_params_and_grads())
        return params

    def zero_grad(self):
        """Clear all gradients."""
        for layer in self.layers:
            layer.zero_grad()


class DataParallelTrainer:
    """
    Data Parallel Trainer using AllReduce for gradient synchronization.

    This implements the standard data parallel training loop:
    1. Each GPU gets a shard of the data
    2. Each GPU forward/backward on its shard
    3. AllReduce gradients across GPUs
    4. Each GPU applies the same update

    Architecture:
        Data Shard 0 -> GPU 0 -> Model Copy 0 -> Grads 0 --+
        Data Shard 1 -> GPU 1 -> Model Copy 1 -> Grads 1 --+-> AllReduce -> Avg Grad
        Data Shard 2 -> GPU 2 -> Model Copy 2 -> Grads 2 --+     |
        Data Shard 3 -> GPU 3 -> Model Copy 3 -> Grads 3 --+     |
                                                                  v
                                                         Update All Models
    """

    def __init__(
        self,
        model_fn: Callable[[Optional[Device]], SimpleModel],
        world_size: int,
        learning_rate: float = 0.01,
        backend: str = "simulation",
        allreduce_algo: str = "ring",
    ):
        """
        Args:
            model_fn: Function that creates a model on a given device
            world_size: Number of GPUs
            learning_rate: Learning rate for SGD
            backend: Communication backend ('simulation' or 'nccl')
            allreduce_algo: AllReduce algorithm ('naive', 'ring', 'tree')
        """
        self.world_size = world_size
        self.learning_rate = learning_rate
        self.backend = backend
        self.allreduce_algo = allreduce_algo

        # Create communicators (one per GPU, using simulation)
        self.communicators: List[Communicator] = []
        for rank in range(world_size):
            comm = create_communicator(world_size, rank, backend)
            self.communicators.append(comm)

        # Create model copies on each GPU
        self.models: List[SimpleModel] = []
        for rank in range(world_size):
            device = get_device(rank)
            model = model_fn(device)
            self.models.append(model)

        # AllReduce algorithm
        self.allreduce = create_allreduce(allreduce_algo)

        # Training statistics
        self.stats = {
            "total_time": 0.0,
            "comm_time": 0.0,
            "compute_time": 0.0,
            "steps": 0,
            "losses": [],
        }

        logger.info(
            f"DataParallelTrainer initialized: {world_size} GPUs, "
            f"backend={backend}, allreduce={allreduce_algo}"
        )

    def _shard_data(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        Shard data across GPUs.

        Splits the batch into equal chunks, one per GPU.
        If the batch size is not divisible by world_size,
        the last shard gets the extra samples.
        """
        n_samples = X.shape[0]
        shard_size = n_samples // self.world_size
        shards = []

        for rank in range(self.world_size):
            start = rank * shard_size
            if rank == self.world_size - 1:
                end = n_samples  # Last shard gets remainder
            else:
                end = start + shard_size
            shards.append((X[start:end], y[start:end]))

        return shards

    def _compute_loss_and_grad(
        self,
        model: SimpleModel,
        X: np.ndarray,
        y: np.ndarray,
    ) -> float:
        """
        Compute loss and gradients for one shard.

        Loss = 0.5 * mean((pred - y)^2)  (MSE loss)
        """
        # Forward pass
        x_tensor = GPUTensor(X, model.device)
        pred = model.forward(x_tensor)

        # Compute MSE loss
        diff = pred._data - y
        loss = 0.5 * np.mean(diff ** 2)

        # Backward pass (gradient of MSE w.r.t. output)
        grad_output = GPUTensor(diff / X.shape[0], model.device)
        model.backward(grad_output)

        return loss

    def _sync_gradients(self) -> None:
        """
        Synchronize gradients across all GPUs using AllReduce.

        For each parameter:
        1. Gather gradients from all GPUs
        2. Average them via AllReduce
        3. Replace local gradients with averaged gradients
        """
        sync_start = time.perf_counter()

        # Get params and grads from all models
        all_params_grads = [model.get_params_and_grads() for model in self.models]

        # For each parameter, AllReduce the gradient
        num_params = len(all_params_grads[0])
        for param_idx in range(num_params):
            # Collect gradients from all GPUs
            grads = []
            for rank in range(self.world_size):
                _, grad = all_params_grads[rank][param_idx]
                if grad is None:
                    grad = GPUTensor.zeros(
                        all_params_grads[rank][param_idx][0].shape,
                        get_device(rank),
                    )
                grads.append(grad)

            # AllReduce (average gradients)
            reduced_grads = self.allreduce.reduce(grads, op="mean")

            # Replace gradients on each model
            for rank in range(self.world_size):
                model = self.models[rank]
                layer_idx = param_idx // 2
                is_bias = param_idx % 2
                if is_bias:
                    model.layers[layer_idx].bias_grad = reduced_grads[rank]
                else:
                    model.layers[layer_idx].weight_grad = reduced_grads[rank]

        sync_elapsed = time.perf_counter() - sync_start
        self.stats["comm_time"] += sync_elapsed

    def _update_parameters(self):
        """
        Apply SGD update to all models using synchronized gradients.

        For each parameter: param = param - lr * grad

        Key Point: All models get the SAME update because gradients were averaged.
        """
        for model in self.models:
            for param, grad in model.get_params_and_grads():
                if grad is not None:
                    param._data -= self.learning_rate * grad._data

    def train_step(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> float:
        """
        Execute one training step (forward + backward + sync + update).

        Args:
            X: Input data (full batch)
            y: Target data (full batch)

        Returns:
            Average loss across all GPUs
        """
        step_start = time.perf_counter()

        # 1. Zero gradients
        for model in self.models:
            model.zero_grad()

        # 2. Shard data across GPUs
        shards = self._shard_data(X, y)

        # 3. Forward + Backward on each GPU
        losses = []
        for rank in range(self.world_size):
            X_shard, y_shard = shards[rank]
            loss = self._compute_loss_and_grad(self.models[rank], X_shard, y_shard)
            losses.append(loss)

        compute_elapsed = time.perf_counter() - step_start
        self.stats["compute_time"] += compute_elapsed

        # 4. Synchronize gradients (AllReduce)
        self._sync_gradients()

        # 5. Update parameters
        self._update_parameters()

        # Record statistics
        avg_loss = np.mean(losses)
        step_elapsed = time.perf_counter() - step_start
        self.stats["total_time"] += step_elapsed
        self.stats["steps"] += 1
        self.stats["losses"].append(avg_loss)

        return avg_loss

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        epochs: int = 10,
        batch_size: int = 32,
        verbose: bool = True,
    ) -> Dict[str, Any]:
        """
        Train the model for multiple epochs.

        Args:
            X: Training data
            y: Training labels
            epochs: Number of epochs
            batch_size: Mini-batch size
            verbose: Print progress

        Returns:
            Training statistics
        """
        n_samples = X.shape[0]

        for epoch in range(epochs):
            # Shuffle data
            indices = np.random.permutation(n_samples)
            X_shuffled = X[indices]
            y_shuffled = y[indices]

            epoch_losses = []
            for i in range(0, n_samples, batch_size):
                X_batch = X_shuffled[i:i + batch_size]
                y_batch = y_shuffled[i:i + batch_size]
                loss = self.train_step(X_batch, y_batch)
                epoch_losses.append(loss)

            avg_epoch_loss = np.mean(epoch_losses)
            if verbose:
                logger.info(
                    f"Epoch {epoch + 1}/{epochs}, "
                    f"Loss: {avg_epoch_loss:.6f}, "
                    f"Time: {self.stats['total_time']:.3f}s"
                )

        return self.stats

    def get_stats(self) -> Dict[str, Any]:
        """Get training statistics."""
        return {
            **self.stats,
            "comm_percentage": (
                self.stats["comm_time"] / self.stats["total_time"] * 100
                if self.stats["total_time"] > 0 else 0
            ),
        }

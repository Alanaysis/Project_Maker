"""
Model Parallel Training
========================

Model Parallelism splits the MODEL across GPUs, unlike data parallelism
which splits the data.

Core Idea:
    - Different layers/parts of the model live on different GPUs
    - Data flows through GPUs sequentially (pipeline)
    - Each GPU only computes its portion of the model

Two Types:
    1. Tensor Parallelism: Split individual layers across GPUs
    2. Pipeline Parallelism: Split model into stages, process micro-batches

Pipeline Parallelism (focus of this module):
    Stage 0 (GPU 0): Layers 0-1
    Stage 1 (GPU 1): Layers 2-3
    Stage 2 (GPU 2): Layers 4-5
    Stage 3 (GPU 3): Layers 6-7

    Forward: Input -> GPU0 -> GPU1 -> GPU2 -> GPU3 -> Output
    Backward: GradOutput -> GPU3 -> GPU2 -> GPU1 -> GPU0 -> GradInput

Key Challenge: Pipeline bubbles (GPUs waiting for data)
Solution: Micro-batching (split batch into micro-batches)

Comparison with Data Parallelism:
    Data Parallelism:
        + Linear speedup
        + Simple implementation
        - Model must fit in one GPU
        - Communication: gradients (large)

    Model Parallelism:
        + Can handle very large models
        + Less gradient communication
        - Pipeline bubbles reduce efficiency
        - More complex implementation
"""

from typing import List, Optional, Callable, Tuple, Dict, Any
from .tensor import GPUTensor, Device, get_device
from .communicator import Communicator, SimulationCommunicator, create_communicator
from .allreduce import create_allreduce
import numpy as np
import logging
import time

logger = logging.getLogger(__name__)


class PipelineStage:
    """
    A pipeline stage that contains one or more layers.

    Each stage lives on a specific GPU and processes its portion of the model.
    """

    def __init__(
        self,
        stage_id: int,
        layers: List,
        device: Device,
    ):
        self.stage_id = stage_id
        self.layers = layers
        self.device = device

        # Buffers for forward/backward
        self._input_buffer: List[GPUTensor] = []
        self._output_buffer: List[GPUTensor] = []
        self._grad_input_buffer: List[GPUTensor] = []
        self._grad_output_buffer: List[GPUTensor] = []

    def forward(self, x: GPUTensor) -> GPUTensor:
        """Forward pass through this stage."""
        self._input_buffer.append(x)
        h = x
        for layer in self.layers:
            h = layer.forward(h)
        self._output_buffer.append(h)
        return h

    def backward(self, grad_output: GPUTensor) -> GPUTensor:
        """Backward pass through this stage."""
        self._grad_output_buffer.append(grad_output)
        grad = grad_output
        for layer in reversed(self.layers):
            grad = layer.backward(grad)
        self._grad_input_buffer.append(grad)
        return grad

    def get_params_and_grads(self):
        """Get all parameters and gradients in this stage."""
        params = []
        for layer in self.layers:
            params.extend(layer.get_params_and_grads())
        return params

    def zero_grad(self):
        """Clear all gradients."""
        for layer in self.layers:
            layer.zero_grad()


class ModelParallelTrainer:
    """
    Model Parallel Trainer using Pipeline Parallelism.

    Splits the model into stages, each on a different GPU.
    Uses micro-batching to reduce pipeline bubbles.

    Pipeline Schedule (GPipe-style):
        Time:  t0    t1    t2    t3    t4    t5    t6    t7
        GPU 0: F0    F1    F2    F3    B3    B2    B1    B0
        GPU 1:       F0    F1    F2    F3    B3    B2    B1
        GPU 2:             F0    F1    F2    F3    B3    B2
        GPU 3:                   F0    F1    F2    F3    B3

        F = Forward micro-batch, B = Backward micro-batch
        Numbers indicate micro-batch index

    Key Implementation Detail:
        - Micro-batches are processed sequentially through the pipeline
        - Forward for all micro-batches, then backward for all micro-batches
        - This is the GPipe schedule (simple but has bubble overhead)
    """

    def __init__(
        self,
        model_fn: Callable[[int, Device], List],  # (stage_id, device) -> layers
        num_stages: int,
        learning_rate: float = 0.01,
        num_micro_batches: int = 4,
        backend: str = "simulation",
    ):
        """
        Args:
            model_fn: Function that creates layers for a given stage
            num_stages: Number of pipeline stages (= number of GPUs)
            learning_rate: Learning rate for SGD
            num_micro_batches: Number of micro-batches per mini-batch
            backend: Communication backend
        """
        self.num_stages = num_stages
        self.learning_rate = learning_rate
        self.num_micro_batches = num_micro_batches

        # Create pipeline stages
        self.stages: List[PipelineStage] = []
        for stage_id in range(num_stages):
            device = get_device(stage_id)
            layers = model_fn(stage_id, device)
            stage = PipelineStage(stage_id, layers, device)
            self.stages.append(stage)

        # Create communicator for inter-stage data transfer
        self.comm = create_communicator(num_stages, 0, backend)

        # Training statistics
        self.stats = {
            "total_time": 0.0,
            "forward_time": 0.0,
            "backward_time": 0.0,
            "steps": 0,
            "losses": [],
            "bubble_ratio": 0.0,
        }

        logger.info(
            f"ModelParallelTrainer initialized: {num_stages} stages, "
            f"micro_batches={num_micro_batches}"
        )

    def _split_micro_batches(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> List[Tuple[np.ndarray, np.ndarray]]:
        """Split data into micro-batches."""
        n_samples = X.shape[0]
        micro_size = max(1, n_samples // self.num_micro_batches)
        micro_batches = []

        for i in range(self.num_micro_batches):
            start = i * micro_size
            end = min((i + 1) * micro_size, n_samples) if i < self.num_micro_batches - 1 else n_samples
            if start < n_samples:
                micro_batches.append((X[start:end], y[start:end]))

        return micro_batches

    def _pipeline_forward(
        self,
        micro_batches: List[Tuple[np.ndarray, np.ndarray]],
    ) -> List[GPUTensor]:
        """
        Execute forward pass through the pipeline.

        For each micro-batch, send it through all stages sequentially.
        This is the simple GPipe schedule.
        """
        forward_start = time.perf_counter()
        outputs = []

        for mb_idx, (X_mb, y_mb) in enumerate(micro_batches):
            # Start with input on first stage
            h = GPUTensor(X_mb, self.stages[0].device)

            # Pass through each stage
            for stage in self.stages:
                h = stage.forward(h)

            outputs.append(h)

        self.stats["forward_time"] += time.perf_counter() - forward_start
        return outputs

    def _pipeline_backward(
        self,
        outputs: List[GPUTensor],
        micro_batches: List[Tuple[np.ndarray, np.ndarray]],
    ):
        """
        Execute backward pass through the pipeline (reverse order).

        For each micro-batch in reverse, compute gradients.
        """
        backward_start = time.perf_counter()

        for mb_idx in range(len(micro_batches) - 1, -1, -1):
            output = outputs[mb_idx]
            _, y_mb = micro_batches[mb_idx]

            # Compute loss gradient (MSE)
            diff = output._data - y_mb
            grad = GPUTensor(diff / y_mb.shape[0], output.device)

            # Backward through stages in reverse
            for stage in reversed(self.stages):
                grad = stage.backward(grad)

        self.stats["backward_time"] += time.perf_counter() - backward_start

    def _accumulate_and_sync_gradients(self):
        """
        Accumulate gradients across micro-batches and synchronize.

        In pipeline parallelism, we need to:
        1. Accumulate gradients from all micro-batches
        2. AllReduce across stages (for shared parameters)
        3. Apply updates
        """
        # Accumulate gradients for each stage
        for stage in self.stages:
            params_grads = stage.get_params_and_grads()
            for param, grad in params_grads:
                if grad is not None:
                    # Accumulated gradient is already in the grad tensor
                    # In real pipeline parallelism, we'd average over micro-batches
                    pass

    def _update_parameters(self):
        """Apply SGD update to all stages."""
        for stage in self.stages:
            for param, grad in stage.get_params_and_grads():
                if grad is not None:
                    param._data -= self.learning_rate * grad._data

    def train_step(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> float:
        """
        Execute one training step with pipeline parallelism.

        Args:
            X: Input data
            y: Target data

        Returns:
            Loss value
        """
        step_start = time.perf_counter()

        # Zero gradients
        for stage in self.stages:
            stage.zero_grad()

        # Split into micro-batches
        micro_batches = self._split_micro_batches(X, y)

        # Pipeline forward
        outputs = self._pipeline_forward(micro_batches)

        # Compute loss
        losses = []
        for mb_idx, (_, y_mb) in enumerate(micro_batches):
            diff = outputs[mb_idx]._data - y_mb
            loss = 0.5 * np.mean(diff ** 2)
            losses.append(loss)

        avg_loss = np.mean(losses)

        # Pipeline backward
        self._pipeline_backward(outputs, micro_batches)

        # Update parameters
        self._update_parameters()

        # Record statistics
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
        """Train the model for multiple epochs."""
        n_samples = X.shape[0]

        for epoch in range(epochs):
            indices = np.random.permutation(n_samples)
            X_shuffled = X[indices]
            y_shuffled = y[indices]

            epoch_losses = []
            for i in range(0, n_samples, batch_size):
                X_batch = X_shuffled[i:i + batch_size]
                y_batch = y_shuffled[i:i + batch_size]
                loss = self.train_step(X_batch, y_batch)
                epoch_losses.append(loss)

            avg_loss = np.mean(epoch_losses)
            if verbose:
                logger.info(
                    f"Epoch {epoch + 1}/{epochs}, Loss: {avg_loss:.6f}"
                )

        return self.stats

    def get_stats(self) -> Dict[str, Any]:
        """Get training statistics."""
        return self.stats

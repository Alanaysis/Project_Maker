# Development Manual

## 1. Environment Setup

### System Requirements

- OS: Windows / macOS / Linux
- Python: 3.8+
- Dependencies: NumPy, pytest

### Installation Steps

```bash
# 1. Navigate to project
cd projects/multi-gpu-computing

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install numpy pytest

# 4. Verify installation
python -c "from src.core import DataParallelTrainer; print('Installation successful')"
```

## 2. Project Structure

```
multi-gpu-computing/
├── README.md                        # Project overview
├── LEARNING_NOTES.md                # Learning notes template
├── docs/                            # Documentation
│   ├── 01-RESEARCH.md              # Market research
│   ├── 02-REQUIREMENTS.md          # Requirements analysis
│   ├── 03-DESIGN.md                # Technical design
│   ├── 04-PRODUCT.md               # Product thinking
│   └── 05-DEVELOPMENT.md           # This file
├── src/                             # Source code
│   ├── __init__.py
│   ├── core/                        # Core modules
│   │   ├── __init__.py
│   │   ├── tensor.py               # GPU tensor abstraction
│   │   ├── communicator.py         # Communication layer
│   │   ├── allreduce.py            # AllReduce algorithms
│   │   ├── data_parallel.py        # Data parallel trainer
│   │   └── model_parallel.py       # Model parallel trainer
│   └── utils/                       # Utilities
│       ├── __init__.py
│       ├── logger.py               # Logging
│       └── benchmark.py            # Benchmarking
├── tests/                           # Unit tests
│   ├── __init__.py
│   ├── test_tensor.py
│   ├── test_allreduce.py
│   ├── test_communicator.py
│   └── test_data_parallel.py
└── examples/                        # Usage examples
    ├── basic_training.py
    ├── allreduce_comparison.py
    └── benchmark.py
```

## 3. Core Module Analysis

### Module 1: GPUTensor (`src/core/tensor.py`)

**Responsibility**: GPU tensor abstraction

**Key Design**:
```python
class GPUTensor:
    """
    Wraps numpy array with device tracking and arithmetic operations.

    In simulation mode, data stays in numpy.
    In production mode, this would wrap CUDA device memory.
    """
    _data: np.ndarray      # Actual data
    device: Device         # Which GPU
    requires_grad: bool    # Track gradients
```

**Understanding Points**:
- Device tracking is crucial for distributed computing
- Arithmetic operators enable natural tensor math
- Memory tracking helps understand GPU memory usage

### Module 2: Communicator (`src/core/communicator.py`)

**Responsibility**: Inter-GPU communication abstraction

**Key Design**:
```python
class Communicator(ABC):
    """Abstract interface for GPU communication."""

    @abstractmethod
    def allreduce(self, tensor, op="sum") -> tensor:
        """The most important collective operation."""
        pass

class SimulationCommunicator(Communicator):
    """CPU simulation of NCCL operations."""
    # Uses numpy to simulate GPU-to-GPU communication
```

**Understanding Points**:
- Communicator abstracts away the communication backend
- Simulation allows learning without GPU hardware
- Same interface could wrap real NCCL calls

### Module 3: AllReduce (`src/core/allreduce.py`)

**Responsibility**: Gradient synchronization algorithms

**Key Design**:
```python
class RingAllReduce(AllReduce):
    """
    Bandwidth-optimal AllReduce used by NCCL.

    Two phases:
    1. ScatterReduce: Each GPU reduces one chunk
    2. AllGather: Distribute reduced chunks
    """
```

**Understanding Points**:
- Ring AllReduce is THE algorithm for distributed training
- Two phases: ScatterReduce + AllGather
- Total data moved: 2*(n-1)/n * message_size

### Module 4: DataParallelTrainer (`src/core/data_parallel.py`)

**Responsibility**: Data parallel training loop

**Key Design**:
```python
class DataParallelTrainer:
    def train_step(self, X, y):
        # 1. Shard data across GPUs
        # 2. Forward + backward on each GPU
        # 3. AllReduce gradients
        # 4. Update parameters (same on all GPUs)
```

**Understanding Points**:
- All models get the same gradient via AllReduce
- This ensures all models stay synchronized
- Linear speedup with number of GPUs

## 4. Key Challenges

### Challenge 1: Ring AllReduce Implementation

**Problem**: Understanding the two-phase algorithm

**Solution**:
1. Phase 1 (ScatterReduce): n-1 steps, each GPU reduces one chunk
2. Phase 2 (AllGather): n-1 steps, distribute reduced chunks

**Key Code** (`src/core/allreduce.py:RingAllReduce.reduce`):
```python
# Phase 1: ScatterReduce
for step in range(n - 1):
    for rank in range(n):
        send_chunk_idx = (rank + step) % n
        recv_chunk_idx = (rank + step - 1) % n
        # Reduce received chunk with local chunk

# Phase 2: AllGather
for step in range(n - 1):
    for rank in range(n):
        send_chunk_idx = (rank + step + 1) % n
        recv_chunk_idx = (rank + step) % n
        # Copy received chunk
```

**Learning Points**:
- Why two phases? (ScatterReduce makes each chunk complete, AllGather distributes)
- Why ring topology? (All links used at full bandwidth simultaneously)
- Data movement formula: 2*(n-1)/n * message_size

### Challenge 2: Gradient Synchronization Correctness

**Problem**: Ensuring all models have the same parameters after update

**Solution**:
1. AllReduce averages gradients across all GPUs
2. All GPUs apply the same averaged gradient
3. Result: all models have identical parameters

**Key Code** (`src/core/data_parallel.py:_sync_gradients`):
```python
def _sync_gradients(self):
    for param_idx in range(num_params):
        # Collect gradients from all GPUs
        grads = [model_grad[param_idx] for model in self.models]

        # AllReduce (average)
        reduced_grads = self.allreduce.reduce(grads, op="mean")

        # Replace gradients on each model
        for rank, grad in enumerate(reduced_grads):
            self.models[rank].set_grad(param_idx, grad)
```

**Learning Points**:
- "mean" operation ensures gradient averaging
- All models get the same update
- This is the core correctness guarantee of data parallelism

### Challenge 3: Pipeline Parallelism Bubbles

**Problem**: GPUs waiting for data in pipeline parallelism

**Solution**: Micro-batching
- Split mini-batch into K micro-batches
- Process micro-batches through pipeline
- Reduces bubble ratio from (n-1)/n to (n-1)/(n+K-1)

**Learning Points**:
- Trade-off: more micro-batches = less bubbles, but more overhead
- GPipe vs PipeDream: different scheduling strategies
- Real-world: 1F1B schedule overlaps forward and backward

## 5. Debugging Tips

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Models not synchronized | AllReduce not applied | Check gradient sync step |
| Loss not decreasing | Learning rate too high/lower | Adjust learning rate |
| Shape mismatch | Data sharding error | Check shard boundaries |
| Import errors | Path not set | Add project root to sys.path |

### Debugging Methods

1. **Print gradients**:
```python
for param, grad in model.get_params_and_grads():
    print(f"param shape: {param.shape}, grad: {grad.data if grad else None}")
```

2. **Verify AllReduce**:
```python
# Compare naive and ring implementations
naive_result = NaiveAllReduce().reduce(tensors)
ring_result = RingAllReduce().reduce(tensors)
assert np.allclose(naive_result[0].data, ring_result[0].data)
```

3. **Check synchronization**:
```python
# After training step, all models should be identical
for rank in range(1, world_size):
    for p0, pr in zip(models[0].params, models[rank].params):
        assert np.allclose(p0.data, pr.data)
```

## 6. Performance Optimization

### Already Optimized

1. **Ring AllReduce**: Bandwidth-optimal algorithm
2. **Numpy operations**: Vectorized tensor math
3. **Minimal copies**: In-place operations where possible

### Optimization Directions

1. **Overlap compute and communication**: Start AllReduce while computing next layer's gradients
2. **Gradient compression**: Reduce communication volume with quantization
3. **Mixed precision**: Use FP16 for gradients, FP32 for accumulation

## 7. Extension Guide

### Adding a New AllReduce Algorithm

1. Create class inheriting from `AllReduce`:
```python
class MyAllReduce(AllReduce):
    def get_name(self):
        return "MyAllReduce"

    def reduce(self, tensors, op="sum"):
        # Your implementation
        pass
```

2. Register in factory:
```python
# In allreduce.py
_allreduce_algorithms["my_algo"] = MyAllReduce
```

3. Add tests:
```python
def test_my_allreduce():
    algo = MyAllReduce()
    result = algo.reduce([t1, t2], op="sum")
    # Verify correctness
```

### Adding a New Communication Backend

1. Create class inheriting from `Communicator`
2. Implement all abstract methods
3. Register in `create_communicator()` factory

### Adding a New Parallelism Strategy

1. Create new trainer class
2. Use existing Communicator and AllReduce
3. Implement the training loop
4. Add tests and examples

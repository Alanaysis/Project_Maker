# Technical Design Document

## 1. Architecture Overview

### System Architecture

```
+--------------------------------------------------+
|                  User Layer                       |
|  examples/basic_training.py                      |
|  examples/allreduce_comparison.py                |
+--------------------------------------------------+
                      |
+--------------------------------------------------+
|              Training Layer                       |
|  DataParallelTrainer  |  ModelParallelTrainer    |
|  - Data sharding      |  - Pipeline stages       |
|  - Gradient sync      |  - Micro-batching        |
|  - Parameter update   |  - Stage communication   |
+--------------------------------------------------+
                      |
+--------------------------------------------------+
|           Communication Layer                     |
|  Communicator (abstract)                         |
|  |- SimulationCommunicator (numpy)               |
|  |- NCCLCommunicator (CUDA)                      |
|                                                   |
|  AllReduce (abstract)                            |
|  |- NaiveAllReduce                               |
|  |- RingAllReduce                                |
|  |- TreeAllReduce                                |
+--------------------------------------------------+
                      |
+--------------------------------------------------+
|              Tensor Layer                         |
|  GPUTensor (numpy backend)                       |
|  - Device management                             |
|  - Arithmetic operations                         |
|  - Memory tracking                               |
+--------------------------------------------------+
```

### Module Responsibilities

| Module | Responsibility | Files |
|--------|---------------|-------|
| Tensor Layer | GPU tensor abstraction | `src/core/tensor.py` |
| Communication Layer | Inter-GPU communication | `src/core/communicator.py` |
| AllReduce | Gradient synchronization algorithms | `src/core/allreduce.py` |
| Training Layer | Training loop management | `src/core/data_parallel.py`, `model_parallel.py` |
| Utilities | Logging and benchmarking | `src/utils/` |

## 2. Core Flows

### Data Parallel Training Flow

```
1. Initialize
   - Create N model copies (one per GPU)
   - Create communicator for N GPUs

2. For each epoch:
   3. Shuffle data
   4. For each mini-batch:
      5. Shard data into N chunks
      6. For each GPU (parallel):
         a. Forward pass on local data shard
         b. Compute loss
         c. Backward pass (compute gradients)
      7. AllReduce gradients:
         a. Each GPU has its local gradients
         b. AllReduce averages gradients across GPUs
         c. All GPUs now have the same averaged gradient
      8. Update parameters:
         a. Each GPU: param = param - lr * grad
         b. Since grads are same, all models stay synchronized
```

### Ring AllReduce Flow (Phase 1: ScatterReduce)

```
For n=4 GPUs, each with 4 chunks:

Initial state:
  GPU0: [A0, A1, A2, A3]
  GPU1: [B0, B1, B2, B3]
  GPU2: [C0, C1, C2, C3]
  GPU3: [D0, D1, D2, D3]

Step 1: Each GPU sends chunk[i] to GPU[i+1]
  GPU0 sends A0 -> GPU1, receives D3 from GPU3
  GPU1 sends B1 -> GPU2, receives A0 from GPU0
  GPU2 sends C2 -> GPU3, receives B1 from GPU1
  GPU3 sends D3 -> GPU0, receives C2 from GPU2

  GPU0: [A0+D3, A1, A2, A3]
  GPU1: [B0, B1+A0, B2, B3]
  ...

After n-1 steps:
  GPU0: [A0+D3+C2+B1, A1, A2, A3]  <- chunk 0 fully reduced
  GPU1: [B0, B1+A0+D3+C2, B2, B3]  <- chunk 1 fully reduced
  GPU2: [C0, C1, C2+B1+A0+D3, C3]  <- chunk 2 fully reduced
  GPU3: [D0, D1, D2, D3+C2+B1+A0]  <- chunk 3 fully reduced
```

### Ring AllReduce Flow (Phase 2: AllGather)

```
After ScatterReduce, each GPU has one fully reduced chunk.
AllGather distributes all reduced chunks to all GPUs.

After n-1 AllGather steps:
  GPU0: [sum_A, sum_B, sum_C, sum_D]  <- all chunks reduced
  GPU1: [sum_A, sum_B, sum_C, sum_D]
  GPU2: [sum_A, sum_B, sum_C, sum_D]
  GPU3: [sum_A, sum_B, sum_C, sum_D]
```

## 3. Data Design

### GPUTensor

```python
class GPUTensor:
    """
    GPU tensor abstraction.

    Attributes:
        _data: np.ndarray          # Actual data (numpy for simulation)
        device: Device             # Which GPU this tensor lives on
        requires_grad: bool        # Whether to track gradients
        grad: Optional[GPUTensor]  # Accumulated gradient

    Key Operations:
        +, -, *, /, @             # Arithmetic
        sum(), mean()             # Reduction
        to(device)                # Device transfer
        zero_(), fill_()          # In-place operations
    """
```

### Device

```python
class Device:
    """
    Compute device representation.

    Attributes:
        device_id: int      # GPU index (-1 for CPU)
        device_type: str    # 'cuda' or 'cpu'
    """
```

### Communicator Interface

```python
class Communicator(ABC):
    """
    Abstract communication interface.

    Methods:
        init()                          # Initialize backend
        allreduce(tensor, op) -> tensor # AllReduce operation
        broadcast(tensor, root)         # Broadcast operation
        allgather(tensor) -> list       # AllGather operation
        reducescatter(tensor) -> tensor # ReduceScatter operation
    """
```

### AllReduce Interface

```python
class AllReduce(ABC):
    """
    Abstract AllReduce algorithm interface.

    Methods:
        reduce(tensors, op) -> list  # Perform AllReduce
        get_name() -> str            # Algorithm name
    """
```

## 4. Interface Design

### DataParallelTrainer API

```python
class DataParallelTrainer:
    def __init__(
        self,
        model_fn: Callable[[Device], SimpleModel],  # Model factory
        world_size: int,                             # Number of GPUs
        learning_rate: float = 0.01,                 # SGD learning rate
        backend: str = "simulation",                 # Communication backend
        allreduce_algo: str = "ring",               # AllReduce algorithm
    )

    def train_step(
        self,
        X: np.ndarray,  # Input batch
        y: np.ndarray,  # Target batch
    ) -> float          # Returns loss

    def train(
        self,
        X: np.ndarray,           # Training data
        y: np.ndarray,           # Training labels
        epochs: int = 10,        # Number of epochs
        batch_size: int = 32,    # Mini-batch size
        verbose: bool = True,    # Print progress
    ) -> Dict[str, Any]         # Returns statistics

    def get_stats(self) -> Dict[str, Any]
```

### AllReduce API

```python
# Create an AllReduce instance
allreduce = create_allreduce("ring")  # or "naive", "tree"

# Perform AllReduce
tensors = [tensor_gpu0, tensor_gpu1, tensor_gpu2, tensor_gpu3]
results = allreduce.reduce(tensors, op="sum")  # or "mean", "max", "min"

# Compare algorithms
results = compare_allreduce_algorithms(tensors, op="sum")
```

## 5. Technical Decisions

### Decision 1: Simulation vs Real CUDA

**Options**:
| Aspect | Option A: Simulation | Option B: Real CUDA |
|--------|---------------------|-------------------|
| Hardware required | None | NVIDIA GPU |
| Learning value | High (focus on logic) | Medium (CUDA complexity) |
| Portability | Any machine | GPU machines only |
| Accuracy | Exact same logic | Real performance |

**Choice**: Simulation (Option A)

**Reason**:
1. Learning goal is understanding algorithms, not CUDA programming
2. No GPU hardware barrier for learners
3. Same core logic, just different backend

### Decision 2: AllReduce Algorithm

**Options**:
| Aspect | Naive | Ring | Tree |
|--------|-------|------|------|
| Bandwidth optimal | No | Yes | No |
| Latency optimal | No | No | Yes |
| Complexity | Low | Medium | Medium |
| Used by NCCL | No | Yes | Partially |

**Choice**: Implement all three for comparison

**Reason**:
1. Understanding trade-offs is key learning objective
2. Ring is the most important (used by NCCL)
3. Comparison reveals why Ring wins for large messages

### Decision 3: Python vs C++

**Options**:
| Aspect | Python | C++ |
|--------|--------|-----|
| Readability | High | Low |
| Performance | Low | High |
| Learning curve | Low | High |
| Ecosystem | NumPy, pytest | CUDA, NCCL |

**Choice**: Python with NumPy

**Reason**:
1. Learning focus, not production performance
2. NumPy provides sufficient tensor operations
3. Much faster to develop and iterate

## 6. Extensibility Design

### Extension Points

1. **New AllReduce Algorithm**:
   - Subclass `AllReduce` ABC
   - Implement `reduce()` method
   - Register in `create_allreduce()` factory

2. **New Communication Backend**:
   - Subclass `Communicator` ABC
   - Implement all collective operations
   - Register in `create_communicator()` factory

3. **New Parallelism Strategy**:
   - Create new trainer class
   - Use existing Communicator and AllReduce
   - Implement training loop

### How to Add a New AllReduce Algorithm

```python
class CustomAllReduce(AllReduce):
    def get_name(self) -> str:
        return "CustomAllReduce"

    def reduce(self, tensors, op="sum"):
        # Your algorithm here
        pass

# Register it
from src.core.allreduce import _allreduce_registry
_allreduce_registry["custom"] = CustomAllReduce
```

## 7. Performance Characteristics

### Communication Complexity

| Algorithm | Time Complexity | Bandwidth | Latency |
|-----------|----------------|-----------|---------|
| Naive | O(n * M) | Not optimal | O(n) |
| Ring | O(2*(n-1)/n * M) | Optimal | O(n) |
| Tree | O(log(n) * M) | Not optimal | O(log(n)) |

Where: n = number of GPUs, M = message size

### Memory Usage

Each GPU needs:
- Model parameters: P bytes
- Gradients: P bytes
- Optimizer states: 2P bytes (for Adam)
- Activations: depends on batch size and model

Total per GPU: ~4P + activations

### Scaling Efficiency

Ideal: speedup = N (linear)
Reality: speedup = N / (1 + overhead)

Where overhead = communication_time / compute_time

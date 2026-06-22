# Multi-GPU Parallel Computing Framework

## Learning Objectives

Through this project, you will master:
- [ ] Understanding data parallelism and model parallelism
- [ ] NCCL communication patterns (AllReduce, Broadcast, AllGather)
- [ ] Gradient synchronization and aggregation techniques
- [ ] Ring AllReduce algorithm (bandwidth-optimal)
- [ ] Pipeline parallelism for large models
- [ ] Performance benchmarking for distributed systems

## Tech Stack

| Technology | Purpose | Learning Difficulty | Official Docs |
|------------|---------|-------------------|---------------|
| Python 3.8+ | Primary language | Medium | [Python](https://docs.python.org/3/) |
| NumPy | Tensor operations (simulation) | Low | [NumPy](https://numpy.org/doc/) |
| CUDA | GPU programming | High | [CUDA](https://docs.nvidia.com/cuda/) |
| NCCL | Multi-GPU communication | High | [NCCL](https://docs.nvidia.com/deeplearning/nccl/) |

## Key Concepts

### Core Training Loop

```
Data Sharding -> Multi-GPU Compute -> Gradient Sync -> Parameter Update
     |                |                    |                |
  Split batch    Forward/Backward    AllReduce gradients   SGD update
  across GPUs    on each GPU         across all GPUs       on all GPUs
```

### Data Parallelism vs Model Parallelism

```
Data Parallelism:                    Model Parallelism:
+--------+  +--------+               +--------+
| GPU 0  |  | GPU 1  |               | GPU 0  |
| Model  |  | Model  |               | Layer  |
| Copy   |  | Copy   |               | 0-1    |
+--------+  +--------+               +--------+
| Data   |  | Data   |                    |
| Shard  |  | Shard  |               +--------+
|   0    |  |   1    |               | GPU 1  |
+--------+  +--------+               | Layer  |
     |          |                    | 2-3    |
     +----+-----+                    +--------+
          |                              |
     AllReduce                      Pipeline
     Gradients                      Forward
```

## Key Challenges

### Challenge 1: Ring AllReduce Algorithm
**Why it matters**: This is the algorithm NCCL uses internally
**Key code**: `src/core/allreduce.py:RingAllReduce`
**Understanding points**:
- Phase 1 (ScatterReduce): Each GPU reduces one chunk completely
- Phase 2 (AllGather): Distribute reduced chunks to all GPUs
- Total data moved: 2*(n-1)/n * data_size (approaches 2x as n grows)

### Challenge 2: Gradient Synchronization
**Why it matters**: Correctness of distributed training depends on this
**Key code**: `src/core/data_parallel.py:_sync_gradients`
**Understanding points**:
- AllReduce produces the same averaged gradient on all GPUs
- All models then apply the same update
- This ensures models stay synchronized

## Worth Thinking About

### 1. Why Ring AllReduce instead of naive gather-reduce-broadcast?
**Background**: Naive approach has a bottleneck at rank 0
**Trade-off**: Ring uses all links simultaneously at full bandwidth
**Conclusion**: Ring is bandwidth-optimal, naive is latency-optimal for tiny messages

### 2. How does communication overhead scale with model size?
**Observation**: Gradient size = model size (one gradient per parameter)
**Implication**: Larger models = more communication time
**Solutions**: Gradient compression, overlapping compute with communication

### 3. Data parallelism vs model parallelism - when to use which?
**Data parallelism**: Model fits in single GPU, want linear speedup
**Model parallelism**: Model too large for single GPU
**Hybrid**: Use both (e.g., Megatron-LM)

## Quick Start

### Requirements
- Python 3.8+
- NumPy

### Install
```bash
cd projects/multi-gpu-computing
pip install numpy pytest
```

### Run Examples
```bash
# Basic data parallel training
python examples/basic_training.py

# AllReduce algorithm comparison
python examples/allreduce_comparison.py

# Performance benchmark
python examples/benchmark.py
```

### Run Tests
```bash
python -m pytest tests/ -v
```

## Related Resources

- [NCCL Documentation](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/) - NVIDIA's official NCCL docs
- [Horovod](https://github.com/horovod/horovod) - Uber's distributed training framework
- [DeepSpeed](https://github.com/microsoft/DeepSpeed) - Microsoft's deep learning optimization library
- [PyTorch Distributed](https://pytorch.org/docs/stable/distributed.html) - PyTorch's distributed package
- [Megatron-LM](https://github.com/NVIDIA/Megatron-LM) - NVIDIA's large-scale transformer training
- [Ring AllReduce Paper](https://arxiv.org/abs/1802.05799) - Horovod paper explaining Ring AllReduce

## Learning Path

1. Read [01-RESEARCH.md](docs/01-RESEARCH.md) to understand the landscape
2. Read [02-REQUIREMENTS.md](docs/02-REQUIREMENTS.md) to understand requirements
3. Read [03-DESIGN.md](docs/03-DESIGN.md) to learn the architecture
4. Read [04-PRODUCT.md](docs/04-PRODUCT.md) for product thinking
5. Read [05-DEVELOPMENT.md](docs/05-DEVELOPMENT.md) for implementation details
6. Run [examples/](examples/) to see it in action
7. Read source code, focusing on sections marked with key annotations
8. Complete exercises in [LEARNING_NOTES.md](LEARNING_NOTES.md)

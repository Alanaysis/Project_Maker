# Learning Notes

## Basic Information

- **Project Name**: Multi-GPU Parallel Computing Framework
- **Start Date**: 2024/01/01
- **Completion Date**: 2024/01/15
- **Learning Hours**: 20 hours

## 1. Core Concepts

### Concept 1: Data Parallelism

**Definition**: Split the training data across multiple GPUs, each GPU has a full copy of the model, compute gradients independently, then synchronize via AllReduce.

**Key Points**:
- Each GPU sees different data (data shard)
- Each GPU has the same model (model replica)
- Gradients are averaged across GPUs via AllReduce
- All models apply the same update -> stay synchronized

**Personal Understanding**:
[Write your understanding here]

### Concept 2: Ring AllReduce

**Definition**: A bandwidth-optimal collective communication algorithm where GPUs form a ring topology and exchange data in two phases: ScatterReduce and AllGather.

**Key Points**:
- Phase 1 (ScatterReduce): n-1 steps, each GPU fully reduces one chunk
- Phase 2 (AllGather): n-1 steps, distribute reduced chunks
- Total data moved: 2*(n-1)/n * message_size
- All links used at full bandwidth simultaneously

**Personal Understanding**:
[Write your understanding here]

### Concept 3: Model Parallelism

**Definition**: Split the model itself across GPUs, where different layers or parts of layers live on different GPUs.

**Key Points**:
- Pipeline parallelism: sequential stages, micro-batching
- Tensor parallelism: split individual layers
- Trade-off: less memory per GPU, but pipeline bubbles

**Personal Understanding**:
[Write your understanding here]

## 2. Key Challenges

### Challenge 1: Understanding Ring AllReduce Phases

**Problem**: Why does Ring AllReduce need two phases instead of one?

**Solution Process**:
1. Tried to understand single-phase approach: each GPU sends all chunks
2. Realized this creates bottleneck (one GPU sends too much)
3. Understood ScatterReduce: make each chunk complete on one GPU
4. Understood AllGather: distribute completed chunks

**Key Insight**:
- Separation of concerns: reduce first, then distribute
- Each phase uses all links at full bandwidth
- Total cost: 2*(n-1)/n * message_size (approaches 2x as n grows)

### Challenge 2: Gradient Synchronization Correctness

**Problem**: How to ensure all models stay synchronized?

**Solution Process**:
1. Initially thought each GPU updates independently
2. Realized this would cause model divergence
3. Understood: AllReduce averages gradients
4. All GPUs apply the same averaged gradient

**Key Insight**:
- AllReduce is the key synchronization mechanism
- "mean" operation ensures averaging
- This is the fundamental guarantee of data parallelism

### Challenge 3: Pipeline Bubbles

**Problem**: GPUs waiting for data in pipeline parallelism

**Solution Process**:
1. Understood basic pipeline: GPU0 -> GPU1 -> GPU2 -> GPU3
2. Realized GPU1 waits for GPU0 to finish
3. Learned about micro-batching: split batch into K micro-batches
4. Understood bubble ratio: (n-1)/(n+K-1)

**Key Insight**:
- Trade-off: more micro-batches = less bubbles
- But more micro-batches = more overhead
- Real systems use 1F1B schedule to overlap forward/backward

## 3. Design Decision Thinking

### Decision 1: Simulation vs Real CUDA

**Background**: Should we require real GPU hardware?

**My Thinking**:
- Pro simulation: lower barrier, focus on logic
- Con simulation: not "real" performance
- Decision: simulation for learning, NCCL interface for production

**Final Choice**: Simulation (with NCCL interface ready)

**Reflection**:
[Write your reflection here]

### Decision 2: Multiple AllReduce Algorithms

**Background**: Should we implement just Ring AllReduce or multiple algorithms?

**My Thinking**:
- Just Ring: simpler, focused
- Multiple: understand trade-offs
- Decision: implement all three for comparison

**Final Choice**: Implement naive, ring, and tree

**Reflection**:
[Write your reflection here]

## 4. Code Snippets to Remember

### Snippet 1: Ring AllReduce Core Loop

```python
# Phase 1: ScatterReduce
for step in range(n - 1):
    for rank in range(n):
        send_idx = (rank + step) % n
        recv_idx = (rank + step - 1) % n
        # Reduce received chunk with local chunk
        chunks[rank][recv_idx] += chunks[(rank-1)%n][recv_idx]

# Phase 2: AllGather
for step in range(n - 1):
    for rank in range(n):
        recv_idx = (rank + step) % n
        # Copy received chunk
        chunks[rank][recv_idx] = chunks[(rank-1)%n][recv_idx].copy()
```

**Why memorable**: This is the core of distributed training. Understanding this means understanding how gradients are synchronized.

### Snippet 2: Gradient Synchronization

```python
def _sync_gradients(self):
    for param_idx in range(num_params):
        grads = [model.grad[param_idx] for model in self.models]
        reduced = self.allreduce.reduce(grads, op="mean")
        for rank, grad in enumerate(reduced):
            self.models[rank].grad[param_idx] = grad
```

**Why memorable**: This is the key correctness mechanism. All models get the same gradient.

## 5. Extended Learning

### Topics to Explore Further

1. **NCCL internals**: How does NCCL choose between Ring and Tree?
2. **ZeRO optimizer**: How does DeepSpeed reduce memory?
3. **Fault tolerance**: What happens when a GPU fails?
4. **Multi-node communication**: How to handle network topology?

### Recommended Resources

- [NCCL Source Code](https://github.com/NVIDIA/nccl): See how real AllReduce is implemented
- [DeepSpeed ZeRO Paper](https://arxiv.org/abs/1910.02054): Memory optimization
- [PyTorch Distributed Tutorial](https://pytorch.org/tutorials/intermediate/ddp_tutorial.html): Practical guide
- [Horovod Paper](https://arxiv.org/abs/1802.05799): Ring AllReduce for deep learning

## 6. Self-Assessment

### Mastery Level

| Knowledge Point | Mastery | Evidence |
|----------------|---------|----------|
| Data Parallelism | [Rate 1-5] | [How you know] |
| Ring AllReduce | [Rate 1-5] | [How you know] |
| Gradient Sync | [Rate 1-5] | [How you know] |
| Pipeline Parallelism | [Rate 1-5] | [How you know] |
| NCCL Communication | [Rate 1-5] | [How you know] |

### Improvement Plan

1. [What to improve]
2. [What to improve]
3. [What to improve]

## 7. Practice Tasks

- [ ] Task 1: Run all examples and understand output
- [ ] Task 2: Implement a new AllReduce algorithm (e.g., recursive halving)
- [ ] Task 3: Add gradient compression to reduce communication
- [ ] Task 4: Implement 1F1B pipeline schedule
- [ ] Task 5: Add multi-node support (MPI-based)
- [ ] Task 6: Benchmark different tensor sizes and GPU counts
- [ ] Task 7: Explain Ring AllReduce to someone else

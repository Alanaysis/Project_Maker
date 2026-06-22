# 🔧 异构计算模块

> 2 个深度学习项目，涵盖 CPU+GPU、多 GPU 并行

---

## 📋 项目列表

| 项目 | 描述 | 技术栈 | 难度 | 状态 |
|------|------|--------|------|------|
| [heterogeneous-computing](heterogeneous-computing/) | CPU+GPU 异构计算 | C++ | ⭐⭐⭐⭐⭐ | ✅ |
| [multi-gpu-computing](multi-gpu-computing/) | 多 GPU 并行计算 | Python | ⭐⭐⭐⭐⭐ | ✅ |

---

## 🎯 学习路径

```
CPU+GPU 异构 → 多 GPU 并行
      ↓              ↓
   任务调度       数据并行
   内存管理       模型并行
   设备抽象       梯度同步
```

### 推荐学习顺序

1. **heterogeneous-computing** (CPU+GPU)
   - 学习 CPU/GPU 架构差异
   - 理解任务调度策略
   - 掌握内存管理

2. **multi-gpu-computing** (多 GPU)
   - 学习数据并行和模型并行
   - 理解 AllReduce 算法
   - 掌握梯度同步

---

## 🔧 技术栈

| 技术 | 用途 | 学习资源 |
|------|------|----------|
| **C++** | 异构计算框架 | [C++ 官方文档](https://en.cppreference.com/) |
| **Python** | 多 GPU 训练 | [Python 官方文档](https://docs.python.org/3/) |
| **CUDA** | GPU 编程 | [CUDA 文档](https://docs.nvidia.com/cuda/) |
| **NCCL** | 多 GPU 通信 | [NCCL 文档](https://docs.nvidia.com/deeplearning/nccl/) |

---

## 📊 项目详情

### 1. heterogeneous-computing (CPU+GPU)

**核心功能**：
- 任务管理（创建、配置、执行）
- 设备管理（CPU/GPU 检测和管理）
- 内存管理（分配、释放、传输）
- 4 种调度策略（轮询、负载均衡、优先级、自适应）
- CPU/GPU 执行器

**代码量**：约 30 个文件

**快速开始**：
```bash
cd heterogeneous-computing
mkdir build && cd build
cmake ..
make
./examples/01_basic_task
```

---

### 2. multi-gpu-computing (多 GPU)

**核心功能**：
- GPUTensor 抽象层（numpy 后端）
- 通信层（SimulationCommunicator、NCCLCommunicator）
- 3 种 AllReduce 算法（Naive、Ring、Tree）
- 数据并行训练器（DataParallelTrainer）
- 模型并行训练器（ModelParallelTrainer）

**代码量**：约 20 个文件

**快速开始**：
```bash
cd multi-gpu-computing
pip install numpy pytest
python -m pytest tests/ -v
python examples/basic_training.py
```

---

## 📚 学习资源

### 书籍
- 《CUDA 编程》
- 《高性能计算》

### 课程
- [NVIDIA DLI](https://www.nvidia.com/en-us/training/)

### 开源项目
- [CUDA Samples](https://github.com/NVIDIA/cuda-samples)
- [Horovod](https://github.com/horovod/horovod)
- [DeepSpeed](https://github.com/microsoft/DeepSpeed)

---

## 🔗 相关链接

- [返回主 README](../README.md)
- [学习路径图](../LEARNING_PATHS.md)
- [项目索引](../PROJECT_INDEX.md)

# CPU+GPU 异构计算框架

## 项目简介

实现一个 CPU+GPU 异构计算框架，支持任务调度和数据传输。通过本项目，深入理解 CPU/GPU 架构差异，掌握 CUDA/OpenCL 编程，学会任务调度和数据传输机制。

## 学习目标

- 理解 CPU/GPU 架构差异
- 掌握 CUDA/OpenCL 编程
- 学会任务调度和数据传输

## 技术栈

| 技术 | 用途 | 学习难度 |
|------|------|----------|
| C++ | 主语言 | ⭐⭐⭐ |
| CUDA | GPU 并行计算 | ⭐⭐⭐⭐ |
| OpenCL | 跨平台异构计算 | ⭐⭐⭐⭐⭐ |
| CMake | 构建系统 | ⭐⭐ |

## 核心循环

```
任务分解 → CPU/GPU 分配 → 数据传输 → 并行执行 → 结果聚合
```

## 重点难点

### ⭐ 重点
1. **CPU/GPU 架构差异**
   - CPU: 少量核心，复杂控制逻辑，适合串行任务
   - GPU: 大量核心，简单控制逻辑，适合并行任务
   - 理解两者的优劣势是任务分配的基础

2. **内存管理**
   - 主机内存 (Host Memory) vs 设备内存 (Device Memory)
   - 数据传输开销是性能瓶颈之一
   - 统一内存 (Unified Memory) 的使用

3. **任务调度策略**
   - 静态调度 vs 动态调度
   - 负载均衡
   - 任务粒度选择

### 💡 值得思考
1. 何时应该将任务分配给 GPU 而非 CPU？
2. 如何最小化 CPU/GPU 之间的数据传输？
3. 如何处理不同设备的计算能力差异？
4. 异步执行如何提高整体性能？

## 项目结构

```
heterogeneous-computing/
├── README.md
├── CMakeLists.txt
├── include/
│   ├── heterogeneous/
│   │   ├── core.h           # 核心框架定义
│   │   ├── task.h           # 任务抽象
│   │   ├── scheduler.h      # 任务调度器
│   │   ├── memory.h         # 内存管理
│   │   ├── device.h         # 设备抽象
│   │   └── executor.h       # 执行器
│   └── utils/
│       └── timer.h          # 性能计时器
├── src/
│   ├── core.cpp
│   ├── task.cpp
│   ├── scheduler.cpp
│   ├── memory.cpp
│   ├── device.cpp
│   └── executor.cpp
├── tests/
│   ├── test_task.cpp
│   ├── test_scheduler.cpp
│   ├── test_memory.cpp
│   └── test_integration.cpp
├── examples/
│   ├── 01_basic_task.cpp
│   ├── 02_matrix_multiply.cpp
│   ├── 03_vector_add.cpp
│   └── 04_performance_benchmark.cpp
└── docs/
    ├── 01-RESEARCH.md
    ├── 02-REQUIREMENTS.md
    ├── 03-DESIGN.md
    ├── 04-PRODUCT.md
    └── 05-DEVELOPMENT.md
```

## 快速开始

### 环境要求

- C++17 或更高版本
- CMake 3.16+
- CUDA Toolkit 11.0+ (可选，用于 GPU 支持)
- OpenCL SDK (可选，用于跨平台支持)

### 编译运行

```bash
# 创建构建目录
mkdir build && cd build

# 配置项目
cmake ..

# 编译
make -j$(nproc)

# 运行测试
./tests/test_all

# 运行示例
./examples/01_basic_task
```

### 无 GPU 环境

如果没有 GPU，框架会自动降级为 CPU-only 模式，所有计算将在 CPU 上执行。

## 参考资源

- [CUDA Programming Guide](https://docs.nvidia.com/cuda/cuda-c-programming-guide/)
- [OpenCL Specification](https://www.khronos.org/opencl/)
- [oneAPI Specification](https://www.oneapi.io/specs/)
- [Kokkos](https://github.com/kokkos/kokkos)
- [RAJA](https://github.com/LLNL/RAJA)

## License

MIT

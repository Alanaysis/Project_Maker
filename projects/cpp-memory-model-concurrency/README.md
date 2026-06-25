# C++ 内存模型和并发

深入学习 C++ 内存模型、原子操作和并发编程的完整教程项目。

## 项目简介

本项目通过可编译运行的示例代码，系统讲解 C++11/17/20 中的内存模型和并发编程知识。涵盖从基础的内存序到高级的无锁数据结构，从线程同步原语到并发设计模式。

## 快速开始

```bash
# 编译
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)

# 运行示例
./memory_location
./atomic_basics
./lock_free_stack
./thread_pool
```

## 核心概念

```
┌─────────────────────────────────────────────────────┐
│                  C++ 并发编程                        │
├──────────────┬──────────────┬───────────────────────┤
│   内存模型    │   原子操作    │     并发数据结构       │
│              │              │                       │
│  内存位置     │  atomic      │  无锁栈/队列/链表     │
│  对象模型     │  CAS         │  并发哈希表           │
│  值类别       │  内存序       │  读写锁              │
│  生命周期     │  内存屏障     │                       │
├──────────────┼──────────────┼───────────────────────┤
│  线程同步     │  并发模式     │     性能优化          │
│              │              │                       │
│  mutex       │  线程池       │  伪共享              │
│  cond_var    │  生产者消费者  │  缓存行对齐           │
│  latch/barrier│  任务调度器   │  线程亲和性           │
│  semaphore   │  async/future │  性能分析            │
│  stop_token  │  协程         │                       │
└──────────────┴──────────────┴───────────────────────┘
```

## 学习路径

### 初级：基础概念
1. `01_memory_model/` - 理解内存位置、对象模型、值类别、生命周期
2. `02_memory_order/` - 掌握五种内存序的含义和使用场景
3. `03_atomic/` - 学会使用 std::atomic 和原子操作

### 中级：并发原语
4. `05_thread_synchronization/` - 掌握 mutex、条件变量、信号量等同步原语
5. `04_concurrent_data_structures/` - 理解无锁数据结构的设计原理

### 高级：并发模式与优化
6. `06_concurrent_patterns/` - 学习线程池、生产者消费者等并发模式
7. `07_performance/` - 掌握伪共享、缓存对齐等性能优化技巧

## 目录结构

```
cpp-memory-model-concurrency/
├── CMakeLists.txt
├── README.md
├── 01_RESEARCH.md          # 市场调研
├── 02_REQUIREMENTS.md      # 需求分析
├── 03_DESIGN.md            # 技术设计
├── 04_PRODUCT.md           # 产品思考
├── 05_DEVELOPMENT.md       # 开发手册
├── include/                # 公共头文件
└── src/
    ├── 01_memory_model/        # 内存模型基础
    │   ├── memory_location.cpp
    │   ├── object_model.cpp
    │   ├── value_categories.cpp
    │   └── lifetime.cpp
    ├── 02_memory_order/        # 内存序
    │   ├── relaxed.cpp
    │   ├── acquire_release.cpp
    │   ├── seq_cst.cpp
    │   └── memory_fence.cpp
    ├── 03_atomic/              # 原子操作
    │   ├── atomic_basics.cpp
    │   ├── atomic_flag.cpp
    │   ├── atomic_smart_ptr.cpp
    │   ├── atomic_float.cpp
    │   ├── cas_operations.cpp
    │   └── atomic_performance.cpp
    ├── 04_concurrent_data_structures/  # 并发数据结构
    │   ├── lock_free_stack.cpp
    │   ├── lock_free_queue.cpp
    │   ├── lock_free_list.cpp
    │   ├── concurrent_hashmap.cpp
    │   └── rwlock.cpp
    ├── 05_thread_synchronization/      # 线程同步
    │   ├── mutex_types.cpp
    │   ├── condition_variable.cpp
    │   ├── latch.cpp
    │   ├── barrier.cpp
    │   ├── semaphore.cpp
    │   └── stop_token.cpp
    ├── 06_concurrent_patterns/         # 并发模式
    │   ├── thread_pool.cpp
    │   ├── producer_consumer.cpp
    │   ├── task_scheduler.cpp
    │   └── async_future.cpp
    └── 07_performance/                 # 性能和调试
        ├── false_sharing.cpp
        ├── cache_alignment.cpp
        ├── thread_affinity.cpp
        └── debug_techniques.cpp
```

## 编译运行

```bash
# Debug 模式（包含调试信息）
cmake .. -DCMAKE_BUILD_TYPE=Debug

# Release 模式（优化性能）
cmake .. -DCMAKE_BUILD_TYPE=Release

# 单独编译某个示例
make memory_location
./memory_location
```

## 环境要求

- C++20 编译器（GCC 10+、Clang 12+、MSVC 2019+）
- CMake 3.16+
- POSIX 线程支持（Linux/macOS）或 Windows 线程

## 关键要点

1. **内存序不是可选的** - 选择正确的内存序是编写正确并发代码的基础
2. **无锁不等于无等待** - 理解 lock-free 和 wait-free 的区别
3. **性能来自测量** - 不要猜测，用数据说话
4. **简单优先** - 除非有性能瓶颈，否则优先使用高层抽象

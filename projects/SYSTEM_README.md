# ⚙️ 系统基础设施模块

> 5 个深度学习项目，涵盖数据库、调度、容器、虚拟机、操作系统

---

## 📋 项目列表

| 项目 | 描述 | 技术栈 | 难度 | 状态 |
|------|------|--------|------|------|
| [high-concurrency-db](high-concurrency-db/) | 高并发数据库查询 | C++ | ⭐⭐⭐⭐⭐ | ✅ |
| [hpc-task-scheduler](hpc-task-scheduler/) | HPC 任务调度系统 | Go | ⭐⭐⭐⭐ | ✅ |
| [container-runtime](container-runtime/) | 容器化基础设施 | Go | ⭐⭐⭐⭐ | ✅ |
| [simple-vm](simple-vm/) | 简易虚拟机 | C++, KVM | ⭐⭐⭐⭐⭐⭐ | ✅ |
| [simple-os](simple-os/) | 简易操作系统 | C, 汇编 | ⭐⭐⭐⭐⭐⭐ | ✅ |

---

## 🎯 学习路径

```
数据库 → 任务调度 → 容器化 → 虚拟化 → 操作系统
   ↓          ↓          ↓          ↓          ↓
 B+树索引   调度算法   Namespace  KVM API    进程管理
 查询优化   资源管理   Cgroups    内存虚拟化  内存管理
 并发控制   容错机制   文件系统   I/O虚拟化   文件系统
```

### 推荐学习顺序

1. **high-concurrency-db** (数据库)
   - 学习 B+ 树索引原理
   - 理解查询优化和执行计划
   - 掌握并发控制和事务管理

2. **hpc-task-scheduler** (任务调度)
   - 学习任务调度算法（FIFO、优先级、公平）
   - 理解资源管理和隔离
   - 掌握容错和重试机制

3. **container-runtime** (容器化)
   - 学习 Linux Namespace 和 Cgroups
   - 理解容器镜像格式
   - 掌握容器网络和存储

4. **simple-vm** (虚拟化)
   - 学习 x86 架构和指令集
   - 理解 KVM API
   - 掌握内存和 I/O 虚拟化

5. **simple-os** (操作系统)
   - 学习引导加载和保护模式
   - 理解进程调度和内存管理
   - 掌握中断处理和系统调用

---

## 🔧 技术栈

| 技术 | 用途 | 学习资源 |
|------|------|----------|
| **C++** | 数据库、虚拟机 | [C++ 官方文档](https://en.cppreference.com/) |
| **Go** | 调度器、容器 | [Go 官方文档](https://go.dev/doc/) |
| **C** | 操作系统、驱动 | [C 官方文档](https://en.cppreference.com/w/c) |
| **汇编** | 引导加载 | [x86 汇编](https://www.felixcloutier.com/x86/) |
| **KVM** | 虚拟化 | [KVM 文档](https://www.kernel.org/doc/html/latest/virt/kvm/) |

---

## 📊 项目详情

### 1. high-concurrency-db (数据库)

**核心功能**：
- SQL 解析器（Tokenizer + 递归下降 Parser）
- B+ 树索引（插入、删除、点查、范围查询）
- 缓冲池管理器（LRU 替换策略）
- 并发控制（事务管理、共享/排他锁）
- 查询执行器（Volcano/Iterator 模型）

**代码量**：约 43 个文件

**快速开始**：
```bash
cd high-concurrency-db
chmod +x build.sh
./build.sh
./build.sh test
```

---

### 2. hpc-task-scheduler (任务调度)

**核心功能**：
- 任务管理（创建、查询、更新、取消）
- 资源管理（CPU、内存分配）
- 三种调度算法（FIFO、优先级、公平调度）
- RESTful API 接口

**代码量**：约 30 个文件

**快速开始**：
```bash
cd hpc-task-scheduler
go mod tidy
make build
make run
```

---

### 3. container-runtime (容器化)

**核心功能**：
- 容器生命周期管理（创建、启动、停止、删除）
- Namespace 隔离（PID、Mount、UTS、IPC、Network）
- Cgroups 资源限制（内存、CPU、进程数）
- 容器网络（IP 地址池、veth pair、Linux bridge）

**代码量**：约 25 个文件

**快速开始**：
```bash
cd container-runtime
go build -o minicontainer ./cmd/minicontainer/
sudo ./minicontainer run --name test alpine /bin/sh
```

---

### 4. simple-vm (虚拟机)

**核心功能**：
- VM 管理模块（KVM API 集成）
- vCPU 管理模块（寄存器读写、VM Exit 处理）
- I/O 处理模块（串口模拟 16550A UART）
- 实模式设置

**代码量**：约 20 个文件

**快速开始**：
```bash
cd simple-vm
mkdir build && cd build
cmake ..
make
./simple-vm build/examples/hello.bin
```

---

### 5. simple-os (操作系统)

**核心功能**：
- 引导加载（实模式→保护模式、A20 地址线）
- 内核核心（GDT、IDT、中断处理、定时器）
- 内存管理（物理内存、分页、堆管理）
- 进程管理（进程控制块、轮转调度、上下文切换）

**代码量**：约 30 个文件

**快速开始**：
```bash
cd simple-os
make
make run
```

---

## 📚 学习资源

### 书籍
- 《数据库系统概念》
- 《操作系统概念》
- 《深入理解计算机系统》

### 课程
- [MIT 6.828](https://pdos.csail.mit.edu/6.828/)
- [CMU 15-445](https://15445.courses.cs.cmu.edu/)

### 开源项目
- [SQLite](https://github.com/nicedoc/sqlite)
- [Linux](https://github.com/torvalds/linux)
- [xv6](https://github.com/mit-pdos/xv6-riscv)

---

## 🔗 相关链接

- [返回主 README](../README.md)
- [学习路径图](../LEARNING_PATHS.md)
- [项目索引](../PROJECT_INDEX.md)

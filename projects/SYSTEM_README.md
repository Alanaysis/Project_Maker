# ⚙️ 系统基础设施模块

> 12 个深度学习项目，涵盖数据库、存储引擎、并发控制、调度、容器、虚拟机、操作系统、流计算、CI/CD、日志收集、监控告警、设备管理

---

## 📋 项目列表

| 项目 | 描述 | 技术栈 | 难度 | 状态 |
|------|------|--------|------|------|
| [high-concurrency-db](high-concurrency-db/) | 高并发数据库查询 | C++ | ⭐⭐⭐⭐⭐ | ✅ |
| [lsm-tree](lsm-tree/) | LSM Tree 存储引擎 | Go | ⭐⭐⭐⭐ | ✅ |
| [hpc-task-scheduler](hpc-task-scheduler/) | HPC 任务调度系统 | Go | ⭐⭐⭐⭐ | ✅ |
| [container-runtime](container-runtime/) | 容器化基础设施 | Go | ⭐⭐⭐⭐ | ✅ |
| [simple-vm](simple-vm/) | 简易虚拟机 | C++, KVM | ⭐⭐⭐⭐⭐⭐ | ✅ |
| [simple-os](simple-os/) | 简易操作系统 | C, 汇编 | ⭐⭐⭐⭐⭐⭐ | ✅ |
| [mvcc](mvcc/) | MVCC 并发控制 | Go | ⭐⭐⭐⭐ | ✅ |
| [stream-processing](stream-processing/) | 流式计算框架 | Go | ⭐⭐⭐⭐ | ✅ |
| [cicd-pipeline](cicd-pipeline/) | CI/CD 流水线 | Go, Docker | ⭐⭐⭐⭐ | ✅ |
| [log-collector](log-collector/) | 分布式日志收集系统 | Go | ⭐⭐⭐⭐ | ✅ |
| [monitoring-alert](monitoring-alert/) | 监控告警系统 | Go | ⭐⭐⭐⭐ | ✅ |
| [device-management](device-management/) | 设备管理系统 | Go | ⭐⭐⭐⭐ | ✅ |

---

## 🎯 学习路径

```
数据库 → 存储引擎 → 任务调度 → 容器化 → 虚拟化 → 操作系统 → CI/CD → 设备管理
   ↓          ↓          ↓          ↓          ↓          ↓        ↓        ↓
 B+树索引   LSM Tree   调度算法   Namespace  KVM API    进程管理  流水线编排 设备注册
 查询优化   MemTable   资源管理   Cgroups    内存虚拟化  内存管理  自动化部署 状态上报
 并发控制   Compaction  容错机制   文件系统   I/O虚拟化   文件系统  状态报告  远程控制
```

### 推荐学习顺序

1. **high-concurrency-db** (数据库)
   - 学习 B+ 树索引原理
   - 理解查询优化和执行计划
   - 掌握并发控制和事务管理

2. **lsm-tree** (存储引擎)
   - 学习 LSM Tree 写优化原理
   - 理解 MemTable/SSTable 数据结构
   - 掌握 WAL 和 Compaction 策略

3. **hpc-task-scheduler** (任务调度)
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

6. **mvcc** (并发控制)
   - 学习多版本并发控制原理
   - 理解快照隔离和版本可见性
   - 掌握垃圾回收机制

7. **stream-processing** (流式计算)
   - 学习流处理模型和事件驱动架构
   - 掌握窗口聚合（滚动窗口、滑动窗口）
   - 学会状态管理和算子链

8. **cicd-pipeline** (CI/CD 流水线)
   - 理解 CI/CD 核心概念
   - 掌握 DAG 依赖编排
   - 学会自动化构建和部署

9. **log-collector** (日志收集)
   - 理解日志架构和管道设计
   - 掌握多格式日志解析（JSON、Logfmt、Common）
   - 学会日志聚合和索引查询

10. **monitoring-alert** (监控告警)
    - 理解监控指标类型（Counter、Gauge、Histogram）
    - 掌握时序数据存储和查询
    - 学会告警规则引擎设计

11. **device-management** (设备管理)
    - 理解设备生命周期管理
    - 掌握设备注册和状态上报
    - 学会远程控制和设备分组

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

### 2. lsm-tree (存储引擎)

**核心功能**：
- MemTable 基于跳表的内存写缓冲
- SSTable 稀疏索引的磁盘有序存储
- WAL 预写日志保证数据持久性
- Leveled Compaction 分层合并策略

**代码量**：约 1665 行核心代码 + 测试

**快速开始**：
```bash
cd lsm-tree
go run cmd/lsm-tree/main.go
go test ./test/ -v
```

---

### 3. hpc-task-scheduler (任务调度)

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

### 6. mvcc (并发控制)

**核心功能**：
- 多版本存储（版本链、可见性判断）
- 快照隔离（事务开始时获取一致性快照）
- 写写冲突检测（乐观并发控制）
- 垃圾回收（基于 SafePoint 的版本清理）

**代码量**：约 1750 行代码 + 测试

**快速开始**：
```bash
cd mvcc
go run cmd/main.go
go test ./... -v
```

---

### 7. stream-processing (流式计算框架)

**核心功能**：
- 数据流处理（事件驱动的流式管道）
- 窗口聚合（滚动窗口、滑动窗口）
- 状态管理（键值状态存储、窗口状态）
- 算子框架（Map、Filter、FlatMap、ReduceByKey、WindowedReduce）

**代码量**：约 1200 行代码 + 测试

**快速开始**：
```bash
cd stream-processing
go run cmd/pipeline/main.go
go test ./... -v
```

---

### 8. cicd-pipeline (CI/CD 流水线)

**核心功能**：
- YAML 流水线配置解析
- DAG 依赖模型与拓扑排序
- 并行阶段执行（goroutine）
- 本地/Docker 命令执行器
- 超时控制与失败重试
- 实时状态报告

**代码量**：约 10 个文件

**快速开始**：
```bash
cd cicd-pipeline
go build -o cicd ./cmd/cicd
./cicd run -f examples/pipeline.yaml -v
go test ./... -v
```

---

### 9. log-collector (日志收集)

**核心功能**：
- 多源日志采集（文件、stdin）
- 多格式日志解析（JSON、Logfmt、Common、自动检测）
- 内存存储与多维索引（时间、级别、来源）
- 高级查询引擎（DSL 查询、文本搜索）
- 交互式查询 Shell

**代码量**：约 8 个核心文件

**快速开始**：
```bash
cd log-collector
go build -o collector ./cmd/collector
echo '{"level":"info","msg":"hello"}' | ./collector
go test ./... -v
```

---

### 10. monitoring-alert (监控告警)

**核心功能**：
- 指标采集器（系统指标、自定义指标）
- 内存时序数据库（标签索引、数据压缩）
- 告警规则引擎（条件解析、状态管理）
- 多通道通知（日志、Webhook、邮件、Slack）
- 通知节流（避免告警风暴）

**代码量**：约 3123 行代码 + 测试

**快速开始**：
```bash
cd monitoring-alert
go mod tidy
go run cmd/server/main.go
go test ./test/... -v
```

---

---

### 11. device-management (设备管理)

**核心功能**：
- 设备注册与认证（生成唯一设备ID、身份验证）
- 设备状态管理（电量、信号、固件版本、IP地址）
- 远程控制（命令下发、命令执行跟踪）
- 设备分组管理（按类型、区域、功能分组）
- 事件通知（设备注册、状态更新、设备删除事件）

**代码量**：约 8 个文件

**快速开始**：
```bash
cd device-management
go mod tidy
go run cmd/server/main.go
go test ./... -v
```

**API 端点**：
- `POST /api/device/register` - 注册设备
- `GET /api/device/get` - 获取设备信息
- `GET /api/device/list` - 列出所有设备
- `POST /api/device/status` - 更新设备状态
- `POST /api/device/command` - 发送控制命令
- `DELETE /api/device/delete` - 删除设备
- `POST /api/group/create` - 创建分组
- `GET /api/group/list` - 列出所有分组
- `POST /api/group/add-device` - 添加设备到分组
- `DELETE /api/group/remove-device` - 从分组移除设备
- `GET /api/group/devices` - 获取分组设备

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

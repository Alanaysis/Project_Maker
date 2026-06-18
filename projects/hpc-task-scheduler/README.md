# HPC Task Scheduler

一个高性能计算任务调度系统，支持任务提交、资源分配、作业隔离。

## 学习目标

- 理解任务调度算法（FIFO、优先级、公平调度）
- 掌握资源管理和隔离技术
- 学会容错和任务重试机制

## 技术栈

| 技术 | 用途 | 学习难度 |
|------|------|----------|
| Go | 主语言 | ⭐⭐ |
| net/http | HTTP API | ⭐ |
| sync | 并发控制 | ⭐⭐⭐ |
| context | 超时控制 | ⭐⭐ |
| cgroups | 资源隔离 | ⭐⭐⭐⭐ |

## 核心架构

```
任务提交 → 资源评估 → 调度决策 → 任务分配 → 执行监控 → 结果收集
```

### 组件说明

1. **TaskManager** - 任务生命周期管理
2. **ResourceManager** - 资源分配与跟踪
3. **Scheduler** - 调度决策核心
4. **API Handler** - HTTP 接口层

## 快速开始

### 前置条件

- Go 1.21+
- jq (用于示例脚本)

### 编译运行

```bash
# 编译
make build

# 运行
make run

# 或者直接运行
go run cmd/server/main.go
```

### 运行测试

```bash
make test
```

### 提交任务示例

```bash
# 使用示例脚本
chmod +x examples/submit_task.sh
./examples/submit_task.sh

# 或者使用 curl
curl -X POST http://localhost:8080/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "hello-world",
    "command": "echo",
    "args": ["Hello, HPC!"],
    "resources": {
      "cpu": 1,
      "memory_mb": 256
    },
    "priority": 5,
    "owner": "user1"
  }'
```

## API 文档

### 任务管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/tasks | 提交新任务 |
| GET | /api/v1/tasks | 获取任务列表 |
| GET | /api/v1/tasks/{id} | 获取单个任务 |
| DELETE | /api/v1/tasks/{id} | 取消任务 |
| GET | /api/v1/tasks/stats | 获取任务统计 |

### 集群管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/cluster | 获取集群信息 |
| GET | /api/v1/cluster/nodes | 获取节点列表 |

### 调度器

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/scheduler | 获取调度器信息 |

### 健康检查

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /health | 健康检查 |

## 调度算法

### FIFO (先进先出)

按任务提交时间排序，先提交的任务先执行。

**优点**: 实现简单，公平
**缺点**: 可能导致长任务阻塞短任务

### Priority (优先级调度)

按任务优先级排序，高优先级任务先执行。

**优点**: 重要任务优先处理
**缺点**: 可能导致低优先级任务饥饿

### Fair (公平调度)

保证每个用户获得公平的资源份额。

**优点**: 防止资源垄断
**缺点**: 实现复杂

## 项目结构

```
hpc-task-scheduler/
├── cmd/
│   └── server/
│       └── main.go          # 程序入口
├── internal/
│   ├── api/
│   │   └── handler.go       # HTTP 处理器
│   ├── config/
│   │   └── config.go        # 配置管理
│   ├── resource/
│   │   ├── resource_manager.go
│   │   └── resource_manager_test.go
│   ├── scheduler/
│   │   ├── scheduler.go     # 调度器核心
│   │   └── scheduler_test.go
│   └── task/
│       ├── task_manager.go
│       └── task_manager_test.go
├── pkg/
│   └── models/
│       └── task.go          # 数据模型
├── docs/                    # 文档
├── examples/                # 使用示例
├── Makefile
├── go.mod
└── README.md
```

## 重点难点

### ⭐ 资源管理

资源管理是 HPC 调度系统的核心。需要考虑：

1. **原子性分配** - 要么全部成功，要么全部失败
2. **资源碎片** - 如何处理分散的资源
3. **资源预留** - 高优先级任务的资源预留

### ⭐ 调度算法

调度算法决定了系统的效率和公平性：

1. **FIFO** - 简单但可能不公平
2. **优先级** - 需要处理饥饿问题
3. **公平调度** - 需要跟踪每个用户的资源使用

### ⭐ 并发控制

Go 的并发模型非常适合调度系统：

1. **goroutine** - 轻量级线程，适合大量任务
2. **channel** - 任务通信
3. **sync.Mutex** - 保护共享资源

## 值得思考

💡 **为什么选择 Go？**

Go 的并发模型（goroutine + channel）非常适合构建调度系统。相比 C/C++，Go 的内存管理和并发控制更简单，适合快速原型开发。

💡 **如何扩展到分布式系统？**

当前是单机版本，扩展到分布式需要考虑：
1. 任务分发到多个 worker 节点
2. 资源信息同步
3. 故障检测和恢复

💡 **cgroups 的作用是什么？**

cgroups (Control Groups) 是 Linux 内核功能，用于：
1. 限制进程的 CPU、内存使用
2. 进程隔离
3. 资源统计

## 参考资源

- [Slurm Workload Manager](https://slurm.schedmd.com/)
- [Kubernetes](https://kubernetes.io/)
- [Apache Mesos](https://mesos.apache.org/)
- [Go Concurrency Patterns](https://go.dev/blog/pipelines)
- [Linux cgroups](https://www.kernel.org/doc/Documentation/cgroup-v1/cgroups.txt)

## 后续改进

- [ ] 实现真实的命令执行
- [ ] 支持 cgroups 资源隔离
- [ ] 实现分布式 worker 节点
- [ ] 添加任务依赖支持
- [ ] 实现资源预留机制
- [ ] 添加 Web UI
- [ ] 支持任务队列持久化

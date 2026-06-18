# 开发手册

## 1. 环境搭建

### 1.1 前置条件

#### Go 环境
```bash
# 安装 Go 1.21+
# macOS
brew install go

# Ubuntu/Debian
sudo apt update
sudo apt install golang-go

# 验证安装
go version
```

#### 工具安装
```bash
# 安装 jq (用于示例脚本)
# macOS
brew install jq

# Ubuntu/Debian
sudo apt install jq

# 安装 golangci-lint (可选，用于代码检查)
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
```

### 1.2 项目初始化

```bash
# 克隆项目
git clone <repository-url>
cd hpc-task-scheduler

# 下载依赖
go mod tidy

# 验证项目
go build ./...
```

### 1.3 开发环境配置

#### VS Code 配置
推荐安装以下扩展：
- Go (golang.go)
- Go Test Explorer
- REST Client

#### GoLand 配置
- 启用 Go Modules 支持
- 配置 Go SDK 路径

## 2. 项目结构详解

```
hpc-task-scheduler/
├── cmd/
│   └── server/
│       └── main.go              # 程序入口
├── internal/
│   ├── api/
│   │   └── handler.go           # HTTP 处理器
│   ├── config/
│   │   └── config.go            # 配置管理
│   ├── resource/
│   │   ├── resource_manager.go  # 资源管理器
│   │   └── resource_manager_test.go
│   ├── scheduler/
│   │   ├── scheduler.go         # 调度器核心
│   │   └── scheduler_test.go
│   └── task/
│       ├── task_manager.go      # 任务管理器
│       └── task_manager_test.go
├── pkg/
│   └── models/
│       └── task.go              # 数据模型
├── docs/                        # 文档
├── examples/                    # 使用示例
├── Makefile                     # 构建脚本
├── go.mod                       # Go 模块文件
└── README.md                    # 项目说明
```

### 2.1 目录职责

#### cmd/
程序入口点，包含主程序的初始化和启动逻辑。

#### internal/
内部实现，不对外暴露。包含：
- **api**: HTTP API 处理器
- **config**: 配置管理
- **resource**: 资源管理
- **scheduler**: 调度器核心
- **task**: 任务管理

#### pkg/
公共包，可以被外部项目引用。包含：
- **models**: 数据模型定义

#### docs/
项目文档，包含设计文档、开发手册等。

#### examples/
使用示例，包含示例脚本和代码。

## 3. 核心模块解析

### 3.1 TaskManager（任务管理器）

**职责**: 管理任务的生命周期

**核心功能**:
1. 创建任务
2. 查询任务
3. 更新任务状态
4. 取消任务

**关键数据结构**:
```go
type TaskManager struct {
    mu      sync.RWMutex
    tasks   map[string]*models.Task        // 任务映射
    byState map[models.TaskState]map[string]bool  // 状态索引
}
```

**状态索引的作用**:
- 快速按状态查询任务
- 避免遍历所有任务
- 提高查询效率

**并发控制**:
- 使用 `sync.RWMutex` 保护共享资源
- 读操作使用 `RLock()`
- 写操作使用 `Lock()`

### 3.2 ResourceManager（资源管理器）

**职责**: 管理集群资源的分配和释放

**核心功能**:
1. 分配资源
2. 释放资源
3. 检查资源可用性
4. 查询资源状态

**关键数据结构**:
```go
type ResourceManager struct {
    mu           sync.RWMutex
    totalCPU     int                           // 总 CPU
    totalMemoryMB int                          // 总内存
    usedCPU      int                           // 已用 CPU
    usedMemoryMB int                           // 已用内存
    allocations  map[string]models.ResourceRequest  // 分配记录
    nodes        map[string]*models.Node       // 节点信息
}
```

**资源分配原则**:
1. **原子性**: 要么全部分配，要么全部失败
2. **互斥性**: 同一资源不能同时分配给多个任务
3. **及时释放**: 任务完成后立即释放资源

### 3.3 Scheduler（调度器）

**职责**: 决定任务的执行顺序

**核心功能**:
1. 管理任务队列
2. 应用调度算法
3. 执行调度决策
4. 监控任务状态

**关键数据结构**:
```go
type Scheduler struct {
    mu        sync.RWMutex
    cfg       config.SchedulerConfig
    rm        *resource.ResourceManager
    tm        *task.TaskManager
    queue     []*models.Task              // 调度队列
    algorithm ScheduleAlgorithm           // 调度算法
    ctx       context.Context
    cancel    context.CancelFunc
    stats     SchedulerStats              // 统计信息
}
```

**调度流程**:
```
1. 定时触发调度
2. 对队列排序
3. 检查资源可用性
4. 分配资源
5. 执行任务
6. 监控任务状态
```

**调度算法接口**:
```go
type ScheduleAlgorithm interface {
    Sort(tasks []*models.Task)
    Name() string
}
```

### 3.4 API Handler（HTTP 处理器）

**职责**: 处理 HTTP 请求

**核心功能**:
1. 解析请求参数
2. 调用业务逻辑
3. 返回响应结果

**路由设计**:
```
/api/v1/tasks          - 任务管理
/api/v1/tasks/{id}     - 单个任务操作
/api/v1/tasks/stats    - 任务统计
/api/v1/cluster        - 集群信息
/api/v1/cluster/nodes  - 节点列表
/api/v1/scheduler      - 调度器信息
/health                - 健康检查
```

## 4. 开发流程

### 4.1 代码风格

#### 命名规范
- 包名：小写单词，不使用下划线
- 结构体：大写驼峰命名
- 函数：大写驼峰命名（导出），小写驼峰命名（内部）
- 常量：大写驼峰命名或全大写下划线分隔

#### 注释规范
- 包注释：必须有，说明包的功能
- 导出函数：必须有注释，说明功能和参数
- 复杂逻辑：必须有注释，说明实现思路

#### 错误处理
- 使用有意义的错误信息
- 错误信息应该可以帮助定位问题
- 避免忽略错误

### 4.2 测试规范

#### 单元测试
- 每个包都应该有对应的测试文件
- 测试文件命名：`xxx_test.go`
- 测试函数命名：`TestXxx`

#### 测试覆盖率
- 核心功能：100% 覆盖
- 边界条件：必须测试
- 错误处理：必须测试

#### 测试示例
```go
func TestCreateTask(t *testing.T) {
    tm := NewTaskManager()

    req := &models.SubmitTaskRequest{
        Name:    "test-task",
        Command: "echo hello",
    }

    task, err := tm.CreateTask(req)
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }

    if task.ID == "" {
        t.Error("expected task ID to be set")
    }
}
```

### 4.3 提交规范

#### Commit Message 格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Type 类型
- **feat**: 新功能
- **fix**: 修复 bug
- **docs**: 文档更新
- **style**: 代码格式调整
- **refactor**: 代码重构
- **test**: 测试相关
- **chore**: 构建/工具相关

#### 示例
```
feat(scheduler): add priority scheduling algorithm

- Implement priority-based scheduling
- Add tests for priority algorithm
- Update documentation

Closes #123
```

## 5. 调试技巧

### 5.1 日志调试

使用 Go 标准库 `log` 包：
```go
log.Printf("Task %s submitted", task.ID)
log.Printf("Resource allocated: CPU=%d, Memory=%dMB", cpu, memory)
```

### 5.2 Race Detector

Go 提供了内置的 race detector：
```bash
go test -race ./...
go run -race cmd/server/main.go
```

### 5.3 性能分析

使用 Go 内置的 pprof：
```go
import _ "net/http/pprof"

// 在代码中启动 pprof server
go func() {
    http.ListenAndServe("localhost:6060", nil)
}()
```

然后访问 `http://localhost:6060/debug/pprof/`

### 5.4 常见问题

#### 问题 1：并发访问 panic
**原因**: 多个 goroutine 同时访问共享资源
**解决**: 使用 sync.Mutex 或 sync.RWMutex

#### 问题 2：资源泄漏
**原因**: 资源分配后未释放
**解决**: 确保所有路径都释放资源

#### 问题 3：死锁
**原因**: 多个锁的获取顺序不一致
**解决**: 统一锁的获取顺序

## 6. 构建和部署

### 6.1 本地构建

```bash
# 编译
make build

# 运行
make run

# 测试
make test
```

### 6.2 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| HPC_PORT | 服务端口 | 8080 |

### 6.3 Docker 部署（待实现）

```dockerfile
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY . .
RUN go build -o server ./cmd/server

FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/server .
EXPOSE 8080
CMD ["./server"]
```

## 7. 扩展开发

### 7.1 添加新调度算法

1. 在 `internal/scheduler/` 目录下创建新文件
2. 实现 `ScheduleAlgorithm` 接口
3. 在 `NewScheduler` 函数中注册新算法
4. 添加单元测试

示例：
```go
// internal/scheduler/sjf.go (Shortest Job First)
type SJFAlgorithm struct{}

func (a *SJFAlgorithm) Sort(tasks []*models.Task) {
    sort.Slice(tasks, func(i, j int) bool {
        // 按任务预计执行时间排序
        return tasks[i].Timeout < tasks[j].Timeout
    })
}

func (a *SJFAlgorithm) Name() string {
    return "sjf"
}
```

### 7.2 添加新资源类型

1. 在 `pkg/models/task.go` 中添加新资源字段
2. 在 `internal/resource/resource_manager.go` 中处理新资源
3. 更新 API 接口
4. 添加单元测试

### 7.3 添加持久化存储

1. 定义存储接口
2. 实现内存存储（当前）
3. 实现文件存储
4. 实现数据库存储

## 8. 学习资源

### 8.1 Go 语言
- [Go 官方文档](https://go.dev/doc/)
- [Go by Example](https://gobyexample.com/)
- [Go Concurrency Patterns](https://go.dev/blog/pipelines)

### 8.2 调度算法
- [Slurm Documentation](https://slurm.schedmd.com/)
- [Kubernetes Scheduling](https://kubernetes.io/docs/concepts/scheduling-eviction/)
- [Scheduling Algorithms](https://en.wikipedia.org/wiki/Scheduling_(computing))

### 8.3 资源管理
- [Linux cgroups](https://www.kernel.org/doc/Documentation/cgroup-v1/cgroups.txt)
- [Docker Resource Management](https://docs.docker.com/config/containers/resource_constraints/)

### 8.4 并发编程
- [Go Memory Model](https://go.dev/ref/mem)
- [Sync Package](https://pkg.go.dev/sync)
- [Context Package](https://pkg.go.dev/context)

## 9. 常见问题解答

### Q1: 为什么选择 Go 语言？
A: Go 的并发模型（goroutine + channel）非常适合构建调度系统，语法简单，标准库丰富。

### Q2: 如何扩展到分布式系统？
A: 需要添加 worker 节点管理、任务分发、故障检测等模块。

### Q3: 如何支持更多资源类型？
A: 在 ResourceRequest 中添加新字段，在 ResourceManager 中处理。

### Q4: 如何提高调度性能？
A: 可以使用更高效的数据结构、减少锁的粒度、使用无锁算法等。

## 10. 贡献指南

### 10.1 如何贡献

1. Fork 项目
2. 创建功能分支
3. 提交代码
4. 创建 Pull Request

### 10.2 代码审查

- 代码风格符合规范
- 测试覆盖完整
- 文档更新及时
- Commit message 规范

### 10.3 Issue 报告

- 描述清晰
- 提供复现步骤
- 提供环境信息
- 提供错误日志

# 技术设计

## 1. 架构设计

### 1.1 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      HTTP API Layer                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ Task API    │ │ Cluster API │ │ Scheduler   │          │
│  │ Handler     │ │ Handler     │ │ API Handler │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Scheduler Core                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                Scheduler                            │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐              │   │
│  │  │   FIFO  │ │Priority │ │  Fair   │              │   │
│  │  │  Algo   │ │  Algo   │ │  Algo   │              │   │
│  │  └─────────┘ └─────────┘ └─────────┘              │   │
│  └─────────────────────────────────────────────────────┘   │
│                              │                              │
│                              ▼                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Task Manager                           │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐              │   │
│  │  │ Create  │ │ Update  │ │ Query   │              │   │
│  │  │ Task    │ │ State   │ │ Tasks   │              │   │
│  │  └─────────┘ └─────────┘ └─────────┘              │   │
│  └─────────────────────────────────────────────────────┘   │
│                              │                              │
│                              ▼                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            Resource Manager                         │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐              │   │
│  │  │Allocate │ │ Release │ │ Check   │              │   │
│  │  │Resource │ │ Resource│ │Resource │              │   │
│  │  └─────────┘ └─────────┘ └─────────┘              │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 组件职责

#### API Layer
- **职责**: 处理 HTTP 请求，参数验证，响应格式化
- **输入**: HTTP 请求
- **输出**: HTTP 响应

#### Scheduler Core
- **职责**: 调度决策，任务队列管理
- **输入**: 待调度任务
- **输出**: 调度结果

#### Task Manager
- **职责**: 任务生命周期管理
- **输入**: 任务操作请求
- **输出**: 任务状态

#### Resource Manager
- **职责**: 资源分配和释放
- **输入**: 资源请求
- **输出**: 分配结果

## 2. 数据结构设计

### 2.1 核心数据结构

#### Task（任务）

```go
type Task struct {
    ID          string          // 任务唯一标识
    Name        string          // 任务名称
    State       TaskState       // 任务状态
    Priority    TaskPriority    // 任务优先级
    Resources   ResourceRequest // 资源需求
    Command     string          // 执行命令
    Args        []string        // 命令参数
    Env         map[string]string // 环境变量
    Owner       string          // 任务所有者
    MaxRetries  int             // 最大重试次数
    RetryCount  int             // 当前重试次数
    ExitCode    *int            // 退出码
    ErrorMsg    string          // 错误信息
    CreatedAt   time.Time       // 创建时间
    StartedAt   *time.Time      // 开始时间
    CompletedAt *time.Time      // 完成时间
    Timeout     int             // 超时时间(秒)
}
```

#### TaskState（任务状态）

```go
type TaskState string

const (
    TaskStatePending   TaskState = "pending"    // 等待调度
    TaskStateQueued    TaskState = "queued"     // 已入队
    TaskStateRunning   TaskState = "running"    // 运行中
    TaskStateCompleted TaskState = "completed"  // 已完成
    TaskStateFailed    TaskState = "failed"     // 失败
    TaskStateCancelled TaskState = "cancelled"  // 已取消
    TaskStateRetrying  TaskState = "retrying"   // 重试中
)
```

#### ResourceRequest（资源请求）

```go
type ResourceRequest struct {
    CPU      int // CPU 核数
    MemoryMB int // 内存(MB)
}
```

### 2.2 数据流图

```
用户提交任务
      │
      ▼
┌─────────────┐
│ Create Task │
└─────────────┘
      │
      ▼
┌─────────────┐
│  Add to     │
│  Queue      │
└─────────────┘
      │
      ▼
┌─────────────┐
│  Scheduler  │
│  Decision   │
└─────────────┘
      │
      ▼
┌─────────────┐
│  Allocate   │
│  Resources  │
└─────────────┘
      │
      ▼
┌─────────────┐
│  Execute    │
│  Task       │
└─────────────┘
      │
      ▼
┌─────────────┐
│  Release    │
│  Resources  │
└─────────────┘
      │
      ▼
┌─────────────┐
│  Update     │
│  Status     │
└─────────────┘
```

## 3. 接口设计

### 3.1 HTTP API 接口

#### POST /api/v1/tasks - 提交任务

**请求体**:
```json
{
  "name": "hello-world",
  "command": "echo",
  "args": ["Hello, HPC!"],
  "resources": {
    "cpu": 2,
    "memory_mb": 1024
  },
  "priority": 5,
  "max_retries": 3,
  "timeout": 300,
  "owner": "user1"
}
```

**响应体**:
```json
{
  "task": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "hello-world",
    "state": "pending",
    "priority": 5,
    "resources": {
      "cpu": 2,
      "memory_mb": 1024
    },
    "command": "echo",
    "args": ["Hello, HPC!"],
    "owner": "user1",
    "max_retries": 3,
    "retry_count": 0,
    "created_at": "2024-01-01T00:00:00Z",
    "timeout": 300
  },
  "message": "Task submitted successfully"
}
```

#### GET /api/v1/tasks - 获取任务列表

**查询参数**:
- `state` (可选): 按状态过滤

**响应体**:
```json
{
  "tasks": [...],
  "total": 10
}
```

#### GET /api/v1/tasks/{id} - 获取单个任务

**响应体**:
```json
{
  "task": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "hello-world",
    "state": "completed",
    ...
  }
}
```

#### DELETE /api/v1/tasks/{id} - 取消任务

**响应体**:
```json
{
  "message": "Task cancelled successfully"
}
```

### 3.2 内部接口设计

#### ScheduleAlgorithm（调度算法接口）

```go
type ScheduleAlgorithm interface {
    // Sort 对任务队列进行排序
    Sort(tasks []*models.Task)
    // Name 返回算法名称
    Name() string
}
```

#### TaskManager 接口

```go
type TaskManager interface {
    CreateTask(req *SubmitTaskRequest) (*Task, error)
    GetTask(id string) (*Task, error)
    GetTasksByState(state TaskState) []*Task
    UpdateTaskState(id string, newState TaskState) error
    CancelTask(id string) error
    MarkTaskRunning(id string) error
    MarkTaskCompleted(id string, exitCode int) error
    MarkTaskFailed(id string, errMsg string) error
    IncrementRetry(id string) (bool, error)
}
```

#### ResourceManager 接口

```go
type ResourceManager interface {
    Allocate(taskID string, req ResourceRequest) error
    Release(taskID string) error
    CheckAvailable(req ResourceRequest) bool
    GetAvailable() ResourceRequest
    GetTotal() ResourceRequest
    GetUsed() ResourceRequest
}
```

## 4. 调度算法设计

### 4.1 FIFO 算法

**算法描述**:
按任务创建时间排序，先创建的任务先调度。

**时间复杂度**: O(n log n)

**空间复杂度**: O(1)

**实现**:
```go
type FIFOAlgorithm struct{}

func (a *FIFOAlgorithm) Sort(tasks []*models.Task) {
    sort.Slice(tasks, func(i, j int) bool {
        return tasks[i].CreatedAt.Before(tasks[j].CreatedAt)
    })
}
```

### 4.2 Priority 算法

**算法描述**:
按任务优先级排序，高优先级任务先调度。同优先级按创建时间排序。

**时间复杂度**: O(n log n)

**空间复杂度**: O(1)

**实现**:
```go
type PriorityAlgorithm struct{}

func (a *PriorityAlgorithm) Sort(tasks []*models.Task) {
    sort.Slice(tasks, func(i, j int) bool {
        if tasks[i].Priority != tasks[j].Priority {
            return tasks[i].Priority > tasks[j].Priority
        }
        return tasks[i].CreatedAt.Before(tasks[j].CreatedAt)
    })
}
```

### 4.3 Fair 算法

**算法描述**:
保证每个用户获得公平的资源份额。低优先级任务优先调度（防止饥饿）。

**时间复杂度**: O(n log n)

**空间复杂度**: O(1)

**实现**:
```go
type FairAlgorithm struct{}

func (a *FairAlgorithm) Sort(tasks []*models.Task) {
    sort.Slice(tasks, func(i, j int) bool {
        if tasks[i].Priority == tasks[j].Priority {
            return tasks[i].CreatedAt.Before(tasks[j].CreatedAt)
        }
        return tasks[i].Priority < tasks[j].Priority
    })
}
```

## 5. 资源管理设计

### 5.1 资源分配策略

**分配原则**:
1. 原子性：要么全部分配，要么全部失败
2. 互斥性：同一资源不能同时分配给多个任务
3. 有序性：按请求顺序分配

**分配流程**:
```
1. 检查资源是否足够
2. 如果足够，分配资源
3. 如果不足，返回错误
```

### 5.2 资源释放策略

**释放原则**:
1. 及时性：任务完成后立即释放
2. 完整性：释放所有占用的资源
3. 原子性：要么全部释放，要么全部保留

**释放流程**:
```
1. 查找任务的资源分配记录
2. 释放所有占用的资源
3. 删除分配记录
```

## 6. 并发控制设计

### 6.1 锁策略

**使用的锁**:
- `sync.RWMutex`: 读写锁，保护共享资源

**锁的粒度**:
- TaskManager: 任务级别的锁
- ResourceManager: 资源级别的锁
- Scheduler: 调度器级别的锁

### 6.2 并发安全

**需要保护的共享资源**:
1. 任务列表
2. 资源分配表
3. 调度队列

**保护方式**:
```go
// 读操作使用读锁
func (tm *TaskManager) GetTask(id string) (*Task, error) {
    tm.mu.RLock()
    defer tm.mu.RUnlock()
    // ...
}

// 写操作使用写锁
func (tm *TaskManager) UpdateTaskState(id string, state TaskState) error {
    tm.mu.Lock()
    defer tm.mu.Unlock()
    // ...
}
```

## 7. 错误处理设计

### 7.1 错误类型

```go
// 资源不足错误
type InsufficientResourceError struct {
    Resource string
    Available int
    Requested int
}

// 任务不存在错误
type TaskNotFoundError struct {
    TaskID string
}

// 状态转换错误
type InvalidStateTransitionError struct {
    From TaskState
    To   TaskState
}
```

### 7.2 错误处理策略

1. **资源不足**: 返回错误，任务保持等待状态
2. **任务不存在**: 返回 404 错误
3. **状态转换错误**: 返回 400 错误
4. **系统错误**: 记录日志，返回 500 错误

## 8. 监控设计

### 8.1 监控指标

**任务指标**:
- 任务提交数
- 任务完成数
- 任务失败数
- 平均等待时间
- 平均执行时间

**资源指标**:
- CPU 使用率
- 内存使用率
- 可用资源量

**调度器指标**:
- 队列长度
- 调度延迟
- 调度成功率

### 8.2 监控实现

```go
type SchedulerStats struct {
    TotalScheduled int
    TotalCompleted int
    TotalFailed    int
    TotalRetried   int
    AvgWaitTimeMs  int64
    AvgRunTimeMs   int64
}
```

## 9. 扩展性设计

### 9.1 调度算法扩展

添加新算法只需要实现 `ScheduleAlgorithm` 接口：

```go
type CustomAlgorithm struct{}

func (a *CustomAlgorithm) Sort(tasks []*models.Task) {
    // 自定义排序逻辑
}

func (a *CustomAlgorithm) Name() string {
    return "custom"
}
```

### 9.2 资源类型扩展

添加新资源类型需要：
1. 在 `ResourceRequest` 中添加新字段
2. 在 `ResourceManager` 中添加处理逻辑

### 9.3 存储后端扩展

当前使用内存存储，可以扩展为：
- 文件存储
- 数据库存储
- 分布式存储

## 10. 安全设计

### 10.1 输入验证

- 任务名称：长度限制，字符过滤
- 命令参数：防止命令注入
- 资源请求：范围检查

### 10.2 资源限制

- 单任务最大资源限制
- 用户资源配额
- 系统资源上限

### 10.3 访问控制

- 用户认证（待实现）
- 用户授权（待实现）
- 操作审计（待实现）

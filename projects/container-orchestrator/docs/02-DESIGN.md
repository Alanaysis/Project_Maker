# 02 - 容器编排系统设计

## 系统架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      API Server                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  /nodes     │  │ /services   │  │  /stats     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Manager                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Scheduler  │  │  Discovery  │  │   Monitor   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│  ┌─────────────┐  ┌─────────────┐                          │
│  │   Scaler    │  │  Container  │                          │
│  └─────────────┘  └─────────────┘                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Cluster                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Node 1    │  │   Node 2    │  │   Node 3    │        │
│  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │        │
│  │ │Container│ │  │ │Container│ │  │ │Container│ │        │
│  │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │        │
│  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │        │
│  │ │Container│ │  │ │Container│ │  │ │Container│ │        │
│  │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### 核心组件

#### 1. Container（容器定义）
- 定义容器的基本属性
- 管理容器状态
- 资源需求规格

#### 2. Scheduler（调度器）
- 实现多种调度策略
- 管理节点和容器映射
- 资源分配和回收

#### 3. Discovery（服务发现）
- 服务注册与注销
- 端点管理
- 服务解析

#### 4. Health Monitor（健康监控）
- 健康检查执行
- 健康状态管理
- 事件通知

#### 5. Scaler（扩缩容）
- 自动扩缩容策略
- 指标收集
- 手动扩缩容

#### 6. Manager（管理器）
- 协调所有组件
- 管理服务生命周期
- 提供统一接口

## 数据模型

### Container
```go
type Container struct {
    ID           string
    Name         string
    Image        string
    State        ContainerState
    NodeID       string
    Labels       map[string]string
    Ports        []Port
    Resources    Resources
    HealthCheck  *HealthCheck
    CreatedAt    time.Time
    StartedAt    *time.Time
    StoppedAt    *time.Time
    RestartCount int
}
```

### Node
```go
type Node struct {
    ID         string
    Name       string
    Address    string
    Labels     map[string]string
    Resources  Resources
    Used       Resources
    State      NodeState
    Containers []string
}
```

### Service
```go
type Service struct {
    ID        string
    Name      string
    Labels    map[string]string
    Replicas  int
    Template  ContainerTemplate
    Selector  map[string]string
    Ports     []ServicePort
    Strategy  Strategy
    CreatedAt time.Time
    UpdatedAt time.Time
}
```

## 调度算法设计

### Bin Packing 算法
```go
func (s *Scheduler) binPacking(nodes []*Node, container *Container) *Node {
    // 按可用资源排序（升序）
    sort.Slice(nodes, func(i, j int) bool {
        return nodes[i].AvailableCPU() < nodes[j].AvailableCPU()
    })
    // 选择资源最少的可用节点
    return nodes[0]
}
```

### Spread 算法
```go
func (s *Scheduler) spread(nodes []*Node, container *Container) *Node {
    // 按容器数量排序（升序）
    sort.Slice(nodes, func(i, j int) bool {
        return len(nodes[i].Containers) < len(nodes[j].Containers)
    })
    // 选择容器最少的节点
    return nodes[0]
}
```

### Round Robin 算法
```go
func (s *Scheduler) roundRobin(nodes []*Node) *Node {
    // 轮询选择
    selected := nodes[s.index % len(nodes)]
    s.index++
    return selected
}
```

## 服务发现设计

### 服务注册流程
```
1. 创建 Service 对象
2. 注册到 Discovery
3. 创建容器并调度
4. 注册 Endpoint
5. 设置健康检查
```

### 服务解析流程
```
1. 接收服务名
2. 查找 Service
3. 获取健康端点
4. 负载均衡选择
5. 返回 Endpoint
```

## 健康检查设计

### 检查类型
1. **HTTP 检查**：发送 HTTP 请求
2. **TCP 检查**：尝试 TCP 连接
3. **命令检查**：执行健康检查命令

### 检查策略
```go
type HealthCheck struct {
    Interval    time.Duration  // 检查间隔
    Timeout     time.Duration  // 超时时间
    Retries     int           // 重试次数
    StartPeriod time.Duration  // 启动延迟
    TestCommand []string       // 检查命令
}
```

## 扩缩容设计

### 自动扩缩容策略
```go
type ScalingPolicy struct {
    MinReplicas     int
    MaxReplicas     int
    ScaleUpCPU      float64  // CPU 使用率阈值（扩）
    ScaleDownCPU    float64  // CPU 使用率阈值（缩）
    ScaleUpMemory   float64  // 内存使用率阈值（扩）
    ScaleDownMemory float64  // 内存使用率阈值（缩）
    Cooldown        time.Duration  // 冷却时间
}
```

### 扩缩容决策
```go
func (s *Scaler) evaluateService(serviceID string) *ScaleDecision {
    // 获取指标
    metrics := s.metrics.GetMetrics(serviceID)

    // 评估扩缩容
    if metrics.CPU > policy.ScaleUpCPU {
        return ScaleUp
    }
    if metrics.CPU < policy.ScaleDownCPU {
        return ScaleDown
    }

    return nil
}
```

## API 设计

### 节点管理
- `POST /api/nodes` - 创建节点
- `GET /api/nodes` - 获取所有节点
- `GET /api/nodes/{id}` - 获取节点
- `DELETE /api/nodes/{id}` - 删除节点

### 服务管理
- `POST /api/services` - 创建服务
- `GET /api/services` - 获取所有服务
- `GET /api/services/{id}` - 获取服务
- `DELETE /api/services/{id}` - 删除服务
- `PUT /api/services/{id}` - 扩缩容服务

### 服务发现
- `GET /api/resolve/{name}` - 解析服务

### 监控
- `GET /api/stats` - 获取集群统计
- `GET /api/health` - 获取健康状态

## 错误处理

### 错误类型
```go
var (
    ErrNoAvailableNode = errors.New("no available node")
    ErrServiceNotFound = errors.New("service not found")
    ErrScalingInProgress = errors.New("scaling in progress")
)
```

### 错误响应
```json
{
    "error": "error message"
}
```

## 并发安全

### 锁策略
- 使用 `sync.RWMutex` 保护共享状态
- 读操作使用 `RLock`
- 写操作使用 `Lock`
- 避免死锁

### 示例
```go
type Container struct {
    mu sync.RWMutex
    // ...
}

func (c *Container) SetState(state ContainerState) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.State = state
}
```

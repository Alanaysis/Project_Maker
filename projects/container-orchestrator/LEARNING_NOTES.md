# 容器编排 - 学习笔记

## 项目概述

本项目实现了一个简易的容器编排系统，用于学习容器编排的核心概念，包括容器调度、服务发现、健康检查和扩缩容。

## 学习目标

### 1. 理解容器编排
- 容器编排是什么？为什么需要它？
- 容器编排解决了哪些问题？
- 主流容器编排工具对比

### 2. 掌握调度算法
- Bin Packing 算法
- Spread 算法
- Round Robin 算法
- 调度策略的选择和权衡

### 3. 学会服务发现
- 服务注册与注销
- 端点管理
- 服务解析与负载均衡

## 核心概念

### 1. 容器（Container）

容器是轻量级、可移植的软件包，包含应用程序及其所有依赖项。在本项目中，容器具有以下属性：

```go
type Container struct {
    ID        string
    Name      string
    Image     string
    State     ContainerState
    NodeID    string
    Resources Resources
    // ...
}
```

**关键点**：
- 容器有明确的状态生命周期：Pending → Running → Stopped/Failed
- 容器需要声明资源需求
- 容器可以被调度到不同的节点

### 2. 节点（Node）

节点是运行容器的物理机或虚拟机。节点管理自己的资源：

```go
type Node struct {
    ID        string
    Resources Resources
    Used      Resources
    State     NodeState
    Containers []string
}
```

**关键点**：
- 节点有资源上限
- 节点需要跟踪已使用的资源
- 节点状态影响调度决策

### 3. 服务（Service）

服务是一组容器的抽象，定义了期望的状态：

```go
type Service struct {
    Name      string
    Replicas  int
    Template  ContainerTemplate
    Strategy  Strategy
}
```

**关键点**：
- 服务定义了期望的副本数
- 服务使用模板创建容器
- 服务支持不同的部署策略

## 调度算法

### 1. Bin Packing

**目标**：最大化资源利用率

**策略**：将容器调度到资源最少的可用节点

```go
func (s *Scheduler) binPacking(nodes []*Node, container *Container) *Node {
    sort.Slice(nodes, func(i, j int) bool {
        return nodes[i].AvailableCPU() < nodes[j].AvailableCPU()
    })
    return nodes[0]
}
```

**优点**：
- 资源利用高效
- 减少碎片化

**缺点**：
- 可能导致热点
- 容错性较差

**适用场景**：
- 成本敏感
- 资源有限
- 批处理任务

### 2. Spread

**目标**：最大化可用性

**策略**：将容器分散到不同节点

```go
func (s *Scheduler) spread(nodes []*Node, container *Container) *Node {
    sort.Slice(nodes, func(i, j int) bool {
        return len(nodes[i].Containers) < len(nodes[j].Containers)
    })
    return nodes[0]
}
```

**优点**：
- 容错性好
- 负载均衡

**缺点**：
- 资源利用率可能较低

**适用场景**：
- 高可用要求
- Web 服务
- 关键业务

### 3. Round Robin

**目标**：简单公平

**策略**：轮询选择节点

```go
func (s *Scheduler) roundRobin(nodes []*Node) *Node {
    selected := nodes[s.index % len(nodes)]
    s.index++
    return selected
}
```

**优点**：
- 实现简单
- 公平分配

**缺点**：
- 不考虑资源差异
- 可能导致不均衡

**适用场景**：
- 节点同构
- 简单场景
- 测试环境

## 服务发现

### 1. 服务注册

服务注册是将服务信息发布到注册中心的过程：

```go
func (d *Discovery) RegisterService(service *Service) error {
    d.services[service.ID] = &ServiceEntry{
        Service:   service,
        Endpoints: make(map[string]*Endpoint),
    }
    return nil
}
```

**关键点**：
- 服务需要唯一标识
- 服务信息需要及时更新
- 需要处理重复注册

### 2. 端点管理

端点是服务的访问地址：

```go
type Endpoint struct {
    ID        string
    ServiceID string
    Address   string
    Port      int
    Health    HealthStatus
    Weight    int
}
```

**关键点**：
- 端点需要健康检查
- 端点可以有权重
- 端点需要及时更新

### 3. 服务解析

服务解析是将服务名转换为访问地址：

```go
func (d *Discovery) Resolve(serviceName string) (*Endpoint, error) {
    service := d.GetServiceByName(serviceName)
    endpoints := d.GetHealthyEndpoints(service.ID)
    return selectEndpoint(endpoints), nil
}
```

**关键点**：
- 只返回健康的端点
- 需要负载均衡
- 需要处理无可用端点的情况

## 健康检查

### 1. 检查类型

#### HTTP 检查
```go
type HTTPHealthChecker struct{}

func (h *HTTPHealthChecker) Check(ctx context.Context, container *Container) (*HealthResult, error) {
    // 发送 HTTP 请求到容器
    resp, err := http.Get(container.HealthCheck.URL)
    if err != nil {
        return &HealthResult{State: StateUnhealthy}, nil
    }
    return &HealthResult{State: StateHealthy}, nil
}
```

#### TCP 检查
```go
type TCPHealthChecker struct{}

func (t *TCPHealthChecker) Check(ctx context.Context, container *Container) (*HealthResult, error) {
    // 尝试 TCP 连接
    conn, err := net.DialTimeout("tcp", container.Address, timeout)
    if err != nil {
        return &HealthResult{State: StateUnhealthy}, nil
    }
    conn.Close()
    return &HealthResult{State: StateHealthy}, nil
}
```

### 2. 检查策略

```go
type HealthCheck struct {
    Interval     time.Duration  // 检查间隔
    Timeout      time.Duration  // 超时时间
    Retries      int           // 重试次数
    StartPeriod  time.Duration  // 启动延迟
}
```

**关键点**：
- 启动延迟：容器启动后等待一段时间再检查
- 检查间隔：多久检查一次
- 重试次数：连续失败多少次才认为不健康
- 超时时间：单次检查的超时时间

### 3. 健康状态

```go
type HealthState string

const (
    StateHealthy   HealthState = "healthy"
    StateUnhealthy HealthState = "unhealthy"
    StateUnknown   HealthState = "unknown"
    StateStarting  HealthState = "starting"
)
```

## 扩缩容

### 1. 自动扩缩容

自动扩缩容基于指标自动调整副本数：

```go
type ScalingPolicy struct {
    MinReplicas     int
    MaxReplicas     int
    ScaleUpCPU      float64  // CPU 使用率阈值（扩）
    ScaleDownCPU    float64  // CPU 使用率阈值（缩）
    Cooldown        time.Duration  // 冷却时间
}
```

**扩缩容决策**：
```go
func (s *Scaler) evaluateService(serviceID string) *ScaleDecision {
    metrics := s.metrics.GetMetrics(serviceID)
    policy := s.policies[serviceID]

    if metrics.CPU > policy.ScaleUpCPU {
        return &ScaleDecision{Direction: ScaleUp}
    }
    if metrics.CPU < policy.ScaleDownCPU {
        return &ScaleDecision{Direction: ScaleDown}
    }
    return nil
}
```

### 2. 手动扩缩容

手动扩缩容由用户触发：

```go
func (s *Scaler) ManualScale(serviceID string, desiredReplicas int) error {
    return s.Scale(serviceID, desiredReplicas)
}
```

### 3. 冷却时间

冷却时间防止频繁扩缩容：

```go
// 检查冷却时间
if lastScale, ok := s.cooldowns[serviceID]; ok {
    if time.Since(lastScale) < policy.Cooldown {
        return nil  // 还在冷却中
    }
}
```

## 并发安全

### 1. 读写锁

使用 `sync.RWMutex` 保护共享状态：

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

func (c *Container) GetState() ContainerState {
    c.mu.RLock()
    defer c.mu.RUnlock()
    return c.State
}
```

**关键点**：
- 读操作使用 `RLock`
- 写操作使用 `Lock`
- 避免长时间持有锁
- 注意死锁风险

### 2. 原子操作

对于简单的计数器，可以使用原子操作：

```go
import "sync/atomic"

type Counter struct {
    value int64
}

func (c *Counter) Increment() {
    atomic.AddInt64(&c.value, 1)
}

func (c *Counter) Value() int64 {
    return atomic.LoadInt64(&c.value)
}
```

## 设计模式

### 1. 接口隔离

使用接口解耦组件：

```go
type HealthChecker interface {
    Check(ctx context.Context, container *Container) (*HealthResult, error)
}

type HTTPHealthChecker struct{}
type TCPHealthChecker struct{}
```

**优点**：
- 便于测试
- 便于扩展
- 降低耦合

### 2. 观察者模式

使用事件通知状态变化：

```go
type HealthEvent struct {
    Type        EventType
    ContainerID string
    Result      *HealthResult
}

type HealthMonitor struct {
    eventHandler func(*HealthEvent)
}
```

### 3. 策略模式

使用策略模式实现不同的算法：

```go
type SchedulerStrategy string

const (
    StrategyBinPacking SchedulerStrategy = "bin_packing"
    StrategySpread     SchedulerStrategy = "spread"
    StrategyRoundRobin SchedulerStrategy = "round_robin"
)
```

## 实践经验

### 1. 错误处理

```go
// 定义明确的错误类型
var (
    ErrNoAvailableNode = errors.New("no available node")
    ErrServiceNotFound = errors.New("service not found")
)

// 包装错误提供上下文
if err != nil {
    return fmt.Errorf("failed to schedule container: %w", err)
}
```

### 2. 测试策略

```go
// 单元测试
func TestContainer(t *testing.T) {
    c := NewContainer("test", "nginx:latest", Resources{})
    assert.Equal(t, StatePending, c.GetState())
}

// 集成测试
func TestAPI(t *testing.T) {
    server := setupTestServer()
    req := httptest.NewRequest(http.MethodGet, "/api/nodes", nil)
    w := httptest.NewRecorder()
    server.ServeHTTP(w, req)
    assert.Equal(t, http.StatusOK, w.Code)
}
```

### 3. 代码组织

```
pkg/
├── container/    # 数据模型
├── scheduler/    # 调度逻辑
├── discovery/    # 服务发现
├── health/       # 健康检查
├── scaler/       # 扩缩容
├── manager/      # 管理器
└── api/          # API 接口
```

## 学习资源

### 书籍
1. 《Kubernetes in Action》- 全面介绍 Kubernetes
2. 《Docker Deep Dive》- 深入理解 Docker
3. 《Designing Data-Intensive Applications》- 分布式系统设计

### 在线资源
1. Kubernetes 官方文档：https://kubernetes.io/docs/
2. Docker 官方文档：https://docs.docker.com/
3. Cloud Native Computing Foundation：https://www.cncf.io/

### 开源项目
1. Kubernetes：https://github.com/kubernetes/kubernetes
2. Docker：https://github.com/moby/moby
3. etcd：https://github.com/etcd-io/etcd

## 总结

通过本项目，我学习了：

1. **容器编排的核心概念**：容器、节点、服务、调度
2. **调度算法的实现**：Bin Packing、Spread、Round Robin
3. **服务发现的机制**：注册、注销、解析
4. **健康检查的策略**：HTTP、TCP、命令检查
5. **扩缩容的实现**：自动、手动、冷却时间
6. **并发安全的实践**：读写锁、原子操作
7. **设计模式的应用**：接口隔离、观察者、策略模式

这些知识为理解和使用 Kubernetes 等容器编排系统打下了坚实的基础。

# 03 - 实现细节

## 项目结构

```
container-orchestrator/
├── cmd/
│   └── main.go              # 主程序入口
├── docs/
│   ├── 01-RESEARCH.md       # 调研文档
│   ├── 02-DESIGN.md         # 设计文档
│   ├── 03-IMPLEMENTATION.md # 实现文档
│   ├── 04-TESTING.md        # 测试文档
│   └── 05-DEVELOPMENT.md    # 开发文档
├── pkg/
│   ├── api/
│   │   └── server.go        # API 服务器
│   ├── container/
│   │   └── types.go         # 容器类型定义
│   ├── discovery/
│   │   └── discovery.go     # 服务发现
│   ├── health/
│   │   └── health.go        # 健康检查
│   ├── manager/
│   │   └── manager.go       # 管理器
│   ├── scaler/
│   │   └── scaler.go        # 扩缩容
│   └── scheduler/
│       └── scheduler.go     # 调度器
├── tests/
│   ├── api_test.go          # API 测试
│   ├── container_test.go    # 容器测试
│   ├── discovery_test.go    # 服务发现测试
│   ├── health_test.go       # 健康检查测试
│   ├── manager_test.go      # 管理器测试
│   ├── scheduler_test.go    # 调度器测试
│   └── scaler_test.go       # 扩缩容测试
├── go.mod
├── go.sum
└── README.md
```

## 核心实现

### 1. 容器定义（container/types.go）

#### 容器状态管理
```go
type ContainerState string

const (
    StatePending   ContainerState = "pending"
    StateRunning   ContainerState = "running"
    StateStopped   ContainerState = "stopped"
    StateFailed    ContainerState = "failed"
    StateCompleted ContainerState = "completed"
)
```

#### 资源定义
```go
type Resources struct {
    CPU    float64 `json:"cpu"`    // CPU 核数
    Memory int64   `json:"memory"` // 内存（字节）
    Disk   int64   `json:"disk"`   // 磁盘（字节）
}
```

#### 节点资源管理
```go
func (n *Node) AvailableResources() Resources {
    return Resources{
        CPU:    n.Resources.CPU - n.Used.CPU,
        Memory: n.Resources.Memory - n.Used.Memory,
        Disk:   n.Resources.Disk - n.Used.Disk,
    }
}

func (n *Node) CanSchedule(container *Container) bool {
    if n.State != NodeReady {
        return false
    }
    available := n.AvailableResources()
    return container.Resources.CPU <= available.CPU &&
        container.Resources.Memory <= available.Memory &&
        container.Resources.Disk <= available.Disk
}
```

### 2. 调度器（scheduler/scheduler.go）

#### 调度策略
```go
type SchedulerStrategy string

const (
    StrategyBinPacking   SchedulerStrategy = "bin_packing"
    StrategySpread       SchedulerStrategy = "spread"
    StrategyRoundRobin   SchedulerStrategy = "round_robin"
)
```

#### Bin Packing 实现
```go
func (s *Scheduler) binPacking(nodes []*container.Node, c *container.Container) *container.Node {
    sort.Slice(nodes, func(i, j int) bool {
        resI := nodes[i].AvailableResources()
        resJ := nodes[j].AvailableResources()
        // 按可用资源升序排序
        return resI.CPU < resJ.CPU
    })
    return nodes[0]
}
```

#### Spread 实现
```go
func (s *Scheduler) spread(nodes []*container.Node, c *container.Container) *container.Node {
    sort.Slice(nodes, func(i, j int) bool {
        return len(nodes[i].Containers) < len(nodes[j].Containers)
    })
    return nodes[0]
}
```

### 3. 服务发现（discovery/discovery.go）

#### 服务注册
```go
func (d *Discovery) RegisterService(service *container.Service) error {
    d.mu.Lock()
    defer d.mu.Unlock()

    if _, exists := d.services[service.ID]; exists {
        return errors.New("service already registered")
    }

    d.services[service.ID] = &ServiceEntry{
        Service:   service,
        Endpoints: make(map[string]*Endpoint),
    }

    return nil
}
```

#### 服务解析
```go
func (d *Discovery) Resolve(serviceName string) (*Endpoint, error) {
    service, err := d.GetServiceByName(serviceName)
    if err != nil {
        return nil, err
    }

    endpoints, err := d.GetHealthyEndpoints(service.ID)
    if err != nil {
        return nil, err
    }

    if len(endpoints) == 0 {
        return nil, fmt.Errorf("no healthy endpoints")
    }

    // 简单的加权轮询
    var selected *Endpoint
    maxWeight := 0
    for _, ep := range endpoints {
        if ep.Weight > maxWeight {
            maxWeight = ep.Weight
            selected = ep
        }
    }

    return selected, nil
}
```

### 4. 健康检查（health/health.go）

#### 健康检查器接口
```go
type HealthChecker interface {
    Check(ctx context.Context, container *container.Container) (*HealthResult, error)
}
```

#### HTTP 健康检查实现
```go
type HTTPHealthChecker struct {
    client HTTPClient
}

func (h *HTTPHealthChecker) Check(ctx context.Context, c *container.Container) (*HealthResult, error) {
    start := time.Now()
    result := &HealthResult{
        ContainerID: c.ID,
        Timestamp:   start,
    }

    if c.GetState() != container.StateRunning {
        result.State = StateUnhealthy
        result.Message = "container not running"
        return result, nil
    }

    result.State = StateHealthy
    result.Message = "health check passed"
    return result, nil
}
```

### 5. 扩缩容（scaler/scaler.go）

#### 扩缩容策略
```go
type ScalingPolicy struct {
    MinReplicas     int
    MaxReplicas     int
    ScaleUpCPU      float64
    ScaleDownCPU    float64
    ScaleUpMemory   float64
    ScaleDownMemory float64
    Cooldown        time.Duration
}
```

#### 扩缩容评估
```go
func (s *Scaler) evaluateService(serviceID string) *ScaleDecision {
    state := s.services[serviceID]
    policy := s.policies[serviceID]
    metrics := s.metrics.GetMetrics(serviceID)

    // 评估扩缩容
    if metrics.CPU > policy.ScaleUpCPU || metrics.Memory > policy.ScaleUpMemory {
        if state.CurrentReplicas < policy.MaxReplicas {
            return &ScaleDecision{
                Direction:       ScaleUp,
                DesiredReplicas: state.CurrentReplicas + 1,
            }
        }
    }

    if metrics.CPU < policy.ScaleDownCPU && metrics.Memory < policy.ScaleDownMemory {
        if state.CurrentReplicas > policy.MinReplicas {
            return &ScaleDecision{
                Direction:       ScaleDown,
                DesiredReplicas: state.CurrentReplicas - 1,
            }
        }
    }

    return nil
}
```

### 6. API 服务器（api/server.go）

#### 路由定义
```go
func (s *Server) routes() {
    s.mux.HandleFunc("/api/nodes", s.handleNodes)
    s.mux.HandleFunc("/api/nodes/", s.handleNode)
    s.mux.HandleFunc("/api/services", s.handleServices)
    s.mux.HandleFunc("/api/services/", s.handleService)
    s.mux.HandleFunc("/api/resolve/", s.handleResolve)
    s.mux.HandleFunc("/api/stats", s.handleStats)
    s.mux.HandleFunc("/api/health", s.handleHealth)
}
```

#### JSON 响应
```go
func writeJSON(w http.ResponseWriter, status int, data interface{}) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(status)
    json.NewEncoder(w).Encode(data)
}
```

## 关键设计决策

### 1. 并发安全
- 使用 `sync.RWMutex` 保护共享状态
- 读多写少场景使用读写锁
- 避免长时间持有锁

### 2. 接口设计
- 使用接口解耦组件
- 便于测试和扩展
- 遵循依赖倒置原则

### 3. 错误处理
- 定义明确的错误类型
- 错误信息清晰
- 便于调试和排查

### 4. 资源管理
- 及时释放资源
- 使用 context 控制生命周期
- 避免资源泄漏

## 性能优化

### 1. 批量操作
- 批量处理健康检查
- 批量更新指标
- 减少锁竞争

### 2. 异步处理
- 异步执行健康检查
- 异步处理扩缩容
- 避免阻塞主流程

### 3. 缓存策略
- 缓存服务端点
- 缓存健康状态
- 减少重复查询

## 扩展点

### 1. 调度策略
- 可添加自定义调度策略
- 支持亲和性/反亲和性
- 支持拓扑感知调度

### 2. 健康检查
- 可添加自定义检查器
- 支持多种检查协议
- 支持自定义检查间隔

### 3. 扩缩容策略
- 可添加自定义扩缩容策略
- 支持多种指标
- 支持预测性扩缩容

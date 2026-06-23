# 04 - 测试文档

## 测试策略

### 测试金字塔

```
        /\
       /  \        E2E 测试
      /    \       - API 端到端测试
     /------\
    /        \     集成测试
   /          \    - 组件间交互测试
  /------------\
 /              \  单元测试
/                \ - 单个函数/方法测试
------------------
```

### 测试类型

1. **单元测试**：测试单个函数/方法
2. **集成测试**：测试组件间交互
3. **端到端测试**：测试完整流程

## 单元测试

### 容器测试（container_test.go）

#### 测试容器创建
```go
func TestNewContainer(t *testing.T) {
    resources := container.Resources{
        CPU:    1.0,
        Memory: 1024 * 1024 * 1024,
        Disk:   10 * 1024 * 1024 * 1024,
    }

    c := container.NewContainer("test-container", "nginx:latest", resources)

    assert.NotEmpty(t, c.ID)
    assert.Equal(t, "test-container", c.Name)
    assert.Equal(t, "nginx:latest", c.Image)
    assert.Equal(t, container.StatePending, c.GetState())
}
```

#### 测试状态转换
```go
func TestContainerStateTransitions(t *testing.T) {
    c := container.NewContainer("test", "nginx:latest", container.Resources{})

    // 初始状态
    assert.Equal(t, container.StatePending, c.GetState())

    // 转换到运行状态
    c.SetState(container.StateRunning)
    assert.Equal(t, container.StateRunning, c.GetState())
    assert.NotNil(t, c.StartedAt)

    // 转换到停止状态
    c.SetState(container.StateStopped)
    assert.Equal(t, container.StateStopped, c.GetState())
    assert.NotNil(t, c.StoppedAt)
}
```

#### 测试节点资源管理
```go
func TestNodeAvailableResources(t *testing.T) {
    resources := container.Resources{
        CPU:    4.0,
        Memory: 8 * 1024 * 1024 * 1024,
        Disk:   100 * 1024 * 1024 * 1024,
    }

    node := container.NewNode("node-1", "192.168.1.1", resources)

    // 初始所有资源可用
    available := node.AvailableResources()
    assert.Equal(t, resources, available)

    // 添加容器
    containerResources := container.Resources{
        CPU:    1.0,
        Memory: 1024 * 1024 * 1024,
        Disk:   10 * 1024 * 1024 * 1024,
    }
    node.AddContainer("container-1", containerResources)

    // 检查可用资源
    available = node.AvailableResources()
    assert.Equal(t, 3.0, available.CPU)
}
```

### 调度器测试（scheduler_test.go）

#### 测试调度
```go
func TestScheduleContainer(t *testing.T) {
    s := scheduler.NewScheduler(scheduler.StrategyBinPacking)

    // 添加节点
    node := container.NewNode("node-1", "192.168.1.1", container.Resources{
        CPU:    4.0,
        Memory: 8 * 1024 * 1024 * 1024,
        Disk:   100 * 1024 * 1024 * 1024,
    })
    s.AddNode(node)

    // 调度容器
    c := container.NewContainer("test", "nginx:latest", container.Resources{
        CPU:    1.0,
        Memory: 1024 * 1024 * 1024,
        Disk:   10 * 1024 * 1024 * 1024,
    })

    selectedNode, err := s.Schedule(c)
    assert.NoError(t, err)
    assert.Equal(t, node.ID, selectedNode.ID)
}
```

#### 测试 Bin Packing 策略
```go
func TestBinPackingStrategy(t *testing.T) {
    s := scheduler.NewScheduler(scheduler.StrategyBinPacking)

    // 添加不同资源的节点
    node1 := container.NewNode("node-1", "192.168.1.1", container.Resources{
        CPU: 4.0, Memory: 8 * 1024 * 1024 * 1024,
    })
    node2 := container.NewNode("node-2", "192.168.1.2", container.Resources{
        CPU: 8.0, Memory: 16 * 1024 * 1024 * 1024,
    })

    s.AddNode(node1)
    s.AddNode(node2)

    // 调度容器 - 应该选择资源较少的 node1
    c := container.NewContainer("test", "nginx:latest", container.Resources{
        CPU: 1.0, Memory: 1024 * 1024 * 1024,
    })

    node, err := s.Schedule(c)
    assert.NoError(t, err)
    assert.Equal(t, node1.ID, node.ID)
}
```

### 服务发现测试（discovery_test.go）

#### 测试服务注册
```go
func TestRegisterService(t *testing.T) {
    d := discovery.NewDiscovery()

    service := container.NewService("web-service", 3, container.ContainerTemplate{
        Image: "nginx:latest",
    })

    err := d.RegisterService(service)
    assert.NoError(t, err)
    assert.Equal(t, 1, d.GetServiceCount())
}
```

#### 测试服务解析
```go
func TestResolve(t *testing.T) {
    d := discovery.NewDiscovery()

    service := container.NewService("web-service", 3, container.ContainerTemplate{
        Image: "nginx:latest",
    })
    d.RegisterService(service)

    // 添加端点
    endpoint := &discovery.Endpoint{
        ID:        "endpoint-1",
        ServiceID: service.ID,
        Address:   "192.168.1.1",
        Port:      8080,
        Health:    discovery.HealthHealthy,
        Weight:    1,
        LastSeen:  time.Now(),
    }
    d.RegisterEndpoint(endpoint)

    // 解析服务
    resolved, err := d.Resolve("web-service")
    assert.NoError(t, err)
    assert.Equal(t, endpoint, resolved)
}
```

### 健康检查测试（health_test.go）

#### 测试健康检查
```go
func TestHealthCheck(t *testing.T) {
    checker := health.NewHTTPHealthChecker(&mockHTTPClient{})
    monitor := health.NewHealthMonitor(checker)

    // 创建运行中的容器
    c := container.NewContainer("test", "nginx:latest", container.Resources{})
    c.SetState(container.StateRunning)

    monitor.AddContainer(c)

    // 设置事件处理器
    eventCh := make(chan *health.HealthEvent, 10)
    monitor.SetEventHandler(func(event *health.HealthEvent) {
        eventCh <- event
    })

    // 启动监控
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()
    monitor.Start(ctx, 100*time.Millisecond)

    // 等待健康检查
    select {
    case event := <-eventCh:
        assert.Equal(t, health.EventContainerHealthy, event.Type)
    case <-time.After(time.Second):
        t.Fatal("timeout waiting for health check")
    }
}
```

### 扩缩容测试（scaler_test.go）

#### 测试手动扩缩容
```go
func TestManualScale(t *testing.T) {
    scaleFunc := func(serviceID string, desiredReplicas int) error {
        return nil
    }

    s := scaler.NewScaler(scaleFunc)
    s.RegisterService("service-1", 3, &scaler.ScalingPolicy{
        MinReplicas: 1,
        MaxReplicas: 10,
    })

    // 扩容
    err := s.ManualScale("service-1", 5)
    assert.NoError(t, err)

    state, _ := s.GetServiceState("service-1")
    assert.Equal(t, 5, state.CurrentReplicas)

    // 缩容
    err = s.ManualScale("service-1", 2)
    assert.NoError(t, err)

    state, _ = s.GetServiceState("service-1")
    assert.Equal(t, 2, state.CurrentReplicas)
}
```

#### 测试自动扩缩容评估
```go
func TestEvaluate(t *testing.T) {
    scaleFunc := func(serviceID string, desiredReplicas int) error {
        return nil
    }

    s := scaler.NewScaler(scaleFunc)
    s.RegisterService("service-1", 3, &scaler.ScalingPolicy{
        MinReplicas:     1,
        MaxReplicas:     10,
        ScaleUpCPU:      0.8,
        ScaleDownCPU:    0.2,
        Cooldown:        0,
    })

    // 更新指标触发扩容
    s.UpdateMetrics("service-1", &scaler.ServiceMetrics{
        CPUUsage:    0.9,
        MemoryUsage: 0.5,
        Timestamp:   time.Now(),
    })

    // 评估
    decisions := s.Evaluate()
    assert.Len(t, decisions, 1)
    assert.Equal(t, scaler.ScaleUp, decisions[0].Direction)
}
```

## 集成测试

### API 测试（api_test.go）

#### 测试创建节点
```go
func TestCreateNode(t *testing.T) {
    server, _ := setupTestServer()

    body := api.CreateNodeRequest{
        Name:    "node-1",
        Address: "192.168.1.1",
        CPU:     4.0,
        Memory:  8 * 1024 * 1024 * 1024,
        Disk:    100 * 1024 * 1024 * 1024,
    }

    jsonBody, _ := json.Marshal(body)
    req := httptest.NewRequest(http.MethodPost, "/api/nodes", bytes.NewBuffer(jsonBody))
    req.Header.Set("Content-Type", "application/json")
    w := httptest.NewRecorder()

    server.ServeHTTP(w, req)

    assert.Equal(t, http.StatusCreated, w.Code)
}
```

#### 测试创建服务
```go
func TestCreateService(t *testing.T) {
    server, mgr := setupTestServer()

    // 添加节点
    mgr.AddNode("node-1", "192.168.1.1", container.Resources{
        CPU:    4.0,
        Memory: 8 * 1024 * 1024 * 1024,
        Disk:   100 * 1024 * 1024 * 1024,
    })

    body := api.CreateServiceRequest{
        Name:     "web-service",
        Image:    "nginx:latest",
        Replicas: 2,
        CPU:      0.5,
        Memory:   512 * 1024 * 1024,
        Disk:     5 * 1024 * 1024 * 1024,
    }

    jsonBody, _ := json.Marshal(body)
    req := httptest.NewRequest(http.MethodPost, "/api/services", bytes.NewBuffer(jsonBody))
    req.Header.Set("Content-Type", "application/json")
    w := httptest.NewRecorder()

    server.ServeHTTP(w, req)

    assert.Equal(t, http.StatusCreated, w.Code)
}
```

## 测试工具

### Mock 对象
```go
// Mock HTTP 客户端
type mockHTTPClient struct{}

func (c *mockHTTPClient) Get(url string) (int, error) {
    return 200, nil
}
```

### 测试辅助函数
```go
func setupTestServer() (*api.Server, *manager.Manager) {
    mgr := manager.NewManager()
    server := api.NewServer(mgr)
    return server, mgr
}
```

## 测试覆盖率

### 目标覆盖率
- 单元测试：80%+
- 集成测试：60%+
- 端到端测试：关键路径

### 运行测试
```bash
# 运行所有测试
go test ./...

# 运行特定包的测试
go test ./tests/...

# 运行带覆盖率的测试
go test -cover ./...

# 生成覆盖率报告
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

## 测试最佳实践

### 1. 测试命名
- 使用描述性名称
- 包含被测试的功能
- 包含预期结果

### 2. 测试组织
- 按功能模块分组
- 每个测试独立
- 避免测试依赖

### 3. 断言
- 使用 testify 库
- 断言明确具体
- 包含失败信息

### 4. Mock
- Mock 外部依赖
- 避免 Mock 内部实现
- 保持 Mock 简单

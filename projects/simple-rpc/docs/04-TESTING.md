# 简易 RPC 框架 - 测试策略

## 1. 测试概述

### 1.1 测试目标

- 验证 RPC 调用流程的正确性
- 验证服务注册与发现功能
- 验证负载均衡策略
- 验证超时处理机制
- 验证错误处理机制

### 1.2 测试类型

- 单元测试：测试单个组件的功能
- 集成测试：测试组件之间的交互
- 性能测试：测试系统性能

## 2. 单元测试

### 2.1 Codec 测试

```go
func TestJSONCodec(t *testing.T) {
    codec := NewJSONCodec()
    
    // 测试编码
    var buf bytes.Buffer
    data := map[string]int{"a": 1, "b": 2}
    err := codec.Encode(&buf, data)
    assert.NoError(t, err)
    
    // 测试解码
    var result map[string]int
    err = codec.Decode(&buf, &result)
    assert.NoError(t, err)
    assert.Equal(t, data, result)
}
```

### 2.2 Registry 测试

```go
func TestMemoryRegistryRegister(t *testing.T) {
    reg := NewMemoryRegistry()
    
    instance := &ServiceInstance{
        ServiceName: "TestService",
        InstanceID:  "instance-1",
        Address:     "localhost",
        Port:        8080,
    }
    
    err := reg.Register(instance)
    assert.NoError(t, err)
    
    // 验证服务已注册
    services, err := reg.ListServices()
    assert.NoError(t, err)
    assert.Contains(t, services, "TestService")
}

func TestMemoryRegistryGetService(t *testing.T) {
    reg := NewMemoryRegistry()
    
    // 注册多个实例
    for i := 0; i < 3; i++ {
        instance := &ServiceInstance{
            ServiceName: "TestService",
            InstanceID:  fmt.Sprintf("instance-%d", i),
            Address:     "localhost",
            Port:        8080 + i,
        }
        reg.Register(instance)
    }
    
    // 获取服务实例
    instances, err := reg.GetService("TestService")
    assert.NoError(t, err)
    assert.Len(t, instances, 3)
}

func TestMemoryRegistryWatch(t *testing.T) {
    reg := NewMemoryRegistry()
    
    // 监听服务变化
    ch, err := reg.Watch("TestService")
    assert.NoError(t, err)
    
    // 注册服务
    instance := &ServiceInstance{
        ServiceName: "TestService",
        InstanceID:  "instance-1",
        Address:     "localhost",
        Port:        8080,
    }
    reg.Register(instance)
    
    // 验证收到通知
    select {
    case instances := <-ch:
        assert.Len(t, instances, 1)
    case <-time.After(1 * time.Second):
        t.Fatal("timeout waiting for watch notification")
    }
}
```

### 2.3 Load Balancer 测试

```go
func TestRandomBalancer(t *testing.T) {
    balancer := NewRandomBalancer()
    instances := createTestInstances(3)
    
    // 测试选择
    instance, err := balancer.Select(instances)
    assert.NoError(t, err)
    assert.NotNil(t, instance)
}

func TestRoundRobinBalancer(t *testing.T) {
    balancer := NewRoundRobinBalancer()
    instances := createTestInstances(3)
    
    // 测试轮询选择
    selected := make([]string, 6)
    for i := 0; i < 6; i++ {
        instance, _ := balancer.Select(instances)
        selected[i] = instance.InstanceID
    }
    
    // 验证轮询顺序
    assert.Equal(t, "instance-B", selected[0])
    assert.Equal(t, "instance-C", selected[1])
    assert.Equal(t, "instance-A", selected[2])
}

func TestWeightedBalancer(t *testing.T) {
    balancer := NewWeightedBalancer()
    instances := createTestInstances(3)
    
    // 设置权重
    balancer.SetWeight("instance-A", 3)
    balancer.SetWeight("instance-B", 2)
    balancer.SetWeight("instance-C", 1)
    
    // 测试选择
    counts := make(map[string]int)
    for i := 0; i < 1000; i++ {
        instance, _ := balancer.Select(instances)
        counts[instance.InstanceID]++
    }
    
    // 验证权重分布
    assert.True(t, counts["instance-A"] > counts["instance-B"])
    assert.True(t, counts["instance-B"] > counts["instance-C"])
}

func TestLeastConnectionsBalancer(t *testing.T) {
    balancer := NewLeastConnectionsBalancer()
    instances := createTestInstances(3)
    
    // 增加连接数
    balancer.IncrementConnections("instance-A")
    balancer.IncrementConnections("instance-A")
    balancer.IncrementConnections("instance-B")
    
    // 应该选择 C（连接数最少）
    instance, _ := balancer.Select(instances)
    assert.Equal(t, "instance-C", instance.InstanceID)
}
```

### 2.4 Timeout 测试

```go
func TestWithTimeout(t *testing.T) {
    // 测试正常完成
    err := WithTimeout(context.Background(), 1*time.Second, func(ctx context.Context) error {
        return nil
    })
    assert.NoError(t, err)
    
    // 测试超时
    err = WithTimeout(context.Background(), 10*time.Millisecond, func(ctx context.Context) error {
        time.Sleep(100 * time.Millisecond)
        return nil
    })
    assert.Error(t, err)
    assert.Contains(t, err.Error(), "timed out")
}

func TestRetryWithTimeout(t *testing.T) {
    // 测试成功重试
    attempts := 0
    err := RetryWithTimeout(context.Background(), 1*time.Second, 3, func(ctx context.Context) error {
        attempts++
        if attempts < 3 {
            return assert.AnError
        }
        return nil
    })
    assert.NoError(t, err)
    assert.Equal(t, 3, attempts)
}

func TestCircuitBreaker(t *testing.T) {
    cb := NewCircuitBreaker(3, 2, 1*time.Second)
    
    // 初始状态应该是关闭的
    assert.Equal(t, "closed", cb.GetState())
    
    // 执行失败操作
    for i := 0; i < 3; i++ {
        cb.Execute(func() error {
            return assert.AnError
        })
    }
    
    // 熔断器应该打开
    assert.Equal(t, "open", cb.GetState())
}
```

## 3. 集成测试

### 3.1 端到端 RPC 调用测试

```go
func TestIntegrationCalculator(t *testing.T) {
    // 创建注册中心
    reg := NewMemoryRegistry()
    
    // 创建编解码器
    c := NewJSONCodec()
    
    // 获取可用端口
    listener, _ := net.Listen("tcp", "localhost:0")
    addr := listener.Addr().String()
    listener.Close()
    
    // 创建并启动服务器
    srv := NewServer(addr, c, reg)
    srv.Register(&Calculator{})
    
    go srv.Start(addr)
    time.Sleep(200 * time.Millisecond)
    
    // 创建客户端
    balancer := NewRoundRobinBalancer()
    config := &ClientConfig{
        ServiceName:  "Calculator",
        BalancerName: "round_robin",
        TimeoutConfig: DefaultConfig(),
        MaxRetries:   3,
    }
    
    client := NewClient(reg, balancer, c, config)
    defer client.Close()
    
    // 测试 Add
    ctx := context.Background()
    addReq := &AddRequest{A: 10, B: 20}
    addResp := &AddResponse{}
    err := client.Call(ctx, "Calculator", "Add", addReq, addResp)
    assert.NoError(t, err)
    assert.Equal(t, 30, addResp.Result)
    
    // 测试 Multiply
    mulReq := &MultiplyRequest{A: 5, B: 6}
    mulResp := &MultiplyResponse{}
    err = client.Call(ctx, "Calculator", "Multiply", mulReq, mulResp)
    assert.NoError(t, err)
    assert.Equal(t, 30, mulResp.Result)
}
```

### 3.2 多服务器负载均衡测试

```go
func TestIntegrationMultipleServers(t *testing.T) {
    // 创建注册中心
    reg := NewMemoryRegistry()
    
    // 创建编解码器
    c := NewJSONCodec()
    
    // 启动多个服务器
    serverCount := 3
    servers := make([]*Server, serverCount)
    
    for i := 0; i < serverCount; i++ {
        listener, _ := net.Listen("tcp", "localhost:0")
        addr := listener.Addr().String()
        listener.Close()
        
        srv := NewServer(addr, c, reg)
        srv.Register(&Calculator{})
        servers[i] = srv
        
        go srv.Start(addr)
    }
    
    time.Sleep(300 * time.Millisecond)
    
    // 验证所有服务器都已注册
    instances, _ := reg.GetService("Calculator")
    assert.Len(t, instances, serverCount)
    
    // 创建客户端
    balancer := NewRoundRobinBalancer()
    config := &ClientConfig{
        ServiceName:  "Calculator",
        BalancerName: "round_robin",
        TimeoutConfig: DefaultConfig(),
        MaxRetries:   3,
    }
    
    client := NewClient(reg, balancer, c, config)
    defer client.Close()
    
    // 测试多个调用
    ctx := context.Background()
    for i := 0; i < 10; i++ {
        addReq := &AddRequest{A: i, B: i * 2}
        addResp := &AddResponse{}
        err := client.Call(ctx, "Calculator", "Add", addReq, addResp)
        assert.NoError(t, err)
        assert.Equal(t, i+i*2, addResp.Result)
    }
}
```

### 3.3 超时和重试测试

```go
func TestIntegrationTimeout(t *testing.T) {
    // 创建注册中心
    reg := NewMemoryRegistry()
    
    // 创建编解码器
    c := NewJSONCodec()
    
    // 获取可用端口
    listener, _ := net.Listen("tcp", "localhost:0")
    addr := listener.Addr().String()
    listener.Close()
    
    // 创建并启动服务器
    srv := NewServer(addr, c, reg)
    srv.Register(&Calculator{})
    
    go srv.Start(addr)
    time.Sleep(200 * time.Millisecond)
    
    // 创建客户端，设置短超时
    balancer := NewRoundRobinBalancer()
    config := &ClientConfig{
        ServiceName: "Calculator",
        BalancerName: "round_robin",
        TimeoutConfig: &TimeoutConfig{
            ConnectTimeout:   1 * time.Second,
            RequestTimeout:   100 * time.Millisecond,
            KeepAliveTimeout: 30 * time.Second,
        },
        MaxRetries: 1,
    }
    
    client := NewClient(reg, balancer, c, config)
    defer client.Close()
    
    // 测试超时
    ctx, cancel := context.WithTimeout(context.Background(), 200*time.Millisecond)
    defer cancel()
    
    addReq := &AddRequest{A: 10, B: 20}
    addResp := &AddResponse{}
    err := client.Call(ctx, "Calculator", "Add", addReq, addResp)
    // 可能成功也可能超时
    if err != nil {
        assert.Contains(t, err.Error(), "timed out")
    }
}
```

## 4. 测试工具

### 4.1 测试辅助函数

```go
func createTestInstances(count int) []*ServiceInstance {
    instances := make([]*ServiceInstance, count)
    for i := 0; i < count; i++ {
        instances[i] = &ServiceInstance{
            ServiceName: "TestService",
            InstanceID:  "instance-" + string(rune('A'+i)),
            Address:     "localhost",
            Port:        8080 + i,
            Status:      "healthy",
        }
    }
    return instances
}

func getAvailablePort() (int, error) {
    listener, err := net.Listen("tcp", "localhost:0")
    if err != nil {
        return 0, err
    }
    defer listener.Close()
    return listener.Addr().(*net.TCPAddr).Port, nil
}
```

### 4.2 测试断言

使用 `testify` 库进行断言：

```go
import (
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

func TestExample(t *testing.T) {
    // require 失败时立即停止测试
    require.NoError(t, err)
    
    // assert 失败时继续执行
    assert.Equal(t, expected, actual)
    assert.Contains(t, str, substr)
    assert.Len(t, slice, length)
}
```

## 5. 测试覆盖率

### 5.1 覆盖率目标

- 单元测试覆盖率：> 80%
- 集成测试覆盖率：> 60%

### 5.2 覆盖率检查

```bash
# 生成覆盖率报告
go test -coverprofile=coverage.out ./...

# 查看覆盖率
go tool cover -func=coverage.out

# 生成 HTML 报告
go tool cover -html=coverage.out -o coverage.html
```

## 6. 测试最佳实践

### 6.1 测试命名

- 使用描述性的测试名称
- 遵循 `TestXxx` 命名规范
- 使用子测试组织相关测试

### 6.2 测试隔离

- 每个测试独立运行
- 使用 `t.Cleanup()` 清理资源
- 避免测试之间的依赖

### 6.3 测试数据

- 使用有意义的测试数据
- 覆盖正常和异常情况
- 使用表驱动测试

### 6.4 测试性能

- 避免在测试中进行耗时操作
- 使用 `testing.Benchmark` 进行性能测试
- 并行运行独立测试

## 7. 持续集成

### 7.1 CI 配置

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-go@v2
        with:
          go-version: '1.22'
      - run: go test ./...
      - run: go test -coverprofile=coverage.out ./...
      - uses: codecov/codecov-action@v2
        with:
          file: ./coverage.out
```

### 7.2 测试报告

- 生成测试报告
- 集成到 CI/CD 流程
- 监控测试覆盖率

## 8. 测试维护

### 8.1 测试代码审查

- 审查测试代码质量
- 确保测试覆盖关键路径
- 定期更新测试用例

### 8.2 测试文档

- 记录测试策略
- 维护测试用例文档
- 分享测试经验

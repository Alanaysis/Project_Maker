# 简易 RPC 框架 - 学习笔记

## 1. RPC 基础概念

### 1.1 什么是 RPC？

RPC（Remote Procedure Call，远程过程调用）是一种计算机通信协议，允许程序调用另一个地址空间（通常是共享网络的另一台机器上）的过程或函数，而不需要显式编写网络通信代码。

### 1.2 RPC 核心原理

```
客户端 → 序列化 → 网络传输 → 反序列化 → 服务端处理
```

**关键步骤**：
1. **客户端调用**：客户端调用本地代理方法
2. **序列化**：将方法名、参数等信息序列化为字节流
3. **网络传输**：通过网络发送到服务端
4. **反序列化**：服务端接收并反序列化请求
5. **服务处理**：服务端执行实际方法
6. **返回结果**：将结果序列化并返回给客户端

### 1.3 RPC vs REST

| 特性 | RPC | REST |
|------|-----|------|
| 协议 | 通常使用 TCP | HTTP |
| 性能 | 更高 | 较低 |
| 耦合度 | 较高 | 较低 |
| 适用场景 | 内部服务调用 | 公开 API |
| 序列化 | 二进制（Protobuf） | 文本（JSON） |

## 2. 序列化技术

### 2.1 Protocol Buffers

**特点**：
- 高效的二进制格式
- 跨语言支持
- 向后兼容
- 代码生成

**示例**：
```protobuf
syntax = "proto3";

message Person {
    string name = 1;
    int32 age = 2;
    string email = 3;
}
```

### 2.2 JSON

**特点**：
- 人类可读
- 广泛支持
- 轻量级
- 无模式

**示例**：
```json
{
    "name": "John",
    "age": 30,
    "email": "john@example.com"
}
```

### 2.3 MessagePack

**特点**：
- 二进制格式
- 高效紧凑
- 跨语言支持

### 2.4 序列化选择

| 场景 | 推荐格式 |
|------|----------|
| 高性能 | Protobuf |
| 易调试 | JSON |
| 紧凑存储 | MessagePack |
| 大数据 | Avro |

## 3. 服务注册与发现

### 3.1 核心概念

- **服务注册**：服务启动时将自身信息注册到注册中心
- **服务发现**：客户端从注册中心获取服务实例列表
- **健康检查**：定期检测服务实例是否可用
- **负载均衡**：在多个实例间分配请求

### 3.2 注册中心实现

```go
type Registry interface {
    Register(instance *ServiceInstance) error
    Deregister(instanceID string) error
    GetService(serviceName string) ([]*ServiceInstance, error)
    GetInstance(serviceName, instanceID string) (*ServiceInstance, error)
    ListServices() ([]string, error)
    Watch(serviceName string) (<-chan []*ServiceInstance, error)
    Close() error
}
```

### 3.3 健康检查

```go
func (r *MemoryRegistry) healthCheck() {
    ticker := time.NewTicker(10 * time.Second)
    defer ticker.Stop()

    for {
        select {
        case <-r.stopCh:
            return
        case <-ticker.C:
            r.mu.Lock()
            for serviceName, instances := range r.services {
                for _, inst := range instances {
                    if time.Since(inst.LastSeen) > 30*time.Second {
                        inst.Status = "unhealthy"
                        r.notifyWatchers(serviceName)
                    }
                }
            }
            r.mu.Unlock()
        }
    }
}
```

## 4. 负载均衡

### 4.1 轮询（Round Robin）

按顺序将请求分配给每个服务器。

```go
type RoundRobinBalancer struct {
    counter uint64
}

func (b *RoundRobinBalancer) Select(instances []*ServiceInstance) (*ServiceInstance, error) {
    idx := atomic.AddUint64(&b.counter, 1)
    return instances[idx%uint64(len(instances))], nil
}
```

### 4.2 随机（Random）

随机选择一个服务器。

```go
type RandomBalancer struct{}

func (b *RandomBalancer) Select(instances []*ServiceInstance) (*ServiceInstance, error) {
    return instances[rand.Intn(len(instances))], nil
}
```

### 4.3 加权轮询（Weighted Round Robin）

根据服务器权重分配请求。

```go
type WeightedBalancer struct {
    weights map[string]int
}

func (b *WeightedBalancer) Select(instances []*ServiceInstance) (*ServiceInstance, error) {
    totalWeight := 0
    for _, inst := range instances {
        totalWeight += b.weights[inst.InstanceID]
    }
    
    r := rand.Intn(totalWeight)
    for _, inst := range instances {
        r -= b.weights[inst.InstanceID]
        if r < 0 {
            return inst, nil
        }
    }
    return instances[0], nil
}
```

### 4.4 最少连接（Least Connections）

选择当前连接数最少的服务器。

```go
type LeastConnectionsBalancer struct {
    connections map[string]int
}

func (b *LeastConnectionsBalancer) Select(instances []*ServiceInstance) (*ServiceInstance, error) {
    var selected *ServiceInstance
    minConns := -1
    
    for _, inst := range instances {
        conns := b.connections[inst.InstanceID]
        if minConns == -1 || conns < minConns {
            minConns = conns
            selected = inst
        }
    }
    
    return selected, nil
}
```

## 5. 超时处理

### 5.1 超时类型

- **连接超时**：建立连接的超时时间
- **读取超时**：等待响应的超时时间
- **写入超时**：发送请求的超时时间

### 5.2 超时实现

```go
func WithTimeout(ctx context.Context, timeout time.Duration, fn func(ctx context.Context) error) error {
    ctx, cancel := context.WithTimeout(ctx, timeout)
    defer cancel()

    errCh := make(chan error, 1)
    go func() {
        errCh <- fn(ctx)
    }()

    select {
    case err := <-errCh:
        return err
    case <-ctx.Done():
        return fmt.Errorf("operation timed out: %w", ctx.Err())
    }
}
```

### 5.3 重试策略

```go
func RetryWithTimeout(ctx context.Context, timeout time.Duration, maxRetries int, fn func(ctx context.Context) error) error {
    ctx, cancel := context.WithTimeout(ctx, timeout)
    defer cancel()

    var lastErr error
    for i := 0; i < maxRetries; i++ {
        if err := fn(ctx); err != nil {
            lastErr = err
            time.Sleep(time.Duration(i+1) * 100 * time.Millisecond)
            continue
        }
        return nil
    }

    return fmt.Errorf("max retries exceeded: %w", lastErr)
}
```

### 5.4 熔断器

```go
type CircuitBreaker struct {
    state            string // "closed", "open", "half-open"
    failureCount     int
    failureThreshold int
    timeout          time.Duration
}

func (cb *CircuitBreaker) Execute(fn func() error) error {
    switch cb.state {
    case "open":
        if time.Since(cb.lastFailureTime) > cb.timeout {
            cb.state = "half-open"
            return cb.executeHalfOpen(fn)
        }
        return fmt.Errorf("circuit breaker is open")
    // ...
    }
}
```

## 6. Go 语言特性

### 6.1 反射机制

```go
// 获取类型信息
t := reflect.TypeOf(obj)

// 获取值信息
v := reflect.ValueOf(obj)

// 调用方法
method := v.MethodByName("Add")
results := method.Call([]reflect.Value{arg1, arg2})
```

### 6.2 接口设计

```go
// 定义接口
type Codec interface {
    Encode(writer io.Writer, v interface{}) error
    Decode(reader io.Reader, v interface{}) error
    Name() string
}

// 实现接口
type JSONCodec struct{}

func (c *JSONCodec) Encode(writer io.Writer, v interface{}) error {
    return json.NewEncoder(writer).Encode(v)
}
```

### 6.3 并发编程

```go
// 使用 Mutex
var mu sync.Mutex
mu.Lock()
defer mu.Unlock()

// 使用 RWMutex
var rwMu sync.RWMutex
rwMu.RLock()
defer rwMu.RUnlock()

// 使用 WaitGroup
var wg sync.WaitGroup
wg.Add(1)
go func() {
    defer wg.Done()
    // ...
}()
wg.Wait()

// 使用 Channel
ch := make(chan int, 10)
ch <- 1
v := <-ch
```

### 6.4 Context 包

```go
// 创建带超时的 context
ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()

// 创建带取消的 context
ctx, cancel := context.WithCancel(context.Background())
defer cancel()

// 使用 context
select {
case <-ctx.Done():
    return ctx.Err()
default:
    // ...
}
```

## 7. 设计模式

### 7.1 工厂模式

```go
type BalancerFactory struct{}

func (f *BalancerFactory) Create(name string) Balancer {
    switch name {
    case "random":
        return NewRandomBalancer()
    case "round_robin":
        return NewRoundRobinBalancer()
    // ...
    }
}
```

### 7.2 策略模式

```go
type Balancer interface {
    Select(instances []*ServiceInstance) (*ServiceInstance, error)
}

type Client struct {
    balancer Balancer
}

func (c *Client) Call(ctx context.Context, service string, method string, args interface{}, reply interface{}) error {
    instance, err := c.balancer.Select(instances)
    // ...
}
```

### 7.3 观察者模式

```go
type Registry struct {
    watchers map[string][]chan []*ServiceInstance
}

func (r *Registry) Watch(serviceName string) (<-chan []*ServiceInstance, error) {
    ch := make(chan []*ServiceInstance, 10)
    r.watchers[serviceName] = append(r.watchers[serviceName], ch)
    return ch, nil
}

func (r *Registry) notifyWatchers(serviceName string) {
    for _, ch := range r.watchers[serviceName] {
        ch <- instances
    }
}
```

### 7.4 代理模式

```go
type RPCProxy struct {
    client *Client
}

func (p *RPCProxy) Call(ctx context.Context, service string, method string, args interface{}, reply interface{}) error {
    // 添加日志
    log.Printf("Calling %s.%s", service, method)
    
    // 添加超时
    ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
    defer cancel()
    
    // 调用实际方法
    return p.client.Call(ctx, service, method, args, reply)
}
```

## 8. 性能优化

### 8.1 连接池

```go
type ConnPool struct {
    mu       sync.Mutex
    conns    map[string][]net.Conn
    maxIdle  int
    maxOpen  int
}

func (p *ConnPool) Get(addr string) (net.Conn, error) {
    p.mu.Lock()
    defer p.mu.Unlock()
    
    if conns, ok := p.conns[addr]; ok && len(conns) > 0 {
        conn := conns[len(conns)-1]
        p.conns[addr] = conns[:len(conns)-1]
        return conn, nil
    }
    
    return net.Dial("tcp", addr)
}
```

### 8.2 批量处理

```go
type BatchClient struct {
    client *Client
    batch  map[string][]*Request
    mu     sync.Mutex
}

func (c *BatchClient) Call(ctx context.Context, service string, method string, args interface{}, reply interface{}) error {
    c.mu.Lock()
    c.batch[service] = append(c.batch[service], &Request{...})
    c.mu.Unlock()
    
    // 批量发送
    // ...
}
```

### 8.3 异步调用

```go
type AsyncClient struct {
    client *Client
}

func (c *AsyncClient) CallAsync(ctx context.Context, service string, method string, args interface{}) <-chan *AsyncResult {
    ch := make(chan *AsyncResult, 1)
    
    go func() {
        reply := &Reply{}
        err := c.client.Call(ctx, service, method, args, reply)
        ch <- &AsyncResult{Reply: reply, Error: err}
    }()
    
    return ch
}
```

## 9. 错误处理

### 9.1 错误类型

```go
var (
    ErrTimeout       = fmt.Errorf("timeout")
    ErrConnection    = fmt.Errorf("connection error")
    ErrSerialization = fmt.Errorf("serialization error")
    ErrService       = fmt.Errorf("service error")
)
```

### 9.2 错误包装

```go
func (c *Client) Call(ctx context.Context, service string, method string, args interface{}, reply interface{}) error {
    instance, err := c.registry.GetService(service)
    if err != nil {
        return fmt.Errorf("failed to get service %s: %w", service, err)
    }
    
    conn, err := c.getConnection(instance)
    if err != nil {
        return fmt.Errorf("failed to connect to %s: %w", instance.Address, err)
    }
    
    // ...
}
```

### 9.3 错误传播

```go
type RpcResponse struct {
    RequestID string          `json:"request_id"`
    Result    json.RawMessage `json:"result"`
    Error     string          `json:"error"`
}

func (c *Client) callInstance(ctx context.Context, instance *ServiceInstance, request *RpcRequest, reply interface{}) error {
    // ...
    
    var response RpcResponse
    if err := json.Unmarshal(respMsg.Payload, &response); err != nil {
        return fmt.Errorf("failed to unmarshal response: %w", err)
    }
    
    if response.Error != "" {
        return fmt.Errorf("rpc error: %s", response.Error)
    }
    
    // ...
}
```

## 10. 测试策略

### 10.1 单元测试

```go
func TestJSONCodec(t *testing.T) {
    codec := NewJSONCodec()
    
    var buf bytes.Buffer
    data := map[string]int{"a": 1, "b": 2}
    err := codec.Encode(&buf, data)
    assert.NoError(t, err)
    
    var result map[string]int
    err = codec.Decode(&buf, &result)
    assert.NoError(t, err)
    assert.Equal(t, data, result)
}
```

### 10.2 集成测试

```go
func TestIntegrationCalculator(t *testing.T) {
    // 创建注册中心
    reg := NewMemoryRegistry()
    
    // 创建服务器
    srv := NewServer(addr, codec, reg)
    srv.Register(&Calculator{})
    
    go srv.Start(addr)
    time.Sleep(200 * time.Millisecond)
    
    // 创建客户端
    client := NewClient(reg, balancer, codec, config)
    defer client.Close()
    
    // 测试调用
    ctx := context.Background()
    addReq := &AddRequest{A: 10, B: 20}
    addResp := &AddResponse{}
    err := client.Call(ctx, "Calculator", "Add", addReq, addResp)
    assert.NoError(t, err)
    assert.Equal(t, 30, addResp.Result)
}
```

### 10.3 性能测试

```go
func BenchmarkRPC(b *testing.B) {
    // ...
    
    for i := 0; i < b.N; i++ {
        addReq := &AddRequest{A: i, B: i * 2}
        addResp := &AddResponse{}
        client.Call(ctx, "Calculator", "Add", addReq, addResp)
    }
}
```

## 11. 部署与运维

### 11.1 配置管理

```go
type Config struct {
    ServerAddr     string
    RegistryAddr   string
    BalancerName   string
    TimeoutConfig  *TimeoutConfig
    MaxRetries     int
}
```

### 11.2 监控指标

- 请求成功率
- 请求延迟
- 并发连接数
- 服务实例状态

### 11.3 日志记录

```go
log.Printf("Calling %s.%s", service, method)
log.Printf("Request completed in %v", duration)
log.Printf("Error: %v", err)
```

## 12. 常见问题

### 12.1 连接泄漏

**问题**：客户端连接未正确关闭

**解决**：实现连接池，使用 `defer` 关闭连接

### 12.2 内存泄漏

**问题**：注册中心未清理过期实例

**解决**：实现健康检查机制，定期清理过期实例

### 12.3 并发问题

**问题**：并发访问共享数据导致 panic

**解决**：使用 `sync.RWMutex` 保护共享数据

### 12.4 超时问题

**问题**：RPC 调用长时间阻塞

**解决**：实现超时控制，使用 `context.WithTimeout`

## 13. 学习资源

### 13.1 书籍

- 《Go 语言实战》
- 《Go 并发编程实战》
- 《分布式系统：概念与设计》

### 13.2 在线资源

- [Go 官方文档](https://golang.org/doc/)
- [gRPC 官方文档](https://grpc.io/docs/)
- [Protocol Buffers 文档](https://developers.google.com/protocol-buffers)

### 13.3 开源项目

- [gRPC-Go](https://github.com/grpc/grpc-go)
- [go-micro](https://github.com/micro/go-micro)
- [go-kit](https://github.com/go-kit/kit)

## 14. 总结

通过这个项目，我学到了：

1. **RPC 原理**：理解了 RPC 的核心流程和实现方式
2. **序列化技术**：掌握了 JSON、Protobuf 等序列化技术
3. **服务注册与发现**：学会了服务注册与发现的实现
4. **负载均衡**：掌握了多种负载均衡策略
5. **超时处理**：学会了超时控制和熔断器模式
6. **Go 语言特性**：深入理解了反射、接口、并发等特性
7. **设计模式**：应用了工厂、策略、观察者等设计模式
8. **测试策略**：学会了单元测试、集成测试、性能测试

这个项目是一个很好的学习 RPC 框架的实践，为后续学习更复杂的分布式系统打下了基础。

---

**开发者**：AI Assistant

**日期**：2024

**版本**：1.0.0

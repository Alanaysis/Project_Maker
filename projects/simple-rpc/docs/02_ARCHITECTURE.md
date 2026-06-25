# 简易 RPC 框架 - 架构设计

## 1. 系统架构

### 1.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Application                      │
├─────────────────────────────────────────────────────────────┤
│                      RPC Client Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Load Balancer │  │   Codec      │  │   Registry   │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
├─────────────────────────────────────────────────────────────┤
│                      Transport Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │    TCP        │  │   Timeout    │  │   Retry      │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
├─────────────────────────────────────────────────────────────┤
│                      Network                                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      Server Application                      │
├─────────────────────────────────────────────────────────────┤
│                      RPC Server Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Service      │  │   Codec      │  │   Registry   │       │
│  │  Registry     │  │              │  │              │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
├─────────────────────────────────────────────────────────────┤
│                      Transport Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │    TCP        │  │   Timeout    │  │   Health     │       │
│  └──────────────┘  └──────────────┘  │   Check      │       │
│                                      └──────────────┘       │
├─────────────────────────────────────────────────────────────┤
│                      Service Implementation                  │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 核心模块

#### 1.2.1 Codec（编解码器）

负责 RPC 消息的序列化和反序列化。

```go
type Codec interface {
    Encode(writer io.Writer, v interface{}) error
    Decode(reader io.Reader, v interface{}) error
    Name() string
}
```

**实现**：
- JSON Codec：使用 JSON 格式序列化
- Gob Codec：使用 Go 原生 Gob 格式序列化

#### 1.2.2 Transport（传输层）

负责网络通信。

```go
type Transport interface {
    Listen(addr string) error
    Accept() (Conn, error)
    Dial(addr string) (Conn, error)
    Close() error
    Addr() net.Addr
}

type Conn interface {
    Send(msg *Message) error
    Receive() (*Message, error)
    Close() error
    RemoteAddr() net.Addr
}
```

**实现**：
- TCP Transport：基于 TCP 协议

#### 1.2.3 Registry（注册中心）

负责服务注册与发现。

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

**实现**：
- Memory Registry：内存实现（学习用途）

#### 1.2.4 Load Balancer（负载均衡器）

负责在多个服务实例间分配请求。

```go
type Balancer interface {
    Select(instances []*registry.ServiceInstance) (*registry.ServiceInstance, error)
    Name() string
}
```

**实现**：
- Random Balancer：随机选择
- Round Robin Balancer：轮询选择
- Weighted Balancer：加权选择
- Least Connections Balancer：最少连接选择

#### 1.2.5 Timeout（超时处理）

负责超时控制和重试。

```go
type TimeoutConfig struct {
    ConnectTimeout   time.Duration
    RequestTimeout   time.Duration
    KeepAliveTimeout time.Duration
}
```

**功能**：
- 连接超时
- 请求超时
- 重试机制
- 熔断器

## 2. 数据流

### 2.1 RPC 调用流程

```
Client                    Server
  │                          │
  │  1. Call(service, method, args)
  │                          │
  │  2. Serialize request    │
  │     (JSON/Protobuf)      │
  │                          │
  │  3. Send over TCP ──────>│
  │                          │
  │                   4. Receive request
  │                          │
  │                   5. Deserialize request
  │                          │
  │                   6. Find service method
  │                          │
  │                   7. Execute method
  │                          │
  │                   8. Serialize response
  │                          │
  │  9. Receive response <───│
  │                          │
  │  10. Deserialize response
  │                          │
  │  11. Return result       │
  │                          │
```

### 2.2 消息格式

```
┌─────────────────────────────────────────┐
│              TCP Message                │
├─────────────────────────────────────────┤
│  Header Length (4 bytes)                │
├─────────────────────────────────────────┤
│  Header (JSON)                          │
│  - Request ID                           │
│  - Service Name                         │
│  - Method Name                          │
├─────────────────────────────────────────┤
│  Payload Length (4 bytes)               │
├─────────────────────────────────────────┤
│  Payload (serialized args/result)       │
└─────────────────────────────────────────┘
```

### 2.3 注册中心交互

```
Server                     Registry                     Client
  │                           │                            │
  │  1. Register(instance) ──>│                            │
  │                           │                            │
  │  2. Heartbeat ──────────>│                            │
  │                           │                            │
  │                           │<── 3. GetService(name) ───│
  │                           │                            │
  │                           │── 4. Return instances ───>│
  │                           │                            │
  │                           │<── 5. Watch(name) ────────│
  │                           │                            │
  │                           │── 6. Notify changes ─────>│
  │                           │                            │
```

## 3. 服务定义

### 3.1 服务接口规范

服务必须满足以下规范：

1. 方法必须是导出的（首字母大写）
2. 方法必须有 3 个参数：
   - receiver
   - context.Context
   - 请求参数（指针）
3. 方法必须返回 1 个值：error
4. 请求和响应参数必须是结构体指针

```go
// 示例服务
type Calculator struct{}

type AddRequest struct {
    A int `json:"a"`
    B int `json:"b"`
}

type AddResponse struct {
    Result int `json:"result"`
}

func (c *Calculator) Add(ctx context.Context, req *AddRequest, resp *AddResponse) error {
    resp.Result = req.A + req.B
    return nil
}
```

### 3.2 服务注册

```go
// 创建服务器
srv := server.NewServer(addr, codec, registry)

// 注册服务
err := srv.Register(&Calculator{})
```

## 4. 客户端调用

### 4.1 调用方式

```go
// 创建客户端
client := client.NewClient(registry, balancer, codec, config)

// 调用 RPC 方法
ctx := context.Background()
req := &AddRequest{A: 10, B: 20}
resp := &AddResponse{}
err := client.Call(ctx, "Calculator", "Add", req, resp)
```

### 4.2 超时配置

```go
config := &client.ClientConfig{
    ServiceName: "Calculator",
    TimeoutConfig: &timeout.TimeoutConfig{
        ConnectTimeout:   5 * time.Second,
        RequestTimeout:   10 * time.Second,
        KeepAliveTimeout: 30 * time.Second,
    },
    MaxRetries: 3,
}
```

## 5. 负载均衡策略

### 5.1 随机策略

```go
type RandomBalancer struct{}

func (b *RandomBalancer) Select(instances []*ServiceInstance) (*ServiceInstance, error) {
    return instances[rand.Intn(len(instances))], nil
}
```

### 5.2 轮询策略

```go
type RoundRobinBalancer struct {
    counter uint64
}

func (b *RoundRobinBalancer) Select(instances []*ServiceInstance) (*ServiceInstance, error) {
    idx := atomic.AddUint64(&b.counter, 1)
    return instances[idx%uint64(len(instances))], nil
}
```

### 5.3 加权策略

```go
type WeightedBalancer struct {
    weights map[string]int
}

func (b *WeightedBalancer) Select(instances []*ServiceInstance) (*ServiceInstance, error) {
    // 按权重选择
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

### 5.4 最少连接策略

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

## 6. 超时处理

### 6.1 超时配置

```go
type TimeoutConfig struct {
    ConnectTimeout   time.Duration // 连接超时
    RequestTimeout   time.Duration // 请求超时
    KeepAliveTimeout time.Duration // 保活超时
}
```

### 6.2 重试机制

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

### 6.3 熔断器

```go
type CircuitBreaker struct {
    state            string // "closed", "open", "half-open"
    failureCount     int
    failureThreshold int
    successThreshold int
    timeout          time.Duration
}

func (cb *CircuitBreaker) Execute(fn func() error) error {
    switch cb.state {
    case "open":
        // 检查是否可以进入半开状态
        if time.Since(cb.lastFailureTime) > cb.timeout {
            cb.state = "half-open"
            return cb.executeHalfOpen(fn)
        }
        return fmt.Errorf("circuit breaker is open")
    case "half-open":
        return cb.executeHalfOpen(fn)
    default: // closed
        return cb.executeClosed(fn)
    }
}
```

## 7. 错误处理

### 7.1 错误类型

- **连接错误**：网络连接失败
- **超时错误**：操作超时
- **序列化错误**：序列化/反序列化失败
- **服务错误**：服务方法执行失败
- **注册中心错误**：服务注册/发现失败

### 7.2 错误传播

```go
type RpcResponse struct {
    RequestID string          `json:"request_id"`
    Result    json.RawMessage `json:"result"`
    Error     string          `json:"error"` // 错误信息
}
```

## 8. 性能优化

### 8.1 连接池

复用 TCP 连接，减少连接建立开销。

### 8.2 异步调用

支持异步 RPC 调用，提高并发性能。

### 8.3 批量调用

支持批量 RPC 调用，减少网络往返。

## 9. 扩展性

### 9.1 编解码器扩展

可以轻松添加新的编解码器（如 Protobuf、MessagePack）。

### 9.2 传输层扩展

可以添加新的传输层实现（如 WebSocket、HTTP/2）。

### 9.3 注册中心扩展

可以对接真实的注册中心（如 Consul、etcd）。

### 9.4 负载均衡器扩展

可以添加新的负载均衡策略（如一致性哈希）。

## 10. 安全考虑

### 10.1 认证

- Token 认证
- TLS 双向认证

### 10.2 授权

- 基于角色的访问控制
- 方法级权限控制

### 10.3 加密

- TLS 加密传输
- 数据加密

## 11. 监控与日志

### 11.1 监控指标

- 请求成功率
- 请求延迟
- 并发连接数
- 服务实例状态

### 11.2 日志记录

- 请求日志
- 错误日志
- 性能日志

## 12. 测试策略

### 12.1 单元测试

- 编解码器测试
- 负载均衡器测试
- 注册中心测试
- 超时处理测试

### 12.2 集成测试

- 端到端 RPC 调用测试
- 多服务器负载均衡测试
- 超时和重试测试

### 12.3 性能测试

- 并发性能测试
- 延迟测试
- 吞吐量测试

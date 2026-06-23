# 简易 RPC 框架 - 实现细节

## 1. 项目结构

```
simple-rpc/
├── cmd/
│   ├── server/
│   │   └── main.go              # 服务器入口
│   └── client/
│       └── main.go              # 客户端入口
├── internal/
│   ├── codec/
│   │   └── codec.go             # 编解码器实现
│   ├── transport/
│   │   └── transport.go         # 传输层实现
│   ├── registry/
│   │   └── registry.go          # 注册中心实现
│   ├── loadbalancer/
│   │   └── balancer.go          # 负载均衡器实现
│   ├── timeout/
│   │   └── timeout.go           # 超时处理实现
│   ├── server/
│   │   └── server.go            # RPC 服务器实现
│   └── client/
│       └── client.go            # RPC 客户端实现
├── proto/
│   ├── rpc.proto                # Protobuf 定义
│   └── rpc.pb.go                # 生成的代码
├── examples/
│   └── service.go               # 示例服务
├── test/
│   ├── server_test.go           # 服务器测试
│   ├── registry_test.go         # 注册中心测试
│   ├── loadbalancer_test.go     # 负载均衡器测试
│   ├── timeout_test.go          # 超时处理测试
│   └── integration_test.go      # 集成测试
├── docs/
│   ├── 01-RESEARCH.md           # 市场调研
│   ├── 02-ARCHITECTURE.md       # 架构设计
│   ├── 03-IMPLEMENTATION.md     # 实现细节
│   ├── 04-TESTING.md            # 测试策略
│   └── 05-DEVELOPMENT.md        # 开发日志
├── LEARNING_NOTES.md            # 学习笔记
├── go.mod                       # Go 模块文件
└── README.md                    # 项目说明
```

## 2. 核心实现

### 2.1 Codec（编解码器）

#### 2.1.1 接口定义

```go
type Codec interface {
    Encode(writer io.Writer, v interface{}) error
    Decode(reader io.Reader, v interface{}) error
    Name() string
}
```

#### 2.1.2 JSON Codec 实现

```go
type JSONCodec struct{}

func (c *JSONCodec) Encode(writer io.Writer, v interface{}) error {
    return json.NewEncoder(writer).Encode(v)
}

func (c *JSONCodec) Decode(reader io.Reader, v interface{}) error {
    return json.NewDecoder(reader).Decode(v)
}
```

#### 2.1.3 编解码器注册表

```go
type Registry struct {
    codecs map[string]Codec
}

func (r *Registry) Register(codec Codec) {
    r.codecs[codec.Name()] = codec
}

func (r *Registry) Get(name string) (Codec, error) {
    codec, ok := r.codecs[name]
    if !ok {
        return nil, fmt.Errorf("codec not found: %s", name)
    }
    return codec, nil
}
```

### 2.2 Transport（传输层）

#### 2.2.1 TCP Transport 实现

```go
type TCPTransport struct {
    listener net.Listener
}

func (t *TCPTransport) Listen(addr string) error {
    ln, err := net.Listen("tcp", addr)
    if err != nil {
        return err
    }
    t.listener = ln
    return nil
}

func (t *TCPTransport) Accept() (Conn, error) {
    conn, err := t.listener.Accept()
    if err != nil {
        return nil, err
    }
    return NewTCPConn(conn), nil
}

func (t *TCPTransport) Dial(addr string) (Conn, error) {
    conn, err := net.Dial("tcp", addr)
    if err != nil {
        return nil, err
    }
    return NewTCPConn(conn), nil
}
```

#### 2.2.2 TCP 连接实现

```go
type TCPConn struct {
    conn net.Conn
}

func (c *TCPConn) Send(msg *Message) error {
    // 消息格式: [length(4 bytes)][payload]
    payloadLen := len(msg.Payload)
    header := make([]byte, 4)
    header[0] = byte(payloadLen >> 24)
    header[1] = byte(payloadLen >> 16)
    header[2] = byte(payloadLen >> 8)
    header[3] = byte(payloadLen)

    if _, err := c.conn.Write(header); err != nil {
        return err
    }
    if _, err := c.conn.Write(msg.Payload); err != nil {
        return err
    }
    return nil
}

func (c *TCPConn) Receive() (*Message, error) {
    // 读取长度头
    header := make([]byte, 4)
    if _, err := io.ReadFull(c.conn, header); err != nil {
        return nil, err
    }

    payloadLen := int(header[0])<<24 | int(header[1])<<16 | int(header[2])<<8 | int(header[3])

    // 读取 payload
    payload := make([]byte, payloadLen)
    if _, err := io.ReadFull(c.conn, payload); err != nil {
        return nil, err
    }

    return &Message{
        Header:  make(map[string]string),
        Payload: payload,
    }, nil
}
```

### 2.3 Registry（注册中心）

#### 2.3.1 内存注册中心实现

```go
type MemoryRegistry struct {
    mu       sync.RWMutex
    services map[string]map[string]*ServiceInstance
    watchers map[string][]chan []*ServiceInstance
    stopCh   chan struct{}
}

func (r *MemoryRegistry) Register(instance *ServiceInstance) error {
    r.mu.Lock()
    defer r.mu.Unlock()

    if _, ok := r.services[instance.ServiceName]; !ok {
        r.services[instance.ServiceName] = make(map[string]*ServiceInstance)
    }

    instance.LastSeen = time.Now()
    instance.Status = "healthy"
    r.services[instance.ServiceName][instance.InstanceID] = instance

    // 通知 watchers
    r.notifyWatchers(instance.ServiceName)

    return nil
}

func (r *MemoryRegistry) GetService(serviceName string) ([]*ServiceInstance, error) {
    r.mu.RLock()
    defer r.mu.RUnlock()

    instances, ok := r.services[serviceName]
    if !ok {
        return nil, fmt.Errorf("service not found: %s", serviceName)
    }

    result := make([]*ServiceInstance, 0, len(instances))
    for _, inst := range instances {
        if inst.Status == "healthy" {
            result = append(result, inst)
        }
    }

    if len(result) == 0 {
        return nil, fmt.Errorf("no healthy instances for service: %s", serviceName)
    }

    return result, nil
}
```

#### 2.3.2 健康检查

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

### 2.4 Load Balancer（负载均衡器）

#### 2.4.1 随机负载均衡

```go
type RandomBalancer struct{}

func (b *RandomBalancer) Select(instances []*ServiceInstance) (*ServiceInstance, error) {
    if len(instances) == 0 {
        return nil, fmt.Errorf("no instances available")
    }
    return instances[rand.Intn(len(instances))], nil
}
```

#### 2.4.2 轮询负载均衡

```go
type RoundRobinBalancer struct {
    counter uint64
}

func (b *RoundRobinBalancer) Select(instances []*ServiceInstance) (*ServiceInstance, error) {
    if len(instances) == 0 {
        return nil, fmt.Errorf("no instances available")
    }

    idx := atomic.AddUint64(&b.counter, 1)
    return instances[idx%uint64(len(instances))], nil
}
```

#### 2.4.3 加权负载均衡

```go
type WeightedBalancer struct {
    mu      sync.Mutex
    weights map[string]int
}

func (b *WeightedBalancer) Select(instances []*ServiceInstance) (*ServiceInstance, error) {
    if len(instances) == 0 {
        return nil, fmt.Errorf("no instances available")
    }

    b.mu.Lock()
    defer b.mu.Unlock()

    // 计算总权重
    totalWeight := 0
    for _, inst := range instances {
        w, ok := b.weights[inst.InstanceID]
        if !ok {
            w = 1
        }
        totalWeight += w
    }

    // 按权重选择
    r := rand.Intn(totalWeight)
    for _, inst := range instances {
        w, ok := b.weights[inst.InstanceID]
        if !ok {
            w = 1
        }
        r -= w
        if r < 0 {
            return inst, nil
        }
    }

    return instances[0], nil
}
```

#### 2.4.4 最少连接负载均衡

```go
type LeastConnectionsBalancer struct {
    mu          sync.Mutex
    connections map[string]int
}

func (b *LeastConnectionsBalancer) Select(instances []*ServiceInstance) (*ServiceInstance, error) {
    if len(instances) == 0 {
        return nil, fmt.Errorf("no instances available")
    }

    b.mu.Lock()
    defer b.mu.Unlock()

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

### 2.5 Timeout（超时处理）

#### 2.5.1 超时执行

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

#### 2.5.2 重试机制

```go
func RetryWithTimeout(ctx context.Context, timeout time.Duration, maxRetries int, fn func(ctx context.Context) error) error {
    ctx, cancel := context.WithTimeout(ctx, timeout)
    defer cancel()

    var lastErr error
    for i := 0; i < maxRetries; i++ {
        select {
        case <-ctx.Done():
            return fmt.Errorf("retry timed out after %d attempts: %w", i, ctx.Err())
        default:
        }

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

#### 2.5.3 熔断器

```go
type CircuitBreaker struct {
    mu               sync.Mutex
    failureCount     int
    successCount     int
    state            string // "closed", "open", "half-open"
    failureThreshold int
    successThreshold int
    timeout          time.Duration
    lastFailureTime  time.Time
}

func (cb *CircuitBreaker) Execute(fn func() error) error {
    cb.mu.Lock()
    state := cb.state
    cb.mu.Unlock()

    switch state {
    case "open":
        cb.mu.Lock()
        if time.Since(cb.lastFailureTime) > cb.timeout {
            cb.state = "half-open"
            cb.mu.Unlock()
            return cb.executeHalfOpen(fn)
        }
        cb.mu.Unlock()
        return fmt.Errorf("circuit breaker is open")
    case "half-open":
        return cb.executeHalfOpen(fn)
    default: // closed
        return cb.executeClosed(fn)
    }
}
```

### 2.6 Server（RPC 服务器）

#### 2.6.1 服务注册

```go
func (s *Server) Register(rcvr interface{}) error {
    svc := &Service{
        Name:    reflect.TypeOf(rcvr).Name(),
        Type:    reflect.TypeOf(rcvr),
        Methods: make(map[string]*ServiceMethod),
    }

    // 注册所有导出的方法
    for i := 0; i < svc.Type.NumMethod(); i++ {
        method := svc.Type.Method(i)
        mtype := method.Type

        // 方法必须有 3 个参数: receiver, context, args
        // 返回 1 个值: error
        if mtype.NumIn() != 3 || mtype.NumOut() != 1 {
            continue
        }

        // 检查返回类型是否为 error
        if !mtype.Out(0).Implements(reflect.TypeOf((*error)(nil)).Elem()) {
            continue
        }

        svc.Methods[method.Name] = &ServiceMethod{
            Name:      method.Name,
            Method:    method,
            ArgType:   mtype.In(1),
            ReplyType: mtype.In(2),
        }
    }

    s.services[svc.Name] = svc
    return nil
}
```

#### 2.6.2 请求处理

```go
func (s *Server) handleRequest(request *RpcRequest) *RpcResponse {
    svc, ok := s.services[request.ServiceName]
    if !ok {
        return &RpcResponse{
            RequestID: request.RequestID,
            Error:     fmt.Sprintf("service not found: %s", request.ServiceName),
        }
    }

    method, ok := svc.Methods[request.MethodName]
    if !ok {
        return &RpcResponse{
            RequestID: request.RequestID,
            Error:     fmt.Sprintf("method not found: %s", request.MethodName),
        }
    }

    // 创建参数
    arg := reflect.New(method.ArgType)
    if err := json.Unmarshal(request.Args, arg.Interface()); err != nil {
        return &RpcResponse{
            RequestID: request.RequestID,
            Error:     fmt.Sprintf("failed to unmarshal args: %v", err),
        }
    }

    // 创建 reply
    reply := reflect.New(method.ReplyType.Elem())

    // 调用方法
    ctx := context.Background()
    results := method.Method.Func.Call([]reflect.Value{
        reflect.ValueOf(svc.Type),
        reflect.ValueOf(ctx),
        arg.Elem(),
        reply,
    })

    // 检查返回值
    if len(results) > 0 && !results[0].IsNil() {
        err := results[0].Interface().(error)
        return &RpcResponse{
            RequestID: request.RequestID,
            Error:     err.Error(),
        }
    }

    // 序列化结果
    resultBytes, err := json.Marshal(reply.Interface())
    if err != nil {
        return &RpcResponse{
            RequestID: request.RequestID,
            Error:     fmt.Sprintf("failed to marshal result: %v", err),
        }
    }

    return &RpcResponse{
        RequestID: request.RequestID,
        Result:    resultBytes,
    }
}
```

### 2.7 Client（RPC 客户端）

#### 2.7.1 RPC 调用

```go
func (c *Client) Call(ctx context.Context, serviceName, methodName string, args interface{}, reply interface{}) error {
    // 获取服务实例
    instances, err := c.registry.GetService(serviceName)
    if err != nil {
        return fmt.Errorf("failed to get service: %w", err)
    }

    // 使用负载均衡选择实例
    instance, err := c.balancer.Select(instances)
    if err != nil {
        return fmt.Errorf("failed to select instance: %w", err)
    }

    // 带超时和重试的调用
    return timeout.RetryWithTimeout(ctx, c.config.TimeoutConfig.RequestTimeout, c.config.MaxRetries, func(ctx context.Context) error {
        return c.callInstance(ctx, instance, serviceName, methodName, args, reply)
    })
}
```

#### 2.7.2 实例调用

```go
func (c *Client) callInstance(ctx context.Context, instance *ServiceInstance, serviceName, methodName string, args interface{}, reply interface{}) error {
    // 获取或创建连接
    conn, err := c.getConnection(instance)
    if err != nil {
        return fmt.Errorf("failed to get connection: %w", err)
    }

    // 序列化参数
    argsBytes, err := json.Marshal(args)
    if err != nil {
        return fmt.Errorf("failed to marshal args: %w", err)
    }

    // 创建请求
    request := &RpcRequest{
        ServiceName: serviceName,
        MethodName:  methodName,
        Args:        argsBytes,
        RequestID:   generateRequestID(),
    }

    // 序列化请求
    requestBytes, err := json.Marshal(request)
    if err != nil {
        return fmt.Errorf("failed to marshal request: %w", err)
    }

    // 发送请求
    msg := &transport.Message{
        Payload: requestBytes,
    }

    if err := conn.Send(msg); err != nil {
        c.removeConnection(instance.InstanceID)
        return fmt.Errorf("failed to send request: %w", err)
    }

    // 接收响应
    respMsg, err := conn.Receive()
    if err != nil {
        c.removeConnection(instance.InstanceID)
        return fmt.Errorf("failed to receive response: %w", err)
    }

    // 解析响应
    var response RpcResponse
    if err := json.Unmarshal(respMsg.Payload, &response); err != nil {
        return fmt.Errorf("failed to unmarshal response: %w", err)
    }

    // 检查错误
    if response.Error != "" {
        return fmt.Errorf("rpc error: %s", response.Error)
    }

    // 反序列化结果
    if reply != nil {
        if err := json.Unmarshal(response.Result, reply); err != nil {
            return fmt.Errorf("failed to unmarshal result: %w", err)
        }
    }

    return nil
}
```

## 3. 关键技术点

### 3.1 反射机制

使用 Go 的反射机制来动态调用服务方法：

```go
// 获取方法类型
method := svc.Type.Method(i)
mtype := method.Type

// 创建参数
arg := reflect.New(method.ArgType)

// 创建返回值
reply := reflect.New(method.ReplyType.Elem())

// 调用方法
results := method.Method.Func.Call([]reflect.Value{
    reflect.ValueOf(svc.Type),
    reflect.ValueOf(ctx),
    arg.Elem(),
    reply,
})
```

### 3.2 并发安全

使用 `sync.RWMutex` 保护共享数据：

```go
type Server struct {
    mu       sync.RWMutex
    services map[string]*Service
}

func (s *Server) Register(rcvr interface{}) error {
    s.mu.Lock()
    defer s.mu.Unlock()
    // ...
}
```

### 3.3 连接管理

客户端维护连接池，复用 TCP 连接：

```go
func (c *Client) getConnection(instance *ServiceInstance) (transport.Conn, error) {
    c.mu.RLock()
    conn, ok := c.connections[instance.InstanceID]
    c.mu.RUnlock()

    if ok {
        return conn, nil
    }

    // 创建新连接
    c.mu.Lock()
    defer c.mu.Unlock()

    // 双重检查
    if conn, ok := c.connections[instance.InstanceID]; ok {
        return conn, nil
    }

    addr := fmt.Sprintf("%s:%d", instance.Address, instance.Port)
    t := transport.NewTCPTransport()
    conn, err := t.Dial(addr)
    if err != nil {
        return nil, err
    }

    c.connections[instance.InstanceID] = conn
    return conn, nil
}
```

### 3.4 优雅关闭

使用信号处理实现优雅关闭：

```go
sigCh := make(chan os.Signal, 1)
signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

go func() {
    <-sigCh
    fmt.Println("\nShutting down server...")
    if err := srv.Stop(); err != nil {
        log.Printf("Failed to stop server: %v", err)
    }
    os.Exit(0)
}()
```

## 4. 性能优化

### 4.1 连接池

复用 TCP 连接，减少连接建立开销。

### 4.2 缓冲区

使用缓冲区减少系统调用次数。

### 4.3 异步处理

使用 goroutine 异步处理请求。

## 5. 错误处理

### 5.1 错误类型

- 连接错误
- 超时错误
- 序列化错误
- 服务错误

### 5.2 错误传播

通过 RPC 响应中的 Error 字段传播错误。

## 6. 测试策略

### 6.1 单元测试

- 编解码器测试
- 负载均衡器测试
- 注册中心测试
- 超时处理测试

### 6.2 集成测试

- 端到端 RPC 调用测试
- 多服务器负载均衡测试
- 超时和重试测试

## 7. 部署考虑

### 7.1 配置管理

- 服务地址
- 超时配置
- 负载均衡策略

### 7.2 监控

- 请求成功率
- 请求延迟
- 并发连接数

### 7.3 日志

- 请求日志
- 错误日志
- 性能日志

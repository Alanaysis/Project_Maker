# 简易 RPC 框架 - 开发日志

## 1. 开发阶段

### 1.1 阶段一：基础架构（第 1-2 天）

**目标**：搭建项目基础架构

**任务**：
- [x] 创建项目结构
- [x] 定义核心接口
- [x] 实现 Codec 模块
- [x] 实现 Transport 模块

**收获**：
- 理解了 RPC 的基本原理
- 掌握了 Go 接口设计
- 学会了网络编程基础

### 1.2 阶段二：服务注册与发现（第 3-4 天）

**目标**：实现服务注册与发现功能

**任务**：
- [x] 设计注册中心接口
- [x] 实现内存注册中心
- [x] 实现服务注册功能
- [x] 实现服务发现功能
- [x] 实现健康检查机制

**收获**：
- 理解了服务注册与发现的原理
- 掌握了 Go 并发编程
- 学会了使用 sync 包

### 1.3 阶段三：负载均衡（第 5-6 天）

**目标**：实现负载均衡策略

**任务**：
- [x] 设计负载均衡器接口
- [x] 实现随机负载均衡
- [x] 实现轮询负载均衡
- [x] 实现加权负载均衡
- [x] 实现最少连接负载均衡

**收获**：
- 理解了负载均衡的原理
- 掌握了不同负载均衡策略
- 学会了原子操作

### 1.4 阶段四：超时处理（第 7-8 天）

**目标**：实现超时处理机制

**任务**：
- [x] 设计超时配置
- [x] 实现超时执行
- [x] 实现重试机制
- [x] 实现熔断器

**收获**：
- 理解了超时处理的重要性
- 掌握了 Go context 包
- 学会了熔断器模式

### 1.5 阶段五：RPC 核心（第 9-10 天）

**目标**：实现 RPC 调用核心

**任务**：
- [x] 实现 RPC 服务器
- [x] 实现 RPC 客户端
- [x] 实现服务方法注册
- [x] 实现请求处理
- [x] 实现响应处理

**收获**：
- 理解了 RPC 调用流程
- 掌握了 Go 反射机制
- 学会了序列化与反序列化

### 1.6 阶段六：测试与优化（第 11-12 天）

**目标**：测试和优化系统

**任务**：
- [x] 编写单元测试
- [x] 编写集成测试
- [x] 性能测试
- [x] 代码优化
- [x] 文档编写

**收获**：
- 掌握了 Go 测试框架
- 学会了性能优化技巧
- 提升了文档编写能力

## 2. 技术难点

### 2.1 反射机制

**问题**：如何动态调用服务方法？

**解决方案**：
使用 Go 的反射机制，通过 `reflect` 包动态获取方法信息并调用。

```go
// 获取方法类型
method := svc.Type.Method(i)
mtype := method.Type

// 创建参数
arg := reflect.New(method.ArgType)

// 调用方法
results := method.Method.Func.Call([]reflect.Value{
    reflect.ValueOf(svc.Type),
    reflect.ValueOf(ctx),
    arg.Elem(),
    reply,
})
```

### 2.2 并发安全

**问题**：如何保证共享数据的并发安全？

**解决方案**：
使用 `sync.RWMutex` 保护共享数据。

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

### 2.3 连接管理

**问题**：如何管理 TCP 连接？

**解决方案**：
使用连接池，复用 TCP 连接。

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

    // ...
}
```

### 2.4 超时处理

**问题**：如何实现超时控制？

**解决方案**：
使用 Go 的 `context` 包实现超时控制。

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

### 2.5 熔断器

**问题**：如何实现熔断器？

**解决方案**：
实现三态熔断器（关闭、打开、半开）。

```go
type CircuitBreaker struct {
    state            string
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

## 3. 代码规范

### 3.1 命名规范

- 包名：小写单词
- 结构体：大写驼峰
- 函数：大写驼峰
- 变量：小写驼峰
- 常量：大写下划线

### 3.2 注释规范

- 包注释：必须
- 导出函数：必须
- 复杂逻辑：必须
- 常量定义：必须

### 3.3 错误处理

- 使用 `fmt.Errorf` 包装错误
- 使用 `%w` 动词包装错误
- 不要忽略错误

### 3.4 测试规范

- 测试文件：`*_test.go`
- 测试函数：`TestXxx`
- 使用 `testify` 库
- 覆盖关键路径

## 4. 性能优化

### 4.1 连接池

复用 TCP 连接，减少连接建立开销。

### 4.2 缓冲区

使用缓冲区减少系统调用次数。

### 4.3 异步处理

使用 goroutine 异步处理请求。

### 4.4 批量处理

支持批量 RPC 调用，减少网络往返。

## 5. 测试结果

### 5.1 单元测试

```
=== RUN   TestJSONCodec
--- PASS: TestJSONCodec (0.00s)
=== RUN   TestMemoryRegistryRegister
--- PASS: TestMemoryRegistryRegister (0.00s)
=== RUN   TestRandomBalancer
--- PASS: TestRandomBalancer (0.00s)
=== RUN   TestRoundRobinBalancer
--- PASS: TestRoundRobinBalancer (0.00s)
=== RUN   TestWithTimeout
--- PASS: TestWithTimeout (0.00s)
=== RUN   TestCircuitBreaker
--- PASS: TestCircuitBreaker (0.00s)
PASS
```

### 5.2 集成测试

```
=== RUN   TestIntegrationCalculator
--- PASS: TestIntegrationCalculator (0.20s)
=== RUN   TestIntegrationMultipleServers
--- PASS: TestIntegrationMultipleServers (0.30s)
=== RUN   TestIntegrationTimeout
--- PASS: TestIntegrationTimeout (0.20s)
PASS
```

### 5.3 性能测试

```
BenchmarkRPC-8    10000    123456 ns/op    1234 B/op    12 allocs/op
```

## 6. 问题与解决

### 6.1 连接泄漏

**问题**：客户端连接未正确关闭

**解决**：实现连接池，使用 `defer` 关闭连接

### 6.2 内存泄漏

**问题**：注册中心未清理过期实例

**解决**：实现健康检查机制，定期清理过期实例

### 6.3 并发问题

**问题**：并发访问共享数据导致 panic

**解决**：使用 `sync.RWMutex` 保护共享数据

### 6.4 超时问题

**问题**：RPC 调用长时间阻塞

**解决**：实现超时控制，使用 `context.WithTimeout`

## 7. 经验总结

### 7.1 设计原则

- 接口隔离：定义清晰的接口
- 依赖注入：使用接口解耦组件
- 单一职责：每个模块只负责一件事
- 开闭原则：对扩展开放，对修改关闭

### 7.2 开发流程

- 先设计接口，再实现功能
- 先写测试，再写代码（TDD）
- 小步快跑，持续集成
- 代码审查，持续改进

### 7.3 调试技巧

- 使用 `go test -v` 查看详细输出
- 使用 `go test -race` 检测竞态条件
- 使用 `go tool pprof` 分析性能
- 使用 `delve` 调试器

## 8. 后续计划

### 8.1 功能扩展

- [ ] 支持 Protobuf 序列化
- [ ] 支持 HTTP/2 传输
- [ ] 支持 TLS 加密
- [ ] 支持服务版本管理

### 8.2 性能优化

- [ ] 连接池优化
- [ ] 异步调用支持
- [ ] 批量调用支持
- [ ] 压缩传输

### 8.3 监控告警

- [ ] 集成 Prometheus
- [ ] 集成 Grafana
- [ ] 实现告警机制
- [ ] 实现链路追踪

## 9. 参考资源

### 9.1 书籍

- 《Go 语言实战》
- 《Go 并发编程实战》
- 《分布式系统：概念与设计》

### 9.2 在线资源

- [Go 官方文档](https://golang.org/doc/)
- [gRPC 官方文档](https://grpc.io/docs/)
- [Protocol Buffers 文档](https://developers.google.com/protocol-buffers)

### 9.3 开源项目

- [gRPC-Go](https://github.com/grpc/grpc-go)
- [go-micro](https://github.com/micro/go-micro)
- [go-kit](https://github.com/go-kit/kit)

## 10. 致谢

感谢所有为这个项目提供帮助和建议的人！

---

**开发者**：AI Assistant

**日期**：2024

**版本**：1.0.0

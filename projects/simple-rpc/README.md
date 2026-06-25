# 简易 RPC 框架

## 项目概述

这是一个学习型的简易 RPC 框架实现项目，旨在深入理解 RPC（远程过程调用）的核心原理。通过实际编码实现 RPC 调用、服务注册与发现、负载均衡、超时处理和连接池等核心功能。

## 学习目标

- **理解 RPC 原理**：掌握 RPC 的核心概念和调用流程
- **掌握序列化**：理解不同序列化技术的优缺点（JSON、Protobuf、Gob）
- **学会服务注册**：实现服务注册与发现机制
- **实践负载均衡**：实现多种负载均衡策略
- **理解超时处理**：实现超时控制和熔断器模式
- **掌握连接池**：实现连接池管理和复用

## 技术栈

- **主语言**：Go 1.22+
- **序列化**：JSON / Protocol Buffers / Gob
- **传输**：TCP / HTTP
- **测试**：Go testing + testify

## 项目结构

```
simple-rpc/
├── cmd/
│   ├── server/
│   │   └── main.go              # 服务器入口
│   └── client/
│       └── main.go              # 客户端入口
├── internal/
│   ├── codec/
│   │   ├── codec.go             # JSON/Gob 编解码器
│   │   └── protobuf.go          # Protobuf 编解码器
│   ├── transport/
│   │   ├── transport.go         # TCP 传输层
│   │   └── http.go              # HTTP 传输层
│   ├── registry/
│   │   └── registry.go          # 注册中心实现
│   ├── loadbalancer/
│   │   └── balancer.go          # 负载均衡器实现
│   ├── pool/
│   │   └── pool.go              # 连接池实现
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
│   ├── pool_test.go             # 连接池测试
│   ├── codec_test.go            # 编解码器测试
│   ├── http_transport_test.go   # HTTP 传输测试
│   └── integration_test.go      # 集成测试
├── docs/
│   ├── 01_RESEARCH.md           # 市场调研
│   ├── 02_ARCHITECTURE.md       # 架构设计
│   ├── 03_IMPLEMENTATION.md     # 实现细节
│   ├── 04_TESTING.md            # 测试策略
│   └── 05_DEVELOPMENT.md        # 开发日志
├── LEARNING_NOTES.md            # 学习笔记
├── go.mod                       # Go 模块文件
└── README.md                    # 项目说明
```

## 快速开始

### 环境要求

- Go 1.22+

### 安装依赖

```bash
cd projects/simple-rpc
go mod tidy
```

### 运行测试

```bash
# 运行所有测试
go test ./...

# 运行特定测试
go test ./test/ -v -run TestIntegration

# 运行性能测试
go test ./test/ -bench=.
```

### 启动服务器

```bash
# 启动 Calculator 服务
go run cmd/server/main.go -addr localhost:8080 -service Calculator

# 启动 UserService 服务
go run cmd/server/main.go -addr localhost:8081 -service UserService
```

### 运行客户端

```bash
# 调用 Calculator 服务
go run cmd/client/main.go -service Calculator -balancer round_robin

# 调用 UserService 服务
go run cmd/client/main.go -service UserService -balancer random
```

## 核心概念

### 1. RPC 调用流程

```
客户端 → 序列化 → 网络传输 → 反序列化 → 服务端处理
```

### 2. 序列化支持

- **JSON**：人类可读，调试方便，适合开发阶段
- **Protocol Buffers**：高效二进制格式，适合生产环境
- **Gob**：Go 原生序列化，性能优秀

### 3. 传输层

- **TCP 传输**：自定义二进制协议，高性能
- **HTTP 传输**：标准 HTTP POST 请求，兼容性好

### 4. 服务注册与发现

- **服务注册**：服务启动时将自身信息注册到注册中心
- **服务发现**：客户端从注册中心获取服务实例列表
- **健康检查**：定期检测服务实例是否可用
- **Watch 机制**：监听服务变化并通知

### 5. 负载均衡策略

- **随机（Random）**：随机选择一个服务器
- **轮询（Round Robin）**：按顺序将请求分配给每个服务器
- **加权（Weighted）**：根据服务器权重分配请求
- **最少连接（Least Connections）**：选择当前连接数最少的服务器

### 6. 超时处理

- **连接超时**：建立连接的超时时间
- **请求超时**：等待响应的超时时间
- **重试机制**：失败后自动重试（支持指数退避）
- **熔断器**：当错误率达到阈值时，停止调用服务

### 7. 连接池

- **连接复用**：减少连接创建开销
- **最大连接数限制**：防止资源耗尽
- **空闲超时**：自动关闭空闲连接
- **健康检查**：定期检测连接可用性
- **并发安全**：支持多协程并发访问

## API 接口

### 1. 服务定义

```go
// Calculator 计算器服务
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

### 2. 服务注册

```go
// 创建服务器
srv := server.NewServer(addr, codec, registry)

// 注册服务
err := srv.Register(&Calculator{})
```

### 3. 客户端调用

```go
// 创建客户端
client := client.NewClient(registry, balancer, codec, config)

// 调用 RPC 方法
ctx := context.Background()
req := &AddRequest{A: 10, B: 20}
resp := &AddResponse{}
err := client.Call(ctx, "Calculator", "Add", req, resp)
```

### 4. 使用 Protobuf 编解码器

```go
// 创建 Protobuf 编解码器
c := codec.NewProtobufCodec()

// 用于服务器
srv := server.NewServer(addr, c, reg)
```

### 5. 使用 HTTP 传输

```go
// 创建 HTTP 传输
httpTransport := transport.NewHTTPTransport()

// 设置处理函数
httpTransport.SetHandler(func(msg *transport.Message) (*transport.Message, error) {
    // 处理消息
    return response, nil
})

// 监听并启动
httpTransport.Listen(":8080")
go httpTransport.Start()

// 客户端连接
conn := transport.NewHTTPRoundTripper("localhost:8080")
conn.Send(msg)
resp, err := conn.Receive()
```

### 6. 使用连接池

```go
// 创建连接池配置
config := &pool.PoolConfig{
    MaxSize:             10,
    MinSize:             2,
    MaxIdleTime:         5 * time.Minute,
    MaxLifetime:         30 * time.Minute,
    HealthCheckInterval: 1 * time.Minute,
}

// 创建连接池
p := pool.NewPool(addr, config, transport.NewTCPTransport())
defer p.Close()

// 获取连接
conn, err := p.Get()
if err != nil {
    log.Fatal(err)
}

// 使用连接
msg := &transport.Message{Payload: []byte("hello")}
conn.Send(msg)

// 归还连接
p.Put(conn)
```

## 配置说明

### 1. 客户端配置

```go
config := &client.ClientConfig{
    ServiceName:  "Calculator",
    BalancerName: "round_robin",
    TimeoutConfig: &timeout.TimeoutConfig{
        ConnectTimeout:   5 * time.Second,
        RequestTimeout:   10 * time.Second,
        KeepAliveTimeout: 30 * time.Second,
    },
    MaxRetries: 3,
}
```

### 2. 负载均衡器配置

```go
// 创建负载均衡器注册表
balancerReg := loadbalancer.NewBalancerRegistry()

// 获取负载均衡器
balancer, err := balancerReg.Get("round_robin")

// 可用的负载均衡器：
// - "random"           随机选择
// - "round_robin"      轮询
// - "weighted"         加权轮询
// - "least_connections" 最少连接
```

### 3. 连接池配置

```go
config := &pool.PoolConfig{
    MaxSize:             10,                // 最大连接数
    MinSize:             2,                 // 最小连接数
    MaxIdleTime:         5 * time.Minute,   // 最大空闲时间
    MaxLifetime:         30 * time.Minute,  // 最大连接生命周期
    HealthCheckInterval: 1 * time.Minute,   // 健康检查间隔
}
```

## 示例代码

### 1. 完整示例（TCP + JSON）

```go
package main

import (
    "context"
    "fmt"
    "log"
    "time"

    "github.com/simple-rpc/examples"
    "github.com/simple-rpc/internal/client"
    "github.com/simple-rpc/internal/codec"
    "github.com/simple-rpc/internal/loadbalancer"
    "github.com/simple-rpc/internal/registry"
    "github.com/simple-rpc/internal/server"
    "github.com/simple-rpc/internal/timeout"
)

func main() {
    // 创建注册中心
    reg := registry.NewMemoryRegistry()

    // 创建编解码器
    c := codec.NewJSONCodec()

    // 创建服务器
    srv := server.NewServer("localhost:8080", c, reg)

    // 注册服务
    srv.Register(&examples.Calculator{})

    // 启动服务器
    go srv.Start("localhost:8080")

    // 等待服务器启动
    time.Sleep(200 * time.Millisecond)

    // 创建客户端
    balancer := loadbalancer.NewRoundRobinBalancer()
    config := &client.ClientConfig{
        ServiceName:  "Calculator",
        BalancerName: "round_robin",
        TimeoutConfig: timeout.DefaultConfig(),
        MaxRetries:   3,
    }

    client := client.NewClient(reg, balancer, c, config)
    defer client.Close()

    // 调用 RPC 方法
    ctx := context.Background()
    addReq := &examples.AddRequest{A: 10, B: 20}
    addResp := &examples.AddResponse{}
    err := client.Call(ctx, "Calculator", "Add", addReq, addResp)
    if err != nil {
        log.Fatalf("Failed to call Add: %v", err)
    }

    fmt.Printf("Add: %d + %d = %d\n", addReq.A, addReq.B, addResp.Result)
}
```

### 2. HTTP 传输示例

```go
package main

import (
    "log"
    "time"

    "github.com/simple-rpc/internal/transport"
)

func main() {
    // 创建 HTTP 传输
    httpTransport := transport.NewHTTPTransport()

    // 设置处理函数
    httpTransport.SetHandler(func(msg *transport.Message) (*transport.Message, error) {
        // 处理请求
        return &transport.Message{
            Header:  map[string]string{"status": "ok"},
            Payload: msg.Payload,
        }, nil
    })

    // 监听
    if err := httpTransport.Listen(":8080"); err != nil {
        log.Fatal(err)
    }
    defer httpTransport.Close()

    // 启动 HTTP 服务器
    log.Println("HTTP server started on :8080")
    if err := httpTransport.Start(); err != nil {
        log.Fatal(err)
    }
}
```

## 学习路径

### 1. 第一阶段：理解 RPC 原理

- 学习 RPC 基本概念
- 理解 RPC 调用流程
- 了解序列化技术（JSON、Protobuf、Gob）

### 2. 第二阶段：实现基础架构

- 实现 Codec 模块（JSON、Gob、Protobuf）
- 实现 Transport 模块（TCP、HTTP）
- 实现 Registry 模块

### 3. 第三阶段：实现核心功能

- 实现 RPC 服务器
- 实现 RPC 客户端
- 实现服务注册与发现

### 4. 第四阶段：实现高级功能

- 实现负载均衡（随机、轮询、加权、最少连接）
- 实现超时处理和重试机制
- 实现熔断器模式
- 实现连接池管理

### 5. 第五阶段：测试与优化

- 编写单元测试
- 编写集成测试
- 性能测试与优化

## 参考资源

### 1. 书籍

- 《Go 语言实战》
- 《Go 并发编程实战》
- 《分布式系统：概念与设计》

### 2. 在线资源

- [Go 官方文档](https://golang.org/doc/)
- [gRPC 官方文档](https://grpc.io/docs/)
- [Protocol Buffers 文档](https://developers.google.com/protocol-buffers)

### 3. 开源项目

- [gRPC-Go](https://github.com/grpc/grpc-go)
- [go-micro](https://github.com/micro/go-micro)
- [go-kit](https://github.com/go-kit/kit)

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

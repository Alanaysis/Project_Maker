# MQTT Broker 开发指南

## 开发环境

### 前置要求

- Go 1.21 或更高版本
- Git

### 安装

```bash
# 克隆项目
git clone <repo-url>
cd projects/mqtt-broker

# 安装依赖
go mod tidy
```

## 项目结构

```
mqtt-broker/
├── cmd/
│   └── main.go              # 程序入口
├── internal/
│   ├── broker/
│   │   ├── broker.go        # Broker 核心逻辑
│   │   └── client.go        # 客户端管理
│   ├── packet/
│   │   └── packet.go        # 数据包编解码
│   └── topic/
│       └── manager.go       # 主题管理
├── tests/
│   ├── broker_test.go       # 集成测试
│   ├── packet_test.go       # 单元测试
│   └── topic_test.go        # 主题测试
└── docs/
    ├── 01-RESEARCH.md       # 协议研究
    ├── 02-DESIGN.md         # 架构设计
    ├── 03-IMPLEMENTATION.md # 实现细节
    ├── 04-TESTING.md        # 测试文档
    └── 05-DEVELOPMENT.md    # 开发指南
```

## 构建和运行

### 构建

```bash
# 构建可执行文件
go build -o mqtt-broker ./cmd

# 交叉编译
GOOS=linux GOARCH=amd64 go build -o mqtt-broker-linux ./cmd
GOOS=darwin GOARCH=arm64 go build -o mqtt-broker-mac ./cmd
```

### 运行

```bash
# 默认端口 1883
./mqtt-broker

# 自定义端口
MQTT_ADDR=:8883 ./mqtt-broker

# 后台运行
./mqtt-broker &
```

### 开发模式

```bash
# 直接运行（不构建）
go run ./cmd/main.go
```

## 测试

### 运行测试

```bash
# 运行所有测试
go test ./tests/ -v

# 运行特定测试
go test ./tests/ -v -run TestBrokerQoS2

# 检测竞态条件
go test ./tests/ -v -race

# 生成覆盖率
go test ./tests/ -coverprofile=coverage.out
go tool cover -html=coverage.out
```

### 编写测试

```go
func TestNewFeature(t *testing.T) {
    // 1. 设置测试环境
    b, addr := setupBroker(t)
    defer b.Stop()
    
    // 2. 创建客户端
    client := connectClient(t, addr, "test-client", true)
    defer client.close()
    
    // 3. 执行测试
    client.send(&packet.PublishPacket{
        TopicName: "test",
        Payload:   []byte("data"),
    })
    
    // 4. 验证结果
    msg, err := client.waitForPacket(packet.PUBLISH, 2*time.Second)
    if err != nil {
        t.Fatalf("Expected message: %v", err)
    }
    
    // 5. 断言
    if string(msg.(*packet.PublishPacket).Payload) != "data" {
        t.Errorf("Wrong payload")
    }
}
```

## 代码规范

### 1. 命名规范

- 包名: 小写单词，无下划线
- 结构体: PascalCase
- 函数/方法: PascalCase（公开）或 camelCase（私有）
- 常量: PascalCase 或全大写下划线

```go
// 好
type Client struct {}
func (c *Client) Send(data []byte) error {}
const MaxPacketSize = 256 * 1024 * 1024

// 不好
type mqtt_client struct {}
func (c *Client) send_data(data []byte) error {}
const MAX_PACKET_SIZE = 256 * 1024 * 1024
```

### 2. 错误处理

```go
// 好
result, err := doSomething()
if err != nil {
    return fmt.Errorf("failed to do something: %w", err)
}

// 不好
result, _ := doSomething()
```

### 3. 注释

```go
// 好
// Subscribe adds a subscriber to a topic pattern.
// It supports MQTT wildcards (+ and #).
func (m *Manager) Subscribe(topic string, sub *Subscriber) {
    // ...
}

// 不好
func (m *Manager) Subscribe(topic string, sub *Subscriber) {
    // subscribe to topic
}
```

### 4. 并发安全

```go
// 好
type SafeMap struct {
    mu sync.RWMutex
    m  map[string]string
}

func (s *SafeMap) Get(key string) string {
    s.mu.RLock()
    defer s.mu.RUnlock()
    return s.m[key]
}

// 不好
type UnsafeMap struct {
    m map[string]string
}

func (s *UnsafeMap) Get(key string) string {
    return s.m[key]
}
```

## 添加新功能

### 1. 添加新的数据包类型

```go
// 1. 定义结构体
type AuthPacket struct {
    ReasonCode byte
    Properties map[string]string
}

// 2. 实现 Packet 接口
func (p *AuthPacket) Type() byte { return AUTH }

func (p *AuthPacket) Encode() ([]byte, error) {
    // 编码逻辑
}

// 3. 添加解码函数
func decodeAuth(r io.Reader) (*AuthPacket, error) {
    // 解码逻辑
}

// 4. 在 ReadPacket 中注册
case AUTH:
    return decodeAuth(bodyReader)
```

### 2. 添加新的 QoS 等级

```go
// 1. 在 broker.go 中添加处理逻辑
func (b *Broker) handlePublish(client *Client, p *packet.PublishPacket) {
    switch p.QoS {
    case 0:
        // QoS 0
    case 1:
        // QoS 1
    case 2:
        // QoS 2
    case 3:
        // 新的 QoS 等级
    }
}

// 2. 添加测试
func TestBrokerQoS3(t *testing.T) {
    // 测试逻辑
}
```

### 3. 添加认证机制

```go
// 1. 定义认证接口
type Authenticator interface {
    Authenticate(username string, password []byte) bool
}

// 2. 实现认证器
type SimpleAuthenticator struct {
    users map[string]string
}

func (a *SimpleAuthenticator) Authenticate(username string, password []byte) bool {
    // 认证逻辑
}

// 3. 在 Broker 中集成
type Broker struct {
    auth Authenticator
}

// 4. 在 handleConnect 中验证
func (b *Broker) handleConnect(client *Client, p *packet.ConnectPacket) {
    if b.auth != nil {
        if !b.auth.Authenticate(p.Username, p.Password) {
            // 认证失败
        }
    }
}
```

## 性能优化

### 1. 内存池

```go
var bufferPool = sync.Pool{
    New: func() interface{} {
        return make([]byte, 4096)
    },
}

func getBuffer() []byte {
    return bufferPool.Get().([]byte)
}

func putBuffer(buf []byte) {
    bufferPool.Put(buf)
}
```

### 2. 批量处理

```go
func (b *Broker) routeMessageBatch(messages []*packet.PublishPacket) {
    // 批量处理消息
}
```

### 3. 异步处理

```go
func (b *Broker) handlePublishAsync(client *Client, p *packet.PublishPacket) {
    go func() {
        b.routeMessage(p)
    }()
}
```

## 调试

### 1. 启用调试日志

```go
const Debug = true

func debugLog(format string, args ...interface{}) {
    if Debug {
        log.Printf("[DEBUG] "+format, args...)
    }
}
```

### 2. 使用 pprof

```go
import _ "net/http/pprof"

go func() {
    http.ListenAndServe("localhost:6060", nil)
}()
```

### 3. 网络抓包

```bash
# tcpdump
sudo tcpdump -i lo port 1883 -A

# Wireshark
# 打开 Wireshark，选择 lo 接口，过滤 port 1883
```

## 部署

### 1. Docker

```dockerfile
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY . .
RUN go build -o mqtt-broker ./cmd

FROM alpine:latest
COPY --from=builder /app/mqtt-broker /usr/local/bin/
EXPOSE 1883
CMD ["mqtt-broker"]
```

### 2. systemd

```ini
[Unit]
Description=MQTT Broker
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/mqtt-broker
Restart=always

[Install]
WantedBy=multi-user.target
```

## 故障排除

### 1. 端口占用

```bash
# 查看端口占用
lsof -i :1883

# 杀死进程
kill -9 <PID>
```

### 2. 权限问题

```bash
# 使用非特权端口
MQTT_ADDR=:8883 ./mqtt-broker
```

### 3. 连接失败

- 检查防火墙设置
- 验证 Broker 是否正常运行
- 检查客户端配置

## 参考资源

- [Go 官方文档](https://golang.org/doc/)
- [MQTT 3.1.1 规范](https://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html)
- [Go 并发编程](https://golang.org/doc/effective_go#concurrency)

# MQTT Broker 设计文档

## 架构概述

```
┌─────────────────────────────────────────────────────────────────┐
│                        MQTT Broker                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   Listener   │  │   Client     │  │     Topic Manager    │  │
│  │              │  │   Manager    │  │                      │  │
│  │  TCP Accept  │  │              │  │  - Subscribe         │  │
│  │              │  │  - Connect   │  │  - Unsubscribe       │  │
│  │              │  │  - Disconnect│  │  - Wildcard Match    │  │
│  │              │  │  - Session   │  │  - Retained Messages │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Message Router                         │  │
│  │                                                          │  │
│  │   PUBLISH ──► Topic Match ──► QoS Processing ──► Deliver │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 模块设计

### 1. Packet 模块 (`internal/packet/`)

负责 MQTT 数据包的编解码。

**设计原则**:
- 每种包类型一个结构体
- 统一的 `Encode()` 和 `ReadPacket()` 接口
- 无状态设计，方便测试

**核心类型**:
```go
type Packet interface {
    Type() byte
    Encode() ([]byte, error)
}
```

**包类型**:
- `ConnectPacket` - 连接请求
- `ConnackPacket` - 连接确认
- `PublishPacket` - 发布消息
- `SubscribePacket` - 订阅请求
- `PubackPacket` - QoS 1 确认
- `PubrecPacket` - QoS 2 步骤 1
- `PubrelPacket` - QoS 2 步骤 2
- `PubcompPacket` - QoS 2 步骤 3
- `PingreqPacket` - 心跳请求
- `PingrespPacket` - 心跳响应
- `DisconnectPacket` - 断开连接

### 2. Topic 模块 (`internal/topic/`)

管理主题订阅和消息路由。

**功能**:
- 订阅管理（添加/删除订阅者）
- 主题匹配（支持 + 和 # 通配符）
- 保留消息存储
- 并发安全

**核心接口**:
```go
type Manager struct {
    subscribers map[string][]*Subscriber
    retained    map[string]*Message
}

func (m *Manager) Subscribe(topic string, sub *Subscriber)
func (m *Manager) GetSubscribers(topic string) []*Subscriber
func (m *Manager) SetRetained(topic string, msg *Message)
```

### 3. Broker 模块 (`internal/broker/`)

核心 Broker 逻辑，协调所有组件。

**功能**:
- TCP 连接管理
- 客户端会话管理
- 消息路由和分发
- QoS 状态管理
- 遗嘱消息处理

**Client 结构**:
```go
type Client struct {
    conn         net.Conn
    clientID     string
    cleanSession bool
    keepAlive    uint16
    
    // Will message
    willTopic    string
    willMessage  []byte
    willQoS      byte
    willRetain   bool
    willFlag     bool
    
    // QoS state
    inflight     map[uint16]*InflightMessage
    qos2State    map[uint16]byte
}
```

## 数据流

### 消息发布流程

```
1. 客户端发送 PUBLISH
       │
       ▼
2. Broker 解析包
       │
       ▼
3. QoS 处理
   ├── QoS 0: 直接路由
   ├── QoS 1: 路由 + 发送 PUBACK
   └── QoS 2: 状态机处理
       │
       ▼
4. 保留消息处理
       │
       ▼
5. 主题匹配
       │
       ▼
6. 分发给订阅者
```

### QoS 2 状态机

```
        ┌─────────────┐
        │   Pending   │  (初始状态)
        └──────┬──────┘
               │ 收到 PUBLISH
               ▼
        ┌─────────────┐
        │  Received   │  (发送 PUBREC)
        └──────┬──────┘
               │ 收到 PUBREL
               ▼
        ┌─────────────┐
        │  Completed  │  (发送 PUBCOMP)
        └─────────────┘
```

## 并发模型

### 连接处理

```
主 Goroutine
    │
    ├── Accept Goroutine
    │       │
    │       ├── Client 1 Goroutine
    │       ├── Client 2 Goroutine
    │       └── Client N Goroutine
    │
    └── Background Goroutines
            ├── Keepalive Checker
            └── Retransmission Handler
```

### 锁策略

- **Broker.clients**: `sync.RWMutex` 保护客户端映射
- **Client**: `sync.Mutex` 保护 QoS 状态
- **Topic.Manager**: `sync.RWMutex` 保护订阅和保留消息

## 错误处理

### 协议错误
- 无效包类型 → 关闭连接
- 格式错误 → 关闭连接
- 协议违规 → 发送 CONNACK 错误码

### 连接错误
- 超时 → 关闭连接，触发遗嘱消息
- 读写错误 → 关闭连接，触发遗嘱消息

## 性能考虑

### 内存优化
- 使用 `sync.Pool` 复用缓冲区
- 限制单个包大小
- 定期清理过期的 inflight 消息

### 并发优化
- 读写锁分离
- 无锁消息队列
- 批量消息处理

## 扩展点

### 可扩展的认证
```go
type Authenticator interface {
    Authenticate(username string, password []byte) bool
}
```

### 可扩展的存储
```go
type SessionStore interface {
    SaveSession(clientID string, session *Session) error
    LoadSession(clientID string) (*Session, error)
    DeleteSession(clientID string) error
}
```

### 可扩展的钩子
```go
type Hook interface {
    OnConnect(client *Client) error
    OnPublish(client *Client, msg *Message) error
    OnSubscribe(client *Client, topics []string) error
}
```

# MQTT Broker

一个用于学习的 MQTT 3.1.1 协议实现。

## 学习目标

- 理解 MQTT 协议的消息格式和流程
- 掌握发布/订阅模式的实现
- 学会 QoS 0/1/2 三种服务质量等级的机制
- 理解遗嘱消息（Last Will and Testament）的作用

## 技术栈

- **语言**: Go 1.21+
- **框架**: 无（纯标准库实现）
- **协议**: MQTT 3.1.1

## 项目结构

```
mqtt-broker/
├── cmd/
│   └── main.go              # 程序入口
├── internal/
│   ├── broker/
│   │   ├── broker.go        # Broker 核心逻辑
│   │   └── client.go        # 客户端连接管理
│   ├── packet/
│   │   └── packet.go        # MQTT 数据包编解码
│   └── topic/
│       └── manager.go       # 主题管理和匹配
├── tests/
│   ├── broker_test.go       # Broker 集成测试
│   ├── packet_test.go       # 数据包单元测试
│   └── topic_test.go        # 主题匹配测试
├── docs/                    # 学习文档
└── README.md
```

## 核心功能

### 1. MQTT 数据包

实现了 MQTT 3.1.1 定义的所有控制包：

| 类型 | 名称 | 用途 |
|------|------|------|
| CONNECT | 连接请求 | 客户端连接到 Broker |
| CONNACK | 连接确认 | Broker 响应连接 |
| PUBLISH | 发布消息 | 发送消息到主题 |
| PUBACK | 发布确认 | QoS 1 消息确认 |
| PUBREC | 发布收到 | QoS 2 第一步 |
| PUBREL | 发布释放 | QoS 2 第二步 |
| PUBCOMP | 发布完成 | QoS 2 第三步 |
| SUBSCRIBE | 订阅 | 订阅主题 |
| SUBACK | 订阅确认 | Broker 确认订阅 |
| UNSUBSCRIBE | 取消订阅 | 取消主题订阅 |
| UNSUBACK | 取消确认 | Broker 确认取消 |
| PINGREQ | 心跳请求 | 保持连接 |
| PINGRESP | 心跳响应 | Broker 响应心跳 |
| DISCONNECT | 断开连接 | 客户端断开 |

### 2. QoS 机制

**QoS 0 - 最多一次（At most once）**
```
Client → PUBLISH → Broker
```
消息可能丢失，不重试。

**QoS 1 - 至少一次（At least once）**
```
Client → PUBLISH → Broker
Client ← PUBACK  ← Broker
```
确保消息到达，可能重复。

**QoS 2 - 恰好一次（Exactly once）**
```
Client → PUBLISH → Broker
Client ← PUBREC   ← Broker
Client → PUBREL   → Broker
Client ← PUBCOMP  ← Broker
```
四次握手确保消息不丢失不重复。

### 3. 遗嘱消息（LWT）

客户端在连接时设置遗嘱消息。如果客户端异常断开（网络故障等），Broker 会自动发布遗嘱消息到指定主题。

```go
// 设置遗嘱消息
connect := &ConnectPacket{
    WillFlag:    true,
    WillTopic:   "client/status",
    WillMessage: []byte("offline"),
    WillQoS:     1,
    WillRetain:  true,
}
```

### 4. 主题通配符

- `+` - 匹配单个主题层级
  - `sensor/+/temperature` 匹配 `sensor/room1/temperature`
- `#` - 匹配任意数量的主题层级（必须在最后）
  - `sensor/#` 匹配 `sensor/room1/temperature`

### 5. 保留消息（Retained Messages）

发布消息时设置 Retain 标志，Broker 会保存消息。新订阅者订阅时会立即收到最新的保留消息。

## 运行

```bash
# 构建
go build -o mqtt-broker ./cmd

# 运行（默认端口 1883）
./mqtt-broker

# 自定义端口
MQTT_ADDR=:8883 ./mqtt-broker
```

## 测试

```bash
# 运行所有测试
go test ./tests/ -v

# 运行特定测试
go test ./tests/ -v -run TestBrokerQoS2
```

## 学习要点

### 协议设计

1. **固定头部**: 每个包都有 1 字节类型 + 可变长度的剩余长度
2. **可变头部**: 包特定的字段（如 PacketID）
3. **负载**: 消息内容

### QoS 状态机

QoS 2 实现了完整的状态机：
- `Pending` → 收到 PUBLISH
- `Received` → 发送 PUBREC
- `Completed` → 收到 PUBREL，发送 PUBCOMP

### 会话管理

- `CleanSession=true`: 每次连接都是新会话
- `CleanSession=false`: 保留订阅和未确认消息

## 参考资料

- [MQTT 3.1.1 规范](https://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html)
- [MQTT 协议入门](https://www.hivemq.com/mqtt-essentials/)

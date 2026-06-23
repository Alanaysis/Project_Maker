# MQTT Broker 学习笔记

## 项目概述

本项目实现了一个 MQTT 3.1.1 协议的 Broker（服务器），用于学习：
- MQTT 协议的工作原理
- 发布/订阅模式的实现
- QoS 机制的设计
- 遗嘱消息的作用

## 核心知识点

### 1. MQTT 协议基础

**什么是 MQTT？**
- 轻量级消息传输协议
- 基于发布/订阅模式
- 专为物联网设计
- 最小包头只有 2 字节

**协议特点**：
- 低带宽消耗
- 低代码 footprint
- 支持三种 QoS 等级
- 支持遗嘱消息
- 支持保留消息

### 2. 发布/订阅模式

**传统请求/响应模式**：
```
Client A → Server → Client B
Client B → Server → Client A
```

**发布/订阅模式**：
```
Publisher → Broker → Subscriber 1
                  → Subscriber 2
                  → Subscriber 3
```

**优势**：
- 发布者和订阅者解耦
- 支持一对多通信
- 更好的扩展性

### 3. 数据包格式

**固定头部**（2-5 字节）：
```
+-------+-------+
| Type  | Flags |  ← 1 字节
+-------+-------+
| Remaining Len |  ← 1-4 字节
+-------+-------+
```

**可变长度编码**：
- 每字节低 7 位存储数据
- 最高位为 1 表示有后续字节
- 最大 4 字节，可表示 256MB

**示例**：
- 值 0-127: 1 字节
- 值 128-16383: 2 字节

### 4. QoS 机制

**QoS 0 - 最多一次**：
```
Client → PUBLISH → Broker
```
- 最快，不保证到达
- 适合传感器数据

**QoS 1 - 至少一次**：
```
Client → PUBLISH → Broker
Client ← PUBACK  ← Broker
```
- 保证到达，可能重复
- 适合大多数场景

**QoS 2 - 恰好一次**：
```
Client → PUBLISH → Broker
Client ← PUBREC  ← Broker
Client → PUBREL  → Broker
Client ← PUBCOMP ← Broker
```
- 四次握手
- 保证不丢失不重复
- 适合计费系统

**QoS 降级**：
- 发布者 QoS 2，订阅者 QoS 1 → 实际使用 QoS 1
- 取较低值确保兼容性

### 5. 遗嘱消息（LWT）

**作用**：
- 客户端异常断开时自动发布的消息
- 通知其他客户端连接状态

**设置**：
```go
CONNECT {
    WillFlag:    true,
    WillTopic:   "client/status",
    WillMessage: []byte("offline"),
    WillQoS:     1,
    WillRetain:  true,
}
```

**触发条件**：
- 网络连接异常断开
- 服务端主动断开
- 心跳超时

**不触发**：
- 客户端正常发送 DISCONNECT

### 6. 保留消息

**作用**：
- Broker 保存最后一条保留消息
- 新订阅者立即收到最新状态

**使用**：
```go
// 发布保留消息
PUBLISH {
    Topic:   "sensor/temp",
    Payload: "25",
    Retain:  true,
}

// 新订阅者订阅时立即收到
SUBSCRIBE "sensor/temp"
// → 立即收到 "25"
```

**清除**：
- 发送空负载的保留消息

### 7. 主题通配符

**单层通配符 `+`**：
```
sensor/+/temperature
├── sensor/room1/temperature ✓
├── sensor/room2/temperature ✓
└── sensor/room1/humidity    ✗
```

**多层通配符 `#`**：
```
sensor/#
├── sensor/temperature       ✓
├── sensor/room1/temperature ✓
└── sensor/a/b/c/d           ✓
```

**规则**：
- `+` 匹配单个层级
- `#` 匹配任意数量层级（必须在最后）
- 主题区分大小写

## 实现细节

### 1. 数据包编解码

**编码流程**：
```
1. 构建可变头部和负载
2. 计算剩余长度
3. 编码剩余长度（可变长度编码）
4. 构建固定头部
5. 拼接所有部分
```

**解码流程**：
```
1. 读取固定头部第一个字节
2. 解析包类型和标志
3. 解码剩余长度
4. 读取剩余字节
5. 根据类型解析
```

### 2. 主题匹配算法

**精确匹配**：
```go
if pattern == topic {
    return true
}
```

**通配符匹配**：
```go
patternParts := strings.Split(pattern, "/")
topicParts := strings.Split(topic, "/")

for i, part := range patternParts {
    if part == "#" {
        return true
    }
    if i >= len(topicParts) {
        return false
    }
    if part != "+" && part != topicParts[i] {
        return false
    }
}
return len(patternParts) == len(topicParts)
```

### 3. QoS 2 状态机

**状态**：
- `Pending`: 初始状态
- `Received`: 收到 PUBLISH，发送 PUBREC
- `Completed`: 收到 PUBREL，发送 PUBCOMP

**实现**：
```go
state := client.GetQoS2State(packetID)
switch state {
case qos2Pending:
    client.SetQoS2State(packetID, qos2Received)
    // 路由消息
    // 发送 PUBREC
case qos2Received:
    // 重复的 PUBLISH，重发 PUBREC
}
```

### 4. 并发安全

**读写锁**：
```go
type Broker struct {
    mu      sync.RWMutex
    clients map[string]*Client
}

// 读操作
func (b *Broker) GetClient(id string) *Client {
    b.mu.RLock()
    defer b.mu.RUnlock()
    return b.clients[id]
}

// 写操作
func (b *Broker) SetClient(id string, client *Client) {
    b.mu.Lock()
    defer b.mu.Unlock()
    b.clients[id] = client
}
```

**客户端锁**：
```go
type Client struct {
    mu       sync.Mutex
    inflight map[uint16]*InflightMessage
}
```

## 设计决策

### 1. 为什么使用接口？

```go
type Packet interface {
    Type() byte
    Encode() ([]byte, error)
}
```

**优势**：
- 统一的处理方式
- 易于扩展新包类型
- 方便测试

### 2. 为什么使用内部包？

```
internal/
├── broker/    # 核心逻辑
├── packet/    # 数据包
└── topic/     # 主题管理
```

**优势**：
- 封装实现细节
- 避免外部依赖
- 清晰的模块边界

### 3. 为什么使用回调？

```go
type Subscriber struct {
    Callback func(msg *Message)
}
```

**优势**：
- 灵活的消息处理
- 易于测试
- 支持异步处理

## 遇到的问题

### 1. 可变长度编码

**问题**：如何正确编码和解码剩余长度？

**解决**：
```go
// 编码
func encodeLength(length int) []byte {
    var encoded []byte
    for {
        digit := byte(length % 128)
        length /= 128
        if length > 0 {
            digit |= 0x80
        }
        encoded = append(encoded, digit)
        if length == 0 {
            break
        }
    }
    return encoded
}

// 解码
func decodeLength(r io.Reader) (int, error) {
    var value int
    multiplier := 1
    for {
        digit := readByte(r)
        value += int(digit & 0x7F) * multiplier
        if digit & 0x80 == 0 {
            break
        }
        multiplier *= 128
    }
    return value, nil
}
```

### 2. QoS 2 状态管理

**问题**：如何正确管理 QoS 2 的四次握手状态？

**解决**：
```go
type Client struct {
    qos2State map[uint16]byte
}

func (c *Client) SetQoS2State(packetID uint16, state byte) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.qos2State[packetID] = state
}
```

### 3. 遗嘱消息触发

**问题**：如何区分正常断开和异常断开？

**解决**：
```go
func (b *Broker) handleDisconnectClean(client *Client) {
    // 正常断开：清除遗嘱标志
    client.willFlag = false
}

func (b *Broker) handleDisconnect(client *Client) {
    // 异常断开：触发遗嘱消息
    if client.willFlag {
        b.publishWill(client)
    }
}
```

### 4. 并发测试

**问题**：如何测试并发场景？

**解决**：
```go
func TestBrokerMultipleSubscribers(t *testing.T) {
    // 创建多个订阅者
    subs := make([]*testClient, 3)
    for i := 0; i < 3; i++ {
        subs[i] = connectClient(t, addr, fmt.Sprintf("sub-%d", i), true)
    }
    
    // 发布消息
    pub.send(&packet.PublishPacket{...})
    
    // 验证所有订阅者都收到
    for _, sub := range subs {
        sub.waitForPacket(packet.PUBLISH, 2*time.Second)
    }
}
```

## 学习收获

### 1. 协议设计

- 理解了 MQTT 的轻量级设计
- 学会了可变长度编码
- 掌握了 QoS 状态机

### 2. 网络编程

- 学会了 TCP 连接管理
- 理解了并发安全
- 掌握了错误处理

### 3. 系统设计

- 学会了发布/订阅模式
- 理解了消息路由
- 掌握了会话管理

### 4. 测试方法

- 学会了单元测试
- 理解了集成测试
- 掌握了并发测试

## 下一步

### 1. 功能扩展

- 支持 MQTT 5.0
- 添加认证机制
- 实现持久化存储

### 2. 性能优化

- 使用内存池
- 批量消息处理
- 异步消息分发

### 3. 监控和运维

- 添加指标收集
- 实现日志系统
- 支持配置文件

## 参考资源

1. [MQTT 3.1.1 规范](https://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html)
2. [HiveMQ MQTT Essentials](https://www.hivemq.com/mqtt-essentials/)
3. [Go 并发编程](https://golang.org/doc/effective_go#concurrency)
4. [Go 网络编程](https://golang.org/pkg/net/)

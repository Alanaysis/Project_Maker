# MQTT Broker 实现细节

## 1. 数据包编解码

### 可变长度编码

MQTT 使用可变长度编码表示剩余长度字段：

```go
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
```

**原理**:
- 每个字节的低 7 位存储数据
- 最高位为 1 表示还有后续字节
- 最多 4 字节，可表示 268,435,455 字节

### 字符串编码

MQTT 字符串使用 2 字节长度前缀：

```go
func encodeString(s string) []byte {
    b := make([]byte, 2+len(s))
    binary.BigEndian.PutUint16(b[0:2], uint16(len(s)))
    copy(b[2:], s)
    return b
}
```

### 固定头部解析

```go
func ReadPacket(r io.Reader) (Packet, *FixedHeader, error) {
    // 1. 读取第一个字节
    headerBuf := make([]byte, 1)
    io.ReadFull(r, headerBuf)
    
    // 2. 解析类型和标志
    fh := &FixedHeader{
        Type:   (headerBuf[0] >> 4) & 0x0F,
        Dup:    (headerBuf[0] & 0x08) != 0,
        QoS:    (headerBuf[0] >> 1) & 0x03,
        Retain: (headerBuf[0] & 0x01) != 0,
    }
    
    // 3. 读取剩余长度
    remaining := decodeLength(r)
    
    // 4. 根据类型解析
    switch fh.Type {
    case CONNECT:
        return decodeConnect(r, fh)
    // ...
    }
}
```

## 2. QoS 实现

### QoS 0

最简单的实现：

```go
case 0:
    // 直接路由，不做任何确认
    b.routeMessage(p)
```

### QoS 1

需要确认机制：

```go
case 1:
    // 路由消息
    b.routeMessage(p)
    
    // 发送 PUBACK
    puback := &packet.PubackPacket{PacketID: p.PacketID}
    data, _ := puback.Encode()
    client.Send(data)
```

### QoS 2

四次握手状态机：

```go
case 2:
    state := client.GetQoS2State(p.PacketID)
    if state == qos2Pending {
        // 第一次收到 PUBLISH
        client.SetQoS2State(p.PacketID, qos2Received)
        b.routeMessage(p)
    }
    
    // 发送 PUBREC
    pubrec := &packet.PubrecPacket{PacketID: p.PacketID}
    data, _ := pubrec.Encode()
    client.Send(data)

// 收到 PUBREL
func (b *Broker) handlePubrel(client *Client, p *packet.PubrelPacket) {
    client.RemoveQoS2State(p.PacketID)
    pubcomp := &packet.PubcompPacket{PacketID: p.PacketID}
    data, _ := pubcomp.Encode()
    client.Send(data)
}
```

### QoS 降级

当发布者和订阅者的 QoS 不同时，取较低值：

```go
// 使用较低的 QoS
qos := pub.QoS
if sub.QoS < qos {
    qos = sub.QoS
}
```

## 3. 主题匹配

### 精确匹配

```go
func matchTopic(pattern, topic string) bool {
    if pattern == topic {
        return true
    }
    // ...
}
```

### 通配符 `+`

匹配单个层级：

```go
patternParts := strings.Split(pattern, "/")
topicParts := strings.Split(topic, "/")

for i, part := range patternParts {
    if part == "+" {
        continue // 匹配任意单个层级
    }
    if part != topicParts[i] {
        return false
    }
}
```

### 通配符 `#`

匹配任意数量层级：

```go
for i, part := range patternParts {
    if part == "#" {
        return true // 匹配剩余所有层级
    }
    // ...
}
```

## 4. 遗嘱消息

### 设置遗嘱

客户端在 CONNECT 包中设置遗嘱：

```go
connect := &ConnectPacket{
    WillFlag:    true,
    WillTopic:   "client/status",
    WillMessage: []byte("offline"),
    WillQoS:     1,
    WillRetain:  true,
}
```

### 触发条件

遗嘱消息在以下情况触发：
- 网络连接异常断开
- 服务端主动断开
- 心跳超时

**不触发**的情况：
- 客户端正常发送 DISCONNECT

### 实现

```go
func (b *Broker) handleDisconnect(client *Client) {
    if client.willFlag {
        b.publishWill(client)
    }
}

func (b *Broker) publishWill(client *Client) {
    pub := &packet.PublishPacket{
        TopicName: client.willTopic,
        Payload:   client.willMessage,
        QoS:       client.willQoS,
        Retain:    client.willRetain,
    }
    b.routeMessage(pub)
}
```

## 5. 保留消息

### 存储

```go
type Manager struct {
    retained map[string]*Message // topic -> retained message
}

func (m *Manager) SetRetained(topic string, msg *Message) {
    if len(msg.Payload) == 0 {
        delete(m.retained, topic) // 空负载删除保留消息
    } else {
        m.retained[topic] = msg
    }
}
```

### 发送保留消息

新订阅者订阅时，立即发送匹配的保留消息：

```go
func (b *Broker) handleSubscribe(client *Client, p *packet.SubscribePacket) {
    for i, t := range p.Topics {
        // 订阅主题
        b.topics.Subscribe(t, sub)
        
        // 发送保留消息
        retained := b.topics.GetRetainedForPattern(t)
        for _, msg := range retained {
            b.deliverToClient(client, msg)
        }
    }
}
```

## 6. 连接管理

### 连接流程

```go
func (b *Broker) handleConnect(client *Client, p *packet.ConnectPacket) {
    // 1. 验证协议
    if p.ProtocolName != "MQTT" || p.ProtocolLevel != 4 {
        // 返回错误
    }
    
    // 2. 处理已有会话
    if existing, ok := b.clients[p.ClientID]; ok {
        if p.CleanSession {
            existing.Close()
        } else {
            // 恢复会话
        }
    }
    
    // 3. 注册客户端
    b.clients[p.ClientID] = client
    
    // 4. 发送 CONNACK
    connack := &ConnackPacket{ReturnCode: ConnAccepted}
    client.Send(connack.Encode())
}
```

### 心跳机制

```go
// 设置读取超时
if client.keepAlive > 0 {
    deadline := time.Duration(client.keepAlive)*3/2 + 5
    conn.SetReadDeadline(time.Now().Add(deadline * time.Second))
}

// 处理心跳
func (b *Broker) handlePingreq(client *Client) {
    resp := &packet.PingrespPacket{}
    data, _ := resp.Encode()
    client.Send(data)
}
```

## 7. 并发安全

### 读写锁

```go
type Broker struct {
    mu      sync.RWMutex
    clients map[string]*Client
}

// 读操作使用 RLock
func (b *Broker) ClientCount() int {
    b.mu.RLock()
    defer b.mu.RUnlock()
    return len(b.clients)
}

// 写操作使用 Lock
func (b *Broker) registerClient(client *Client) {
    b.mu.Lock()
    defer b.mu.Unlock()
    b.clients[client.ClientID()] = client
}
```

### 客户端锁

```go
type Client struct {
    mu       sync.Mutex
    inflight map[uint16]*InflightMessage
}

func (c *Client) AddInflight(msg *InflightMessage) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.inflight[msg.PacketID] = msg
}
```

## 8. 错误处理

### 协议错误

```go
// 无效协议
if p.ProtocolName != "MQTT" {
    connack := &ConnackPacket{ReturnCode: ConnRefusedProtocol}
    client.Send(connack.Encode())
    return
}

// 无效客户端 ID
if len(p.ClientID) == 0 && !p.CleanSession {
    connack := &ConnackPacket{ReturnCode: ConnRefusedIdentifier}
    client.Send(connack.Encode())
    return
}
```

### 连接错误

```go
// 读取错误
pkt, _, err := packet.ReadPacket(conn)
if err != nil {
    if netErr, ok := err.(net.Error); ok && netErr.Timeout() {
        // 超时，触发遗嘱消息
    }
    return
}
```

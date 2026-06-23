# MQTT Broker 测试文档

## 测试策略

### 1. 单元测试
- 数据包编解码测试
- 主题匹配测试
- 独立模块功能测试

### 2. 集成测试
- 完整的客户端-服务器交互
- QoS 流程测试
- 遗嘱消息测试
- 保留消息测试

### 3. 并发测试
- 多客户端同时连接
- 并发订阅和发布
- 竞态条件检测

## 测试覆盖

### 数据包测试 (`packet_test.go`)

| 测试用例 | 描述 |
|---------|------|
| `TestConnectPacketEncodeDecode` | CONNECT 包编解码 |
| `TestConnectPacketWithWill` | 带遗嘱的 CONNECT 包 |
| `TestConnackPacketEncodeDecode` | CONNACK 包编解码 |
| `TestPublishPacketQoS0` | QoS 0 PUBLISH 包 |
| `TestPublishPacketQoS1` | QoS 1 PUBLISH 包 |
| `TestPublishPacketQoS2` | QoS 2 PUBLISH 包 |
| `TestPubackPacket` | PUBACK 包 |
| `TestSubscribePacket` | SUBSCRIBE 包 |
| `TestPingreqPingresp` | 心跳包 |
| `TestDisconnectPacket` | DISCONNECT 包 |

### 主题测试 (`topic_test.go`)

| 测试用例 | 描述 |
|---------|------|
| `TestExactMatch` | 精确匹配 |
| `TestWildcardPlus` | `+` 通配符 |
| `TestWildcardHash` | `#` 通配符 |
| `TestMultipleSubscribers` | 多订阅者 |
| `TestDuplicateSubscription` | 重复订阅处理 |
| `TestUnsubscribe` | 取消订阅 |
| `TestUnsubscribeAll` | 取消所有订阅 |
| `TestRetainedMessage` | 保留消息 |
| `TestRetainedMessageWildcard` | 通配符匹配保留消息 |

### Broker 集成测试 (`broker_test.go`)

| 测试用例 | 描述 |
|---------|------|
| `TestBrokerConnectDisconnect` | 连接和断开 |
| `TestBrokerSubscribePublish` | 基本发布订阅 |
| `TestBrokerQoS1` | QoS 1 流程 |
| `TestBrokerQoS2` | QoS 2 四次握手 |
| `TestBrokerWillMessage` | 遗嘱消息触发 |
| `TestBrokerNoWillOnCleanDisconnect` | 正常断开不触发遗嘱 |
| `TestBrokerRetainedMessage` | 保留消息 |
| `TestBrokerPingPong` | 心跳机制 |
| `TestBrokerWildcardSubscription` | 通配符订阅 |
| `TestBrokerUnsubscribe` | 取消订阅 |
| `TestBrokerMultipleSubscribers` | 多订阅者分发 |

## 运行测试

### 运行所有测试

```bash
go test ./tests/ -v
```

### 运行特定测试

```bash
# 运行 QoS 2 测试
go test ./tests/ -v -run TestBrokerQoS2

# 运行数据包测试
go test ./tests/ -v -run TestPacket

# 运行主题测试
go test ./tests/ -v -run TestTopic
```

### 检测竞态条件

```bash
go test ./tests/ -v -race
```

### 生成覆盖率报告

```bash
go test ./tests/ -coverprofile=coverage.out
go tool cover -html=coverage.out
```

## 测试辅助工具

### testClient

用于模拟 MQTT 客户端：

```go
type testClient struct {
    conn     net.Conn
    received []packet.Packet
    mu       sync.Mutex
}

// 创建客户端并连接
func newTestClient(addr string) (*testClient, error)

// 发送数据包
func (tc *testClient) send(pkt packet.Packet) error

// 等待接收特定类型的数据包
func (tc *testClient) waitForPacket(pktType byte, timeout time.Duration) (packet.Packet, error)

// 获取所有接收到的数据包
func (tc *testClient) getReceived() []packet.Packet
```

### setupBroker

创建测试用的 Broker：

```go
func setupBroker(t *testing.T) (*broker.Broker, string) {
    b := broker.New()
    // 使用随机端口
    ln, _ := net.Listen("tcp", "127.0.0.1:0")
    addr := ln.Addr().String()
    ln.Close()
    
    b.Start(addr)
    return b, addr
}
```

### connectClient

创建并认证客户端：

```go
func connectClient(t *testing.T, addr string, clientID string, cleanSession bool) *testClient {
    tc := newTestClient(addr)
    
    // 发送 CONNECT
    tc.send(&ConnectPacket{...})
    
    // 等待 CONNACK
    tc.waitForPacket(CONNACK, 2*time.Second)
    
    return tc
}
```

## 测试场景

### 1. QoS 2 完整流程

```
1. 订阅者订阅 QoS 2 主题
2. 发布者发送 QoS 2 消息
3. 验证四次握手:
   - 发布者收到 PUBREC
   - 发布者发送 PUBREL
   - 发布者收到 PUBCOMP
4. 验证订阅者收到消息
```

### 2. 遗嘱消息触发

```
1. 订阅者订阅遗嘱主题
2. 客户端设置遗嘱消息
3. 客户端异常断开（直接关闭连接）
4. 验证订阅者收到遗嘱消息
```

### 3. 正常断开不触发遗嘱

```
1. 订阅者订阅遗嘱主题
2. 客户端设置遗嘱消息
3. 客户端发送 DISCONNECT
4. 验证订阅者未收到遗嘱消息
```

### 4. 保留消息

```
1. 发布者发送带 Retain 标志的消息
2. 新订阅者订阅该主题
3. 验证新订阅者立即收到保留消息
```

### 5. 多订阅者分发

```
1. 创建 3 个订阅者订阅同一主题
2. 发布者发送消息
3. 验证所有订阅者都收到消息
```

## 调试技巧

### 1. 启用详细日志

在 Broker 代码中添加日志：

```go
log.Printf("Received %T from %s", pkt, client.ClientID())
```

### 2. 使用网络抓包

```bash
# 使用 tcpdump 抓包
sudo tcpdump -i lo port 1883 -A

# 使用 Wireshark 分析
```

### 3. 使用 MQTT 客户端工具

```bash
# mosquitto 客户端
mosquitto_sub -t "test/topic"
mosquitto_pub -t "test/topic" -m "hello"
```

## 常见问题

### 1. 测试超时

- 检查 Broker 是否正确启动
- 增加 `waitForPacket` 的超时时间
- 检查是否有死锁

### 2. 竞态条件

- 使用 `-race` 标志运行测试
- 检查锁的使用是否正确
- 避免在持锁时进行阻塞操作

### 3. 消息丢失

- 检查主题匹配是否正确
- 验证 QoS 流程是否完整
- 检查客户端是否正确读取数据

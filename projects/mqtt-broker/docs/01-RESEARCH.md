# MQTT 协议研究

## 什么是 MQTT

MQTT（Message Queuing Telemetry Transport）是一种轻量级的消息传输协议，专为低带宽、高延迟或不可靠的网络环境设计。它广泛应用于物联网（IoT）、移动应用和实时通信场景。

## 协议特点

### 1. 轻量级
- 最小包头只有 2 字节
- 适合嵌入式设备和低带宽网络

### 2. 发布/订阅模式
- 发布者和订阅者解耦
- 通过主题（Topic）路由消息
- 支持一对多通信

### 3. 三种 QoS 等级
- **QoS 0**: 最多一次，消息可能丢失
- **QoS 1**: 至少一次，消息可能重复
- **QoS 2**: 恰好一次，保证消息到达且不重复

### 4. 遗嘱消息
- 客户端异常断开时自动发布的消息
- 用于通知其他客户端连接状态

### 5. 保留消息
- Broker 保存最后一条保留消息
- 新订阅者立即收到最新状态

## 协议架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Publisher   │     │   Broker    │     │ Subscriber  │
│             │     │             │     │             │
│  PUBLISH ──►│────►│  路由消息   │────►│◄── 消息     │
│             │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
```

## 数据包格式

### 固定头部（Fixed Header）

```
+-------+-------+-------+-------+-------+-------+-------+-------+
|  Bit  │  7    │  6    │  5    │  4    │  3    │  2    │  1    │  0    │
+-------+-------+-------+-------+-------+-------+-------+-------+-------+
| Byte 1│       Packet Type         │  DUP  │    QoS      │ Retain│
+-------+-------+-------+-------+-------+-------+-------+-------+-------+
| Byte 2│                     Remaining Length                          │
+-------+-------+-------+-------+-------+-------+-------+-------+-------+
```

- **Packet Type** (4 bits): 控制包类型
- **DUP** (1 bit): 重发标志
- **QoS** (2 bits): 服务质量等级
- **Retain** (1 bit): 保留消息标志
- **Remaining Length**: 可变长度编码的剩余字节数

### 可变长度编码

剩余长度使用可变长度编码方案：
- 每个字节的低 7 位存储数据
- 最高位为 1 表示还有后续字节
- 最大 4 字节，可表示 256MB

```
值 0-127:     1 字节
值 128-16383: 2 字节
```

## 主题（Topics）

### 主题层级
- 使用 `/` 分隔层级
- 例如: `home/livingroom/temperature`

### 通配符
- `+`: 匹配单个层级
  - `home/+/temperature` 匹配 `home/livingroom/temperature`
- `#`: 匹配任意数量层级（必须在最后）
  - `home/#` 匹配 `home/livingroom/temperature`

### 主题规则
- 空格不允许
- 以 `$` 开头的主题为系统主题
- 主题区分大小写

## 连接流程

```
Client                     Broker
  │                          │
  │──── CONNECT ────────────►│
  │                          │
  │◄─── CONNACK ─────────────│
  │                          │
  │──── SUBSCRIBE ──────────►│
  │                          │
  │◄─── SUBACK ──────────────│
  │                          │
  │◄─── PUBLISH ─────────────│  (如果有保留消息)
  │                          │
```

## QoS 详细流程

### QoS 0
```
Publisher              Broker               Subscriber
    │                    │                      │
    │── PUBLISH ────────►│                      │
    │                    │── PUBLISH ──────────►│
    │                    │                      │
```

### QoS 1
```
Publisher              Broker               Subscriber
    │                    │                      │
    │── PUBLISH ────────►│                      │
    │◄── PUBACK ─────────│                      │
    │                    │── PUBLISH ──────────►│
    │                    │◄── PUBACK ───────────│
    │                    │                      │
```

### QoS 2
```
Publisher              Broker               Subscriber
    │                    │                      │
    │── PUBLISH ────────►│                      │
    │◄── PUBREC ─────────│                      │
    │── PUBREL ─────────►│                      │
    │◄── PUBCOMP ────────│                      │
    │                    │── PUBLISH ──────────►│
    │                    │◄── PUBREC ───────────│
    │                    │── PUBREL ───────────►│
    │                    │◄── PUBCOMP ──────────│
    │                    │                      │
```

## 参考资料

1. [MQTT 3.1.1 官方规范](https://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html)
2. [MQTT 5.0 规范](https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html)
3. [HiveMQ MQTT Essentials](https://www.hivemq.com/mqtt-essentials/)

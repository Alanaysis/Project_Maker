# 技术设计文档

## 1. 架构概述

```
┌──────────┐    ┌──────────┐    ┌──────────┐
│ Producer │───▶│  Queue   │───▶│ Consumer │
└──────────┘    └──────────┘    └──────────┘
                      │
                      ▼
                ┌──────────┐
                │ Storage  │
                │ (WAL)    │
                └──────────┘
```

### 模块划分

| 模块 | 职责 | 文件 |
|------|------|------|
| Message | 消息结构和序列化 | `src/message.rs` |
| Queue | 队列核心逻辑 | `src/queue.rs` |
| Storage | 持久化存储 | `src/storage.rs` |
| Consumer | 消费者偏移管理 | `src/consumer.rs` |
| Producer | 生产者 trait | `src/producer.rs` |

## 2. 数据设计

### 消息格式
```
| id(8) | topic_len(4) | topic | payload_len(8) | payload | timestamp(16) | offset(8) |
```

### 存储格式
```
| msg_len(8) | msg_data |
| msg_len(8) | msg_data |
...
```

## 3. 接口设计

```rust
Queue::new(name, data_dir) -> Queue
Queue::push(topic, payload) -> Result<u64>
Queue::pop() -> Option<Message>
Queue::register_consumer(name)
Consumer::commit(offset)
```

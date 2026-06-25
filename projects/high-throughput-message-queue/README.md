# 高吞吐消息队列

实现一个基于日志存储的高吞吐量消息队列，支持消息生产、持久化、消费和恢复。

## 核心循环

```
消息生产 → 持久化 → 消息分发 → 消费确认
```

## 学习目标

- 理解消息队列的核心原理
- 掌握顺序 I/O 和日志存储设计
- 学会消息持久化和崩溃恢复

## 技术栈

- 主语言：Rust
- 依赖：无

## 项目结构

```
high-throughput-message-queue/
├── src/
│   ├── lib.rs       # 库入口
│   ├── main.rs      # 基准测试
│   ├── message.rs   # 消息序列化
│   ├── queue.rs     # 队列核心
│   ├── storage.rs   # 日志存储
│   ├── consumer.rs  # 消费者
│   └── producer.rs  # 生产者 trait
├── tests/           # 集成测试
├── examples/        # 示例
└── docs/            # 文档
```

## 快速开始

### 运行测试

```bash
cargo test
```

### 运行示例

```bash
cargo run --example basic_usage
cargo run --example consumer_group
cargo run --example throughput_bench
```

### 基准测试

```bash
cargo run --release
```

## 核心功能

```rust
let mut queue = Queue::new("myqueue", "/tmp/data")?;
queue.push("orders", b"order_data".to_vec())?;
while let Some(msg) = queue.pop() {
    println!("{}", String::from_utf8_lossy(&msg.payload));
}
```

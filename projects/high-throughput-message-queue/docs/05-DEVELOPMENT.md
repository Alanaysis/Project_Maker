# 开发手册

## 1. 环境搭建

```bash
cd projects/high-throughput-message-queue
cargo build
```

## 2. 项目结构

```
high-throughput-message-queue/
├── src/
│   ├── lib.rs        # 库入口
│   ├── main.rs       # 基准测试
│   ├── message.rs    # 消息结构
│   ├── queue.rs      # 队列核心
│   ├── storage.rs    # 持久化
│   ├── consumer.rs   # 消费者
│   └── producer.rs   # 生产者 trait
├── tests/            # 集成测试
├── examples/         # 示例
└── docs/             # 文档
```

## 3. 运行

```bash
cargo run --release          # 基准测试
cargo test                   # 测试
cargo run --example basic_usage  # 示例
```

# WAL 日志

## 概述

WAL（Write-Ahead Logging，预写日志）是一种在数据库和文件系统中广泛使用的技术，用于保证数据的一致性和持久性。本项目实现了 WAL 日志的核心功能，包括日志格式定义、日志写入与读取、崩溃恢复和检查点机制。

**技术栈**：Go

**学习目标**：
- 理解 WAL 原理
- 掌握日志写入
- 学会崩溃恢复

## 核心循环

```
操作 → 日志写入 → 数据写入 → 检查点
```

## 最小可用版本

- [x] 实现 WAL 日志格式
- [x] 日志写入和读取
- [x] 崩溃恢复
- [x] 检查点机制

## 项目结构

```
wal/
├── README.md
├── docs/
│   ├── 01-RESEARCH.md
│   ├── 02-DESIGN.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── cmd/
│   └── wal-server/
│       └── main.go
├── internal/
│   ├── wal/
│   │   ├── wal.go
│   │   ├── entry.go
│   │   ├── recovery.go
│   │   └── checkpoint.go
│   └── storage/
│       └── storage.go
├── test/
│   ├── wal_test.go
│   ├── recovery_test.go
│   └── checkpoint_test.go
└── examples/
    └── usage.go
```

## 快速开始

```bash
# 运行示例
cd projects/wal
go run examples/usage.go

# 运行测试
go test ./test/...

# 运行 WAL 服务器
go run cmd/wal-server/main.go
```

## 文档

- [01-RESEARCH.md](docs/01-RESEARCH.md) - WAL 技术研究
- [02-DESIGN.md](docs/02-DESIGN.md) - 系统设计
- [03-IMPLEMENTATION.md](docs/03-IMPLEMENTATION.md) - 实现细节
- [04-TESTING.md](docs/04-TESTING.md) - 测试策略
- [05-DEVELOPMENT.md](docs/05-DEVELOPMENT.md) - 开发指南

## 依赖

- Go 1.21+
- 无外部依赖

# 分布式事务实现

## 项目概述

这是一个学习分布式事务的项目，实现了2PC（两阶段提交）和3PC（三阶段提交）协议。通过这个项目，你将深入理解分布式系统中事务一致性的保证机制。

## 学习目标

- 理解分布式事务的概念和挑战
- 掌握2PC协议的工作原理和实现
- 学习3PC协议对2PC的改进
- 了解分布式系统中的CAP定理和一致性模型

## 技术栈

- **语言**: Go 1.21+
- **框架**: 无（纯标准库实现）
- **测试**: Go标准测试框架

## 项目结构

```
distributed-transaction/
├── README.md
├── docs/                    # 学习文档
│   ├── 01-RESEARCH.md      # 研究笔记
│   ├── 02-DESIGN.md        # 设计文档
│   ├── 03-IMPLEMENTATION.md # 实现细节
│   ├── 04-TESTING.md       # 测试文档
│   └── 05-DEVELOPMENT.md   # 开发日志
├── LEARNING_NOTES.md        # 学习笔记
├── cmd/                     # 示例程序
│   └── main.go
├── internal/                # 内部实现
│   ├── coordinator/         # 协调者实现
│   ├── cohort/             # 参与者实现
│   └── transaction/        # 事务管理
├── pkg/                    # 公共工具包
│   └── utils/
└── test/                   # 测试文件
```

## 核心概念

### 2PC（两阶段提交）

**阶段1：准备阶段（Prepare Phase）**
- 协调者向所有参与者发送准备请求
- 参与者执行本地事务，锁定资源
- 参与者返回同意（YES）或中止（NO）

**阶段2：提交阶段（Commit Phase）**
- 如果所有参与者都同意，协调者发送提交命令
- 如果有参与者中止，协调者发送回滚命令
- 参与者执行提交或回滚操作

### 3PC（三阶段提交）

**阶段1：CanCommit**
- 协调者询问参与者是否可以提交
- 参与者检查自身状态，返回YES/NO

**阶段2：PreCommit**
- 如果所有参与者都同意，协调者发送预提交命令
- 参与者执行本地事务，锁定资源

**阶段3：DoCommit**
- 协调者发送提交命令
- 参与者提交事务，释放锁

## 快速开始

### 运行2PC示例

```bash
go run cmd/main.go --mode=2pc
```

### 运行3PC示例

```bash
go run cmd/main.go --mode=3pc
```

### 运行测试

```bash
go test ./...
```

## API示例

### 2PC事务示例

```go
// 创建协调者
coordinator := coordinator.NewCoordinator("coordinator-1")

// 创建参与者
cohort1 := cohort.NewCohort("cohort-1")
cohort2 := cohort.NewCohort("cohort-2")

// 注册参与者
coordinator.RegisterCohort(cohort1)
coordinator.RegisterCohort(cohort2)

// 开始事务
tx := transaction.NewTransaction("tx-1")
result, err := coordinator.ExecuteTransaction(tx)

if err != nil {
    log.Printf("Transaction failed: %v", err)
} else {
    log.Printf("Transaction %s: %s", tx.ID, result.Status)
}
```

### 3PC事务示例

```go
// 创建3PC协调者
coordinator := coordinator.NewThreePhaseCoordinator("coordinator-1")

// 创建参与者
cohort1 := cohort.NewCohort("cohort-1")
cohort2 := cohort.NewCohort("cohort-2")

// 注册参与者
coordinator.RegisterCohort(cohort1)
coordinator.RegisterCohort(cohort2)

// 开始事务
tx := transaction.NewTransaction("tx-1")
result, err := coordinator.ExecuteTransaction(tx)
```

## 协议对比

| 特性 | 2PC | 3PC |
|------|-----|-----|
| 阶段数 | 2 | 3 |
| 阻塞性 | 阻塞 | 非阻塞 |
| 协调者故障 | 可能导致不确定状态 | 更好的容错性 |
| 性能 | 较低 | 较高 |
| 复杂度 | 简单 | 复杂 |

## 参考资源

- [Distributed Systems: Principles and Paradigms](https://www.amazon.com/Distributed-Systems-Principles-Andrew-Tanenbaum/dp/0132392275)
- [Designing Data-Intensive Applications](https://www.amazon.com/Designing-Data-Intensive-Applications-Reliable-Maintainable/dp/1449373321)
- [Two-phase commit protocol - Wikipedia](https://en.wikipedia.org/wiki/Two-phase_commit_protocol)

## 许可证

MIT License

---

[返回 NLP 模块](../NLP_README.md) | [返回主目录](../../README.md)

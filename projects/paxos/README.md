# Paxos 共识算法实现 / Paxos Consensus Algorithm Implementation

## 项目概述 / Project Overview

Paxos 是一种分布式共识算法，用于在分布式系统中达成一致。本项目使用 Go 实现了完整的 Paxos 算法，包括 Basic Paxos 和 Multi Paxos。

Paxos is a distributed consensus algorithm designed to achieve agreement in a distributed system. This project implements the complete Paxos algorithm in Go, including Basic Paxos and Multi Paxos.

## 学习目标 / Learning Objectives

- **理解 Paxos 原理** / Understand Paxos Principles
  - 掌握两阶段提交协议 / Master two-phase commit protocol
  - 理解多数派（Quorum）机制 / Understand quorum mechanism
  - 学习容错设计 / Learn fault-tolerant design

- **掌握两阶段提交** / Master Two-Phase Commit
  - Prepare（准备）阶段 / Prepare phase
  - Accept（接受）阶段 / Accept phase

- **学会多 Paxos** / Learn Multi-Paxos
  - Leader 选举机制 / Leader election mechanism
  - 日志复制优化 / Log replication optimization
  - 消息复杂度降低 / Reduced message complexity

## 目录结构 / Directory Structure

```
paxos/
├── README.md              # 本文件 / This file
├── go.mod                 # Go module definition
├── src/
│   └── paxos/            # Paxos 核心实现 / Core implementation
│       ├── doc.go         # 包文档 / Package documentation
│       ├── types.go       # 类型定义（ProposalID, Message 等）/ Type definitions
│       ├── acceptor.go    # Acceptor 角色实现 / Acceptor role
│       ├── proposer.go    # Proposer 角色实现 / Proposer role
│       ├── learner.go     # Learner 角色实现 / Learner role
│       ├── single.go      # Single Paxos 实现 / Single Paxos
│       └── multi.go       # Multi Paxos 实现 / Multi Paxos
├── examples/             # 演示程序 / Demo programs
│   ├── 01_single_paxos.go     # Single Paxos 共识演示
│   ├── 02_multi_paxos.go      # Multi Paxos 共识演示
│   ├── 03_network_partition.go # 网络分区模拟
│   └── 04_failure_recovery.go # 故障恢复演示
└── tests/                # 单元测试 / Unit tests
    ├── types_test.go       # 类型和工具测试
    ├── single_test.go      # Single Paxos 测试
    └── multi_test.go       # Multi Paxos 测试
```

## 如何运行 / How to Run

### 运行示例 / Run Examples

```bash
# Single Paxos 共识演示
go run examples/01_single_paxos.go

# Multi Paxos 共识演示
go run examples/02_multi_paxos.go

# 网络分区模拟
go run examples/03_network_partition.go

# 故障恢复演示
go run examples/04_failure_recovery.go
```

### 运行测试 / Run Tests

```bash
# 运行所有测试
go test ./tests/ -v

# 运行 Single Paxos 测试
go test ./tests/ -run TestSinglePaxos -v

# 运行 Multi Paxos 测试
go test ./tests/ -run TestMultiPaxos -v

# 运行类型测试
go test ./tests/ -run TestAcceptor -v
go test ./tests/ -run TestProposer -v
```

### 覆盖率 / Coverage

```bash
go test ./tests/ -cover
```

## Paxos 算法详解 / Paxos Algorithm Explained

### 基本概念 / Basic Concepts

Paxos 算法中有三种角色：

1. **Proposer（提议者）**：提出提案，试图让系统达成一致
2. **Acceptor（接受者）**：接收和响应提案
3. **Learner（学习者）**：学习已决定的值

### Basic Paxos 协议流程 / Protocol Flow

```
Proposer                    Acceptor                    Learner
    |                           |                           |
    |------ Prepare(n) -------->|                           |
    |  请求提议编号 n           |                           |
    |                           |                           |
    |<--- Promise(n, v) --------|                           |
    |  承诺不接受更小编号        |                           |
    |  返回已接受的最大提案      |                           |
    |                           |                           |
    |------ Accept(n, v) ------>|                           |
    |  请求接受值 v             |                           |
    |                           |                           |
    |<--- Accepted(n, v) -------|                           |
    |                           |                           |
    |                           |------ Notify(n, v) ------>|
    |                           |  通知已决定的值            |
    |                           |                           |
```

### 两阶段协议 / Two-Phase Protocol

#### Phase 1: Prepare（准备阶段）

```
1. Proposer 选择唯一的提案编号 n
2. Proposer 向多数派 Acceptor 发送 Prepare(n)
3. Acceptor 检查 n 是否大于已承诺的最大编号
   - 如果是：承诺不接受编号 < n 的提案，返回已接受的最大提案
   - 如果否：拒绝该请求
```

#### Phase 2: Accept（接受阶段）

```
1. Proposer 收到多数派的 Promise
2. Proposer 确定值 v：
   - 如果任何 Promise 包含已接受的值，使用编号最大的那个
   - 否则使用自己的值
3. Proposer 向多数派 Acceptor 发送 Accept(n, v)
4. Acceptor 接受值 v（如果没有收到更高编号的 Promise）
5. 当 Proposer 收到多数派的 Accepted 响应，值被决定
```

### Multi Paxos 优化

Multi Paxos 通过选举一个 Leader 来优化 Basic Paxos：

```
                    Leader Election
    Follower 1  Follower 2  Follower 3
        |           |           |
        |<-- Vote Request --- Leader
        |           |           |
        |--> Vote Response --->|
        |           |           |
        +-- Leader Elected! ----+
                    |
    |--- Log Replication ---|
        |           |           |
        |< AppendEntries --- Leader
        |           |           |
        |-> AppendResponse -->|
        |           |           |
        |< AppendEntries --- Leader
        |           |           |
        |-> AppendResponse -->|
                    |
    +-- All Entries Replicated! --+
```

**优化要点**：
- Leader 稳定后，大多数提案只需一次 Prepare + Accept
- Leader 通过心跳维持权威
- 消息复杂度从 O(n²) 降到 O(n)

### 容错能力 / Fault Tolerance

| 集群大小 | 多数派 | 容忍故障数 | 存活节点 |
|---------|--------|-----------|---------|
| 3       | 2      | 1         | 2       |
| 5       | 3      | 2         | 3       |
| 7       | 5      | 3         | 4       |
| 9       | 7      | 4         | 5       |

**关键洞察**：两个重叠的多数派保证至少有一个节点在两个多数派中都存在，确保已决定的值不会被覆盖。

## 技术栈 / Tech Stack

- **语言 / Language**: Go 1.22+
- **并发 / Concurrency**: goroutines, channels, sync.Mutex
- **测试 / Testing**: go test

## 参考资料 / References

- [Paxos Made Simple](https://lamport.azurewebsites.net/pubs/paxos-simple.pdf) - Leslie Lamport
- [The Part-Time Parliament](https://lamport.azurewebsites.net/pubs/lamport-paxos.pdf) - Leslie Lamport
- [In Search of an Understandable Consensus Algorithm](https://raft.github.io/raft.pdf) - Raft 论文（对比 Paxos）
- [Paxos vs Raft](https://raft.github.io/) - Raft 对比 Paxos 的改进

## 许可证 / License

MIT License

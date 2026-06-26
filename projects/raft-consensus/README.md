# Raft 共识算法实现 | Raft Consensus Algorithm Implementation

## 中文

### 项目描述
本项目是一个教育性的 Raft 共识算法 Go 语言实现。它旨在帮助开发者深入理解分布式系统中的共识算法原理。

Raft 是一种易于理解的分布式共识算法，用于管理复制日志。它将共识分解为几个相对独立的部分：领导者选举、日志复制和安全性。

### 学习目标
- **理解 Raft 原理**：掌握 Raft 算法的核心思想和设计原则
- **掌握领导者选举**：学习节点如何通过投票机制选出领导者
- **学会日志复制**：理解日志如何在集群中同步和提交
- **安全性保证**：了解 Raft 如何保证一致性和容错性

### 核心循环
```
领导者选举 → 日志复制 → 安全性 → 成员变更
```

### 项目结构
```
raft-consensus/
├── src/                    # Raft 核心实现
│   ├── raft.go             # 基础类型和状态定义
│   ├── node.go             # 节点管理和状态机
│   ├── election.go         # 领导者选举实现
│   ├── log_replication.go  # 日志复制实现
│   ├── safety.go           # 安全性属性验证
│   └── cluster.go          # 集群成员管理
├── examples/               # 演示程序
│   ├── leader_election.go  # 领导者选举演示
│   ├── log_replication.go  # 日志复制演示
│   ├── log_consistency.go  # 日志一致性演示
│   └── cluster_demo.go     # 完整集群演示
├── tests/                  # 单元测试
│   └── raft_test.go
├── go.mod
└── README.md
```

### 运行示例

#### 1. 领导者选举演示
```bash
cd examples
go run leader_election.go
```

#### 2. 日志复制演示
```bash
cd examples
go run log_replication.go
```

#### 3. 日志一致性演示
```bash
cd examples
go run log_consistency.go
```

#### 4. 完整集群演示
```bash
cd examples
go run cluster_demo.go
```

#### 5. 运行测试
```bash
go test ./tests/...
```

### Raft 算法详解

#### 节点状态
Raft 节点有三种状态：

1. **Follower（跟随者）**
   - 响应领导者的心跳和候选人的请求
   - 可以被选举为候选人
   - 默认状态

2. **Candidate（候选人）**
   - 发起选举，请求投票
   - 获得多数票后成为领导者
   - 超时后重新发起选举

3. **Leader（领导者）**
   - 处理客户端请求
   - 复制日志到跟随者
   - 发送心跳维持权威

#### 领导者选举
1. 节点启动时是 Follower
2. 选举超时后，转为 Candidate
3. Candidate 投票给自己并请求其他节点的投票
4. 获得多数票的 Candidate 成为 Leader
5. Leader 定期发送心跳防止重新选举

#### 日志复制
1. 客户端向 Leader 发送请求
2. Leader 将命令追加到自己的日志中
3. Leader 发送 AppendEntries RPC 到所有 Follower
4. Follower 将条目追加到自己的日志中
5. Leader 收到多数确认后提交条目
6. Leader 将命令应用到状态机

#### 安全性
- **选举限制**：候选人必须拥有所有已提交的条目
- **日志匹配**：相同索引和-term 的条目必须相同
- **状态机安全**：已提交的条目在所有节点上相同

---

## English

### Project Description
This project is an educational implementation of the Raft consensus algorithm in Go. It aims to help developers deeply understand the principles of consensus algorithms in distributed systems.

Raft is a consensus algorithm designed to be more understandable than Paxos. It divides consensus into several relatively independent parts: leader election, log replication, and safety.

### Learning Objectives
- **Understand Raft Principles**: Master the core ideas and design principles of the Raft algorithm
- **Master Leader Election**: Learn how nodes elect a leader through voting
- **Learn Log Replication**: Understand how logs are synchronized and committed across the cluster
- **Safety Guarantees**: Understand how Raft ensures consistency and fault tolerance

### Core Loop
```
Leader Election → Log Replication → Safety → Membership Changes
```

### Project Structure
```
raft-consensus/
├── src/                    # Core Raft implementation
│   ├── raft.go             # Base types and state definitions
│   ├── node.go             # Node management and state machine
│   ├── election.go         # Leader election implementation
│   ├── log_replication.go  # Log replication implementation
│   ├── safety.go           # Safety property verification
│   └── cluster.go          # Cluster membership management
├── examples/               # Demo programs
│   ├── leader_election.go  # Leader election demo
│   ├── log_replication.go  # Log replication demo
│   ├── log_consistency.go  # Log consistency demo
│   └── cluster_demo.go     # Full cluster demo
├── tests/                  # Unit tests
│   └── raft_test.go
├── go.mod
└── README.md
```

### Running Examples

#### 1. Leader Election Demo
```bash
cd examples
go run leader_election.go
```

#### 2. Log Replication Demo
```bash
cd examples
go run log_replication.go
```

#### 3. Log Consistency Demo
```bash
cd examples
go run log_consistency.go
```

#### 4. Full Cluster Demo
```bash
cd examples
go run cluster_demo.go
```

#### 5. Run Tests
```bash
go test ./tests/...
```

### Raft Algorithm Explained

#### Node States
Raft nodes have three states:

1. **Follower**
   - Responds to leader heartbeats and candidate vote requests
   - Can be elected as a candidate
   - Default state

2. **Candidate**
   - Initiates election, requests votes
   - Becomes leader if it receives majority votes
   - Retransmits election if timeout occurs

3. **Leader**
   - Handles client requests
   - Replicates logs to followers
   - Sends heartbeats to maintain authority

#### Leader Election
1. Nodes start as Followers
2. On election timeout, transition to Candidate
3. Candidate votes for itself and requests votes from others
4. Candidate with majority votes becomes Leader
5. Leader sends periodic heartbeats to prevent re-election

#### Log Replication
1. Client sends request to Leader
2. Leader appends command to its log
3. Leader sends AppendEntries RPC to all Followers
4. Followers append entry to their logs
5. Leader commits entry after majority acknowledgment
6. Leader applies command to state machine

#### Safety Properties
- **Election Restriction**: A candidate must have all committed entries
- **Log Matching**: Entries with same index and term must be identical
- **State Machine Safety**: Committed entries are the same on all nodes

### 技术栈 | Tech Stack
- **语言**: Go
- **框架**: 无
- **库**: gRPC (用于生产环境 RPC)

### 优先级 | Priority
P1

### 预计时间 | Estimated Time
12 小时

---

## Raft 算法核心概念 | Core Raft Concepts

### Term (任期)
Raft 将时间划分为任意长度的任期，任期编号从 1 开始递增。每个任期要么是空白的（没有选出领导者），要幺有一个领导者管理整个任期。

### Vote (投票)
每个节点在每个任期内最多只能投一票。投票顺序决定了选举结果。

### Log Entry (日志条目)
每个日志条目包含 (term, command) 对。条目一旦追加就不会被修改，只能追加。

### Commit Index (提交索引)
最高已知已提交的日志索引。领导者只有知道大多数服务器已经复制了条目后才会提交。

### 一致性保证 | Consistency Guarantees
1. **日志匹配属性**: 如果两个日志有相同索引和-term 的条目，则它们存储相同的命令
2. **领导者追加-only**: 领导者永远不会覆盖或删除自己的日志条目
3. **状态机安全**: 如果服务器在给定索引应用了日志条目，则没有其他服务器会在该索引应用不同的条目

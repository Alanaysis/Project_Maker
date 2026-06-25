# Raft 共识算法实现总结

## 已实现功能

### 1. 核心 Raft 算法
- **领导者选举**：完整的选举机制，包括任期、投票、心跳
- **日志复制**：AppendEntries RPC，日志一致性检查
- **状态管理**：线程安全的状态访问

### 2. 快照机制
- **快照创建**：保存状态机当前状态
- **日志截断**：删除快照点之前的日志
- **快照传输**：InstallSnapshot RPC
- **快照安装**：从领导者接收快照

### 3. 成员变更
- **添加节点**：向集群添加新节点
- **移除节点**：从集群移除节点
- **安全性检查**：只有领导者能发起变更

### 4. 客户端交互
- **命令提交**：提交写命令到集群
- **线性一致性读**：确保读取最新数据
- **命令转发**：非领导者自动转发请求

### 5. gRPC 服务
- **RequestVote**：投票请求 RPC
- **AppendEntries**：日志复制/心跳 RPC
- **InstallSnapshot**：快照安装 RPC

## 项目结构

```
raft-consensus/
├── cmd/server/main.go           # 服务器入口
├── internal/
│   ├── raft/
│   │   ├── raft.go              # 核心实现
│   │   ├── election.go          # 选举管理
│   │   ├── log_replication.go   # 日志复制
│   │   ├── state.go             # 状态管理
│   │   ├── snapshot.go          # 快照管理
│   │   ├── membership.go        # 成员变更
│   │   └── client.go            # 客户端交互
│   ├── pb/
│   │   ├── raft.proto           # gRPC 定义
│   │   ├── raft.pb.go           # 生成代码
│   │   └── raft_grpc.pb.go      # gRPC 服务代码
│   ├── statemachine/kv.go       # KV 状态机
│   └── storage/memory.go        # 内存存储
├── test/
│   ├── election_test.go         # 选举测试
│   ├── log_replication_test.go  # 日志复制测试
│   ├── snapshot_test.go         # 快照测试
│   ├── membership_test.go       # 成员变更测试
│   ├── network_partition_test.go # 网络分区测试
│   ├── node_failure_test.go     # 节点故障测试
│   └── integration_test.go      # 集成测试
└── docs/
    ├── 01-RESEARCH.md           # 市场调研
    ├── 02-ARCHITECTURE.md       # 架构设计
    ├── 03-IMPLEMENTATION.md     # 实现细节
    ├── 04-TESTING.md            # 测试策略
    └── 05-DEVELOPMENT.md        # 开发日志
```

## 测试覆盖

### 选举测试 (7 个)
- 基本选举流程
- 状态转换
- 任期管理
- 投票机制
- 投票请求处理
- 更高任期请求
- 更低任期请求

### 日志复制测试 (8 个)
- 日志追加
- 多条日志
- 日志截断
- 提交索引
- 应用索引
- nextIndex/matchIndex
- 持久化状态
- 基本复制
- 跟随者拒绝

### 快照测试 (4 个)
- 快照创建
- 日志截断
- 初始状态
- 多次快照

### 成员变更测试 (5 个)
- 添加节点
- 成员检查
- 移除节点
- 非领导者拒绝
- 不能移除自己

### 网络分区测试 (7 个)
- 基本分区
- 分区恢复
- 多数分区
- 少数分区
- 对称分区
- 多个分区
- 领导者分区

### 节点故障测试 (9 个)
- 单节点故障
- 多节点故障
- 多数故障
- 节点重启
- 领导者故障
- 故障后选举
- 崩溃恢复
- 并发操作
- 法定人数

### 集成测试 (7 个)
- KV 状态机
- 无效命令
- 快照创建
- 节点创建
- 节点状态
- 应用通道
- 并发访问
- 日志一致性
- 状态字符串

## 运行测试

```bash
# 安装依赖
go mod tidy

# 运行所有测试
go test ./...

# 运行特定测试
go test ./test/ -v -run TestElection
go test ./test/ -v -run TestSnapshot
go test ./test/ -v -run TestNetworkPartition
go test ./test/ -v -run TestNodeFailure

# 运行竞态检测
go test -race ./...
```

## 启动集群

```bash
# 终端 1
go run cmd/server/main.go -id 1 -port 50051 -peers "localhost:50052,localhost:50053"

# 终端 2
go run cmd/server/main.go -id 2 -port 50052 -peers "localhost:50051,localhost:50053"

# 终端 3
go run cmd/server/main.go -id 3 -port 50053 -peers "localhost:50051,localhost:50052"
```

## Go API 使用

```go
// 创建节点
config := raft.Config{
    ID:                 1,
    Address:            "localhost:50051",
    Peers:              map[int64]string{...},
    ElectionTimeoutMin: 150 * time.Millisecond,
    ElectionTimeoutMax: 300 * time.Millisecond,
    HeartbeatInterval:  50 * time.Millisecond,
}
node := raft.NewRaftNode(config)
node.Start()

// 提交命令
resp := node.SubmitCommand("PUT key value", 1)

// 线性一致性读
value, err := node.LinearizableRead("key")

// 创建快照
node.CreateSnapshot(100, snapshotData)

// 成员变更
node.AddNode(4, "localhost:50054")
node.RemoveNode(3)

// 获取集群信息
members := node.GetClusterMembers()
leaderID, leaderAddr, _ := node.GetLeaderAddress()
```

## 学习要点

1. **领导者选举**：随机化超时避免选票分割
2. **日志复制**：领导者负责复制，大多数确认后提交
3. **安全性**：选举限制确保日志完整性
4. **快照机制**：日志压缩防止无限增长
5. **成员变更**：支持集群动态调整
6. **客户端交互**：提供线性一致性接口

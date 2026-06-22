# 02 - 项目架构设计

## 1. 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Application                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Raft Server                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                    gRPC Service                          ││
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   ││
│  │  │ RequestVote  │ │ AppendEntries│ │ ClientRequest│   ││
│  │  └──────────────┘ └──────────────┘ └──────────────┘   ││
│  └─────────────────────────────────────────────────────────┘│
│                              │                               │
│                              ▼                               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                    Raft Core                             ││
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   ││
│  │  │   Election   │ │    Log       │ │   State      │   ││
│  │  │   Manager    │ │   Replicator │ │   Machine    │   ││
│  │  └──────────────┘ └──────────────┘ └──────────────┘   ││
│  └─────────────────────────────────────────────────────────┘│
│                              │                               │
│                              ▼                               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                    Storage Layer                         ││
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   ││
│  │  │    Log       │ │   State      │ │   Snapshot   │   ││
│  │  │   Storage    │ │   Storage    │ │   Storage    │   ││
│  │  └──────────────┘ └──────────────┘ └──────────────┘   ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## 2. 核心组件

### 2.1 RaftNode（核心状态）

```go
type RaftNode struct {
    // 持久化状态
    currentTerm int64
    votedFor    int64
    log         []LogEntry

    // 易失性状态
    commitIndex int64
    lastApplied int64

    // 领导者状态
    nextIndex   map[int64]int64
    matchIndex  map[int64]int64

    // 节点信息
    id          int64
    peers       map[int64]*Peer
    state       NodeState
    leader      int64

    // 同步原语
    mu          sync.RWMutex
    applyCh     chan ApplyMsg
    stopCh      chan struct{}
}
```

### 2.2 LogEntry（日志条目）

```go
type LogEntry struct {
    Term    int64
    Index   int64
    Command interface{}
}
```

### 2.3 Peer（对等节点）

```go
type Peer struct {
    id       int64
    address  string
    client   pb.RaftServiceClient
    conn     *grpc.ClientConn
    nextIdx  int64
    matchIdx int64
}
```

## 3. 状态机设计

### 3.1 状态机接口

```go
type StateMachine interface {
    Apply(command interface{}) interface{}
    Snapshot() []byte
    Restore(data []byte) error
}
```

### 3.2 KV 状态机实现

```go
type KVStateMachine struct {
    data map[string]string
}
```

## 4. 存储设计

### 4.1 存储接口

```go
type Storage interface {
    // 日志存储
    AppendLog(entries []LogEntry) error
    GetLog(index int64) (*LogEntry, error)
    GetLogs(start, end int64) ([]LogEntry, error)
    TruncateLog(index int64) error

    // 状态存储
    SaveState(state HardState) error
    LoadState() (*HardState, error)

    // 快照存储
    SaveSnapshot(data []byte) error
    LoadSnapshot() ([]byte, error)
}
```

### 4.2 HardState（持久化状态）

```go
type HardState struct {
    CurrentTerm int64
    VotedFor    int64
}
```

## 5. gRPC 服务定义

### 5.1 Proto 文件

```protobuf
syntax = "proto3";
package raft;

service RaftService {
    rpc RequestVote(RequestVoteRequest) returns (RequestVoteResponse);
    rpc AppendEntries(AppendEntriesRequest) returns (AppendEntriesResponse);
    rpc InstallSnapshot(InstallSnapshotRequest) returns (InstallSnapshotResponse);
}

message RequestVoteRequest {
    int64 term = 1;
    int64 candidateId = 2;
    int64 lastLogIndex = 3;
    int64 lastLogTerm = 4;
}

message RequestVoteResponse {
    int64 term = 1;
    bool granted = 2;
}

message AppendEntriesRequest {
    int64 term = 1;
    int64 leaderId = 2;
    int64 prevLogIndex = 3;
    int64 prevLogTerm = 4;
    repeated LogEntry entries = 5;
    int64 leaderCommit = 6;
}

message AppendEntriesResponse {
    int64 term = 1;
    bool success = 2;
    int64 conflictIndex = 3;
    int64 conflictTerm = 4;
}

message LogEntry {
    int64 term = 1;
    int64 index = 2;
    bytes command = 3;
}
```

## 6. 并发模型

### 6.1 协程设计

```
┌─────────────────────────────────────────────┐
│              Main Goroutine                  │
│  ┌─────────────────────────────────────┐    │
│  │         Election Timer               │    │
│  │         (随机超时)                    │    │
│  └─────────────────────────────────────┘    │
│  ┌─────────────────────────────────────┐    │
│  │         Heartbeat Timer              │    │
│  │         (定期心跳)                    │    │
│  └─────────────────────────────────────┘    │
│  ┌─────────────────────────────────────┐    │
│  │         Log Replicator               │    │
│  │         (日志复制)                    │    │
│  └─────────────────────────────────────┘    │
│  ┌─────────────────────────────────────┐    │
│  │         Apply Goroutine              │    │
│  │         (状态机应用)                  │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

### 6.2 消息传递

- **applyCh**：用于向状态机应用已提交的日志
- **stopCh**：用于优雅关闭
- **选举超时通道**：重置选举定时器

## 7. 错误处理

### 7.1 网络错误
- 超时重试
- 连接池管理
- 错误日志记录

### 7.2 状态错误
- 任期过期处理
- 日志不一致修复
- 领导者失效检测

## 8. 测试策略

### 8.1 单元测试
- 选举逻辑测试
- 日志复制测试
- 状态机测试

### 8.2 集成测试
- 多节点集群测试
- 网络分区测试
- 领导者切换测试

### 8.3 性能测试
- 日志复制吞吐量
- 选举时间
- 提交延迟

# 03 - 实现细节

## 1. 项目结构

```
raft-consensus/
├── cmd/
│   └── server/
│       └── main.go              # 服务器入口
├── internal/
│   ├── raft/
│   │   ├── raft.go              # Raft 核心实现
│   │   ├── election.go          # 领导者选举
│   │   ├── log_replication.go   # 日志复制
│   │   ├── state.go             # 状态管理
│   │   ├── snapshot.go          # 快照管理
│   │   ├── membership.go        # 成员变更
│   │   └── client.go            # 客户端交互
│   ├── pb/
│   │   ├── raft.proto           # gRPC 服务定义
│   │   ├── raft.pb.go           # 生成的代码
│   │   └── raft_grpc.pb.go      # gRPC 服务代码
│   ├── statemachine/
│   │   └── kv.go                # KV 状态机实现
│   └── storage/
│       └── memory.go            # 内存存储实现
├── configs/
│   └── config.toml              # 配置文件
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

## 2. 核心组件实现

### 2.1 状态管理 (state.go)

状态管理模块负责维护 Raft 节点的所有状态，包括：

- **持久化状态**：currentTerm、votedFor、log
- **易失性状态**：commitIndex、lastApplied
- **领导者状态**：nextIndex、matchIndex

关键设计：
- 使用 `sync.RWMutex` 保护并发访问
- 提供线程安全的 getter/setter 方法
- 支持状态快照和恢复

```go
type RaftState struct {
    mu sync.RWMutex

    // 持久化状态
    currentTerm int64
    votedFor    int64
    log         []LogEntry

    // 易失性状态
    commitIndex int64
    lastApplied int64

    // 领导者状态
    nextIndex  map[int64]int64
    matchIndex map[int64]int64

    // 节点信息
    id     int64
    state  NodeState
    leader int64
}
```

### 2.2 领导者选举 (election.go)

选举模块实现 Raft 的选举机制：

1. **选举超时**：随机化超时时间避免选票分割
2. **投票请求**：并行向所有节点请求投票
3. **投票响应**：处理投票结果和任期更新
4. **选举结果**：统计票数，判断是否赢得选举

关键算法：
```go
func (em *ElectionManager) startElection() {
    // 1. 转变为候选人
    // 2. 增加当前任期
    // 3. 投票给自己
    // 4. 并行请求投票
    // 5. 等待投票结果
    // 6. 判断是否赢得选举
}
```

### 2.3 日志复制 (log_replication.go)

日志复制模块实现日志的一致性复制：

1. **客户端请求**：领导者接收并追加日志
2. **心跳机制**：定期发送心跳维持领导地位
3. **日志复制**：并行复制到所有跟随者
4. **提交确认**：大多数节点确认后提交

关键流程：
```go
func (lr *LogReplicator) AppendEntries(command interface{}) {
    // 1. 创建日志条目
    // 2. 追加到本地日志
    // 3. 广播到其他节点
    // 4. 等待确认
    // 5. 更新 commitIndex
}
```

### 2.4 快照管理 (snapshot.go)

快照模块实现日志压缩：

1. **创建快照**：保存状态机当前状态
2. **日志截断**：删除快照点之前的日志
3. **快照传输**：发送快照给落后太多的跟随者
4. **快照安装**：从领导者接收并安装快照

关键功能：
```go
func (sm *SnapshotManager) CreateSnapshot(lastIncludedIndex int64, data []byte) {
    // 1. 获取 lastIncludedIndex 处的任期
    // 2. 保存快照数据
    // 3. 截断日志
}

func (sm *SnapshotManager) InstallSnapshot(req *pb.InstallSnapshotRequest) {
    // 1. 更新快照元数据
    // 2. 重置日志
    // 3. 更新 commitIndex 和 lastApplied
}
```

### 2.5 成员变更 (membership.go)

成员变更模块支持集群动态调整：

1. **添加节点**：向集群添加新节点
2. **移除节点**：从集群移除节点
3. **安全性检查**：确保变更过程中保持一致性

关键功能：
```go
func (mm *MembershipManager) RequestChange(change MembershipChange) error {
    // 1. 检查是否是领导者
    // 2. 验证变更请求
    // 3. 执行变更
}

func (mm *MembershipManager) handleAddNode(change MembershipChange) {
    // 1. 检查节点是否已存在
    // 2. 初始化 nextIndex 和 matchIndex
    // 3. 添加到 peers 映射
}
```

### 2.6 客户端交互 (client.go)

客户端模块提供用户接口：

1. **命令提交**：提交写命令到集群
2. **线性一致性读**：确保读取最新数据
3. **命令转发**：非领导者自动转发请求

关键功能：
```go
func (cm *ClientManager) SubmitCommand(command interface{}, commandID int64) ClientResponse {
    // 1. 检查是否是领导者
    // 2. 如果不是，转发到领导者
    // 3. 等待命令提交
}

func (cm *ClientManager) LinearizableRead(key interface{}) (interface{}, error) {
    // 1. 确认领导权
    // 2. 等待 commitIndex 被应用
    // 3. 执行读操作
}
```

### 2.7 gRPC 服务 (pb/raft.proto)

定义 Raft 节点间的 RPC 接口：

```protobuf
service RaftService {
    rpc RequestVote(RequestVoteRequest) returns (RequestVoteResponse);
    rpc AppendEntries(AppendEntriesRequest) returns (AppendEntriesResponse);
    rpc InstallSnapshot(InstallSnapshotRequest) returns (InstallSnapshotResponse);
}
```

消息类型：
- `RequestVoteRequest`：投票请求
- `RequestVoteResponse`：投票响应
- `AppendEntriesRequest`：日志复制请求
- `AppendEntriesResponse`：日志复制响应
- `LogEntry`：日志条目
- `InstallSnapshotRequest`：快照安装请求
- `InstallSnapshotResponse`：快照安装响应

### 2.5 状态机 (statemachine/kv.go)

KV 状态机实现简单的键值存储：

```go
type KVStateMachine struct {
    data map[string]string
}
```

支持命令：
- `PUT key value`：设置键值对
- `GET key`：获取值
- `DELETE key`：删除键值对

### 2.6 存储层 (storage/memory.go)

内存存储实现：

```go
type MemoryStorage struct {
    log       []LogEntry
    hardState HardState
}
```

接口：
- `AppendLog`：追加日志
- `GetLog`：获取日志
- `SaveState`：保存状态
- `LoadState`：加载状态

## 3. 并发模型

### 3.1 协程设计

- **选举定时器协程**：监控选举超时
- **心跳协程**：定期发送心跳
- **日志复制协程**：并行复制日志
- **状态机应用协程**：应用已提交的日志

### 3.2 同步机制

- `sync.RWMutex`：保护共享状态
- `channel`：协程间通信
- `WaitGroup`：等待并行操作完成

## 4. 错误处理

### 4.1 网络错误

- 超时重试
- 连接池管理
- 错误日志记录

### 4.2 状态错误

- 任期过期处理
- 日志不一致修复
- 领导者失效检测

## 5. 性能优化

### 5.1 批量操作

- 批量日志复制
- 批量状态机应用

### 5.2 并行处理

- 并行投票请求
- 并行日志复制

### 5.3 缓存机制

- 日志缓存
- 状态缓存
# Raft 共识算法学习笔记

## 一、Raft 算法概述

### 1.1 什么是 Raft？

Raft 是一种分布式共识算法，由 Diego Ongaro 和 John Ousterhout 在 2014 年提出。它的设计目标是比 Paxos 更易于理解，同时提供相同的安全性和活性保证。

### 1.2 核心思想

Raft 将共识问题分解为三个相对独立的子问题：

1. **领导者选举（Leader Election）**
   - 节点通过选举产生领导者
   - 领导者负责处理所有客户端请求
   - 通过心跳机制维持领导地位

2. **日志复制（Log Replication）**
   - 领导者接收客户端请求并追加到日志
   - 领导者将日志条目复制到所有跟随者
   - 当大多数节点确认后，日志被提交

3. **安全性（Safety）**
   - 确保所有节点以相同顺序应用相同的命令
   - 选举限制：只有包含所有已提交日志的节点才能成为领导者

## 二、核心概念

### 2.1 节点状态

Raft 中的每个节点处于以下三种状态之一：

- **跟随者（Follower）**：被动响应请求，不主动发起通信
- **候选人（Candidate）**：发起选举，请求其他节点投票
- **领导者（Leader）**：处理客户端请求，管理日志复制

```
                  超时
    ┌──────────────────────────────────┐
    │                                  ▼
┌───┴───┐    选举超时    ┌────────────┐    赢得选举    ┌────────┐
│Follower│ ─────────────► │ Candidate  │ ─────────────► │ Leader │
└───┬───┘    └────────────┘    └────────┘
    │                                  │
    │              发现新领导者          │
    └──────────────────────────────────┘
```

### 2.2 任期（Term）

任期是 Raft 中的逻辑时钟：

- 每次选举增加
- 每个节点维护当前任期号
- 任期号用于检测过期的信息

```
任期 1    任期 2    任期 3    任期 4    任期 5
─────────────────────────────────────────────────
  选举      选举      选举      选举      选举
```

### 2.3 日志条目

每个日志条目包含：

- **索引（Index）**：条目在日志中的位置
- **任期（Term）**：条目创建时的任期号
- **命令（Command）**：状态机要执行的命令

```
索引    1    2    3    4    5
任期    1    1    2    3    3
命令   cmd1 cmd2 cmd3 cmd4 cmd5
```

## 三、领导者选举

### 3.1 选举流程

1. **选举超时**
   - 跟随者在超时时间内没有收到领导者的心跳
   - 超时时间随机化，避免选票分割

2. **发起选举**
   - 跟随者转变为候选人
   - 增加当前任期
   - 投票给自己
   - 并行向其他节点请求投票

3. **投票规则**
   - 每个节点在每个任期只能投一票
   - 投票给日志至少和自己一样新的候选人
   - 先到先得

4. **选举结果**
   - 赢得大多数投票：成为领导者
   - 收到领导者心跳：回到跟随者状态
   - 选举超时：重新发起选举

### 3.2 选举超时随机化

```go
func (em *ElectionManager) randomTimeout() time.Duration {
    delta := em.config.TimeoutMax - em.config.TimeoutMin
    return em.config.TimeoutMin + time.Duration(rand.Int63n(int64(delta)))
}
```

**为什么需要随机化？**

如果所有节点同时超时，会同时发起选举，导致选票分割，无法选出领导者。

### 3.3 投票请求

```go
type RequestVoteRequest struct {
    Term         int64  // 候选人的任期号
    CandidateId  int64  // 候选人 ID
    LastLogIndex int64  // 候选人最后日志条目的索引
    LastLogTerm  int64  // 候选人最后日志条目的任期号
}
```

### 3.4 投票响应

```go
type RequestVoteResponse struct {
    Term    int64  // 当前任期号
    Granted bool   // 是否投票
}
```

## 四、日志复制

### 4.1 日志复制流程

1. **客户端请求**
   - 客户端向领导者发送命令
   - 领导者将命令追加到日志

2. **日志复制**
   - 领导者并行发送 AppendEntries RPC 到所有跟随者
   - 跟随者追加日志并响应

3. **提交确认**
   - 当大多数节点确认后，日志被提交
   - 领导者更新 commitIndex

4. **状态机应用**
   - 节点将已提交的日志应用到状态机
   - 更新 lastApplied

### 4.2 AppendEntries RPC

```go
type AppendEntriesRequest struct {
    Term         int64       // 领导者的任期号
    LeaderId     int64       // 领导者 ID
    PrevLogIndex int64       // 新日志条目前一个条目的索引
    PrevLogTerm  int64       // 新日志条目前一个条目的任期号
    Entries      []LogEntry  // 要存储的日志条目
    LeaderCommit int64       // 领导者的 commitIndex
}
```

### 4.3 日志一致性检查

领导者通过 `PrevLogIndex` 和 `PrevLogTerm` 检查日志是否匹配：

- 如果匹配：追加新日志
- 如果不匹配：拒绝并返回冲突信息

### 4.4 日志回退

当日志不一致时，领导者需要回退：

```go
if resp.ConflictTerm > 0 {
    // 查找冲突任期的最后一个索引
    conflictIndex := int64(0)
    for i := int64(len(lr.state.log)) - 1; i >= 1; i-- {
        if lr.state.log[i].Term == resp.ConflictTerm {
            conflictIndex = i
            break
        }
    }
    if conflictIndex > 0 {
        lr.state.nextIndex[peer.ID] = conflictIndex + 1
    } else {
        lr.state.nextIndex[peer.ID] = resp.ConflictIndex
    }
}
```

## 五、安全性

### 5.1 选举限制

**规则**：只有包含所有已提交日志的候选人才能赢得选举。

**实现**：
- 候选人在投票请求中包含最后日志条目的索引和任期
- 节点拒绝日志比自己旧的候选人

### 5.2 日志匹配原则

**规则**：如果两个日志在某个索引处有相同的任期号，那么它们在该索引之前的所有条目都相同。

**证明**：
- 领导者在某个任期最多创建一个日志条目
- 日志条目的位置永远不会改变
- 因此，相同索引和任期的条目必然相同

### 5.3 领导者完整性

**规则**：如果一个日志条目在某个任期被提交，那么该条目会出现在所有更高任期的领导者日志中。

**证明**：
- 日志条目只能由领导者创建
- 领导者只能提交当前任期的条目
- 因此，已提交的条目必然存在于后续领导者的日志中

## 六、实现细节

### 6.1 并发控制

```go
type RaftState struct {
    mu sync.RWMutex
    // ... 状态字段
}

func (rs *RaftState) GetState() (int64, bool) {
    rs.mu.RLock()
    defer rs.mu.RUnlock()
    return rs.currentTerm, rs.state == Leader
}
```

### 6.2 协程设计

- **选举定时器协程**：监控选举超时
- **心跳协程**：定期发送心跳
- **日志复制协程**：并行复制日志
- **状态机应用协程**：应用已提交的日志
- **快照协程**：定期创建快照
- **成员变更协程**：处理成员变更请求

### 6.3 通道通信

```go
type RaftNode struct {
    applyCh chan ApplyMsg  // 状态机应用通道
    stopCh  chan struct{}  // 停止信号通道
}
```

### 6.4 快照实现

```go
type SnapshotManager struct {
    state           *RaftState
    peers           map[int64]*Peer
    lastIncludedIdx int64
    lastIncludedTerm int64
    data            []byte
}

func (sm *SnapshotManager) CreateSnapshot(lastIncludedIndex int64, data []byte) {
    // 1. 获取 lastIncludedIndex 处的任期
    // 2. 保存快照数据
    // 3. 截断日志
}
```

### 6.5 成员变更实现

```go
type MembershipManager struct {
    state      *RaftState
    peers      *map[int64]*Peer
    pendingCh  chan MembershipChange
}

func (mm *MembershipManager) RequestChange(change MembershipChange) error {
    // 1. 检查是否是领导者
    // 2. 验证变更请求
    // 3. 执行变更
}
```

## 七、常见问题

### 7.1 选票分割

**问题**：多个候选人同时发起选举，导致选票分割。

**解决**：
- 随机化选举超时时间
- 设置合理的超时范围
- 使用指数退避策略

### 7.2 日志不一致

**问题**：节点间日志不一致，导致复制失败。

**解决**：
- 实现日志回退机制
- 使用 conflictIndex 和 conflictTerm
- 逐步回退直到找到匹配点

### 7.3 网络分区

**问题**：网络分区导致节点无法通信。

**解决**：
- 实现超时重试机制
- 使用心跳检测节点状态
- 支持节点重新加入

## 八、学习资源

### 8.1 官方资源

- [Raft 论文](https://raft.github.io/raft.pdf)
- [Raft 可视化](http://raft.github.io/)
- [Raft 作者讲解](https://www.youtube.com/watch?v=YbZ3zDzDnrw)

### 8.2 Go 实现参考

- [etcd/raft 源码](https://github.com/etcd-io/raft)
- [hashicorp/raft 源码](https://github.com/hashicorp/raft)

### 8.3 中文资源

- [Raft 一致性算法](https://www.cnblogs.com/mindwind/p/5231986.html)
- [Raft 算法详解](https://zhuanlan.zhihu.com/p/27207160)

## 九、快照机制

### 9.1 为什么需要快照？

日志会无限增长，快照机制用于压缩日志：
- 保存状态机当前状态
- 删除快照点之前的日志
- 减少存储空间和恢复时间

### 9.2 快照创建流程

1. 状态机创建快照
2. 保存快照元数据（lastIncludedIndex, lastIncludedTerm）
3. 截断日志
4. 持久化快照数据

### 9.3 快照传输

当跟随者落后太多时，领导者发送快照：
1. 领导者发送 InstallSnapshot RPC
2. 跟随者接收并安装快照
3. 跟随者重置日志和状态

## 十、成员变更

### 10.1 单节点变更

一次只添加或移除一个节点，确保安全性：
- 添加节点：新节点以只读模式加入，追上进度后正式加入
- 移除节点：确保移除后仍有多数节点

### 10.2 联合共识

两阶段成员变更：
1. 阶段一：旧配置和新配置同时生效
2. 阶段二：新配置生效

## 十一、客户端交互

### 11.1 线性一致性读

确保读取到最新提交的数据：
1. 确认领导权（发送心跳）
2. 等待 commitIndex 被应用
3. 执行读操作

### 11.2 命令转发

非领导者自动转发请求到领导者：
1. 检查是否是领导者
2. 获取领导者地址
3. 转发请求

## 十二、总结

### 12.1 核心要点

1. **领导者选举**：随机化超时避免选票分割
2. **日志复制**：领导者负责复制，大多数确认后提交
3. **安全性**：选举限制确保日志完整性
4. **快照机制**：日志压缩防止无限增长
5. **成员变更**：支持集群动态调整
6. **客户端交互**：提供线性一致性接口

### 12.2 实践建议

1. **理解原理**：先理解算法原理再实现
2. **测试驱动**：先写测试再写实现
3. **增量开发**：逐步完善功能
4. **故障测试**：测试各种故障场景

### 12.3 进阶学习

1. **性能优化**：优化网络传输和存储性能
2. **持久化存储**：实现 BoltDB 等持久化存储
3. **监控告警**：实现集群监控和告警
4. **生产部署**：部署到生产环境
# 04 - 测试策略

## 1. 测试层次

### 1.1 单元测试

测试单个函数或方法的功能：

```go
func TestStateTransitions(t *testing.T) {
    state := raft.NewRaftState(1)

    // 测试状态转换
    assert.Equal(t, raft.Follower, state.GetNodeState())

    state.SetNodeState(raft.Candidate)
    assert.Equal(t, raft.Candidate, state.GetNodeState())

    state.SetNodeState(raft.Leader)
    assert.Equal(t, raft.Leader, state.GetNodeState())
}
```

### 1.2 集成测试

测试多个组件协同工作：

```go
func TestRaftNodeCreation(t *testing.T) {
    config := raft.Config{
        ID: 1,
        Address: "localhost:50051",
        Peers: map[int64]string{},
    }

    node := raft.NewRaftNode(config)
    assert.NotNil(t, node)
}
```

### 1.3 端到端测试

测试完整的业务流程：

```go
func TestClusterElection(t *testing.T) {
    // 创建集群
    // 触发选举
    // 验证领导者产生
}
```

### 1.4 故障测试

测试系统在故障情况下的行为：

```go
func TestNetworkPartition(t *testing.T) {
    // 创建集群
    // 模拟网络分区
    // 验证多数分区能继续工作
    // 验证少数分区无法选出领导者
}

func TestNodeFailure(t *testing.T) {
    // 创建集群
    // 停止部分节点
    // 验证集群能继续工作
    // 重启节点
    // 验证集群恢复正常
}
```

## 2. 测试覆盖

### 2.1 选举测试

- 基本选举流程
- 任期管理
- 投票机制
- 并发选举

### 2.2 日志复制测试

- 日志追加
- 日志复制
- 提交确认
- 日志一致性

### 2.3 状态机测试

- 命令应用
- 快照创建
- 快照恢复

### 2.4 快照测试

- 快照创建
- 日志截断
- 多次快照
- 快照安装

### 2.5 成员变更测试

- 添加节点
- 移除节点
- 非领导者拒绝变更
- 不能移除自己

### 2.6 网络分区测试

- 基本分区
- 分区恢复
- 多数分区选举
- 少数分区无法选举
- 对称分区

### 2.7 节点故障测试

- 单节点故障
- 多节点故障
- 多数故障
- 节点重启
- 领导者故障
- 并发节点操作

### 2.8 并发测试

- 并发读写
- 竞态条件检测
- 死锁检测

## 3. 测试工具

### 3.1 测试框架

- Go testing：标准库
- testify：断言库

### 3.2 测试命令

```bash
# 运行所有测试
go test ./...

# 运行特定测试
go test ./internal/raft/ -v -run TestElection

# 运行测试并显示覆盖率
go test ./... -coverprofile=coverage.out

# 查看覆盖率报告
go tool cover -html=coverage.out
```

### 3.3 竞态检测

```bash
# 运行竞态检测
go test -race ./...
```

## 4. 测试用例

### 4.1 选举测试用例

| 测试用例 | 描述 | 预期结果 |
|----------|------|----------|
| TestElectionBasic | 基本选举流程 | 节点成功当选 |
| TestStateTransitions | 状态转换 | 状态正确更新 |
| TestTermManagement | 任期管理 | 任期正确递增 |
| TestVoting | 投票机制 | 投票正确记录 |
| TestHandleRequestVote | 投票请求处理 | 投票正确响应 |
| TestRequestVoteHigherTerm | 更高任期请求 | 更新任期并投票 |
| TestRequestVoteLowerTerm | 更低任期请求 | 拒绝投票 |

### 4.2 日志复制测试用例

| 测试用例 | 描述 | 预期结果 |
|----------|------|----------|
| TestLogEntryAppend | 日志追加 | 日志正确追加 |
| TestLogEntryMultiple | 多条日志 | 日志数量正确 |
| TestLogTruncation | 日志截断 | 日志正确截断 |
| TestCommitIndex | 提交索引 | 索引正确更新 |
| TestLastApplied | 应用索引 | 索引正确更新 |
| TestLogReplicationBasic | 基本复制 | 日志正确复制 |
| TestLogReplicationFollowerReject | 跟随者拒绝 | 拒绝追加请求 |

### 4.3 集成测试用例

| 测试用例 | 描述 | 预期结果 |
|----------|------|----------|
| TestKVStateMachine | KV 状态机 | 命令正确执行 |
| TestKVStateMachineSnapshot | 快照创建 | 快照正确创建 |
| TestConcurrentStateAccess | 并发状态访问 | 无竞态条件 |
| TestConcurrentLogAccess | 并发日志访问 | 无竞态条件 |
| TestLogConsistency | 日志一致性 | 日志顺序正确 |

### 4.4 快照测试用例

| 测试用例 | 描述 | 预期结果 |
|----------|------|----------|
| TestSnapshotCreation | 创建快照 | 快照正确创建 |
| TestSnapshotTruncatesLog | 日志截断 | 日志正确截断 |
| TestNoSnapshotInitially | 初始状态 | 无快照 |
| TestMultipleSnapshots | 多次快照 | 快照正确更新 |

### 4.5 成员变更测试用例

| 测试用例 | 描述 | 预期结果 |
|----------|------|----------|
| TestMembershipAddNode | 添加节点 | 节点正确添加 |
| TestMembershipIsMember | 成员检查 | 正确识别成员 |
| TestMembershipRemoveNode | 移除节点 | 节点正确移除 |
| TestMembershipNonLeaderReject | 非领导者拒绝 | 拒绝变更请求 |
| TestMembershipCannotRemoveSelf | 不能移除自己 | 拒绝移除请求 |

### 4.6 网络分区测试用例

| 测试用例 | 描述 | 预期结果 |
|----------|------|----------|
| TestNetworkPartitionBasic | 基本分区 | 分区正确创建 |
| TestNetworkPartitionHeal | 分区恢复 | 分区正确恢复 |
| TestNetworkPartitionMajority | 多数分区 | 能选出领导者 |
| TestNetworkPartitionMinorityCannotLead | 少数分区 | 无法选出领导者 |
| TestNetworkPartitionSymmetric | 对称分区 | 连接对称断开 |
| TestMultiplePartitions | 多个分区 | 分区正确创建 |
| TestPartitionWithLeader | 领导者分区 | 新领导者正确选出 |

### 4.7 节点故障测试用例

| 测试用例 | 描述 | 预期结果 |
|----------|------|----------|
| TestSingleNodeFailure | 单节点故障 | 集群继续工作 |
| TestMultipleNodeFailures | 多节点故障 | 集群继续工作 |
| TestMajorityFailure | 多数故障 | 集群无法工作 |
| TestNodeRestart | 节点重启 | 节点正确恢复 |
| TestLeaderFailure | 领导者故障 | 新领导者选出 |
| TestLeaderElectionAfterFailure | 故障后选举 | 新领导者正确选出 |
| TestNodeCrashAndRecover | 崩溃恢复 | 节点正确恢复 |
| TestConcurrentNodeOperations | 并发操作 | 无竞态条件 |
| TestClusterMaintainsQuorum | 法定人数 | 正确维护法定人数 |

## 5. 性能测试

### 5.1 基准测试

```go
func BenchmarkLogAppend(b *testing.B) {
    state := raft.NewRaftState(1)
    
    for i := 0; i < b.N; i++ {
        entry := raft.LogEntry{
            Term: 1,
            Index: int64(i + 1),
            Command: "TEST",
        }
        state.AppendLog(entry)
    }
}
```

### 5.2 负载测试

- 并发客户端请求
- 高频日志复制
- 大量状态机操作

### 5.3 压力测试

- 网络延迟模拟
- 节点故障模拟
- 网络分区模拟

## 6. 测试环境

### 6.1 本地测试

```bash
# 单元测试
go test ./internal/...

# 集成测试
go test ./test/...
```

### 6.2 CI/CD 测试

- GitHub Actions 自动测试
- 多平台测试
- 代码覆盖率报告

## 7. 测试最佳实践

### 7.1 测试命名

- 使用描述性名称
- 遵循 `Test_功能_场景` 格式

### 7.2 测试隔离

- 每个测试独立运行
- 不依赖外部状态
- 清理测试数据

### 7.3 断言清晰

- 使用明确的断言
- 提供有意义的错误消息
- 测试边界条件
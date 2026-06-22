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

### 2.4 并发测试

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
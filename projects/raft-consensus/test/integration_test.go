package test

import (
	"sync"
	"testing"
	"time"

	"github.com/raft-consensus/internal/raft"
	"github.com/raft-consensus/internal/statemachine"
	"github.com/stretchr/testify/assert"
)

func TestKVStateMachine(t *testing.T) {
	kv := statemachine.NewKVStateMachine()

	// 测试 PUT 命令
	result := kv.Apply("PUT name raft")
	assert.Contains(t, result, "OK")

	// 测试 GET 命令
	result = kv.Apply("GET name")
	assert.Contains(t, result, "raft")

	// 测试 DELETE 命令
	result = kv.Apply("DELETE name")
	assert.Contains(t, result, "OK")

	// 测试获取不存在的键
	result = kv.Apply("GET name")
	assert.Contains(t, result, "KEY_NOT_FOUND")
}

func TestKVStateMachineInvalidCommand(t *testing.T) {
	kv := statemachine.NewKVStateMachine()

	// 测试无效命令
	result := kv.Apply(123)
	assert.Error(t, result.(error))

	// 测试无效格式
	result = kv.Apply("INVALID")
	assert.Error(t, result.(error))
}

func TestKVStateMachineSnapshot(t *testing.T) {
	kv := statemachine.NewKVStateMachine()

	// 添加一些数据
	kv.Apply("PUT key1 value1")
	kv.Apply("PUT key2 value2")

	// 创建快照
	snapshot := kv.Snapshot()
	assert.NotEmpty(t, snapshot)

	// 创建新的状态机并恢复
	kv2 := statemachine.NewKVStateMachine()
	err := kv2.Restore(snapshot)
	assert.NoError(t, err)

	// 验证数据
	val, exists := kv2.Get("key1")
	assert.True(t, exists)
	assert.Equal(t, "value1", val)

	val, exists = kv2.Get("key2")
	assert.True(t, exists)
	assert.Equal(t, "value2", val)
}

func TestRaftNodeCreation(t *testing.T) {
	config := raft.Config{
		ID:                 1,
		Address:            "localhost:50051",
		Peers:              map[int64]string{},
		ElectionTimeoutMin: 150 * time.Millisecond,
		ElectionTimeoutMax: 300 * time.Millisecond,
		HeartbeatInterval:  50 * time.Millisecond,
	}

	node := raft.NewRaftNode(config)
	assert.NotNil(t, node)
	assert.Equal(t, int64(1), node.GetID())
}

func TestRaftNodeState(t *testing.T) {
	config := raft.Config{
		ID:                 1,
		Address:            "localhost:50051",
		Peers:              map[int64]string{},
		ElectionTimeoutMin: 150 * time.Millisecond,
		ElectionTimeoutMax: 300 * time.Millisecond,
		HeartbeatInterval:  50 * time.Millisecond,
	}

	node := raft.NewRaftNode(config)

	// 初始状态
	term, isLeader := node.GetState()
	assert.Equal(t, int64(0), term)
	assert.False(t, isLeader)
}

func TestRaftNodeApplyChannel(t *testing.T) {
	config := raft.Config{
		ID:                 1,
		Address:            "localhost:50051",
		Peers:              map[int64]string{},
		ElectionTimeoutMin: 150 * time.Millisecond,
		ElectionTimeoutMax: 300 * time.Millisecond,
		HeartbeatInterval:  50 * time.Millisecond,
	}

	node := raft.NewRaftNode(config)
	applyCh := node.GetApplyCh()
	assert.NotNil(t, applyCh)
}

func TestConcurrentStateAccess(t *testing.T) {
	state := raft.NewRaftState(1)

	var wg sync.WaitGroup
	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()

			// 并发读写
			state.SetCurrentTerm(int64(i))
			_ = state.GetCurrentTerm()

			state.SetVotedFor(int64(i))
			_ = state.GetVotedFor()

			state.SetNodeState(raft.NodeState(i % 3))
			_ = state.GetNodeState()

			state.SetCommitIndex(int64(i))
			_ = state.GetCommitIndex()

			state.SetLastApplied(int64(i))
			_ = state.GetLastApplied()
		}(i)
	}
	wg.Wait()

	// 验证没有 panic
	assert.True(t, true)
}

func TestConcurrentLogAccess(t *testing.T) {
	state := raft.NewRaftState(1)

	var wg sync.WaitGroup
	for i := 0; i < 50; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()

			// 并发追加日志
			entry := raft.LogEntry{
				Term:    int64(i),
				Index:   int64(i + 1),
				Command: "TEST",
			}
			state.AppendLog(entry)

			// 并发读取日志
			_ = state.GetLastLogIndex()
			_ = state.GetLastLogTerm()
		}(i)
	}
	wg.Wait()

	// 验证没有 panic
	assert.True(t, true)
}

func TestLogConsistency(t *testing.T) {
	state := raft.NewRaftState(1)

	// 追加日志条目
	for i := 1; i <= 10; i++ {
		entry := raft.LogEntry{
			Term:    1,
			Index:   int64(i),
			Command: "CMD" + string(rune('0'+i)),
		}
		state.AppendLog(entry)
	}

	// 验证日志一致性
	for i := 1; i <= 10; i++ {
		log, exists := state.GetLog(int64(i))
		assert.True(t, exists)
		assert.Equal(t, int64(i), log.Index)
		assert.Equal(t, int64(1), log.Term)
	}
}

func TestStateString(t *testing.T) {
	assert.Equal(t, "Follower", raft.Follower.String())
	assert.Equal(t, "Candidate", raft.Candidate.String())
	assert.Equal(t, "Leader", raft.Leader.String())
	assert.Equal(t, "Unknown", raft.NodeState(99).String())
}
package test

import (
	"testing"
	"time"

	"github.com/raft-consensus/internal/raft"
	pb "github.com/raft-consensus/internal/pb"
	"github.com/stretchr/testify/assert"
)

func TestLogEntryAppend(t *testing.T) {
	state := raft.NewRaftState(1)

	// 追加日志条目
	entry := raft.LogEntry{
		Term:    1,
		Index:   1,
		Command: "PUT key1 value1",
	}

	index := state.AppendLog(entry)
	assert.Equal(t, int64(1), index)

	// 获取日志条目
	log, exists := state.GetLog(1)
	assert.True(t, exists)
	assert.Equal(t, int64(1), log.Term)
	assert.Equal(t, int64(1), log.Index)
	assert.Equal(t, "PUT key1 value1", log.Command)
}

func TestLogEntryMultiple(t *testing.T) {
	state := raft.NewRaftState(1)

	// 追加多个日志条目
	for i := 1; i <= 5; i++ {
		entry := raft.LogEntry{
			Term:    1,
			Index:   int64(i),
			Command: "PUT key" + string(rune('0'+i)) + " value" + string(rune('0'+i)),
		}
		state.AppendLog(entry)
	}

	// 验证日志数量
	assert.Equal(t, int64(5), state.GetLastLogIndex())

	// 获取日志范围
	logs := state.GetLogs(1, 6)
	assert.Equal(t, 5, len(logs))
}

func TestLogTruncation(t *testing.T) {
	state := raft.NewRaftState(1)

	// 追加日志条目
	for i := 1; i <= 5; i++ {
		entry := raft.LogEntry{
			Term:    1,
			Index:   int64(i),
			Command: "PUT key" + string(rune('0'+i)),
		}
		state.AppendLog(entry)
	}

	// 截断日志
	state.TruncateLog(3)

	// 验证截断后的日志
	assert.Equal(t, int64(2), state.GetLastLogIndex())
}

func TestCommitIndex(t *testing.T) {
	state := raft.NewRaftState(1)

	// 初始提交索引应该是 0
	assert.Equal(t, int64(0), state.GetCommitIndex())

	// 更新提交索引
	state.SetCommitIndex(5)
	assert.Equal(t, int64(5), state.GetCommitIndex())
}

func TestLastApplied(t *testing.T) {
	state := raft.NewRaftState(1)

	// 初始应用索引应该是 0
	assert.Equal(t, int64(0), state.GetLastApplied())

	// 更新应用索引
	state.SetLastApplied(3)
	assert.Equal(t, int64(3), state.GetLastApplied())
}

func TestNextIndex(t *testing.T) {
	state := raft.NewRaftState(1)

	// 初始化 nextIndex
	peers := []int64{2, 3}
	state.InitNextIndex(peers)

	// 验证 nextIndex
	assert.Equal(t, int64(1), state.GetNextIndex(2))
	assert.Equal(t, int64(1), state.GetNextIndex(3))
}

func TestMatchIndex(t *testing.T) {
	state := raft.NewRaftState(1)

	// 设置 matchIndex
	state.SetMatchIndex(2, 5)
	state.SetMatchIndex(3, 3)

	// 验证 matchIndex
	assert.Equal(t, int64(5), state.GetMatchIndex(2))
	assert.Equal(t, int64(3), state.GetMatchIndex(3))
}

func TestHardState(t *testing.T) {
	state := raft.NewRaftState(1)

	// 设置状态
	state.SetCurrentTerm(5)
	state.SetVotedFor(2)

	// 获取持久化状态
	hardState := state.GetHardState()
	assert.Equal(t, int64(5), hardState.CurrentTerm)
	assert.Equal(t, int64(2), hardState.VotedFor)
}

func TestLogReplicationBasic(t *testing.T) {
	state := raft.NewRaftState(1)
	peers := make(map[int64]*raft.Peer)
	applyCh := make(chan raft.ApplyMsg, 100)

	replicator := raft.NewLogReplicator(state, peers, applyCh, 50*time.Millisecond)

	// 设置为领导者状态
	state.SetNodeState(raft.Leader)
	state.SetCurrentTerm(1)

	// 追加日志条目
	index, term, ok := replicator.AppendEntries("PUT key1 value1")
	assert.True(t, ok)
	assert.Equal(t, int64(1), index)
	assert.Equal(t, int64(1), term)
}

func TestLogReplicationFollowerReject(t *testing.T) {
	state := raft.NewRaftState(1)
	peers := make(map[int64]*raft.Peer)
	applyCh := make(chan raft.ApplyMsg, 100)

	replicator := raft.NewLogReplicator(state, peers, applyCh, 50*time.Millisecond)

	// 跟随者状态应该拒绝追加
	_, _, ok := replicator.AppendEntries("PUT key1 value1")
	assert.False(t, ok)
}

func TestHandleAppendEntries(t *testing.T) {
	state := raft.NewRaftState(1)
	peers := make(map[int64]*raft.Peer)
	applyCh := make(chan raft.ApplyMsg, 100)

	replicator := raft.NewLogReplicator(state, peers, applyCh, 50*time.Millisecond)

	// 测试追加日志请求
	req := &pb.AppendEntriesRequest{
		Term:         1,
		LeaderId:     2,
		PrevLogIndex: 0,
		PrevLogTerm:  0,
		Entries: []*pb.LogEntry{
			{
				Term:    1,
				Index:   1,
				Command: []byte("PUT key1 value1"),
			},
		},
		LeaderCommit: 0,
	}

	resp := replicator.HandleAppendEntries(req)
	assert.True(t, resp.Success)
	assert.Equal(t, int64(1), resp.Term)
}
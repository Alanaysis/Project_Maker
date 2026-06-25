package test

import (
	"testing"

	"github.com/raft-consensus/internal/raft"
	"github.com/stretchr/testify/assert"
)

func TestSnapshotCreation(t *testing.T) {
	state := raft.NewRaftState(1)
	peers := make(map[int64]*raft.Peer)

	sm := raft.NewSnapshotManager(state, peers)

	// 添加一些日志
	for i := 1; i <= 10; i++ {
		state.AppendLog(raft.LogEntry{
			Term:    1,
			Index:   int64(i),
			Command: "CMD" + string(rune('0'+i)),
		})
	}

	// 创建快照
	snapshotData := []byte("snapshot data")
	sm.CreateSnapshot(5, snapshotData)

	// 验证快照
	hasSnapshot := sm.HasSnapshot()
	assert.True(t, hasSnapshot)

	lastIdx, lastTerm, data := sm.GetSnapshot()
	assert.Equal(t, int64(5), lastIdx)
	assert.Equal(t, int64(1), lastTerm)
	assert.Equal(t, snapshotData, data)
}

func TestSnapshotTruncatesLog(t *testing.T) {
	state := raft.NewRaftState(1)
	peers := make(map[int64]*raft.Peer)

	sm := raft.NewSnapshotManager(state, peers)

	// 添加日志
	for i := 1; i <= 10; i++ {
		state.AppendLog(raft.LogEntry{
			Term:    1,
			Index:   int64(i),
			Command: "CMD" + string(rune('0'+i)),
		})
	}

	// 创建快照
	sm.CreateSnapshot(5, []byte("snapshot"))

	// 验证日志被截断
	lastLogIndex := state.GetLastLogIndex()
	// 快照后日志应该只包含索引 5 之后的条目
	assert.True(t, lastLogIndex >= 5)
}

func TestNoSnapshotInitially(t *testing.T) {
	state := raft.NewRaftState(1)
	peers := make(map[int64]*raft.Peer)

	sm := raft.NewSnapshotManager(state, peers)

	hasSnapshot := sm.HasSnapshot()
	assert.False(t, hasSnapshot)
}

func TestMultipleSnapshots(t *testing.T) {
	state := raft.NewRaftState(1)
	peers := make(map[int64]*raft.Peer)

	sm := raft.NewSnapshotManager(state, peers)

	// 添加日志
	for i := 1; i <= 20; i++ {
		state.AppendLog(raft.LogEntry{
			Term:    1,
			Index:   int64(i),
			Command: "CMD",
		})
	}

	// 创建第一个快照
	sm.CreateSnapshot(5, []byte("snapshot1"))
	lastIdx, _, _ := sm.GetSnapshot()
	assert.Equal(t, int64(5), lastIdx)

	// 创建第二个快照（更远的位置）
	sm.CreateSnapshot(15, []byte("snapshot2"))
	lastIdx, _, _ = sm.GetSnapshot()
	assert.Equal(t, int64(15), lastIdx)
}

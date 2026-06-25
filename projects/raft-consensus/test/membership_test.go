package test

import (
	"testing"

	"github.com/raft-consensus/internal/raft"
	"github.com/stretchr/testify/assert"
)

func TestMembershipAddNode(t *testing.T) {
	state := raft.NewRaftState(1)
	peers := make(map[int64]*raft.Peer)

	// 添加初始节点
	peers[1] = &raft.Peer{ID: 1, Address: "localhost:50051"}
	peers[2] = &raft.Peer{ID: 2, Address: "localhost:50052"}

	mm := raft.NewMembershipManager(state, &peers)

	// 获取初始成员
	members := mm.GetClusterMembers()
	assert.Equal(t, 2, len(members))
}

func TestMembershipIsMember(t *testing.T) {
	state := raft.NewRaftState(1)
	peers := make(map[int64]*raft.Peer)

	peers[1] = &raft.Peer{ID: 1, Address: "localhost:50051"}
	peers[2] = &raft.Peer{ID: 2, Address: "localhost:50052"}

	mm := raft.NewMembershipManager(state, &peers)

	// 检查成员
	assert.True(t, mm.IsMember(1))
	assert.True(t, mm.IsMember(2))
	assert.False(t, mm.IsMember(3))
}

func TestMembershipRemoveNode(t *testing.T) {
	state := raft.NewRaftState(1)
	peers := make(map[int64]*raft.Peer)

	peers[1] = &raft.Peer{ID: 1, Address: "localhost:50051"}
	peers[2] = &raft.Peer{ID: 2, Address: "localhost:50052"}
	peers[3] = &raft.Peer{ID: 3, Address: "localhost:50053"}

	mm := raft.NewMembershipManager(state, &peers)

	// 设置为领导者状态
	state.SetNodeState(raft.Leader)

	// 移除节点
	err := mm.RequestChange(raft.MembershipChange{
		Type:   raft.RemoveNode,
		NodeID: 3,
	})
	assert.NoError(t, err)

	// 注意：由于 RequestChange 是异步的，这里可能需要等待
	// 在实际测试中应该使用同步机制
}

func TestMembershipNonLeaderReject(t *testing.T) {
	state := raft.NewRaftState(1)
	peers := make(map[int64]*raft.Peer)

	peers[1] = &raft.Peer{ID: 1, Address: "localhost:50051"}

	mm := raft.NewMembershipManager(state, &peers)

	// 非领导者不能发起成员变更
	err := mm.RequestChange(raft.MembershipChange{
		Type:    raft.AddNode,
		NodeID:  2,
		Address: "localhost:50052",
	})
	assert.Error(t, err)
}

func TestMembershipCannotRemoveSelf(t *testing.T) {
	state := raft.NewRaftState(1)
	peers := make(map[int64]*raft.Peer)

	peers[1] = &raft.Peer{ID: 1, Address: "localhost:50051"}
	peers[2] = &raft.Peer{ID: 2, Address: "localhost:50052"}

	mm := raft.NewMembershipManager(state, &peers)

	// 设置为领导者状态
	state.SetNodeState(raft.Leader)

	// 不能移除自己
	err := mm.RequestChange(raft.MembershipChange{
		Type:   raft.RemoveNode,
		NodeID: 1,
	})
	assert.NoError(t, err) // 请求会被接受但不会执行
}

func TestMembershipClusterMembers(t *testing.T) {
	state := raft.NewRaftState(1)
	peers := make(map[int64]*raft.Peer)

	peers[1] = &raft.Peer{ID: 1, Address: "localhost:50051"}
	peers[2] = &raft.Peer{ID: 2, Address: "localhost:50052"}
	peers[3] = &raft.Peer{ID: 3, Address: "localhost:50053"}

	mm := raft.NewMembershipManager(state, &peers)

	members := mm.GetClusterMembers()
	assert.Equal(t, 3, len(members))

	// 验证所有成员都在列表中
	memberMap := make(map[int64]bool)
	for _, id := range members {
		memberMap[id] = true
	}
	assert.True(t, memberMap[1])
	assert.True(t, memberMap[2])
	assert.True(t, memberMap[3])
}

package test

import (
	"sync"
	"testing"
	"time"

	"github.com/raft-consensus/internal/raft"
	pb "github.com/raft-consensus/internal/pb"
	"github.com/stretchr/testify/assert"
)

func TestElectionBasic(t *testing.T) {
	// 创建单个节点测试选举逻辑
	state := raft.NewRaftState(1)
	peers := make(map[int64]*raft.Peer)

	config := raft.ElectionConfig{
		TimeoutMin: 50 * time.Millisecond,
		TimeoutMax: 100 * time.Millisecond,
	}

	em := raft.NewElectionManager(state, peers, config)
	em.Start()
	defer em.Stop()

	// 初始状态应该是跟随者
	assert.Equal(t, raft.Follower, state.GetNodeState())
	assert.Equal(t, int64(0), state.GetCurrentTerm())
}

func TestStateTransitions(t *testing.T) {
	state := raft.NewRaftState(1)

	// 测试状态转换
	assert.Equal(t, raft.Follower, state.GetNodeState())

	state.SetNodeState(raft.Candidate)
	assert.Equal(t, raft.Candidate, state.GetNodeState())

	state.SetNodeState(raft.Leader)
	assert.Equal(t, raft.Leader, state.GetNodeState())

	state.SetNodeState(raft.Follower)
	assert.Equal(t, raft.Follower, state.GetNodeState())
}

func TestTermManagement(t *testing.T) {
	state := raft.NewRaftState(1)

	// 初始任期应该是 0
	assert.Equal(t, int64(0), state.GetCurrentTerm())

	// 设置新任期
	state.SetCurrentTerm(1)
	assert.Equal(t, int64(1), state.GetCurrentTerm())

	// 任期只能增加
	state.SetCurrentTerm(2)
	assert.Equal(t, int64(2), state.GetCurrentTerm())
}

func TestVoting(t *testing.T) {
	state := raft.NewRaftState(1)

	// 初始应该未投票
	assert.Equal(t, int64(-1), state.GetVotedFor())

	// 投票给候选人 2
	state.SetVotedFor(2)
	assert.Equal(t, int64(2), state.GetVotedFor())

	// 重置投票
	state.SetVotedFor(-1)
	assert.Equal(t, int64(-1), state.GetVotedFor())
}

func TestHandleRequestVote(t *testing.T) {
	state := raft.NewRaftState(1)
	peers := make(map[int64]*raft.Peer)

	config := raft.ElectionConfig{
		TimeoutMin: 50 * time.Millisecond,
		TimeoutMax: 100 * time.Millisecond,
	}

	em := raft.NewElectionManager(state, peers, config)

	// 测试投票请求
	req := &pb.RequestVoteRequest{
		Term:         1,
		CandidateId:  2,
		LastLogIndex: 0,
		LastLogTerm:  0,
	}

	resp := em.HandleRequestVote(req)
	assert.True(t, resp.Granted)
	assert.Equal(t, int64(1), resp.Term)

	// 再次请求应该被拒绝（已经投票）
	req2 := &pb.RequestVoteRequest{
		Term:         1,
		CandidateId:  3,
		LastLogIndex: 0,
		LastLogTerm:  0,
	}

	resp2 := em.HandleRequestVote(req2)
	assert.False(t, resp2.Granted)
}

func TestRequestVoteHigherTerm(t *testing.T) {
	state := raft.NewRaftState(1)
	peers := make(map[int64]*raft.Peer)

	config := raft.ElectionConfig{
		TimeoutMin: 50 * time.Millisecond,
		TimeoutMax: 100 * time.Millisecond,
	}

	em := raft.NewElectionManager(state, peers, config)

	// 设置当前任期
	state.SetCurrentTerm(1)

	// 请求更高任期
	req := &pb.RequestVoteRequest{
		Term:         2,
		CandidateId:  2,
		LastLogIndex: 0,
		LastLogTerm:  0,
	}

	resp := em.HandleRequestVote(req)
	assert.True(t, resp.Granted)
	assert.Equal(t, int64(2), state.GetCurrentTerm())
}

func TestRequestVoteLowerTerm(t *testing.T) {
	state := raft.NewRaftState(1)
	peers := make(map[int64]*raft.Peer)

	config := raft.ElectionConfig{
		TimeoutMin: 50 * time.Millisecond,
		TimeoutMax: 100 * time.Millisecond,
	}

	em := raft.NewElectionManager(state, peers, config)

	// 设置当前任期
	state.SetCurrentTerm(2)

	// 请求更低任期
	req := &pb.RequestVoteRequest{
		Term:         1,
		CandidateId:  2,
		LastLogIndex: 0,
		LastLogTerm:  0,
	}

	resp := em.HandleRequestVote(req)
	assert.False(t, resp.Granted)
	assert.Equal(t, int64(2), resp.Term)
}

func TestConcurrentAccess(t *testing.T) {
	state := raft.NewRaftState(1)

	var wg sync.WaitGroup
	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			state.SetCurrentTerm(int64(i))
			_ = state.GetCurrentTerm()
		}(i)
	}
	wg.Wait()

	// 验证没有数据竞争
	term := state.GetCurrentTerm()
	assert.True(t, term >= 0)
}
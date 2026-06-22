package raft

import (
	"sync"
)

// NodeState 节点状态类型
type NodeState int

const (
	// Follower 跟随者状态
	Follower NodeState = iota
	// Candidate 候选人状态
	Candidate
	// Leader 领导者状态
	Leader
)

// String 返回状态的字符串表示
func (s NodeState) String() string {
	switch s {
	case Follower:
		return "Follower"
	case Candidate:
		return "Candidate"
	case Leader:
		return "Leader"
	default:
		return "Unknown"
	}
}

// LogEntry 日志条目
type LogEntry struct {
	Term    int64       // 条目创建时的任期号
	Index   int64       // 条目的索引
	Command interface{} // 状态机要执行的命令
}

// HardState 持久化状态
type HardState struct {
	CurrentTerm int64 // 节点看到的最新任期
	VotedFor    int64 // 当前任期投票给的候选人 ID（-1 表示未投票）
}

// RaftState Raft 节点状态
type RaftState struct {
	mu sync.RWMutex

	// 持久化状态（所有服务器上持久化存储）
	currentTerm int64
	votedFor    int64
	log         []LogEntry

	// 易失性状态（所有服务器）
	commitIndex int64
	lastApplied int64

	// 易失性状态（仅领导者）
	nextIndex  map[int64]int64
	matchIndex map[int64]int64

	// 节点信息
	id     int64
	state  NodeState
	leader int64
}

// NewRaftState 创建新的 Raft 状态
func NewRaftState(id int64) *RaftState {
	return &RaftState{
		id:          id,
		currentTerm: 0,
		votedFor:    -1,
		log:         make([]LogEntry, 1), // 索引 0 是空的，日志从索引 1 开始
		commitIndex: 0,
		lastApplied: 0,
		nextIndex:   make(map[int64]int64),
		matchIndex:  make(map[int64]int64),
		state:       Follower,
		leader:      -1,
	}
}

// GetState 获取当前状态（线程安全）
func (rs *RaftState) GetState() (int64, bool) {
	rs.mu.RLock()
	defer rs.mu.RUnlock()
	return rs.currentTerm, rs.state == Leader
}

// GetCurrentTerm 获取当前任期
func (rs *RaftState) GetCurrentTerm() int64 {
	rs.mu.RLock()
	defer rs.mu.RUnlock()
	return rs.currentTerm
}

// SetCurrentTerm 设置当前任期
func (rs *RaftState) SetCurrentTerm(term int64) {
	rs.mu.Lock()
	defer rs.mu.Unlock()
	rs.currentTerm = term
}

// GetVotedFor 获取投票给的候选人
func (rs *RaftState) GetVotedFor() int64 {
	rs.mu.RLock()
	defer rs.mu.RUnlock()
	return rs.votedFor
}

// SetVotedFor 设置投票给的候选人
func (rs *RaftState) SetVotedFor(candidateID int64) {
	rs.mu.Lock()
	defer rs.mu.Unlock()
	rs.votedFor = candidateID
}

// GetState 获取节点状态
func (rs *RaftState) GetNodeState() NodeState {
	rs.mu.RLock()
	defer rs.mu.RUnlock()
	return rs.state
}

// SetState 设置节点状态
func (rs *RaftState) SetNodeState(state NodeState) {
	rs.mu.Lock()
	defer rs.mu.Unlock()
	rs.state = state
}

// GetLeader 获取当前领导者
func (rs *RaftState) GetLeader() int64 {
	rs.mu.RLock()
	defer rs.mu.RUnlock()
	return rs.leader
}

// SetLeader 设置当前领导者
func (rs *RaftState) SetLeader(leaderID int64) {
	rs.mu.Lock()
	defer rs.mu.Unlock()
	rs.leader = leaderID
}

// GetID 获取节点 ID
func (rs *RaftState) GetID() int64 {
	rs.mu.RLock()
	defer rs.mu.RUnlock()
	return rs.id
}

// AppendLog 追加日志条目
func (rs *RaftState) AppendLog(entry LogEntry) int64 {
	rs.mu.Lock()
	defer rs.mu.Unlock()
	rs.log = append(rs.log, entry)
	return int64(len(rs.log) - 1)
}

// GetLog 获取指定索引的日志条目
func (rs *RaftState) GetLog(index int64) (*LogEntry, bool) {
	rs.mu.RLock()
	defer rs.mu.RUnlock()
	if index < 1 || int(index) >= len(rs.log) {
		return nil, false
	}
	return &rs.log[index], true
}

// GetLogs 获取指定范围的日志条目
func (rs *RaftState) GetLogs(start, end int64) []LogEntry {
	rs.mu.RLock()
	defer rs.mu.RUnlock()
	if start < 1 {
		start = 1
	}
	if int(end) > len(rs.log) {
		end = int64(len(rs.log))
	}
	if start >= end {
		return nil
	}
	result := make([]LogEntry, end-start)
	copy(result, rs.log[start:end])
	return result
}

// GetLastLogIndex 获取最后一个日志条目的索引
func (rs *RaftState) GetLastLogIndex() int64 {
	rs.mu.RLock()
	defer rs.mu.RUnlock()
	return int64(len(rs.log) - 1)
}

// GetLastLogTerm 获取最后一个日志条目的任期号
func (rs *RaftState) GetLastLogTerm() int64 {
	rs.mu.RLock()
	defer rs.mu.RUnlock()
	if len(rs.log) <= 1 {
		return 0
	}
	return rs.log[len(rs.log)-1].Term
}

// TruncateLog 从指定索引开始截断日志
func (rs *RaftState) TruncateLog(index int64) {
	rs.mu.Lock()
	defer rs.mu.Unlock()
	if int(index) < len(rs.log) {
		rs.log = rs.log[:index]
	}
}

// GetCommitIndex 获取已提交的最高日志条目索引
func (rs *RaftState) GetCommitIndex() int64 {
	rs.mu.RLock()
	defer rs.mu.RUnlock()
	return rs.commitIndex
}

// SetCommitIndex 设置已提交的最高日志条目索引
func (rs *RaftState) SetCommitIndex(index int64) {
	rs.mu.Lock()
	defer rs.mu.Unlock()
	rs.commitIndex = index
}

// GetLastApplied 获取已应用到状态机的最高日志条目索引
func (rs *RaftState) GetLastApplied() int64 {
	rs.mu.RLock()
	defer rs.mu.RUnlock()
	return rs.lastApplied
}

// SetLastApplied 设置已应用到状态机的最高日志条目索引
func (rs *RaftState) SetLastApplied(index int64) {
	rs.mu.Lock()
	defer rs.mu.Unlock()
	rs.lastApplied = index
}

// GetNextIndex 获取指定节点的下一个日志索引
func (rs *RaftState) GetNextIndex(peerID int64) int64 {
	rs.mu.RLock()
	defer rs.mu.RUnlock()
	return rs.nextIndex[peerID]
}

// SetNextIndex 设置指定节点的下一个日志索引
func (rs *RaftState) SetNextIndex(peerID, index int64) {
	rs.mu.Lock()
	defer rs.mu.Unlock()
	rs.nextIndex[peerID] = index
}

// GetMatchIndex 获取指定节点的最高匹配日志索引
func (rs *RaftState) GetMatchIndex(peerID int64) int64 {
	rs.mu.RLock()
	defer rs.mu.RUnlock()
	return rs.matchIndex[peerID]
}

// SetMatchIndex 设置指定节点的最高匹配日志索引
func (rs *RaftState) SetMatchIndex(peerID, index int64) {
	rs.mu.Lock()
	defer rs.mu.Unlock()
	rs.matchIndex[peerID] = index
}

// InitNextIndex 初始化所有节点的 nextIndex
func (rs *RaftState) InitNextIndex(peers []int64) {
	rs.mu.Lock()
	defer rs.mu.Unlock()
	lastLogIndex := int64(len(rs.log) - 1)
	for _, peerID := range peers {
		rs.nextIndex[peerID] = lastLogIndex + 1
		rs.matchIndex[peerID] = 0
	}
}

// GetHardState 获取持久化状态
func (rs *RaftState) GetHardState() HardState {
	rs.mu.RLock()
	defer rs.mu.RUnlock()
	return HardState{
		CurrentTerm: rs.currentTerm,
		VotedFor:    rs.votedFor,
	}
}

// RestoreState 恢复状态
func (rs *RaftState) RestoreState(hardState HardState, log []LogEntry) {
	rs.mu.Lock()
	defer rs.mu.Unlock()
	rs.currentTerm = hardState.CurrentTerm
	rs.votedFor = hardState.VotedFor
	if log != nil {
		rs.log = log
	}
}
package raft

import (
	"log"
	"sync"

	pb "github.com/raft-consensus/internal/pb"
)

// SnapshotManager 快照管理器
type SnapshotManager struct {
	state           *RaftState
	peers           map[int64]*Peer
	lastIncludedIdx int64
	lastIncludedTerm int64
	data            []byte
	mu              sync.RWMutex
}

// NewSnapshotManager 创建新的快照管理器
func NewSnapshotManager(state *RaftState, peers map[int64]*Peer) *SnapshotManager {
	return &SnapshotManager{
		state: state,
		peers: peers,
	}
}

// CreateSnapshot 创建快照
func (sm *SnapshotManager) CreateSnapshot(lastIncludedIndex int64, data []byte) {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	// 获取 lastIncludedIndex 处的任期
	sm.state.mu.RLock()
	var lastIncludedTerm int64
	if int(lastIncludedIndex) < len(sm.state.log) {
		lastIncludedTerm = sm.state.log[lastIncludedIndex].Term
	}
	sm.state.mu.RUnlock()

	sm.lastIncludedIdx = lastIncludedIndex
	sm.lastIncludedTerm = lastIncludedTerm
	sm.data = data

	// 截断日志
	sm.state.mu.Lock()
	if int(lastIncludedIndex)+1 < len(sm.state.log) {
		// 保留 lastIncludedIndex 作为日志的起点
		newLog := make([]LogEntry, 1)
		newLog[0] = LogEntry{
			Term:  lastIncludedTerm,
			Index: lastIncludedIndex,
		}
		// 保留 lastIncludedIndex 之后的日志
		sm.state.log = append(newLog, sm.state.log[lastIncludedIndex+1:]...)
	} else {
		sm.state.log = []LogEntry{
			{
				Term:  lastIncludedTerm,
				Index: lastIncludedIndex,
			},
		}
	}
	sm.state.mu.Unlock()

	log.Printf("Node %d created snapshot at index %d", sm.state.GetID(), lastIncludedIndex)
}

// GetSnapshot 获取快照数据
func (sm *SnapshotManager) GetSnapshot() (int64, int64, []byte) {
	sm.mu.RLock()
	defer sm.mu.RUnlock()
	return sm.lastIncludedIdx, sm.lastIncludedTerm, sm.data
}

// HasSnapshot 检查是否有快照
func (sm *SnapshotManager) HasSnapshot() bool {
	sm.mu.RLock()
	defer sm.mu.RUnlock()
	return sm.lastIncludedIdx > 0
}

// InstallSnapshot 安装快照（从领导者接收）
func (sm *SnapshotManager) InstallSnapshot(req *pb.InstallSnapshotRequest) {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	// 更新快照元数据
	sm.lastIncludedIdx = req.LastIncludedIndex
	sm.lastIncludedTerm = req.LastIncludedTerm
	sm.data = req.Data

	// 重置日志
	sm.state.mu.Lock()
	sm.state.log = []LogEntry{
		{
			Term:  req.LastIncludedTerm,
			Index: req.LastIncludedIndex,
		},
	}
	// 更新 commitIndex 和 lastApplied
	if req.LastIncludedIndex > sm.state.commitIndex {
		sm.state.commitIndex = req.LastIncludedIndex
	}
	if req.LastIncludedIndex > sm.state.lastApplied {
		sm.state.lastApplied = req.LastIncludedIndex
	}
	sm.state.mu.Unlock()

	log.Printf("Node %d installed snapshot at index %d", sm.state.GetID(), req.LastIncludedIndex)
}

// SendSnapshot 发送快照到指定节点
func (sm *SnapshotManager) SendSnapshot(peer *Peer) {
	sm.mu.RLock()
	lastIncludedIdx := sm.lastIncludedIdx
	lastIncludedTerm := sm.lastIncludedTerm
	data := sm.data
	sm.mu.RUnlock()

	if lastIncludedIdx == 0 {
		return
	}

	req := &pb.InstallSnapshotRequest{
		Term:              sm.state.GetCurrentTerm(),
		LeaderId:          sm.state.GetID(),
		LastIncludedIndex: lastIncludedIdx,
		LastIncludedTerm:  lastIncludedTerm,
		Data:              data,
	}

	resp, err := peer.Client.InstallSnapshot(nil, req)
	if err != nil {
		log.Printf("Node %d: failed to send snapshot to %d: %v", sm.state.GetID(), peer.ID, err)
		return
	}

	// 检查任期
	if resp.Term > sm.state.GetCurrentTerm() {
		sm.state.SetCurrentTerm(resp.Term)
		sm.state.SetNodeState(Follower)
		sm.state.SetVotedFor(-1)
		return
	}

	// 更新 nextIndex 和 matchIndex
	sm.state.SetNextIndex(peer.ID, lastIncludedIdx+1)
	sm.state.SetMatchIndex(peer.ID, lastIncludedIdx)

	log.Printf("Node %d sent snapshot to node %d, updated nextIndex to %d",
		sm.state.GetID(), peer.ID, lastIncludedIdx+1)
}

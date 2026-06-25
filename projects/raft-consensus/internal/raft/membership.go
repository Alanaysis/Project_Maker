package raft

import (
	"fmt"
	"log"
	"sync"
)

// MembershipChangeType 成员变更类型
type MembershipChangeType int

const (
	// AddNode 添加节点
	AddNode MembershipChangeType = iota
	// RemoveNode 移除节点
	RemoveNode
)

// MembershipChange 成员变更请求
type MembershipChange struct {
	Type    MembershipChangeType
	NodeID  int64
	Address string
}

// MembershipManager 成员变更管理器
type MembershipManager struct {
	state      *RaftState
	peers      *map[int64]*Peer
	pendingCh  chan MembershipChange
	stopCh     chan struct{}
	mu         sync.RWMutex
}

// NewMembershipManager 创建新的成员变更管理器
func NewMembershipManager(state *RaftState, peers *map[int64]*Peer) *MembershipManager {
	return &MembershipManager{
		state:     state,
		peers:     peers,
		pendingCh: make(chan MembershipChange, 10),
		stopCh:    make(chan struct{}),
	}
}

// Start 启动成员变更管理器
func (mm *MembershipManager) Start() {
	go mm.run()
}

// Stop 停止成员变更管理器
func (mm *MembershipManager) Stop() {
	close(mm.stopCh)
}

// RequestChange 请求成员变更
func (mm *MembershipManager) RequestChange(change MembershipChange) error {
	mm.mu.RLock()
	isLeader := mm.state.GetNodeState() == Leader
	mm.mu.RUnlock()

	if !isLeader {
		return fmt.Errorf("only leader can propose membership changes")
	}

	select {
	case mm.pendingCh <- change:
		return nil
	default:
		return fmt.Errorf("membership change queue is full")
	}
}

// run 运行成员变更处理
func (mm *MembershipManager) run() {
	for {
		select {
		case change := <-mm.pendingCh:
			mm.handleChange(change)
		case <-mm.stopCh:
			return
		}
	}
}

// handleChange 处理成员变更
func (mm *MembershipManager) handleChange(change MembershipChange) {
	mm.mu.Lock()
	defer mm.mu.Unlock()

	// 检查是否是领导者
	if mm.state.GetNodeState() != Leader {
		log.Printf("Node %d is not leader, ignoring membership change", mm.state.GetID())
		return
	}

	switch change.Type {
	case AddNode:
		mm.handleAddNode(change)
	case RemoveNode:
		mm.handleRemoveNode(change)
	}
}

// handleAddNode 处理添加节点
func (mm *MembershipManager) handleAddNode(change MembershipChange) {
	mm.state.mu.Lock()

	// 检查节点是否已存在
	if _, exists := (*mm.peers)[change.NodeID]; exists {
		mm.state.mu.Unlock()
		log.Printf("Node %d already exists in cluster", change.NodeID)
		return
	}

	// 获取当前日志索引
	lastLogIndex := mm.state.GetLastLogIndex()

	// 初始化新节点的 nextIndex 和 matchIndex
	mm.state.nextIndex[change.NodeID] = lastLogIndex + 1
	mm.state.matchIndex[change.NodeID] = 0

	mm.state.mu.Unlock()

	// 添加到 peers 映射
	// 注意：实际的 gRPC 连接需要在外部建立
	log.Printf("Node %d added to cluster at %s", change.NodeID, change.Address)
}

// handleRemoveNode 处理移除节点
func (mm *MembershipManager) handleRemoveNode(change MembershipChange) {
	mm.state.mu.Lock()
	defer mm.state.mu.Unlock()

	// 检查节点是否存在
	if _, exists := (*mm.peers)[change.NodeID]; !exists {
		log.Printf("Node %d does not exist in cluster", change.NodeID)
		return
	}

	// 不能移除自己
	if change.NodeID == mm.state.id {
		log.Printf("Cannot remove self from cluster")
		return
	}

	// 从 peers 中移除
	delete(*mm.peers, change.NodeID)

	// 清理 nextIndex 和 matchIndex
	delete(mm.state.nextIndex, change.NodeID)
	delete(mm.state.matchIndex, change.NodeID)

	log.Printf("Node %d removed from cluster", change.NodeID)
}

// GetClusterMembers 获取集群成员列表
func (mm *MembershipManager) GetClusterMembers() []int64 {
	mm.mu.RLock()
	defer mm.mu.RUnlock()

	mm.state.mu.RLock()
	defer mm.state.mu.RUnlock()

	members := make([]int64, 0, len(*mm.peers))
	for id := range *mm.peers {
		members = append(members, id)
	}
	return members
}

// IsMember 检查节点是否是集群成员
func (mm *MembershipManager) IsMember(nodeID int64) bool {
	mm.mu.RLock()
	defer mm.mu.RUnlock()

	_, exists := (*mm.peers)[nodeID]
	return exists
}

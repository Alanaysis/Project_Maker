package test

import (
	"sync"
	"testing"
	"time"

	"github.com/raft-consensus/internal/raft"
	"github.com/stretchr/testify/assert"
)

// NodeState 节点运行状态
type NodeState int

const (
	NodeRunning NodeState = iota
	NodeStopped
	NodeCrashed
)

// TestNode 节点封装
type TestNode struct {
	ID          int64
	State       *raft.RaftState
	Status      NodeState
	mu          sync.RWMutex
}

// TestCluster 测试集群
type TestCluster struct {
	nodes    map[int64]*TestNode
	mu       sync.RWMutex
}

// NewTestCluster 创建测试集群
func NewTestCluster(nodeCount int) *TestCluster {
	cluster := &TestCluster{
		nodes: make(map[int64]*TestNode),
	}

	for i := 1; i <= nodeCount; i++ {
		id := int64(i)
		cluster.nodes[id] = &TestNode{
			ID:     id,
			State:  raft.NewRaftState(id),
			Status: NodeRunning,
		}
	}

	return cluster
}

// StopNode 停止节点
func (tc *TestCluster) StopNode(nodeID int64) {
	tc.mu.Lock()
	defer tc.mu.Unlock()

	if node, exists := tc.nodes[nodeID]; exists {
		node.mu.Lock()
		node.Status = NodeStopped
		node.mu.Unlock()
	}
}

// CrashNode 模拟节点崩溃
func (tc *TestCluster) CrashNode(nodeID int64) {
	tc.mu.Lock()
	defer tc.mu.Unlock()

	if node, exists := tc.nodes[nodeID]; exists {
		node.mu.Lock()
		node.Status = NodeCrashed
		node.mu.Unlock()
	}
}

// RestartNode 重启节点
func (tc *TestCluster) RestartNode(nodeID int64) {
	tc.mu.Lock()
	defer tc.mu.Unlock()

	if node, exists := tc.nodes[nodeID]; exists {
		node.mu.Lock()
		node.Status = NodeRunning
		node.mu.Unlock()
	}
}

// GetRunningNodes 获取运行中的节点
func (tc *TestCluster) GetRunningNodes() []int64 {
	tc.mu.RLock()
	defer tc.mu.RUnlock()

	var running []int64
	for id, node := range tc.nodes {
		node.mu.RLock()
		if node.Status == NodeRunning {
			running = append(running, id)
		}
		node.mu.RUnlock()
	}
	return running
}

// GetRunningNodeCount 获取运行中的节点数量
func (tc *TestCluster) GetRunningNodeCount() int {
	return len(tc.GetRunningNodes())
}

// CanElectLeader 检查是否能选出领导者
func (tc *TestCluster) CanElectLeader() bool {
	running := tc.GetRunningNodeCount()
	majority := len(tc.nodes)/2 + 1
	return running >= majority
}

func TestSingleNodeFailure(t *testing.T) {
	cluster := NewTestCluster(5)

	// 初始状态：所有节点运行
	assert.Equal(t, 5, cluster.GetRunningNodeCount())

	// 停止一个节点
	cluster.StopNode(3)

	// 剩余节点应该能维持集群
	assert.Equal(t, 4, cluster.GetRunningNodeCount())
	assert.True(t, cluster.CanElectLeader())
}

func TestMultipleNodeFailures(t *testing.T) {
	cluster := NewTestCluster(5)

	// 停止两个节点
	cluster.StopNode(4)
	cluster.StopNode(5)

	// 剩余节点应该能维持集群
	assert.Equal(t, 3, cluster.GetRunningNodeCount())
	assert.True(t, cluster.CanElectLeader())
}

func TestMajorityFailure(t *testing.T) {
	cluster := NewTestCluster(5)

	// 停止三个节点（多数）
	cluster.StopNode(3)
	cluster.StopNode(4)
	cluster.StopNode(5)

	// 集群无法正常工作
	assert.Equal(t, 2, cluster.GetRunningNodeCount())
	assert.False(t, cluster.CanElectLeader())
}

func TestNodeRestart(t *testing.T) {
	cluster := NewTestCluster(5)

	// 停止节点
	cluster.StopNode(3)
	assert.Equal(t, 4, cluster.GetRunningNodeCount())

	// 重启节点
	cluster.RestartNode(3)
	assert.Equal(t, 5, cluster.GetRunningNodeCount())
	assert.True(t, cluster.CanElectLeader())
}

func TestLeaderFailure(t *testing.T) {
	// 模拟领导者故障场景
	state := raft.NewRaftState(1)

	// 设置为领导者
	state.SetNodeState(raft.Leader)
	state.SetCurrentTerm(1)

	// 验证是领导者
	_, isLeader := state.GetState()
	assert.True(t, isLeader)

	// 模拟领导者故障（转换为跟随者）
	state.SetNodeState(raft.Follower)

	// 验证不再是领导者
	_, isLeader = state.GetState()
	assert.False(t, isLeader)
}

func TestLeaderElectionAfterFailure(t *testing.T) {
	// 模拟领导者故障后的选举
	cluster := NewTestCluster(5)

	// 假设节点 1 是领导者
	cluster.nodes[1].State.SetNodeState(raft.Leader)
	cluster.nodes[1].State.SetCurrentTerm(1)

	// 领导者故障
	cluster.StopNode(1)

	// 剩余节点应该能选出新领导者
	assert.True(t, cluster.CanElectLeader())

	// 模拟选举过程
	running := cluster.GetRunningNodes()
	assert.Equal(t, 4, len(running))

	// 选择一个节点作为新领导者
	newLeaderID := running[0]
	cluster.nodes[newLeaderID].State.SetNodeState(raft.Leader)
	cluster.nodes[newLeaderID].State.SetCurrentTerm(2)

	// 验证新领导者
	_, isLeader := cluster.nodes[newLeaderID].State.GetState()
	assert.True(t, isLeader)
	assert.Equal(t, int64(2), cluster.nodes[newLeaderID].State.GetCurrentTerm())
}

func TestNodeCrashAndRecover(t *testing.T) {
	cluster := NewTestCluster(5)

	// 节点崩溃
	cluster.CrashNode(2)
	assert.Equal(t, 4, cluster.GetRunningNodeCount())

	// 节点恢复
	cluster.RestartNode(2)
	assert.Equal(t, 5, cluster.GetRunningNodeCount())
}

func TestConcurrentNodeOperations(t *testing.T) {
	cluster := NewTestCluster(5)

	var wg sync.WaitGroup

	// 并发停止和重启节点
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			nodeID := int64(i%5 + 1)
			if i%2 == 0 {
				cluster.StopNode(nodeID)
			} else {
				cluster.RestartNode(nodeID)
			}
		}(i)
	}

	wg.Wait()

	// 验证没有 panic
	assert.True(t, true)
}

func TestElectionTimeoutAfterFailure(t *testing.T) {
	state := raft.NewRaftState(1)
	peers := make(map[int64]*raft.Peer)

	config := raft.ElectionConfig{
		TimeoutMin: 50 * time.Millisecond,
		TimeoutMax: 100 * time.Millisecond,
	}

	em := raft.NewElectionManager(state, peers, config)

	// 启动选举管理器
	em.Start()

	// 等待选举超时
	time.Sleep(150 * time.Millisecond)

	// 节点应该尝试发起选举
	// 由于没有 peers，会失败并回到跟随者状态
	assert.Equal(t, raft.Follower, state.GetNodeState())

	em.Stop()
}

func TestClusterMaintainsQuorum(t *testing.T) {
	cluster := NewTestCluster(7)

	// 逐步停止节点
	for i := 1; i <= 7; i++ {
		cluster.StopNode(int64(i))

		remaining := cluster.GetRunningNodeCount()
		majority := 4

		if remaining >= majority {
			assert.True(t, cluster.CanElectLeader())
		} else {
			assert.False(t, cluster.CanElectLeader())
		}
	}
}

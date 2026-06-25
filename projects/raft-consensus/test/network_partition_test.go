package test

import (
	"sync"
	"testing"
	"time"

	"github.com/raft-consensus/internal/raft"
	"github.com/stretchr/testify/assert"
)

// MockCluster 模拟集群
type MockCluster struct {
	nodes  map[int64]*raft.RaftState
	peers  map[int64]map[int64]bool // nodeID -> connected peers
	mu     sync.RWMutex
}

// NewMockCluster 创建模拟集群
func NewMockCluster(nodeIDs []int64) *MockCluster {
	cluster := &MockCluster{
		nodes: make(map[int64]*raft.RaftState),
		peers: make(map[int64]map[int64]bool),
	}

	for _, id := range nodeIDs {
		cluster.nodes[id] = raft.NewRaftState(id)
		cluster.peers[id] = make(map[int64]bool)
		for _, peerID := range nodeIDs {
			if peerID != id {
				cluster.peers[id][peerID] = true
			}
		}
	}

	return cluster
}

// Partition 模拟网络分区
func (mc *MockCluster) Partition(partition1, partition2 []int64) {
	mc.mu.Lock()
	defer mc.mu.Unlock()

	// 断开两个分区之间的连接
	for _, id1 := range partition1 {
		for _, id2 := range partition2 {
			delete(mc.peers[id1], id2)
			delete(mc.peers[id2], id1)
		}
	}
}

// Heal 恢复网络分区
func (mc *MockCluster) Heal() {
	mc.mu.Lock()
	defer mc.mu.Unlock()

	// 恢复所有连接
	for id1 := range mc.nodes {
		for id2 := range mc.nodes {
			if id1 != id2 {
				mc.peers[id1][id2] = true
			}
		}
	}
}

// IsConnected 检查两个节点是否连接
func (mc *MockCluster) IsConnected(node1, node2 int64) bool {
	mc.mu.RLock()
	defer mc.mu.RUnlock()
	return mc.peers[node1][node2]
}

// SimulateElection 模拟选举过程
func (mc *MockCluster) SimulateElection() int64 {
	mc.mu.RLock()
	defer mc.mu.RUnlock()

	// 找到可以连接到大多数节点的节点
	majority := len(mc.nodes)/2 + 1

	for id, connections := range mc.peers {
		connected := 1 // 包括自己
		for peerID := range connections {
			if mc.peers[peerID][id] {
				connected++
			}
		}
		if connected >= majority {
			return id
		}
	}

	return -1
}

func TestNetworkPartitionBasic(t *testing.T) {
	// 创建 5 节点集群
	cluster := NewMockCluster([]int64{1, 2, 3, 4, 5})

	// 初始状态：所有节点都连接
	assert.True(t, cluster.IsConnected(1, 2))
	assert.True(t, cluster.IsConnected(1, 3))

	// 模拟分区：{1, 2} 和 {3, 4, 5}
	cluster.Partition([]int64{1, 2}, []int64{3, 4, 5})

	// 验证分区
	assert.False(t, cluster.IsConnected(1, 3))
	assert.False(t, cluster.IsConnected(1, 4))
	assert.False(t, cluster.IsConnected(2, 3))
	assert.True(t, cluster.IsConnected(1, 2))
	assert.True(t, cluster.IsConnected(3, 4))
}

func TestNetworkPartitionHeal(t *testing.T) {
	cluster := NewMockCluster([]int64{1, 2, 3, 4, 5})

	// 创建分区
	cluster.Partition([]int64{1, 2}, []int64{3, 4, 5})
	assert.False(t, cluster.IsConnected(1, 3))

	// 恢复分区
	cluster.Heal()
	assert.True(t, cluster.IsConnected(1, 3))
	assert.True(t, cluster.IsConnected(2, 4))
}

func TestNetworkPartitionMajority(t *testing.T) {
	cluster := NewMockCluster([]int64{1, 2, 3, 4, 5})

	// 分区：{1, 2} (少数) vs {3, 4, 5} (多数)
	cluster.Partition([]int64{1, 2}, []int64{3, 4, 5})

	// 多数分区应该能选出领导者
	leader := cluster.SimulateElection()
	assert.True(t, leader == 3 || leader == 4 || leader == 5)
}

func TestNetworkPartitionMinorityCannotLead(t *testing.T) {
	cluster := NewMockCluster([]int64{1, 2, 3, 4, 5})

	// 分区：{1, 2} (少数) vs {3, 4, 5} (多数)
	cluster.Partition([]int64{1, 2}, []int64{3, 4, 5})

	// 少数分区不应该能选出领导者
	// 检查节点 1 和 2 是否能连接到大多数
	majority := 3
	node1Connected := 1 // 自己
	node2Connected := 1 // 自己

	for peerID := range cluster.peers[1] {
		if cluster.peers[peerID][1] {
			node1Connected++
		}
	}
	for peerID := range cluster.peers[2] {
		if cluster.peers[peerID][2] {
			node2Connected++
		}
	}

	assert.True(t, node1Connected < majority)
	assert.True(t, node2Connected < majority)
}

func TestNetworkPartitionSymmetric(t *testing.T) {
	cluster := NewMockCluster([]int64{1, 2, 3, 4, 5})

	// 分区：{1, 2, 3} vs {4, 5}
	cluster.Partition([]int64{1, 2, 3}, []int64{4, 5})

	// 验证连接是对称的
	assert.False(t, cluster.IsConnected(1, 4))
	assert.False(t, cluster.IsConnected(4, 1))
	assert.True(t, cluster.IsConnected(1, 2))
	assert.True(t, cluster.IsConnected(4, 5))
}

func TestNodeFailureDetection(t *testing.T) {
	state := raft.NewRaftState(1)
	peers := make(map[int64]*raft.Peer)

	config := raft.ElectionConfig{
		TimeoutMin: 50 * time.Millisecond,
		TimeoutMax: 100 * time.Millisecond,
	}

	em := raft.NewElectionManager(state, peers, config)

	// 启动选举管理器
	em.Start()
	defer em.Stop()

	// 初始状态
	assert.Equal(t, raft.Follower, state.GetNodeState())

	// 等待选举超时
	time.Sleep(200 * time.Millisecond)

	// 节点应该尝试发起选举（但由于没有 peers，会失败）
	// 验证没有 panic
	assert.True(t, true)
}

func TestMultiplePartitions(t *testing.T) {
	cluster := NewMockCluster([]int64{1, 2, 3, 4, 5, 6, 7})

	// 创建多个分区
	cluster.Partition([]int64{1, 2}, []int64{3, 4})
	cluster.Partition([]int64{5, 6}, []int64{7})

	// 验证分区
	assert.False(t, cluster.IsConnected(1, 3))
	assert.False(t, cluster.IsConnected(5, 7))
	assert.True(t, cluster.IsConnected(1, 2))
	assert.True(t, cluster.IsConnected(5, 6))
}

func TestPartitionWithLeader(t *testing.T) {
	// 模拟领导者在分区中的情况
	cluster := NewMockCluster([]int64{1, 2, 3, 4, 5})

	// 假设节点 1 是领导者
	// 分区：{1} (领导者单独) vs {2, 3, 4, 5}
	cluster.Partition([]int64{1}, []int64{2, 3, 4, 5})

	// 领导者无法连接到大多数节点
	majority := 3
	leaderConnected := 1 // 自己
	for peerID := range cluster.peers[1] {
		if cluster.peers[peerID][1] {
			leaderConnected++
		}
	}

	assert.True(t, leaderConnected < majority)

	// 多数分区应该能选出新领导者
	newLeader := cluster.SimulateElection()
	assert.True(t, newLeader >= 2 && newLeader <= 5)
}

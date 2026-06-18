package hashing

import (
	"crypto/sha256"
	"encoding/binary"
	"fmt"
	"sort"
	"sync"
)

// ⭐ 一致性哈希 (Consistent Hashing)
//
// 核心思想：将服务器和玩家映射到同一个哈希环上。
//
// 为什么需要一致性哈希？
// - 普通哈希：当服务器数量变化时，几乎所有玩家都需要重新分配
// - 一致性哈希：只有 1/n 的玩家需要重新分配
//
// 哈希环示意：
//
//        0 ---- Server1 ---- Server2 ---- Server3 ---- 0
//               (环形)
//
// 虚拟节点：
// - 每个物理节点对应多个虚拟节点
// - 解决节点较少时的分布不均问题
// - 通常 100-200 个虚拟节点/物理节点

// HashRing 一致性哈希环
type HashRing struct {
	mu sync.RWMutex

	// 虚拟节点列表（排序后）
	nodes []uint32

	// 虚拟节点 -> 物理节点映射
	vnodeMap map[uint32]string

	// 每个物理节点的虚拟节点数
	replicas int

	// 物理节点列表
	physicalNodes map[string]bool
}

// NewHashRing 创建一致性哈希环
// replicas: 每个物理节点的虚拟节点数
func NewHashRing(replicas int) *HashRing {
	if replicas <= 0 {
		replicas = 100 // 默认 100 个虚拟节点
	}
	return &HashRing{
		nodes:         make([]uint32, 0),
		vnodeMap:      make(map[uint32]string),
		replicas:      replicas,
		physicalNodes: make(map[string]bool),
	}
}

// AddNode 添加物理节点
func (r *HashRing) AddNode(nodeID string) {
	r.mu.Lock()
	defer r.mu.Unlock()

	if r.physicalNodes[nodeID] {
		return // 已存在
	}

	r.physicalNodes[nodeID] = true

	// 为该节点创建虚拟节点
	for i := 0; i < r.replicas; i++ {
		hash := r.hash(fmt.Sprintf("%s#%d", nodeID, i))
		r.nodes = append(r.nodes, hash)
		r.vnodeMap[hash] = nodeID
	}

	// 排序
	sort.Slice(r.nodes, func(i, j int) bool {
		return r.nodes[i] < r.nodes[j]
	})
}

// RemoveNode 移除物理节点
func (r *HashRing) RemoveNode(nodeID string) {
	r.mu.Lock()
	defer r.mu.Unlock()

	if !r.physicalNodes[nodeID] {
		return
	}

	delete(r.physicalNodes, nodeID)

	// 移除该节点的所有虚拟节点
	newNodes := make([]uint32, 0)
	for _, hash := range r.nodes {
		if r.vnodeMap[hash] != nodeID {
			newNodes = append(newNodes, hash)
		} else {
			delete(r.vnodeMap, hash)
		}
	}
	r.nodes = newNodes
}

// GetNode 根据键查找对应的节点
func (r *HashRing) GetNode(key string) (string, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	if len(r.nodes) == 0 {
		return "", fmt.Errorf("no nodes available")
	}

	hash := r.hash(key)

	// 顺时针查找第一个节点
	idx := sort.Search(len(r.nodes), func(i int) bool {
		return r.nodes[i] >= hash
	})

	// 环形处理
	if idx == len(r.nodes) {
		idx = 0
	}

	return r.vnodeMap[r.nodes[idx]], nil
}

// GetNodes 获取所有物理节点
func (r *HashRing) GetNodes() []string {
	r.mu.RLock()
	defer r.mu.RUnlock()

	nodes := make([]string, 0, len(r.physicalNodes))
	for nodeID := range r.physicalNodes {
		nodes = append(nodes, nodeID)
	}
	return nodes
}

// GetNodeCount 获取物理节点数量
func (r *HashRing) GetNodeCount() int {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return len(r.physicalNodes)
}

// GetDistribution 获取节点分布（用于调试）
func (r *HashRing) GetDistribution(sampleSize int) map[string]int {
	r.mu.RLock()
	defer r.mu.RUnlock()

	dist := make(map[string]int)
	for nodeID := range r.physicalNodes {
		dist[nodeID] = 0
	}

	// 模拟随机键分配
	for i := 0; i < sampleSize; i++ {
		key := fmt.Sprintf("player_%d", i)
		hash := r.hash(key)

		idx := sort.Search(len(r.nodes), func(j int) bool {
			return r.nodes[j] >= hash
		})
		if idx == len(r.nodes) {
			idx = 0
		}

		nodeID := r.vnodeMap[r.nodes[idx]]
		dist[nodeID]++
	}

	return dist
}

// hash 计算哈希值
func (r *HashRing) hash(key string) uint32 {
	h := sha256.Sum256([]byte(key))
	return binary.BigEndian.Uint32(h[:4])
}

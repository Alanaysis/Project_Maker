package cache

import (
	"crypto/md5"
	"fmt"
	"sort"
	"sync"
)

// ConsistentHashRing implements the consistent hashing algorithm with
// virtual nodes for even distribution across cache nodes.
//
// Consistent Hashing Explained:
//
// Traditional hashing (hash(key) % num_nodes) has a major problem:
// when a node is added or removed, nearly ALL keys need to be remapped.
// This causes massive cache thrashing in distributed systems.
//
// Consistent hashing solves this by:
// 1. Hashing both nodes and keys onto a circular "hash ring" (0 to 2^32-1)
// 2. A key maps to the first node found when moving clockwise on the ring
// 3. When a node is added/removed, only keys between the affected nodes
//    need to be remapped (typically ~1/N of all keys)
//
// Virtual Nodes:
// To prevent hot spots when nodes have different hash values, each real
// node is mapped to multiple "virtual" points on the ring. This ensures
// even distribution even with few real nodes.
//
// Example with 3 nodes and 160 virtual nodes each:
//
//     Ring: [0]---------------------------------[2^32-1]
//           node1-v1    node2-v42    node3-v99
//           \           /  \           /
//           \         /    \         /
//           key-a /        key-b /
//
// Key "a" hashes to a point between node1-v1 and node2-v42, so it
// maps to node1. Key "b" hashes between node2-v42 and node3-v99,
// so it maps to node2.

// HashRing represents the consistent hashing ring.
type HashRing struct {
	sortedKeys   []uint32     // Sorted virtual node positions on the ring
	keyToNode    map[uint32]string // Maps ring position to node ID
	nodePrefixes map[string][]uint32 // Maps node ID to its virtual node positions
	vnodes       int              // Number of virtual nodes per real node
	mu           sync.RWMutex
}

// New creates a new consistent hash ring with the specified number of
// virtual nodes per real node. More virtual nodes = more even distribution.
func New(vnodes int) *HashRing {
	return &HashRing{
		sortedKeys:   make([]uint32, 0),
		keyToNode:    make(map[uint32]string),
		nodePrefixes: make(map[string][]uint32),
		vnodes:       vnodes,
	}
}

// AddNode adds a real node to the hash ring by creating virtual node replicas.
// Each virtual node is a unique hash point on the ring.
func (r *HashRing) AddNode(nodeID string) {
	r.mu.Lock()
	defer r.mu.Unlock()

	positions := make([]uint32, 0, r.vnodes)
	for i := 0; i < r.vnodes; i++ {
		// Create a virtual node key by combining real node ID with a virtual node index
		// This ensures each real node maps to many distinct points on the ring
		virtualKey := fmt.Sprintf("%s-%d", nodeID, i)
		hash := hashKey(virtualKey)
		positions = append(positions, hash)
		r.keyToNode[hash] = nodeID
	}

	// Sort positions for binary search
	sort.Slice(positions, func(i, j int) bool {
		return positions[i] < positions[j]
	})

	r.nodePrefixes[nodeID] = positions
	r.sortedKeys = append(r.sortedKeys, positions...)
	sort.Slice(r.sortedKeys, func(i, j int) bool {
		return r.sortedKeys[i] < r.sortedKeys[j]
	})
}

// RemoveNode removes a node from the hash ring.
// Only keys that were mapped to this node's range need to be remapped.
func (r *HashRing) RemoveNode(nodeID string) {
	r.mu.Lock()
	defer r.mu.Unlock()

	positions := r.nodePrefixes[nodeID]
	for _, pos := range positions {
		delete(r.keyToNode, pos)
	}
	delete(r.nodePrefixes, nodeID)

	// Rebuild sorted keys
	r.sortedKeys = make([]uint32, 0, len(r.keyToNode))
	for k := range r.keyToNode {
		r.sortedKeys = append(r.sortedKeys, k)
	}
	sort.Slice(r.sortedKeys, func(i, j int) bool {
		return r.sortedKeys[i] < r.sortedKeys[j]
	})
}

// GetNode finds the node responsible for the given key.
// It uses binary search to find the first virtual node position
// that is >= the key's hash, then clockwise on the ring.
func (r *HashRing) GetNode(key string) string {
	r.mu.RLock()
	defer r.mu.RUnlock()

	if len(r.sortedKeys) == 0 {
		return ""
	}

	hash := hashKey(key)

	// Binary search for the first position >= hash
	idx := sort.Search(len(r.sortedKeys), func(i int) bool {
		return r.sortedKeys[i] >= hash
	})

	// If we went past the end, wrap around to the beginning (clockwise)
	if idx >= len(r.sortedKeys) {
		idx = 0
	}

	return r.keyToNode[r.sortedKeys[idx]]
}

// SortedKeys returns all sorted ring positions for visualization.
func (r *HashRing) SortedKeys() []uint32 {
	r.mu.RLock()
	defer r.mu.RUnlock()

	result := make([]uint32, len(r.sortedKeys))
	copy(result, r.sortedKeys)
	return result
}

// hashKey computes a hash of the input string, returning a uint32 value.
// MD5 is used here for its fast 128-bit output; we take the first 4 bytes.
// In production, you might use xxhash or murmur3 for better performance.
func hashKey(key string) uint32 {
	sum := md5.Sum([]byte(key))
	return uint32(sum[0])<<24 | uint32(sum[1])<<16 | uint32(sum[2])<<8 | uint32(sum[3])
}

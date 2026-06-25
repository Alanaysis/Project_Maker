package hash

import (
	"crypto/sha256"
	"encoding/binary"
	"fmt"
	"sort"
	"sync"
)

// ConsistentHash implements consistent hashing with virtual nodes
type ConsistentHash struct {
	mu           sync.RWMutex
	hashFunc     func(data []byte) uint32
	replicas     int               // Number of virtual nodes per real node
	ring         []uint32          // Sorted hash ring
	nodes        map[uint32]string // Hash -> node name
	nodeSet      map[string]bool   // Set of real nodes
	loadFactor   map[string]int64  // Load per node
}

// NewConsistentHash creates a new consistent hash ring
func NewConsistentHash(replicas int, hashFunc func(data []byte) uint32) *ConsistentHash {
	if hashFunc == nil {
		hashFunc = defaultHash
	}
	return &ConsistentHash{
		hashFunc:   hashFunc,
		replicas:   replicas,
		ring:       make([]uint32, 0),
		nodes:      make(map[uint32]string),
		nodeSet:    make(map[string]bool),
		loadFactor: make(map[string]int64),
	}
}

// defaultHash implements a default hash function using SHA256
func defaultHash(data []byte) uint32 {
	h := sha256.Sum256(data)
	return binary.BigEndian.Uint32(h[:4])
}

// Add adds a node to the hash ring
func (ch *ConsistentHash) Add(node string) {
	ch.mu.Lock()
	defer ch.mu.Unlock()

	if ch.nodeSet[node] {
		return
	}

	ch.nodeSet[node] = true
	ch.loadFactor[node] = 0

	// Add virtual nodes
	for i := 0; i < ch.replicas; i++ {
		key := fmt.Sprintf("%s#%d", node, i)
		hash := ch.hashFunc([]byte(key))
		ch.ring = append(ch.ring, hash)
		ch.nodes[hash] = node
	}

	sort.Slice(ch.ring, func(i, j int) bool {
		return ch.ring[i] < ch.ring[j]
	})
}

// Remove removes a node from the hash ring
func (ch *ConsistentHash) Remove(node string) {
	ch.mu.Lock()
	defer ch.mu.Unlock()

	if !ch.nodeSet[node] {
		return
	}

	delete(ch.nodeSet, node)
	delete(ch.loadFactor, node)

	// Remove virtual nodes
	for i := 0; i < ch.replicas; i++ {
		key := fmt.Sprintf("%s#%d", node, i)
		hash := ch.hashFunc([]byte(key))
		delete(ch.nodes, hash)
	}

	// Rebuild ring
	ch.ring = make([]uint32, 0, len(ch.nodes))
	for hash := range ch.nodes {
		ch.ring = append(ch.ring, hash)
	}
	sort.Slice(ch.ring, func(i, j int) bool {
		return ch.ring[i] < ch.ring[j]
	})
}

// Get returns the node responsible for the given key
func (ch *ConsistentHash) Get(key string) (string, bool) {
	ch.mu.RLock()
	defer ch.mu.RUnlock()

	if len(ch.ring) == 0 {
		return "", false
	}

	hash := ch.hashFunc([]byte(key))

	// Binary search for the first node with hash >= key hash
	idx := sort.Search(len(ch.ring), func(i int) bool {
		return ch.ring[i] >= hash
	})

	// Wrap around if necessary
	if idx >= len(ch.ring) {
		idx = 0
	}

	node := ch.nodes[ch.ring[idx]]
	ch.loadFactor[node]++
	return node, true
}

// GetN returns N nodes responsible for the given key (for replication)
func (ch *ConsistentHash) GetN(key string, n int) []string {
	ch.mu.RLock()
	defer ch.mu.RUnlock()

	if len(ch.ring) == 0 || n <= 0 {
		return nil
	}

	if n > len(ch.nodeSet) {
		n = len(ch.nodeSet)
	}

	hash := ch.hashFunc([]byte(key))
	idx := sort.Search(len(ch.ring), func(i int) bool {
		return ch.ring[i] >= hash
	})

	result := make([]string, 0, n)
	seen := make(map[string]bool)

	for i := 0; len(result) < n && i < len(ch.ring); i++ {
		pos := (idx + i) % len(ch.ring)
		node := ch.nodes[ch.ring[pos]]
		if !seen[node] {
			seen[node] = true
			result = append(result, node)
		}
	}

	return result
}

// Nodes returns all nodes in the hash ring
func (ch *ConsistentHash) Nodes() []string {
	ch.mu.RLock()
	defer ch.mu.RUnlock()
	nodes := make([]string, 0, len(ch.nodeSet))
	for node := range ch.nodeSet {
		nodes = append(nodes, node)
	}
	return nodes
}

// LoadFactor returns the load distribution across nodes
func (ch *ConsistentHash) LoadFactor() map[string]int64 {
	ch.mu.RLock()
	defer ch.mu.RUnlock()
	result := make(map[string]int64)
	for node, load := range ch.loadFactor {
		result[node] = load
	}
	return result
}

// NodeCount returns the number of nodes in the ring
func (ch *ConsistentHash) NodeCount() int {
	ch.mu.RLock()
	defer ch.mu.RUnlock()
	return len(ch.nodeSet)
}

// String returns a string representation of the hash ring
func (ch *ConsistentHash) String() string {
	ch.mu.RLock()
	defer ch.mu.RUnlock()
	return fmt.Sprintf("ConsistentHash{nodes: %d, virtual_nodes: %d, ring_size: %d}",
		len(ch.nodeSet), ch.replicas, len(ch.ring))
}

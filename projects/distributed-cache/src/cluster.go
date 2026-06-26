package cache

import (
	"fmt"
	"sync"
	"time"
)

// Cluster represents a multi-node cache cluster that distributes keys
// across nodes using consistent hashing.
//
// Cluster Architecture:
//
//     Client
//        |
//        v
//     +--------+
//     | Cluster| -- consistent hashing --+
//     +--------+                         |
//        |                               |
//   Get/Set/Delete              +-------+-------+
//        |                        |       |       |
//        v                        v       v       v
//     +------+                 +-----+ +-----+ +-----+
//     |Node1 |                 |N1   | |N2  | |N3  |
//     +------+                 +-----+ +-----+ +-----+
//
// The cluster wraps multiple cache nodes and uses consistent hashing
// to determine which node stores each key. This enables:
//   - Horizontal scaling: add nodes to increase capacity
//   - Fault tolerance: remove nodes gracefully
//   - Even distribution: consistent hashing balances load

// Cluster manages a group of cache nodes with consistent hashing.
type Cluster struct {
	name    string
	ring    *HashRing
	nodes   map[string]*Node
	mu      sync.RWMutex
	stats   *Stats
}

// NewCluster creates a new cluster with the given name.
func NewCluster(name string, numNodes int) *Cluster {
	// Use 160 virtual nodes per real node for good distribution
	// More vnodes = more even distribution, but uses more memory
	ring := New(160)
	return &Cluster{
		name:  name,
		ring:  ring,
		nodes: make(map[string]*Node),
		stats: &Stats{},
	}
}

// Name returns the cluster's name.
func (c *Cluster) Name() string {
	return c.name
}

// AddNode adds a new cache node to the cluster.
// The node is added to the consistent hash ring, and existing keys
// may be remapped to this new node.
func (c *Cluster) AddNode(nodeID string, capacity int) {
	c.mu.Lock()
	defer c.mu.Unlock()

	node := NewNode(nodeID, capacity, LRU)
	c.nodes[nodeID] = node
	c.ring.AddNode(nodeID)
}

// RemoveNode removes a node from the cluster.
// Keys that were stored on this node will be remapped to other nodes.
// In a real distributed system, this would involve migrating data.
func (c *Cluster) RemoveNode(nodeID string) {
	c.mu.Lock()
	defer c.mu.Unlock()

	delete(c.nodes, nodeID)
	c.ring.RemoveNode(nodeID)
}

// Nodes returns all nodes in the cluster.
func (c *Cluster) Nodes() []*Node {
	c.mu.RLock()
	defer c.mu.RUnlock()

	result := make([]*Node, 0, len(c.nodes))
	for _, node := range c.nodes {
		result = append(result, node)
	}
	return result
}

// GetNode returns the node responsible for the given key.
func (c *Cluster) GetNode(key string) *Node {
	c.mu.RLock()
	defer c.mu.RUnlock()

	nodeID := c.ring.GetNode(key)
	return c.nodes[nodeID]
}

// Set adds a key-value pair to the appropriate node in the cluster.
// The target node is determined by consistent hashing of the key.
func (c *Cluster) Set(key, value string) {
	c.mu.RLock()
	node := c.ring.GetNode(key)
	c.mu.RUnlock()

	target := c.nodes[node]
	if target != nil {
		target.Set(key, value)
	}
}

// SetWithTTL adds a key-value pair with TTL to the appropriate node.
func (c *Cluster) SetWithTTL(key, value string, ttl time.Duration) {
	c.mu.RLock()
	node := c.ring.GetNode(key)
	c.mu.RUnlock()

	target := c.nodes[node]
	if target != nil {
		target.SetWithTTL(key, value, ttl)
	}
}

// Get retrieves a value from the appropriate node in the cluster.
func (c *Cluster) Get(key string) (string, bool) {
	c.mu.RLock()
	node := c.ring.GetNode(key)
	c.mu.RUnlock()

	target := c.nodes[node]
	if target == nil {
		return "", false
	}

	val, ok := target.Get(key)
	if ok {
		c.stats.mu.Lock()
		c.stats.Hits++
		c.stats.mu.Unlock()
	} else {
		c.stats.mu.Lock()
		c.stats.Misses++
		c.stats.mu.Unlock()
	}
	c.stats.mu.Lock()
	c.stats.Gets++
	c.stats.mu.Unlock()

	return val, ok
}

// Delete removes a key from the appropriate node.
func (c *Cluster) Delete(key string) bool {
	c.mu.RLock()
	node := c.ring.GetNode(key)
	c.mu.RUnlock()

	target := c.nodes[node]
	if target == nil {
		return false
	}
	return target.Delete(key)
}

// Stats returns aggregate statistics across all nodes in the cluster.
func (c *Cluster) Stats() Stats {
	// Get per-node stats
	var nodeStats []Stats
	c.mu.RLock()
	for _, node := range c.nodes {
		s := node.Stats()
		nodeStats = append(nodeStats, s)
	}
	c.mu.RUnlock()

	// Aggregate node stats only (cluster-level Get/Set stats are redundant)
	var total Stats
	for _, s := range nodeStats {
		total.Gets += s.Gets
		total.Hits += s.Hits
		total.Misses += s.Misses
		total.Sets += s.Sets
		total.Deletes += s.Deletes
		total.Evictions += s.Evictions
		total.TotalItems += s.TotalItems
	}

	return total
}

// String returns a string representation of the cluster.
func (c *Cluster) String() string {
	return fmt.Sprintf("Cluster(%s, %d nodes)", c.name, len(c.nodes))
}

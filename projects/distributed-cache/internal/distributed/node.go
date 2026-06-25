package distributed

import (
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/distributed-cache/internal/cache"
	"github.com/distributed-cache/internal/hash"
)

// Node represents a cache node in the distributed system
type Node struct {
	mu         sync.RWMutex
	ID         string
	Address    string
	cache      *cache.Cache
	peers      map[string]*PeerNode
	hashRing   *hash.ConsistentHash
	state      NodeState
	lastHealth time.Time
	metadata   map[string]string
}

// NodeState represents the state of a node
type NodeState int

const (
	NodeStateRunning NodeState = iota
	NodeStateSuspect
	NodeStateDown
	NodeStateLeaving
)

// PeerNode represents a peer node
type PeerNode struct {
	ID       string
	Address  string
	State    NodeState
	LastSeen time.Time
	Client   CacheClient
}

// CacheClient is the interface for remote cache operations
type CacheClient interface {
	Get(key string) (interface{}, error)
	Set(key string, value interface{}, ttl time.Duration) error
	Delete(key string) error
	Ping() error
}

// NewNode creates a new cache node
func NewNode(id, address string, cacheConfig cache.CacheConfig) *Node {
	c := cache.NewCache(cacheConfig)
	ring := hash.NewConsistentHash(150, nil) // 150 virtual nodes per real node

	node := &Node{
		ID:         id,
		Address:    address,
		cache:      c,
		peers:      make(map[string]*PeerNode),
		hashRing:   ring,
		state:      NodeStateRunning,
		lastHealth: time.Now(),
		metadata:   make(map[string]string),
	}

	// Add self to ring
	ring.Add(id)

	return node
}

// Start starts the node
func (n *Node) Start() error {
	n.mu.Lock()
	defer n.mu.Unlock()

	if n.state != NodeStateRunning {
		return fmt.Errorf("node is not in running state")
	}

	log.Printf("Node %s started at %s", n.ID, n.Address)

	// Start health check
	go n.healthCheckLoop()

	return nil
}

// Stop stops the node
func (n *Node) Stop() {
	n.mu.Lock()
	defer n.mu.Unlock()

	n.state = NodeStateLeaving
	n.cache.Stop()
	log.Printf("Node %s stopped", n.ID)
}

// Get retrieves a value from the distributed cache
func (n *Node) Get(key string) (interface{}, error) {
	// Determine which node owns this key
	owner, ok := n.hashRing.Get(key)
	if !ok {
		return nil, fmt.Errorf("no node available for key: %s", key)
	}

	// If we own the key, get from local cache
	if owner == n.ID {
		val, found := n.cache.Get(key)
		if !found {
			return nil, fmt.Errorf("key not found: %s", key)
		}
		return val, nil
	}

	// Otherwise, forward to the owner
	peer, exists := n.peers[owner]
	if !exists {
		return nil, fmt.Errorf("peer node not found: %s", owner)
	}

	return peer.Client.Get(key)
}

// Set stores a value in the distributed cache
func (n *Node) Set(key string, value interface{}, ttl time.Duration) error {
	// Determine which node owns this key
	owner, ok := n.hashRing.Get(key)
	if !ok {
		return fmt.Errorf("no node available for key: %s", key)
	}

	// If we own the key, set in local cache
	if owner == n.ID {
		n.cache.Set(key, value, ttl)
		return nil
	}

	// Otherwise, forward to the owner
	peer, exists := n.peers[owner]
	if !exists {
		return fmt.Errorf("peer node not found: %s", owner)
	}

	return peer.Client.Set(key, value, ttl)
}

// Delete removes a value from the distributed cache
func (n *Node) Delete(key string) error {
	owner, ok := n.hashRing.Get(key)
	if !ok {
		return fmt.Errorf("no node available for key: %s", key)
	}

	if owner == n.ID {
		n.cache.Delete(key)
		return nil
	}

	peer, exists := n.peers[owner]
	if !exists {
		return fmt.Errorf("peer node not found: %s", owner)
	}

	return peer.Client.Delete(key)
}

// AddPeer adds a peer node
func (n *Node) AddPeer(id, address string, client CacheClient) {
	n.mu.Lock()
	defer n.mu.Unlock()

	n.peers[id] = &PeerNode{
		ID:       id,
		Address:  address,
		State:    NodeStateRunning,
		LastSeen: time.Now(),
		Client:   client,
	}

	n.hashRing.Add(id)
	log.Printf("Node %s added peer: %s (%s)", n.ID, id, address)
}

// RemovePeer removes a peer node
func (n *Node) RemovePeer(id string) {
	n.mu.Lock()
	defer n.mu.Unlock()

	delete(n.peers, id)
	n.hashRing.Remove(id)
	log.Printf("Node %s removed peer: %s", n.ID, id)
}

// GetReplicaNodes returns N replica nodes for a key
func (n *Node) GetReplicaNodes(key string, replicas int) []string {
	return n.hashRing.GetN(key, replicas)
}

// State returns the node state
func (n *Node) State() NodeState {
	n.mu.RLock()
	defer n.mu.RUnlock()
	return n.state
}

// Stats returns cache statistics
func (n *Node) Stats() cache.CacheStats {
	return n.cache.Stats()
}

// healthCheckLoop periodically checks peer health
func (n *Node) healthCheckLoop() {
	ticker := time.NewTicker(10 * time.Second)
	defer ticker.Stop()

	for {
		n.mu.RLock()
		state := n.state
		n.mu.RUnlock()

		if state == NodeStateLeaving {
			return
		}

		<-ticker.C
		n.checkPeers()
	}
}

func (n *Node) checkPeers() {
	n.mu.Lock()
	defer n.mu.Unlock()

	for id, peer := range n.peers {
		if peer.Client == nil {
			continue
		}

		if err := peer.Client.Ping(); err != nil {
			peer.State = NodeStateSuspect
			log.Printf("Node %s: peer %s is suspect: %v", n.ID, id, err)
		} else {
			peer.State = NodeStateRunning
			peer.LastSeen = time.Now()
		}
	}
}

// String returns a string representation of the node
func (n *Node) String() string {
	return fmt.Sprintf("Node{ID: %s, Address: %s, State: %d, Peers: %d}",
		n.ID, n.Address, n.state, len(n.peers))
}

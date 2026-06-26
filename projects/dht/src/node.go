package chord

import (
	"fmt"
	"sync"
	"time"
)

// Node represents a Chord node in the DHT ring.
// Each node has:
//   - A unique ID on the ring
//   - A successor pointer (the next node clockwise)
//   - A predecessor pointer (the previous node clockwise)
//   - A finger table for O(log N) routing
//   - A key-value store for data it is responsible for
type Node struct {
	ID          NodeID         // This node's ID on the ring
	Successor   NodeID         // Immediate successor
	Predecessor NodeID         // Immediate predecessor
	FingerTable []NodeID       // Finger table for routing
	Store       *KeyValueStore // Key-value data store
	mu          sync.RWMutex   // Mutex for thread safety
	
	// Network address (for distributed simulation)
	Address string
	
	// Liveness tracking
	LastHeartbeat time.Time
	IsAlive       bool
	
	// Callbacks for events
	OnNodeJoin  func(NodeID)
	OnNodeLeave func(NodeID)
	OnKeyMove   func(string, NodeID, NodeID)
}

// NewNode creates a new Chord node with the given ID and address.
func NewNode(id NodeID, address string) *Node {
	fingerTableSize := ComputeFingerTableSize()
	node := &Node{
		ID:          id,
		Successor:   id, // Initially points to itself
		Predecessor: 0,
		FingerTable: make([]NodeID, fingerTableSize),
		Store:       NewKeyValueStore(),
		Address:     address,
		LastHeartbeat: time.Now(),
		IsAlive:       true,
	}
	// Initialize finger table entries to self
	for i := 0; i < fingerTableSize; i++ {
		node.FingerTable[i] = id
	}
	return node
}

// SetSuccessor sets the successor pointer and updates the first finger table entry.
func (n *Node) SetSuccessor(successor NodeID) {
	n.mu.Lock()
	defer n.mu.Unlock()
	
	if n.Successor != successor {
		n.Successor = successor
		// Update finger table entry 0 (closest successor)
		if len(n.FingerTable) > 0 {
			n.FingerTable[0] = successor
		}
	}
}

// GetSuccessor returns the current successor.
func (n *Node) GetSuccessor() NodeID {
	n.mu.RLock()
	defer n.mu.RUnlock()
	return n.Successor
}

// SetPredecessor sets the predecessor pointer.
func (n *Node) SetPredecessor(pred NodeID) {
	n.mu.Lock()
	defer n.mu.Unlock()
	n.Predecessor = pred
}

// GetPredecessor returns the current predecessor.
func (n *Node) GetPredecessor() NodeID {
	n.mu.RLock()
	defer n.mu.RUnlock()
	return n.Predecessor
}

// UpdateFingerTable updates the finger table with a new node information.
// This is called during stabilization when new nodes join the ring.
func (n *Node) UpdateFingerTable(newNode NodeID) {
	n.mu.Lock()
	defer n.mu.Unlock()
	
	fingerTableSize := len(n.FingerTable)
	for i := 0; i < fingerTableSize; i++ {
		// Finger table entry i covers the range [id + 2^(i-1), id + 2^i)
		fingerID := FingerIndex(n.ID, i+1)
		
		// Check if newNode is closer to fingerID than current entry
		if IsInRange(n.ID, fingerID, newNode) {
			if n.FingerTable[i] == 0 || Distance(n.ID, newNode) < Distance(n.ID, n.FingerTable[i]) {
				n.FingerTable[i] = newNode
			}
		}
	}
}

// GetFingerTable returns a copy of the finger table.
func (n *Node) GetFingerTable() []NodeID {
	n.mu.RLock()
	defer n.mu.RUnlock()
	ft := make([]NodeID, len(n.FingerTable))
	copy(ft, n.FingerTable)
	return ft
}

// StoreValue stores a key-value pair in this node's local store.
// The node is responsible for keys whose IDs fall in the range (predecessor, nodeID].
func (n *Node) StoreValue(key string, value string) bool {
	n.mu.RLock()
	keyID := GenerateKeyID(key)
	responsible := IsInRange(n.Predecessor, n.ID, keyID)
	n.mu.RUnlock()
	
	if responsible {
		n.Store.Put(key, value)
		return true
	}
	return false
}

// GetValue retrieves a value by key from this node's local store.
func (n *Node) GetValue(key string) (string, bool) {
	return n.Store.Get(key)
}

// DeleteValue removes a key from this node's local store.
func (n *Node) DeleteValue(key string) bool {
	n.mu.RLock()
	keyID := GenerateKeyID(key)
	responsible := IsInRange(n.Predecessor, n.ID, keyID)
	n.mu.RUnlock()
	
	if responsible {
		return n.Store.Delete(key)
	}
	return false
}

// KeysForNode returns the list of keys stored by this node.
func (n *Node) KeysForNode() []string {
	return n.Store.Keys()
}

// Heartbeat updates the last heartbeat timestamp.
func (n *Node) Heartbeat() {
	n.mu.Lock()
	defer n.mu.Unlock()
	n.LastHeartbeat = time.Now()
	n.IsAlive = true
}

// CheckAlive checks if the node is considered alive based on heartbeat timeout.
func (n *Node) CheckAlive(timeout time.Duration) bool {
	n.mu.RLock()
	defer n.mu.RUnlock()
	return time.Since(n.LastHeartbeat) < timeout
}

// String returns a string representation of the node.
func (n *Node) String() string {
	return fmt.Sprintf("Node(id=%d, addr=%s, succ=%d, pred=%d)",
		n.ID, n.Address, n.Successor, n.Predecessor)
}

// FingerTableString returns a string representation of the finger table.
func (n *Node) FingerTableString() string {
	n.mu.RLock()
	defer n.mu.RUnlock()
	
	var sb string
	for i, entry := range n.FingerTable {
		sb += fmt.Sprintf("  Finger[%d]: %d\n", i, entry)
	}
	return sb
}

// Stats returns statistics about this node.
func (n *Node) Stats() map[string]interface{} {
	return map[string]interface{}{
		"id":              n.ID,
		"successor":       n.Successor,
		"predecessor":     n.Predecessor,
		"finger_table_size": len(n.FingerTable),
		"store_size":      n.Store.Size(),
		"is_alive":        n.IsAlive,
		"address":         n.Address,
	}
}

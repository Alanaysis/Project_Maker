package internal

import (
	"fmt"
	"math/big"
	"sync"
)

// NodeID represents a node's identifier in the Chord ring
type NodeID struct {
	ID   *big.Int
	Addr string // Network address (e.g., "localhost:8000")
}

// FingerEntry represents an entry in the finger table
type FingerEntry struct {
	Start *big.Int // Start of the interval
	Node  *NodeID  // Node responsible for this interval
}

// Node represents a Chord node
type Node struct {
	mu sync.RWMutex

	// Core fields
	ID          *big.Int
	Addr        string
	FingerTable []FingerEntry
	Predecessor *NodeID
	Successor   *NodeID

	// Storage for key-value pairs
	storage map[string]string

	// For stabilization and fault tolerance
	successorList []*NodeID
	maxSuccessors int

	// Hash function
	hashFunc HashFunc

	// Node state
	alive bool
}

// NewNode creates a new Chord node
func NewNode(addr string, hashFunc HashFunc) *Node {
	if hashFunc == nil {
		hashFunc = DefaultHash
	}

	node := &Node{
		ID:            hashFunc(addr),
		Addr:          addr,
		FingerTable:   make([]FingerEntry, M),
		Predecessor:   nil,
		Successor:     nil,
		storage:       make(map[string]string),
		successorList: make([]*NodeID, 0, 10),
		maxSuccessors: 10,
		hashFunc:      hashFunc,
		alive:         true,
	}

	// Initialize finger table entries
	for i := 0; i < M; i++ {
		start := new(big.Int).Add(node.ID, PowerOfTwo(i))
		start.Mod(start, PowerOfTwo(M))
		node.FingerTable[i] = FingerEntry{
			Start: start,
			Node:  nil,
		}
	}

	return node
}

// IsAlive returns whether the node is alive
func (n *Node) IsAlive() bool {
	n.mu.RLock()
	defer n.mu.RUnlock()
	return n.alive
}

// SetAlive sets the node's alive status
func (n *Node) SetAlive(alive bool) {
	n.mu.Lock()
	defer n.mu.Unlock()
	n.alive = alive
}

// GetSuccessor returns the node's successor
func (n *Node) GetSuccessor() *NodeID {
	n.mu.RLock()
	defer n.mu.RUnlock()
	return n.Successor
}

// SetSuccessor sets the node's successor
func (n *Node) SetSuccessor(successor *NodeID) {
	n.mu.Lock()
	defer n.mu.Unlock()
	n.Successor = successor
}

// GetPredecessor returns the node's predecessor
func (n *Node) GetPredecessor() *NodeID {
	n.mu.RLock()
	defer n.mu.RUnlock()
	return n.Predecessor
}

// SetPredecessor sets the node's predecessor
func (n *Node) SetPredecessor(predecessor *NodeID) {
	n.mu.Lock()
	defer n.mu.Unlock()
	n.Predecessor = predecessor
}

// GetFingerNode returns the node at finger table index i
func (n *Node) GetFingerNode(i int) *NodeID {
	n.mu.RLock()
	defer n.mu.RUnlock()
	if i < 0 || i >= M {
		return nil
	}
	return n.FingerTable[i].Node
}

// SetFingerNode sets the node at finger table index i
func (n *Node) SetFingerNode(i int, node *NodeID) {
	n.mu.Lock()
	defer n.mu.Unlock()
	if i >= 0 && i < M {
		n.FingerTable[i].Node = node
	}
}

// GetFingerStart returns the start value at finger table index i
func (n *Node) GetFingerStart(i int) *big.Int {
	n.mu.RLock()
	defer n.mu.RUnlock()
	if i < 0 || i >= M {
		return nil
	}
	return n.FingerTable[i].Start
}

// Store stores a key-value pair in the node
func (n *Node) Store(key, value string) {
	n.mu.Lock()
	defer n.mu.Unlock()
	n.storage[key] = value
}

// Get retrieves a value from the node by key
func (n *Node) Get(key string) (string, bool) {
	n.mu.RLock()
	defer n.mu.RUnlock()
	val, ok := n.storage[key]
	return val, ok
}

// Delete removes a key-value pair from the node
func (n *Node) Delete(key string) bool {
	n.mu.Lock()
	defer n.mu.Unlock()
	_, ok := n.storage[key]
	if ok {
		delete(n.storage, key)
	}
	return ok
}

// GetSuccessorList returns the successor list
func (n *Node) GetSuccessorList() []*NodeID {
	n.mu.RLock()
	defer n.mu.RUnlock()
	return n.successorList
}

// AddSuccessor adds a node to the successor list
func (n *Node) AddSuccessor(successor *NodeID) {
	n.mu.Lock()
	defer n.mu.Unlock()

	// Add to front
	n.successorList = append([]*NodeID{successor}, n.successorList...)

	// Trim to max size
	if len(n.successorList) > n.maxSuccessors {
		n.successorList = n.successorList[:n.maxSuccessors]
	}
}

// FindSuccessor finds the successor of the given ID
// This is the core Chord routing algorithm
func (n *Node) FindSuccessor(id *big.Int) *NodeID {
	n.mu.RLock()
	defer n.mu.RUnlock()

	// If successor is nil, we're the only node
	if n.Successor == nil {
		return &NodeID{ID: n.ID, Addr: n.Addr}
	}

	// Check if id is between n and successor
	if BetweenRightInclusive(id, n.ID, n.Successor.ID) {
		return n.Successor
	}

	// Find the closest preceding node in the finger table
	closest := n.closestPrecedingFinger(id)
	if closest == nil {
		return n.Successor
	}

	return closest
}

// closestPrecedingFinger finds the closest preceding node for the given ID
func (n *Node) closestPrecedingFinger(id *big.Int) *NodeID {
	// Search finger table in reverse order
	for i := M - 1; i >= 0; i-- {
		finger := n.FingerTable[i].Node
		if finger != nil && Between(finger.ID, n.ID, id) {
			return finger
		}
	}

	// If no finger found, return successor
	return n.Successor
}

// Join makes this node join the Chord ring through an existing node
func (n *Node) Join(existing *NodeID) error {
	if existing == nil {
		// First node in the ring
		n.mu.Lock()
		n.Successor = &NodeID{ID: n.ID, Addr: n.Addr}
		n.Predecessor = &NodeID{ID: n.ID, Addr: n.Addr}
		n.mu.Unlock()
		return nil
	}

	// Find successor through the existing node
	// In a real implementation, this would be a network call
	// For now, we assume the existing node can find our successor
	return nil
}

// Stabilize verifies n's successor and tells the successor about n
func (n *Node) Stabilize() error {
	n.mu.RLock()
	successor := n.Successor
	n.mu.RUnlock()

	if successor == nil {
		return fmt.Errorf("successor is nil")
	}

	// In a real implementation, we would call successor.GetPredecessor()
	// For now, we just ensure our successor is valid

	return nil
}

// Notify notifies this node that nodeID might be its predecessor
func (n *Node) Notify(nodeID *NodeID) {
	n.mu.Lock()
	defer n.mu.Unlock()

	if n.Predecessor == nil || Between(nodeID.ID, n.Predecessor.ID, n.ID) {
		n.Predecessor = nodeID
	}
}

// FixFingers refreshes finger table entries
func (n *Node) FixFingers() {
	n.mu.Lock()
	defer n.mu.Unlock()

	for i := 0; i < M; i++ {
		start := new(big.Int).Add(n.ID, PowerOfTwo(i))
		start.Mod(start, PowerOfTwo(M))

		// In a real implementation, we would find the successor of start
		// through network calls. For now, we'll update the finger table locally
		n.FingerTable[i].Start = start
	}
}

// CheckPredecessor checks if predecessor has failed
func (n *Node) CheckPredecessor() {
	n.mu.Lock()
	defer n.mu.Unlock()

	if n.Predecessor != nil && !n.Predecessor.ID.IsInt64() {
		// In a real implementation, we would ping the predecessor
		// If it fails, set predecessor to nil
		n.Predecessor = nil
	}
}

// String returns a string representation of the node
func (n *Node) String() string {
	return fmt.Sprintf("Node{ID: %s, Addr: %s}", FormatID(n.ID), n.Addr)
}

// PrintFingerTable prints the finger table for debugging
func (n *Node) PrintFingerTable() {
	n.mu.RLock()
	defer n.mu.RUnlock()

	fmt.Printf("Finger Table for Node %s:\n", FormatID(n.ID))
	for i := 0; i < M && i < 10; i++ { // Print first 10 for brevity
		entry := n.FingerTable[i]
		if entry.Node != nil {
			fmt.Printf("  [%d] Start: %s -> Node: %s\n", i, FormatID(entry.Start), FormatID(entry.Node.ID))
		} else {
			fmt.Printf("  [%d] Start: %s -> nil\n", i, FormatID(entry.Start))
		}
	}
	if M > 10 {
		fmt.Printf("  ... (%d more entries)\n", M-10)
	}
}

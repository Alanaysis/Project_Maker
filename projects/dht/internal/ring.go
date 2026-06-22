package internal

import (
	"fmt"
	"math/big"
	"sort"
	"sync"
)

// Ring represents the Chord ring with multiple nodes
type Ring struct {
	mu        sync.RWMutex
	nodes     map[string]*Node // addr -> node
	sortedIDs []*big.Int       // Sorted node IDs for efficient lookup
	hashFunc  HashFunc
}

// NewRing creates a new Chord ring
func NewRing(hashFunc HashFunc) *Ring {
	if hashFunc == nil {
		hashFunc = DefaultHash
	}

	return &Ring{
		nodes:     make(map[string]*Node),
		sortedIDs: make([]*big.Int, 0),
		hashFunc:  hashFunc,
	}
}

// AddNode adds a new node to the ring
func (r *Ring) AddNode(addr string) (*Node, error) {
	r.mu.Lock()
	defer r.mu.Unlock()

	// Check if node already exists
	if _, exists := r.nodes[addr]; exists {
		return nil, fmt.Errorf("node %s already exists", addr)
	}

	// Create new node
	node := NewNode(addr, r.hashFunc)

	// Add to ring
	r.nodes[addr] = node
	r.sortedIDs = append(r.sortedIDs, node.ID)

	// Sort IDs for efficient lookup
	sort.Slice(r.sortedIDs, func(i, j int) bool {
		return r.sortedIDs[i].Cmp(r.sortedIDs[j]) < 0
	})

	// Update finger tables for all nodes
	r.updateFingerTables()

	return node, nil
}

// RemoveNode removes a node from the ring
func (r *Ring) RemoveNode(addr string) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	node, exists := r.nodes[addr]
	if !exists {
		return fmt.Errorf("node %s not found", addr)
	}

	// Transfer keys to successor
	r.transferKeys(node)

	// Remove from ring
	delete(r.nodes, addr)

	// Remove from sorted IDs
	for i, id := range r.sortedIDs {
		if id.Cmp(node.ID) == 0 {
			r.sortedIDs = append(r.sortedIDs[:i], r.sortedIDs[i+1:]...)
			break
		}
	}

	// Update finger tables for all nodes
	r.updateFingerTables()

	return nil
}

// GetNode returns a node by address
func (r *Ring) GetNode(addr string) *Node {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return r.nodes[addr]
}

// FindNode finds the node responsible for the given key
func (r *Ring) FindNode(key string) *Node {
	r.mu.RLock()
	defer r.mu.RUnlock()

	keyID := r.hashFunc(key)
	return r.findNodeByID(keyID)
}

// findNodeByID finds the node responsible for the given ID
func (r *Ring) findNodeByID(id *big.Int) *Node {
	if len(r.sortedIDs) == 0 {
		return nil
	}

	// Find the first node with ID >= key ID
	for _, nodeID := range r.sortedIDs {
		if nodeID.Cmp(id) >= 0 {
			addr := r.findAddrByID(nodeID)
			if addr != "" {
				return r.nodes[addr]
			}
		}
	}

	// Wrap around to the first node
	addr := r.findAddrByID(r.sortedIDs[0])
	return r.nodes[addr]
}

// findAddrByID finds the address of a node by its ID
func (r *Ring) findAddrByID(id *big.Int) string {
	for addr, node := range r.nodes {
		if node.ID.Cmp(id) == 0 {
			return addr
		}
	}
	return ""
}

// updateFingerTables updates finger tables for all nodes in the ring
func (r *Ring) updateFingerTables() {
	// This is a simplified version for local ring
	// In a distributed system, this would involve network calls

	for _, node := range r.nodes {
		// Update successor
		successor := r.findSuccessorLocal(node.ID)
		if successor != nil {
			node.SetSuccessor(&NodeID{ID: successor.ID, Addr: successor.Addr})
		}

		// Update predecessor
		predecessor := r.findPredecessorLocal(node.ID)
		if predecessor != nil {
			node.SetPredecessor(&NodeID{ID: predecessor.ID, Addr: predecessor.Addr})
		}

		// Update finger table
		for i := 0; i < M; i++ {
			start := new(big.Int).Add(node.ID, PowerOfTwo(i))
			start.Mod(start, PowerOfTwo(M))

			successor := r.findSuccessorLocal(start)
			if successor != nil {
				node.SetFingerNode(i, &NodeID{ID: successor.ID, Addr: successor.Addr})
			}
		}
	}
}

// findSuccessorLocal finds the successor of an ID in the local ring
func (r *Ring) findSuccessorLocal(id *big.Int) *Node {
	if len(r.sortedIDs) == 0 {
		return nil
	}

	// Find the first node with ID > id
	for _, nodeID := range r.sortedIDs {
		if nodeID.Cmp(id) > 0 {
			addr := r.findAddrByID(nodeID)
			if addr != "" {
				return r.nodes[addr]
			}
		}
	}

	// Wrap around to the first node
	addr := r.findAddrByID(r.sortedIDs[0])
	return r.nodes[addr]
}

// findPredecessorLocal finds the predecessor of an ID in the local ring
func (r *Ring) findPredecessorLocal(id *big.Int) *Node {
	if len(r.sortedIDs) == 0 {
		return nil
	}

	// Find the last node with ID < id
	var predecessor *Node
	for _, nodeID := range r.sortedIDs {
		if nodeID.Cmp(id) < 0 {
			addr := r.findAddrByID(nodeID)
			if addr != "" {
				predecessor = r.nodes[addr]
			}
		}
	}

	if predecessor == nil {
		// Wrap around to the last node
		addr := r.findAddrByID(r.sortedIDs[len(r.sortedIDs)-1])
		return r.nodes[addr]
	}

	return predecessor
}

// transferKeys transfers keys from a leaving node to its successor
func (r *Ring) transferKeys(node *Node) {
	successor := node.GetSuccessor()
	if successor == nil {
		return
	}

	successorNode := r.nodes[successor.Addr]
	if successorNode == nil {
		return
	}

	// Transfer all keys to successor
	// In a real implementation, we would only transfer keys that belong to the successor
	node.mu.Lock()
	for key, value := range node.storage {
		successorNode.Store(key, value)
	}
	node.storage = make(map[string]string)
	node.mu.Unlock()
}

// Put stores a key-value pair in the ring
func (r *Ring) Put(key, value string) error {
	node := r.FindNode(key)
	if node == nil {
		return fmt.Errorf("no node available to store key")
	}

	node.Store(key, value)
	return nil
}

// Get retrieves a value from the ring by key
func (r *Ring) Get(key string) (string, error) {
	node := r.FindNode(key)
	if node == nil {
		return "", fmt.Errorf("no node available to retrieve key")
	}

	value, ok := node.Get(key)
	if !ok {
		return "", fmt.Errorf("key not found: %s", key)
	}

	return value, nil
}

// Delete removes a key-value pair from the ring
func (r *Ring) Delete(key string) error {
	node := r.FindNode(key)
	if node == nil {
		return fmt.Errorf("no node available to delete key")
	}

	if !node.Delete(key) {
		return fmt.Errorf("key not found: %s", key)
	}

	return nil
}

// GetNodes returns all nodes in the ring
func (r *Ring) GetNodes() []*Node {
	r.mu.RLock()
	defer r.mu.RUnlock()

	nodes := make([]*Node, 0, len(r.nodes))
	for _, node := range r.nodes {
		nodes = append(nodes, node)
	}

	// Sort by ID for consistent output
	sort.Slice(nodes, func(i, j int) bool {
		return nodes[i].ID.Cmp(nodes[j].ID) < 0
	})

	return nodes
}

// GetNodeCount returns the number of nodes in the ring
func (r *Ring) GetNodeCount() int {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return len(r.nodes)
}

// PrintRing prints the ring structure for debugging
func (r *Ring) PrintRing() {
	r.mu.RLock()
	defer r.mu.RUnlock()

	fmt.Println("=== Chord Ring ===")
	fmt.Printf("Total nodes: %d\n", len(r.nodes))

	// Print nodes in order
	for _, id := range r.sortedIDs {
		addr := r.findAddrByID(id)
		if addr != "" {
			node := r.nodes[addr]
			fmt.Printf("\n%s\n", node.String())
			fmt.Printf("  Successor: %s\n", FormatID(node.GetSuccessor().ID))
			if pred := node.GetPredecessor(); pred != nil {
				fmt.Printf("  Predecessor: %s\n", FormatID(pred.ID))
			}
		}
	}
}

// Lookup performs a key lookup using the Chord routing algorithm
func (r *Ring) Lookup(key string) (string, *Node, error) {
	r.mu.RLock()
	keyID := r.hashFunc(key)
	startNode := r.findNodeByID(keyID)
	r.mu.RUnlock()

	if startNode == nil {
		return "", nil, fmt.Errorf("no node available")
	}

	// Use Chord routing to find the responsible node
	current := startNode
	visited := make(map[string]bool)

	for {
		if visited[current.Addr] {
			// Cycle detected, shouldn't happen in correct ring
			break
		}
		visited[current.Addr] = true

		// Check if this node is responsible for the key
		if BetweenRightInclusive(keyID, current.GetPredecessor().ID, current.ID) {
			value, ok := current.Get(key)
			if !ok {
				return "", current, fmt.Errorf("key not found: %s", key)
			}
			return value, current, nil
		}

		// Find next hop using finger table
		nextHop := current.FindSuccessor(keyID)
		if nextHop == nil {
			break
		}

		// In local ring, we can directly get the node
		r.mu.RLock()
		nextNode := r.nodes[nextHop.Addr]
		r.mu.RUnlock()

		if nextNode == nil {
			break
		}

		current = nextNode
	}

	// Fallback to direct lookup
	value, err := r.Get(key)
	return value, startNode, err
}

// RunStabilization runs the stabilization protocol for all nodes
func (r *Ring) RunStabilization() {
	r.mu.RLock()
	defer r.mu.RUnlock()

	for _, node := range r.nodes {
		node.Stabilize()
		node.FixFingers()
		node.CheckPredecessor()
	}
}

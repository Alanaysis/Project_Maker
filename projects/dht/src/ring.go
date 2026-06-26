package chord

import (
	"fmt"
	"sync"
	"time"
)

// ChordRing represents the entire Chord DHT ring with all nodes.
// This is used for simulation purposes - in a real distributed system,
// each node would run independently and communicate over the network.
type ChordRing struct {
	nodes   map[NodeID]*Node // All nodes in the ring, indexed by ID
	mu      sync.RWMutex     // Mutex for thread safety
	running bool             // Whether the ring is actively running
	stopCh  chan struct{}    // Stop channel for background goroutines
}

// NewChordRing creates a new empty Chord ring.
func NewChordRing() *ChordRing {
	return &ChordRing{
		nodes: make(map[NodeID]*Node),
		stopCh: make(chan struct{}),
	}
}

// AddNode adds a new node to the Chord ring.
// This simulates the node joining process:
// 1. The new node connects to an existing node
// 2. It finds its successor using the existing node's finger table
// 3. It initializes its finger table
// 4. The ring stabilizes to maintain consistency
func (cr *ChordRing) AddNode(node *Node) {
	cr.mu.Lock()
	defer cr.mu.Unlock()
	
	// Step 1: Find the successor of the new node
	cr.addNodeWithoutLock(node)
}

// addNodeWithoutLock adds a node without acquiring the lock (caller must hold lock).
func (cr *ChordRing) addNodeWithoutLock(node *Node) {
	// Find the current successor of the new node
	// The successor is the first node on the ring with ID in (predecessorOfNew, newID]
	successor := cr.findSuccessor(node.ID)
	
	// Initialize the new node's successor to the found successor
	node.SetSuccessor(successor)
	node.SetPredecessor(0) // Will be set during stabilization
	node.FingerTable = make([]NodeID, ComputeFingerTableSize())
	for i := range node.FingerTable {
		node.FingerTable[i] = node.ID
	}
	
	// Add the node to the ring
	cr.nodes[node.ID] = node
	
	// Notify the successor about the new node (for finger table update)
	if succ, ok := cr.nodes[successor]; ok {
		succ.UpdateFingerTable(node.ID)
	}
}

// RemoveNode removes a node from the Chord ring.
// This simulates graceful departure:
// 1. The node's successor takes over its key range
// 2. The node's predecessor updates its successor
// 3. The ring stabilizes
func (cr *ChordRing) RemoveNode(nodeID NodeID) {
	cr.mu.Lock()
	defer cr.mu.Unlock()
	
	node, ok := cr.nodes[nodeID]
	if !ok {
		return
	}
	
	// Transfer the node's keys to its successor
	if node.Successor != 0 {
		succ, ok := cr.nodes[node.Successor]
		if ok {
			node.Store.ForEach(func(key, value string) {
				succ.Store.Put(key, value)
			})
		}
	}
	
	// Update predecessor's successor to skip the removed node
	if node.Predecessor != 0 {
		pred, ok := cr.nodes[node.Predecessor]
		if ok {
			pred.SetSuccessor(node.Successor)
		}
	}
	
	// Update successor's predecessor
	if node.Successor != 0 {
		succ, ok := cr.nodes[node.Successor]
		if ok {
			succ.SetPredecessor(node.Predecessor)
		}
	}
	
	// Remove the node
	delete(cr.nodes, nodeID)
}

// GetNode returns a node by its ID.
func (cr *ChordRing) GetNode(nodeID NodeID) (*Node, bool) {
	cr.mu.RLock()
	defer cr.mu.RUnlock()
	node, ok := cr.nodes[nodeID]
	return node, ok
}

// GetNodes returns all nodes in the ring.
func (cr *ChordRing) GetNodes() []*Node {
	cr.mu.RLock()
	defer cr.mu.RUnlock()
	
	nodes := make([]*Node, 0, len(cr.nodes))
	for _, node := range cr.nodes {
		nodes = append(nodes, node)
	}
	return nodes
}

// findSuccessor finds the successor of a given ID in the ring.
// The successor is the first node with ID in the range (predecessor, ID].
func (cr *ChordRing) findSuccessor(id NodeID) NodeID {
	if len(cr.nodes) == 0 {
		return 0
	}
	
	var closest NodeID
	closestDist := RingSize + 1
	
	for _, node := range cr.nodes {
		dist := Distance(PrevID(id), node.ID)
		if dist < closestDist {
			closestDist = dist
			closest = node.ID
		}
	}
	
	return closest
}

// Lookup finds the node responsible for a given key.
// This simulates the Chord lookup algorithm which uses the finger table
// to route the query in O(log N) hops.
func (cr *ChordRing) Lookup(key string) (*Node, int) {
	keyID := GenerateKeyID(key)
	
	// Start from a random node (simulating any node in the system)
	nodes := cr.GetNodes()
	if len(nodes) == 0 {
		return nil, 0
	}
	
	// Start from the first node for simplicity
	currentNode := nodes[0]
	hops := 0
	
	// Follow the finger table to find the closest preceding node
	for {
		hops++
		if hops > 100 { // Safety limit
			break
		}
		
		// Find the closest preceding node to keyID in the finger table
		target := currentNode.GetSuccessor()
		closest := ClosestPrecedingNodeOptimized(currentNode.ID, keyID, currentNode.GetFingerTable())
		
		if closest == currentNode.ID {
			// No closer node found, return current node's successor
			return currentNode, hops
		}
		
		// Move to the closest preceding node
		if nextNode, ok := cr.nodes[closest]; ok {
			currentNode = nextNode
		} else {
			break
		}
	}
	
	// Return the successor of the last node
	succID := currentNode.GetSuccessor()
	if succNode, ok := cr.nodes[succID]; ok {
		return succNode, hops
	}
	
	return currentNode, hops
}

// Store stores a key-value pair in the ring.
// The key is routed to the node responsible for it.
func (cr *ChordRing) Store(key, value string) bool {
	node, _ := cr.Lookup(key)
	if node == nil {
		return false
	}
	
	// Store locally (the node is responsible for this key)
	node.Store.Put(key, value)
	return true
}

// Retrieve retrieves a value by key from the ring.
func (cr *ChordRing) Retrieve(key string) (string, bool) {
	node, _ := cr.Lookup(key)
	if node == nil {
		return "", false
	}
	return node.GetValue(key)
}

// Delete removes a key from the ring.
func (cr *ChordRing) Delete(key string) bool {
	node, _ := cr.Lookup(key)
	if node == nil {
		return false
	}
	return node.DeleteValue(key)
}

// Stabilize runs the stabilization protocol on all nodes.
// Stabilization ensures that each node's successor pointer is correct
// and that finger tables are properly maintained.
func (cr *ChordRing) Stabilize() {
	nodes := cr.GetNodes()
	for _, node := range nodes {
		cr.stabilizeNode(node)
	}
	// Fix predecessors for all nodes
	for _, node := range nodes {
		cr.fixPredecessor(node)
	}
}

// stabilizeNode updates a node's successor pointer.
// If the node's successor reports that it has a closer successor, update.
func (cr *ChordRing) stabilizeNode(node *Node) {
	succID := node.GetSuccessor()
	if succID == 0 {
		return
	}
	
	succ, ok := cr.nodes[succID]
	if !ok {
		return
	}
	
	// Ask successor if it has a closer successor to node.ID
	succSuccID := succ.GetSuccessor()
	if succSuccID != 0 && succSuccID != succID {
		succSucc, ok := cr.nodes[succSuccID]
		if ok {
			// Check if succSucc is closer to node.ID than succ
			if Distance(node.ID, succSucc.ID) < Distance(node.ID, succ.ID) {
				node.SetSuccessor(succSuccID)
			}
		}
	}
}

// fixPredecessor fixes a node's predecessor pointer.
// It asks its successor who its predecessor is.
func (cr *ChordRing) fixPredecessor(node *Node) {
	succID := node.GetSuccessor()
	if succID == 0 {
		return
	}
	
	succ, ok := cr.nodes[succID]
	if !ok {
		return
	}
	
	// Ask successor for its predecessor
	succPredID := succ.GetPredecessor()
	if succPredID != 0 {
		pred, ok := cr.nodes[succPredID]
		if ok && pred.IsAlive {
			node.SetPredecessor(succPredID)
		}
	}
}

// PrintRing prints the current state of the Chord ring.
func (cr *ChordRing) PrintRing() {
	cr.mu.RLock()
	defer cr.mu.RUnlock()
	
	nodes := cr.GetNodes()
	fmt.Println("=== Chord Ring State ===")
	fmt.Printf("Total nodes: %d\n", len(nodes))
	fmt.Println()
	
	// Sort nodes by ID for display
	for i := 0; i < len(nodes); i++ {
		for j := i + 1; j < len(nodes); j++ {
			if nodes[i].ID > nodes[j].ID {
				nodes[i], nodes[j] = nodes[j], nodes[i]
			}
		}
	}
	
	for _, node := range nodes {
		fmt.Printf("Node %s\n", node.Address)
		fmt.Printf("  ID: %d\n", node.ID)
		fmt.Printf("  Successor: %d\n", node.GetSuccessor())
		fmt.Printf("  Predecessor: %d\n", node.GetPredecessor())
		fmt.Printf("  Finger Table:\n")
		fmt.Print(node.FingerTableString())
		fmt.Printf("  Keys stored: %d\n", node.Store.Size())
		fmt.Println()
	}
}

// PrintRingSummary prints a summary of the ring state.
func (cr *ChordRing) PrintRingSummary() {
	nodes := cr.GetNodes()
	fmt.Printf("Chord Ring: %d nodes, %d total keys\n", len(nodes), cr.totalKeys())
	
	// Print node IDs in order
	var ids []NodeID
	for _, node := range nodes {
		ids = append(ids, node.ID)
	}
	fmt.Printf("Ring IDs: ")
	for i := 0; i < len(ids); i++ {
		for j := i + 1; j < len(ids); j++ {
			if ids[i] > ids[j] {
				ids[i], ids[j] = ids[j], ids[i]
			}
		}
	}
	for i, id := range ids {
		if i > 0 {
			fmt.Print(" -> ")
		}
		fmt.Printf("%d", id)
	}
	fmt.Println()
}

// totalKeys returns the total number of keys across all nodes.
func (cr *ChordRing) totalKeys() int {
	total := 0
	for _, node := range cr.GetNodes() {
		total += node.Store.Size()
	}
	return total
}

// VerifyRingIntegrity checks that the ring is consistent.
func (cr *ChordRing) VerifyRingIntegrity() (bool, []string) {
	nodes := cr.GetNodes()
	var issues []string
	
	if len(nodes) == 0 {
		return true, issues
	}
	
	// Check each node's successor
	for _, node := range nodes {
		succID := node.GetSuccessor()
		if succID != 0 {
			if _, ok := cr.nodes[succID]; !ok {
				issues = append(issues, fmt.Sprintf("Node %d has invalid successor %d", node.ID, succID))
			}
		}
		
		// Check predecessor consistency
		predID := node.GetPredecessor()
		if predID != 0 {
			if pred, ok := cr.nodes[predID]; ok {
				if pred.GetSuccessor() != node.ID {
					issues = append(issues, fmt.Sprintf("Predecessor inconsistency: %d -> %d but %d -> %d",
						predID, node.ID, predID, pred.GetSuccessor()))
				}
			}
		}
	}
	
	return len(issues) == 0, issues
}

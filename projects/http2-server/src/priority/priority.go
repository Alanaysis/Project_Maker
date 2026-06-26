// Package priority implements HTTP/2 stream priority and dependency management.
//
// HTTP/2 allows streams to be prioritized using a dependency tree.
// Each stream can depend on another stream with a weight (1-256).
// This is defined in RFC 7540 Section 5.3.
//
// Priority Tree Structure:
//
//	    stream 0 (root)
//	    /    \
//	  stream 1   stream 3
//	  /    \
//	stream 5  stream 7
//
// Key concepts:
//   - Dependency: A stream can depend on another stream
//   - Weight: The relative priority (1-256) among siblings
//   - Exclusive: Whether to make this stream the sole dependency
//   - Default weight is 16
package priority

import (
	"fmt"
	"sync"
)

// StreamPriority describes the priority of an HTTP/2 stream
type StreamPriority struct {
	StreamID     uint32
	DependsOn    uint32 // Stream this depends on (0 = depends on root)
	Weight       int32  // Priority weight (1-256, default 16)
	Exclusive    bool   // Make this the exclusive dependency
	Dependent    bool   // Whether this stream has dependents
	Children     []uint32
	parentID     uint32
}

// PriorityTree manages the stream dependency tree
type PriorityTree struct {
	mu         sync.RWMutex
	root       *StreamNode
	streams    map[uint32]*StreamNode
	streamList []uint32 // Ordered by priority
}

// StreamNode is a node in the priority tree
type StreamNode struct {
	priority StreamPriority
	children []*StreamNode
	parent   *StreamNode
}

// NewPriorityTree creates a new priority tree with the root node
func NewPriorityTree() *PriorityTree {
	return &PriorityTree{
		root: &StreamNode{
			priority: StreamPriority{StreamID: 0, Weight: 0},
		},
		streams: make(map[uint32]*StreamNode),
	}
}

// AddStream adds a stream to the priority tree
//
// When a client sends a HEADERS frame with Priority flag set,
// it includes stream dependency information:
//
//	Priority field format:
//	+---------------+
//	|Depends-on (31)|
//	|               |
//	+--|E|-Weight--|
//	|
	// +-----------------+
//
// Parameters:
//   - streamID: The stream being added
//   - dependsOn: The stream this depends on (0 for root)
//   - weight: Priority weight 1-256
//   - exclusive: If true, remove other dependents of dependsOn
func (pt *PriorityTree) AddStream(streamID uint32, dependsOn uint32, weight int32, exclusive bool) error {
	if streamID == 0 {
		return fmt.Errorf("cannot add stream 0 (connection-level)")
	}
	if weight < 1 || weight > 256 {
		return fmt.Errorf("weight must be between 1 and 256, got %d", weight)
	}
	if dependsOn > 0 && streamID == dependsOn {
		return fmt.Errorf("stream cannot depend on itself")
	}

	pt.mu.Lock()
	defer pt.mu.Unlock()

	// Create the new stream node
	node := &StreamNode{
		priority: StreamPriority{
			StreamID:  streamID,
			DependsOn: dependsOn,
			Weight:    weight,
			Exclusive: exclusive,
		},
	}
	pt.streams[streamID] = node

	// If dependsOn is 0, attach to root
	if dependsOn == 0 {
		node.parent = pt.root
		pt.root.children = append(pt.root.children, node)
	} else {
		// Find the parent node
		parentNode, exists := pt.streams[dependsOn]
		if !exists {
			// Parent is not in our tree, attach to root
			node.parent = pt.root
			pt.root.children = append(pt.root.children, node)
		} else {
			// Remove this stream from its current parent's children if exclusive
			if exclusive {
				// Remove all siblings
				if parent := node.parent; parent != nil {
					// Will be reattached below
				}
			}
			node.parent = parentNode
			parentNode.children = append(parentNode.children, node)
		}
	}

	// Mark parent as having dependents
	if dependsOn > 0 {
		if parentNode, exists := pt.streams[dependsOn]; exists {
			parentNode.priority.Dependent = true
		}
	}

	// Rebuild priority order
	pt.rebuildOrder()
	return nil
}

// RemoveStream removes a stream from the priority tree
// When a stream is closed, its dependents must be reparented
func (pt *PriorityTree) RemoveStream(streamID uint32) {
	pt.mu.Lock()
	defer pt.mu.Unlock()

	node, exists := pt.streams[streamID]
	if !exists {
		return
	}

	// Reparent children to the removed stream's parent
	var children []*StreamNode
	for _, child := range node.children {
		children = append(children, child)
	}

	// Remove from parent's children list
	if parent := node.parent; parent != nil {
		for i, child := range parent.children {
			if child == node {
				parent.children = append(parent.children[:i], parent.children[i+1:]...)
				break
			}
		}
	}

	// Reparent children to the node's parent
	for _, child := range children {
		child.parent = node.parent
		if node.parent != nil {
			node.parent.children = append(node.parent.children, child)
		}
	}

	// Remove from map
	delete(pt.streams, streamID)

	// Rebuild priority order
	pt.rebuildOrder()
}

// GetPriority returns the priority of a stream
func (pt *PriorityTree) GetPriority(streamID uint32) (*StreamPriority, bool) {
	pt.mu.RLock()
	defer pt.mu.RUnlock()

	node, exists := pt.streams[streamID]
	if !exists {
		return nil, false
	}
	p := node.priority
	return &p, true
}

// GetStreamOrder returns streams ordered by priority
// Higher priority streams (with more dependents and higher weights) come first
func (pt *PriorityTree) GetStreamOrder() []uint32 {
	pt.mu.RLock()
	defer pt.mu.RUnlock()
	return pt.streamList
}

// GetDependents returns all dependent streams of a given stream
func (pt *PriorityTree) GetDependents(streamID uint32) []uint32 {
	pt.mu.RLock()
	defer pt.mu.RUnlock()

	node, exists := pt.streams[streamID]
	if !exists {
		return nil
	}

	var dependents []uint32
	var collect func(n *StreamNode)
	collect = func(n *StreamNode) {
		for _, child := range n.children {
			dependents = append(dependents, child.priority.StreamID)
			collect(child)
		}
	}
	for _, child := range node.children {
		dependents = append(dependents, child.priority.StreamID)
		collect(child)
	}
	return dependents
}

// GetEffectiveWeight calculates the effective weight of a stream
// The effective weight determines how much of the parent's bandwidth the stream gets
func (pt *PriorityTree) GetEffectiveWeight(streamID uint32) int32 {
	pt.mu.RLock()
	defer pt.mu.RUnlock()

	node, exists := pt.streams[streamID]
	if !exists {
		return 16 // Default weight
	}

	// Walk up the tree to find the nearest exclusive dependency
	weight := node.priority.Weight
	current := node

	for current.parent != nil && current.parent.priority.StreamID != 0 {
		// Find the total weight of siblings
		var totalWeight int32
		for _, sibling := range current.parent.children {
			totalWeight += sibling.priority.Weight
		}

		// Check if parent has an exclusive dependency
		hasExclusive := false
		for _, child := range current.parent.children {
			if child.priority.Exclusive {
				hasExclusive = true
				break
			}
		}

		if hasExclusive {
			weight = node.priority.Weight
		} else if totalWeight > 0 {
			// Scale weight based on sibling total
			weight = (weight * 256) / totalWeight
		}

		current = current.parent
	}

	return weight
}

// rebuildOrder rebuilds the priority-ordered stream list using a tree traversal
func (pt *PriorityTree) rebuildOrder() {
	pt.streamList = nil

	// Collect all streams with their effective weights
	type streamWeight struct {
		id   uint32
		weight int32
	}
	var streams []streamWeight

	for id, node := range pt.streams {
		w := pt.getTreeWeight(node)
		streams = append(streams, streamWeight{id, w})
	}

	// Sort by weight descending (simple insertion sort for small sets)
	for i := 1; i < len(streams); i++ {
		j := i
		for j > 0 && streams[j-1].weight < streams[j].weight {
			streams[j-1], streams[j] = streams[j], streams[j-1]
			j--
		}
	}

	// Extract IDs
	for _, sw := range streams {
		pt.streamList = append(pt.streamList, sw.id)
	}
}

// getTreeWeight returns the raw priority weight of a node
func (pt *PriorityTree) getTreeWeight(node *StreamNode) int32 {
	w := node.priority.Weight
	if node.parent != nil && node.parent.priority.Exclusive {
		w = 256 // Exclusive dependencies get full weight
	}
	return w
}

// String returns a string representation of the priority tree
func (pt *PriorityTree) String() string {
	pt.mu.RLock()
	defer pt.mu.RUnlock()

	var result string
	result += "Priority Tree:\n"
	result += fmt.Sprintf("  Root (stream 0)\n")
	for _, child := range pt.root.children {
		result += pt.formatNode(child, "  ")
	}
	return result
}

func (pt *PriorityTree) formatNode(node *StreamNode, indent string) string {
	var result string
	depStr := "root"
	if node.priority.DependsOn > 0 {
		depStr = fmt.Sprintf("stream %d", node.priority.DependsOn)
	}
	result += fmt.Sprintf("%sStream %d (weight=%d, depends on %s, exclusive=%v)\n",
		indent, node.priority.StreamID, node.priority.Weight, depStr, node.priority.Exclusive)
	for _, child := range node.children {
		result += pt.formatNode(child, indent+"  ")
	}
	return result
}

// Settings represents priority-related connection settings
type Settings struct {
	// DefaultPriority is the default priority weight for new streams
	DefaultPriority int32
	// MaxDependencyDepth limits how deep the dependency tree can go
	MaxDependencyDepth int
}

// DefaultPrioritySettings returns default priority configuration
func DefaultPrioritySettings() *Settings {
	return &Settings{
		DefaultPriority:      16,
		MaxDependencyDepth:   31, // Per RFC 7540, max depends-on value is 2^31-1
	}
}

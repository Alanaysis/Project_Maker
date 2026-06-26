package chord

import (
	"fmt"
	"sync"
	"time"
)

// KeyMigration tracks key migrations during node join/leave operations.
type KeyMigration struct {
	FromNode NodeID
	ToNode   NodeID
	Keys     []string
}

// MigrationTracker tracks key migrations in the ring.
type MigrationTracker struct {
	migrations []KeyMigration
	mu         sync.Mutex
}

// NewMigrationTracker creates a new migration tracker.
func NewMigrationTracker() *MigrationTracker {
	return &MigrationTracker{
		migrations: make([]KeyMigration, 0),
	}
}

// RecordMigration records a key migration event.
func (mt *MigrationTracker) RecordMigration(from, to NodeID, keys []string) {
	mt.mu.Lock()
	defer mt.mu.Unlock()
	mt.migrations = append(mt.migrations, KeyMigration{
		FromNode: from,
		ToNode:   to,
		Keys:     keys,
	})
}

// GetMigrations returns all recorded migrations.
func (mt *MigrationTracker) GetMigrations() []KeyMigration {
	mt.mu.Lock()
	defer mt.mu.Unlock()
	result := make([]KeyMigration, len(mt.migrations))
	copy(result, mt.migrations)
	return result
}

// MigrationCount returns the number of recorded migrations.
func (mt *MigrationTracker) MigrationCount() int {
	mt.mu.Lock()
	defer mt.mu.Unlock()
	return len(mt.migrations)
}

// Clear clears all recorded migrations.
func (mt *MigrationTracker) Clear() {
	mt.mu.Lock()
	defer mt.mu.Unlock()
	mt.migrations = make([]KeyMigration, 0)
}

// HeartbeatMonitor monitors node liveness via heartbeats.
type HeartbeatMonitor struct {
	monitoringNodes map[NodeID]time.Time
	timeout         time.Duration
	mu              sync.RWMutex
}

// NewHeartbeatMonitor creates a new heartbeat monitor.
func NewHeartbeatMonitor(timeout time.Duration) *HeartbeatMonitor {
	return &HeartbeatMonitor{
		monitoringNodes: make(map[NodeID]time.Time),
		timeout:         timeout,
	}
}

// RegisterNode starts monitoring a node.
func (hm *HeartbeatMonitor) RegisterNode(nodeID NodeID) {
	hm.mu.Lock()
	defer hm.mu.Unlock()
	hm.monitoringNodes[nodeID] = time.Now()
}

// UpdateHeartbeat updates the heartbeat timestamp for a node.
func (hm *HeartbeatMonitor) UpdateHeartbeat(nodeID NodeID) {
	hm.mu.Lock()
	defer hm.mu.Unlock()
	hm.monitoringNodes[nodeID] = time.Now()
}

// IsAlive checks if a node is considered alive.
func (hm *HeartbeatMonitor) IsAlive(nodeID NodeID) bool {
	hm.mu.RLock()
	defer hm.mu.RUnlock()
	lastHB, ok := hm.monitoringNodes[nodeID]
	if !ok {
		return false
	}
	return time.Since(lastHB) < hm.timeout
}

// GetFailedNodes returns all nodes that have failed (no heartbeat within timeout).
func (hm *HeartbeatMonitor) GetFailedNodes() []NodeID {
	hm.mu.RLock()
	defer hm.mu.RUnlock()
	
	var failed []NodeID
	for nodeID, lastHB := range hm.monitoringNodes {
		if time.Since(lastHB) > hm.timeout {
			failed = append(failed, nodeID)
		}
	}
	return failed
}

// PrintHeartbeatStatus prints the heartbeat status of all monitored nodes.
func (hm *HeartbeatMonitor) PrintHeartbeatStatus() {
	hm.mu.RLock()
	defer hm.mu.RUnlock()
	
	fmt.Println("=== Heartbeat Status ===")
	for nodeID, lastHB := range hm.monitoringNodes {
		status := "ALIVE"
		if time.Since(lastHB) > hm.timeout {
			status = "FAILED"
		}
		elapsed := time.Since(lastHB).Truncate(time.Millisecond)
		fmt.Printf("Node %d: %s (last heartbeat: %s ago)\n", nodeID, status, elapsed)
	}
	fmt.Println()
}

// RingSimulator provides a high-level interface for simulating Chord ring operations.
type RingSimulator struct {
	ring          *ChordRing
	migration     *MigrationTracker
	heartbeat     *HeartbeatMonitor
	NodeAddresses []string
}

// NewRingSimulator creates a new ring simulator.
func NewRingSimulator() *RingSimulator {
	return &RingSimulator{
		ring:          NewChordRing(),
		migration:     NewMigrationTracker(),
		heartbeat:     NewHeartbeatMonitor(30 * time.Second),
		NodeAddresses: []string{},
	}
}

// JoinNode simulates a node joining the Chord ring.
func (rs *RingSimulator) JoinNode(address string) *Node {
	// Generate node ID from address
	nodeID := GenerateNodeID(address)
	
	// Create the new node
	node := NewNode(nodeID, address)
	
	// Add to ring
	rs.ring.AddNode(node)
	
	// Stabilize the ring
	rs.ring.Stabilize()
	
	// Register heartbeat
	rs.heartbeat.RegisterNode(nodeID)
	
	// Track address
	rs.NodeAddresses = append(rs.NodeAddresses, address)
	
	fmt.Printf("  Node joined: %s (ID: %d)\n", address, nodeID)
	return node
}

// LeaveNode simulates a node leaving the Chord ring gracefully.
func (rs *RingSimulator) LeaveNode(address string) {
	// Find the node
	nodeID := GenerateNodeID(address)
	node, ok := rs.ring.GetNode(nodeID)
	if !ok {
		fmt.Printf("  Node not found: %s\n", address)
		return
	}
	
	// Record key migration
	keys := node.KeysForNode()
	if len(keys) > 0 {
		rs.migration.RecordMigration(nodeID, node.GetSuccessor(), keys)
	}
	
	// Remove from ring
	rs.ring.RemoveNode(nodeID)
	
	// Stabilize the ring
	rs.ring.Stabilize()
	
	fmt.Printf("  Node left: %s (ID: %d), migrated %d keys\n", address, nodeID, len(keys))
}

// StoreKey stores a key-value pair in the ring.
func (rs *RingSimulator) StoreKey(key, value string) {
	rs.ring.Store(key, value)
}

// RetrieveKey retrieves a value from the ring.
func (rs *RingSimulator) RetrieveKey(key string) (string, bool) {
	return rs.ring.Retrieve(key)
}

// PrintStatus prints the current ring status.
func (rs *RingSimulator) PrintStatus() {
	fmt.Println("\n=== Ring Status ===")
	rs.ring.PrintRingSummary()
	
	// Print key distribution
	nodes := rs.ring.GetNodes()
	var ids []NodeID
	keyDistribution := make(map[NodeID]int)
	for _, node := range nodes {
		ids = append(ids, node.ID)
		keyDistribution[node.ID] = node.Store.Size()
	}
	fmt.Printf("Key distribution: ")
	for i := 0; i < len(ids); i++ {
		for j := i + 1; j < len(ids); j++ {
			if ids[i] > ids[j] {
				ids[i], ids[j] = ids[j], ids[i]
			}
		}
	}
	for i, id := range ids {
		if i > 0 {
			fmt.Print(" ")
		}
		fmt.Printf("%d:%d", id, keyDistribution[id])
	}
	fmt.Println()
	fmt.Println()
}

// PrintMigrations prints all recorded key migrations.
func (rs *RingSimulator) PrintMigrations() {
	migrations := rs.migration.GetMigrations()
	if len(migrations) == 0 {
		fmt.Println("No key migrations recorded.")
		return
	}
	
	fmt.Println("=== Key Migrations ===")
	for i, m := range migrations {
		fmt.Printf("Migration %d: Node %d -> Node %d (%d keys)\n",
			i+1, m.FromNode, m.ToNode, len(m.Keys))
		for _, key := range m.Keys {
			fmt.Printf("  - %s\n", key)
		}
	}
	fmt.Println()
}

// Verify prints the ring integrity check result.
func (rs *RingSimulator) Verify() {
	ok, issues := rs.ring.VerifyRingIntegrity()
	if ok {
		fmt.Println("Ring integrity: OK")
	} else {
		fmt.Println("Ring integrity: ISSUES FOUND")
		for _, issue := range issues {
			fmt.Printf("  - %s\n", issue)
		}
	}
}

package chord

import (
	"testing"
	"time"
)

func TestNewMigrationTracker(t *testing.T) {
	tracker := NewMigrationTracker()
	
	if tracker == nil {
		t.Fatal("NewMigrationTracker() should not return nil")
	}
	
	if tracker.MigrationCount() != 0 {
		t.Errorf("New tracker should have 0 migrations, got %d", tracker.MigrationCount())
	}
}

func TestMigrationTrackerRecord(t *testing.T) {
	tracker := NewMigrationTracker()
	
	from := GenerateNodeID("from-node")
	to := GenerateNodeID("to-node")
	
	tracker.RecordMigration(from, to, []string{"key1", "key2"})
	
	if tracker.MigrationCount() != 1 {
		t.Errorf("Migration count = %d, want 1", tracker.MigrationCount())
	}
	
	migrations := tracker.GetMigrations()
	if len(migrations) != 1 {
		t.Errorf("Migrations length = %d, want 1", len(migrations))
	}
	
	if migrations[0].FromNode != from {
		t.Errorf("FromNode = %d, want %d", migrations[0].FromNode, from)
	}
	
	if migrations[0].ToNode != to {
		t.Errorf("ToNode = %d, want %d", migrations[0].ToNode, to)
	}
	
	if len(migrations[0].Keys) != 2 {
		t.Errorf("Keys length = %d, want 2", len(migrations[0].Keys))
	}
}

func TestMigrationTrackerClear(t *testing.T) {
	tracker := NewMigrationTracker()
	
	tracker.RecordMigration(1, 2, []string{"key1"})
	
	tracker.Clear()
	
	if tracker.MigrationCount() != 0 {
		t.Errorf("After clear, count = %d, want 0", tracker.MigrationCount())
	}
}

func TestNewHeartbeatMonitor(t *testing.T) {
	monitor := NewHeartbeatMonitor(5 * time.Second)
	
	if monitor == nil {
		t.Fatal("NewHeartbeatMonitor() should not return nil")
	}
	
	// Node not registered should not be alive
	if monitor.IsAlive(999) {
		t.Error("Unregistered node should not be alive")
	}
}

func TestHeartbeatMonitorRegister(t *testing.T) {
	monitor := NewHeartbeatMonitor(5 * time.Second)
	
	nodeID := GenerateNodeID("test-node")
	monitor.RegisterNode(nodeID)
	
	if !monitor.IsAlive(nodeID) {
		t.Error("Registered node should be alive")
	}
}

func TestHeartbeatMonitorUpdate(t *testing.T) {
	monitor := NewHeartbeatMonitor(5 * time.Second)
	
	nodeID := GenerateNodeID("test-node")
	monitor.RegisterNode(nodeID)
	
	// Update heartbeat
	monitor.UpdateHeartbeat(nodeID)
	
	if !monitor.IsAlive(nodeID) {
		t.Error("Node should be alive after heartbeat update")
	}
}

func TestHeartbeatMonitorTimeout(t *testing.T) {
	monitor := NewHeartbeatMonitor(1 * time.Millisecond)
	
	nodeID := GenerateNodeID("test-node")
	monitor.RegisterNode(nodeID)
	
	// Wait for timeout
	time.Sleep(10 * time.Millisecond)
	
	if monitor.IsAlive(nodeID) {
		t.Error("Node should be dead after timeout")
	}
}

func TestHeartbeatMonitorGetFailedNodes(t *testing.T) {
	monitor := NewHeartbeatMonitor(1 * time.Millisecond)
	
	node1 := GenerateNodeID("node-1")
	node2 := GenerateNodeID("node-2")
	
	monitor.RegisterNode(node1)
	monitor.RegisterNode(node2)
	
	// Wait for timeout
	time.Sleep(10 * time.Millisecond)
	
	failed := monitor.GetFailedNodes()
	
	if len(failed) != 2 {
		t.Errorf("Failed nodes count = %d, want 2", len(failed))
	}
}

func TestHeartbeatMonitorPartialFailure(t *testing.T) {
	monitor := NewHeartbeatMonitor(1 * time.Millisecond)
	
	node1 := GenerateNodeID("node-1")
	node2 := GenerateNodeID("node-2")
	
	monitor.RegisterNode(node1)
	monitor.RegisterNode(node2)
	
	// Update node2 heartbeat to keep it alive
	monitor.UpdateHeartbeat(node2)
	
	// Wait for timeout
	time.Sleep(10 * time.Millisecond)
	
	failed := monitor.GetFailedNodes()
	
	if len(failed) != 1 {
		t.Errorf("Failed nodes count = %d, want 1", len(failed))
	}
	
	if failed[0] != node1 {
		t.Errorf("Failed node = %d, want %d", failed[0], node1)
	}
}

func TestNewRingSimulator(t *testing.T) {
	sim := NewRingSimulator()
	
	if sim == nil {
		t.Fatal("NewRingSimulator() should not return nil")
	}
	
	if sim.ring == nil {
		t.Error("Ring simulator should have a ring")
	}
	
	if sim.migration == nil {
		t.Error("Ring simulator should have a migration tracker")
	}
	
	if sim.heartbeat == nil {
		t.Error("Ring simulator should have a heartbeat monitor")
	}
}

func TestRingSimulatorJoin(t *testing.T) {
	sim := NewRingSimulator()
	
	node := sim.JoinNode("test-node-1")
	
	if node == nil {
		t.Fatal("JoinNode should return a node")
	}
	
	if node.ID == 0 {
		t.Error("Joined node should have non-zero ID")
	}
	
	if len(sim.ring.GetNodes()) != 1 {
		t.Errorf("Ring should have 1 node, got %d", len(sim.ring.GetNodes()))
	}
}

func TestRingSimulatorMultipleJoin(t *testing.T) {
	sim := NewRingSimulator()
	
	for i := 0; i < 5; i++ {
		sim.JoinNode("test-node-" + string(rune('1'+i)))
	}
	
	if len(sim.ring.GetNodes()) != 5 {
		t.Errorf("Ring should have 5 nodes, got %d", len(sim.ring.GetNodes()))
	}
}

func TestRingSimulatorStoreRetrieve(t *testing.T) {
	sim := NewRingSimulator()
	
	sim.JoinNode("test-node-1")
	sim.JoinNode("test-node-2")
	sim.ring.Stabilize()
	
	sim.StoreKey("sim-key", "sim-value")
	
	value, found := sim.RetrieveKey("sim-key")
	if !found {
		t.Error("Should retrieve stored value")
	}
	if value != "sim-value" {
		t.Errorf("Retrieved value = %s, want sim-value", value)
	}
}

func TestRingSimulatorVerify(t *testing.T) {
	sim := NewRingSimulator()
	
	sim.JoinNode("test-node-1")
	sim.JoinNode("test-node-2")
	sim.JoinNode("test-node-3")
	sim.ring.Stabilize()
	
	sim.Verify()
	// Just verify it doesn't panic
}

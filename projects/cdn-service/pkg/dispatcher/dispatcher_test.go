package dispatcher

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestRoundRobinStrategy_Select(t *testing.T) {
	strategy := NewRoundRobinStrategy()

	nodes := []*Node{
		{ID: "node1", Address: "192.168.1.1:8080", Weight: 1, Status: NodeStatusHealthy},
		{ID: "node2", Address: "192.168.1.2:8080", Weight: 1, Status: NodeStatusHealthy},
		{ID: "node3", Address: "192.168.1.3:8080", Weight: 1, Status: NodeStatusHealthy},
	}

	req := httptest.NewRequest("GET", "/", nil)

	// Select nodes in round-robin order
	selected := make(map[string]int)
	for i := 0; i < 9; i++ {
		node, err := strategy.Select(nodes, req)
		if err != nil {
			t.Fatalf("Unexpected error: %v", err)
		}
		selected[node.ID]++
	}

	// Each node should be selected 3 times
	if selected["node1"] != 3 {
		t.Errorf("Expected node1 selected 3 times, got %d", selected["node1"])
	}
	if selected["node2"] != 3 {
		t.Errorf("Expected node2 selected 3 times, got %d", selected["node2"])
	}
	if selected["node3"] != 3 {
		t.Errorf("Expected node3 selected 3 times, got %d", selected["node3"])
	}
}

func TestRoundRobinStrategy_NoNodes(t *testing.T) {
	strategy := NewRoundRobinStrategy()

	req := httptest.NewRequest("GET", "/", nil)

	_, err := strategy.Select([]*Node{}, req)
	if err != ErrNoNodes {
		t.Errorf("Expected ErrNoNodes, got %v", err)
	}
}

func TestRoundRobinStrategy_UnhealthyNodes(t *testing.T) {
	strategy := NewRoundRobinStrategy()

	nodes := []*Node{
		{ID: "node1", Address: "192.168.1.1:8080", Weight: 1, Status: NodeStatusUnhealthy},
		{ID: "node2", Address: "192.168.1.2:8080", Weight: 1, Status: NodeStatusUnhealthy},
	}

	req := httptest.NewRequest("GET", "/", nil)

	_, err := strategy.Select(nodes, req)
	if err != ErrNoNodes {
		t.Errorf("Expected ErrNoNodes, got %v", err)
	}
}

func TestWeightedRoundRobinStrategy_Select(t *testing.T) {
	strategy := NewWeightedRoundRobinStrategy()

	nodes := []*Node{
		{ID: "node1", Address: "192.168.1.1:8080", Weight: 2, Status: NodeStatusHealthy},
		{ID: "node2", Address: "192.168.1.2:8080", Weight: 1, Status: NodeStatusHealthy},
	}

	req := httptest.NewRequest("GET", "/", nil)

	// Select nodes in weighted round-robin order
	selected := make(map[string]int)
	for i := 0; i < 6; i++ {
		node, err := strategy.Select(nodes, req)
		if err != nil {
			t.Fatalf("Unexpected error: %v", err)
		}
		selected[node.ID]++
	}

	// node1 should be selected twice as often as node2
	if selected["node1"] != 4 {
		t.Errorf("Expected node1 selected 4 times, got %d", selected["node1"])
	}
	if selected["node2"] != 2 {
		t.Errorf("Expected node2 selected 2 times, got %d", selected["node2"])
	}
}

func TestLeastConnectionsStrategy_Select(t *testing.T) {
	strategy := NewLeastConnectionsStrategy()

	nodes := []*Node{
		{ID: "node1", Address: "192.168.1.1:8080", Weight: 1, Status: NodeStatusHealthy, Connections: 5},
		{ID: "node2", Address: "192.168.1.2:8080", Weight: 1, Status: NodeStatusHealthy, Connections: 3},
		{ID: "node3", Address: "192.168.1.3:8080", Weight: 1, Status: NodeStatusHealthy, Connections: 7},
	}

	req := httptest.NewRequest("GET", "/", nil)

	// Should select node2 (least connections)
	node, err := strategy.Select(nodes, req)
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}
	if node.ID != "node2" {
		t.Errorf("Expected node2, got %s", node.ID)
	}
}

func TestDispatcher_AddNode(t *testing.T) {
	d := NewDispatcher(NewRoundRobinStrategy())
	defer d.Stop()

	node := &Node{
		ID:      "node1",
		Address: "192.168.1.1:8080",
		Weight:  1,
		Status:  NodeStatusHealthy,
	}

	d.AddNode(node)

	nodes := d.Nodes()
	if len(nodes) != 1 {
		t.Errorf("Expected 1 node, got %d", len(nodes))
	}
	if nodes[0].ID != "node1" {
		t.Errorf("Expected node1, got %s", nodes[0].ID)
	}
}

func TestDispatcher_RemoveNode(t *testing.T) {
	d := NewDispatcher(NewRoundRobinStrategy())
	defer d.Stop()

	node := &Node{
		ID:      "node1",
		Address: "192.168.1.1:8080",
		Weight:  1,
		Status:  NodeStatusHealthy,
	}

	d.AddNode(node)
	d.RemoveNode("node1")

	nodes := d.Nodes()
	if len(nodes) != 0 {
		t.Errorf("Expected 0 nodes, got %d", len(nodes))
	}
}

func TestDispatcher_Select(t *testing.T) {
	d := NewDispatcher(NewRoundRobinStrategy())
	defer d.Stop()

	d.AddNode(&Node{
		ID:      "node1",
		Address: "192.168.1.1:8080",
		Weight:  1,
		Status:  NodeStatusHealthy,
	})
	d.AddNode(&Node{
		ID:      "node2",
		Address: "192.168.1.2:8080",
		Weight:  1,
		Status:  NodeStatusHealthy,
	})

	req := httptest.NewRequest("GET", "/", nil)

	// Select nodes
	node1, err := d.Select(req)
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}

	node2, err := d.Select(req)
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}

	// Should alternate between nodes
	if node1.ID == node2.ID {
		t.Error("Expected different nodes")
	}
}

func TestDispatcher_Release(t *testing.T) {
	d := NewDispatcher(NewRoundRobinStrategy())
	defer d.Stop()

	node := &Node{
		ID:          "node1",
		Address:     "192.168.1.1:8080",
		Weight:      1,
		Status:      NodeStatusHealthy,
		Connections: 0,
	}

	d.AddNode(node)

	req := httptest.NewRequest("GET", "/", nil)

	// Select and release
	selected, _ := d.Select(req)
	if selected.Connections != 1 {
		t.Errorf("Expected 1 connection, got %d", selected.Connections)
	}

	d.Release(selected)
	if selected.Connections != 0 {
		t.Errorf("Expected 0 connections, got %d", selected.Connections)
	}
}

func TestFilterHealthy(t *testing.T) {
	nodes := []*Node{
		{ID: "node1", Status: NodeStatusHealthy},
		{ID: "node2", Status: NodeStatusUnhealthy},
		{ID: "node3", Status: NodeStatusHealthy},
		{ID: "node4", Status: NodeStatusUnknown},
	}

	healthy := filterHealthy(nodes)
	if len(healthy) != 2 {
		t.Errorf("Expected 2 healthy nodes, got %d", len(healthy))
	}
	if healthy[0].ID != "node1" {
		t.Errorf("Expected node1, got %s", healthy[0].ID)
	}
	if healthy[1].ID != "node3" {
		t.Errorf("Expected node3, got %s", healthy[1].ID)
	}
}

func BenchmarkRoundRobinStrategy_Select(b *testing.B) {
	strategy := NewRoundRobinStrategy()

	nodes := []*Node{
		{ID: "node1", Address: "192.168.1.1:8080", Weight: 1, Status: NodeStatusHealthy},
		{ID: "node2", Address: "192.168.1.2:8080", Weight: 1, Status: NodeStatusHealthy},
		{ID: "node3", Address: "192.168.1.3:8080", Weight: 1, Status: NodeStatusHealthy},
	}

	req := httptest.NewRequest("GET", "/", nil)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		strategy.Select(nodes, req)
	}
}
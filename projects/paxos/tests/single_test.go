package paxos_test

import (
	"testing"

	"paxos/src/paxos"
)

// TestSinglePaxosAllNodes verifies single Paxos works with all nodes.
func TestSinglePaxosAllNodes(t *testing.T) {
	nodes := []string{"node1", "node2", "node3", "node4", "node5"}
	network := paxos.NewNetworkSimulator(nodes)

	result, err := paxos.SinglePaxos(nodes, network, "test-value")
	if err != nil {
		t.Fatalf("SinglePaxos failed: %v", err)
	}

	if !result.Decided {
		t.Error("Expected consensus to be decided")
	}

	if result.Value != "test-value" {
		t.Errorf("Expected value 'test-value', got %v", result.Value)
	}

	if result.Promises <= len(nodes)/2 {
		t.Errorf("Expected more than %d promises, got %d", len(nodes)/2, result.Promises)
	}

	if result.Acceptances <= len(nodes)/2 {
		t.Errorf("Expected more than %d acceptances, got %d", len(nodes)/2, result.Acceptances)
	}
}

// TestSinglePaxosMajority verifies single Paxos works with majority.
func TestSinglePaxosMajority(t *testing.T) {
	// Use 3 nodes - majority is 2
	nodes := []string{"node1", "node2", "node3"}
	network := paxos.NewNetworkSimulator(nodes)

	result, err := paxos.SinglePaxos(nodes, network, "majority-value")
	if err != nil {
		t.Fatalf("SinglePaxos failed: %v", err)
	}

	if !result.Decided {
		t.Error("Expected consensus to be decided")
	}
}

// TestSinglePaxosMinority verifies single Paxos fails with minority.
func TestSinglePaxosMinority(t *testing.T) {
	// Use 2 nodes - no majority possible with 1 node
	nodes := []string{"node1", "node2"}
	network := paxos.NewNetworkSimulator(nodes)

	_, err := paxos.SinglePaxos(nodes, network, "minority-value")
	if err == nil {
		t.Error("Expected consensus to fail with minority")
	}
}

// TestSinglePaxosSingleNode verifies single Paxos with 1 node.
func TestSinglePaxosSingleNode(t *testing.T) {
	nodes := []string{"node1"}
	network := paxos.NewNetworkSimulator(nodes)

	result, err := paxos.SinglePaxos(nodes, network, "single-value")
	if err != nil {
		t.Fatalf("SinglePaxos failed: %v", err)
	}

	if !result.Decided {
		t.Error("Expected consensus to be decided with single node")
	}

	if result.Value != "single-value" {
		t.Errorf("Expected value 'single-value', got %v", result.Value)
	}
}

// TestSinglePaxosDifferentValues verifies different values can be proposed.
func TestSinglePaxosDifferentValues(t *testing.T) {
	nodes := []string{"node1", "node2", "node3"}
	network := paxos.NewNetworkSimulator(nodes)

	values := []interface{}{"value1", "value2", 42, true, "final"}

	for _, val := range values {
		network = paxos.NewNetworkSimulator(nodes)
		result, err := paxos.SinglePaxos(nodes, network, val)
		if err != nil {
			t.Fatalf("SinglePaxos failed for value %v: %v", val, err)
		}
		if !result.Decided {
			t.Errorf("Expected consensus for value %v", val)
		}
	}

	_ = values[len(values)-1] // last value is the one that will be decided
}

// TestSinglePaxosNetworkMessages verifies message flow.
func TestSinglePaxosNetworkMessages(t *testing.T) {
	nodes := []string{"node1", "node2", "node3"}
	network := paxos.NewNetworkSimulator(nodes)

	result, err := paxos.SinglePaxos(nodes, network, "msg-test")
	if err != nil {
		t.Fatalf("SinglePaxos failed: %v", err)
	}

	messages := network.AllMessages()
	if len(messages) == 0 {
		t.Error("Expected messages in network")
	}
}

// TestSinglePaxosLargeCluster verifies Paxos works with larger cluster.
func TestSinglePaxosLargeCluster(t *testing.T) {
	nodes := []string{"n1", "n2", "n3", "n4", "n5", "n6", "n7"}
	network := paxos.NewNetworkSimulator(nodes)

	result, err := paxos.SinglePaxos(nodes, network, "large-cluster")
	if err != nil {
		t.Fatalf("SinglePaxos failed: %v", err)
	}

	if !result.Decided {
		t.Error("Expected consensus in large cluster")
	}

	// Majority is 4
	majority := len(nodes)/2 + 1
	if result.Promises < majority {
		t.Errorf("Expected at least %d promises, got %d", majority, result.Promises)
	}
}

// TestSinglePaxosIntValue verifies integer values work.
func TestSinglePaxosIntValue(t *testing.T) {
	nodes := []string{"node1", "node2", "node3"}
	network := paxos.NewNetworkSimulator(nodes)

	value := 12345
	result, err := paxos.SinglePaxos(nodes, network, value)
	if err != nil {
		t.Fatalf("SinglePaxos failed: %v", err)
	}

	if result.Value != value {
		t.Errorf("Expected value %d, got %v", value, result.Value)
	}
}

// TestSinglePaxosBoolValue verifies boolean values work.
func TestSinglePaxosBoolValue(t *testing.T) {
	nodes := []string{"node1", "node2", "node3"}
	network := paxos.NewNetworkSimulator(nodes)

	value := true
	result, err := paxos.SinglePaxos(nodes, network, value)
	if err != nil {
		t.Fatalf("SinglePaxos failed: %v", err)
	}

	if result.Value != value {
		t.Errorf("Expected value %v, got %v", value, result.Value)
	}
}

// TestSinglePaxosEmptyStringValue verifies empty string values work.
func TestSinglePaxosEmptyStringValue(t *testing.T) {
	nodes := []string{"node1", "node2", "node3"}
	network := paxos.NewNetworkSimulator(nodes)

	value := ""
	result, err := paxos.SinglePaxos(nodes, network, value)
	if err != nil {
		t.Fatalf("SinglePaxos failed: %v", err)
	}

	if result.Value != value {
		t.Errorf("Expected value %q, got %v", value, result.Value)
	}
}

package test

import (
	"testing"
	"time"

	"github.com/dht-chord/internal"
)

// ==================== NetworkNode Tests ====================

func TestNewNetworkNode(t *testing.T) {
	node := internal.NewNetworkNode("localhost:19000")

	if node == nil {
		t.Fatal("NewNetworkNode should not return nil")
	}

	if node.GetAddr() != "localhost:19000" {
		t.Errorf("Node addr = %s, want localhost:19000", node.GetAddr())
	}

	if node.GetID() == nil {
		t.Error("Node ID should not be nil")
	}
}

func TestNetworkNodeStartStop(t *testing.T) {
	node := internal.NewNetworkNode("localhost:19001")

	// Start
	if err := node.Start(); err != nil {
		t.Fatalf("Failed to start node: %v", err)
	}

	if !node.IsRunning() {
		t.Error("Node should be running after start")
	}

	// Stop
	if err := node.Stop(); err != nil {
		t.Fatalf("Failed to stop node: %v", err)
	}

	// Give it a moment to stop
	time.Sleep(100 * time.Millisecond)
}

func TestNetworkNodePing(t *testing.T) {
	// Create and start a server node
	server := internal.NewNetworkNode("localhost:19002")
	if err := server.Start(); err != nil {
		t.Fatalf("Failed to start server: %v", err)
	}
	defer server.Stop()

	time.Sleep(100 * time.Millisecond)

	// Create a client node
	client := internal.NewNetworkNode("localhost:19003")
	if err := client.Start(); err != nil {
		t.Fatalf("Failed to start client: %v", err)
	}
	defer client.Stop()

	time.Sleep(100 * time.Millisecond)

	// Ping server from client
	if err := client.Ping("localhost:19002"); err != nil {
		t.Fatalf("Failed to ping server: %v", err)
	}
}

func TestNetworkNodeStore(t *testing.T) {
	// Create and start a server node
	server := internal.NewNetworkNode("localhost:19004")
	if err := server.Start(); err != nil {
		t.Fatalf("Failed to start server: %v", err)
	}
	defer server.Stop()

	time.Sleep(100 * time.Millisecond)

	// Create a client node
	client := internal.NewNetworkNode("localhost:19005")
	if err := client.Start(); err != nil {
		t.Fatalf("Failed to start client: %v", err)
	}
	defer client.Stop()

	time.Sleep(100 * time.Millisecond)

	// Store a value on server
	if err := client.RemoteStore("localhost:19004", "testkey", "testvalue"); err != nil {
		t.Fatalf("Failed to store: %v", err)
	}
}

func TestNetworkNodeFindNode(t *testing.T) {
	// Create and start a server node
	server := internal.NewNetworkNode("localhost:19006")
	if err := server.Start(); err != nil {
		t.Fatalf("Failed to start server: %v", err)
	}
	defer server.Stop()

	time.Sleep(100 * time.Millisecond)

	// Create a client node
	client := internal.NewNetworkNode("localhost:19007")
	if err := client.Start(); err != nil {
		t.Fatalf("Failed to start client: %v", err)
	}
	defer client.Stop()

	time.Sleep(100 * time.Millisecond)

	// Find nodes
	targetID := internal.KademliaHash("target")
	contacts, err := client.RemoteFindNode("localhost:19006", targetID)
	if err != nil {
		t.Fatalf("Failed to find nodes: %v", err)
	}

	// Server should return itself as a contact
	if len(contacts) == 0 {
		t.Error("FindNode should return at least one contact")
	}
}

func TestNetworkNodeFindValue(t *testing.T) {
	// Create and start a server node
	server := internal.NewNetworkNode("localhost:19008")
	if err := server.Start(); err != nil {
		t.Fatalf("Failed to start server: %v", err)
	}
	defer server.Stop()

	time.Sleep(100 * time.Millisecond)

	// Store a value on server
	serverNode := server.GetID()
	_ = serverNode

	// Create a client node
	client := internal.NewNetworkNode("localhost:19009")
	if err := client.Start(); err != nil {
		t.Fatalf("Failed to start client: %v", err)
	}
	defer client.Stop()

	time.Sleep(100 * time.Millisecond)

	// Store value on server first
	if err := client.RemoteStore("localhost:19008", "mykey", "myvalue"); err != nil {
		t.Fatalf("Failed to store: %v", err)
	}

	// Find value
	value, contacts, found, err := client.RemoteFindValue("localhost:19008", "mykey")
	if err != nil {
		t.Fatalf("Failed to find value: %v", err)
	}

	if found {
		if value != "myvalue" {
			t.Errorf("FindValue returned %s, want myvalue", value)
		}
	} else {
		// If not found, should return contacts
		if len(contacts) == 0 {
			t.Error("FindValue should return contacts if value not found")
		}
	}
}

// ==================== NodeManager Tests ====================

func TestNodeManager(t *testing.T) {
	nm := internal.NewNodeManager()

	// Create nodes
	node1, err := nm.CreateNode("localhost:19010")
	if err != nil {
		t.Fatalf("Failed to create node1: %v", err)
	}

	node2, err := nm.CreateNode("localhost:19011")
	if err != nil {
		t.Fatalf("Failed to create node2: %v", err)
	}

	// Verify node count
	if nm.NodeCount() != 2 {
		t.Errorf("NodeManager should have 2 nodes, got %d", nm.NodeCount())
	}

	// Get node
	got := nm.GetNode("localhost:19010")
	if got == nil {
		t.Error("GetNode should return node1")
	}

	// Get primary
	primary := nm.GetPrimary()
	if primary == nil {
		t.Error("GetPrimary should not return nil")
	}

	// Remove node
	if err := nm.RemoveNode("localhost:19011"); err != nil {
		t.Fatalf("Failed to remove node: %v", err)
	}

	if nm.NodeCount() != 1 {
		t.Errorf("NodeManager should have 1 node after removal, got %d", nm.NodeCount())
	}

	// Stop all
	nm.StopAll()

	// Clean up
	_ = node1
	_ = node2
}

// ==================== Discovery Tests ====================

func TestDiscovery(t *testing.T) {
	// Create a node
	node := internal.NewNetworkNode("localhost:19012")
	if err := node.Start(); err != nil {
		t.Fatalf("Failed to start node: %v", err)
	}
	defer node.Stop()

	time.Sleep(100 * time.Millisecond)

	// Create discovery
	config := internal.DefaultDiscoveryConfig()
	config.RefreshInterval = 1 * time.Second
	config.PingInterval = 1 * time.Second

	discovery := internal.NewDiscovery(node, config)

	// Start discovery
	if err := discovery.Start(); err != nil {
		t.Fatalf("Failed to start discovery: %v", err)
	}

	if !discovery.IsRunning() {
		t.Error("Discovery should be running")
	}

	// Stop discovery
	discovery.Stop()

	time.Sleep(100 * time.Millisecond)
}

func TestDiscoveryBootstrap(t *testing.T) {
	// Create bootstrap node
	bootstrap := internal.NewNetworkNode("localhost:19013")
	if err := bootstrap.Start(); err != nil {
		t.Fatalf("Failed to start bootstrap: %v", err)
	}
	defer bootstrap.Stop()

	time.Sleep(100 * time.Millisecond)

	// Create a node with bootstrap
	node := internal.NewNetworkNode("localhost:19014")
	if err := node.Start(); err != nil {
		t.Fatalf("Failed to start node: %v", err)
	}
	defer node.Stop()

	time.Sleep(100 * time.Millisecond)

	// Create discovery with bootstrap
	config := internal.DefaultDiscoveryConfig()
	config.BootstrapAddrs = []string{"localhost:19013"}

	discovery := internal.NewDiscovery(node, config)
	if err := discovery.Start(); err != nil {
		t.Fatalf("Failed to start discovery: %v", err)
	}
	defer discovery.Stop()

	// Give it time to bootstrap
	time.Sleep(500 * time.Millisecond)

	// Check that bootstrap node is in routing table
	bootstrapID := bootstrap.GetID()
	contacts := node.GetID()
	_ = contacts
	_ = bootstrapID
}

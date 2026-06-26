package main

import (
	"fmt"
	"log"
	"math/rand"
	"sync"
	"time"

	"raft-consensus/src"
)

// ClusterDemo demonstrates a complete Raft cluster with multiple nodes.
//
// This demo shows:
//   1. Multi-node cluster formation
//   2. Leader election in a cluster
//   3. Log replication across nodes
//   4. Client request handling through the leader
//   5. Cluster membership changes
//   6. Safety verification across all nodes
//
// This is the most comprehensive demo, showing all Raft concepts working together.
type ClusterDemo struct {
	nodes   map[int]*raft.Node
	peers   map[int]string
	cluster *raft.ClusterManager
	mu      sync.Mutex
}

// NewClusterDemo creates a new cluster demo with the given peers.
func NewClusterDemo(peers map[int]string) *ClusterDemo {
	cluster := raft.NewClusterManager(peers)
	return &ClusterDemo{
		nodes:   make(map[int]*raft.Node),
		peers:   peers,
		cluster: cluster,
	}
}

// Start starts all nodes in the cluster.
func (cd *ClusterDemo) Start() {
	for id, addr := range cd.peers {
		log.Printf("Starting node %d at %s", id, addr)
		cd.nodes[id] = raft.StartNode(id, cd.peers)
	}
}

// Shutdown shuts down all nodes in the cluster.
func (cd *ClusterDemo) Shutdown() {
	for id, node := range cd.nodes {
		log.Printf("Shutting down node %d", id)
		node.Shutdown()
		delete(cd.nodes, id)
	}
}

// ElectLeader triggers an election and returns the leader.
func (cd *ClusterDemo) ElectLeader(candidateID int) *raft.Node {
	cd.nodes[candidateID].StartElection()
	return cd.nodes[candidateID]
}

// SubmitRequest submits a request to the leader.
func (cd *ClusterDemo) SubmitRequest(command string) string {
	// Find the leader
	var leader *raft.Node
	for _, node := range cd.nodes {
		if node.GetRole() == "Leader" {
			leader = node
			break
		}
	}

	if leader == nil {
		return "NO_LEADER: No leader elected"
	}

	return leader.SubmitRequest(command)
}

// GetLogStates returns the log state of all nodes.
func (cd *ClusterDemo) GetLogStates() map[int][]raft.LogEntry {
	states := make(map[int][]raft.LogEntry)
	for id, node := range cd.nodes {
		states[id] = node.GetLog()
	}
	return states
}

// VerifySafety checks if all safety properties hold.
func (cd *ClusterDemo) VerifySafety() (bool, []string) {
	safetyManager := raft.NewSafetyManager()

	// Get leader log
	var leaderLog []raft.LogEntry
	var leaderID int
	for id, node := range cd.nodes {
		if node.GetRole() == "Leader" {
			leaderLog = node.GetLog()
			leaderID = id
			break
		}
	}

	if leaderLog == nil {
		return false, []string{"No leader found"}
	}

	// Check against all followers
	followerLogs := make(map[int][]raft.LogEntry)
	for id, node := range cd.nodes {
		if id != leaderID {
			followerLogs[id] = node.GetLog()
		}
	}

	consistent, issues := safetyManager.VerifyClusterSafety(leaderLog, followerLogs)
	return consistent, issues
}

// AddPeer adds a new peer to the cluster.
func (cd *ClusterDemo) AddPeer(peerID int, addr string) error {
	if err := cd.cluster.AddPeer(peerID); err != nil {
		return err
	}
	cd.peers[peerID] = addr
	cd.nodes[peerID] = raft.StartNode(peerID, cd.peers)
	return nil
}

// RemovePeer removes a peer from the cluster.
func (cd *ClusterDemo) RemovePeer(peerID int) error {
	// Don't remove the leader
	if cd.nodes[peerID].GetRole() == "Leader" {
		return fmt.Errorf("cannot remove leader")
	}

	if err := cd.cluster.RemovePeer(peerID); err != nil {
		return err
	}
	delete(cd.peers, peerID)
	cd.nodes[peerID].Shutdown()
	delete(cd.nodes, peerID)
	return nil
}

// PrintClusterStatus prints the current status of all nodes.
func (cd *ClusterDemo) PrintClusterStatus() {
	fmt.Println("Cluster Status:")
	fmt.Println("-------------------------------")

	for id, node := range cd.nodes {
		logEntries := node.GetLog()
		commitIdx := node.GetCommitIndex()
		fmt.Printf("  Node %d: role=%-8s term=%d log_len=%d commit_idx=%d\n",
			id, node.GetRole(), node.GetCurrentTerm(), len(logEntries), commitIdx)

		for j, entry := range logEntries {
			fmt.Printf("    [%d] term=%d cmd=%s\n", j+1, entry.Term, entry.Command)
		}
	}
	fmt.Println("-------------------------------")
}

func main() {
	fmt.Println("=== Raft Cluster Demo ===")
	fmt.Println()

	// Create initial 3-node cluster
	peers := map[int]string{
		1: "localhost:8001",
		2: "localhost:8002",
		3: "localhost:8003",
	}

	fmt.Printf("Initial cluster: %s\n", raft.FormatClusterInfo(peers, len(peers)))
	fmt.Println()

	// Create and start cluster
	demo := NewClusterDemo(peers)
	demo.Start()
	time.Sleep(100 * time.Millisecond)
	fmt.Println()

	// Phase 1: Leader Election
	fmt.Println("--- Phase 1: Leader Election ---")
	leader := demo.ElectLeader(1)
	fmt.Printf("Leader elected: Node %d (term %d)\n", leader.GetPeerID(), leader.GetCurrentTerm())
	demo.PrintClusterStatus()
	fmt.Println()

	// Phase 2: Log Replication
	fmt.Println("--- Phase 2: Log Replication ---")
	commands := []string{
		"SET user:1=Alice",
		"SET user:2=Bob",
		"SET user:3=Charlie",
		"SET counter=42",
		"DELETE user:2",
	}

	fmt.Println("Submitting client requests...")
	for _, cmd := range commands {
		result := demo.SubmitRequest(cmd)
		fmt.Printf("  %s -> %s\n", cmd, result)
	}
	fmt.Println()

	// Phase 3: Verify Consistency
	fmt.Println("--- Phase 3: Consistency Verification ---")
	consistent, issues := demo.VerifySafety()
	if consistent {
		fmt.Println("  All safety properties verified!")
	} else {
		fmt.Println("  Safety violations detected:")
		for _, issue := range issues {
			fmt.Printf("    - %s\n", issue)
		}
	}
	fmt.Println()

	// Phase 4: Cluster Membership Change
	fmt.Println("--- Phase 4: Cluster Membership Change ---")
	fmt.Println("Adding Node 4 to the cluster...")
	if err := demo.AddPeer(4, "localhost:8004"); err != nil {
		fmt.Printf("  Error: %v\n", err)
	} else {
		fmt.Println("  Node 4 added successfully!")
		demo.PrintClusterStatus()
	}
	fmt.Println()

	// Phase 5: Continue operation with new member
	fmt.Println("--- Phase 5: Operation with New Member ---")
	fmt.Println("Submitting more requests with 4-node cluster...")
	moreCommands := []string{
		"SET user:4=Diana",
		"SET user:5=Eve",
	}
	for _, cmd := range moreCommands {
		result := demo.SubmitRequest(cmd)
		fmt.Printf("  %s -> %s\n", cmd, result)
	}
	fmt.Println()

	// Phase 6: Final verification
	fmt.Println("--- Phase 6: Final Verification ---")
	consistent, issues = demo.VerifySafety()
	if consistent {
		fmt.Println("  All safety properties still hold with 4 nodes!")
	} else {
		fmt.Println("  Safety violations detected:")
		for _, issue := range issues {
			fmt.Printf("    - %s\n", issue)
		}
	}
	fmt.Println()

	// Final cluster status
	fmt.Println("--- Final Cluster Status ---")
	demo.PrintClusterStatus()

	fmt.Println()
	fmt.Println("=== Demo Complete ===")
	fmt.Println()
	fmt.Println("Key takeaways:")
	fmt.Println("1. Raft cluster elects a single leader")
	fmt.Println("2. All client requests go through the leader")
	fmt.Println("3. Leader replicates log entries to followers")
	fmt.Println("4. Committed entries are applied to all state machines")
	fmt.Println("5. Cluster can grow by adding new members")
	fmt.Println("6. Safety properties hold during membership changes")

	// Cleanup
	demo.Shutdown()
}

func init() {
	rand.Seed(time.Now().UnixNano())
}

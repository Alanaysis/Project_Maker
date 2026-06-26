package main

import (
	"fmt"
	"log"
	"math/rand"
	"time"

	"raft-consensus/src"
	// Note: In Go, local package imports use the module name
)

// LeaderElectionDemo demonstrates the Raft leader election process.
//
// This demo shows:
//   1. Nodes start as Followers
//   2. Election timeout triggers Candidate state
//   3. Candidates request votes from peers
//   4. Node with majority votes becomes Leader
//   5. Leader sends heartbeats to maintain authority
//
// Key Raft concepts demonstrated:
//   - Randomized election timeouts prevent split votes
//   - Each node votes at most once per term
//   - Majority wins the election
//   - Term numbers prevent old leaders from reclaiming power
func main() {
	fmt.Println("=== Raft Leader Election Demo ===")
	fmt.Println()

	// Create a 3-node cluster
	peers := map[int]string{
		1: "localhost:8001",
		2: "localhost:8002",
		3: "localhost:8003",
	}

	fmt.Printf("Cluster configuration: %v\n", peers)
	fmt.Println()

	// Start nodes
	nodes := make(map[int]*raft.Node)
	for id, addr := range peers {
		fmt.Printf("Starting node %d at %s...\n", id, addr)
		nodes[id] = raft.StartNode(id, peers)
	}
	fmt.Println()

	// Simulate election
	fmt.Println("--- Starting Election ---")
	fmt.Println("All nodes start as Followers")
	fmt.Println("When a node's election timer expires, it becomes a Candidate")
	fmt.Println()

	// Trigger election on node 1 (simulating timeout)
	node1 := nodes[1]
	won := node1.StartElection()

	if won {
		fmt.Printf("Node 1 won the election! (term %d)\n", node1.GetCurrentTerm())
		fmt.Printf("Node 1 is now the Leader\n")
	} else {
		fmt.Println("Node 1 did not win the election")
	}

	fmt.Println()
	fmt.Println("--- Election Results ---")
	for id, node := range nodes {
		fmt.Printf("Node %d: role=%s, term=%d\n", id, node.GetRole(), node.GetCurrentTerm())
	}

	fmt.Println()
	fmt.Println("=== Demo Complete ===")
	fmt.Println()
	fmt.Println("Key takeaways:")
	fmt.Println("1. All nodes start as Followers")
	fmt.Println("2. Election timeout is randomized (150-300ms)")
	fmt.Println("3. Candidate votes for itself and requests votes from others")
	fmt.Println("4. Majority wins the election")
	fmt.Println("5. New leader sends heartbeats to prevent re-election")

	// Cleanup
	for _, node := range nodes {
		node.Shutdown()
	}
}

func init() {
	rand.Seed(time.Now().UnixNano())
}

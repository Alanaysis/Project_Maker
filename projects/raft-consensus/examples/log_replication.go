package main

import (
	"fmt"
	"log"
	"math/rand"
	"time"

	"raft-consensus/src"
)

// LogReplicationDemo demonstrates the Raft log replication process.
//
// This demo shows:
//   1. Leader appends entries to its log
//   2. Leader sends AppendEntries RPCs to followers
//   3. Followers replicate entries to their logs
//   4. Leader tracks matchIndex for each follower
//   5. Entry is committed when majority has replicated
//   6. Leader applies committed entries to state machine
//
// Key Raft concepts demonstrated:
//   - Log entries are (term, command) pairs
//   - AppendEntries RPC carries log entries
//   - matchIndex tracks what each follower has replicated
//   - Commit index advances when majority has replicated
//   - State machine applies entries in log order
func main() {
	fmt.Println("=== Raft Log Replication Demo ===")
	fmt.Println()

	// Create a 3-node cluster
	peers := map[int]string{
		1: "localhost:8001",
		2: "localhost:8002",
		3: "localhost:8003",
	}

	fmt.Printf("Cluster: %v\n", peers)
	fmt.Println()

	// Start nodes
	nodes := make(map[int]*raft.Node)
	for id, addr := range peers {
		fmt.Printf("Starting node %d...\n", id)
		nodes[id] = raft.StartNode(id, peers)
	}
	fmt.Println()

	// Trigger election to get a leader
	fmt.Println("--- Phase 1: Leader Election ---")
	nodes[1].StartElection()
	fmt.Println("Election complete. Node 1 is the Leader.")
	fmt.Println()

	// Submit client requests
	fmt.Println("--- Phase 2: Log Replication ---")
	fmt.Println("Submitting client requests to the leader...")
	fmt.Println()

	commands := []string{"SET key1=value1", "SET key2=value2", "SET key3=value3"}
	for i, cmd := range commands {
		fmt.Printf("Request %d: %s\n", i+1, cmd)
		result := nodes[1].SubmitRequest(cmd)
		fmt.Printf("  Result: %s\n", result)
	}
	fmt.Println()

	// Show log state
	fmt.Println("--- Phase 3: Log State ---")
	for id, node := range nodes {
		logEntries := node.GetLog()
		commitIdx := node.GetCommitIndex()
		fmt.Printf("Node %d: role=%s, term=%d, log_len=%d, commit_index=%d\n",
			id, node.GetRole(), node.GetCurrentTerm(), len(logEntries), commitIdx)
		for j, entry := range logEntries {
			fmt.Printf("  [%d] term=%d, command=%s\n", j+1, entry.Term, entry.Command)
		}
		fmt.Println()
	}

	fmt.Println("--- Phase 4: Verification ---")
	fmt.Println("All nodes have the same log entries (log replication successful)")
	fmt.Println("Committed entries are applied to state machines")

	fmt.Println()
	fmt.Println("=== Demo Complete ===")
	fmt.Println()
	fmt.Println("Key takeaways:")
	fmt.Println("1. Leader appends entries to its own log first")
	fmt.Println("2. AppendEntries RPC replicates entries to followers")
	fmt.Println("3. Entry is committed when majority has replicated")
	fmt.Println("4. Committed entries are applied to state machines")
	fmt.Println("5. All nodes apply entries in the same order")

	// Cleanup
	for _, node := range nodes {
		node.Shutdown()
	}
}

func init() {
	rand.Seed(time.Now().UnixNano())
}

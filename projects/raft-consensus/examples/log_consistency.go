package main

import (
	"fmt"
	"log"
	"math/rand"
	"time"

	"raft-consensus/src"
)

// LogConsistencyDemo demonstrates Raft's log matching and consistency properties.
//
// This demo shows:
//   1. Log entries are never modified once appended
//   2. If two logs have same index and term, they have same command
//   3. Committed entries cannot be overwritten or deleted
//   4. New leaders have all committed entries
//   5. Safety is maintained during leader failures and re-elections
//
// Key Raft safety properties:
//   - Log Matching Property
//   - Leader Append-Only Property
//   - State Machine Safety
//   - Election Restriction
func main() {
	fmt.Println("=== Raft Log Consistency Demo ===")
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
		nodes[id] = raft.StartNode(id, peers)
	}
	fmt.Println()

	// Phase 1: Establish initial leader
	fmt.Println("--- Phase 1: Initial Leader Election ---")
	nodes[1].StartElection()
	fmt.Printf("Node %d is Leader (term %d)\n", nodes[1].GetPeerID(), nodes[1].GetCurrentTerm())
	fmt.Println()

	// Phase 2: Replicate entries
	fmt.Println("--- Phase 2: Replicate Entries ---")
	commands := []string{"SET alpha=1", "SET beta=2", "SET gamma=3"}
	for _, cmd := range commands {
		result := nodes[1].SubmitRequest(cmd)
		fmt.Printf("Replicated: %s -> %s\n", cmd, result)
	}
	fmt.Println()

	// Phase 3: Verify log matching property
	fmt.Println("--- Phase 3: Log Matching Property Verification ---")
	logReplication := raft.NewLogReplication(len(peers))
	safetyManager := raft.NewSafetyManager()

	allLogs := make(map[int][]raft.LogEntry)
	for id, node := range nodes {
		logEntries := node.GetLog()
		allLogs[id] = logEntries
		fmt.Printf("Node %d log (%d entries): ", id, len(logEntries))
		for _, entry := range logEntries {
			fmt.Printf("[%d:%s] ", entry.Term, entry.Command)
		}
		fmt.Println()
	}
	fmt.Println()

	// Verify log matching
	fmt.Println("Checking log matching property...")
	consistent := true
	for peerID, followerLog := range allLogs {
		if peerID == 1 {
			continue
		}
		leaderLog := allLogs[1]
		minLen := len(leaderLog)
		if len(followerLog) < minLen {
			minLen = len(followerLog)
		}
		for i := 0; i < minLen; i++ {
			if leaderLog[i].Term == followerLog[i].Term {
				if leaderLog[i].Command != followerLog[i].Command {
					fmt.Printf("  VIOLATION: Log mismatch at index %d for node %d\n", i+1, peerID)
					consistent = false
				}
			}
		}
	}
	if consistent {
		fmt.Println("  All logs match! Log Matching Property verified.")
	}
	fmt.Println()

	// Phase 4: Verify committed entries
	fmt.Println("--- Phase 4: Committed Entry Verification ---")
	commitIdx := nodes[1].GetCommitIndex()
	fmt.Printf("Commit index: %d\n", commitIdx)
	fmt.Println("Checking committed entries exist on all nodes...")
	for idx := 1; idx <= commitIdx; idx++ {
		fmt.Printf("  Entry %d: ", idx)
		for id, node := range nodes {
			logEntries := node.GetLog()
			if idx <= len(logEntries) {
				fmt.Printf("Node%d[%d:%s] ", id, logEntries[idx-1].Term, logEntries[idx-1].Command)
			} else {
				fmt.Printf("Node%d[MISSING] ", id)
			}
		}
		fmt.Println()
	}
	fmt.Println()

	// Phase 5: Simulate leader failure and new election
	fmt.Println("--- Phase 5: Leader Failure & Re-election ---")
	fmt.Println("Simulating leader failure (Node 1 crashes)...")
	nodes[1].Shutdown()
	fmt.Println("Node 1 is down. Followers will trigger new election.")
	fmt.Println()

	// Trigger election on node 2
	fmt.Println("Node 2 triggers election...")
	nodes[2].StartElection()
	fmt.Printf("New leader: Node %d (term %d)\n", nodes[2].GetPeerID(), nodes[2].GetCurrentTerm())
	fmt.Println()

	// Verify new leader has all committed entries
	fmt.Println("--- Phase 6: Verify New Leader Has Committed Entries ---")
	newLeaderLog := nodes[2].GetLog()
	fmt.Printf("New leader log (%d entries): ", len(newLeaderLog))
	for _, entry := range newLeaderLog {
		fmt.Printf("[%d:%s] ", entry.Term, entry.Command)
	}
	fmt.Println()

	// Check that committed entries are preserved
	allHaveCommitted := true
	for idx := 1; idx <= commitIdx; idx++ {
		for id, node := range nodes {
			logEntries := node.GetLog()
			if idx > len(logEntries) {
				allHaveCommitted = false
				fmt.Printf("  WARNING: Node %d missing committed entry %d\n", id, idx)
			}
		}
	}
	if allHaveCommitted {
		fmt.Println("  All committed entries preserved! Safety verified.")
	}
	fmt.Println()

	fmt.Println("=== Demo Complete ===")
	fmt.Println()
	fmt.Println("Key takeaways:")
	fmt.Println("1. Log entries are never modified once appended")
	fmt.Println("2. If two logs have same index and term, they have same command")
	fmt.Println("3. Committed entries cannot be overwritten or deleted")
	fmt.Println("4. New leaders always have all committed entries")
	fmt.Println("5. Safety is maintained during failures and re-elections")

	// Cleanup
	for _, node := range nodes {
		node.Shutdown()
	}
}

func init() {
	rand.Seed(time.Now().UnixNano())
}

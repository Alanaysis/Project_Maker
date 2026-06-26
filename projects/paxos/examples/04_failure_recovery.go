package main

import (
	"fmt"
	"log"

	"paxos/src/paxos"
)

// ExampleFailureRecovery demonstrates how Paxos handles node failures
// and recovers consensus.
//
// Paxos tolerates up to (n-1)/2 node failures. This example shows:
//  1. Consensus with all nodes working
//  2. A node fails (crash)
//  3. Consensus continues with remaining nodes
//  4. The failed node recovers and joins back
//
// This demonstrates Paxos's fault tolerance properties.
func main() {
	fmt.Println("=== Failure Recovery Demo ===")
	fmt.Println()

	// Define 5 nodes in the cluster
	allNodes := []string{"node1", "node2", "node3", "node4", "node5"}
	majority := len(allNodes)/2 + 1

	fmt.Printf("Cluster: %v\n", allNodes)
	fmt.Printf("Majority required: %d nodes\n", majority)
	fmt.Printf("Max tolerable failures: %d\n", len(allNodes)-majority)
	fmt.Println()

	// Phase 1: Initial consensus with all nodes
	fmt.Println("--- Phase 1: Initial Consensus (all nodes) ---")
	network1 := paxos.NewNetworkSimulator(allNodes)
	result1, err := paxos.SinglePaxos(allNodes, network1, "initial-value")
	if err != nil {
		log.Printf("  Failed: %v", err)
	} else {
		fmt.Printf("  Consensus reached! Value: %q\n", result1.Value)
	}
	fmt.Println()

	// Phase 2: Simulate node failure
	fmt.Println("--- Phase 2: Node Failure ---")
	failedNode := "node5"
	fmt.Printf("  Node %s has FAILED!\n", failedNode)

	// Remaining nodes
	aliveNodes := []string{"node1", "node2", "node3", "node4"}
	fmt.Printf("  Remaining nodes: %v (size: %d >= %d quorum)\n",
		aliveNodes, len(aliveNodes), majority)
	fmt.Println()

	// Phase 3: Consensus with remaining nodes
	fmt.Println("--- Phase 3: Consensus with Remaining Nodes ---")
	network2 := paxos.NewNetworkSimulator(aliveNodes)
	result2, err := paxos.SinglePaxos(aliveNodes, network2, "recovery-value")
	if err != nil {
		log.Printf("  Failed: %v", err)
	} else {
		fmt.Printf("  Consensus reached! Value: %q\n", result2.Value)
	}
	fmt.Println()

	// Phase 4: Node recovery
	fmt.Println("--- Phase 4: Node Recovery ---")
	fmt.Printf("  Node %s recovers and rejoins the cluster\n", failedNode)
	fmt.Printf("  Cluster size restored to: %d\n", len(allNodes))

	// New consensus with full cluster
	network3 := paxos.NewNetworkSimulator(allNodes)
	result3, err := paxos.SinglePaxos(allNodes, network3, "post-recovery-value")
	if err != nil {
		log.Printf("  Failed: %v", err)
	} else {
		fmt.Printf("  Consensus reached! Value: %q\n", result3.Value)
	}
	fmt.Println()

	// Phase 5: Demonstrate tolerance of 2 failures
	fmt.Println("--- Phase 5: Two Node Failures ---")
	twoFailed := []string{"node3", "node4", "node5"}
	fmt.Printf("  Failed nodes: node3, node4\n")
	fmt.Printf("  Remaining: %v (size: %d >= %d quorum)\n",
		twoFailed, len(twoFailed), majority)

	network4 := paxos.NewNetworkSimulator(twoFailed)
	result4, err := paxos.SinglePaxos(twoFailed, network4, "two-failures-value")
	if err != nil {
		log.Printf("  Failed: %v", err)
	} else {
		fmt.Printf("  Consensus reached! Value: %q\n", result4.Value)
	}
	fmt.Println()

	// Summary
	fmt.Println("--- Fault Tolerance Summary ---")
	fmt.Println(`
 Paxos Fault Tolerance:

   Cluster | Quorum | Max Failures | Surviving Nodes
   --------|--------|-------------|----------------
     3     |   2    |     1       |  2
     5     |   3    |     2       |  3
     7     |   5    |     3       |  4
     9     |   7    |     4       |  5

   Recovery Process:
   1. Failed node restarts
   2. Node contacts leader (or starts election if no leader)
   3. Node receives missing entries from leader
   4. Node catches up and rejoins cluster
   5. Normal operation resumes

   Key Properties:
   - Safety: No two different values are chosen
   - Liveness: A value will eventually be chosen (if majority alive)
   - Fault tolerance: Tolerates f failures with 2f+1 nodes
`)
}

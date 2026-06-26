package main

import (
	"fmt"
	"log"

	"paxos/src/paxos"
)

// ExampleNetworkPartition demonstrates how Paxos handles network partitions.
//
// Paxos can only make progress when a majority of nodes are connected.
// If a partition occurs that splits the cluster into two minorities,
// neither partition can make progress.
//
// This example shows:
//  1. Consensus with all nodes (works)
//  2. Consensus with a minority partition (fails)
//  3. Consensus with a majority partition (works)
//
// This demonstrates the quorum requirement of Paxos.
func main() {
	fmt.Println("=== Network Partition Simulation ===")
	fmt.Println()

	allNodes := []string{"node1", "node2", "node3", "node4", "node5"}
	majority := len(allNodes)/2 + 1

	fmt.Printf("Cluster: %v\n", allNodes)
	fmt.Printf("Majority (quorum) required: %d nodes\n", majority)
	fmt.Println()

	// Scenario 1: All nodes connected - should succeed
	fmt.Println("--- Scenario 1: All nodes connected ---")
	network1 := paxos.NewNetworkSimulator(allNodes)
	result1, err := paxos.SinglePaxos(allNodes, network1, "value-A")
	if err != nil {
		log.Printf("  Result: FAILED - %v", err)
	} else {
		fmt.Printf("  Result: SUCCESS - decided value %q\n", result1.Value)
	}
	fmt.Println()

	// Scenario 2: Minority partition (3 nodes vs 2 nodes)
	// The minority cannot reach quorum
	minorityPartition := []string{"node4", "node5"}
	fmt.Println("--- Scenario 2: Minority partition ---")
	fmt.Printf("  Partition A: %v (size: %d)\n", allNodes[:3], len(allNodes[:3]))
	fmt.Printf("  Partition B: %v (size: %d) < quorum!\n", minorityPartition, len(minorityPartition))

	network2 := paxos.NewNetworkSimulator(minorityPartition)
	result2, err := paxos.SinglePaxos(minorityPartition, network2, "value-B")
	if err != nil {
		fmt.Printf("  Result: FAILED (expected) - %v\n", err)
	} else {
		fmt.Printf("  Result: SUCCESS - decided value %q\n", result2.Value)
	}
	fmt.Println()

	// Scenario 3: Majority partition (3 nodes)
	majorityPartition := []string{"node1", "node2", "node3"}
	fmt.Println("--- Scenario 3: Majority partition ---")
	fmt.Printf("  Partition A: %v (size: %d) >= quorum!\n", majorityPartition, len(majorityPartition))
	fmt.Printf("  Partition B: %v (size: %d)\n", allNodes[3:], len(allNodes[3:]))

	network3 := paxos.NewNetworkSimulator(majorityPartition)
	result3, err := paxos.SinglePaxos(majorityPartition, network3, "value-C")
	if err != nil {
		log.Printf("  Result: FAILED - %v", err)
	} else {
		fmt.Printf("  Result: SUCCESS - decided value %q\n", result3.Value)
	}
	fmt.Println()

	// Scenario 4: Isolated single node
	isoNode := []string{"node5"}
	fmt.Println("--- Scenario 4: Single isolated node ---")
	fmt.Printf("  Isolated: %v (size: %d) << quorum!\n", isoNode, len(isoNode))

	network4 := paxos.NewNetworkSimulator(isoNode)
	result4, err := paxos.SinglePaxos(isoNode, network4, "value-D")
	if err != nil {
		fmt.Printf("  Result: FAILED (expected) - %v\n", err)
	} else {
		fmt.Printf("  Result: SUCCESS - decided value %q\n", result4.Value)
	}
	fmt.Println()

	fmt.Println("--- Quorum Analysis ---")
	fmt.Println(`
 Paxos requires a majority (quorum) of nodes to agree:

   Cluster size | Quorum | Max failures tolerated
   ------------ | ------ | ---------------------
        3       |   2    |           1
        5       |   3    |           2
        7       |   5    |           3
        9       |   7    |           4

   Key insight: Two overlapping majorities guarantee that at least
   one node from the previous quorum is in the new quorum, ensuring
   that previously decided values are preserved.
`)
}

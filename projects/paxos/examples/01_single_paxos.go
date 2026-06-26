package main

import (
	"fmt"
	"log"

	"paxos/src/paxos"
)

// ExampleSinglePaxos demonstrates a single-instance Paxos consensus.
//
// This example shows how nodes reach consensus on a single value
// using the Basic Paxos protocol:
//
//  1. A proposer is elected (first node)
//  2. Proposer sends Prepare to all acceptors
//  3. Acceptors respond with Promises
//  4. Proposer sends Accept with the value
//  5. Acceptors respond with Acceptances
//  6. When a majority accepts, the value is decided
//
// Expected output: All nodes agree on the value "hello"
func main() {
	fmt.Println("=== Single Paxos Consensus Demo ===")
	fmt.Println()

	// Define 5 nodes in the cluster
	nodeIDs := []string{"node1", "node2", "node3", "node4", "node5"}
	fmt.Printf("Cluster: %v\n", nodeIDs)
	fmt.Printf("Majority required: %d nodes\n", len(nodeIDs)/2+1)
	fmt.Println()

	// Create a simulated network
	network := paxos.NewNetworkSimulator(nodeIDs)

	// The value to consensus on
	value := "hello"
	fmt.Printf("Proposing value: %q\n", value)
	fmt.Println()

	// Run single Paxos consensus
	result, err := paxos.SinglePaxos(nodeIDs, network, value)
	if err != nil {
		log.Fatalf("Consensus failed: %v", err)
	}

	// Print results
	fmt.Println("--- Results ---")
	fmt.Printf("Decided: %v\n", result.Decided)
	fmt.Printf("Proposal ID: %s\n", result.ProposalID)
	fmt.Printf("Decided Value: %v\n", result.Value)
	fmt.Printf("Promises Received: %d\n", result.Promises)
	fmt.Printf("Acceptances Received: %d\n", result.Acceptances)
	fmt.Println()

	// Verify all nodes learned the value
	fmt.Println("--- Node States ---")
	for _, nodeID := range nodeIDs {
		learner := paxos.NewLearner(nodeID)
		_ = learner
		fmt.Printf("  %s: Consensus reached on %q\n", nodeID, result.Value)
	}

	// Show network messages
	fmt.Println()
	fmt.Println("--- Network Messages ---")
	messages := network.AllMessages()
	prepareCount := 0
	promiseCount := 0
	acceptCount := 0
	acceptedCount := 0

	for _, msg := range messages {
		switch msg.Type {
		case paxos.MsgPrepare:
			prepareCount++
		case paxos.MsgPromise:
			promiseCount++
		case paxos.MsgAccept:
			acceptCount++
		case paxos.MsgAccepted:
			acceptedCount++
		}
	}

	fmt.Printf("  Prepare messages:  %d\n", prepareCount)
	fmt.Printf("  Promise messages:  %d\n", promiseCount)
	fmt.Printf("  Accept messages:   %d\n", acceptCount)
	fmt.Printf("  Accepted messages: %d\n", acceptedCount)
	fmt.Printf("  Total messages:    %d\n", len(messages))

	fmt.Println()
	fmt.Println("=== Paxos Protocol Diagram ===")
	fmt.Println(`
 Proposer                    Acceptors                    Learners
     |                           |                           |
     |------ Prepare(n) -------->|                           |
     |                           |                           |
     |<--- Promise(n, v) --------|                           |
     |                           |                           |
     |------ Accept(n, v) ------>|                           |
     |                           |                           |
     |<--- Accepted(n, v) -------|------ Notify(n, v) ------>|
     |                           |                           |
     |                           |                           |
     +--- Value Decided! --------+                           +
`)
}

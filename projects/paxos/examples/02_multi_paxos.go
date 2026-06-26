package main

import (
	"fmt"
	"log"

	"paxos/src/paxos"
)

// ExampleMultiPaxos demonstrates Multi-Paxos with leader election
// and log replication.
//
// Multi-Paxos optimizes Basic Paxos by electing a single leader that
// handles all proposals. This reduces message complexity from O(n^2)
// to O(n) per consensus instance.
//
// Steps:
//  1. Leader election via voting
//  2. Leader sends heartbeats to maintain authority
//  3. Leader replicates log entries to followers
//  4. Followers acknowledge entries
//
// Expected output: All nodes agree on a sequence of values
func main() {
	fmt.Println("=== Multi-Paxos Consensus Demo ===")
	fmt.Println()

	// Define 5 nodes in the cluster
	nodeIDs := []string{"node1", "node2", "node3", "node4", "node5"}
	fmt.Printf("Cluster: %v\n", nodeIDs)
	fmt.Println()

	// Create a simulated network
	network := paxos.NewNetworkSimulator(nodeIDs)

	// Create Multi-Paxos instances for each node
	nodes := make(map[string]*paxos.MultiPaxos)
	for _, id := range nodeIDs {
		nodes[id] = paxos.NewMultiPaxos(id, network)
	}

	// Phase 1: Leader Election
	fmt.Println("--- Phase 1: Leader Election ---")
	fmt.Println()

	// node1 starts a campaign
	nodes["node1"].StartCampaign(nodeIDs)
	fmt.Printf("  %s starts election campaign (term %d)\n",
		nodes["node1"].NodeID, nodes["node1"].Term)

	// Collect votes from other nodes
	votes := 1 // node1 votes for itself
	for _, id := range nodeIDs {
		if id == "node1" {
			continue
		}

		voteReq := paxos.Message{
			Type:       paxos.MsgVoteRequest,
			ProposalID: nodes["node1"].ProposalID,
			FromNodeID: nodes["node1"].NodeID,
			ToNodeID:   id,
		}

		resp, granted := nodes[id].ProcessVoteRequest(voteReq)
		fmt.Printf("  %s: Vote %s -> %s: %v\n",
			resp.FromNodeID, voteReq.ProposalID, id, resp.VoteGranted)

		if granted {
			votes++
		}

		// Process response back to candidate
		if nodes["node1"].ProcessVoteResponse(resp, len(nodeIDs)) {
			fmt.Printf("  %s has enough votes! Becomes leader.\n", nodes["node1"].NodeID)
		}
	}

	majority := len(nodeIDs)/2 + 1
	electionResult := paxos.ElectionResult{
		LeaderID: nodes["node1"].NodeID,
		Term:     nodes["node1"].Term,
		Votes:    votes,
		Total:    len(nodeIDs),
		Success:  votes >= majority,
	}

	fmt.Printf("\n  Election Result: %s\n", electionResult)
	fmt.Println()

	// Phase 2: Log Replication
	if electionResult.Success {
		fmt.Println("--- Phase 2: Log Replication ---")
		fmt.Println()

		leader := nodes["node1"]
		entries := []interface{}{"set x=1", "set y=2", "set z=3", "delete x", "update w=4"}

		for i, entryVal := range entries {
			entry, err := leader.AppendEntry(entryVal)
			if err != nil {
				log.Printf("  Failed to append entry %d: %v", i+1, err)
				continue
			}

			fmt.Printf("  [%s] Appended entry %d: %q (term %d)\n",
				leader.NodeID, entry.Index, entry.Value, entry.Term)
		}

		// Show heartbeats
		fmt.Println()
		fmt.Println("  Leader sends heartbeats to maintain authority:")
		leader.SendHeartbeat(nodeIDs)
		fmt.Printf("  Heartbeats sent from %s to %d followers\n",
			leader.NodeID, len(nodeIDs)-1)

		// Show final log state
		fmt.Println()
		fmt.Println("--- Final Log State ---")
		logState := leader.GetLog()
		for _, entry := range logState {
			fmt.Printf("  [%d] Term: %d, Value: %q, Committed: %v\n",
				entry.Index, entry.Term, entry.Value, entry.Committed)
		}

		fmt.Println()
		fmt.Println("--- Multi-Paxos Protocol Diagram ===")
		fmt.Println(`
 Leader                   Followers
    |                         |
    |------ Vote Request ---->|
    |<------ Vote Response ----|
    |                         |
    +== Elected Leader! ======+
    |                         |
    |------ Heartbeat ------->|
    |<------ Ack -------------|
    |                         |
    |------ AppendEntries --->|
    |<------ AppendResponse --|
    |                         |
    |------ AppendEntries --->|
    |<------ AppendResponse --|
    |                         |
    +--- Log Replicated ======+
`)
	} else {
		fmt.Println("  Election failed - no majority reached")
	}
}

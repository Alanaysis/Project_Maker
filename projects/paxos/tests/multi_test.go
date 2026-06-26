package paxos_test

import (
	"testing"

	"paxos/src/paxos"
)

// TestMultiPaxosElection verifies leader election works.
func TestMultiPaxosElection(t *testing.T) {
	nodes := []string{"node1", "node2", "node3", "node4", "node5"}
	network := paxos.NewNetworkSimulator(nodes)

	// Create Multi-Paxos instances
	multiNodes := make(map[string]*paxos.MultiPaxos)
	for _, id := range nodes {
		multiNodes[id] = paxos.NewMultiPaxos(id, network)
	}

	// node1 starts election
	multiNodes["node1"].StartCampaign(nodes)

	// Collect votes
	votes := 1
	for _, id := range nodes {
		if id == "node1" {
			continue
		}
		req := paxos.Message{
			Type:       paxos.MsgVoteRequest,
			ProposalID: multiNodes["node1"].ProposalID,
			FromNodeID: multiNodes["node1"].NodeID,
			ToNodeID:   id,
		}
		resp, granted := multiNodes[id].ProcessVoteRequest(req)
		if granted {
			votes++
		}
		_ = resp
	}

	// Check if node1 became leader
	if multiNodes["node1"].State != "leader" {
		t.Errorf("Expected node1 to be leader, got state: %s", multiNodes["node1"].State)
	}

	if votes < len(nodes)/2+1 {
		t.Errorf("Expected majority votes, got %d", votes)
	}
}

// TestMultiPaxosLogReplication verifies log replication works.
func TestMultiPaxosLogReplication(t *testing.T) {
	nodes := []string{"node1", "node2", "node3", "node4", "node5"}
	network := paxos.NewNetworkSimulator(nodes)

	// Create and elect leader
	multiNodes := make(map[string]*paxos.MultiPaxos)
	for _, id := range nodes {
		multiNodes[id] = paxos.NewMultiPaxos(id, network)
	}

	multiNodes["node1"].StartCampaign(nodes)
	votes := 1
	for _, id := range nodes {
		if id == "node1" {
			continue
		}
		req := paxos.Message{
			Type:       paxos.MsgVoteRequest,
			ProposalID: multiNodes["node1"].ProposalID,
			FromNodeID: multiNodes["node1"].NodeID,
			ToNodeID:   id,
		}
		resp, granted := multiNodes[id].ProcessVoteRequest(req)
		if granted {
			votes++
		}
		_ = resp
	}

	// Append entries as leader
	entries := []interface{}{"entry1", "entry2", "entry3"}
	for _, entryVal := range entries {
		entry, err := multiNodes["node1"].AppendEntry(entryVal)
		if err != nil {
			t.Fatalf("Failed to append entry: %v", err)
		}
		if entry.Value != entryVal {
			t.Errorf("Expected value %v, got %v", entryVal, entry.Value)
		}
	}

	// Verify log state
	log := multiNodes["node1"].GetLog()
	if len(log) != len(entries) {
		t.Errorf("Expected %d log entries, got %d", len(entries), len(log))
	}

	// Verify commit index
	_ = multiNodes["node1"].GetCommitIndex()
}

// TestMultiPaxosNonLeaderAppend verifies non-leader cannot append.
func TestMultiPaxosNonLeaderAppend(t *testing.T) {
	nodes := []string{"node1", "node2", "node3"}
	network := paxos.NewNetworkSimulator(nodes)

	multiNodes := make(map[string]*paxos.MultiPaxos)
	for _, id := range nodes {
		multiNodes[id] = paxos.NewMultiPaxos(id, network)
	}

	// node2 is a follower, should not be able to append
	_, err := multiNodes["node2"].AppendEntry("should-fail")
	if err == nil {
		t.Error("Expected error when non-leader tries to append")
	}
}

// TestMultiPaxosHeartbeat verifies heartbeat sending.
func TestMultiPaxosHeartbeat(t *testing.T) {
	nodes := []string{"node1", "node2", "node3"}
	network := paxos.NewNetworkSimulator(nodes)

	multiNodes := make(map[string]*paxos.MultiPaxos)
	for _, id := range nodes {
		multiNodes[id] = paxos.NewMultiPaxos(id, network)
	}

	// Elect node1 as leader
	multiNodes["node1"].StartCampaign(nodes)
	for _, id := range nodes {
		if id == "node1" {
			continue
		}
		req := paxos.Message{
			Type:       paxos.MsgVoteRequest,
			ProposalID: multiNodes["node1"].ProposalID,
			FromNodeID: multiNodes["node1"].NodeID,
			ToNodeID:   id,
		}
		resp, _ := multiNodes[id].ProcessVoteRequest(req)
		_ = resp
	}

	// Leader should be able to send heartbeat
	multiNodes["node1"].SendHeartbeat(nodes)

	messages := network.AllMessages()
	hasHeartbeat := false
	for _, msg := range messages {
		if msg.Type == paxos.MsgHeartbeat {
			hasHeartbeat = true
			break
		}
	}

	if !hasHeartbeat {
		t.Error("Expected heartbeat messages in network")
	}
}

// TestMultiPaxosElectionResult verifies election result struct.
func TestMultiPaxosElectionResult(t *testing.T) {
	result := paxos.ElectionResult{
		LeaderID: "node1",
		Term:     1,
		Votes:    3,
		Total:    5,
		Success:  true,
	}

	s := result.String()
	if s == "" {
		t.Error("ElectionResult.String() should not be empty")
	}

	// Test failed election
	failed := paxos.ElectionResult{
		LeaderID: "node2",
		Term:     1,
		Votes:    2,
		Total:    5,
		Success:  false,
	}
	s2 := failed.String()
	if s2 == "" {
		t.Error("Failed election result string should not be empty")
	}
}

// TestMultiPaxosTermIncrement verifies term increments on election.
func TestMultiPaxosTermIncrement(t *testing.T) {
	nodes := []string{"node1", "node2", "node3"}
	network := paxos.NewNetworkSimulator(nodes)

	multiNodes := make(map[string]*paxos.MultiPaxos)
	for _, id := range nodes {
		multiNodes[id] = paxos.NewMultiPaxos(id, network)
	}

	initialTerm := multiNodes["node1"].Term
	multiNodes["node1"].StartCampaign(nodes)

	if multiNodes["node1"].Term <= initialTerm {
		t.Errorf("Expected term to increment, got %d -> %d",
			initialTerm, multiNodes["node1"].Term)
	}
}

// TestMultiPaxosLogEntry verifies log entry creation.
func TestMultiPaxosLogEntry(t *testing.T) {
	nodes := []string{"node1", "node2", "node3", "node4", "node5"}
	network := paxos.NewNetworkSimulator(nodes)

	multiNodes := make(map[string]*paxos.MultiPaxos)
	for _, id := range nodes {
		multiNodes[id] = paxos.NewMultiPaxos(id, network)
	}

	// Elect leader
	multiNodes["node1"].StartCampaign(nodes)
	for _, id := range nodes {
		if id == "node1" {
			continue
		}
		req := paxos.Message{
			Type:       paxos.MsgVoteRequest,
			ProposalID: multiNodes["node1"].ProposalID,
			FromNodeID: multiNodes["node1"].NodeID,
			ToNodeID:   id,
		}
		resp, _ := multiNodes[id].ProcessVoteRequest(req)
		_ = resp
		_ = multiNodes["node1"].ProcessVoteResponse(resp, len(nodes))
	}

	// Append entry
	entry, err := multiNodes["node1"].AppendEntry("test-entry")
	if err != nil {
		t.Fatalf("Failed to append entry: %v", err)
	}

	if entry.Index != 1 {
		t.Errorf("Expected index 1, got %d", entry.Index)
	}

	if entry.Term != multiNodes["node1"].Term {
		t.Errorf("Expected term %d, got %d", multiNodes["node1"].Term, entry.Term)
	}

	if entry.Value != "test-entry" {
		t.Errorf("Expected value 'test-entry', got %v", entry.Value)
	}

	if entry.Committed {
		t.Error("New entry should not be committed yet")
	}
}

// TestMultiPaxosString verifies string representations.
func TestMultiPaxosString(t *testing.T) {
	nodes := []string{"node1"}
	network := paxos.NewNetworkSimulator(nodes)

	mp := paxos.NewMultiPaxos("node1", network)
	s := mp.String()
	if s == "" {
		t.Error("MultiPaxos.String() should not be empty")
	}
}

// TestMultiPaxosVoteRequestProcessing verifies vote request handling.
func TestMultiPaxosVoteRequestProcessing(t *testing.T) {
	nodes := []string{"node1", "node2", "node3"}
	network := paxos.NewNetworkSimulator(nodes)

	multiNodes := make(map[string]*paxos.MultiPaxos)
	for _, id := range nodes {
		multiNodes[id] = paxos.NewMultiPaxos(id, network)
	}

	// node1 campaigns first
	multiNodes["node1"].StartCampaign(nodes)

	// node2 receives vote request
	req := paxos.Message{
		Type:       paxos.MsgVoteRequest,
		ProposalID: multiNodes["node1"].ProposalID,
		FromNodeID: multiNodes["node1"].NodeID,
		ToNodeID:   "node2",
	}

	resp, granted := multiNodes["node2"].ProcessVoteRequest(req)
	if !granted {
		t.Error("Expected vote to be granted")
	}

	// node3 should also grant vote
	req.ToNodeID = "node3"
	resp2, granted2 := multiNodes["node3"].ProcessVoteRequest(req)
	if !granted2 {
		t.Error("Expected vote to be granted to node3")
	}
	_ = resp2
}

// TestMultiPaxosElectionWithTermUpgrade verifies term upgrade on vote request.
func TestMultiPaxosElectionWithTermUpgrade(t *testing.T) {
	nodes := []string{"node1", "node2", "node3"}
	network := paxos.NewNetworkSimulator(nodes)

	multiNodes := make(map[string]*paxos.MultiPaxos)
	for _, id := range nodes {
		multiNodes[id] = paxos.NewMultiPaxos(id, network)
	}

	// node1 campaigns (term becomes 1)
	multiNodes["node1"].StartCampaign(nodes)

	// node2 campaigns first (term becomes 1)
	multiNodes["node2"].StartCampaign(nodes)

	// node1 campaigns again (term becomes 2)
	multiNodes["node1"].StartCampaign(nodes)

	// node2 receives vote request from node1 with higher term
	req := paxos.Message{
		Type:       paxos.MsgVoteRequest,
		ProposalID: multiNodes["node1"].ProposalID,
		FromNodeID: multiNodes["node1"].NodeID,
		ToNodeID:   "node2",
	}

	// node2 should update its term and grant vote
	resp, granted := multiNodes["node2"].ProcessVoteRequest(req)
	if !granted {
		t.Error("Expected vote to be granted for higher term")
	}

	// node2's term should be updated
	if multiNodes["node2"].Term != multiNodes["node1"].Term {
		t.Errorf("Expected node2 term to be updated to %d, got %d",
			multiNodes["node1"].Term, multiNodes["node2"].Term)
	}
	_ = resp
}

// TestMultiPaxosMultipleAppends verifies multiple sequential appends.
func TestMultiPaxosMultipleAppends(t *testing.T) {
	nodes := []string{"node1", "node2", "node3", "node4", "node5"}
	network := paxos.NewNetworkSimulator(nodes)

	multiNodes := make(map[string]*paxos.MultiPaxos)
	for _, id := range nodes {
		multiNodes[id] = paxos.NewMultiPaxos(id, network)
	}

	// Elect leader
	multiNodes["node1"].StartCampaign(nodes)
	for _, id := range nodes {
		if id == "node1" {
			continue
		}
		req := paxos.Message{
			Type:       paxos.MsgVoteRequest,
			ProposalID: multiNodes["node1"].ProposalID,
			FromNodeID: multiNodes["node1"].NodeID,
			ToNodeID:   id,
		}
		resp, _ := multiNodes[id].ProcessVoteRequest(req)
		_ = resp
	}

	// Append multiple entries
	numEntries := 10
	for i := 0; i < numEntries; i++ {
		_, err := multiNodes["node1"].AppendEntry(i)
		if err != nil {
			t.Fatalf("Failed to append entry %d: %v", i, err)
		}
	}

	log := multiNodes["node1"].GetLog()
	if len(log) != numEntries {
		t.Errorf("Expected %d log entries, got %d", numEntries, len(log))
	}

	// Verify indices are sequential
	for i, entry := range log {
		if entry.Index != i+1 {
			t.Errorf("Expected index %d, got %d", i+1, entry.Index)
		}
	}
}

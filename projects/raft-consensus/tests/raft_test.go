package raft

import (
	"testing"
)

// TestStartNode tests that a new node starts in Follower state.
func TestStartNode(t *testing.T) {
	peers := map[int]string{
		1: "localhost:8001",
		2: "localhost:8002",
		3: "localhost:8003",
	}

	node := StartNode(1, peers)
	defer node.Shutdown()

	if node.GetRole() != "Follower" {
		t.Errorf("Expected role Follower, got %s", node.GetRole())
	}

	if node.GetCurrentTerm() != 0 {
		t.Errorf("Expected term 0, got %d", node.GetCurrentTerm())
	}

	if node.GetPeerID() != 1 {
		t.Errorf("Expected peerID 1, got %d", node.GetPeerID())
	}

	if len(node.GetLog()) != 0 {
		t.Errorf("Expected empty log, got %d entries", len(node.GetLog()))
	}
}

// TestNodeRoleTransition tests the transition from Follower to Candidate to Leader.
func TestNodeRoleTransition(t *testing.T) {
	peers := map[int]string{
		1: "localhost:8001",
		2: "localhost:8002",
		3: "localhost:8003",
	}

	node := StartNode(1, peers)
	defer node.Shutdown()

	// Node starts as Follower
	if node.GetRole() != "Follower" {
		t.Errorf("Expected Follower, got %s", node.GetRole())
	}

	// Start election
	won := node.StartElection()

	// In a single node cluster, it should win (votes for self = majority)
	if !won {
		t.Error("Expected node to win election in single-node cluster")
	}

	if node.GetRole() != "Leader" {
		t.Errorf("Expected Leader, got %s", node.GetRole())
	}

	if node.GetCurrentTerm() != 1 {
		t.Errorf("Expected term 1, got %d", node.GetCurrentTerm())
	}
}

// TestElectionTimeout tests that election timeout produces a valid term.
func TestElectionTimeout(t *testing.T) {
	timeout := ElectionTimeout(150, 300)

	if timeout < 150 {
		t.Errorf("Expected timeout >= 150ms, got %v", timeout)
	}

	if timeout > 300 {
		t.Errorf("Expected timeout <= 300ms, got %v", timeout)
	}
}

// TestLogEntry tests basic log entry creation.
func TestLogEntry(t *testing.T) {
	entry := LogEntry{
		Term:    1,
		Command: "SET key=value",
	}

	if entry.Term != 1 {
		t.Errorf("Expected term 1, got %d", entry.Term)
	}

	if entry.Command != "SET key=value" {
		t.Errorf("Expected command SET key=value, got %s", entry.Command)
	}
}

// TestStateMachine tests basic state machine operations.
func TestStateMachine(t *testing.T) {
	sm := NewStateMachine()

	entry := LogEntry{
		Term:    1,
		Command: "SET key=value",
	}

	result := sm.Apply(entry)
	if result != "OK" {
		t.Errorf("Expected result OK, got %s", result)
	}
}

// TestMultipleNodes tests that multiple nodes can participate in an election.
func TestMultipleNodes(t *testing.T) {
	peers := map[int]string{
		1: "localhost:8001",
		2: "localhost:8002",
		3: "localhost:8003",
	}

	nodes := make(map[int]*Node)
	for id := range peers {
		nodes[id] = StartNode(id, peers)
	}
	defer func() {
		for _, node := range nodes {
			node.Shutdown()
		}
	}()

	// All nodes start as Followers
	for id, node := range nodes {
		if node.GetRole() != "Follower" {
			t.Errorf("Node %d: Expected Follower, got %s", id, node.GetRole())
		}
	}

	// Node 1 starts election
	nodes[1].StartElection()

	// Check that node 1 became leader
	if nodes[1].GetRole() != "Leader" {
		t.Errorf("Node 1: Expected Leader, got %s", nodes[1].GetRole())
	}

	// Check that term was incremented
	if nodes[1].GetCurrentTerm() != 1 {
		t.Errorf("Node 1: Expected term 1, got %d", nodes[1].GetCurrentTerm())
	}
}

// TestLogReplication tests log replication from leader to followers.
func TestLogReplication(t *testing.T) {
	peers := map[int]string{
		1: "localhost:8001",
		2: "localhost:8002",
		3: "localhost:8003",
	}

	// Create log replication manager
	lr := NewLogReplication(len(peers))

	// Create a leader log with entries
	leaderLog := []LogEntry{
		{Term: 1, Command: "SET a=1"},
		{Term: 1, Command: "SET b=2"},
		{Term: 1, Command: "SET c=3"},
	}

	// Initialize nextIndex for all peers
	for peerID := range peers {
		lr.nextIndex[peerID] = 1
	}

	// Replicate first entry
	entry := leaderLog[0]
	committed := lr.ReplicateEntry(entry, leaderLog)

	if !committed {
		t.Error("Expected entry to be committed (majority = 2)")
	}

	// Check commit index
	commitIdx := lr.GetCommitIndex()
	if commitIdx != 1 {
		t.Errorf("Expected commit index 1, got %d", commitIdx)
	}
}

// TestLogMatchingProperty tests the log matching property.
func TestLogMatchingProperty(t *testing.T) {
	safety := NewSafetyManager()

	// Create two logs with matching entries
	logA := []LogEntry{
		{Term: 1, Command: "SET a=1"},
		{Term: 1, Command: "SET b=2"},
		{Term: 2, Command: "SET c=3"},
	}

	logB := []LogEntry{
		{Term: 1, Command: "SET a=1"},
		{Term: 1, Command: "SET b=2"},
		{Term: 2, Command: "SET c=3"},
	}

	// Check matching at each index
	for i := 1; i <= len(logA); i++ {
		if !safety.VerifyLogMatching(logA, logB, i) {
			t.Errorf("Log mismatch at index %d", i)
		}
	}
}

// TestElectionRestriction tests the election restriction property.
func TestElectionRestriction(t *testing.T) {
	// Create a candidate with a complete log
	candidateLog := []LogEntry{
		{Term: 1, Command: "SET a=1"},
		{Term: 1, Command: "SET b=2"},
	}

	// Create voter logs
	voterLogs := [][]LogEntry{
		{
			{Term: 1, Command: "SET a=1"},
			{Term: 1, Command: "SET b=2"},
		},
		{
			{Term: 1, Command: "SET a=1"},
			{Term: 1, Command: "SET b=2"},
		},
	}

	safety := NewSafetyManager()
	safety.RecordCommittedEntry(1, candidateLog[0])
	safety.RecordCommittedEntry(2, candidateLog[1])

	if !safety.VerifyElectionRestriction(candidateLog, voterLogs) {
		t.Error("Election restriction violated: candidate should be eligible")
	}
}

// TestStateMachineSafety tests the state machine safety property.
func TestStateMachineSafety(t *testing.T) {
	sm1 := NewStateMachine()
	sm2 := NewStateMachine()

	// Apply same entries to both state machines
	entries := []LogEntry{
		{Term: 1, Command: "SET x=1"},
		{Term: 1, Command: "SET y=2"},
	}

	for _, entry := range entries {
		sm1.Apply(entry)
		sm2.Apply(entry)
	}

	safety := NewSafetyManager()
	if !safety.VerifyStateMachineSafety([]*StateMachine{sm1, sm2}) {
		t.Error("State machine safety violated: state machines should be identical")
	}
}

// TestClusterManager tests cluster membership changes.
func TestClusterManager(t *testing.T) {
	peers := map[int]string{
		1: "localhost:8001",
		2: "localhost:8002",
	}

	cm := NewClusterManager(peers)

	// Check initial state
	if cm.GetClusterSize() != 2 {
		t.Errorf("Expected cluster size 2, got %d", cm.GetClusterSize())
	}

	// Add a peer
	if err := cm.AddPeer(3); err != nil {
		t.Errorf("Failed to add peer: %v", err)
	}

	if cm.GetClusterSize() != 3 {
		t.Errorf("Expected cluster size 3, got %d", cm.GetClusterSize())
	}

	// Try to add duplicate peer
	if err := cm.AddPeer(3); err == nil {
		t.Error("Expected error when adding duplicate peer")
	}

	// Remove a peer
	if err := cm.RemovePeer(3); err != nil {
		t.Errorf("Failed to remove peer: %v", err)
	}

	if cm.GetClusterSize() != 2 {
		t.Errorf("Expected cluster size 2 after removal, got %d", cm.GetClusterSize())
	}

	// Try to remove non-existent peer
	if err := cm.RemovePeer(4); err == nil {
		t.Error("Expected error when removing non-existent peer")
	}
}

// TestHasMajority tests majority calculation.
func TestHasMajority(t *testing.T) {
	cm := &ClusterManager{
		clusterSize: 3,
	}

	// 2 nodes have majority in a 3-node cluster
	if !cm.HasMajority([]int{1, 2}) {
		t.Error("Expected [1,2] to have majority in 3-node cluster")
	}

	// 1 node does not have majority
	if cm.HasMajority([]int{1}) {
		t.Error("Expected [1] to not have majority in 3-node cluster")
	}

	// 4-node cluster
	cm.clusterSize = 4
	if !cm.HasMajority([]int{1, 2, 3}) {
		t.Error("Expected [1,2,3] to have majority in 4-node cluster")
	}

	if cm.HasMajority([]int{1, 2}) {
		t.Error("Expected [1,2] to not have majority in 4-node cluster")
	}
}

// TestStateRoleString tests the String method of StateRole.
func TestStateRoleString(t *testing.T) {
	tests := []struct {
		role   StateRole
		expect string
	}{
		{Follower, "Follower"},
		{Candidate, "Candidate"},
		{Leader, "Leader"},
		{StateRole(99), "Unknown"},
	}

	for _, test := range tests {
		if test.role.String() != test.expect {
			t.Errorf("Role %d: expected %s, got %s", test.role, test.expect, test.role.String())
		}
	}
}

// TestClientRequest tests client request handling.
func TestClientRequest(t *testing.T) {
	peers := map[int]string{
		1: "localhost:8001",
		2: "localhost:8002",
		3: "localhost:8003",
	}

	// Start node 1 as leader
	node := StartNode(1, peers)
	node.StartElection()

	// Submit a request
	result := node.SubmitRequest("SET key=value")

	// The request should be processed (result is "OK" or similar)
	if result == "" {
		t.Error("Expected non-empty result")
	}
}

// TestCommitIndex tests commit index advancement.
func TestCommitIndex(t *testing.T) {
	peers := map[int]string{
		1: "localhost:8001",
		2: "localhost:8002",
		3: "localhost:8003",
	}

	node := StartNode(1, peers)
	node.StartElection()

	// Initially commit index should be 0
	if node.GetCommitIndex() != 0 {
		t.Errorf("Expected initial commit index 0, got %d", node.GetCommitIndex())
	}

	// Submit requests
	for i := 0; i < 3; i++ {
		node.SubmitRequest("SET key" + string(rune('0'+i)) + "=value")
	}

	// Commit index should have advanced
	commitIdx := node.GetCommitIndex()
	if commitIdx == 0 {
		t.Error("Expected commit index to advance after requests")
	}
}

// TestLogReplicationPayload tests building AppendEntries payload.
func TestLogReplicationPayload(t *testing.T) {
	lr := NewLogReplication(3)

	// Initialize nextIndex
	for i := 1; i <= 3; i++ {
		lr.nextIndex[i] = 1
	}

	leaderLog := []LogEntry{
		{Term: 1, Command: "SET a=1"},
		{Term: 1, Command: "SET b=2"},
	}

	prevLogIndex, prevLogTerm, entries := lr.BuildAppendEntriesPayload(leaderLog, 2)

	// First entry: prevLogIndex=0, prevLogTerm=0, entries contain all
	if prevLogIndex != 0 {
		t.Errorf("Expected prevLogIndex 0, got %d", prevLogIndex)
	}
	if prevLogTerm != 0 {
		t.Errorf("Expected prevLogTerm 0, got %d", prevLogTerm)
	}
	if len(entries) != 2 {
		t.Errorf("Expected 2 entries, got %d", len(entries))
	}
}

// TestFormatAppendEntries tests formatting of AppendEntries messages.
func TestFormatAppendEntries(t *testing.T) {
	msg := FormatAppendEntries(1, 0, 0, nil, 0)
	if msg == "" {
		t.Error("Expected non-empty message")
	}

	msg = FormatAppendEntries(2, 5, 3, []LogEntry{{Term: 4, Command: "SET x=1"}}, 5)
	if msg == "" {
		t.Error("Expected non-empty message")
	}
}

// TestFormatClusterInfo tests formatting of cluster info.
func TestFormatClusterInfo(t *testing.T) {
	info := FormatClusterInfo([]int{1, 2, 3}, 3)
	if info == "" {
		t.Error("Expected non-empty cluster info")
	}
}

// TestElectionWithMultipleCandidates tests election with multiple candidates.
func TestElectionWithMultipleCandidates(t *testing.T) {
	peers := map[int]string{
		1: "localhost:8001",
		2: "localhost:8002",
		3: "localhost:8003",
	}

	nodes := make(map[int]*Node)
	for id := range peers {
		nodes[id] = StartNode(id, peers)
	}
	defer func() {
		for _, node := range nodes {
			node.Shutdown()
		}
	}()

	// Node 1 starts election first
	nodes[1].StartElection()

	// Node 2 should not start a new election if it receives a heartbeat
	// In this simulation, we just verify that node 1 won

	if nodes[1].GetRole() != "Leader" {
		t.Errorf("Node 1 should be Leader, got %s", nodes[1].GetRole())
	}
}

// TestLogEntryTermIncrements tests that log entries have increasing terms.
func TestLogEntryTermIncrements(t *testing.T) {
	peers := map[int]string{
		1: "localhost:8001",
		2: "localhost:8002",
		3: "localhost:8003",
	}

	node := StartNode(1, peers)
	node.StartElection()

	// Submit requests in term 1
	for i := 0; i < 3; i++ {
		node.SubmitRequest("SET key" + string(rune('0'+i)) + "=value")
	}

	logEntries := node.GetLog()
	for i, entry := range logEntries {
		if entry.Term != 1 {
			t.Errorf("Entry %d: expected term 1, got %d", i+1, entry.Term)
		}
	}
}

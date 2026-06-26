package paxos

import (
	"fmt"
	"sync"
	"time"
)

// MultiPaxos implements the Multi-Paxos optimization of the Paxos protocol.
//
// Multi-Paxos improves upon Basic Paxos by electing a single leader that
// handles all proposals. This reduces message complexity:
//   - Basic Paxos: O(n^2) messages per consensus instance
//   - Multi-Paxos: O(n) messages per consensus instance (after leader election)
//
// # Leader Election
//
// Nodes compete to become the leader by requesting votes from a majority.
// The node that receives votes from a majority becomes the leader.
//
// # Log Replication
//
// Once a leader is elected, it replicates log entries to all other nodes.
// Each log entry goes through the Paxos prepare/accept phases, but since
// the leader is stable, most entries are accepted on the first try.
//
// # Key Optimizations
//
//  1. Leader stabilization: The leader sends heartbeats to maintain authority
//  2. Fast path: Accepted entries don't need re-proposal
//  3. Log compaction: Committed entries can be compacted
type MultiPaxos struct {
	NodeID     string
	Term       int
	LeaderID   string
	State      string // "follower", "candidate", "leader"
	Log        []LogEntry
	CommitIndex int
	LastApplied int
	Network    *NetworkSimulator
	ProposalID ProposalID
	mu         sync.RWMutex
}

// LogEntry represents a single entry in the Paxos log.
type LogEntry struct {
	Term       int
	Index      int
	ProposalID ProposalID
	Value      interface{}
	Committed  bool
	Timestamp  time.Time
}

// NewMultiPaxos creates a new Multi-Paxos instance for the given node.
func NewMultiPaxos(nodeID string, network *NetworkSimulator) *MultiPaxos {
	return &MultiPaxos{
		NodeID:  nodeID,
		Term:    0,
		State:   "follower",
		Log:     make([]LogEntry, 0),
		Network: network,
	}
}

// StartCampaign begins a leader election campaign.
func (mp *MultiPaxos) StartCampaign(nodes []string) {
	mp.mu.Lock()
	defer mp.mu.Unlock()

	mp.Term++
	mp.State = "candidate"

	// Send vote requests to all nodes
	voteReq := Message{
		Type:     MsgVoteRequest,
		ProposalID: ProposalID{Number: int64(mp.Term), NodeID: mp.NodeID},
		FromNodeID: mp.NodeID,
	}

	for _, nodeID := range nodes {
		if nodeID == mp.NodeID {
			continue
		}
		voteReq.ToNodeID = nodeID
		mp.Network.Deliver(voteReq)
	}
}

// ProcessVoteRequest handles an incoming vote request.
func (mp *MultiPaxos) ProcessVoteRequest(req Message) (Message, bool) {
	mp.mu.Lock()
	defer mp.mu.Unlock()

	votedFor := "" // Track who we voted for in this term

	// Grant vote if:
	// 1. We haven't voted in this term yet, OR
	// 2. The candidate's term is higher than ours
	grantVote := false
	if req.ProposalID.Number > int64(mp.Term) {
		mp.Term = int(req.ProposalID.Number)
		votedFor = ""
		grantVote = true
	} else if req.ProposalID.Number == int64(mp.Term) && votedFor == "" {
		grantVote = true
	}

	if grantVote {
		votedFor = req.ProposalID.NodeID
	}

	return Message{
		Type:       MsgVoteResponse,
		ProposalID: req.ProposalID,
		FromNodeID: mp.NodeID,
		Term:       mp.Term,
		VoteGranted: grantVote,
	}, grantVote
}

// ProcessVoteResponse handles a vote response.
// Returns true if we've become the leader.
func (mp *MultiPaxos) ProcessVoteResponse(resp Message, totalNodes int) bool {
	mp.mu.Lock()
	defer mp.mu.Unlock()

	if !resp.VoteGranted {
		return false
	}

	// Count votes (including our own)
	votes := 1
	majority := totalNodes/2 + 1

	if votes >= majority {
		mp.State = "leader"
		mp.LeaderID = mp.NodeID
		return true
	}

	return false
}

// SendHeartbeat sends a heartbeat to all nodes to maintain leadership.
func (mp *MultiPaxos) SendHeartbeat(nodes []string) {
	mp.mu.RLock()
	if mp.State != "leader" {
		mp.mu.RUnlock()
		return
	}
	mp.mu.RUnlock()

	heartbeat := Message{
		Type:     MsgHeartbeat,
		FromNodeID: mp.NodeID,
		Term:     mp.Term,
	}

	for _, nodeID := range nodes {
		if nodeID == mp.NodeID {
			continue
		}
		heartbeat.ToNodeID = nodeID
		mp.Network.Deliver(heartbeat)
	}
}

// AppendEntry appends a new entry to the log and replicates it.
func (mp *MultiPaxos) AppendEntry(value interface{}) (*LogEntry, error) {
	mp.mu.Lock()
	defer mp.mu.Unlock()

	if mp.State != "leader" {
		return nil, fmt.Errorf("node %s is not the leader", mp.NodeID)
	}

	// Create new log entry
	entryIndex := len(mp.Log) + 1
	entry := LogEntry{
		Term:       mp.Term,
		Index:      entryIndex,
		ProposalID: ProposalID{Number: int64(entryIndex), NodeID: mp.NodeID},
		Value:      value,
		Committed:  false,
		Timestamp:  time.Now(),
	}
	mp.Log = append(mp.Log, entry)

	// Replicate to all followers
	appendReq := Message{
		Type:       MsgAppendEntries,
		ProposalID: entry.ProposalID,
		Value:      value,
		FromNodeID: mp.NodeID,
		Term:       mp.Term,
	}

	for _, nodeID := range mp.Network.NodeIDs() {
		if nodeID == mp.NodeID {
			continue
		}
		appendReq.ToNodeID = nodeID
		mp.Network.Deliver(appendReq)
	}

	return &entry, nil
}

// GetLog returns a copy of the log.
func (mp *MultiPaxos) GetLog() []LogEntry {
	mp.mu.RLock()
	defer mp.mu.RUnlock()

	logCopy := make([]LogEntry, len(mp.Log))
	copy(logCopy, mp.Log)
	return logCopy
}

// GetCommitIndex returns the commit index.
func (mp *MultiPaxos) GetCommitIndex() int {
	mp.mu.RLock()
	defer mp.mu.RUnlock()
	return mp.CommitIndex
}

// String returns a string representation of the Multi-Paxos instance.
func (mp *MultiPaxos) String() string {
	mp.mu.RLock()
	defer mp.mu.RUnlock()
	return fmt.Sprintf("MultiPaxos{NodeID: %s, Term: %d, State: %s, LogLen: %d}",
		mp.NodeID, mp.Term, mp.State, len(mp.Log))
}

// ElectionResult represents the result of a leader election.
type ElectionResult struct {
	LeaderID string
	Term     int
	Votes    int
	Total    int
	Success  bool
}

// String returns a string representation of the election result.
func (e *ElectionResult) String() string {
	status := "failed"
	if e.Success {
		status = "elected"
	}
	return fmt.Sprintf("Election{Leader: %s, Term: %d, Votes: %d/%d, Status: %s}",
		e.LeaderID, e.Term, e.Votes, e.Total, status)
}

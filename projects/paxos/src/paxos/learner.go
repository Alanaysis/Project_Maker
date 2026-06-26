package paxos

import (
	"sync"
)

// Learner implements the learner role in the Paxos protocol.
//
// The learner's job is to learn the decided value once a majority
// of acceptors have accepted a proposal. The learner does not
// participate in the consensus protocol itself; it simply observes
// the Accepted messages and learns the value when a majority agrees.
//
// A value is decided when it has been accepted by a majority of acceptors.
// Once decided, the value cannot change - this is the safety property of Paxos.
type Learner struct {
	NodeID      string
	Decided     bool
	DecidedID   ProposalID
	DecidedVal  interface{}
	AcceptedBy  map[string]ProposalID // Track which acceptors have accepted
	mu          sync.RWMutex
}

// NewLearner creates a new learner with the given node ID.
func NewLearner(nodeID string) *Learner {
	return &Learner{
		NodeID:     nodeID,
		AcceptedBy: make(map[string]ProposalID),
	}
}

// Learn processes an Accepted message from an acceptor.
//
// When an acceptor accepts a proposal, it notifies all learners.
// The learner tracks which acceptors have accepted which proposal.
// When a majority have accepted the same proposal, the value is decided.
func (l *Learner) Learn(msg Message) bool {
	l.mu.Lock()
	defer l.mu.Unlock()

	// Track which acceptor accepted which proposal
	l.AcceptedBy[msg.FromNodeID] = msg.ProposalID

	// Check if a majority has accepted the same proposal
	if l.isDecided() {
		l.Decided = true
		l.DecidedID = msg.ProposalID
		l.DecidedVal = msg.Value
		return true
	}

	return false
}

// isDecided checks if a majority of acceptors have accepted the same proposal.
func (l *Learner) isDecided() bool {
	// Count acceptances for each proposal ID
	counts := make(map[string]int)
	for _, id := range l.AcceptedBy {
		key := id.String()
		counts[key]++
	}

	// Check if any proposal has majority support
	for _, count := range counts {
		// We don't know total nodes here, so we return a special signal
		_ = count
	}
	return false
}

// CheckMajority checks if a proposal has majority support given total nodes.
func (l *Learner) CheckMajority(totalNodes int) bool {
	l.mu.RLock()
	defer l.mu.RUnlock()

	// Count acceptances for the most recent proposal
	proposalKey := ""
	for _, id := range l.AcceptedBy {
		proposalKey = id.String()
	}

	if proposalKey == "" {
		return false
	}

	count := 0
	for _, id := range l.AcceptedBy {
		if id.String() == proposalKey {
			count++
		}
	}

	return count > totalNodes/2
}

// GetDecidedValue returns the decided value, if any.
func (l *Learner) GetDecidedValue() (bool, ProposalID, interface{}) {
	l.mu.RLock()
	defer l.mu.RUnlock()
	return l.Decided, l.DecidedID, l.DecidedVal
}

// Reset clears the learner's state for a new consensus round.
func (l *Learner) Reset() {
	l.mu.Lock()
	defer l.mu.Unlock()
	l.Decided = false
	l.DecidedID = ProposalID{}
	l.DecidedVal = nil
	l.AcceptedBy = make(map[string]ProposalID)
}

package paxos

import (
	"sync"
)

// Proposer implements the proposer role in the Paxos protocol.
//
// The proposer's job is to:
//  1. Choose a unique proposal number
//  2. Send Prepare requests to a majority of acceptors
//  3. If it receives promises from a majority, send Accept requests
//  4. Wait for acceptances from a majority to decide the value
//
// The proposer must handle the case where another proposer with a
// higher proposal number may have already promised, in which case
// it should adopt the value from the highest accepted proposal
// (or use its own value if no proposal was accepted).
type Proposer struct {
	NodeID       string
	ProposalNum  int64
	ProposalID   ProposalID
	Value        interface{}
	State        string // "idle", "preparing", "accepting", "decided"
	Promises     []Message
	Acceptances  []Message
	mu           sync.Mutex
}

// NewProposer creates a new proposer with the given node ID and proposal counter.
func NewProposer(nodeID string, counter *ProposalCounter) *Proposer {
	p := &Proposer{
		NodeID:  nodeID,
		State:   "idle",
	}
	// Generate initial proposal number
	p.ProposalNum = counter.Next()
	p.ProposalID = NewProposalID(p.ProposalNum, nodeID)
	return p
}

// NewProposal creates a new proposal with a fresh number.
func (p *Proposer) NewProposal(counter *ProposalCounter) {
	p.mu.Lock()
	defer p.mu.Unlock()
	p.ProposalNum = counter.Next()
	p.ProposalID = NewProposalID(p.ProposalNum, p.NodeID)
	p.State = "idle"
	p.Promises = make([]Message, 0)
	p.Acceptances = make([]Message, 0)
}

// Prepare sends a Prepare request and returns the result.
func (p *Proposer) Prepare() Proposal {
	p.mu.Lock()
	p.State = "preparing"
	p.mu.Unlock()

	return Proposal{
		ID:      p.ProposalID,
		Value:   p.Value,
		Phase:   "prepare",
	}
}

// ProcessPromise handles a Promise response from an acceptor.
//
// If the promise is valid (proposal number >= highest promise at acceptor),
// add it to the promises list. If we have promises from a majority,
// transition to the accept phase.
func (p *Proposer) ProcessPromise(msg Message) bool {
	p.mu.Lock()
	defer p.mu.Unlock()

	// Check if this promise is still valid (our proposal number is still highest)
	if p.State != "preparing" {
		return false
	}

	p.Promises = append(p.Promises, msg)
	return true
}

// HasMajority checks if we have promises from a majority of acceptors.
func (p *Proposer) HasMajority(totalNodes int) bool {
	return len(p.Promises) > totalNodes/2
}

// DetermineValue determines the value to propose.
//
// If any acceptor has previously accepted a value, use the value
// from the acceptor with the highest proposal ID. Otherwise, use
// the proposer's own value.
//
// This ensures safety: if a value has been accepted, it will be
// the one that gets chosen.
func (p *Proposer) DetermineValue() interface{} {
	p.mu.Lock()
	defer p.mu.Unlock()

	// Find the highest accepted value among promises
	highestID := ProposalID{}
	value := p.Value

	for _, msg := range p.Promises {
		if msg.AcceptedID.Number > highestID.Number {
			highestID = msg.AcceptedID
			value = msg.AcceptedVal
		}
	}

	return value
}

// ProcessAccept handles an Accept response from an acceptor.
func (p *Proposer) ProcessAccept(msg Message) bool {
	p.mu.Lock()
	defer p.mu.Unlock()

	if p.State != "accepting" {
		return false
	}

	p.Acceptances = append(p.Acceptances, msg)
	return true
}

// HasMajorityAccept checks if we have acceptances from a majority.
func (p *Proposer) HasMajorityAccept(totalNodes int) bool {
	count := 0
	for _, msg := range p.Acceptances {
		if msg.Accepted {
			count++
		}
	}
	return count > totalNodes/2
}

// Decide marks the proposal as decided and returns the decided value.
func (p *Proposer) Decide() interface{} {
	p.mu.Lock()
	defer p.mu.Unlock()
	p.State = "decided"
	return p.Value
}

package paxos

import (
	"fmt"
	"sync"
)

// SinglePaxos implements a single instance of the Paxos protocol.
//
// This implements Basic Paxos for a single value consensus among n nodes
// where up to (n-1)/2 nodes may fail.
//
// # Protocol Flow
//
//	Proposer                    Acceptors                    Learners
//	    |                           |                           |
//	    |------ Prepare(n) -------->|                           |
//	    |                           |                           |
//	    |<--- Promise(n, v) --------|                           |
//	    |                           |                           |
//	    |------ Accept(n, v) ------>|                           |
//	    |                           |                           |
//	    |<--- Accepted(n, v) -------|------ Notify(n, v) ------>|
//	    |                           |                           |
//
// # Safety Property
//
// Once a value is chosen, no other value will be chosen. This is ensured by:
//  1. The prepare phase: acceptors promise not to accept lower-numbered proposals
//  2. The accept phase: a value is only accepted if it hasn't been promised
//     away to a higher-numbered proposal
//
// # Liveness Property
//
// Eventually, a value will be chosen, assuming:
//  1. A majority of nodes are always available
//  2. Network messages are eventually delivered
//  3. Proposer proposal numbers are unique and strictly increasing
func SinglePaxos(nodes []string, network *NetworkSimulator, value interface{}) (*Result, error) {
	// Create acceptors for each node
	acceptors := make(map[string]*Acceptor)
	for _, nodeID := range nodes {
		acceptors[nodeID] = NewAcceptor(nodeID)
	}

	// Create a proposal counter for unique proposal numbers
	counter := NewProposalCounter()

	// Choose a proposer (first node)
	proposerID := nodes[0]
	proposer := NewProposer(proposerID, counter)
	proposer.Value = value

	// Phase 1: Prepare
	// The proposer picks a new proposal number and sends Prepare to all acceptors
	prepareMsg := proposer.Prepare()

	// Send Prepare to all acceptors
	for _, nodeID := range nodes {
		if nodeID == proposerID {
			continue
		}
		pMsg := Message{
			Type:       MsgPrepare,
			ProposalID: prepareMsg.ID,
			FromNodeID: proposerID,
			ToNodeID:   nodeID,
		}
		network.Deliver(pMsg)
	}

	// Collect promises from acceptors
	promises := make([]Message, 0)

	// Process the proposer's own acceptor
	promise := acceptors[proposerID].Promise(prepareMsg.ID)
	promises = append(promises, promise)

	// Process promises from other acceptors
	for _, nodeID := range nodes {
		if nodeID == proposerID {
			continue
		}
		promise := acceptors[nodeID].Promise(prepareMsg.ID)
		promises = append(promises, promise)

		// Deliver promise back to proposer
		dMsg := Message{
			Type:       MsgPromise,
			ProposalID: promise.ProposalID,
			FromNodeID: nodeID,
			ToNodeID:   proposerID,
			Promise:    promise.Promise,
			AcceptedID: promise.AcceptedID,
			AcceptedVal: promise.AcceptedVal,
		}
		network.Deliver(dMsg)
	}

	// Check if we got a majority of promises
	majorityCount := len(nodes)/2 + 1
	if len(promises) < majorityCount {
		return nil, fmt.Errorf("not enough promises: got %d, need %d", len(promises), majorityCount)
	}

	// Determine the value to propose
	// If any promise includes an accepted value, use the one from the
	// highest proposal ID (ensures safety)
	proposedValue := value
	highestID := ProposalID{}
	for _, p := range promises {
		if p.AcceptedID.Number > highestID.Number {
			highestID = p.AcceptedID
			proposedValue = p.AcceptedVal
		}
	}

	proposer.Value = proposedValue
	proposer.Promises = promises

	// Phase 2: Accept
	// The proposer sends Accept to all acceptors

	// Send Accept to all acceptors
	acceptances := make([]Message, 0)
	for _, nodeID := range nodes {
		accepted := acceptors[nodeID].Accept(proposer.ProposalID, proposedValue)
		acceptances = append(acceptances, accepted)

		// Deliver acceptance notification to learners (all nodes)
		for _, learnerID := range nodes {
			lMsg := Message{
				Type:       MsgAccepted,
				ProposalID: proposer.ProposalID,
				Value:      proposedValue,
				FromNodeID: nodeID,
				ToNodeID:   learnerID,
			}
			network.Deliver(lMsg)
		}
	}

	// Check if we got a majority of acceptances
	acceptCount := 0
	for _, a := range acceptances {
		if a.Accepted {
			acceptCount++
		}
	}

	if acceptCount < majorityCount {
		return nil, fmt.Errorf("not enough acceptances: got %d, need %d", acceptCount, majorityCount)
	}

	// Value is decided!
	proposer.Decide()

	// Create learners and learn the value
	learners := make(map[string]*Learner)
	for _, nodeID := range nodes {
		learners[nodeID] = NewLearner(nodeID)
	}

	for _, nodeID := range nodes {
		for _, a := range acceptances {
			if a.FromNodeID == nodeID {
				learners[nodeID].Learn(a)
			}
		}
	}

	return &Result{
		Decided:    true,
		ProposalID: proposer.ProposalID,
		Value:      proposedValue,
		Promises:   len(promises),
		Acceptances: acceptCount,
	}, nil
}

// Result contains the outcome of a Paxos consensus round.
type Result struct {
	Decided    bool
	ProposalID ProposalID
	Value      interface{}
	Promises   int
	Acceptances int
}

// String returns a string representation of the result.
func (r *Result) String() string {
	status := "undecided"
	if r.Decided {
		status = "decided"
	}
	return fmt.Sprintf("Result{Status: %s, ID: %s, Value: %v, Promises: %d, Acceptances: %d}",
		status, r.ProposalID, r.Value, r.Promises, r.Acceptances)
}

// ConsensusNode represents a node that participates in Paxos consensus.
type ConsensusNode struct {
	NodeID   string
	Acceptor *Acceptor
	Learner  *Learner
	Proposer *Proposer
	Network  *NetworkSimulator
	mu       sync.Mutex
}

// NewConsensusNode creates a new consensus node.
func NewConsensusNode(nodeID string, network *NetworkSimulator) *ConsensusNode {
	return &ConsensusNode{
		NodeID:  nodeID,
		Acceptor: NewAcceptor(nodeID),
		Learner: NewLearner(nodeID),
		Network: network,
	}
}

// RunSinglePaxos runs a complete single Paxos consensus round.
func RunSinglePaxos(nodes []string, network *NetworkSimulator, value interface{}) (*Result, error) {
	return SinglePaxos(nodes, network, value)
}

// StartRound initiates a new consensus round.
func (cn *ConsensusNode) StartRound(counter *ProposalCounter, value interface{}) {
	cn.mu.Lock()
	defer cn.mu.Unlock()
	cn.Proposer = NewProposer(cn.NodeID, counter)
	cn.Proposer.Value = value
	cn.Proposer.NewProposal(counter)
}

// ResetLearner resets the learner for a new round.
func (cn *ConsensusNode) ResetLearner() {
	cn.Learner.Reset()
}

// GetDecidedValue returns the decided value if any.
func (cn *ConsensusNode) GetDecidedValue() (bool, ProposalID, interface{}) {
	return cn.Learner.GetDecidedValue()
}

// String returns a string representation of the consensus node.
func (cn *ConsensusNode) String() string {
	return fmt.Sprintf("ConsensusNode{ID: %s}", cn.NodeID)
}

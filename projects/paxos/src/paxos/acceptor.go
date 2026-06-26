package paxos

import (
	"fmt"
	"sync"
)

// Acceptor implements the acceptor role in the Paxos protocol.
//
// The acceptor's responsibilities are:
//  1. Accept promises for prepare requests with the highest proposal number seen.
//  2. Accept proposals if the proposal number is higher than any promised.
//  3. Report the highest accepted proposal (if any) in promise responses.
//
// Key invariant: An acceptor can promise for proposal number N only if it
// has not already promised for a proposal with a higher number.
// Once it accepts a proposal with number N, it must accept all future
// proposals with numbers > N.
type Acceptor struct {
	NodeID         string
	HighestPromise int64       // Highest proposal number this acceptor has promised for
	PromiseID      ProposalID // The proposal ID the acceptor promised for
	AcceptedID     ProposalID // The highest proposal ID the acceptor has accepted
	AcceptedVal    interface{} // The value associated with AcceptedID
	mu             sync.Mutex
}

// NewAcceptor creates a new acceptor with the given node ID.
func NewAcceptor(nodeID string) *Acceptor {
	return &Acceptor{
		NodeID: nodeID,
	}
}

// Promise handles a Prepare request from a proposer.
//
// The acceptor responds with a promise if the incoming proposal number
// is strictly greater than any previous promise number. The promise
// includes the highest proposal the acceptor has previously accepted
// (if any), so the proposer can use the value from that proposal.
//
// Returns a Promise message containing:
//   - promise: true if the acceptor promises not to accept lower-numbered proposals
//   - promiseID: the proposal ID the acceptor promised for
//   - acceptedID: the highest accepted proposal ID (if any)
//   - acceptedVal: the value of the highest accepted proposal (if any)
func (a *Acceptor) Promise(incomingID ProposalID) Message {
	a.mu.Lock()
	defer a.mu.Unlock()

	msg := Message{
		Type:       MsgPromise,
		ProposalID: incomingID,
		FromNodeID: a.NodeID,
		Promise:    false,
	}

	// Accept the promise only if incoming proposal number is higher
	if incomingID.Number > a.HighestPromise {
		a.HighestPromise = incomingID.Number
		a.PromiseID = incomingID

		msg.Promise = true

		// Include the highest accepted proposal info (if any)
		if a.AcceptedID.Number > 0 {
			msg.AcceptedID = a.AcceptedID
			msg.AcceptedVal = a.AcceptedVal
		}
	}

	return msg
}

// Accept handles an Accept request from a proposer.
//
// The acceptor accepts the proposal if the proposal number is at least
// as high as any promise it has given. This ensures that once a value
// is accepted by a majority, it cannot be overwritten by a lower-numbered proposal.
//
// Returns an Accepted message containing:
//   - accepted: true if the acceptor accepted the proposal
//   - proposalID: the proposal ID that was accepted
func (a *Acceptor) Accept(proposalID ProposalID, value interface{}) Message {
	a.mu.Lock()
	defer a.mu.Unlock()

	msg := Message{
		Type:       MsgAccepted,
		ProposalID: proposalID,
		FromNodeID: a.NodeID,
		Accepted:   false,
	}

	// Only accept if the proposal number is >= highest promise
	if proposalID.Number >= a.HighestPromise {
		a.AcceptedID = proposalID
		a.AcceptedVal = value

		msg.Accepted = true
	}

	return msg
}

// GetState returns the current state of the acceptor for inspection.
func (a *Acceptor) GetState() (int64, ProposalID, interface{}) {
	a.mu.Lock()
	defer a.mu.Unlock()
	return a.HighestPromise, a.AcceptedID, a.AcceptedVal
}

// String returns a string representation of the acceptor.
func (a *Acceptor) String() string {
	a.mu.Lock()
	defer a.mu.Unlock()
	return fmt.Sprintf("Acceptor{NodeID: %s, HighestPromise: %d, AcceptedID: %s}",
		a.NodeID, a.HighestPromise, a.AcceptedID)
}

package paxos

import (
	"fmt"
	"sync/atomic"
)

// ProposalID uniquely identifies a proposal in Paxos.
// It consists of a monotonically increasing number and the proposer's node ID.
// The proposal number must be globally unique to ensure safety.
type ProposalID struct {
	Number int64  // Monotonically increasing proposal number
	NodeID string // ID of the node that created this proposal
}

// NewProposalID creates a new proposal ID.
func NewProposalID(number int64, nodeID string) ProposalID {
	return ProposalID{Number: number, NodeID: nodeID}
}

// String returns a string representation of the proposal ID.
func (p ProposalID) String() string {
	return fmt.Sprintf("%d-%s", p.Number, p.NodeID)
}

// GreaterThan compares two proposal IDs.
// Returns true if p has a higher number, or same number but higher node ID.
func (p ProposalID) GreaterThan(other ProposalID) bool {
	if p.Number != other.Number {
		return p.Number > other.Number
	}
	return p.NodeID > other.NodeID
}

// AcceptorRole represents the role of an acceptor in the Paxos protocol.
type AcceptorRole int

const (
	// AcceptorStateUnpromised means the acceptor has never promised.
	AcceptorStateUnpromised AcceptorRole = iota
	// AcceptorStatePromised means the acceptor has promised not to accept
	// proposals with lower numbers.
	AcceptorStatePromised
	// AcceptorStateAccepted means the acceptor has accepted a proposal.
	AcceptorStateAccepted
)

// Proposal represents a Paxos proposal containing a value to be decided.
type Proposal struct {
	ID      ProposalID
	Value   interface{}
	Phase   string // "prepare", "accept", "learn"
}

// Message represents a message exchanged between Paxos nodes.
type Message struct {
	Type        MessageType
	ProposalID  ProposalID
	Value       interface{}
	FromNodeID  string
	ToNodeID    string
	Promise     bool
	Accepted    bool
	FromState   AcceptorRole
	AcceptedID  ProposalID // Highest accepted proposal ID (for Promise messages)
	AcceptedVal interface{} // Value of the highest accepted proposal
	Term        int       // Term for leader election (Multi-Paxos)
	VoteGranted bool      // Whether vote was granted
}

// MessageType identifies the kind of Paxos protocol message.
type MessageType int

const (
	// MsgPrepare is sent by a proposer to request permission to propose.
	MsgPrepare MessageType = iota
	// MsgPromise is the response to a Prepare message.
	MsgPromise
	// MsgAccept is sent by a proposer to request acceptance of a value.
	MsgAccept
	// MsgAccepted is sent by an acceptor when it accepts a value.
	MsgAccepted
	// MsgLearn is sent to notify learners of a decided value.
	MsgLearn
	// MsgVoteRequest is used in leader election (Multi-Paxos).
	MsgVoteRequest
	// MsgVoteResponse is the response to a vote request.
	MsgVoteResponse
	// MsgHeartbeat is sent by the leader to maintain authority.
	MsgHeartbeat
	// MsgAppendEntries is used in log replication (Multi-Paxos).
	MsgAppendEntries
	// MsgAppendResponse is the response to an append entries request.
	MsgAppendResponse
)

// String returns a string representation of the message type.
func (m MessageType) String() string {
	names := []string{
		"PREPARE", "PROMISE", "ACCEPT", "ACCEPTED",
		"LEARN", "VOTE_REQUEST", "VOTE_RESPONSE",
		"HEARTBEAT", "APPEND_ENTRIES", "APPEND_RESPONSE",
	}
	if int(m) < len(names) {
		return names[m]
	}
	return "UNKNOWN"
}

// NetworkSimulator provides a simulated network for testing Paxos.
type NetworkSimulator struct {
	nodeIDs   []string
	messages  []Message
	deliver   map[string]chan Message
	delivered map[string][]Message
}

// NewNetworkSimulator creates a new network simulator with the given node IDs.
func NewNetworkSimulator(nodeIDs []string) *NetworkSimulator {
	ns := &NetworkSimulator{
		nodeIDs:   nodeIDs,
		messages:  make([]Message, 0),
		deliver:   make(map[string]chan Message),
		delivered: make(map[string][]Message),
	}
	for _, id := range nodeIDs {
		ns.deliver[id] = make(chan Message, 100)
		ns.delivered[id] = make([]Message, 0)
	}
	return ns
}

// Deliver sends a message to a node.
func (ns *NetworkSimulator) Deliver(msg Message) {
	ns.messages = append(ns.messages, msg)
	if ch, ok := ns.deliver[msg.ToNodeID]; ok {
		ch <- msg
	}
}

// DeliverBatch delivers all pending messages to a node.
func (ns *NetworkSimulator) DeliverBatch(nodeID string) []Message {
	ch := ns.deliver[nodeID]
	messages := make([]Message, 0)
	for {
		select {
		case msg := <-ch:
			messages = append(messages, msg)
			ns.delivered[nodeID] = append(ns.delivered[nodeID], msg)
		default:
			return messages
		}
	}
}

// GetDelivered returns all messages delivered to a node.
func (ns *NetworkSimulator) GetDelivered(nodeID string) []Message {
	return ns.delivered[nodeID]
}

// NodeIDs returns the list of node IDs in this network.
func (ns *NetworkSimulator) NodeIDs() []string {
	return ns.nodeIDs
}

// AllMessages returns all messages in the network.
func (ns *NetworkSimulator) AllMessages() []Message {
	return ns.messages
}

// Clear clears all delivered messages.
func (ns *NetworkSimulator) Clear() {
	for id := range ns.deliver {
		ns.delivered[id] = make([]Message, 0)
	}
}

// ProposalCounter generates unique proposal numbers.
type ProposalCounter struct {
	counter atomic.Int64
}

// NewProposalCounter creates a new proposal number generator.
func NewProposalCounter() *ProposalCounter {
	return &ProposalCounter{}
}

// Next generates the next unique proposal number.
func (pc *ProposalCounter) Next() int64 {
	return pc.counter.Add(1)
}

// Value represents a decided value in the Paxos protocol.
type Value struct {
	ProposalID ProposalID
	Value      interface{}
}

// String returns a string representation of the value.
func (v Value) String() string {
	return fmt.Sprintf("Value{ID: %s, Value: %v}", v.ProposalID, v.Value)
}

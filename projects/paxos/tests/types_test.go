package paxos_test

import (
	"testing"

	"paxos/src/paxos"
)

// TestProposalIDOrdering verifies proposal ID comparison works correctly.
func TestProposalIDOrdering(t *testing.T) {
	tests := []struct {
		a        paxos.ProposalID
		b        paxos.ProposalID
		greater  bool
	}{
		{paxos.NewProposalID(10, "node1"), paxos.NewProposalID(5, "node2"), true},
		{paxos.NewProposalID(5, "node1"), paxos.NewProposalID(10, "node2"), false},
		{paxos.NewProposalID(10, "node2"), paxos.NewProposalID(10, "node1"), true},
		{paxos.NewProposalID(10, "node1"), paxos.NewProposalID(10, "node2"), false},
		{paxos.NewProposalID(10, "node1"), paxos.NewProposalID(10, "node1"), false},
	}

	for _, tc := range tests {
		got := tc.a.GreaterThan(tc.b)
		if got != tc.greater {
			t.Errorf("GreaterThan(%v, %v) = %v, want %v",
				tc.a, tc.b, got, tc.greater)
		}
	}
}

// TestProposalIDString verifies string representation.
func TestProposalIDString(t *testing.T) {
	id := paxos.NewProposalID(42, "node1")
	want := "42-node1"
	if got := id.String(); got != want {
		t.Errorf("ProposalID.String() = %q, want %q", got, want)
	}
}

// TestProposalCounter verifies unique proposal number generation.
func TestProposalCounter(t *testing.T) {
	counter := paxos.NewProposalCounter()
	n1 := counter.Next()
	n2 := counter.Next()
	n3 := counter.Next()

	if n1 >= n2 || n2 >= n3 {
		t.Errorf("Proposal numbers not strictly increasing: %d, %d, %d", n1, n2, n3)
	}
}

// TestAcceptorPromise verifies the promise mechanism.
func TestAcceptorPromise(t *testing.T) {
	acceptor := paxos.NewAcceptor("acceptor1")

	// First promise should succeed
	p1 := paxos.NewProposalID(10, "proposer1")
	msg1 := acceptor.Promise(p1)
	if !msg1.Promise {
		t.Error("First promise should be granted")
	}

	// Second promise with higher number should succeed
	p2 := paxos.NewProposalID(20, "proposer2")
	msg2 := acceptor.Promise(p2)
	if !msg2.Promise {
		t.Error("Higher-numbered promise should be granted")
	}

	// Third promise with lower number should fail
	p3 := paxos.NewProposalID(15, "proposer3")
	msg3 := acceptor.Promise(p3)
	if msg3.Promise {
		t.Error("Lower-numbered promise should be rejected")
	}
}

// TestAcceptorAccept verifies the accept mechanism.
func TestAcceptorAccept(t *testing.T) {
	acceptor := paxos.NewAcceptor("acceptor1")

	// Promise for proposal 10
	p := paxos.NewProposalID(10, "proposer1")
	acceptor.Promise(p)

	// Accept should succeed for proposal >= 10
	accept1 := acceptor.Accept(paxos.NewProposalID(10, "proposer1"), "value1")
	if !accept1.Accepted {
		t.Error("Accept for proposal >= promised should succeed")
	}

	// Accept should fail for proposal < 10
	accept2 := acceptor.Accept(paxos.NewProposalID(5, "proposer2"), "value2")
	if accept2.Accepted {
		t.Error("Accept for proposal < promised should fail")
	}
}

// TestAcceptorInitialState verifies default state.
func TestAcceptorInitialState(t *testing.T) {
	acceptor := paxos.NewAcceptor("acceptor1")
	promise, id, val := acceptor.GetState()

	if promise != 0 {
		t.Errorf("Initial highest promise should be 0, got %d", promise)
	}
	if id.Number != 0 {
		t.Errorf("Initial accepted ID should be 0, got %d", id.Number)
	}
	if val != nil {
		t.Errorf("Initial accepted value should be nil, got %v", val)
	}
}

// TestAcceptorString verifies string representation.
func TestAcceptorString(t *testing.T) {
	acceptor := paxos.NewAcceptor("acceptor1")
	s := acceptor.String()
	if s == "" {
		t.Error("Acceptor.String() should not be empty")
	}
}

// TestMessageTypeString verifies message type names.
func TestMessageTypeString(t *testing.T) {
	tests := []struct {
		msgType paxos.MessageType
		want    string
	}{
		{paxos.MsgPrepare, "PREPARE"},
		{paxos.MsgPromise, "PROMISE"},
		{paxos.MsgAccept, "ACCEPT"},
		{paxos.MsgAccepted, "ACCEPTED"},
		{paxos.MsgLearn, "LEARN"},
		{paxos.MsgVoteRequest, "VOTE_REQUEST"},
		{paxos.MsgVoteResponse, "VOTE_RESPONSE"},
		{paxos.MsgHeartbeat, "HEARTBEAT"},
		{paxos.MsgAppendEntries, "APPEND_ENTRIES"},
		{paxos.MsgAppendResponse, "APPEND_RESPONSE"},
	}

	for _, tc := range tests {
		got := tc.msgType.String()
		if got != tc.want {
			t.Errorf("MessageType.String(%d) = %q, want %q", tc.msgType, got, tc.want)
		}
	}
}

// TestNetworkSimulator verifies the network simulator.
func TestNetworkSimulator(t *testing.T) {
	nodes := []string{"node1", "node2", "node3"}
	ns := paxos.NewNetworkSimulator(nodes)

	// Verify node IDs
	got := ns.NodeIDs()
	if len(got) != len(nodes) {
		t.Errorf("NodeIDs() = %d, want %d", len(got), len(nodes))
	}

	// Deliver a message
	msg := paxos.Message{
		Type:       paxos.MsgPrepare,
		ProposalID: paxos.NewProposalID(1, "proposer1"),
		FromNodeID: "proposer1",
		ToNodeID:   "node2",
	}
	ns.Deliver(msg)

	// Deliver batch to node2
	delivered := ns.DeliverBatch("node2")
	if len(delivered) != 1 {
		t.Errorf("Delivered %d messages, want 1", len(delivered))
	}

	// Verify all messages
	allMsgs := ns.AllMessages()
	if len(allMsgs) != 1 {
		t.Errorf("AllMessages() = %d, want 1", len(allMsgs))
	}

	// Verify delivered messages
	gotDelivered := ns.GetDelivered("node2")
	if len(gotDelivered) != 1 {
		t.Errorf("GetDelivered() = %d, want 1", len(gotDelivered))
	}

	// Test clear
	ns.Clear()
	gotDelivered = ns.GetDelivered("node2")
	if len(gotDelivered) != 0 {
		t.Errorf("After clear, GetDelivered() = %d, want 0", len(gotDelivered))
	}
}

// TestValueString verifies Value string representation.
func TestValueString(t *testing.T) {
	v := paxos.Value{
		ProposalID: paxos.NewProposalID(42, "node1"),
		Value:      "hello",
	}
	s := v.String()
	if s == "" {
		t.Error("Value.String() should not be empty")
	}
}

// TestResultString verifies Result string representation.
func TestResultString(t *testing.T) {
	r := &paxos.Result{
		Decided:    true,
		ProposalID: paxos.NewProposalID(1, "node1"),
		Value:      "test",
		Promises:   3,
		Acceptances: 3,
	}
	s := r.String()
	if s == "" {
		t.Error("Result.String() should not be empty")
	}
}

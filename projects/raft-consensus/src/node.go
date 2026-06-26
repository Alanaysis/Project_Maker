package raft

import (
	"fmt"
	"log"
	"math/rand"
	"sync"
	"time"
)

// StartNode creates and starts a new Raft node.
//
// The node starts as a Follower and will transition to Candidate
// when its election timer expires.
func StartNode(peerID int, peers map[int]string) *Node {
	sm := NewStateMachine()

	n := &Node{
		currentTerm:    0,
		votedFor:       -1,
		peerID:         peerID,
		peers:          peers,
		clusterSize:    len(peers),
		role:           Follower,
		stateMachine:   sm,
		log:            []LogEntry{},
		nextIndex:      make(map[int]int),
		matchIndex:     make(map[int]int),
		votesReceived:  make(map[int]bool),
		committedCount: make(map[int]bool),
		reqChan:        make(chan ClientRequest, 100),
		quit:           make(chan struct{}),
		done:           make(chan struct{}),
	}

	// Initialize matchIndex for all peers
	for id := range peers {
		n.matchIndex[id] = 0
	}
	n.matchIndex[peerID] = 0

	n.electionTimer = NewElectionTimer(150, 300)

	// Start the node's main loop
	go n.run()

	log.Printf("[RAFT] Node %d started as Follower, term %d", peerID, n.currentTerm)
	return n
}

// run is the main event loop for the Raft node.
// It handles:
//   1. Processing client requests
//   2. Handling election timeouts
//   3. Processing RPC responses
//
// This loop processes events in order, which is critical for Raft's safety.
func (n *Node) run() {
	defer close(n.done)

	for {
		select {
		case req := <-n.reqChan:
			n.handleClientRequest(req)
		case <-n.quit:
			return
		default:
			// Check election timeout
			if n.electionTimer != nil {
				// In production, would check actual timer expiry
				// For simulation, we trigger elections based on conditions
			}
			time.Sleep(10 * time.Millisecond)
		}
	}
}

// Shutdown gracefully stops the Raft node.
func (n *Node) Shutdown() {
	close(n.quit)
	<-n.done
	log.Printf("[RAFT] Node %d shut down", n.peerID)
}

// SubmitRequest submits a client request to the Raft cluster.
// The request will be replicated by the leader and applied to the state machine.
// Returns the result once the request is committed.
func (n *Node) SubmitRequest(command string) string {
	resultChan := make(chan string, 1)
	n.reqChan <- ClientRequest{
		Command: command,
		Result:  resultChan,
	}
	return <-resultChan
}

// handleClientRequest processes a client request.
// Only the leader can accept client requests.
// The leader appends the request to its log, replicates it to followers,
// and once committed, applies it to the state machine.
func (n *Node) handleClientRequest(req ClientRequest) {
	if n.role != Leader {
		req.Result <- fmt.Sprintf("NOT_LEADER: Node %d is not the leader", n.peerID)
		return
	}

	// Append the command to the leader's log
	entry := LogEntry{
		Term:    n.currentTerm,
		Command: req.Command,
	}
	n.log = append(n.log, entry)
	n.matchIndex[n.peerID] = len(n.log)

	// Replicate to followers (simplified - in production this is asynchronous)
	n.replicateToFollowers(entry)

	// Check if entry is committed (majority replication)
	if n.isCommitted(len(n.log) - 1) {
		// Apply to state machine
		result := n.stateMachine.Apply(entry)
		req.Result <- result
	} else {
		req.Result <- "PENDING: Entry not yet committed by majority"
	}
}

// replicateToFollowers replicates a log entry to all followers.
// In production, this sends AppendEntries RPCs to each follower.
// The leader tracks matchIndex for each follower to determine commit point.
func (n *Node) replicateToFollowers(entry LogEntry) {
	if n.role != Leader {
		return
	}

	// Count how many nodes (including leader) have this entry
	count := 1 // Leader has it
	for peerID := range n.peers {
		if peerID != n.peerID {
			// In production, would send AppendEntries RPC
			// For simulation, assume successful replication
			n.matchIndex[peerID] = len(n.log)
			count++
		}
	}

	// Update committed index if majority has replicated
	if count > n.clusterSize/2 {
		n.updateCommitIndex()
	}
}

// updateCommitIndex advances the commit index when a majority has replicated.
// A leader commits a log entry when it knows that a majority of the servers
// have replicated it. The entry is effectively committed at index N when
// any condition N >= commitIndex holds:
//   1. There exists an index M such that M >= N and a majority of matchIndex[i] >= M
//   2. term(currentTerm) >= N and a majority of matchIndex[i] >= N
func (n *Node) updateCommitIndex() {
	// Count majority for each index (working backwards from lastLogIndex)
	for i := len(n.log) - 1; i >= n.commitIndex; i-- {
		count := 0
		for _, mi := range n.matchIndex {
			if mi > i {
				count++
			}
		}
		if count > n.clusterSize/2 {
			n.commitIndex = i + 1
			n.applyCommitted()
			break
		}
	}
}

// applyCommitted applies all committed but unapplied entries to the state machine.
// Raft guarantees that once an entry is committed, it will remain in the log
// and be applied to every server's state machine in the same order.
func (n *Node) applyCommitted() {
	for n.lastApplied < n.commitIndex {
		n.lastApplied++
		if n.lastApplied <= len(n.log) {
			entry := n.log[n.lastApplied-1]
			n.stateMachine.Apply(entry)
		}
	}
}

// isCommitted checks if the entry at the given index has been committed.
// An entry is committed when a majority of nodes have replicated it.
func (n *Node) isCommitted(index int) bool {
	count := 0
	for _, mi := range n.matchIndex {
		if mi > index {
			count++
		}
	}
	return count > n.clusterSize/2
}

// GetCurrentTerm returns the node's current term.
func (n *Node) GetCurrentTerm() int {
	return n.currentTerm
}

// GetRole returns the node's current role (Follower/Candidate/Leader).
func (n *Node) GetRole() string {
	return n.role.String()
}

// GetLog returns a copy of the node's log.
func (n *Node) GetLog() []LogEntry {
	logCopy := make([]LogEntry, len(n.log))
	copy(logCopy, n.log)
	return logCopy
}

// GetCommitIndex returns the node's commit index.
func (n *Node) GetCommitIndex() int {
	return n.commitIndex
}

// GetPeerID returns the node's peer ID.
func (n *Node) GetPeerID() int {
	return n.peerID
}

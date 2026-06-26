package raft

import (
	"fmt"
	"log"
	"math/rand"
	"sync"
	"time"
)

// ElectionTimeout generates a randomized election timeout.
// Raft uses randomized timeouts to minimize the possibility of
// split votes. By choosing a timeout uniformly at random from
// a fixed interval (e.g., 150-300ms), nodes are likely to
// time out at different times, allowing one node to win the
// election before others trigger their own elections.
func ElectionTimeout(minMs, maxMs int) time.Duration {
	timeout := minMs + rand.Intn(maxMs-minMs)
	return time.Duration(timeout) * time.Millisecond
}

// StartElection begins a new election on this node.
//
// Election process:
//   1. Increment currentTerm
//   2. Transition to Candidate state
//   3. Vote for self
//   4. Request votes from all peers via RequestVote RPC
//
// A node wins the election if it receives votes from a majority
// of the cluster. If it wins, it becomes the Leader.
//
// Election Restriction (Safety):
//   A node will only grant a vote if:
//     - The candidate's term >= current term
//     - The candidate's log is at least as up-to-date as the voter's
//
// This ensures that a candidate can only win if it has all
// committed entries.
func (n *Node) StartElection() bool {
	n.currentTerm++
	n.votedFor = n.peerID
	n.role = Candidate
	n.votesReceived = make(map[int]bool)
	n.votesReceived[n.peerID] = true

	log.Printf("[RAFT] Node %d starts election for term %d", n.peerID, n.currentTerm)

	// Request votes from all peers
	// In production, this would be async RPC calls
	votesNeeded := n.clusterSize/2 + 1 // Majority

	for peerID := range n.peers {
		if peerID == n.peerID {
			continue
		}

		// Send RequestVote RPC (simulated)
		voteGranted := n.requestVote(peerID)
		if voteGranted {
			n.votesReceived[peerID] = true
			log.Printf("[RAFT] Node %d received vote from peer %d for term %d", n.peerID, peerID, n.currentTerm)
		} else {
			log.Printf("[RAFT] Node %d rejected vote from peer %d for term %d", n.peerID, peerID, n.currentTerm)
		}
	}

	// Check if we won the election
	if len(n.votesReceived) >= votesNeeded {
		n.becomeLeader()
		return true
	}

	return false
}

// requestVote handles a RequestVote RPC from a candidate.
//
// A follower/grant vote if:
//   1. Candidate's term >= current term
//   2. Follower has not voted for anyone else in this term, OR
//      has already voted for this candidate
//   3. Candidate's log is at least as up-to-date as the follower's
//
// Log up-to-date check:
//   - Higher term log wins
//   - If same term, longer log wins
//   - Equal logs are considered up-to-date
func (n *Node) requestVote(candidateID int, candidateTerm int, candidateLastLogIndex int, candidateLastLogTerm int) bool {
	// Reject if candidate's term is less than current term
	if candidateTerm < n.currentTerm {
		return false
	}

	// Check if we've already voted in this term
	if n.votedFor != -1 && n.votedFor != candidateID && n.currentTerm == candidateTerm {
		return false
	}

	// Check if candidate's log is at least as up-to-date
	if !n.isLogUpToDate(candidateLastLogIndex, candidateLastLogTerm) {
		return false
	}

	// Grant the vote
	n.votedFor = candidateID
	n.currentTerm = candidateTerm // Update term if candidate's term is higher
	log.Printf("[RAFT] Node %d voted for Node %d in term %d", n.peerID, candidateID, candidateTerm)
	return true
}

// isLogUpToDate checks if the candidate's log is at least as up-to-date as this node's log.
//
// A log is considered more up-to-date if:
//   1. The last entry has a higher term
//   2. The last entries have the same term and the log is longer
//
// This is critical for the Election Restriction property: it ensures
// that a candidate that wins an election has all committed entries.
func (n *Node) isLogUpToDate(candidateLastLogIndex, candidateLastLogTerm int) bool {
	if len(n.log) == 0 {
		return true
	}
	myLastTerm := n.log[len(n.log)-1].Term
	myLastIndex := len(n.log)

	if candidateLastLogTerm != myLastTerm {
		return candidateLastLogTerm > myLastTerm
	}
	return candidateLastLogIndex >= myLastIndex
}

// becomeLeader transitions this node to the Leader role.
//
// When a node becomes leader, it must:
//   1. Send initial empty AppendEntries RPCs (heartbeats) to all servers
//      to prevent followers from triggering elections
//   2. Initialize nextIndex and matchIndex for each server
//   3. Begin processing client requests
//
// The leader must handle all client requests and replicate log entries.
// If the leader fails during replication, the election mechanism will
// select a new leader, who will then complete replication.
func (n *Node) becomeLeader() {
	n.role = Leader
	n.nextIndex = make(map[int]int)
	n.matchIndex = make(map[int]int)

	// Initialize nextIndex to one past the end of the log
	// The leader will start by sending empty heartbeats, then
	// the actual log entries
	for peerID := range n.peers {
		n.nextIndex[peerID] = len(n.log) + 1
		n.matchIndex[peerID] = 0
	}

	log.Printf("[RAFT] Node %d became Leader for term %d", n.peerID, n.currentTerm)

	// Send initial heartbeats to all followers
	// This is critical: it prevents followers from triggering
	// elections while the new leader is still sending heartbeats
	n.sendHeartbeats()
}

// sendHeartbeats sends AppendEntries RPCs (heartbeats) to all peers.
// Heartbeats serve two purposes:
//   1. Prevent election timeouts on followers (keeping the leader in power)
//   2. Enable log replication (AppendEntries carries log entries)
//
// The heartbeat includes:
//   - term: Leader's current term
//   - leaderID: Leader's peer ID
//   - prevLogIndex: Index of log entry immediately preceding new ones
//   - prevLogTerm: Term of prevLogEntry
//   - entries[]: Log entries to be stored (empty for heartbeat)
//   - leaderCommit: Leader's commitIndex
func (n *Node) sendHeartbeats() {
	for peerID := range n.peers {
		if peerID == n.peerID {
			continue
		}
		n.appendEntries(peerID)
	}
}

// appendEntries sends an AppendEntries RPC to a follower.
//
// The follower responds with:
//   - success: true if prevLogIndex and prevLogTerm are valid
//   - failure: false otherwise
//
// On success, the leader increments nextIndex and matchIndex.
// On failure, the leader decrements nextIndex and retries.
//
// The follower checks:
//   1. If term >= currentTerm, reject (leader is outdated)
//   2. If prevLog is inconsistent, reject
//   3. If an existing entry conflicts with a new one, delete self and below
//   4. Append any new entries not already in the log
func (n *Node) appendEntries(peerID int) bool {
	// In production, this would be an actual RPC call
	// For simulation, we assume the RPC succeeds
	nextIdx := n.nextIndex[peerID]

	// Check if there are entries to send
	if nextIdx > len(n.log)+1 {
		return false
	}

	// Simulate successful AppendEntries
	n.matchIndex[peerID] = nextIdx - 1
	n.nextIndex[peerID] = nextIdx

	// Check for commit
	n.updateCommitIndex()

	return true
}

// handleRequestVoteResponse processes a response to a RequestVote RPC.
// This is called when a candidate receives a vote response.
func (n *Node) handleRequestVoteResponse(peerID int, voteGranted bool) {
	if n.role != Candidate {
		return
	}

	if voteGranted {
		n.votesReceived[peerID] = true
		votesNeeded := n.clusterSize/2 + 1
		if len(n.votesReceived) >= votesNeeded {
			n.becomeLeader()
		}
	} else {
		delete(n.votesReceived, peerID)
	}
}

// handleAppendEntriesResponse processes a response to an AppendEntries RPC.
// This is called when a leader receives a response from a follower.
func (n *Node) handleAppendEntriesResponse(peerID int, success bool) {
	if n.role != Leader {
		return
	}

	if success {
		n.matchIndex[peerID] = n.nextIndex[peerID] - 1
		n.nextIndex[peerID]++
		n.updateCommitIndex()
	} else {
		// Decrement nextIndex and retry
		if n.nextIndex[peerID] > 1 {
			n.nextIndex[peerID]--
		}
	}
}

// Package raft implements the Raft consensus algorithm.
//
// Raft is a consensus algorithm designed as an alternative to Paxos.
// Raft defines three node states: Follower, Candidate, and Leader.
//
// Core Loop:
//   Leader Election → Log Replication → Safety → Membership Changes
//
// The algorithm works through these phases:
//   1. Leader Election: Nodes elect a leader via voting
//   2. Log Replication: Leader replicates log entries to followers
//   3. Safety: Ensure consistency during failures
//   4. Membership Changes: Add/remove nodes from the cluster
//
// Key Concepts:
//   - Term: Logical clock that increases monotonically
//   - Vote: Each node can vote for one candidate per term
//   - Log Entry: (term, command) pair stored on all nodes
//   - Commit Index: Highest log entry known to be committed
//   - Leader Complete: Leader must have all entries from previous term committed
//
// Safety Properties:
//   - Election Restriction: Candidate must have all committed entries
//   - Log Matching: If two logs have same index and term, they are identical above
//   - Leader Append-Only: Leader never overwrites/deletes its own log entries
package raft

// StateRole represents the role of a Raft node
type StateRole int

const (
	Follower StateRole = iota
	Candidate
	Leader
)

func (r StateRole) String() string {
	switch r {
	case Follower:
		return "Follower"
	case Candidate:
		return "Candidate"
	case Leader:
		return "Leader"
	default:
		return "Unknown"
	}
}

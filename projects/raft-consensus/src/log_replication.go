package raft

import (
	"fmt"
	"log"
)

// LogReplication manages log replication from leader to followers.
//
// Raft's log replication works as follows:
//   1. Client sends request to leader
//   2. Leader appends entry to its log
//   3. Leader sends AppendEntries RPC with the entry to all followers
//   4. Followers append the entry to their logs
//   5. Leader replicates until majority acknowledges
//   6. Leader commits the entry and applies to state machine
//
// Key invariant: If a log entry is committed, then every log in the
// cluster will contain that entry.
//
// Log Matching Property:
//   If two log entries have the same term and index, then they store
//   the same command. Furthermore, if two logs contain an entry with
//   the same term and index, then the logs are identical in all
//   entries up through the given index.
type LogReplication struct {
	// Leader's nextIndex for each follower
	nextIndex map[int]int

	// Leader's matchIndex for each follower
	matchIndex map[int]int

	// Cluster size for majority calculation
	clusterSize int
}

// NewLogReplication creates a new log replication manager.
func NewLogReplication(clusterSize int) *LogReplication {
	return &LogReplication{
		nextIndex:   make(map[int]int),
		matchIndex:  make(map[int]int),
		clusterSize: clusterSize,
	}
}

// ReplicateEntry replicates a log entry to followers.
// Returns true if the entry was committed by a majority.
func (lr *LogReplication) ReplicateEntry(entry LogEntry, leaderLog []LogEntry) bool {
	// Leader has the entry
	leaderIdx := len(leaderLog)
	lr.matchIndex[0] = leaderIdx // Using 0 as leader's own index

	// In production, would send AppendEntries RPC to each follower
	// For simulation, we track what would happen:

	// Count how many nodes have this entry (including leader)
	count := 1
	for peerID := range lr.nextIndex {
		if peerID == 0 {
			continue
		}
		// Simulate successful replication
		lr.matchIndex[peerID] = leaderIdx
		lr.nextIndex[peerID] = leaderIdx + 1
		count++
	}

	// Check if majority has replicated
	return count > lr.clusterSize/2
}

// UpdateNextIndex updates the nextIndex for a follower after AppendEntries.
// On success: nextIndex++
// On failure: nextIndex--
func (lr *LogReplication) UpdateNextIndex(peerID int, success bool) {
	if success {
		lr.nextIndex[peerID]++
	} else {
		if lr.nextIndex[peerID] > 1 {
			lr.nextIndex[peerID]--
		}
	}
}

// UpdateMatchIndex updates the matchIndex for a follower.
func (lr *LogReplication) UpdateMatchIndex(peerID, index int) {
	lr.matchIndex[peerID] = index
}

// GetCommitIndex calculates the highest committed log index.
// An entry at index N is committed if there exists M >= N such that
// a majority of matchIndex[i] >= M.
func (lr *LogReplication) GetCommitIndex() int {
	// Work backwards from the highest known index
	for i := 10000; i >= 0; i-- {
		count := 0
		for _, mi := range lr.matchIndex {
			if mi >= i {
				count++
			}
		}
		if count > lr.clusterSize/2 {
			return i
		}
	}
	return 0
}

// CheckLogConsistency verifies the log matching property.
// If two logs have the same index and term, they should be identical.
func (lr *LogReplication) CheckLogConsistency(logA, logB []LogEntry, index int) bool {
	if index <= 0 || index > len(logA) || index > len(logB) {
		return false
	}

	// Check if entries at the same index have the same term
	entryA := logA[index-1]
	entryB := logB[index-1]

	if entryA.Term == entryB.Term {
		// Same term means same command (Log Matching Property)
		return entryA.Command == entryB.Command
	}

	return true
}

// FindLeaderConsistency checks if the leader's log is consistent with followers.
// The leader's log must contain all committed entries.
func (lr *LogReplication) FindLeaderConsistency(leaderLog []LogEntry, followerLogs map[int][]LogEntry) bool {
	// Check that leader's committed entries exist in all followers
	commitIdx := lr.GetCommitIndex()

	for _, followerLog := range followerLogs {
		if commitIdx > len(followerLog) {
			return false
		}
		for i := 0; i < commitIdx; i++ {
			if leaderLog[i].Command != followerLog[i].Command {
				return false
			}
		}
	}

	return true
}

// BuildAppendEntriesPayload constructs the payload for an AppendEntries RPC.
func (lr *LogReplication) BuildAppendEntriesPayload(leaderLog []LogEntry, peerID int) (prevLogIndex, prevLogTerm int, entries []LogEntry) {
	nextIdx := lr.nextIndex[peerID]

	if nextIdx <= 1 {
		prevLogIndex = 0
		prevLogTerm = 0
	} else if nextIdx-1 <= len(leaderLog) {
		prevLogIndex = nextIdx - 1
		prevLogTerm = leaderLog[prevLogIndex-1].Term
	} else {
		prevLogIndex = len(leaderLog)
		prevLogTerm = leaderLog[len(leaderLog)-1].Term
	}

	// Send entries starting from nextIndex
	if nextIdx <= len(leaderLog) {
		entries = leaderLog[nextIdx-1:]
	}

	return
}

// FormatAppendEntries formats an AppendEntries message for logging/debugging.
func FormatAppendEntries(peerID int, prevLogIndex, prevLogTerm int, entries []LogEntry, leaderCommit int) string {
	return fmt.Sprintf("AppendEntries(peer=%d, prevLogIndex=%d, prevLogTerm=%d, entries=%d, leaderCommit=%d)",
		peerID, prevLogIndex, prevLogTerm, len(entries), leaderCommit)
}

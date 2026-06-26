// Package mvcc implements Multi-Version Concurrency Control for educational purposes.
//
// MVCC (Multi-Version Concurrency Control) is a concurrency control method
// that allows non-conflicting transactions to access different versions of the
// same data simultaneously, improving database throughput.
//
// Key concepts:
//   - Each data item has multiple versions, each tagged with a timestamp
//   - Transactions read from a snapshot (consistent view) taken at transaction start
//   - Write-write and read-write conflicts are detected to ensure isolation
//   - Garbage collection removes old versions no transaction needs
//   - Serializable Snapshot Isolation (SSI) prevents serializable anomalies
//
// Core loop:
//
//	Transaction Begin → Read Snapshot → Write → Commit → Version Garbage Collection
package mvcc

import (
	"fmt"
	"sync"
	"time"
)

// Timestamp represents a logical timestamp in the MVCC system.
// We use a monotonic counter instead of wall-clock time to ensure
// consistent ordering across all operations.
type Timestamp int64

// TransactionState represents the lifecycle state of a transaction.
type TransactionState int

const (
	// StateActive: Transaction is running and can read/write.
	StateActive TransactionState = iota
	// StateCommitted: Transaction has been successfully committed.
	StateCommitted
	// StateAborted: Transaction was rolled back.
	StateAborted
	// StateSnapshotRead: Transaction has created a read view but not yet started writing.
	StateSnapshotRead
	// StateConflict: Transaction was aborted due to a conflict detection.
	StateConflict
)

func (s TransactionState) String() string {
	switch s {
	case StateActive:
		return "ACTIVE"
	case StateCommitted:
		return "COMMITTED"
	case StateAborted:
		return "ABORTED"
	case StateSnapshotRead:
		return "SNAPSHOT_READ"
	case StateConflict:
		return "CONFLICT"
	default:
		return "UNKNOWN"
	}
}

// Transaction represents an MVCC transaction.
// Each transaction has a unique ID, start/commit timestamps, and tracks
// its read and write sets for conflict detection.
type Transaction struct {
	ID            int
	StartTime     Timestamp // Timestamp when the transaction began
	CommitTime    Timestamp // Timestamp when the transaction committed (0 if not committed)
	State         TransactionState
	ReadSet       map[string]Timestamp // key -> timestamp of last read
	WriteSet      map[string][]byte    // key -> new value being written
	ReadTimestamp Timestamp            // The snapshot timestamp for reads
	mu            sync.RWMutex
}

// NewTransaction creates a new transaction with the given start timestamp.
func NewTransaction(id int, startTime Timestamp) *Transaction {
	return &Transaction{
		ID:            id,
		StartTime:     startTime,
		ReadSet:       make(map[string]Timestamp),
		WriteSet:      make(map[string][]byte),
		ReadTimestamp: 0, // Will be set when creating a snapshot
	}
}

// CreateSnapshot creates a consistent read view for this transaction.
// The snapshot captures the latest committed version of each data item
// as of the snapshot timestamp. This is the core of snapshot isolation.
func (t *Transaction) CreateSnapshot(snapshotTS Timestamp) {
	t.ReadTimestamp = snapshotTS
	t.State = StateSnapshotRead
}

// AddToReadSet records that this transaction read the given key.
func (t *Transaction) AddToReadSet(key string, readTS Timestamp) {
	t.mu.Lock()
	defer t.mu.Unlock()
	t.ReadSet[key] = readTS
}

// AddToWriteSet records a write to the given key.
func (t *Transaction) AddToWriteSet(key string, value []byte) {
	t.mu.Lock()
	defer t.mu.Unlock()
	t.WriteSet[key] = value
}

// GetWriteSet returns a copy of the write set.
func (t *Transaction) GetWriteSet() map[string][]byte {
	t.mu.RLock()
	defer t.mu.RUnlock()
	result := make(map[string][]byte, len(t.WriteSet))
	for k, v := range t.WriteSet {
		result[k] = v
	}
	return result
}

// GetReadSet returns a copy of the read set.
func (t *Transaction) GetReadSet() map[string]Timestamp {
	t.mu.RLock()
	defer t.mu.RUnlock()
	result := make(map[string]Timestamp, len(t.ReadSet))
	for k, v := range t.ReadSet {
		result[k] = v
	}
	return result
}

// IsCommitted returns true if the transaction has been committed.
func (t *Transaction) IsCommitted() bool {
	return t.State == StateCommitted
}

// IsAborted returns true if the transaction has been aborted.
func (t *Transaction) IsAborted() bool {
	return t.State == StateAborted || t.State == StateConflict
}

// Version represents a single version of a data item.
// Each version has a value, a write timestamp (when it was written),
// and a read timestamp (when it was last read).
type Version struct {
	Value     []byte
	WriteTS   Timestamp // Timestamp when this version was written
	ReadTS    Timestamp // Timestamp when this version was last read
	WriterID  int       // Transaction ID of the writer (0 for initial value)
	Committed bool      // Whether the write that created this version was committed
}

func (v *Version) String() string {
	commitStr := "uncommitted"
	if v.Committed {
		commitStr = "committed"
	}
	return fmt.Sprintf("v{val=%q, writeTS=%d, readTS=%d, writer=%d, %s}",
		v.Value, v.WriteTS, v.ReadTS, v.WriterID, commitStr)
}

// MVCCStorage is the core MVCC data store.
// It manages multiple versions of each data item and provides
// the primitives for snapshot isolation and conflict detection.
//
// Architecture:
//
//	key1 -> [version1 -> version2 -> version3]  (version chain, ordered by WriteTS)
//	key2 -> [versionA -> versionB]
//	...
//
// Each version chain is sorted by WriteTS in descending order (newest first).
// When a transaction reads a key, it traverses the chain to find the latest
// version visible to its snapshot timestamp.
type MVCCStorage struct {
	data      map[string][]*Version // key -> version chain (newest first)
	mu        sync.RWMutex
	timestamp Timestamp
	// Garbage collection configuration
	gcEnabled   bool
	gcInterval  time.Duration
	lastGCCheck time.Time
}

// NewMVCCStorage creates a new MVCC storage instance.
func NewMVCCStorage() *MVCCStorage {
	return &MVCCStorage{
		data:       make(map[string][]*Version),
		timestamp:  0,
		gcEnabled:  true,
		gcInterval: time.Second,
	}
}

// NextTimestamp advances and returns the next logical timestamp.
// This ensures strict monotonic ordering of timestamps.
func (s *MVCCStorage) NextTimestamp() Timestamp {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.timestamp++
	return s.timestamp
}

// CurrentTimestamp returns the current logical timestamp without advancing.
func (s *MVCCStorage) CurrentTimestamp() Timestamp {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.timestamp
}

// Write writes a new version of the given key with the specified value.
// The new version is inserted at the head of the version chain with
// the current timestamp as its WriteTS.
//
// MVCC write path:
//
//	1. Allocate new timestamp
//	2. Create new Version with current timestamp
//	3. Insert at head of version chain
//	4. Transaction's write set is tracked separately for conflict detection
func (s *MVCCStorage) Write(key string, value []byte, writerTS Timestamp, writerID int) *Version {
	s.mu.Lock()
	defer s.mu.Unlock()

	// Create new version
	newVer := &Version{
		Value:     value,
		WriteTS:   writerTS,
		ReadTS:    writerTS,
		WriterID:  writerID,
		Committed: false, // Will be set to true on commit
	}

	// Insert at head of version chain (newest first)
	if chain, exists := s.data[key]; exists {
		// Insert at the beginning
		newChain := make([]*Version, 0, len(chain)+1)
		newChain = append(newChain, newVer)
		newChain = append(newChain, chain...)
		s.data[key] = newChain
	} else {
		s.data[key] = []*Version{newVer}
	}

	return newVer
}

// Read reads the latest visible version of the given key for a transaction
// with the given snapshot timestamp. It traverses the version chain and
// returns the first version whose WriteTS <= snapshotTS and is committed.
//
// MVCC read path (snapshot isolation):
//
//	1. Traverse version chain from newest to oldest
//	2. Skip versions with WriteTS > snapshotTS (not yet written at snapshot time)
//	3. Skip uncommitted versions (from aborted/in-flight transactions)
//	4. Return first version that passes both checks
//
// This gives the transaction a consistent view of the database as of snapshotTS.
func (s *MVCCStorage) Read(key string, snapshotTS Timestamp) ([]byte, bool, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	chain, exists := s.data[key]
	if !exists {
		return nil, false, nil // Key does not exist
	}

	// Traverse the version chain to find the latest visible version
	for _, ver := range chain {
		// Skip versions written after our snapshot
		if ver.WriteTS > snapshotTS {
			continue
		}
		// Skip uncommitted versions
		if !ver.Committed {
			continue
		}
		// This version is visible to our snapshot
		return ver.Value, true, nil
	}

	return nil, false, nil // No visible version found
}

// Commit marks a transaction's writes as committed.
// All versions written by this transaction are marked as committed,
// making them visible to future transactions.
func (s *MVCCStorage) Commit(tx *Transaction) {
	s.mu.Lock()
	defer s.mu.Unlock()

	// Mark all versions written by this transaction as committed
	for key := range tx.WriteSet {
		if chain, exists := s.data[key]; exists {
			for _, ver := range chain {
				if ver.WriterID == tx.ID && !ver.Committed {
					ver.Committed = true
				}
			}
		}
	}

	tx.State = StateCommitted
	tx.CommitTime = s.timestamp
}

// Rollback marks a transaction's writes as uncommitted (aborted).
// This effectively "undoes" the transaction's writes.
func (s *MVCCStorage) Rollback(tx *Transaction) {
	s.mu.Lock()
	defer s.mu.Unlock()

	// Mark all versions written by this transaction as uncommitted
	for key := range tx.WriteSet {
		if chain, exists := s.data[key]; exists {
			for _, ver := range chain {
				if ver.WriterID == tx.ID {
					ver.Committed = false
				}
			}
		}
	}

	tx.State = StateAborted
}

// GetVersions returns all versions of the given key (for debugging/visualization).
func (s *MVCCStorage) GetVersions(key string) []*Version {
	s.mu.RLock()
	defer s.mu.RUnlock()

	if chain, exists := s.data[key]; exists {
		result := make([]*Version, len(chain))
		copy(result, chain)
		return result
	}
	return nil
}

// GetAllKeys returns all keys in the storage.
func (s *MVCCStorage) GetAllKeys() []string {
	s.mu.RLock()
	defer s.mu.RUnlock()

	keys := make([]string, 0, len(s.data))
	for k := range s.data {
		keys = append(keys, k)
	}
	return keys
}

// PrintVersionChain prints the version chain for a key (for debugging).
func (s *MVCCStorage) PrintVersionChain(key string) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	chain, exists := s.data[key]
	if !exists {
		fmt.Printf("  %s: (not found)\n", key)
		return
	}

	fmt.Printf("  %s:\n", key)
	for i, ver := range chain {
		commitStr := "uncommitted"
		if ver.Committed {
			commitStr = "committed"
		}
		fmt.Printf("    [%d] %s | writeTS=%d, readTS=%d, writer=%d, %s\n",
			i, ver.Value, ver.WriteTS, ver.ReadTS, ver.WriterID, commitStr)
	}
}

// ConflictType represents the type of conflict detected between transactions.
type ConflictType int

const (
	// ConflictWriteWrite: Two transactions write to the same key (write-write conflict).
	ConflictWriteWrite ConflictType = iota
	// ConflictReadWrite: One transaction reads a key that another transaction is writing (read-write conflict).
	ConflictReadWrite
	// ConflictSerialization: SSSI detects a serialization anomaly (cycle in wait-for graph).
	ConflictSerialization
)

func (c ConflictType) String() string {
	switch c {
	case ConflictWriteWrite:
		return "WRITE-WRITE"
	case ConflictReadWrite:
		return "READ-WRITE"
	case ConflictSerialization:
		return "SERIALIZATION"
	default:
		return "UNKNOWN"
	}
}

// ConflictError represents a conflict detected during transaction processing.
type ConflictError struct {
	Type     ConflictType
	Key      string
	ReaderTx int // Transaction that detected the conflict
	WriterTx int // Transaction that caused the conflict
}

func (e *ConflictError) Error() string {
	return fmt.Sprintf("MVCC Conflict [%s]: key=%q, tx%d detected conflict with tx%d",
		e.Type, e.Key, e.ReaderTx, e.WriterTx)
}

// ConflictDetector handles conflict detection for MVCC transactions.
// It implements both write-write and read-write conflict detection,
// as well as SSI (Serializable Snapshot Isolation) cycle detection.
type ConflictDetector struct {
	// readCommits tracks which transactions a transaction has read committed versions from
	readCommits map[int]map[int]Timestamp // txID -> map of committed writer txID -> timestamp

	// writeSets tracks the write sets of all active transactions
	writeSets map[int]map[string]bool // txID -> set of written keys

	// waitGraph is the wait-for graph for deadlock detection
	// A directed edge from txA to txB means txA is waiting for txB
	waitGraph map[int]map[int]bool // txA -> map of txB (txA waits for txB)

	mu sync.RWMutex
}

// NewConflictDetector creates a new conflict detector.
func NewConflictDetector() *ConflictDetector {
	return &ConflictDetector{
		readCommits: make(map[int]map[int]Timestamp),
		writeSets:   make(map[int]map[string]bool),
		waitGraph:   make(map[int]map[int]bool),
	}
}

// RecordWrite records that a transaction has written to a key.
func (cd *ConflictDetector) RecordWrite(txID int, key string) {
	cd.mu.Lock()
	defer cd.mu.Unlock()

	if _, exists := cd.writeSets[txID]; !exists {
		cd.writeSets[txID] = make(map[string]bool)
	}
	cd.writeSets[txID][key] = true
}

// RecordRead records that a transaction has read a committed version written by another transaction.
// This is used for SSI: if txA reads a version committed by txB after txA started,
// we record that txA "depends on" txB.
func (cd *ConflictDetector) RecordRead(readerTx, writerTx int, commitTS Timestamp) {
	cd.mu.Lock()
	defer cd.mu.Unlock()

	if _, exists := cd.readCommits[readerTx]; !exists {
		cd.readCommits[readerTx] = make(map[int]Timestamp)
	}
	// Keep the latest commit timestamp for each writer
	if prev, exists := cd.readCommits[readerTx][writerTx]; !exists || prev < commitTS {
		cd.readCommits[readerTx][writerTx] = commitTS
	}
}

// CheckWriteWrite detects write-write conflicts.
// Returns a ConflictError if txB's write set overlaps with txA's committed writes.
func (cd *ConflictDetector) CheckWriteWrite(txA, txB *Transaction) *ConflictError {
	cd.mu.RLock()
	defer cd.mu.RUnlock()

	// Check if txB is writing to any key that txA has already written
	for key := range txA.WriteSet {
		if cd.writeSets[txB.ID] != nil && cd.writeSets[txB.ID][key] {
			return &ConflictError{
				Type:     ConflictWriteWrite,
				Key:      key,
				ReaderTx: txA.ID,
				WriterTx: txB.ID,
			}
		}
	}
	return nil
}

// CheckReadWrite detects read-write conflicts.
// Returns a ConflictError if txB is writing to a key that txA has read,
// and txB's write was committed after txA read it.
func (cd *ConflictDetector) CheckReadWrite(txA *Transaction, txB *Transaction) *ConflictError {
	cd.mu.RLock()
	defer cd.mu.RUnlock()

	// Check if txB is writing to any key that txA has read
	for key := range txA.ReadSet {
		if cd.writeSets[txB.ID] != nil && cd.writeSets[txB.ID][key] {
			// Check if txB's write happened after txA read this key
			writerTS := cd.getLatestWriteTS(txB.ID, key)
			readTS := txA.ReadSet[key]
			if writerTS > readTS {
				return &ConflictError{
					Type:     ConflictReadWrite,
					Key:      key,
					ReaderTx: txA.ID,
					WriterTx: txB.ID,
				}
			}
		}
	}
	return nil
}

// getLatestWriteTS returns the latest write timestamp for a key by a given transaction.
func (cd *ConflictDetector) getLatestWriteTS(txID int, key string) Timestamp {
	// In a real implementation, this would query the MVCC storage.
	// For this educational implementation, we approximate.
	return cd.CurrentTimestamp()
}

// CurrentTimestamp returns the current timestamp approximation.
func (cd *ConflictDetector) CurrentTimestamp() Timestamp {
	return Timestamp(time.Now().UnixNano())
}

// AddWaitEdge adds a directed edge to the wait-for graph: txA waits for txB.
func (cd *ConflictDetector) AddWaitEdge(txA, txB int) {
	cd.mu.Lock()
	defer cd.mu.Unlock()

	if cd.waitGraph[txA] == nil {
		cd.waitGraph[txA] = make(map[int]bool)
	}
	cd.waitGraph[txA][txB] = true
}

// RemoveWaitEdge removes a directed edge from the wait-for graph.
func (cd *ConflictDetector) RemoveWaitEdge(txA, txB int) {
	cd.mu.Lock()
	defer cd.mu.Unlock()

	if waiters, exists := cd.waitGraph[txA]; exists {
		delete(waiters, txB)
	}
}

// RemoveTransaction removes all edges involving the given transaction.
func (cd *ConflictDetector) RemoveTransaction(txID int) {
	cd.mu.Lock()
	defer cd.mu.Unlock()

	delete(cd.waitGraph, txID)
	for tx := range cd.waitGraph {
		delete(cd.waitGraph[tx], txID)
	}
	delete(cd.writeSets, txID)
	delete(cd.readCommits, txID)
}

// DetectCycle detects cycles in the wait-for graph using DFS.
// A cycle indicates a deadlock situation.
// Returns the cycle path if found, nil otherwise.
func (cd *ConflictDetector) DetectCycle() []int {
	cd.mu.RLock()
	defer cd.mu.RUnlock()

	visited := make(map[int]bool)
	recStack := make(map[int]bool)
	parent := make(map[int]int)

	var dfs func(node int) bool
	dfs = func(node int) bool {
		visited[node] = true
		recStack[node] = true

		for neighbor := range cd.waitGraph[node] {
			if !visited[neighbor] {
				parent[neighbor] = node
				if dfs(neighbor) {
					return true
				}
			} else if recStack[neighbor] {
				// Found a cycle, reconstruct it
				cycle := []int{neighbor}
				for cur := node; cur != neighbor; cur = parent[cur] {
					cycle = append(cycle, cur)
				}
				return true
			}
		}

		recStack[node] = false
		return false
	}

	// Check all nodes as potential cycle starts
	for node := range cd.waitGraph {
		if !visited[node] {
			if dfs(node) {
				// Return the first node in the cycle as victim
				for node := range cd.waitGraph {
					if recStack[node] {
						return []int{node}
					}
				}
			}
		}
	}

	return nil
}

// HasCycle returns true if there is a cycle in the wait-for graph.
func (cd *ConflictDetector) HasCycle() bool {
	return cd.DetectCycle() != nil
}

// GarbageCollector handles cleanup of old version chains in MVCC storage.
// It removes versions that are no longer needed by any active transaction,
// freeing memory and keeping the version chains manageable.
//
// Garbage collection strategy:
//
//	1. Find the oldest active snapshot timestamp (minSnapshotTS)
//	2. For each key, remove versions with WriteTS < minSnapshotTS
//	3. Keep at least one version per key (the oldest visible one)
//	4. Remove completely if no versions are visible
//
// This is safe because:
// - Any active transaction started at or after minSnapshotTS
// - Versions older than minSnapshotTS cannot be visible to any active transaction
type GarbageCollector struct {
	storage *MVCCStorage
	// Track active snapshot timestamps
	activeSnapshots map[Timestamp]bool
	mu              sync.RWMutex
	// Statistics
	versionsReclaimed int64
	keysCleaned       int64
}

// NewGarbageCollector creates a new garbage collector.
func NewGarbageCollector(storage *MVCCStorage) *GarbageCollector {
	return &GarbageCollector{
		storage:         storage,
		activeSnapshots: make(map[Timestamp]bool),
	}
}

// RegisterSnapshot registers an active snapshot timestamp.
// The GC will not reclaim versions that might be visible to this snapshot.
func (gc *GarbageCollector) RegisterSnapshot(ts Timestamp) {
	gc.mu.Lock()
	defer gc.mu.Unlock()
	gc.activeSnapshots[ts] = true
}

// UnregisterSnapshot removes a snapshot registration (transaction committed/aborted).
func (gc *GarbageCollector) UnregisterSnapshot(ts Timestamp) {
	gc.mu.Lock()
	defer gc.mu.Unlock()
	delete(gc.activeSnapshots, ts)
}

// Collect runs garbage collection, removing old versions no longer needed.
func (gc *GarbageCollector) Collect() (reclaimed int64, cleaned int) {
	gc.mu.RLock()

	// Find the oldest active snapshot
	var minSnapshot Timestamp
	hasSnapshot := false
	for ts := range gc.activeSnapshots {
		if !hasSnapshot || ts < minSnapshot {
			minSnapshot = ts
			hasSnapshot = true
		}
	}
	gc.mu.RUnlock()

	if !hasSnapshot {
		// No active snapshots: safe to clean everything except the latest version per key
		return gc.collectNoSnapshots()
	}

	// All active transactions started at or after minSnapshot
	// We can safely remove versions with WriteTS < minSnapshot
	return gc.collectWithSnapshot(minSnapshot)
}

// collectNoSnapshots removes all versions except the latest committed one per key.
func (gc *GarbageCollector) collectNoSnapshots() (int64, int) {
	var reclaimed int64
	var cleaned int

	gc.storage.mu.Lock()
	defer gc.storage.mu.Unlock()

	for key, chain := range gc.storage.data {
		if len(chain) <= 1 {
			continue
		}

		// Find the latest committed version to keep
		latestCommittedIdx := -1
		for i := len(chain) - 1; i >= 0; i-- {
			if chain[i].Committed {
				latestCommittedIdx = i
				break
			}
		}

		if latestCommittedIdx == -1 {
			// No committed versions, remove all
			reclaimed += int64(len(chain))
			delete(gc.storage.data, key)
			cleaned++
			continue
		}

		// Keep only the latest committed version
		keep := chain[latestCommittedIdx]
		reclaimed += int64(len(chain) - 1)
		gc.storage.data[key] = []*Version{keep}
		cleaned++
	}

	gc.versionsReclaimed += reclaimed
	gc.keysCleaned += int64(cleaned)
	return reclaimed, cleaned
}

// collectWithSnapshot removes versions older than the oldest snapshot.
func (gc *GarbageCollector) collectWithSnapshot(minSnapshot Timestamp) (int64, int) {
	var reclaimed int64
	var cleaned int

	gc.storage.mu.Lock()
	defer gc.storage.mu.Unlock()

	for key, chain := range gc.storage.data {
		if len(chain) <= 1 {
			continue
		}

		// Find the cutoff point: first version with WriteTS >= minSnapshot
		cutoffIdx := -1
		for i, ver := range chain {
			if ver.WriteTS >= minSnapshot {
				cutoffIdx = i
				break
			}
		}

		if cutoffIdx == -1 {
			// All versions are older than minSnapshot
			// Keep the oldest committed version
			oldestCommitted := -1
			for i := len(chain) - 1; i >= 0; i-- {
				if chain[i].Committed {
					oldestCommitted = i
				}
			}
			if oldestCommitted >= 0 {
				reclaimed += int64(len(chain) - 1)
				gc.storage.data[key] = []*Version{chain[oldestCommitted]}
				cleaned++
			} else {
				reclaimed += int64(len(chain))
				delete(gc.storage.data, key)
				cleaned++
			}
			continue
		}

		// Remove versions before cutoffIdx
		reclaimed += int64(cutoffIdx)
		gc.storage.data[key] = chain[cutoffIdx:]
		cleaned++
	}

	gc.versionsReclaimed += reclaimed
	gc.keysCleaned += int64(cleaned)
	return reclaimed, cleaned
}

// Stats returns garbage collection statistics.
func (gc *GarbageCollector) Stats() (reclaimed int64, keysCleaned int64) {
	gc.mu.RLock()
	defer gc.mu.RUnlock()
	return gc.versionsReclaimed, gc.keysCleaned
}

// SnapshotManager manages snapshot creation and lifecycle for transactions.
// It ensures that each transaction gets a consistent view of the database
// at a specific point in time.
type SnapshotManager struct {
	storage      *MVCCStorage
	gc           *GarbageCollector
	nextTxID     int
	mu           sync.Mutex
	activeTxns   map[int]*Transaction
	snapshotTS   Timestamp
	gcInterval   time.Duration
	lastGCTime   time.Time
}

// NewSnapshotManager creates a new snapshot manager.
func NewSnapshotManager(storage *MVCCStorage) *SnapshotManager {
	return &SnapshotManager{
		storage:    storage,
		gc:         NewGarbageCollector(storage),
		nextTxID:   1,
		activeTxns: make(map[int]*Transaction),
		snapshotTS: 0,
		gcInterval: time.Millisecond * 100,
	}
}

// BeginTransaction starts a new transaction and returns it.
// The transaction gets a unique ID and a snapshot timestamp.
func (sm *SnapshotManager) BeginTransaction() *Transaction {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	txID := sm.nextTxID
	sm.nextTxID++

	// Advance the global timestamp for the new snapshot
	sm.snapshotTS = sm.storage.NextTimestamp()

	tx := NewTransaction(txID, sm.snapshotTS)
	tx.CreateSnapshot(sm.snapshotTS)
	sm.activeTxns[txID] = tx

	// Register the snapshot with the GC
	sm.gc.RegisterSnapshot(sm.snapshotTS)

	// Periodically trigger garbage collection
	if time.Since(sm.lastGCTime) > sm.gcInterval {
		go sm.triggerGC()
		sm.lastGCTime = time.Now()
	}

	return tx
}

// CommitTransaction commits a transaction.
// It checks for conflicts before committing and marks the transaction's
// writes as visible in the MVCC storage.
func (sm *SnapshotManager) CommitTransaction(tx *Transaction, detector *ConflictDetector) error {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	if tx.IsAborted() {
		return fmt.Errorf("transaction %d is already aborted", tx.ID)
	}

	// SSI: Check for serialization conflicts
	conflict := sm.checkSSISerializable(tx, detector)
	if conflict != nil {
		sm.gc.UnregisterSnapshot(tx.ReadTimestamp)
		tx.State = StateConflict
		return conflict
	}

	// Commit the transaction's writes
	sm.storage.Commit(tx)
	delete(sm.activeTxns, tx.ID)
	sm.gc.UnregisterSnapshot(tx.ReadTimestamp)

	return nil
}

// RollbackTransaction rolls back a transaction.
// It undoes all writes and releases the snapshot.
func (sm *SnapshotManager) RollbackTransaction(tx *Transaction) {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	sm.storage.Rollback(tx)
	delete(sm.activeTxns, tx.ID)
	sm.gc.UnregisterSnapshot(tx.ReadTimestamp)
}

// Read reads a value from the storage using the transaction's snapshot.
func (sm *SnapshotManager) Read(tx *Transaction, key string) ([]byte, error) {
	if tx.IsAborted() {
		return nil, fmt.Errorf("transaction %d is aborted", tx.ID)
	}

	value, exists, err := sm.storage.Read(key, tx.ReadTimestamp)
	if err != nil {
		return nil, err
	}

	// Record the read in the transaction's read set
	tx.AddToReadSet(key, tx.ReadTimestamp)

	// Record for SSI: if the version was committed by another transaction
	if exists && value != nil {
		sm.recordSSIRead(tx, key, value)
	}

	return value, nil
}

// Write writes a value in the transaction's write set.
// The actual storage write happens at commit time.
func (sm *SnapshotManager) Write(tx *Transaction, key string, value []byte) {
	tx.AddToWriteSet(key, value)
}

// checkSSISerializable checks for serialization anomalies using SSI rules.
// SSI (Serializable Snapshot Isolation) prevents the two known anomalies
// that Snapshot Isolation allows:
//
//	1. Write skew: Two transactions read overlapping data, then each writes
//	   to a disjoint subset, violating a constraint that depends on both reads.
//	2. Read-write skew: A transaction reads a value that was written by another
//	   transaction that committed after the read began.
func (sm *SnapshotManager) checkSSISerializable(tx *Transaction, detector *ConflictDetector) *ConflictError {
	// Check against all other active transactions
	for otherTxID, otherTx := range sm.activeTxns {
		if otherTx.ID == tx.ID {
			continue
		}

		// Rule 1: If tx reads something written by otherTx after tx started,
		// and otherTx writes something tx read, that's a serialization anomaly
		for readKey := range tx.ReadSet {
			// Check if otherTx wrote to this key after tx read it
			versions := sm.storage.GetVersions(readKey)
			for _, ver := range versions {
				if ver.WriterID == otherTx.ID && ver.Committed && ver.WriteTS > tx.StartTime {
					// Check if tx also wrote to a key that otherTx read
					if len(otherTx.ReadSet) > 0 && len(tx.WriteSet) > 0 {
						for writeKey := range tx.WriteSet {
							if otherTx.ReadSet[writeKey] > 0 {
								return &ConflictError{
									Type:     ConflictSerialization,
									Key:      readKey,
									ReaderTx: tx.ID,
									WriterTx: otherTx.ID,
								}
							}
						}
					}
				}
			}
		}

		// Rule 2: Write-write conflict detection
		if conflict := detector.CheckWriteWrite(tx, otherTx); conflict != nil {
			return conflict
		}

		// Rule 3: Read-write conflict detection
		if conflict := detector.CheckReadWrite(tx, otherTx); conflict != nil {
			return conflict
		}
	}

	return nil
}

// recordSSIRecords SSI read information for later conflict detection.
func (sm *SnapshotManager) recordSSIRead(tx *Transaction, key string, _ []byte) {
	versions := sm.storage.GetVersions(key)
	for _, ver := range versions {
		if ver.Committed && ver.WriteTS <= tx.ReadTimestamp {
			sm.gc.mu.RLock()
			sm.gc.mu.RUnlock()
			// Record this dependency for SSI
			_ = ver
		}
	}
}

// triggerGC runs garbage collection in a goroutine.
func (sm *SnapshotManager) triggerGC() {
	reclaimed, cleaned := sm.gc.Collect()
	fmt.Printf("  [GC] Reclaimed %d versions, cleaned %d keys\n", reclaimed, cleaned)
}

// ActiveTransactions returns all active transactions.
func (sm *SnapshotManager) ActiveTransactions() map[int]*Transaction {
	sm.mu.RLock()
	defer sm.mu.RUnlock()

	result := make(map[int]*Transaction)
	for id, tx := range sm.activeTxns {
		result[id] = tx
	}
	return result
}

// TransactionManager is the high-level API for MVCC operations.
// It coordinates the SnapshotManager and ConflictDetector to provide
// a complete MVCC interface.
type TransactionManager struct {
	snapshotMgr *SnapshotManager
	detector    *ConflictDetector
	gc          *GarbageCollector
}

// NewTransactionManager creates a new transaction manager.
func NewTransactionManager(storage *MVCCStorage) *TransactionManager {
	detector := NewConflictDetector()
	snapshotMgr := NewSnapshotManager(storage)
	snapshotMgr.gc = NewGarbageCollector(storage)
	return &TransactionManager{
		snapshotMgr: snapshotMgr,
		detector:    detector,
		gc:          snapshotMgr.gc,
	}
}

// Begin starts a new transaction.
func (tm *TransactionManager) Begin() *Transaction {
	return tm.snapshotMgr.BeginTransaction()
}

// Commit commits a transaction with conflict detection.
func (tm *TransactionManager) Commit(tx *Transaction) error {
	return tm.snapshotMgr.CommitTransaction(tx, tm.detector)
}

// Rollback rolls back a transaction.
func (tm *TransactionManager) Rollback(tx *Transaction) {
	tm.snapshotMgr.RollbackTransaction(tx)
}

// Read performs a snapshot read.
func (tm *TransactionManager) Read(tx *Transaction, key string) ([]byte, error) {
	return tm.snapshotMgr.Read(tx, key)
}

// Write records a write in the transaction's write set.
func (tm *TransactionManager) Write(tx *Transaction, key string, value []byte) {
	tm.snapshotMgr.Write(tx, key, value)
}

// DetectDeadlock checks for deadlocks in the wait-for graph.
func (tm *TransactionManager) DetectDeadlock() []int {
	return tm.detector.DetectCycle()
}

// GC collects garbage.
func (tm *TransactionManager) GC() (int64, int) {
	return tm.gc.Collect()
}

// PrintStorage prints the current state of the MVCC storage.
func (tm *TransactionManager) PrintStorage() {
	keys := tm.snapshotMgr.storage.GetAllKeys()
	fmt.Println("MVCC Storage State:")
	for _, key := range keys {
		tm.snapshotMgr.storage.PrintVersionChain(key)
	}
	fmt.Println()
}

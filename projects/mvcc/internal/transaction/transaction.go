package transaction

import (
	"fmt"
	"sync"
	"sync/atomic"
)

// TxnStatus represents the status of a transaction
type TxnStatus int

const (
	TxnActive    TxnStatus = iota // Transaction is active
	TxnCommitted                  // Transaction has committed
	TxnAborted                    // Transaction has been aborted
)

func (s TxnStatus) String() string {
	switch s {
	case TxnActive:
		return "Active"
	case TxnCommitted:
		return "Committed"
	case TxnAborted:
		return "Aborted"
	default:
		return "Unknown"
	}
}

// WriteRecord tracks a write operation within a transaction
type WriteRecord struct {
	Key      string
	Value    []byte
	IsDelete bool
}

// Transaction represents a single MVCC transaction
type Transaction struct {
	ID              uint64
	StartTimestamp  uint64    // Snapshot timestamp when transaction began
	CommitTimestamp uint64    // Timestamp assigned at commit time (0 until committed)
	Status          TxnStatus
	ReadSet         map[string]uint64    // key -> read timestamp
	WriteSet        map[string]WriteRecord // key -> write record
	mu              sync.RWMutex
}

// NewTransaction creates a new transaction with the given ID and start timestamp
func NewTransaction(id uint64, startTimestamp uint64) *Transaction {
	return &Transaction{
		ID:             id,
		StartTimestamp: startTimestamp,
		Status:         TxnActive,
		ReadSet:        make(map[string]uint64),
		WriteSet:       make(map[string]WriteRecord),
	}
}

// AddRead records a read operation on the given key
func (t *Transaction) AddRead(key string, readTimestamp uint64) {
	t.mu.Lock()
	defer t.mu.Unlock()
	t.ReadSet[key] = readTimestamp
}

// AddWrite records a write operation on the given key
func (t *Transaction) AddWrite(key string, value []byte) {
	t.mu.Lock()
	defer t.mu.Unlock()
	t.WriteSet[key] = WriteRecord{
		Key:   key,
		Value: value,
	}
}

// AddDelete records a delete operation on the given key
func (t *Transaction) AddDelete(key string) {
	t.mu.Lock()
	defer t.mu.Unlock()
	t.WriteSet[key] = WriteRecord{
		Key:      key,
		IsDelete: true,
	}
}

// GetWrite returns the write record for a key if it exists in the write set
func (t *Transaction) GetWrite(key string) (WriteRecord, bool) {
	t.mu.RLock()
	defer t.mu.RUnlock()
	wr, ok := t.WriteSet[key]
	return wr, ok
}

// IsActive returns true if the transaction is still active
func (t *Transaction) IsActive() bool {
	t.mu.RLock()
	defer t.mu.RUnlock()
	return t.Status == TxnActive
}

// String returns a string representation of the transaction
func (t *Transaction) String() string {
	t.mu.RLock()
	defer t.mu.RUnlock()
	return fmt.Sprintf("Txn{ID: %d, StartTS: %d, CommitTS: %d, Status: %s, Reads: %d, Writes: %d}",
		t.ID, t.StartTimestamp, t.CommitTimestamp, t.Status, len(t.ReadSet), len(t.WriteSet))
}

// TransactionManager manages all transactions and provides timestamp allocation
type TransactionManager struct {
	mu               sync.RWMutex
	clock            uint64 // Logical clock for timestamp allocation
	activeTxns       map[uint64]*Transaction // txnID -> Transaction
	committedTxns    map[uint64]*Transaction // txnID -> Transaction (for GC visibility)
	minActiveTS      uint64 // Minimum start timestamp among active transactions
	needsMinRecalc   bool   // Flag to recalculate minActiveTS
}

// NewTransactionManager creates a new transaction manager
func NewTransactionManager() *TransactionManager {
	return &TransactionManager{
		activeTxns:    make(map[uint64]*Transaction),
		committedTxns: make(map[uint64]*Transaction),
	}
}

// AllocateTimestamp atomically increments and returns a new timestamp
func (tm *TransactionManager) AllocateTimestamp() uint64 {
	return atomic.AddUint64(&tm.clock, 1)
}

// CurrentTimestamp returns the current clock value without incrementing
func (tm *TransactionManager) CurrentTimestamp() uint64 {
	return atomic.LoadUint64(&tm.clock)
}

// Begin starts a new transaction and returns it
func (tm *TransactionManager) Begin() *Transaction {
	ts := tm.AllocateTimestamp()
	txn := NewTransaction(ts, ts)

	tm.mu.Lock()
	tm.activeTxns[txn.ID] = txn
	tm.updateMinActiveTS()
	tm.mu.Unlock()

	return txn
}

// Commit commits a transaction with a new commit timestamp
// Returns error if the transaction is not active
func (tm *TransactionManager) Commit(txnID uint64) (uint64, error) {
	tm.mu.Lock()
	defer tm.mu.Unlock()

	txn, ok := tm.activeTxns[txnID]
	if !ok {
		return 0, fmt.Errorf("transaction %d not found or not active", txnID)
	}

	commitTS := tm.AllocateTimestamp()
	txn.CommitTimestamp = commitTS
	txn.Status = TxnCommitted

	// Move from active to committed
	delete(tm.activeTxns, txnID)
	tm.committedTxns[txnID] = txn
	tm.updateMinActiveTS()

	return commitTS, nil
}

// Abort aborts a transaction
func (tm *TransactionManager) Abort(txnID uint64) error {
	tm.mu.Lock()
	defer tm.mu.Unlock()

	txn, ok := tm.activeTxns[txnID]
	if !ok {
		return fmt.Errorf("transaction %d not found or not active", txnID)
	}

	txn.Status = TxnAborted
	delete(tm.activeTxns, txnID)
	tm.updateMinActiveTS()

	return nil
}

// GetTransaction returns a transaction by ID (checks both active and committed)
func (tm *TransactionManager) GetTransaction(txnID uint64) (*Transaction, bool) {
	tm.mu.RLock()
	defer tm.mu.RUnlock()

	if txn, ok := tm.activeTxns[txnID]; ok {
		return txn, true
	}
	if txn, ok := tm.committedTxns[txnID]; ok {
		return txn, true
	}
	return nil, false
}

// IsActive checks if a transaction is still active
func (tm *TransactionManager) IsActive(txnID uint64) bool {
	tm.mu.RLock()
	defer tm.mu.RUnlock()
	_, ok := tm.activeTxns[txnID]
	return ok
}

// ActiveTransactions returns a list of all active transaction IDs
func (tm *TransactionManager) ActiveTransactions() []uint64 {
	tm.mu.RLock()
	defer tm.mu.RUnlock()

	ids := make([]uint64, 0, len(tm.activeTxns))
	for id := range tm.activeTxns {
		ids = append(ids, id)
	}
	return ids
}

// MinActiveTimestamp returns the minimum start timestamp among active transactions
// This is used by the garbage collector to determine safe cleanup points
func (tm *TransactionManager) MinActiveTimestamp() uint64 {
	tm.mu.RLock()
	defer tm.mu.RUnlock()
	return tm.minActiveTS
}

// ActiveCount returns the number of active transactions
func (tm *TransactionManager) ActiveCount() int {
	tm.mu.RLock()
	defer tm.mu.RUnlock()
	return len(tm.activeTxns)
}

// updateMinActiveTS recalculates the minimum active timestamp
// Must be called with tm.mu held
func (tm *TransactionManager) updateMinActiveTS() {
	if len(tm.activeTxns) == 0 {
		tm.minActiveTS = tm.CurrentTimestamp()
		return
	}

	minTS := uint64(^uint64(0)) // Max uint64
	for _, txn := range tm.activeTxns {
		if txn.StartTimestamp < minTS {
			minTS = txn.StartTimestamp
		}
	}
	tm.minActiveTS = minTS
}

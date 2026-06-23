package internal

import (
	"fmt"
	"sync"

	"mvcc/internal/gc"
	"mvcc/internal/store"
	"mvcc/internal/transaction"
)

// MVSSEngine is the main MVCC engine that coordinates store, transactions, and GC
type MVSSEngine struct {
	store *store.Store
	txMgr *transaction.TransactionManager
	gc    *gc.GarbageCollector
}

// NewMVSSEngine creates a new MVCC engine
func NewMVSSEngine() *MVSSEngine {
	s := store.NewStore()
	txMgr := transaction.NewTransactionManager()
	return &MVSSEngine{
		store: s,
		txMgr: txMgr,
	}
}

// NewMVSSEngineWithGC creates a new MVCC engine with garbage collection
func NewMVSSEngineWithGC(gcInterval ...interface{ Duration() }) *MVSSEngine {
	s := store.NewStore()
	txMgr := transaction.NewTransactionManager()
	gcCollector := gc.NewGarbageCollector(s, txMgr, 0)
	return &MVSSEngine{
		store: s,
		txMgr: txMgr,
		gc:    gcCollector,
	}
}

// Store returns the underlying store (for advanced usage)
func (e *MVSSEngine) Store() *store.Store {
	return e.store
}

// TxnManager returns the transaction manager (for advanced usage)
func (e *MVSSEngine) TxnManager() *transaction.TransactionManager {
	return e.txMgr
}

// SetGC sets the garbage collector for the engine
func (e *MVSSEngine) SetGC(g *gc.GarbageCollector) {
	e.gc = g
}

// GC returns the garbage collector
func (e *MVSSEngine) GC() *gc.GarbageCollector {
	return e.gc
}

// Transaction represents an active transaction context with convenience methods
type Transaction struct {
	txn    *transaction.Transaction
	engine *MVSSEngine
	mu     sync.RWMutex
}

// Begin starts a new transaction
func (e *MVSSEngine) Begin() *Transaction {
	txn := e.txMgr.Begin()
	return &Transaction{
		txn:    txn,
		engine: e,
	}
}

// Read reads a value within the transaction's snapshot
// Returns the value and true if found, nil and false if not found
func (t *Transaction) Read(key string) ([]byte, bool) {
	t.mu.RLock()
	defer t.mu.RUnlock()

	if !t.txn.IsActive() {
		return nil, false
	}

	// Check write set first (read-your-own-writes)
	if wr, ok := t.txn.GetWrite(key); ok {
		if wr.IsDelete {
			return nil, false
		}
		return wr.Value, true
	}

	// Read from store at snapshot timestamp
	value, found := t.engine.store.Get(key, t.txn.StartTimestamp)
	if found {
		t.txn.AddRead(key, t.txn.StartTimestamp)
	}
	return value, found
}

// Write writes a value within the transaction
// The write is buffered and only applied on commit
func (t *Transaction) Write(key string, value []byte) error {
	t.mu.Lock()
	defer t.mu.Unlock()

	if !t.txn.IsActive() {
		return fmt.Errorf("transaction %d is not active", t.txn.ID)
	}

	t.txn.AddWrite(key, value)
	return nil
}

// Delete marks a key for deletion within the transaction
func (t *Transaction) Delete(key string) error {
	t.mu.Lock()
	defer t.mu.Unlock()

	if !t.txn.IsActive() {
		return fmt.Errorf("transaction %d is not active", t.txn.ID)
	}

	t.txn.AddDelete(key)
	return nil
}

// Commit validates and commits the transaction
// Performs optimistic concurrency control by checking for write-write conflicts
func (t *Transaction) Commit() error {
	t.mu.Lock()
	defer t.mu.Unlock()

	if !t.txn.IsActive() {
		return fmt.Errorf("transaction %d is not active", t.txn.ID)
	}

	// Validate: check for write-write conflicts
	for key := range t.txn.WriteSet {
		if t.engine.store.HasConflict(key, t.txn.StartTimestamp, t.txn.ID) {
			// Conflict detected - abort
			t.engine.txMgr.Abort(t.txn.ID)
			return fmt.Errorf("write-write conflict on key %q for transaction %d", key, t.txn.ID)
		}
	}

	// Get commit timestamp
	commitTS, err := t.engine.txMgr.Commit(t.txn.ID)
	if err != nil {
		return fmt.Errorf("failed to commit transaction %d: %w", t.txn.ID, err)
	}

	// Apply writes to store
	for key, wr := range t.txn.WriteSet {
		if wr.IsDelete {
			t.engine.store.Delete(key, t.txn.ID, commitTS)
		} else {
			t.engine.store.Put(key, wr.Value, t.txn.ID, commitTS)
		}
	}

	return nil
}

// Abort aborts the transaction, discarding all writes
func (t *Transaction) Abort() error {
	t.mu.Lock()
	defer t.mu.Unlock()

	if !t.txn.IsActive() {
		return fmt.Errorf("transaction %d is not active", t.txn.ID)
	}

	return t.engine.txMgr.Abort(t.txn.ID)
}

// ID returns the transaction ID
func (t *Transaction) ID() uint64 {
	return t.txn.ID
}

// Status returns the transaction status
func (t *Transaction) Status() transaction.TxnStatus {
	t.mu.RLock()
	defer t.mu.RUnlock()
	return t.txn.Status
}

// StartTimestamp returns the snapshot timestamp of the transaction
func (t *Transaction) StartTimestamp() uint64 {
	return t.txn.StartTimestamp
}

// String returns a string representation of the transaction
func (t *Transaction) String() string {
	return t.txn.String()
}

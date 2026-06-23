// Package transaction implements transactional message processing.
//
// A Transaction groups multiple operations into an atomic unit: either
// all operations succeed, or all are rolled back. This is critical for
// exactly-once semantics when a message handler needs to perform multiple
// side effects (e.g., update a database AND send a notification).
//
// The implementation uses a two-phase approach:
//   - Phase 1 (Prepare): Execute all operations, collect results
//   - Phase 2 (Commit/Rollback): Either commit all results or roll back
//
// This is inspired by the Two-Phase Commit (2PC) protocol used in
// distributed databases.
package transaction

import (
	"fmt"
	"sync"
	"time"
)

// State represents the transaction state.
type State int

const (
	// StateActive indicates the transaction is accepting operations.
	StateActive State = iota
	// StatePrepared indicates all operations have been executed (phase 1).
	StatePrepared
	// StateCommitted indicates the transaction was successfully committed.
	StateCommitted
	// StateAborted indicates the transaction was rolled back.
	StateAborted
)

// String returns a human-readable representation of the transaction state.
func (s State) String() string {
	switch s {
	case StateActive:
		return "ACTIVE"
	case StatePrepared:
		return "PREPARED"
	case StateCommitted:
		return "COMMITTED"
	case StateAborted:
		return "ABORTED"
	default:
		return fmt.Sprintf("UNKNOWN(%d)", int(s))
	}
}

// Operation represents a single operation within a transaction.
type Operation struct {
	// Name identifies the operation.
	Name string

	// Execute performs the operation and returns a result.
	Execute func() (interface{}, error)

	// Undo reverses the operation's side effects.
	Undo func() error

	// Result stores the result after execution.
	Result interface{}

	// Error stores any error during execution.
	Error error

	// Executed tracks whether this operation has been executed.
	Executed bool
}

// Transaction groups operations into an atomic unit.
type Transaction struct {
	mu         sync.Mutex
	ID         string
	State      State
	Operations []*Operation
	StartedAt  time.Time
	CommittedAt *time.Time
	AbortedAt   *time.Time
	Error       string
}

// New creates a new Transaction with the given ID.
func New(id string) *Transaction {
	return &Transaction{
		ID:        id,
		State:     StateActive,
		StartedAt: time.Now(),
	}
}

// Add adds an operation to the transaction.
// Returns an error if the transaction is not in the Active state.
func (t *Transaction) Add(op *Operation) error {
	t.mu.Lock()
	defer t.mu.Unlock()

	if t.State != StateActive {
		return fmt.Errorf("cannot add operation to transaction in state %s", t.State)
	}

	t.Operations = append(t.Operations, op)
	return nil
}

// Prepare executes all operations (Phase 1).
// If any operation fails, the transaction is aborted and all executed
// operations are rolled back.
func (t *Transaction) Prepare() error {
	t.mu.Lock()
	defer t.mu.Unlock()

	if t.State != StateActive {
		return fmt.Errorf("cannot prepare transaction in state %s", t.State)
	}

	// Execute operations in order
	for i, op := range t.Operations {
		result, err := op.Execute()
		op.Result = result
		op.Error = err
		op.Executed = true

		if err != nil {
			// Operation failed - roll back all executed operations
			t.rollbackExecuted(i)
			t.State = StateAborted
			now := time.Now()
			t.AbortedAt = &now
			t.Error = fmt.Sprintf("operation '%s' failed: %v", op.Name, err)
			return fmt.Errorf("prepare failed at operation '%s': %w", op.Name, err)
		}
	}

	t.State = StatePrepared
	return nil
}

// Commit finalizes the transaction (Phase 2).
// All operations have been prepared successfully.
func (t *Transaction) Commit() error {
	t.mu.Lock()
	defer t.mu.Unlock()

	if t.State != StatePrepared {
		return fmt.Errorf("cannot commit transaction in state %s", t.State)
	}

	t.State = StateCommitted
	now := time.Now()
	t.CommittedAt = &now
	return nil
}

// Abort rolls back the transaction.
func (t *Transaction) Abort() error {
	t.mu.Lock()
	defer t.mu.Unlock()

	if t.State == StateCommitted {
		return fmt.Errorf("cannot abort committed transaction")
	}

	if t.State == StateAborted {
		return nil // Already aborted
	}

	// Roll back all executed operations
	t.rollbackExecuted(len(t.Operations))

	t.State = StateAborted
	now := time.Now()
	t.AbortedAt = &now
	return nil
}

// rollbackExecuted rolls back operations from index 0 to lastIndex-1
// (in reverse order). Must be called with mu held.
func (t *Transaction) rollbackExecuted(lastIndex int) {
	for i := lastIndex - 1; i >= 0; i-- {
		op := t.Operations[i]
		if op.Executed && op.Undo != nil {
			if err := op.Undo(); err != nil {
				// Log but continue - best effort rollback
				t.Error = fmt.Sprintf("rollback error for '%s': %v", op.Name, err)
			}
		}
	}
}

// Execute performs Prepare + Commit in a single call.
// This is a convenience method for the common case.
func (t *Transaction) Execute() error {
	if err := t.Prepare(); err != nil {
		return err
	}
	return t.Commit()
}

// GetResult returns the result of the named operation.
func (t *Transaction) GetResult(name string) (interface{}, bool) {
	t.mu.Lock()
	defer t.mu.Unlock()

	for _, op := range t.Operations {
		if op.Name == name {
			return op.Result, op.Executed
		}
	}
	return nil, false
}

// Duration returns the total transaction duration.
func (t *Transaction) Duration() time.Duration {
	t.mu.Lock()
	defer t.mu.Unlock()

	if t.CommittedAt != nil {
		return t.CommittedAt.Sub(t.StartedAt)
	}
	if t.AbortedAt != nil {
		return t.AbortedAt.Sub(t.StartedAt)
	}
	return time.Since(t.StartedAt)
}

// OperationCount returns the number of operations in the transaction.
func (t *Transaction) OperationCount() int {
	t.mu.Lock()
	defer t.mu.Unlock()
	return len(t.Operations)
}

// ExecutedCount returns the number of operations that have been executed.
func (t *Transaction) ExecutedCount() int {
	t.mu.Lock()
	defer t.mu.Unlock()
	count := 0
	for _, op := range t.Operations {
		if op.Executed {
			count++
		}
	}
	return count
}

// Manager manages multiple transactions.
type Manager struct {
	mu           sync.RWMutex
	transactions map[string]*Transaction
}

// NewManager creates a new transaction Manager.
func NewManager() *Manager {
	return &Manager{
		transactions: make(map[string]*Transaction),
	}
}

// Begin creates and registers a new transaction.
func (m *Manager) Begin(id string) *Transaction {
	m.mu.Lock()
	defer m.mu.Unlock()

	t := New(id)
	m.transactions[id] = t
	return t
}

// Get returns a transaction by ID, or nil if not found.
func (m *Manager) Get(id string) *Transaction {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.transactions[id]
}

// CommittedCount returns the number of committed transactions.
func (m *Manager) CommittedCount() int {
	m.mu.RLock()
	defer m.mu.RUnlock()
	count := 0
	for _, t := range m.transactions {
		if t.State == StateCommitted {
			count++
		}
	}
	return count
}

// AbortedCount returns the number of aborted transactions.
func (m *Manager) AbortedCount() int {
	m.mu.RLock()
	defer m.mu.RUnlock()
	count := 0
	for _, t := range m.transactions {
		if t.State == StateAborted {
			count++
		}
	}
	return count
}

// Size returns the total number of managed transactions.
func (m *Manager) Size() int {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return len(m.transactions)
}

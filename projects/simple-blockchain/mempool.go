package main

import (
	"fmt"
	"sync"
)

// Mempool represents the transaction memory pool
type Mempool struct {
	PendingTxs map[string]*Transaction // Pending transactions indexed by ID
	mu         sync.RWMutex
	MaxSize    int // Maximum number of transactions in the pool
}

// NewMempool creates a new mempool
func NewMempool(maxSize int) *Mempool {
	return &Mempool{
		PendingTxs: make(map[string]*Transaction),
		MaxSize:    maxSize,
	}
}

// AddTransaction adds a transaction to the mempool
func (mp *Mempool) AddTransaction(tx *Transaction) error {
	mp.mu.Lock()
	defer mp.mu.Unlock()

	// Check if mempool is full
	if mp.MaxSize > 0 && len(mp.PendingTxs) >= mp.MaxSize {
		return fmt.Errorf("mempool is full (max size: %d)", mp.MaxSize)
	}

	// Check if transaction already exists
	txID := HashToString(tx.ID)
	if _, exists := mp.PendingTxs[txID]; exists {
		return fmt.Errorf("transaction already in mempool: %s", txID)
	}

	// Verify transaction
	if err := tx.Verify(); err != nil {
		return fmt.Errorf("invalid transaction: %v", err)
	}

	// Add to pool
	mp.PendingTxs[txID] = tx
	return nil
}

// RemoveTransaction removes a transaction from the mempool
func (mp *Mempool) RemoveTransaction(txID [32]byte) {
	mp.mu.Lock()
	defer mp.mu.Unlock()

	delete(mp.PendingTxs, HashToString(txID))
}

// GetTransaction returns a transaction by ID
func (mp *Mempool) GetTransaction(txID [32]byte) (*Transaction, bool) {
	mp.mu.RLock()
	defer mp.mu.RUnlock()

	tx, exists := mp.PendingTxs[HashToString(txID)]
	return tx, exists
}

// GetPendingTransactions returns all pending transactions
func (mp *Mempool) GetPendingTransactions() []*Transaction {
	mp.mu.RLock()
	defer mp.mu.RUnlock()

	txs := make([]*Transaction, 0, len(mp.PendingTxs))
	for _, tx := range mp.PendingTxs {
		txs = append(txs, tx)
	}
	return txs
}

// GetPendingCount returns the number of pending transactions
func (mp *Mempool) GetPendingCount() int {
	mp.mu.RLock()
	defer mp.mu.RUnlock()

	return len(mp.PendingTxs)
}

// Clear clears the mempool
func (mp *Mempool) Clear() {
	mp.mu.Lock()
	defer mp.mu.Unlock()

	mp.PendingTxs = make(map[string]*Transaction)
}

// ClearConfirmed removes confirmed transactions from the mempool
func (mp *Mempool) ClearConfirmed(confirmedTxs []*Transaction) {
	mp.mu.Lock()
	defer mp.mu.Unlock()

	for _, tx := range confirmedTxs {
		delete(mp.PendingTxs, HashToString(tx.ID))
	}
}

// String returns a string representation of the mempool
func (mp *Mempool) String() string {
	mp.mu.RLock()
	defer mp.mu.RUnlock()

	return fmt.Sprintf("Mempool{PendingTxs: %d, MaxSize: %d}", len(mp.PendingTxs), mp.MaxSize)
}

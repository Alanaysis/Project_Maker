package main

import (
	"testing"
)

func TestNewMempool(t *testing.T) {
	mp := NewMempool(100)

	if mp == nil {
		t.Fatal("NewMempool should not return nil")
	}
	if mp.MaxSize != 100 {
		t.Errorf("Expected MaxSize 100, got %d", mp.MaxSize)
	}
	if len(mp.PendingTxs) != 0 {
		t.Errorf("Expected 0 pending transactions, got %d", len(mp.PendingTxs))
	}
}

func TestMempoolAddTransaction(t *testing.T) {
	mp := NewMempool(100)

	// Create a coinbase transaction (passes verification without signing)
	tx := NewCoinbaseTX("test-address", "Test data")

	err := mp.AddTransaction(tx)
	if err != nil {
		t.Fatalf("Failed to add transaction: %v", err)
	}

	if mp.GetPendingCount() != 1 {
		t.Errorf("Expected 1 pending transaction, got %d", mp.GetPendingCount())
	}
}

func TestMempoolAddDuplicateTransaction(t *testing.T) {
	mp := NewMempool(100)

	tx := NewCoinbaseTX("test-address", "Test data")

	err := mp.AddTransaction(tx)
	if err != nil {
		t.Fatalf("Failed to add transaction: %v", err)
	}

	// Adding the same transaction again should fail
	err = mp.AddTransaction(tx)
	if err == nil {
		t.Error("Adding duplicate transaction should fail")
	}
}

func TestMempoolMaxSize(t *testing.T) {
	mp := NewMempool(2)

	// Add two transactions
	tx1 := NewCoinbaseTX("addr1", "tx1")
	tx2 := NewCoinbaseTX("addr2", "tx2")

	err := mp.AddTransaction(tx1)
	if err != nil {
		t.Fatalf("Failed to add transaction 1: %v", err)
	}

	err = mp.AddTransaction(tx2)
	if err != nil {
		t.Fatalf("Failed to add transaction 2: %v", err)
	}

	// Third transaction should fail
	tx3 := NewCoinbaseTX("addr3", "tx3")
	err = mp.AddTransaction(tx3)
	if err == nil {
		t.Error("Adding transaction beyond max size should fail")
	}
}

func TestMempoolRemoveTransaction(t *testing.T) {
	mp := NewMempool(100)

	tx := NewCoinbaseTX("test-address", "Test data")
	mp.AddTransaction(tx)

	mp.RemoveTransaction(tx.ID)

	if mp.GetPendingCount() != 0 {
		t.Errorf("Expected 0 pending transactions after removal, got %d", mp.GetPendingCount())
	}
}

func TestMempoolGetTransaction(t *testing.T) {
	mp := NewMempool(100)

	tx := NewCoinbaseTX("test-address", "Test data")
	mp.AddTransaction(tx)

	// Should find the transaction
	found, exists := mp.GetTransaction(tx.ID)
	if !exists {
		t.Error("Transaction should exist in mempool")
	}
	if found.ID != tx.ID {
		t.Error("Found transaction ID should match")
	}

	// Should not find a non-existent transaction
	var fakeID [32]byte
	fakeID[0] = 0xFF
	_, exists = mp.GetTransaction(fakeID)
	if exists {
		t.Error("Non-existent transaction should not be found")
	}
}

func TestMempoolGetPendingTransactions(t *testing.T) {
	mp := NewMempool(100)

	tx1 := NewCoinbaseTX("addr1", "tx1")
	tx2 := NewCoinbaseTX("addr2", "tx2")

	mp.AddTransaction(tx1)
	mp.AddTransaction(tx2)

	pending := mp.GetPendingTransactions()
	if len(pending) != 2 {
		t.Errorf("Expected 2 pending transactions, got %d", len(pending))
	}
}

func TestMempoolClear(t *testing.T) {
	mp := NewMempool(100)

	tx := NewCoinbaseTX("test-address", "Test data")
	mp.AddTransaction(tx)

	mp.Clear()

	if mp.GetPendingCount() != 0 {
		t.Errorf("Expected 0 pending transactions after clear, got %d", mp.GetPendingCount())
	}
}

func TestMempoolClearConfirmed(t *testing.T) {
	mp := NewMempool(100)

	tx1 := NewCoinbaseTX("addr1", "tx1")
	tx2 := NewCoinbaseTX("addr2", "tx2")

	mp.AddTransaction(tx1)
	mp.AddTransaction(tx2)

	// Clear only tx1
	mp.ClearConfirmed([]*Transaction{tx1})

	if mp.GetPendingCount() != 1 {
		t.Errorf("Expected 1 pending transaction after clear, got %d", mp.GetPendingCount())
	}

	// tx2 should still be there
	_, exists := mp.GetTransaction(tx2.ID)
	if !exists {
		t.Error("tx2 should still be in mempool")
	}
}

func TestMempoolString(t *testing.T) {
	mp := NewMempool(100)

	str := mp.String()
	if str == "" {
		t.Error("String representation should not be empty")
	}
}

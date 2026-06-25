package tests

import (
	"sync"
	"testing"

	"distributed-transaction/transaction"
)

func TestNewTransaction(t *testing.T) {
	tx := transaction.NewTransaction("test-tx-001")

	if tx.ID != "test-tx-001" {
		t.Errorf("expected ID 'test-tx-001', got '%s'", tx.ID)
	}
	if tx.GetState() != transaction.TxStateInit {
		t.Errorf("expected state INIT, got %s", tx.GetState())
	}
	if tx.CreatedAt.IsZero() {
		t.Error("expected CreatedAt to be set")
	}
	if tx.UpdatedAt.IsZero() {
		t.Error("expected UpdatedAt to be set")
	}
}

func TestTransactionSetState(t *testing.T) {
	tx := transaction.NewTransaction("test-tx-002")

	tx.SetState(transaction.TxStatePreparing)
	if tx.GetState() != transaction.TxStatePreparing {
		t.Errorf("expected PREPARING, got %s", tx.GetState())
	}

	tx.SetState(transaction.TxStatePrepared)
	if tx.GetState() != transaction.TxStatePrepared {
		t.Errorf("expected PREPARED, got %s", tx.GetState())
	}

	tx.SetState(transaction.TxStateCommitted)
	if tx.GetState() != transaction.TxStateCommitted {
		t.Errorf("expected COMMITTED, got %s", tx.GetState())
	}
}

func TestTransactionStateString(t *testing.T) {
	tests := []struct {
		state    transaction.TxState
		expected string
	}{
		{transaction.TxStateInit, "INIT"},
		{transaction.TxStatePreparing, "PREPARING"},
		{transaction.TxStatePrepared, "PREPARED"},
		{transaction.TxStateCommitting, "COMMITTING"},
		{transaction.TxStateCommitted, "COMMITTED"},
		{transaction.TxStateAborting, "ABORTING"},
		{transaction.TxStateAborted, "ABORTED"},
		{transaction.TxState(99), "UNKNOWN"},
	}

	for _, tt := range tests {
		if got := tt.state.String(); got != tt.expected {
			t.Errorf("TxState(%d).String() = %s, want %s", tt.state, got, tt.expected)
		}
	}
}

func TestTransactionString(t *testing.T) {
	tx := transaction.NewTransaction("test-tx-003")
	s := tx.String()

	if s == "" {
		t.Error("expected non-empty string representation")
	}
}

func TestTransactionConcurrentState(t *testing.T) {
	tx := transaction.NewTransaction("test-tx-concurrent")
	states := []transaction.TxState{
		transaction.TxStatePreparing,
		transaction.TxStatePrepared,
		transaction.TxStateCommitting,
		transaction.TxStateCommitted,
	}

	var wg sync.WaitGroup
	for _, state := range states {
		wg.Add(1)
		go func(s transaction.TxState) {
			defer wg.Done()
			tx.SetState(s)
		}(state)
	}
	wg.Wait()

	// 最终状态应该是最后一个设置的状态之一
	finalState := tx.GetState()
	valid := false
	for _, s := range states {
		if finalState == s {
			valid = true
			break
		}
	}
	if !valid {
		t.Errorf("unexpected final state: %s", finalState)
	}
}

func TestTransactionData(t *testing.T) {
	tx := transaction.NewTransaction("test-tx-data")

	// 设置数据
	tx.SetData("key1", "value1")
	tx.SetData("key2", 42)
	tx.SetData("key3", true)

	// 获取数据
	val, ok := tx.GetData("key1")
	if !ok || val != "value1" {
		t.Errorf("expected 'value1', got %v", val)
	}

	val, ok = tx.GetData("key2")
	if !ok || val != 42 {
		t.Errorf("expected 42, got %v", val)
	}

	// 不存在的键
	_, ok = tx.GetData("nonexistent")
	if ok {
		t.Error("expected key not found")
	}
}

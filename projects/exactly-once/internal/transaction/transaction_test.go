package transaction

import (
	"errors"
	"testing"
)

func TestTransactionExecute(t *testing.T) {
	txn := New("txn-001")

	var step1Done, step2Done bool

	txn.Add(&Operation{
		Name: "step1",
		Execute: func() (interface{}, error) {
			step1Done = true
			return "result1", nil
		},
	})
	txn.Add(&Operation{
		Name: "step2",
		Execute: func() (interface{}, error) {
			step2Done = true
			return "result2", nil
		},
	})

	err := txn.Execute()
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if !step1Done {
		t.Error("expected step1 to be executed")
	}
	if !step2Done {
		t.Error("expected step2 to be executed")
	}
	if txn.State != StateCommitted {
		t.Errorf("expected COMMITTED, got %s", txn.State)
	}
}

func TestTransactionRollback(t *testing.T) {
	txn := New("txn-001")

	var step1Undone bool

	txn.Add(&Operation{
		Name: "step1",
		Execute: func() (interface{}, error) {
			return "ok", nil
		},
		Undo: func() error {
			step1Undone = true
			return nil
		},
	})
	txn.Add(&Operation{
		Name: "step2",
		Execute: func() (interface{}, error) {
			return nil, errors.New("step2 failed")
		},
	})

	err := txn.Execute()
	if err == nil {
		t.Fatal("expected error, got nil")
	}

	if txn.State != StateAborted {
		t.Errorf("expected ABORTED, got %s", txn.State)
	}
	if !step1Undone {
		t.Error("expected step1 to be rolled back")
	}
}

func TestTransactionAbort(t *testing.T) {
	txn := New("txn-001")

	var undone bool
	txn.Add(&Operation{
		Name: "step1",
		Execute: func() (interface{}, error) {
			return "ok", nil
		},
		Undo: func() error {
			undone = true
			return nil
		},
	})

	txn.Prepare()
	err := txn.Abort()
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if txn.State != StateAborted {
		t.Errorf("expected ABORTED, got %s", txn.State)
	}
	if !undone {
		t.Error("expected step1 to be undone")
	}
}

func TestTransactionCannotAddAfterPrepare(t *testing.T) {
	txn := New("txn-001")

	txn.Add(&Operation{
		Name: "step1",
		Execute: func() (interface{}, error) {
			return "ok", nil
		},
	})

	txn.Prepare()

	err := txn.Add(&Operation{
		Name: "step2",
		Execute: func() (interface{}, error) {
			return "ok", nil
		},
	})
	if err == nil {
		t.Fatal("expected error when adding to prepared transaction")
	}
}

func TestTransactionCannotCommitWithoutPrepare(t *testing.T) {
	txn := New("txn-001")

	err := txn.Commit()
	if err == nil {
		t.Fatal("expected error when committing without prepare")
	}
}

func TestTransactionCannotAbortCommitted(t *testing.T) {
	txn := New("txn-001")

	txn.Add(&Operation{
		Name: "step1",
		Execute: func() (interface{}, error) {
			return "ok", nil
		},
	})

	txn.Execute()

	err := txn.Abort()
	if err == nil {
		t.Fatal("expected error when aborting committed transaction")
	}
}

func TestTransactionDoubleAbort(t *testing.T) {
	txn := New("txn-001")

	txn.Abort()
	err := txn.Abort() // Should be no-op
	if err != nil {
		t.Fatalf("unexpected error on double abort: %v", err)
	}
}

func TestTransactionGetResult(t *testing.T) {
	txn := New("txn-001")

	txn.Add(&Operation{
		Name: "step1",
		Execute: func() (interface{}, error) {
			return 42, nil
		},
	})

	txn.Execute()

	result, found := txn.GetResult("step1")
	if !found {
		t.Fatal("expected to find step1 result")
	}
	if result != 42 {
		t.Errorf("expected 42, got %v", result)
	}

	_, found = txn.GetResult("nonexistent")
	if found {
		t.Error("expected not to find nonexistent result")
	}
}

func TestTransactionDuration(t *testing.T) {
	txn := New("txn-001")

	txn.Add(&Operation{
		Name: "step1",
		Execute: func() (interface{}, error) {
			return "ok", nil
		},
	})

	txn.Execute()

	dur := txn.Duration()
	if dur <= 0 {
		t.Error("expected positive duration")
	}
}

func TestTransactionOperationCount(t *testing.T) {
	txn := New("txn-001")

	txn.Add(&Operation{Name: "a", Execute: func() (interface{}, error) { return nil, nil }})
	txn.Add(&Operation{Name: "b", Execute: func() (interface{}, error) { return nil, nil }})

	if txn.OperationCount() != 2 {
		t.Errorf("expected 2 operations, got %d", txn.OperationCount())
	}
}

func TestTransactionExecutedCount(t *testing.T) {
	txn := New("txn-001")

	txn.Add(&Operation{
		Name: "step1",
		Execute: func() (interface{}, error) {
			return "ok", nil
		},
	})
	txn.Add(&Operation{
		Name: "step2",
		Execute: func() (interface{}, error) {
			return nil, errors.New("fail")
		},
	})

	txn.Prepare() // step2 fails, so only step1 is executed

	if txn.ExecutedCount() != 2 {
		t.Errorf("expected 2 executed (both attempted), got %d", txn.ExecutedCount())
	}
}

func TestTransactionStateString(t *testing.T) {
	tests := []struct {
		state    State
		expected string
	}{
		{StateActive, "ACTIVE"},
		{StatePrepared, "PREPARED"},
		{StateCommitted, "COMMITTED"},
		{StateAborted, "ABORTED"},
		{State(99), "UNKNOWN(99)"},
	}

	for _, tt := range tests {
		if got := tt.state.String(); got != tt.expected {
			t.Errorf("State(%d).String() = %q, want %q", int(tt.state), got, tt.expected)
		}
	}
}

func TestManagerBegin(t *testing.T) {
	m := NewManager()

	txn := m.Begin("txn-001")
	if txn == nil {
		t.Fatal("expected non-nil transaction")
	}
	if txn.ID != "txn-001" {
		t.Errorf("expected ID 'txn-001', got '%s'", txn.ID)
	}

	if m.Size() != 1 {
		t.Errorf("expected size 1, got %d", m.Size())
	}
}

func TestManagerGet(t *testing.T) {
	m := NewManager()

	m.Begin("txn-001")

	txn := m.Get("txn-001")
	if txn == nil {
		t.Fatal("expected non-nil transaction")
	}

	txn = m.Get("nonexistent")
	if txn != nil {
		t.Error("expected nil for nonexistent transaction")
	}
}

func TestManagerCounts(t *testing.T) {
	m := NewManager()

	// Committed transaction
	txn1 := m.Begin("txn-001")
	txn1.Add(&Operation{
		Name: "step1",
		Execute: func() (interface{}, error) {
			return "ok", nil
		},
	})
	txn1.Execute()

	// Aborted transaction
	txn2 := m.Begin("txn-002")
	txn2.Add(&Operation{
		Name: "step1",
		Execute: func() (interface{}, error) {
			return nil, errors.New("fail")
		},
	})
	txn2.Execute()

	// Active transaction
	m.Begin("txn-003")

	if m.CommittedCount() != 1 {
		t.Errorf("expected 1 committed, got %d", m.CommittedCount())
	}
	if m.AbortedCount() != 1 {
		t.Errorf("expected 1 aborted, got %d", m.AbortedCount())
	}
	if m.Size() != 3 {
		t.Errorf("expected size 3, got %d", m.Size())
	}
}

func TestTransactionMultipleRollbacks(t *testing.T) {
	txn := New("txn-001")

	var undoOrder []string

	for i, name := range []string{"a", "b", "c"} {
		name := name
		txn.Add(&Operation{
			Name: name,
			Execute: func() (interface{}, error) {
				if name == "c" {
					return nil, errors.New("c failed")
				}
				return i, nil
			},
			Undo: func() error {
				undoOrder = append(undoOrder, name)
				return nil
			},
		})
	}

	txn.Execute()

	// Should roll back in reverse order: b, a
	if len(undoOrder) != 2 {
		t.Fatalf("expected 2 undos, got %d", len(undoOrder))
	}
	if undoOrder[0] != "b" || undoOrder[1] != "a" {
		t.Errorf("expected rollback order [b, a], got %v", undoOrder)
	}
}

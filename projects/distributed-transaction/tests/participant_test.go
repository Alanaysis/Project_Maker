package tests

import (
	"testing"

	"distributed-transaction/participant"
	"distributed-transaction/transaction"
)

func TestNewDefaultCohort(t *testing.T) {
	c := participant.NewDefaultCohort("test-cohort-1")

	if c.ID() != "test-cohort-1" {
		t.Errorf("expected ID 'test-cohort-1', got '%s'", c.ID())
	}
	if c.Status() != participant.StatusReady {
		t.Errorf("expected status READY, got %s", c.Status())
	}
}

func TestCohortPrepareSuccess(t *testing.T) {
	c := participant.NewDefaultCohort("cohort-1")
	tx := transaction.NewTransaction("tx-001")

	err := c.Prepare(tx)
	if err != nil {
		t.Errorf("expected no error, got %v", err)
	}
	if c.Status() != participant.StatusPrepared {
		t.Errorf("expected PREPARED, got %s", c.Status())
	}
}

func TestCohortPrepareError(t *testing.T) {
	c := participant.NewDefaultCohort("cohort-err")
	c.SetSimulateError(true)
	tx := transaction.NewTransaction("tx-002")

	err := c.Prepare(tx)
	if err == nil {
		t.Error("expected error, got nil")
	}
	if c.Status() != participant.StatusFailed {
		t.Errorf("expected FAILED, got %s", c.Status())
	}
}

func TestCohortCommitSuccess(t *testing.T) {
	c := participant.NewDefaultCohort("cohort-2")
	tx := transaction.NewTransaction("tx-003")

	// 先 Prepare
	if err := c.Prepare(tx); err != nil {
		t.Fatalf("prepare failed: %v", err)
	}

	// 再 Commit
	err := c.Commit(tx)
	if err != nil {
		t.Errorf("expected no error, got %v", err)
	}
	if c.Status() != participant.StatusCommitted {
		t.Errorf("expected COMMITTED, got %s", c.Status())
	}
}

func TestCohortCommitWithoutPrepare(t *testing.T) {
	c := participant.NewDefaultCohort("cohort-3")
	tx := transaction.NewTransaction("tx-004")

	// 直接 Commit（未 Prepare）
	err := c.Commit(tx)
	if err == nil {
		t.Error("expected error for commit without prepare, got nil")
	}
}

func TestCohortAbortSuccess(t *testing.T) {
	c := participant.NewDefaultCohort("cohort-4")
	tx := transaction.NewTransaction("tx-005")

	// 先 Prepare
	if err := c.Prepare(tx); err != nil {
		t.Fatalf("prepare failed: %v", err)
	}

	// 再 Abort
	err := c.Abort(tx)
	if err != nil {
		t.Errorf("expected no error, got %v", err)
	}
	if c.Status() != participant.StatusAborted {
		t.Errorf("expected ABORTED, got %s", c.Status())
	}
}

func TestCohortStatusString(t *testing.T) {
	tests := []struct {
		status   participant.Status
		expected string
	}{
		{participant.StatusReady, "READY"},
		{participant.StatusPreparing, "PREPARING"},
		{participant.StatusPrepared, "PREPARED"},
		{participant.StatusCommitting, "COMMITTING"},
		{participant.StatusCommitted, "COMMITTED"},
		{participant.StatusAborting, "ABORTING"},
		{participant.StatusAborted, "ABORTED"},
		{participant.StatusFailed, "FAILED"},
		{participant.Status(99), "UNKNOWN"},
	}

	for _, tt := range tests {
		if got := tt.status.String(); got != tt.expected {
			t.Errorf("Status(%d).String() = %s, want %s", tt.status, got, tt.expected)
		}
	}
}

func TestCohortInterface(t *testing.T) {
	// 确保 DefaultCohort 实现了 Cohort 接口
	var _ participant.Cohort = (*participant.DefaultCohort)(nil)
}

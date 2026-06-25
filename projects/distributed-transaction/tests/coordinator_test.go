package tests

import (
	"fmt"
	"sync"
	"testing"
	"time"

	"distributed-transaction/coordinator"
	"distributed-transaction/participant"
	"distributed-transaction/transaction"
)

func TestNewCoordinator(t *testing.T) {
	c := coordinator.NewCoordinator("test-coord")
	if c == nil {
		t.Fatal("expected non-nil coordinator")
	}
	if c.CohortCount() != 0 {
		t.Errorf("expected 0 cohorts, got %d", c.CohortCount())
	}
}

func TestRegisterCohort(t *testing.T) {
	c := coordinator.NewCoordinator("test-coord")
	p := participant.NewDefaultCohort("cohort-1")

	err := c.RegisterCohort(p)
	if err != nil {
		t.Errorf("expected no error, got %v", err)
	}
	if c.CohortCount() != 1 {
		t.Errorf("expected 1 cohort, got %d", c.CohortCount())
	}
}

func TestRegisterDuplicateCohort(t *testing.T) {
	c := coordinator.NewCoordinator("test-coord")
	p := participant.NewDefaultCohort("cohort-1")

	_ = c.RegisterCohort(p)
	err := c.RegisterCohort(p)
	if err == nil {
		t.Error("expected error for duplicate registration")
	}
}

func TestExecuteTransaction2PCSuccess(t *testing.T) {
	c := coordinator.NewCoordinator("test-coord")
	p1 := participant.NewDefaultCohort("cohort-1")
	p2 := participant.NewDefaultCohort("cohort-2")
	p3 := participant.NewDefaultCohort("cohort-3")

	_ = c.RegisterCohort(p1)
	_ = c.RegisterCohort(p2)
	_ = c.RegisterCohort(p3)

	tx := transaction.NewTransaction("tx-success")
	result, err := c.ExecuteTransaction(tx)

	if err != nil {
		t.Errorf("expected no error, got %v", err)
	}
	if result == nil {
		t.Fatal("expected non-nil result")
	}
	if result.Status != "COMMITTED" {
		t.Errorf("expected COMMITTED, got %s", result.Status)
	}
}

func TestExecuteTransaction2PCAbort(t *testing.T) {
	c := coordinator.NewCoordinator("test-coord")
	p1 := participant.NewDefaultCohort("cohort-1")
	p2 := participant.NewDefaultCohort("cohort-fail")
	p2.SetSimulateError(true)

	_ = c.RegisterCohort(p1)
	_ = c.RegisterCohort(p2)

	tx := transaction.NewTransaction("tx-abort")
	result, err := c.ExecuteTransaction(tx)

	if err == nil {
		t.Error("expected error, got nil")
	}
	if result == nil {
		t.Fatal("expected non-nil result")
	}
	if result.Status != "ABORTED" {
		t.Errorf("expected ABORTED, got %s", result.Status)
	}
}

func TestExecuteTransactionNoCohorts(t *testing.T) {
	c := coordinator.NewCoordinator("test-coord-empty")
	tx := transaction.NewTransaction("tx-no-cohorts")

	_, err := c.ExecuteTransaction(tx)
	if err == nil {
		t.Error("expected error for no cohorts")
	}
}

func TestSetTimeouts(t *testing.T) {
	c := coordinator.NewCoordinator("test-coord")
	c.SetPrepareTimeout(10 * time.Second)
	c.SetCommitTimeout(10 * time.Second)
	// 没有 panic 即可
}

func TestResultString(t *testing.T) {
	r := &coordinator.Result{
		TransactionID: "tx-001",
		Status:        "COMMITTED",
		Duration:      time.Second,
	}
	s := r.String()
	if s == "" {
		t.Error("expected non-empty string")
	}
}

func Test2PCConcurrentTransactions(t *testing.T) {
	c := coordinator.NewCoordinator("test-coord-concurrent")
	for i := 0; i < 5; i++ {
		p := participant.NewDefaultCohort(fmt.Sprintf("cohort-%d", i))
		_ = c.RegisterCohort(p)
	}

	// 并发执行多个事务
	var wg sync.WaitGroup
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func(idx int) {
			defer wg.Done()
			tx := transaction.NewTransaction(fmt.Sprintf("tx-concurrent-%d", idx))
			result, err := c.ExecuteTransaction(tx)
			if err != nil {
				t.Errorf("transaction %d failed: %v", idx, err)
			}
			if result != nil && result.Status != "COMMITTED" {
				t.Errorf("transaction %d: expected COMMITTED, got %s", idx, result.Status)
			}
		}(i)
	}
	wg.Wait()
}

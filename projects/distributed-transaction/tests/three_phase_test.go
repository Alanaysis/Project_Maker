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

func TestNewThreePhaseCoordinator(t *testing.T) {
	c := coordinator.NewThreePhaseCoordinator("test-3pc")
	if c == nil {
		t.Fatal("expected non-nil coordinator")
	}
}

func Test3PCRegisterCohort(t *testing.T) {
	c := coordinator.NewThreePhaseCoordinator("test-3pc")
	p := participant.NewDefaultCohort("3pc-cohort-1")

	err := c.RegisterCohort(p)
	if err != nil {
		t.Errorf("expected no error, got %v", err)
	}
}

func Test3PCRegisterDuplicateCohort(t *testing.T) {
	c := coordinator.NewThreePhaseCoordinator("test-3pc")
	p := participant.NewDefaultCohort("3pc-cohort-1")

	_ = c.RegisterCohort(p)
	err := c.RegisterCohort(p)
	if err == nil {
		t.Error("expected error for duplicate registration")
	}
}

func Test3PCExecuteSuccess(t *testing.T) {
	c := coordinator.NewThreePhaseCoordinator("test-3pc")
	p1 := participant.NewDefaultCohort("3pc-cohort-1")
	p2 := participant.NewDefaultCohort("3pc-cohort-2")
	p3 := participant.NewDefaultCohort("3pc-cohort-3")

	_ = c.RegisterCohort(p1)
	_ = c.RegisterCohort(p2)
	_ = c.RegisterCohort(p3)

	tx := transaction.NewTransaction("tx-3pc-success")
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

func Test3PCExecuteAbort(t *testing.T) {
	c := coordinator.NewThreePhaseCoordinator("test-3pc")
	p1 := participant.NewDefaultCohort("3pc-cohort-1")
	p2 := participant.NewDefaultCohort("3pc-cohort-fail")
	p2.SetSimulateError(true)

	_ = c.RegisterCohort(p1)
	_ = c.RegisterCohort(p2)

	tx := transaction.NewTransaction("tx-3pc-abort")
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

func Test3PCNoCohorts(t *testing.T) {
	c := coordinator.NewThreePhaseCoordinator("test-3pc-empty")
	tx := transaction.NewTransaction("tx-3pc-no-cohorts")

	_, err := c.ExecuteTransaction(tx)
	if err == nil {
		t.Error("expected error for no cohorts")
	}
}

func Test3PCSetTimeouts(t *testing.T) {
	c := coordinator.NewThreePhaseCoordinator("test-3pc")
	c.SetCanTimeout(10 * time.Second)
	c.SetPreTimeout(10 * time.Second)
	c.SetCommitTimeout(10 * time.Second)
	// 没有 panic 即可
}

func Test3PCConcurrentTransactions(t *testing.T) {
	c := coordinator.NewThreePhaseCoordinator("test-3pc-concurrent")
	for i := 0; i < 5; i++ {
		p := participant.NewDefaultCohort(fmt.Sprintf("3pc-cohort-%d", i))
		_ = c.RegisterCohort(p)
	}

	var wg sync.WaitGroup
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func(idx int) {
			defer wg.Done()
			tx := transaction.NewTransaction(fmt.Sprintf("tx-3pc-concurrent-%d", idx))
			result, err := c.ExecuteTransaction(tx)
			if err != nil {
				t.Errorf("3PC transaction %d failed: %v", idx, err)
			}
			if result != nil && result.Status != "COMMITTED" {
				t.Errorf("3PC transaction %d: expected COMMITTED, got %s", idx, result.Status)
			}
		}(i)
	}
	wg.Wait()
}

func Test3PCvs2PCComparison(t *testing.T) {
	// 2PC
	coord2pc := coordinator.NewCoordinator("2pc")
	for i := 0; i < 3; i++ {
		p := participant.NewDefaultCohort(fmt.Sprintf("2pc-cohort-%d", i))
		_ = coord2pc.RegisterCohort(p)
	}

	// 3PC
	coord3pc := coordinator.NewThreePhaseCoordinator("3pc")
	for i := 0; i < 3; i++ {
		p := participant.NewDefaultCohort(fmt.Sprintf("3pc-cohort-%d", i))
		_ = coord3pc.RegisterCohort(p)
	}

	tx2pc := transaction.NewTransaction("compare-2pc")
	tx3pc := transaction.NewTransaction("compare-3pc")

	start2pc := time.Now()
	result2pc, err2pc := coord2pc.ExecuteTransaction(tx2pc)
	duration2pc := time.Since(start2pc)

	start3pc := time.Now()
	result3pc, err3pc := coord3pc.ExecuteTransaction(tx3pc)
	duration3pc := time.Since(start3pc)

	if err2pc != nil {
		t.Errorf("2PC failed: %v", err2pc)
	}
	if err3pc != nil {
		t.Errorf("3PC failed: %v", err3pc)
	}

	t.Logf("2PC duration: %v, result: %s", duration2pc, result2pc.Status)
	t.Logf("3PC duration: %v, result: %s", duration3pc, result3pc.Status)
}

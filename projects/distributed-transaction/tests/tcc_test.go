package tests

import (
	"fmt"
	"testing"

	"distributed-transaction/tcc"
)

func TestNewTCCTransaction(t *testing.T) {
	tx := tcc.NewTCCTransaction("test-tcc")
	if tx == nil {
		t.Fatal("expected non-nil transaction")
	}
	if tx.GetStatus() != tcc.TCCPending {
		t.Errorf("expected PENDING, got %s", tx.GetStatus())
	}
}

func TestTCCRegisterParticipant(t *testing.T) {
	tx := tcc.NewTCCTransaction("test-tcc")
	tx.RegisterParticipant(&tcc.TCCParticipant{
		Name: "test-participant",
		Try:  func(data map[string]interface{}) (map[string]interface{}, error) { return nil, nil },
	})
	// 不 panic 即可
}

func TestTCCExecuteSuccess(t *testing.T) {
	tx := tcc.NewTCCTransaction("test-tcc-success")
	tx.Data["amount"] = 100

	confirmed := make([]string, 0)

	tx.RegisterParticipant(&tcc.TCCParticipant{
		Name: "service-1",
		Try: func(data map[string]interface{}) (map[string]interface{}, error) {
			data["frozen_1"] = data["amount"]
			return nil, nil
		},
		Confirm: func(data map[string]interface{}) (map[string]interface{}, error) {
			confirmed = append(confirmed, "service-1")
			delete(data, "frozen_1")
			return nil, nil
		},
		Cancel: func(data map[string]interface{}) (map[string]interface{}, error) {
			return nil, nil
		},
	})

	tx.RegisterParticipant(&tcc.TCCParticipant{
		Name: "service-2",
		Try: func(data map[string]interface{}) (map[string]interface{}, error) {
			return nil, nil
		},
		Confirm: func(data map[string]interface{}) (map[string]interface{}, error) {
			confirmed = append(confirmed, "service-2")
			return nil, nil
		},
		Cancel: func(data map[string]interface{}) (map[string]interface{}, error) {
			return nil, nil
		},
	})

	err := tx.Execute()
	if err != nil {
		t.Errorf("expected no error, got %v", err)
	}
	if tx.GetStatus() != tcc.TCCConfirmed {
		t.Errorf("expected CONFIRMED, got %s", tx.GetStatus())
	}
	if len(confirmed) != 2 {
		t.Errorf("expected 2 confirmations, got %d", len(confirmed))
	}
}

func TestTCCExecuteTryFailure(t *testing.T) {
	tx := tcc.NewTCCTransaction("test-tcc-try-fail")
	cancelled := make([]string, 0)

	tx.RegisterParticipant(&tcc.TCCParticipant{
		Name: "service-1",
		Try: func(data map[string]interface{}) (map[string]interface{}, error) {
			return nil, nil
		},
		Confirm: func(data map[string]interface{}) (map[string]interface{}, error) {
			return nil, nil
		},
		Cancel: func(data map[string]interface{}) (map[string]interface{}, error) {
			cancelled = append(cancelled, "service-1")
			return nil, nil
		},
	})

	tx.RegisterParticipant(&tcc.TCCParticipant{
		Name: "service-2-will-fail",
		Try: func(data map[string]interface{}) (map[string]interface{}, error) {
			return nil, fmt.Errorf("try failed")
		},
		Confirm: func(data map[string]interface{}) (map[string]interface{}, error) {
			return nil, nil
		},
		Cancel: func(data map[string]interface{}) (map[string]interface{}, error) {
			return nil, nil
		},
	})

	err := tx.Execute()
	if err == nil {
		t.Error("expected error, got nil")
	}
	if tx.GetStatus() != tcc.TCCCancelled {
		t.Errorf("expected CANCELLED, got %s", tx.GetStatus())
	}
	// service-1 应该被取消
	if len(cancelled) != 1 || cancelled[0] != "service-1" {
		t.Errorf("expected service-1 cancelled, got %v", cancelled)
	}
}

func TestTCCExecuteConfirmFailure(t *testing.T) {
	tx := tcc.NewTCCTransaction("test-tcc-confirm-fail")

	tx.RegisterParticipant(&tcc.TCCParticipant{
		Name: "service-1",
		Try: func(data map[string]interface{}) (map[string]interface{}, error) {
			return nil, nil
		},
		Confirm: func(data map[string]interface{}) (map[string]interface{}, error) {
			return nil, fmt.Errorf("confirm failed")
		},
		Cancel: func(data map[string]interface{}) (map[string]interface{}, error) {
			return nil, nil
		},
	})

	err := tx.Execute()
	if err == nil {
		t.Error("expected error, got nil")
	}
	if tx.GetStatus() != tcc.TCCFailed {
		t.Errorf("expected FAILED, got %s", tx.GetStatus())
	}
}

func TestTCCStatusString(t *testing.T) {
	tests := []struct {
		status   tcc.TCCStatus
		expected string
	}{
		{tcc.TCCPending, "PENDING"},
		{tcc.TCCTrying, "TRYING"},
		{tcc.TCCConfirmed, "CONFIRMED"},
		{tcc.TCCCancelled, "CANCELLED"},
		{tcc.TCCFailed, "FAILED"},
		{tcc.TCCStatus(99), "UNKNOWN"},
	}

	for _, tt := range tests {
		if got := tt.status.String(); got != tt.expected {
			t.Errorf("TCCStatus(%d).String() = %s, want %s", tt.status, got, tt.expected)
		}
	}
}

func TestParticipantStatusString(t *testing.T) {
	tests := []struct {
		status   tcc.ParticipantStatus
		expected string
	}{
		{tcc.ParticipantPending, "PENDING"},
		{tcc.ParticipantTried, "TRIED"},
		{tcc.ParticipantConfirmed, "CONFIRMED"},
		{tcc.ParticipantCancelled, "CANCELLED"},
		{tcc.ParticipantFailed, "FAILED"},
		{tcc.ParticipantStatus(99), "UNKNOWN"},
	}

	for _, tt := range tests {
		if got := tt.status.String(); got != tt.expected {
			t.Errorf("ParticipantStatus(%d).String() = %s, want %s", tt.status, got, tt.expected)
		}
	}
}

func TestTCCDataFlow(t *testing.T) {
	tx := tcc.NewTCCTransaction("test-tcc-data")
	tx.Data["balance"] = 1000
	tx.Data["amount"] = 200

	tx.RegisterParticipant(&tcc.TCCParticipant{
		Name: "debit",
		Try: func(data map[string]interface{}) (map[string]interface{}, error) {
			balance := data["balance"].(int)
			amount := data["amount"].(int)
			if balance < amount {
				return nil, fmt.Errorf("insufficient balance")
			}
			data["balance"] = balance - amount
			return nil, nil
		},
		Confirm: func(data map[string]interface{}) (map[string]interface{}, error) {
			return nil, nil
		},
		Cancel: func(data map[string]interface{}) (map[string]interface{}, error) {
			return nil, nil
		},
	})

	err := tx.Execute()
	if err != nil {
		t.Errorf("expected no error, got %v", err)
	}
	if tx.Data["balance"] != 800 {
		t.Errorf("expected balance 800, got %v", tx.Data["balance"])
	}
}

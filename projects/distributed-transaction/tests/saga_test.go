package tests

import (
	"fmt"
	"testing"

	"distributed-transaction/saga"
)

func TestNewSaga(t *testing.T) {
	s := saga.NewSaga("test-saga")
	if s == nil {
		t.Fatal("expected non-nil saga")
	}
	if s.GetStatus() != saga.SagaPending {
		t.Errorf("expected PENDING, got %s", s.GetStatus())
	}
}

func TestSagaAddStep(t *testing.T) {
	s := saga.NewSaga("test-saga")
	s.AddStep("step1",
		func(data map[string]interface{}) (map[string]interface{}, error) { return nil, nil },
		func(data map[string]interface{}) (map[string]interface{}, error) { return nil, nil },
	)
	if len(s.Steps) != 1 {
		t.Errorf("expected 1 step, got %d", len(s.Steps))
	}
}

func TestSagaExecuteSuccess(t *testing.T) {
	s := saga.NewSaga("test-saga-success")

	executed := make([]string, 0)

	s.AddStep("step1",
		func(data map[string]interface{}) (map[string]interface{}, error) {
			executed = append(executed, "step1")
			return nil, nil
		},
		func(data map[string]interface{}) (map[string]interface{}, error) {
			return nil, nil
		},
	)

	s.AddStep("step2",
		func(data map[string]interface{}) (map[string]interface{}, error) {
			executed = append(executed, "step2")
			data["result"] = "done"
			return nil, nil
		},
		func(data map[string]interface{}) (map[string]interface{}, error) {
			return nil, nil
		},
	)

	err := s.Execute()
	if err != nil {
		t.Errorf("expected no error, got %v", err)
	}
	if s.GetStatus() != saga.SagaCompleted {
		t.Errorf("expected COMPLETED, got %s", s.GetStatus())
	}
	if len(executed) != 2 {
		t.Errorf("expected 2 steps executed, got %d", len(executed))
	}
}

func TestSagaExecuteFailure(t *testing.T) {
	s := saga.NewSaga("test-saga-fail")
	compensated := make([]string, 0)

	s.AddStep("step1",
		func(data map[string]interface{}) (map[string]interface{}, error) {
			return nil, nil
		},
		func(data map[string]interface{}) (map[string]interface{}, error) {
			compensated = append(compensated, "step1")
			return nil, nil
		},
	)

	s.AddStep("step2",
		func(data map[string]interface{}) (map[string]interface{}, error) {
			return nil, nil
		},
		func(data map[string]interface{}) (map[string]interface{}, error) {
			compensated = append(compensated, "step2")
			return nil, nil
		},
	)

	s.AddStep("step3-will-fail",
		func(data map[string]interface{}) (map[string]interface{}, error) {
			return nil, fmt.Errorf("step3 failed")
		},
		func(data map[string]interface{}) (map[string]interface{}, error) {
			compensated = append(compensated, "step3")
			return nil, nil
		},
	)

	err := s.Execute()
	if err == nil {
		t.Error("expected error, got nil")
	}
	if s.GetStatus() != saga.SagaFailed {
		t.Errorf("expected FAILED, got %s", s.GetStatus())
	}

	// 补偿应该是逆序的
	if len(compensated) != 2 {
		t.Fatalf("expected 2 compensations, got %d", len(compensated))
	}
	if compensated[0] != "step2" {
		t.Errorf("expected first compensation to be step2, got %s", compensated[0])
	}
	if compensated[1] != "step1" {
		t.Errorf("expected second compensation to be step1, got %s", compensated[1])
	}
}

func TestSagaDataFlow(t *testing.T) {
	s := saga.NewSaga("test-saga-data")
	s.Data["input"] = 10

	s.AddStep("step1",
		func(data map[string]interface{}) (map[string]interface{}, error) {
			input := data["input"].(int)
			return map[string]interface{}{"doubled": input * 2}, nil
		},
		nil,
	)

	s.AddStep("step2",
		func(data map[string]interface{}) (map[string]interface{}, error) {
			doubled := data["doubled"].(int)
			if doubled != 20 {
				return nil, fmt.Errorf("expected 20, got %d", doubled)
			}
			return nil, nil
		},
		nil,
	)

	err := s.Execute()
	if err != nil {
		t.Errorf("expected no error, got %v", err)
	}
}

func TestSagaStepStatus(t *testing.T) {
	tests := []struct {
		status   saga.StepStatus
		expected string
	}{
		{saga.StepPending, "PENDING"},
		{saga.StepCompleted, "COMPLETED"},
		{saga.StepFailed, "FAILED"},
		{saga.StepCompensated, "COMPENSATED"},
		{saga.StepCompensating, "COMPENSATING"},
		{saga.StepStatus(99), "UNKNOWN"},
	}

	for _, tt := range tests {
		if got := tt.status.String(); got != tt.expected {
			t.Errorf("StepStatus(%d).String() = %s, want %s", tt.status, got, tt.expected)
		}
	}
}

func TestSagaStatusString(t *testing.T) {
	tests := []struct {
		status   saga.SagaStatus
		expected string
	}{
		{saga.SagaPending, "PENDING"},
		{saga.SagaRunning, "RUNNING"},
		{saga.SagaCompleted, "COMPLETED"},
		{saga.SagaCompensating, "COMPENSATING"},
		{saga.SagaCompensated, "COMPENSATED"},
		{saga.SagaFailed, "FAILED"},
		{saga.SagaStatus(99), "UNKNOWN"},
	}

	for _, tt := range tests {
		if got := tt.status.String(); got != tt.expected {
			t.Errorf("SagaStatus(%d).String() = %s, want %s", tt.status, got, tt.expected)
		}
	}
}

func TestChoreographySagaSuccess(t *testing.T) {
	cs := saga.NewChoreographySaga("test-choreography")

	cs.RegisterParticipant(&saga.ChoreographyParticipant{
		Name: "service-a",
		Action: func(data map[string]interface{}) (map[string]interface{}, error) {
			data["a_done"] = true
			return nil, nil
		},
		Compensate: func(data map[string]interface{}) (map[string]interface{}, error) {
			return nil, nil
		},
	})

	cs.RegisterParticipant(&saga.ChoreographyParticipant{
		Name: "service-b",
		Action: func(data map[string]interface{}) (map[string]interface{}, error) {
			if !data["a_done"].(bool) {
				return nil, fmt.Errorf("service-a not done")
			}
			return nil, nil
		},
		Compensate: func(data map[string]interface{}) (map[string]interface{}, error) {
			return nil, nil
		},
	})

	err := cs.Execute()
	if err != nil {
		t.Errorf("expected no error, got %v", err)
	}
	if cs.Status != saga.SagaCompleted {
		t.Errorf("expected COMPLETED, got %s", cs.Status)
	}
}

func TestChoreographySagaFailure(t *testing.T) {
	cs := saga.NewChoreographySaga("test-choreography-fail")
	compensated := make([]string, 0)

	cs.RegisterParticipant(&saga.ChoreographyParticipant{
		Name: "service-a",
		Action: func(data map[string]interface{}) (map[string]interface{}, error) {
			return nil, nil
		},
		Compensate: func(data map[string]interface{}) (map[string]interface{}, error) {
			compensated = append(compensated, "service-a")
			return nil, nil
		},
	})

	cs.RegisterParticipant(&saga.ChoreographyParticipant{
		Name: "service-b-will-fail",
		Action: func(data map[string]interface{}) (map[string]interface{}, error) {
			return nil, fmt.Errorf("service-b failed")
		},
		Compensate: func(data map[string]interface{}) (map[string]interface{}, error) {
			return nil, nil
		},
	})

	err := cs.Execute()
	if err == nil {
		t.Error("expected error, got nil")
	}
	if cs.Status != saga.SagaCompensated {
		t.Errorf("expected COMPENSATED, got %s", cs.Status)
	}
	if len(compensated) != 1 || compensated[0] != "service-a" {
		t.Errorf("expected service-a compensated, got %v", compensated)
	}
}

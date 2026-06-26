package device

import (
	"testing"
)

func TestLifecycleManager_Register(t *testing.T) {
	lm := NewLifecycleManager()

	lm.Register("device-1")

	state, err := lm.GetCurrentState("device-1")
	if err != nil {
		t.Fatalf("Failed to get current state: %v", err)
	}

	if state != LifecycleRegistered {
		t.Errorf("Expected state 'registered', got '%s'", state)
	}
}

func TestLifecycleManager_Transition(t *testing.T) {
	lm := NewLifecycleManager()

	lm.Register("device-1")

	// Valid transition: registered -> activated
	err := lm.Transition("device-1", LifecycleActivated, "device connected")
	if err != nil {
		t.Fatalf("Failed to transition to activated: %v", err)
	}

	state, _ := lm.GetCurrentState("device-1")
	if state != LifecycleActivated {
		t.Errorf("Expected state 'activated', got '%s'", state)
	}

	// Valid transition: activated -> running
	err = lm.Transition("device-1", LifecycleRunning, "device ready")
	if err != nil {
		t.Fatalf("Failed to transition to running: %v", err)
	}

	state, _ = lm.GetCurrentState("device-1")
	if state != LifecycleRunning {
		t.Errorf("Expected state 'running', got '%s'", state)
	}
}

func TestLifecycleManager_InvalidTransition(t *testing.T) {
	lm := NewLifecycleManager()

	lm.Register("device-1")

	// Invalid transition: registered -> retired (skip activated and running)
	err := lm.Transition("device-1", LifecycleRetired, "skip")
	if err == nil {
		t.Error("Invalid transition should return error")
	}
}

func TestLifecycleManager_GetHistory(t *testing.T) {
	lm := NewLifecycleManager()

	lm.Register("device-1")
	lm.Transition("device-1", LifecycleActivated, "connected")
	lm.Transition("device-1", LifecycleRunning, "ready")

	history, err := lm.GetHistory("device-1")
	if err != nil {
		t.Fatalf("Failed to get history: %v", err)
	}

	// Initial registration + 2 transitions = 3 entries
	if len(history) != 3 {
		t.Errorf("Expected 3 history entries, got %d", len(history))
	}
}

func TestLifecycleManager_CanTransition(t *testing.T) {
	lm := NewLifecycleManager()

	lm.Register("device-1")

	// Should be able to transition to activated
	can, err := lm.CanTransition("device-1", LifecycleActivated)
	if err != nil {
		t.Fatalf("Error checking transition: %v", err)
	}
	if !can {
		t.Error("Should be able to transition to activated from registered")
	}

	// Should not be able to transition to retired from registered
	can, err = lm.CanTransition("device-1", LifecycleRetired)
	if err != nil {
		t.Fatalf("Error checking transition: %v", err)
	}
	if can {
		t.Error("Should not be able to transition to retired from registered")
	}
}

func TestLifecycleManager_GetAllStates(t *testing.T) {
	lm := NewLifecycleManager()

	lm.Register("device-1")
	lm.Register("device-2")
	lm.Transition("device-2", LifecycleActivated, "connected")

	states := lm.GetAllStates()

	if len(states) != 2 {
		t.Errorf("Expected 2 states, got %d", len(states))
	}

	if states["device-1"] != LifecycleRegistered {
		t.Error("device-1 should be registered")
	}

	if states["device-2"] != LifecycleActivated {
		t.Error("device-2 should be activated")
	}
}

func TestIsTerminalState(t *testing.T) {
	if !IsTerminalState(LifecycleRetired) {
		t.Error("Retired should be a terminal state")
	}

	if IsTerminalState(LifecycleRunning) {
		t.Error("Running should not be a terminal state")
	}
}

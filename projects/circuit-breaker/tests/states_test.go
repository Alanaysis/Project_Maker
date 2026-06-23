package tests

import (
    "testing"

    "circuit-breaker/src"
)

func TestState_String(t *testing.T) {
    tests := []struct {
        state    src.State
        expected string
    }{
        {src.StateClosed, "Closed"},
        {src.StateOpen, "Open"},
        {src.StateHalfOpen, "HalfOpen"},
    }

    for _, test := range tests {
        if test.state.String() != test.expected {
            t.Errorf("Expected %s, got %s", test.expected, test.state.String())
        }
    }
}

func TestState_IsValid(t *testing.T) {
    validStates := []src.State{
        src.StateClosed,
        src.StateOpen,
        src.StateHalfOpen,
    }

    for _, state := range validStates {
        if !state.IsValid() {
            t.Errorf("State %v should be valid", state)
        }
    }

    invalidState := src.State(99)
    if invalidState.IsValid() {
        t.Errorf("State %v should be invalid", invalidState)
    }
}

func TestState_CanExecute(t *testing.T) {
    tests := []struct {
        state       src.State
        canExecute  bool
    }{
        {src.StateClosed, true},
        {src.StateOpen, false},
        {src.StateHalfOpen, true},
    }

    for _, test := range tests {
        if test.state.CanExecute() != test.canExecute {
            t.Errorf("State %v: expected CanExecute to be %v, got %v",
                test.state, test.canExecute, test.state.CanExecute())
        }
    }
}

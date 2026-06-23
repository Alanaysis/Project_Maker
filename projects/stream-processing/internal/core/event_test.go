package core

import (
	"testing"
	"time"
)

func TestNewEvent(t *testing.T) {
	before := time.Now()
	e := NewEvent("key1", 42)
	after := time.Now()

	if e.Key != "key1" {
		t.Errorf("expected key 'key1', got '%s'", e.Key)
	}
	if e.Value != 42 {
		t.Errorf("expected value 42, got %v", e.Value)
	}
	if e.Timestamp.Before(before) || e.Timestamp.After(after) {
		t.Errorf("timestamp should be between before and after")
	}
}

func TestNewEventWithTime(t *testing.T) {
	ts := time.Date(2024, 1, 1, 12, 0, 0, 0, time.UTC)
	e := NewEventWithTime("k", "v", ts)

	if e.Timestamp != ts {
		t.Errorf("expected timestamp %v, got %v", ts, e.Timestamp)
	}
}

func TestWindowContains(t *testing.T) {
	w := Window{
		Start: time.Date(2024, 1, 1, 12, 0, 0, 0, time.UTC),
		End:   time.Date(2024, 1, 1, 12, 0, 10, 0, time.UTC),
	}

	tests := []struct {
		ts       time.Time
		expected bool
	}{
		{w.Start, true},                     // start boundary: included
		{w.Start.Add(time.Second), true},    // inside
		{w.End.Add(-time.Nanosecond), true}, // just before end
		{w.End, false},                      // end boundary: excluded
		{w.Start.Add(-time.Second), false},  // before window
	}

	for _, tt := range tests {
		got := w.Contains(tt.ts)
		if got != tt.expected {
			t.Errorf("Contains(%v) = %v, want %v", tt.ts, got, tt.expected)
		}
	}
}

func TestWindowDuration(t *testing.T) {
	w := Window{
		Start: time.Date(2024, 1, 1, 12, 0, 0, 0, time.UTC),
		End:   time.Date(2024, 1, 1, 12, 0, 10, 0, time.UTC),
	}

	if w.Duration() != 10*time.Second {
		t.Errorf("expected 10s duration, got %v", w.Duration())
	}
}

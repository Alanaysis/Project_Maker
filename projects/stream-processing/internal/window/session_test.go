package window

import (
	"testing"
	"time"

	"github.com/learning/stream-processing/internal/core"
)

func TestSessionWindow(t *testing.T) {
	t.Run("BasicSession", func(t *testing.T) {
		sw := NewSessionWindow(5 * time.Second)
		base := time.Now()

		// Events within the same session
		events := []core.Event{
			core.NewEventWithTime("user1", "click", base),
			core.NewEventWithTime("user1", "click", base.Add(2*time.Second)),
			core.NewEventWithTime("user1", "click", base.Add(4*time.Second)),
		}

		for _, e := range events {
			closed := sw.ProcessEvent(e)
			if len(closed) != 0 {
				t.Errorf("Expected no closed windows, got %d", len(closed))
			}
		}

		if sw.ActiveSessions() != 1 {
			t.Errorf("Expected 1 active session, got %d", sw.ActiveSessions())
		}
	})

	t.Run("SessionClose", func(t *testing.T) {
		sw := NewSessionWindow(5 * time.Second)
		base := time.Now()

		// First session
		sw.ProcessEvent(core.NewEventWithTime("user1", "click", base))
		sw.ProcessEvent(core.NewEventWithTime("user1", "click", base.Add(2*time.Second)))

		// Gap > 5 seconds, should close first session
		closed := sw.ProcessEvent(core.NewEventWithTime("user1", "click", base.Add(10*time.Second)))

		if len(closed) != 1 {
			t.Errorf("Expected 1 closed window, got %d", len(closed))
		}

		if closed[0].Start != base {
			t.Errorf("Expected window start at base, got %v", closed[0].Start)
		}
	})

	t.Run("MultipleKeys", func(t *testing.T) {
		sw := NewSessionWindow(5 * time.Second)
		base := time.Now()

		sw.ProcessEvent(core.NewEventWithTime("user1", "click", base))
		sw.ProcessEvent(core.NewEventWithTime("user2", "click", base.Add(1*time.Second)))
		sw.ProcessEvent(core.NewEventWithTime("user1", "click", base.Add(2*time.Second)))

		if sw.ActiveSessions() != 2 {
			t.Errorf("Expected 2 active sessions, got %d", sw.ActiveSessions())
		}
	})

	t.Run("ForceClose", func(t *testing.T) {
		sw := NewSessionWindow(5 * time.Second)
		base := time.Now()

		sw.ProcessEvent(core.NewEventWithTime("user1", "click", base))
		sw.ProcessEvent(core.NewEventWithTime("user1", "click", base.Add(2*time.Second)))

		closed := sw.ForceClose("user1")
		if len(closed) != 1 {
			t.Errorf("Expected 1 closed window, got %d", len(closed))
		}

		if sw.ActiveSessions() != 0 {
			t.Errorf("Expected 0 active sessions, got %d", sw.ActiveSessions())
		}
	})

	t.Run("ForceCloseAll", func(t *testing.T) {
		sw := NewSessionWindow(5 * time.Second)
		base := time.Now()

		sw.ProcessEvent(core.NewEventWithTime("user1", "click", base))
		sw.ProcessEvent(core.NewEventWithTime("user2", "click", base.Add(1*time.Second)))

		closed := sw.ForceCloseAll()
		if len(closed) != 2 {
			t.Errorf("Expected 2 closed windows, got %d", len(closed))
		}
	})

	t.Run("Gap", func(t *testing.T) {
		sw := NewSessionWindow(10 * time.Second)
		if sw.Gap() != 10*time.Second {
			t.Errorf("Expected gap 10s, got %v", sw.Gap())
		}
	})
}

func TestSessionWindowOperator(t *testing.T) {
	t.Run("SumAggregation", func(t *testing.T) {
		op := NewSessionWindowOperator(5*time.Second, func(a, b interface{}) interface{} {
			return a.(int) + b.(int)
		})

		base := time.Now()
		out := core.NewStream(10)

		// Process events in same session
		op.Process(core.NewEventWithTime("sensor", 10, base), out)
		op.Process(core.NewEventWithTime("sensor", 20, base.Add(2*time.Second)), out)

		// Close session with gap
		op.Process(core.NewEventWithTime("sensor", 30, base.Add(10*time.Second)), out)

		// Close the stream
		out.Close()

		// Collect results
		var results []int
		for e := range out.Events() {
			results = append(results, e.Value.(int))
		}

		// Should have one result: 10 + 20 = 30
		if len(results) != 1 {
			t.Errorf("Expected 1 result, got %d", len(results))
		} else if results[0] != 30 {
			t.Errorf("Expected 30, got %d", results[0])
		}
	})

	t.Run("Flush", func(t *testing.T) {
		op := NewSessionWindowOperator(5*time.Second, func(a, b interface{}) interface{} {
			return a.(int) + b.(int)
		})

		base := time.Now()
		out := core.NewStream(10)

		op.Process(core.NewEventWithTime("sensor", 10, base), out)
		op.Process(core.NewEventWithTime("sensor", 20, base.Add(2*time.Second)), out)

		// Flush without closing session
		op.Flush(out)
		out.Close()

		var results []int
		for e := range out.Events() {
			results = append(results, e.Value.(int))
		}

		if len(results) != 1 {
			t.Errorf("Expected 1 result, got %d", len(results))
		} else if results[0] != 30 {
			t.Errorf("Expected 30, got %d", results[0])
		}
	})
}

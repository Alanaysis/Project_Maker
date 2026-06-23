package operator

import (
	"strings"
	"testing"
	"time"

	"github.com/learning/stream-processing/internal/core"
)

// helper to drain a stream into a slice
func drainStream(s *core.Stream) []core.Event {
	var results []core.Event
	for e := range s.Events() {
		results = append(results, e)
	}
	return results
}

// helper to create and close a stream from events
func streamFrom(events ...core.Event) *core.Stream {
	s := core.NewStream(len(events))
	go func() {
		for _, e := range events {
			s.Emit(e)
		}
		s.Close()
	}()
	return s
}

func TestMapOperator(t *testing.T) {
	m := NewMapOperator(func(v interface{}) interface{} {
		return v.(int) * 2
	})

	input := streamFrom(
		core.NewEvent("a", 1),
		core.NewEvent("b", 2),
		core.NewEvent("c", 3),
	)

	output := core.NewStream(10)
	go func() {
		defer output.Close()
		for e := range input.Events() {
			m.Process(e, output)
		}
		m.Flush(output)
	}()

	results := drainStream(output)
	if len(results) != 3 {
		t.Fatalf("expected 3 results, got %d", len(results))
	}

	expected := []int{2, 4, 6}
	for i, r := range results {
		if r.Value != expected[i] {
			t.Errorf("result[%d] = %v, want %d", i, r.Value, expected[i])
		}
	}
}

func TestFilterOperator(t *testing.T) {
	f := NewFilterOperator(func(e core.Event) bool {
		return e.Value.(int) > 2
	})

	input := streamFrom(
		core.NewEvent("a", 1),
		core.NewEvent("b", 3),
		core.NewEvent("c", 2),
		core.NewEvent("d", 5),
	)

	output := core.NewStream(10)
	go func() {
		defer output.Close()
		for e := range input.Events() {
			f.Process(e, output)
		}
		f.Flush(output)
	}()

	results := drainStream(output)
	if len(results) != 2 {
		t.Fatalf("expected 2 results, got %d", len(results))
	}
	if results[0].Value != 3 || results[1].Value != 5 {
		t.Errorf("unexpected results: %v, %v", results[0].Value, results[1].Value)
	}
}

func TestReduceByKeyOperator(t *testing.T) {
	r := NewReduceByKeyOperator(func(a, b interface{}) interface{} {
		return a.(int) + b.(int)
	})

	input := streamFrom(
		core.NewEvent("a", 1),
		core.NewEvent("b", 2),
		core.NewEvent("a", 3),
		core.NewEvent("b", 4),
		core.NewEvent("c", 10),
	)

	output := core.NewStream(10)
	go func() {
		defer output.Close()
		for e := range input.Events() {
			r.Process(e, output)
		}
		r.Flush(output)
	}()

	results := drainStream(output)

	// Check state directly
	state := r.GetState()
	if state["a"] != 4 {
		t.Errorf("state[a] = %v, want 4", state["a"])
	}
	if state["b"] != 6 {
		t.Errorf("state[b] = %v, want 6", state["b"])
	}
	if state["c"] != 10 {
		t.Errorf("state[c] = %v, want 10", state["c"])
	}

	// Flush should emit results
	if len(results) != 3 {
		t.Errorf("expected 3 flush results, got %d", len(results))
	}
}

func TestFlatMapOperator(t *testing.T) {
	fm := NewFlatMapOperator(func(e core.Event) []core.Event {
		words := strings.Fields(e.Value.(string))
		events := make([]core.Event, len(words))
		for i, w := range words {
			events[i] = core.NewEvent(e.Key, w)
		}
		return events
	})

	input := streamFrom(
		core.NewEvent("line1", "hello world"),
		core.NewEvent("line2", "foo bar baz"),
	)

	output := core.NewStream(10)
	go func() {
		defer output.Close()
		for e := range input.Events() {
			fm.Process(e, output)
		}
		fm.Flush(output)
	}()

	results := drainStream(output)
	if len(results) != 5 {
		t.Fatalf("expected 5 results, got %d", len(results))
	}

	expected := []string{"hello", "world", "foo", "bar", "baz"}
	for i, r := range results {
		if r.Value != expected[i] {
			t.Errorf("result[%d] = %v, want %s", i, r.Value, expected[i])
		}
	}
}

func TestFuncOperator(t *testing.T) {
	fo := NewFuncOperator(func(e core.Event) []core.Event {
		return []core.Event{
			core.NewEvent(e.Key, e.Value.(int)+100),
		}
	})

	input := streamFrom(core.NewEvent("x", 5))
	output := core.NewStream(10)
	go func() {
		defer output.Close()
		for e := range input.Events() {
			fo.Process(e, output)
		}
		fo.Flush(output)
	}()

	results := drainStream(output)
	if len(results) != 1 {
		t.Fatalf("expected 1 result, got %d", len(results))
	}
	if results[0].Value != 105 {
		t.Errorf("result = %v, want 105", results[0].Value)
	}
}

func TestWindowedReduceOperatorTumbling(t *testing.T) {
	wr := NewWindowedReduceOperator(10*time.Second, 10*time.Second, func(a, b interface{}) interface{} {
		return a.(int) + b.(int)
	})

	base := time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)

	// Events in [0, 10s) window
	input := streamFrom(
		core.NewEventWithTime("k", 1, base.Add(1*time.Second)),
		core.NewEventWithTime("k", 2, base.Add(3*time.Second)),
		core.NewEventWithTime("k", 3, base.Add(7*time.Second)),
	)

	output := core.NewStream(10)
	go func() {
		defer output.Close()
		for e := range input.Events() {
			wr.Process(e, output)
		}
		// Force emit all windows
		wr.EmitWindows(output)
	}()

	results := drainStream(output)
	if len(results) != 1 {
		t.Fatalf("expected 1 window result, got %d", len(results))
	}
	if results[0].Value != 6 {
		t.Errorf("window result = %v, want 6", results[0].Value)
	}
}

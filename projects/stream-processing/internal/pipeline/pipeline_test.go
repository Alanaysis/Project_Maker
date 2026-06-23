package pipeline

import (
	"testing"

	"github.com/learning/stream-processing/internal/core"
	"github.com/learning/stream-processing/internal/operator"
)

func drainStream(s *core.Stream) []core.Event {
	var results []core.Event
	for e := range s.Events() {
		results = append(results, e)
	}
	return results
}

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

func TestPipelineEmpty(t *testing.T) {
	p := NewPipeline()
	input := streamFrom(
		core.NewEvent("a", 1),
		core.NewEvent("b", 2),
	)

	output := p.Execute(input)
	results := drainStream(output)

	if len(results) != 2 {
		t.Errorf("empty pipeline should pass through all events, got %d", len(results))
	}
}

func TestPipelineSingleOperator(t *testing.T) {
	p := NewPipeline()
	p.AddOperator(operator.NewMapOperator(func(v interface{}) interface{} {
		return v.(int) * 10
	}))

	input := streamFrom(
		core.NewEvent("a", 1),
		core.NewEvent("b", 2),
		core.NewEvent("c", 3),
	)

	output := p.Execute(input)
	results := drainStream(output)

	if len(results) != 3 {
		t.Fatalf("expected 3 results, got %d", len(results))
	}

	expected := []int{10, 20, 30}
	for i, r := range results {
		if r.Value != expected[i] {
			t.Errorf("result[%d] = %v, want %d", i, r.Value, expected[i])
		}
	}
}

func TestPipelineFilterThenMap(t *testing.T) {
	p := NewPipeline()
	p.AddOperator(operator.NewFilterOperator(func(e core.Event) bool {
		return e.Value.(int) > 2
	}))
	p.AddOperator(operator.NewMapOperator(func(v interface{}) interface{} {
		return v.(int) * 100
	}))

	input := streamFrom(
		core.NewEvent("a", 1),
		core.NewEvent("b", 3),
		core.NewEvent("c", 2),
		core.NewEvent("d", 5),
	)

	output := p.Execute(input)
	results := drainStream(output)

	if len(results) != 2 {
		t.Fatalf("expected 2 results, got %d", len(results))
	}

	expected := []int{300, 500}
	for i, r := range results {
		if r.Value != expected[i] {
			t.Errorf("result[%d] = %v, want %d", i, r.Value, expected[i])
		}
	}
}

func TestPipelineMapThenFilter(t *testing.T) {
	p := NewPipeline()
	p.AddOperator(operator.NewMapOperator(func(v interface{}) interface{} {
		return v.(int) * 2
	}))
	p.AddOperator(operator.NewFilterOperator(func(e core.Event) bool {
		return e.Value.(int) > 5
	}))

	input := streamFrom(
		core.NewEvent("a", 1),
		core.NewEvent("b", 3),
		core.NewEvent("c", 4),
	)

	output := p.Execute(input)
	results := drainStream(output)

	// 1*2=2 (filtered), 3*2=6 (kept), 4*2=8 (kept)
	if len(results) != 2 {
		t.Fatalf("expected 2 results, got %d", len(results))
	}
}

func TestPipelineThreeOperators(t *testing.T) {
	p := NewPipeline()
	// Multiply by 2
	p.AddOperator(operator.NewMapOperator(func(v interface{}) interface{} {
		return v.(int) * 2
	}))
	// Keep even numbers
	p.AddOperator(operator.NewFilterOperator(func(e core.Event) bool {
		return e.Value.(int)%2 == 0
	}))
	// Add 100
	p.AddOperator(operator.NewMapOperator(func(v interface{}) interface{} {
		return v.(int) + 100
	}))

	input := streamFrom(
		core.NewEvent("a", 1),  // 2 -> even -> 102
		core.NewEvent("b", 2),  // 4 -> even -> 104
		core.NewEvent("c", 3),  // 6 -> even -> 106
		core.NewEvent("d", 11), // 22 -> even -> 122
	)

	output := p.Execute(input)
	results := drainStream(output)

	if len(results) != 4 {
		t.Fatalf("expected 4 results, got %d", len(results))
	}

	expected := []int{102, 104, 106, 122}
	for i, r := range results {
		if r.Value != expected[i] {
			t.Errorf("result[%d] = %v, want %d", i, r.Value, expected[i])
		}
	}
}

func TestPipelineParallel(t *testing.T) {
	p := NewPipeline()
	p.AddOperator(operator.NewMapOperator(func(v interface{}) interface{} {
		return v.(int) * 2
	}))

	input := streamFrom(
		core.NewEvent("a", 1),
		core.NewEvent("b", 2),
		core.NewEvent("c", 3),
		core.NewEvent("d", 4),
	)

	output := p.ExecuteParallel(input, 3)
	results := drainStream(output)

	if len(results) != 4 {
		t.Fatalf("expected 4 results, got %d", len(results))
	}

	// Results may be out of order due to parallelism
	sum := 0
	for _, r := range results {
		sum += r.Value.(int)
	}
	if sum != 20 { // (1+2+3+4)*2 = 20
		t.Errorf("sum = %d, want 20", sum)
	}
}

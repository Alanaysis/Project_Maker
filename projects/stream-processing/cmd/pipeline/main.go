package main

import (
	"fmt"
	"strings"
	"time"

	"github.com/learning/stream-processing/internal/core"
	"github.com/learning/stream-processing/internal/operator"
	"github.com/learning/stream-processing/internal/pipeline"
)

func main() {
	fmt.Println("=== Stream Processing Framework Demo ===")
	fmt.Println()

	demoBasicPipeline()
	demoFilterAndMap()
	demoReduceByKey()
	demoWindowedAggregation()
	demoFlatMap()
	demoParallelPipeline()
}

// demoBasicPipeline shows a simple map pipeline.
func demoBasicPipeline() {
	fmt.Println("--- Demo 1: Basic Map Pipeline ---")

	p := pipeline.NewPipeline()
	p.AddOperator(operator.NewMapOperator(func(v interface{}) interface{} {
		return v.(int) * 2
	}))

	input := core.NewStream(10)
	go func() {
		for i := 1; i <= 5; i++ {
			input.Emit(core.NewEvent("num", i))
		}
		input.Close()
	}()

	output := p.Execute(input)
	for e := range output.Events() {
		fmt.Printf("  Input: %d -> Output: %d\n", e.Value.(int)/2, e.Value.(int))
	}
	fmt.Println()
}

// demoFilterAndMap shows chaining filter and map operators.
func demoFilterAndMap() {
	fmt.Println("--- Demo 2: Filter + Map Pipeline ---")

	p := pipeline.NewPipeline()
	// Keep only positive numbers
	p.AddOperator(operator.NewFilterOperator(func(e core.Event) bool {
		return e.Value.(int) > 0
	}))
	// Square them
	p.AddOperator(operator.NewMapOperator(func(v interface{}) interface{} {
		n := v.(int)
		return n * n
	}))

	input := core.NewStream(10)
	go func() {
		nums := []int{-3, 1, -2, 4, 0, 5, -1}
		for _, n := range nums {
			input.Emit(core.NewEvent("num", n))
		}
		input.Close()
	}()

	output := p.Execute(input)
	for e := range output.Events() {
		fmt.Printf("  Squared: %d\n", e.Value.(int))
	}
	fmt.Println()
}

// demoReduceByKey shows per-key aggregation.
func demoReduceByKey() {
	fmt.Println("--- Demo 3: Reduce By Key ---")

	reducer := operator.NewReduceByKeyOperator(func(a, b interface{}) interface{} {
		return a.(int) + b.(int)
	})

	events := []core.Event{
		core.NewEvent("sensor-A", 10),
		core.NewEvent("sensor-B", 20),
		core.NewEvent("sensor-A", 15),
		core.NewEvent("sensor-B", 5),
		core.NewEvent("sensor-A", 25),
	}

	output := core.NewStream(10)
	go func() {
		defer output.Close()
		for _, e := range events {
			fmt.Printf("  Processing: %s = %d\n", e.Key, e.Value.(int))
			reducer.Process(e, output)
		}
		reducer.Flush(output)
	}()

	for e := range output.Events() {
		fmt.Printf("  Result: %s = %d\n", e.Key, e.Value.(int))
	}
	fmt.Println()
}

// demoWindowedAggregation shows time-windowed reduce.
func demoWindowedAggregation() {
	fmt.Println("--- Demo 4: Windowed Aggregation (Tumbling Window, 5s) ---")

	wr := operator.NewWindowedReduceOperator(5*time.Second, 5*time.Second,
		func(a, b interface{}) interface{} {
			return a.(int) + b.(int)
		},
	)

	base := time.Now()
	events := []core.Event{
		core.NewEventWithTime("metric", 10, base),
		core.NewEventWithTime("metric", 20, base.Add(1*time.Second)),
		core.NewEventWithTime("metric", 30, base.Add(3*time.Second)),
		core.NewEventWithTime("metric", 5, base.Add(6*time.Second)),  // next window
		core.NewEventWithTime("metric", 15, base.Add(8*time.Second)), // next window
	}

	output := core.NewStream(10)
	go func() {
		defer output.Close()
		for _, e := range events {
			wr.Process(e, output)
		}
		wr.EmitWindows(output)
	}()

	for e := range output.Events() {
		fmt.Printf("  Window sum: %d\n", e.Value.(int))
	}
	fmt.Println()
}

// demoFlatMap shows splitting events.
func demoFlatMap() {
	fmt.Println("--- Demo 5: FlatMap (Word Count) ---")

	p := pipeline.NewPipeline()
	// Split sentences into words
	p.AddOperator(operator.NewFlatMapOperator(func(e core.Event) []core.Event {
		words := strings.Fields(e.Value.(string))
		events := make([]core.Event, len(words))
		for i, w := range words {
			events[i] = core.NewEvent(e.Key, w)
		}
		return events
	}))
	// Map each word to (word, 1)
	p.AddOperator(operator.NewMapOperator(func(v interface{}) interface{} {
		return map[string]int{v.(string): 1}
	}))

	input := core.NewStream(10)
	go func() {
		input.Emit(core.NewEvent("doc", "hello world hello"))
		input.Emit(core.NewEvent("doc", "world go go go"))
		input.Close()
	}()

	output := p.Execute(input)
	counts := make(map[string]int)
	for e := range output.Events() {
		m := e.Value.(map[string]int)
		for word, count := range m {
			counts[word] += count
		}
	}

	fmt.Println("  Word counts:")
	for word, count := range counts {
		fmt.Printf("    %s: %d\n", word, count)
	}
	fmt.Println()
}

// demoParallelPipeline shows parallel execution.
func demoParallelPipeline() {
	fmt.Println("--- Demo 6: Parallel Pipeline (4 workers) ---")

	p := pipeline.NewPipeline()
	p.AddOperator(operator.NewMapOperator(func(v interface{}) interface{} {
		return v.(int) * v.(int) // square
	}))

	input := core.NewStream(20)
	go func() {
		for i := 1; i <= 10; i++ {
			input.Emit(core.NewEvent("num", i))
		}
		input.Close()
	}()

	output := p.ExecuteParallel(input, 4)
	sum := 0
	count := 0
	for e := range output.Events() {
		sum += e.Value.(int)
		count++
	}

	fmt.Printf("  Processed %d events\n", count)
	fmt.Printf("  Sum of squares: %d\n", sum)
	fmt.Println()
}

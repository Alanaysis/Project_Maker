package pipeline

import (
	"sync"

	"github.com/learning/stream-processing/internal/core"
	"github.com/learning/stream-processing/internal/operator"
)

// Pipeline chains multiple operators together into a data processing pipeline.
//
// Usage:
//
//	p := pipeline.NewPipeline()
//	p.AddOperator(operator.NewFilterOperator(...))
//	p.AddOperator(operator.NewMapOperator(...))
//	output := p.Execute(input)
type Pipeline struct {
	operators []operator.Operator
}

// NewPipeline creates an empty pipeline.
func NewPipeline() *Pipeline {
	return &Pipeline{}
}

// AddOperator appends an operator to the pipeline.
// Operators are executed in the order they are added.
func (p *Pipeline) AddOperator(op operator.Operator) *Pipeline {
	p.operators = append(p.operators, op)
	return p
}

// Execute runs the pipeline on the input stream and returns the output stream.
// It processes events through all operators sequentially.
//
// The pipeline runs in a goroutine. The output stream is closed when
// all input events have been processed and flushed.
func (p *Pipeline) Execute(input *core.Stream) *core.Stream {
	output := core.NewStream(100)

	go func() {
		defer output.Close()

		if len(p.operators) == 0 {
			// Passthrough: copy all events
			for event := range input.Events() {
				output.Emit(event)
			}
			return
		}

		// Chain operators: each operator's output feeds the next
		current := input
		for i, op := range p.operators {
			next := core.NewStream(100)

			if i < len(p.operators)-1 {
				// Intermediate operator: run in goroutine
				go func(op operator.Operator, in *core.Stream, out *core.Stream) {
					defer out.Close()
					for event := range in.Events() {
						op.Process(event, out)
					}
					op.Flush(out)
				}(op, current, next)
			} else {
				// Last operator: output goes directly to the pipeline output
				for event := range current.Events() {
					op.Process(event, output)
				}
				op.Flush(output)
			}

			current = next
		}
	}()

	return output
}

// ExecuteParallel runs the pipeline on the input stream with parallelism.
// Events are distributed across the given number of workers.
// Each worker runs the full pipeline chain on its assigned events.
func (p *Pipeline) ExecuteParallel(input *core.Stream, parallelism int) *core.Stream {
	output := core.NewStream(100)

	go func() {
		defer output.Close()

		var wg sync.WaitGroup

		for i := 0; i < parallelism; i++ {
			wg.Add(1)
			go func() {
				defer wg.Done()
				for event := range input.Events() {
					// Process through all operators using the standard interface
					intermediate := core.NewStream(1)
					intermediate.Emit(event)
					intermediate.Close()

					var current *core.Stream
					current = intermediate

					for _, op := range p.operators {
						next := core.NewStream(10)
						for e := range current.Events() {
							op.Process(e, next)
						}
						next.Close()
						current = next
					}

					// Forward results to output
					for result := range current.Events() {
						output.Emit(result)
					}
				}
			}()
		}

		wg.Wait()
	}()

	return output
}

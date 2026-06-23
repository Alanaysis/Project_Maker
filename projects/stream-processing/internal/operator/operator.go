package operator

import (
	"github.com/learning/stream-processing/internal/core"
)

// Operator transforms a stream of events.
// It reads from an input stream and writes to an output stream.
type Operator interface {
	// Process handles a single event and may emit zero or more output events.
	Process(event core.Event, out *core.Stream)

	// Flush is called when no more input events are coming.
	// Operators with internal state should emit remaining results here.
	Flush(out *core.Stream)
}

// FuncOperator wraps a simple function as an Operator.
// It applies the function to each event and emits the result.
type FuncOperator struct {
	fn func(core.Event) []core.Event
}

// NewFuncOperator creates an operator from a function.
func NewFuncOperator(fn func(core.Event) []core.Event) *FuncOperator {
	return &FuncOperator{fn: fn}
}

func (fo *FuncOperator) Process(event core.Event, out *core.Stream) {
	results := fo.fn(event)
	for _, r := range results {
		out.Emit(r)
	}
}

func (fo *FuncOperator) Flush(out *core.Stream) {
	// Stateless, nothing to flush
}

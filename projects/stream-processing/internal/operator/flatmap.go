package operator

import (
	"github.com/learning/stream-processing/internal/core"
)

// FlatMapFunc transforms one event into zero or more events.
type FlatMapFunc func(core.Event) []core.Event

// FlatMapOperator applies a function that can produce multiple output events
// from a single input event.
//
// Example:
//   FlatMap(func(e Event) []Event {
//       str := e.Value.(string)
//       words := strings.Split(str, " ")
//       events := make([]Event, len(words))
//       for i, w := range words {
//           events[i] = NewEvent(e.Key, w)
//       }
//       return events
//   })
type FlatMapOperator struct {
	fn FlatMapFunc
}

// NewFlatMapOperator creates a flat map operator.
func NewFlatMapOperator(fn FlatMapFunc) *FlatMapOperator {
	return &FlatMapOperator{fn: fn}
}

func (fm *FlatMapOperator) Process(event core.Event, out *core.Stream) {
	results := fm.fn(event)
	for _, r := range results {
		out.Emit(r)
	}
}

func (fm *FlatMapOperator) Flush(out *core.Stream) {}

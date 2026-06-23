package operator

import (
	"github.com/learning/stream-processing/internal/core"
)

// FilterFunc is a predicate that decides whether to keep an event.
type FilterFunc func(core.Event) bool

// FilterOperator keeps only events that satisfy a predicate.
//
// Example:
//   Filter(func(e Event) bool {
//       return e.Value.(int) > 10
//   })
type FilterOperator struct {
	fn FilterFunc
}

// NewFilterOperator creates a filter operator with the given predicate.
func NewFilterOperator(fn FilterFunc) *FilterOperator {
	return &FilterOperator{fn: fn}
}

func (f *FilterOperator) Process(event core.Event, out *core.Stream) {
	if f.fn(event) {
		out.Emit(event)
	}
}

func (f *FilterOperator) Flush(out *core.Stream) {}

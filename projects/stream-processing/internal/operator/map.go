package operator

import (
	"github.com/learning/stream-processing/internal/core"
)

// MapFunc is a function that transforms one event's value.
type MapFunc func(interface{}) interface{}

// MapOperator applies a transformation function to each event's value.
//
// Example:
//   Map(func(v interface{}) interface{} {
//       return v.(int) * 2
//   })
type MapOperator struct {
	fn MapFunc
}

// NewMapOperator creates a map operator with the given transform function.
func NewMapOperator(fn MapFunc) *MapOperator {
	return &MapOperator{fn: fn}
}

func (m *MapOperator) Process(event core.Event, out *core.Stream) {
	result := core.Event{
		Key:       event.Key,
		Value:     m.fn(event.Value),
		Timestamp: event.Timestamp,
	}
	out.Emit(result)
}

func (m *MapOperator) Flush(out *core.Stream) {}

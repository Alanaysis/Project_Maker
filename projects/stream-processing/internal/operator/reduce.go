package operator

import (
	"github.com/learning/stream-processing/internal/core"
)

// ReduceFunc combines two values into one.
type ReduceFunc func(a, b interface{}) interface{}

// ReduceByKeyOperator accumulates values per key.
// It holds state internally and emits the current aggregate on Flush.
//
// Example:
//   ReduceByKey(func(a, b interface{}) interface{} {
//       return a.(int) + b.(int)
//   })
type ReduceByKeyOperator struct {
	fn     ReduceFunc
	state  map[string]interface{}
}

// NewReduceByKeyOperator creates a reduce-by-key operator.
func NewReduceByKeyOperator(fn ReduceFunc) *ReduceByKeyOperator {
	return &ReduceByKeyOperator{
		fn:    fn,
		state: make(map[string]interface{}),
	}
}

func (r *ReduceByKeyOperator) Process(event core.Event, out *core.Stream) {
	if existing, ok := r.state[event.Key]; ok {
		r.state[event.Key] = r.fn(existing, event.Value)
	} else {
		r.state[event.Key] = event.Value
	}
}

func (r *ReduceByKeyOperator) Flush(out *core.Stream) {
	for key, val := range r.state {
		out.Emit(core.Event{
			Key:       key,
			Value:     val,
			Timestamp: core.NewEvent("", nil).Timestamp,
		})
	}
}

// GetState returns the current accumulated state (for inspection/testing).
func (r *ReduceByKeyOperator) GetState() map[string]interface{} {
	return r.state
}

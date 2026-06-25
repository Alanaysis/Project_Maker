package operator

import (
	"github.com/learning/stream-processing/internal/core"
)

// KeyByFunc extracts a key from an event's value.
type KeyByFunc func(interface{}) string

// KeyByOperator re-keys events based on a key extraction function.
// This is essential for partitioning data before keyed operations
// like reduce-by-key or windowed aggregation.
//
// Example:
//   KeyBy(func(v interface{}) string {
//       return v.(SensorReading).SensorID
//   })
type KeyByOperator struct {
	fn KeyByFunc
}

// NewKeyByOperator creates a key-by operator with the given key function.
func NewKeyByOperator(fn KeyByFunc) *KeyByOperator {
	return &KeyByOperator{fn: fn}
}

func (k *KeyByOperator) Process(event core.Event, out *core.Stream) {
	result := core.Event{
		Key:       k.fn(event.Value),
		Value:     event.Value,
		Timestamp: event.Timestamp,
	}
	out.Emit(result)
}

func (k *KeyByOperator) Flush(out *core.Stream) {}

// PartitionByOperator routes events to different output streams based on key.
// Useful for parallel processing where each partition is handled independently.
type PartitionByOperator struct {
	fn         KeyByFunc
	partitions int
}

// NewPartitionByOperator creates a partition operator.
func NewPartitionByOperator(fn KeyByFunc, partitions int) *PartitionByOperator {
	return &PartitionByOperator{
		fn:         fn,
		partitions: partitions,
	}
}

// PartitionIndex returns which partition an event belongs to.
func (p *PartitionByOperator) PartitionIndex(event core.Event) int {
	key := p.fn(event.Value)
	hash := 0
	for _, c := range key {
		hash = hash*31 + int(c)
	}
	if hash < 0 {
		hash = -hash
	}
	return hash % p.partitions
}

func (p *PartitionByOperator) Process(event core.Event, out *core.Stream) {
	// Re-key with partition info
	result := core.Event{
		Key:       p.fn(event.Value),
		Value:     event.Value,
		Timestamp: event.Timestamp,
	}
	out.Emit(result)
}

func (p *PartitionByOperator) Flush(out *core.Stream) {}

package streaming

import (
	"math"
	"sync"
)

// StreamAgg provides general-purpose streaming aggregation with O(1) memory.
//
// Unlike SlidingWindow which stores all values, StreamAgg maintains only
// running aggregates, making it suitable for streams of unlimited length
// where you need continuous sum, count, average, min, and max.
//
// This is the most memory-efficient approach but cannot compute values
// that depend on the full distribution (like median, std dev, etc.).
//
// Core loop:
//
//	value arrives → update aggregates → query current state
//
// Example usage:
//
//	agg := NewStreamAgg()
//	for _, v := range data {
//	    agg.Add(v)
//	}
//	fmt.Println("Sum:", agg.Sum())
//	fmt.Println("Avg:", agg.Avg())
//	fmt.Println("Count:", agg.Count())
type StreamAgg struct {
	mu      sync.RWMutex
	sum     float64
	count   int64
	min     float64
	max     float64
	hasData bool
}

// NewStreamAgg creates a new streaming aggregator.
func NewStreamAgg() *StreamAgg {
	return &StreamAgg{
		min: math.MaxFloat64,
		max: -math.MaxFloat64,
	}
}

// Add inserts a value into the aggregator.
//
// All aggregates are updated in O(1) time:
//   - sum: += v
//   - count: += 1
//   - min: min(min, v)
//   - max: max(max, v)
func (a *StreamAgg) Add(v float64) {
	a.mu.Lock()
	defer a.mu.Unlock()

	a.sum += v
	a.count++
	if v < a.min {
		a.min = v
	}
	if v > a.max {
		a.max = v
	}
	a.hasData = true
}

// Sum returns the running sum.
func (a *StreamAgg) Sum() float64 {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.sum
}

// Count returns the number of elements added.
func (a *StreamAgg) Count() int64 {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.count
}

// Avg returns the running average.
func (a *StreamAgg) Avg() float64 {
	a.mu.RLock()
	defer a.mu.RUnlock()
	if a.count == 0 {
		return 0
	}
	return a.sum / float64(a.count)
}

// Min returns the minimum value seen so far.
func (a *StreamAgg) Min() float64 {
	a.mu.RLock()
	defer a.mu.RUnlock()
	if !a.hasData {
		return 0
	}
	return a.min
}

// Max returns the maximum value seen so far.
func (a *StreamAgg) Max() float64 {
	a.mu.RLock()
	defer a.mu.RUnlock()
	if !a.hasData {
		return 0
	}
	return a.max
}

// HasData returns true if any elements have been added.
func (a *StreamAgg) HasData() bool {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.hasData
}

// Reset clears all aggregates.
func (a *StreamAgg) Reset() {
	a.mu.Lock()
	defer a.mu.Unlock()
	a.sum = 0
	a.count = 0
	a.min = math.MaxFloat64
	a.max = -math.MaxFloat64
	a.hasData = false
}

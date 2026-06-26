package streaming

import (
	"sync"
	"time"
)

// SlidingWindow implements a sliding window aggregator over a data stream.
//
// It supports two modes:
//   - Fixed-size window: keeps the last N elements regardless of time
//   - Time-based window: keeps elements within a time duration
//
// Each element is tagged with a timestamp (auto-assigned or provided).
// As new elements arrive, expired elements are evicted from the window.
//
// Example usage:
//
//	w := NewSlidingWindow(100) // fixed size
//	for _, v := range data {
//	    w.Add(v)
//	    avg := w.Avg()
//	}
type SlidingWindow struct {
	mu         sync.RWMutex
	values     []float64
	timestamps []time.Time
	size       int
	windowDur  time.Duration
	useTime    bool
}

// NewSlidingWindow creates a fixed-size sliding window with the given capacity.
func NewSlidingWindow(size int) *SlidingWindow {
	return &SlidingWindow{
		values:     make([]float64, 0, size),
		timestamps: make([]time.Time, 0, size),
		size:       size,
	}
}

// NewTimeSlidingWindow creates a time-based sliding window with the given duration.
func NewTimeSlidingWindow(dur time.Duration) *SlidingWindow {
	return &SlidingWindow{
		values:     make([]float64, 0),
		timestamps: make([]time.Time, 0),
		windowDur:  dur,
		useTime:    true,
	}
}

// Add inserts a value into the window with the current time as its timestamp.
// Expired elements are evicted before insertion.
func (w *SlidingWindow) Add(v float64) {
	w.mu.Lock()
	defer w.mu.Unlock()

	w.evict()

	w.values = append(w.values, v)
	w.timestamps = append(w.timestamps, time.Now())
}

// AddWithTime inserts a value with an explicit timestamp.
func (w *SlidingWindow) AddWithTime(v float64, t time.Time) {
	w.mu.Lock()
	defer w.mu.Unlock()

	// Temporarily use the provided timestamp for eviction logic
	w.mu.Unlock()
	w.evictWithTime(t)
	w.mu.Lock()

	w.values = append(w.values, v)
	w.timestamps = append(w.timestamps, t)
}

// evict removes elements that have expired based on the window mode.
func (w *SlidingWindow) evict() {
	now := time.Now()
	if w.useTime {
		w.evictWithTime(now)
		return
	}
	for len(w.values) >= w.size {
		w.values = w.values[1:]
		w.timestamps = w.timestamps[1:]
	}
}

// evictWithTime removes elements older than windowDur from the given reference time.
func (w *SlidingWindow) evictWithTime(ref time.Time) {
	if !w.useTime {
		return
	}
	cutoff := ref.Add(-w.windowDur)
	idx := 0
	for idx < len(w.timestamps) && w.timestamps[idx].Before(cutoff) {
		idx++
	}
	if idx > 0 {
		w.values = w.values[idx:]
		w.timestamps = w.timestamps[idx:]
	}
}

// Size returns the number of elements currently in the window.
func (w *SlidingWindow) Size() int {
	w.mu.RLock()
	defer w.mu.RUnlock()
	return len(w.values)
}

// Values returns a copy of the current window values.
func (w *SlidingWindow) Values() []float64 {
	w.mu.RLock()
	defer w.mu.RUnlock()
	cp := make([]float64, len(w.values))
	copy(cp, w.values)
	return cp
}

// Avg computes the average of values in the current window.
func (w *SlidingWindow) Avg() float64 {
	w.mu.RLock()
	defer w.mu.RUnlock()
	if len(w.values) == 0 {
		return 0
	}
	var sum float64
	for _, v := range w.values {
		sum += v
	}
	return sum / float64(len(w.values))
}

// Sum computes the sum of values in the current window.
func (w *SlidingWindow) Sum() float64 {
	w.mu.RLock()
	defer w.mu.RUnlock()
	var s float64
	for _, v := range w.values {
		s += v
	}
	return s
}

// Min returns the minimum value in the current window.
func (w *SlidingWindow) Min() float64 {
	w.mu.RLock()
	defer w.mu.RUnlock()
	if len(w.values) == 0 {
		return 0
	}
	m := w.values[0]
	for _, v := range w.values[1:] {
		if v < m {
			m = v
		}
	}
	return m
}

// Max returns the maximum value in the current window.
func (w *SlidingWindow) Max() float64 {
	w.mu.RLock()
	defer w.mu.RUnlock()
	if len(w.values) == 0 {
		return 0
	}
	m := w.values[0]
	for _, v := range w.values[1:] {
		if v > m {
			m = v
		}
	}
	return m
}

// Count returns the count of elements in the current window.
func (w *SlidingWindow) Count() int {
	w.mu.RLock()
	defer w.mu.RUnlock()
	return len(w.values)
}

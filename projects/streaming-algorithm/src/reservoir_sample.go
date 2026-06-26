package streaming

import (
	"math/rand"
	"sync"
	"time"
)

// ReservoirSample implements the Reservoir Sampling algorithm (Algorithm R).
//
// Reservoir sampling allows you to draw k random samples from a stream of
// unknown length n, where n is not known in advance. Each element has an
// equal probability (k/n) of being selected.
//
// Algorithm:
//
//	1. Fill the reservoir with the first k elements
//	2. For each subsequent element i (k+1, k+2, ...):
//	   - Generate random j in [0, i)
//	   - If j < k, replace reservoir[j] with element i
//
// This guarantees uniform sampling: every element has exactly k/n probability
// of appearing in the final reservoir.
//
// Example usage:
//
//	r := NewReservoirSample(10)
//	for _, v := range stream {
//	    r.Add(v)
//	}
//	sample := r.Get() // returns 10 random elements
type ReservoirSample struct {
	mu      sync.RWMutex
	res     []float64
	count   int64
	k       int
	randSrc *rand.Rand
}

// NewReservoirSample creates a new reservoir sampler with capacity k.
func NewReservoirSample(k int) *ReservoirSample {
	return &ReservoirSample{
		res:     make([]float64, k),
		k:       k,
		count:   0,
		randSrc: rand.New(rand.NewSource(time.Now().UnixNano())),
	}
}

// Add processes one element from the stream.
//
// For the first k elements, they are placed directly into the reservoir.
// For element i (0-indexed, i >= k), it replaces a random reservoir entry
// with probability k/(i+1).
func (r *ReservoirSample) Add(v float64) {
	r.mu.Lock()
	defer r.mu.Unlock()

	r.count++
	if int(r.count) <= r.k {
		// Phase 1: fill the reservoir
		r.res[r.count-1] = v
	} else {
		// Phase 2: probabilistic replacement
		j := r.randSrc.Int63n(r.count)
		if j < int64(r.k) {
			r.res[j] = v
		}
	}
}

// Get returns a copy of the current reservoir contents.
func (r *ReservoirSample) Get() []float64 {
	r.mu.RLock()
	defer r.mu.RUnlock()
	cp := make([]float64, len(r.res))
	copy(cp, r.res)
	return cp
}

// Count returns the total number of elements seen so far.
func (r *ReservoirSample) Count() int64 {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return r.count
}

// IsComplete returns true when at least k elements have been added.
func (r *ReservoirSample) IsComplete() bool {
	return r.count >= int64(r.k)
}

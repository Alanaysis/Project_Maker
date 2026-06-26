package streaming

import (
	"crypto/sha256"
	"fmt"
	"math"
	"sync"
)

// HyperLogLog implements the HyperLogLog probabilistic cardinality estimation algorithm.
//
// HyperLogLog estimates the number of distinct elements (cardinality) in a stream
// using very little memory (~1.3 KB for 2% error rate). It works by:
//
//   1. Hashing each element
//   2. Splitting the hash into two parts: register index and position bits
//   3. Tracking the maximum run of leading zeros for each register
//   4. Combining register values using harmonic mean for the final estimate
//
// Key properties:
//   - Space: O(1/ln(2) * 2^p) bits where p = precision parameter
//   - Standard error: ~1.04 / sqrt(2^p)
//   - For p=14: ~16 KB memory, ~1% error rate
//
// The algorithm is particularly effective for very large cardinalities where
// exact counting would be impractical.
//
// Example usage:
//
//	hll := NewHyperLogLog(14) // ~1% error rate
//	for _, s := range items {
//	    hll.Add(s)
//	}
//	distinct := hll.Count() // estimated cardinality
type HyperLogLog struct {
	mu         sync.Mutex
	p          uint8   // precision: number of bits for register index
	m          uint32  // number of registers = 2^p
	registers  []uint8 // max leading zeros per register
	alpha      float64 // correction constant
	totalHashs uint64  // total number of elements added
}

// NewHyperLogLog creates a HyperLogLog counter with the given precision parameter p.
//
// Recommended values:
//   - p=10: ~64 registers, ~4.1% error, ~512 bytes
//   - p=12: ~4096 registers, ~2.05% error, ~2 KB
//   - p=14: ~16384 registers, ~1.03% error, ~8 KB
//   - p=16: ~65536 registers, ~0.65% error, ~32 KB
func NewHyperLogLog(p uint8) *HyperLogLog {
	m := uint32(1) << p
	alpha := computeAlpha(p, m)
	return &HyperLogLog{
		p:         p,
		m:         m,
		registers: make([]uint8, m),
		alpha:     alpha,
	}
}

// computeAlpha returns the correction constant based on p and m.
// These constants correct for bias in the harmonic mean estimator.
func computeAlpha(p uint8, m uint32) float64 {
	switch p {
	case 4:
		return 0.673
	case 5:
		return 0.697
	case 6:
		return 0.709
	default:
		return 0.7213 / (1.0 + 1.079 / float64(m))
	}
}

// hash64 computes a 64-bit hash of the input string.
func (h *HyperLogLog) hash64(s string) uint64 {
	data := sha256.Sum256([]byte(s))
	var h64 uint64
	for i := 0; i < 8; i++ {
		h64 = (h64 << 8) | uint64(data[i])
	}
	return h64
}

// rho computes the position of the leftmost 1-bit (plus 1).
// For a hash value, this is equivalent to counting leading zeros + 1.
func (h *HyperLogLog) rho(val uint64) uint8 {
	// Extract the bits after the register index
	remaining := val >> h.p
	if remaining == 0 {
		return uint8(h.p) + 1
	}
	// Count leading zeros in the remaining bits
	r := uint8(0)
	for (remaining & 1) == 0 {
		remaining >>= 1
		r++
	}
	return h.p + r + 1
}

// Add inserts an element into the HyperLogLog counter.
func (h *HyperLogLog) Add(element string) {
	h.mu.Lock()
	defer h.mu.Unlock()

	hash := h.hash64(element)
	// Use first p bits as register index
	idx := hash & (uint64(h.m) - 1)
	// Count leading zeros in remaining bits
	w := h.rho(hash)
	if w > h.registers[idx] {
		h.registers[idx] = w
	}
	h.totalHashs++
}

// Count returns the estimated number of distinct elements.
//
// The estimate uses three corrections:
//   1. Linear counting for small cardinalities (underestimation correction)
//   2. Standard harmonic mean estimator
//   3. Large cardinality correction (overestimation correction)
func (h *HyperLogLog) Count() uint64 {
	h.mu.Lock()
	defer h.mu.Unlock()

	// Compute the harmonic mean of 2^(-register values)
	sum := 0.0
	for _, v := range h.registers {
		sum += math.Pow(2.0, -float64(v))
	}
	estimate := h.alpha * float64(h.m) * float64(h.m) / sum

	// Small range correction: when estimate < 5/2 * m
	if estimate <= 2.5*float64(h.m) {
		// Count zero registers
		zeroRegs := 0
		for _, v := range h.registers {
			if v == 0 {
				zeroRegs++
			}
		}
		if zeroRegs > 0 {
			estimate = float64(h.m) * math.Log(float64(h.m)/float64(zeroRegs))
		}
	}

	// Large range correction: when estimate > 2^32 / 30
	if estimate > (1 << 32) / 30.0 {
		estimate = -(1 << 32) * math.Log(1-estimate/(1<<32))
	}

	return uint64(estimate + 0.5)
}

// Reset clears all registers and counters.
func (h *HyperLogLog) Reset() {
	h.mu.Lock()
	defer h.mu.Unlock()
	for i := range h.registers {
		h.registers[i] = 0
	}
	h.totalHashs = 0
}

// String returns a string representation of the HyperLogLog counter.
func (h *HyperLogLog) String() string {
	return fmt.Sprintf("HyperLogLog{p: %d, m: %d, est: %d}", h.p, h.m, h.Count())
}

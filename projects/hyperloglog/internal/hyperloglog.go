// Package hyperloglog implements the HyperLogLog cardinality estimation algorithm.
//
// HyperLogLog is a probabilistic data structure used for estimating the number
// of distinct elements in a multiset (the cardinality). It achieves remarkable
// accuracy using very little memory - typically 1.5KB for ~2% standard error.
//
// The algorithm works by:
// 1. Hashing each element to get a uniform random bit string
// 2. Using the first p bits to determine which register (bucket) to update
// 3. Counting the number of leading zeros in the remaining bits
// 4. Updating the register with the maximum value seen
// 5. Estimating cardinality using the harmonic mean of the registers
package hyperloglog

import (
	"errors"
	"fmt"
	"math"
	"math/bits"
)

// ErrInvalidPrecision is returned when precision is out of valid range.
var ErrInvalidPrecision = errors.New("precision must be between 4 and 16")

// HyperLogLog implements the HyperLogLog cardinality estimation algorithm.
type HyperLogLog struct {
	// p is the precision parameter (number of bits for register addressing).
	// The number of registers m = 2^p.
	p uint8

	// m is the number of registers (buckets).
	m uint32

	// registers stores the maximum leading zero count for each bucket.
	registers []uint8

	// alpha is the bias correction constant.
	alpha float64
}

// New creates a new HyperLogLog estimator with the given precision.
//
// The precision parameter p must be between 4 and 16 inclusive.
// - p=4:  16 registers,   ~1.6KB memory, ~26% standard error
// - p=8:  256 registers,  ~1.6KB memory, ~6.5% standard error
// - p=10: 1024 registers, ~1.6KB memory, ~3.25% standard error
// - p=12: 4096 registers, ~1.6KB memory, ~1.6% standard error
// - p=14: 16384 registers, ~16KB memory, ~0.8% standard error
// - p=16: 65536 registers, ~64KB memory, ~0.4% standard error
func New(p uint8) (*HyperLogLog, error) {
	if p < 4 || p > 16 {
		return nil, ErrInvalidPrecision
	}

	m := uint32(1) << p
	alpha := calculateAlpha(m)

	return &HyperLogLog{
		p:         p,
		m:         m,
		registers: make([]uint8, m),
		alpha:     alpha,
	}, nil
}

// calculateAlpha computes the bias correction constant based on the number of registers.
//
// For m >= 128, alpha = 0.7213 / (1 + 1.079 / m)
// For m = 64, alpha = 0.709
// For m = 32, alpha = 0.697
// For m = 16, alpha = 0.673
func calculateAlpha(m uint32) float64 {
	switch m {
	case 16:
		return 0.673
	case 32:
		return 0.697
	case 64:
		return 0.709
	default:
		return 0.7213 / (1.0 + 1.079/float64(m))
	}
}

// Add hashes the given data and updates the registers.
// This is the core operation: hash -> bucket assignment -> leading zero counting.
func (h *HyperLogLog) Add(data []byte) {
	hash := Hash(data)
	h.AddHash(hash)
}

// AddHash adds a pre-computed hash value to the HyperLogLog.
// This is useful when you want to control the hashing yourself.
func (h *HyperLogLog) AddHash(hash uint64) {
	// Use the first p bits for bucket index
	bucketIdx := hash >> (64 - h.p)

	// Use the remaining bits for leading zero counting
	remainingBits := hash << h.p

	// Count leading zeros in the remaining bits (plus 1 to avoid log(0))
	leadingZeros := uint8(bits.LeadingZeros64(remainingBits)) + 1

	// Update the register if we found more leading zeros
	if leadingZeros > h.registers[bucketIdx] {
		h.registers[bucketIdx] = leadingZeros
	}
}

// Estimate returns the estimated cardinality of the set.
//
// The estimation uses the harmonic mean of the registers:
// E = alpha * m^2 * (sum of 2^(-register[i]))^(-1)
//
// For small cardinalities, it uses Linear Counting instead.
// For very large cardinalities, it applies a correction factor.
func (h *HyperLogLog) Estimate() uint64 {
	// Calculate the raw estimate using harmonic mean
	var sum float64
	for _, v := range h.registers {
		sum += 1.0 / float64(uint64(1)<<v)
	}

	estimate := h.alpha * float64(h.m) * float64(h.m) / sum

	// Small cardinality correction using Linear Counting
	if estimate <= 2.5*float64(h.m) {
		// Count empty registers
		var emptyRegisters uint32
		for _, v := range h.registers {
			if v == 0 {
				emptyRegisters++
			}
		}
		if emptyRegisters > 0 {
			// Linear Counting: E = m * ln(m / V)
			// where V is the number of empty registers
			return uint64(float64(h.m) * math.Log(float64(h.m)/float64(emptyRegisters)))
		}
	}

	// Large cardinality correction
	if estimate > 143165576.5 { // 2^32 / 30
		estimate = -math.Pow(2, 32) * math.Log(1-estimate/math.Pow(2, 32))
	}

	return uint64(estimate)
}

// Merge combines another HyperLogLog into this one.
// Both HyperLogLog instances must have the same precision.
func (h *HyperLogLog) Merge(other *HyperLogLog) error {
	if h.p != other.p {
		return fmt.Errorf("cannot merge HyperLogLog with different precision: %d vs %d", h.p, other.p)
	}

	for i := uint32(0); i < h.m; i++ {
		if other.registers[i] > h.registers[i] {
			h.registers[i] = other.registers[i]
		}
	}

	return nil
}

// Reset clears all registers, allowing the HyperLogLog to be reused.
func (h *HyperLogLog) Reset() {
	for i := range h.registers {
		h.registers[i] = 0
	}
}

// Precision returns the precision parameter p.
func (h *HyperLogLog) Precision() uint8 {
	return h.p
}

// Registers returns the number of registers (m = 2^p).
func (h *HyperLogLog) Registers() uint32 {
	return h.m
}

// MemoryUsage returns the approximate memory usage in bytes.
func (h *HyperLogLog) MemoryUsage() uint32 {
	return h.m // 1 byte per register
}

// StandardError returns the theoretical standard error for this precision.
// Standard error = 1.04 / sqrt(m)
func (h *HyperLogLog) StandardError() float64 {
	return 1.04 / math.Sqrt(float64(h.m))
}

// Density returns the fraction of non-empty registers.
// This is useful for understanding the data distribution.
func (h *HyperLogLog) Density() float64 {
	var nonEmpty uint32
	for _, v := range h.registers {
		if v > 0 {
			nonEmpty++
		}
	}
	return float64(nonEmpty) / float64(h.m)
}

// RegisterStats returns statistics about the register distribution.
type RegisterStats struct {
	Min      uint8   // Minimum register value
	Max      uint8   // Maximum register value
	Average  float64 // Average register value
	Empty    uint32  // Number of empty registers
	NonEmpty uint32  // Number of non-empty registers
}

// GetRegisterStats returns statistics about the register distribution.
func (h *HyperLogLog) GetRegisterStats() RegisterStats {
	var min, max uint8
	var sum uint64
	var empty, nonEmpty uint32

	min = 255
	for _, v := range h.registers {
		if v < min {
			min = v
		}
		if v > max {
			max = v
		}
		sum += uint64(v)
		if v == 0 {
			empty++
		} else {
			nonEmpty++
		}
	}

	return RegisterStats{
		Min:      min,
		Max:      max,
		Average:  float64(sum) / float64(h.m),
		Empty:    empty,
		NonEmpty: nonEmpty,
	}
}

// Package hyperloglog provides a HyperLogLog cardinality estimation implementation.
//
// HyperLogLog is a probabilistic algorithm for counting the number of distinct elements
// in a multiset. It uses far less memory than exact counting while maintaining
// reasonable accuracy (standard error ~0.81%).
//
// Core Algorithm:
//   1. Hash each element to a fixed-size binary string
//   2. Split the hash into two parts: bucket index (p bits) and position info (remaining bits)
//   3. For each bucket, track the position of the leftmost 1-bit (rho value)
//   4. Estimate cardinality using harmonic mean of bucket values with corrections
package hyperloglog

import (
	"crypto/sha256"
	"encoding/binary"
	"math"
)

// Precision defines the number of bits used for bucket indexing.
// Higher p = more buckets = better accuracy but more memory.
// p ranges from 4 to 16. Common values: 10 (default), 14, 16.
type Precision uint8

const (
	// MinPrecision is the minimum allowed precision value.
	MinPrecision Precision = 4
	// MaxPrecision is the maximum allowed precision value.
	MaxPrecision Precision = 16
	// DefaultPrecision is the recommended precision for general use.
	DefaultPrecision Precision = 10
	// HashBytes is the number of bytes in the hash output.
	HashBytes = 8 // 64-bit hash
)

// Alpha constants for bias correction based on number of buckets (m = 2^p).
// These are calibrated constants that ensure unbiased estimation across different ranges.
var alphaConstants = map[uint32]float64{
	16: 0.673,
	32: 0.692,
	64: 0.709,
}

// HyperLogLog is the core data structure for cardinality estimation.
//
// Memory layout:
//   - m = 2^p registers, each storing a uint8 (rho value)
//   - Total memory: 2^p bytes
//   - For p=10: 1024 bytes (~1KB) for ~2% error
//   - For p=14: 16384 bytes (~16KB) for ~0.8% error
//   - For p=16: 65536 bytes (~64KB) for ~0.5% error
type HyperLogLog struct {
	p       Precision // Bucket precision (bits for bucket index)
	m       uint32    // Number of buckets = 2^p
	registers []uint8 // Array of m registers, each stores rho value
	sum     float64   // Cached harmonic mean sum (invalidated on update)
	valid   bool      // Whether the structure has been initialized
}

// New creates a new HyperLogLog instance with the default precision.
//
// For most use cases, DefaultPrecision (p=10) is recommended:
// - Memory: ~1KB
// - Standard error: ~2%
// - Good for cardinalities up to ~10^9
func New() *HyperLogLog {
	return NewWithPrecision(DefaultPrecision)
}

// NewWithPrecision creates a new HyperLogLog instance with the given precision.
//
// Precision selection guide:
//   p=4  : 16 buckets,  ~16 bytes, error ~12% (educational only)
//   p=8  : 256 buckets, ~256 bytes, error ~4.5%
//   p=10 : 1024 buckets, ~1KB, error ~2% (good balance)
//   p=14 : 16384 buckets, ~16KB, error ~0.8% (high accuracy)
//   p=16 : 65536 buckets, ~64KB, error ~0.5% (very high accuracy)
//
// The precision determines the number of buckets (2^p) and directly affects
// the trade-off between memory usage and estimation accuracy.
func NewWithPrecision(p Precision) *HyperLogLog {
	if p < MinPrecision || p > MaxPrecision {
		p = DefaultPrecision
	}
	m := uint32(1) << p // m = 2^p
	return &HyperLogLog{
		p:         p,
		m:         m,
		registers: make([]uint8, m),
	}
}

// Hash computes a 64-bit hash of the input data.
//
// HyperLogLog requires a good hash function that distributes inputs uniformly
// across the hash space. We use a truncated SHA-256 output for simplicity.
//
// In production systems, MurmurHash3 or CityHash are preferred for speed.
// The hash must satisfy:
//   - Uniform distribution: each bit is equally likely to be 0 or 1
//   - Avalanche effect: small input changes produce large output changes
//   - Deterministic: same input always produces same output
func (h *HyperLogLog) Hash(data []byte) uint64 {
	// Compute SHA-256 hash
	hash := sha256.Sum256(data)
	// Take first 8 bytes as our 64-bit hash
	return binary.BigEndian.Uint64(hash[:HashBytes])
}

// HashString is a convenience wrapper for hashing strings.
func (h *HyperLogLog) HashString(s string) uint64 {
	return h.Hash([]byte(s))
}

// Add inserts an element into the HyperLogLog sketch.
//
// Algorithm steps:
//   1. Hash the element to get a 64-bit value
//   2. Use the first p bits as the bucket index
//   3. Use the remaining (64-p) bits to find the position of the leftmost 1-bit
//   4. Update the bucket's register if the new rho value is larger
//
// The rho function counts the position of the leftmost 1-bit (1-indexed).
// For example, if the remaining bits are 000101..., rho = 4.
//
// Time complexity: O(1) per insertion
// Space complexity: O(2^p) bytes total
func (h *HyperLogLog) Add(data []byte) {
	hash := h.Hash(data)

	// Extract bucket index from the first p bits of the hash.
	// This determines which register will store our rho value.
	bucketIndex := h.extractBucketIndex(hash)

	// Count the position of the leftmost 1-bit in the remaining bits.
	// This is the rho value: position of first '1' bit (1-indexed).
	// If no 1-bit exists (all zeros), rho = number of remaining bits + 1.
	rho := h.countLeadingZeros(hash, h.p)

	// Update the register if this rho value is larger than what's stored.
	// We keep the maximum because larger rho values indicate more distinct elements.
	if rho > h.registers[bucketIndex] {
		h.registers[bucketIndex] = uint8(rho)
	}

	// Invalidate the cached sum so it will be recomputed on next Estimate().
	h.valid = false
}

// AddString is a convenience wrapper for adding strings.
func (h *HyperLogLog) AddString(s string) {
	h.Add([]byte(s))
}

// extractBucketIndex extracts the first p bits of the hash as the bucket index.
//
// The hash is split into two parts:
//   - First p bits: bucket index (0 to 2^p - 1)
//   - Remaining (64-p) bits: used for rho calculation
//
// Example with p=10:
//   hash = 0b1101010110 0101010110010101...
//   bucket = 0b1101010110 = 422
//   remaining = 0101010110010101...
func (h *HyperLogLog) extractBucketIndex(hash uint64) uint32 {
	// Use the top p bits of the hash as bucket index.
	// Shift right by (64-p) to get the top p bits.
	bucket := hash >> (64 - uint64(h.p))
	return uint32(bucket) & (h.m - 1) // Mask to p bits (equivalent to modulo 2^p)
}

// countLeadingZeros counts the position of the leftmost 1-bit in the remaining bits.
//
// Given the hash and bucket precision p:
//   1. Mask out the first p bits (bucket index)
//   2. Count leading zeros in the remaining bits
//   3. Return (leading_zeros + 1) as the rho value
//
// The rho value represents the "run length" - how many leading zeros before
// the first 1-bit. In a random bit stream, the expected value of rho is
// related to the cardinality by: E[rho] ≈ log2(n)
//
// For example with remaining bits "000101...":
//   leading zeros = 3
//   rho = 3 + 1 = 4 (the 1 is at position 4)
func (h *HyperLogLog) countLeadingZeros(hash uint64, p Precision) int {
	// Mask out the first p bits to get the remaining bits
	remaining := (hash << p) >> p // Keep only the bottom (64-p) bits

	// Count leading zeros in the remaining 64-p bits
	// We use bits.OnesCount64 to count trailing ones from the right
	// by reversing the bit order, or use math.Log2 for approximation

	// Method: find the position of the most significant 1-bit
	// If all bits are zero, return (64 - p) + 1
	if remaining == 0 {
		return int(64 - p) + 1
	}

	// Find the position of the highest set bit
	// The rho value is: (64 - p) - floor(log2(remaining))
	// But we need to count from the left among the remaining bits
	// Use bit.Len() which returns the position of the highest 1-bit
	bitLen := remaining.BitLen() // Returns position of highest 1-bit (1-indexed)

	// rho = number of remaining bits - position of highest 1-bit + 1
	// This equals the number of leading zeros + 1
	rho := int(64-p) - bitLen + 1
	return rho
}

// Estimate returns the current cardinality estimate.
//
// The estimation uses the harmonic mean of the register values with
// appropriate bias corrections for different ranges:
//
//   1. Small range correction (linear counting): when estimate is small
//   2. Raw harmonic mean: standard HyperLogLog estimation
//   3. Large range correction: for very large cardinalities
//
// The formula is:
//   Z = 1 / (1/r1 + 1/r2 + ... + 1/rm) * m  (harmonic mean)
//   estimate = alpha_m * m^2 / Z
//
// Where alpha_m is a calibration constant that depends on m.
func (h *HyperLogLog) Estimate() uint64 {
	// Recompute the harmonic mean sum if registers have changed
	if !h.valid {
		h.computeSum()
	}

	// Apply bias corrections based on the estimated range
	estimate := h.applyCorrections()

	// Ensure we never return zero for non-empty sketches
	if estimate == 0 && h.registersSum() > 0 {
		estimate = 1
	}

	return estimate
}

// computeSum calculates the harmonic mean sum of all registers.
//
// The harmonic mean is used because it's more robust to outliers than
// the arithmetic mean. In HyperLogLog, most registers will have small
// rho values, but a few may have large values - the harmonic mean
// gives less weight to these outliers.
//
// Sum = sum(2^(-register[i]) for i in 0..m-1)
func (h *HyperLogLog) computeSum() {
	sum := 0.0
	for _, reg := range h.registers {
		sum += math.Pow(2, -float64(reg))
	}
	h.sum = sum
	h.valid = true
}

// applyCorrections applies bias corrections to the raw estimate.
//
// Three correction regimes:
//   1. Small range (linear counting): When Z > 0.725 * m, use linear counting formula
//   2. Raw estimate: Standard HyperLogLog formula
//   3. Large range: Correction for very large cardinalities approaching 2^64
//
// These corrections reduce bias in the estimator at different cardinality ranges.
func (h *HyperLogLog) applyCorrections() float64 {
	m := float64(h.m)
	Z := m * h.sum // Harmonic mean denominator

	var estimate float64

	// Small range correction (linear counting regime)
	// When many buckets are still zero, the harmonic mean underestimates
	if Z == 0 {
		// All registers are zero - no elements added yet
		return 0
	}

	// Get the alpha constant for our number of buckets
	alpha := h.getAlpha()

	// Raw estimate using the standard HyperLogLog formula
	rawEstimate := alpha * m * m / Z

	// Small range correction: when estimate < 2.5 * m, use linear counting
	// This corrects for the bias when many buckets are empty
	if rawEstimate <= 2.5*m {
		// Count non-zero registers
		zeroCount := 0.0
		for _, reg := range h.registers {
			if reg == 0 {
				zeroCount++
			}
		}
		// Linear counting formula: m * ln(m / V) where V is zero count
		if zeroCount != 0 {
			estimate = m * math.Log(m/zeroCount)
		} else {
			estimate = rawEstimate
		}
	} else if rawEstimate > (1<<32) / 30 {
		// Large range correction: for very large cardinalities
		// When estimate approaches 2^64, we need exponential correction
		estimate = -((1 << 64) * math.Log(1-Z/m))
	} else {
		estimate = rawEstimate
	}

	return estimate
}

// getAlpha returns the calibration constant for the given number of buckets.
//
// Alpha constants are empirically derived to minimize mean squared error.
// For intermediate values of m, we interpolate between the known constants.
//
// The alpha constant compensates for the bias in the harmonic mean estimator.
func (h *HyperLogLog) getAlpha() float64 {
	m := h.m

	// Use pre-calibrated alpha values for small m
	if alpha, ok := alphaConstants[m]; ok {
		return alpha
	}

	// For larger m, use the asymptotic value
	return 0.7213 / (1 + 1.079/m)
}

// registersSum returns the sum of all register values.
func (h *HyperLogLog) registersSum() float64 {
	sum := 0.0
	for _, reg := range h.registers {
		sum += float64(reg)
	}
	return sum
}

// Reset clears all registers and resets the sketch to its initial state.
func (h *HyperLogLog) Reset() {
	for i := range h.registers {
		h.registers[i] = 0
	}
	h.valid = false
}

// Clone creates a deep copy of the HyperLogLog sketch.
func (h *HyperLogLog) Clone() *HyperLogLog {
	registers := make([]uint8, len(h.registers))
	copy(registers, h.registers)
	return &HyperLogLog{
		p:         h.p,
		m:         h.m,
		registers: registers,
		valid:     h.valid,
		sum:       h.sum,
	}
}

// Merge combines another HyperLogLog sketch into this one.
//
// Merging takes the element-wise maximum of corresponding registers.
// This is a key property of HyperLogLog: sketches can be merged without
// losing information, enabling distributed cardinality estimation.
//
// Both sketches must have the same precision (number of buckets).
// If precisions differ, an error is returned.
func (h *HyperLogLog) Merge(other *HyperLogLog) error {
	if h.m != other.m {
		return ErrPrecisionMismatch
	}

	for i := range h.registers {
		if other.registers[i] > h.registers[i] {
			h.registers[i] = other.registers[i]
		}
	}
	h.valid = false
	return nil
}

// Precision returns the precision parameter p of this sketch.
func (h *HyperLogLog) Precision() Precision {
	return h.p
}

// BucketCount returns the number of buckets (m = 2^p).
func (h *HyperLogLog) BucketCount() uint32 {
	return h.m
}

// MemoryBytes returns the approximate memory usage in bytes.
//
// Memory = 2^p bytes for the registers, plus small overhead for metadata.
func (h *HyperLogLog) MemoryBytes() int {
	return int(h.m) + 32 // registers + struct overhead
}

// RegisterValues returns a copy of the current register values.
// Useful for debugging and educational purposes.
func (h *HyperLogLog) RegisterValues() []uint8 {
	cp := make([]uint8, len(h.registers))
	copy(cp, h.registers)
	return cp
}

// MaxRegister returns the maximum register value.
func (h *HyperLogLog) MaxRegister() uint8 {
	max := uint8(0)
	for _, reg := range h.registers {
		if reg > max {
			max = reg
		}
	}
	return max
}

// AverageRegister returns the average register value.
func (h *HyperLogLog) AverageRegister() float64 {
	sum := 0.0
	for _, reg := range h.registers {
		sum += float64(reg)
	}
	return sum / float64(h.m)
}

// ZeroBucketCount returns the number of buckets with zero values.
func (h *HyperLogLog) ZeroBucketCount() int {
	count := 0
	for _, reg := range h.registers {
		if reg == 0 {
			count++
		}
	}
	return count
}

// StandardError computes the standard error of the estimate.
//
// The theoretical standard error of HyperLogLog is approximately:
//   SE = 0.81 / sqrt(m) = 0.81 / sqrt(2^p)
//
// This means:
//   p=10: SE ≈ 2.55%
//   p=14: SE ≈ 0.64%
//   p=16: SE ≈ 0.28%
//
// The actual error depends on the cardinality relative to m.
func (h *HyperLogLog) StandardError() float64 {
	return 0.81 / math.Sqrt(float64(h.m))
}

// ConfidenceInterval computes a confidence interval for the estimate.
//
// Returns (lower, upper) bounds for the given confidence level.
// Assumes the estimate follows a normal distribution (asymptotically true).
//
// For a 95% confidence interval:
//   [estimate - 1.96 * SE * estimate, estimate + 1.96 * SE * estimate]
//
// The confidence interval width is proportional to the standard error
// and the estimate magnitude.
func (h *HyperLogLog) ConfidenceInterval(estimate float64, confidenceLevel float64) (lower, upper float64) {
	// Get the z-score for the desired confidence level
	zScore := h.zScore(confidenceLevel)

	// Standard error as a fraction of the estimate
	seFraction := h.StandardError()

	// Compute the interval bounds
	margin := zScore * seFraction * estimate
	lower = estimate - margin
	upper = estimate + margin

	// Ensure lower bound is non-negative
	if lower < 0 {
		lower = 0
	}

	return lower, upper
}

// zScore returns the z-score (inverse CDF of standard normal) for the given confidence level.
// Uses a polynomial approximation for the inverse normal CDF.
func (h *HyperLogLog) zScore(confidenceLevel float64) float64 {
	// For common confidence levels, use hardcoded values
	switch {
	case confidenceLevel >= 0.999:
		return 3.291
	case confidenceLevel >= 0.99:
		return 2.576
	case confidenceLevel >= 0.95:
		return 1.96
	case confidenceLevel >= 0.90:
		return 1.645
	case confidenceLevel >= 0.80:
		return 1.282
	default:
		// Default to 95% confidence
		return 1.96
	}
}

// ExpectedCardinalityForMemory estimates the cardinality that can be estimated
// with a given memory budget and target precision.
//
// This helps users choose the right precision for their use case:
//   Memory | Precision | Max cardinality (approx)
//   1 KB   | p=10      | ~10^9
//   16 KB  | p=14      | ~10^11
//   64 KB  | p=16      | ~10^12
//
// The relationship is: max_cardinality ≈ 2^(64-p) for the hash space limit.
func ExpectedCardinalityForMemory(memoryBytes int) (Precision, float64) {
	// Find the maximum precision that fits in the memory budget
	var p Precision
	for p = MaxPrecision; p >= MinPrecision; p-- {
		if (1<<uint(p)) <= uint32(memoryBytes) {
			break
		}
	}

	// Estimate max cardinality based on hash space
	// With 64-bit hash, we can estimate up to ~2^64 elements
	// But accuracy degrades as cardinality approaches hash space
	maxCardinality := math.Pow(2, 64-float64(p))

	return p, maxCardinality
}

// PrecisionFromError computes the minimum precision needed to achieve
// a target standard error.
//
// Formula: p = ceil(log2((0.81 / targetSE)^2))
//
// Example:
//   targetSE = 0.01 (1%) → p = 14
//   targetSE = 0.005 (0.5%) → p = 16
func PrecisionFromError(targetSE float64) Precision {
	// p = ceil(log2((0.81 / targetSE)^2))
	m := math.Ceil(math.Pow(0.81/targetSE, 2))
	p := Precision(math.Ceil(math.Log2(m)))

	// Clamp to valid range
	if p < MinPrecision {
		p = MinPrecision
	}
	if p > MaxPrecision {
		p = MaxPrecision
	}

	return p
}

// ErrPrecisionMismatch is returned when trying to merge sketches with different precisions.
var ErrPrecisionMismatch = &PrecisionMismatchError{}

// PrecisionMismatchError indicates a precision mismatch during merge.
type PrecisionMismatchError struct {
	p1, p2 Precision
}

func (e *PrecisionMismatchError) Error() string {
	return fmt.Sprintf("precision mismatch: %d vs %d", e.p1, e.p2)
}

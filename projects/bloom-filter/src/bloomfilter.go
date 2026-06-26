// Package bloomfilter implements a Bloom Filter and its variants.
//
// A Bloom filter is a space-efficient probabilistic data structure used
// to test whether an element is a member of a set. False positive matches
// are possible, but false negatives are not -- i.e. a query returns either
// "maybe in set" or "definitely not in set".
//
// Core concepts:
//   - Bit array: A large array of bits, all initialized to 0
//   - Hash functions: k independent hash functions map elements to bit positions
//   - Insert: Set k bit positions to 1 for each element
//   - Query: Check if all k bit positions are 1
//
// False positive rate formula:
//   p ≈ (1 - e^(-kn/m))^k
//   where n = number of inserted elements, m = bit array size, k = number of hash functions
//
// Optimal parameters:
//   m = -(n * ln(p)) / (ln(2))^2
//   k = (m / n) * ln(2)
package bloomfilter

import (
	"crypto/sha256"
	"encoding/binary"
	"fmt"
	"math"
	"sync"
)

// BloomFilter is the core probabilistic data structure.
// It uses multiple hash functions to map elements to bit positions in a bit array.
type BloomFilter struct {
	bitSet   []uint64 // underlying bit array stored as uint64 chunks
	size     uint64   // total number of bits
	hashCount uint64  // number of hash functions (k)
	elementCount uint64 // number of elements inserted
	mu       sync.RWMutex
}

// New creates a new Bloom filter with given bit array size and number of hash functions.
//
// Parameters:
//   - size: total number of bits in the bit array
//   - k: number of independent hash functions to use
//
// The bit array is initialized to all zeros.
func New(size uint64, k uint64) *BloomFilter {
	chunks := (size + 63) / 64 // number of uint64 chunks needed
	return &BloomFilter{
		bitSet:    make([]uint64, chunks),
		size:      size,
		hashCount: k,
	}
}

// NewOptimal creates a Bloom filter with optimal parameters for the given
// expected number of elements and target false positive rate.
//
// Uses the formulas:
//   m = -(n * ln(p)) / (ln(2))^2
//   k = round((m / n) * ln(2))
//
// Parameters:
//   - n: expected number of elements to insert
//   - p: desired false positive rate (e.g., 0.01 for 1%)
//
// Returns the Bloom filter, or an error if parameters are invalid.
func NewOptimal(n uint64, p float64) (*BloomFilter, error) {
	if n == 0 {
		return nil, fmt.Errorf("expected elements must be positive")
	}
	if p <= 0 || p >= 1 {
		return nil, fmt.Errorf("false positive rate must be in (0, 1)")
	}

	ln2 := math.Log(2)
	m := math.Ceil(-float64(n) * math.Log(p) / (ln2 * ln2))
	k := math.Round((m / float64(n)) * ln2)

	if k < 1 {
		k = 1
	}
	if m < float64(k) {
		m = float64(k)
	}

	return New(uint64(m), uint64(k)), nil
}

// NewFromFP calculates optimal parameters from expected elements and false positive rate,
// then creates a Bloom filter with those parameters. This is a convenience wrapper
// around NewOptimal.
func NewFromFP(n uint64, fp float64) (*BloomFilter, error) {
	return NewOptimal(n, fp)
}

// hashWithSalt generates k hash values for the given data using SHA-256 with different salts.
//
// Uses a single hash function (SHA-256) with different salt prefixes to generate
// k independent-looking hash values. This is more efficient than using k different
// hash algorithms while still providing good distribution.
//
// For each hash i (0 <= i < k):
//   1. Compute SHA-256(salt_prefix_i + data)
//   2. Extract two 32-bit values from the hash output
//   3. Combine them using double-hashing: h = h1 + i*h2
//
// This double-hashing technique (from Kirsch & Mitzenmacher) allows generating
// many hash functions from just two base hashes.
func (bf *BloomFilter) hashWithSalt(data []byte) []uint64 {
	positions := make([]uint64, bf.hashCount)

	// Use double-hashing: generate two base hashes, then derive k hashes from them
	// h(i) = h1 + i * h2  (for i = 0, 1, ..., k-1)
	// This only requires two SHA-256 computations regardless of k
	for i := uint64(0); i < bf.hashCount; i++ {
		// Create salted input: each hash gets a unique prefix
		salted := make([]byte, 8, 40)
		copy(salted, binary.BigEndian.AppendUint64(nil, i))
		salted = append(salted, data...)

		// Compute SHA-256 of salted input
		hash := sha256.Sum256(salted)

		// Extract two 32-bit values from the hash
		h1 := binary.BigEndian.Uint32(hash[0:4])
		h2 := binary.BigEndian.Uint32(hash[4:8])

		// Double hashing: combine h1 and h2 to get a unique position
		// h(i) = (h1 + i * h2) mod size
		// Using Montgomery multiplication to avoid overflow
		pos := doubleHash(h1, h2, i, bf.size)
		positions[i] = pos
	}

	return positions
}

// doubleHash implements the Kirsch-Mitzenmacher double hashing technique.
// It generates k hash values from two base hashes h1 and h2.
func doubleHash(h1, h2, i, size uint64) uint64 {
	if h2 == 0 {
		h2 = 1 // avoid division by zero
	}
	// h(i) = (h1 + i * h2) mod size
	// Use high-multiply technique to avoid overflow:
	// (a + i*b) mod m = ((a mod m) + ((i mod m) * (b mod m)) mod m) mod m
	h1Mod := h1 % size
	iMod := i % size
	h2Mod := h2 % size
	return (h1Mod + ((iMod * h2Mod) % size)) % size
}

// Add inserts an element into the Bloom filter.
//
// Sets the bit positions corresponding to all k hash values of the element.
// This operation is always safe (no false negatives possible).
func (bf *BloomFilter) Add(data []byte) {
	bf.mu.Lock()
	defer bf.mu.Unlock()

	positions := bf.hashWithSalt(data)
	for _, pos := range positions {
		setBit(bf.bitSet, pos)
	}
	bf.elementCount++
}

// AddString inserts a string element into the Bloom filter.
func (bf *BloomFilter) AddString(s string) {
	bf.Add([]byte(s))
}

// Contains checks if an element might be in the Bloom filter.
//
// Returns true if ALL bit positions are set (element "might" be present).
// Returns false if ANY bit position is not set (element "definitely" not present).
//
// IMPORTANT: A true result is a "maybe" -- there is a false positive probability.
// A false result is definitive -- the element was never inserted.
func (bf *BloomFilter) Contains(data []byte) bool {
	bf.mu.RLock()
	defer bf.mu.RUnlock()

	positions := bf.hashWithSalt(data)
	for _, pos := range positions {
		if !getBit(bf.bitSet, pos) {
			return false // definitely not in the filter
		}
	}
	return true // might be in the filter
}

// ContainsString checks if a string element might be in the Bloom filter.
func (bf *BloomFilter) ContainsString(s string) bool {
	return bf.Contains([]byte(s))
}

// Reset clears all bits in the filter, effectively removing all elements.
// The filter structure (size, hash count) is preserved.
func (bf *BloomFilter) Reset() {
	bf.mu.Lock()
	defer bf.mu.Unlock()

	for i := range bf.bitSet {
		bf.bitSet[i] = 0
	}
	bf.elementCount = 0
}

// Merge combines two Bloom filters using bitwise OR.
//
// The result contains the union of all elements from both filters.
// Both filters must have the same size.
//
// After merging, the false positive rate will be higher than either filter alone.
// This is useful for distributed systems where multiple nodes maintain local filters.
func (bf *BloomFilter) Merge(other *BloomFilter) error {
	bf.mu.Lock()
	defer bf.mu.Unlock()

	other.mu.RLock()
	defer other.mu.RUnlock()

	if bf.size != other.size {
		return fmt.Errorf("cannot merge filters of different sizes: %d vs %d", bf.size, other.size)
	}

	for i := range bf.bitSet {
		bf.bitSet[i] |= other.bitSet[i]
	}
	return nil
}

// MergeMultiple merges multiple Bloom filters into one.
// All filters must have the same size.
func (bf *BloomFilter) MergeMultiple(others []*BloomFilter) error {
	for _, other := range others {
		if err := bf.Merge(other); err != nil {
			return err
		}
	}
	return nil
}

// ElementCount returns the number of elements that have been inserted.
func (bf *BloomFilter) ElementCount() uint64 {
	bf.mu.RLock()
	defer bf.mu.RUnlock()
	return bf.elementCount
}

// Size returns the total number of bits in the bit array.
func (bf *BloomFilter) Size() uint64 {
	bf.mu.RLock()
	defer bf.mu.RUnlock()
	return bf.size
}

// HashCount returns the number of hash functions (k).
func (bf *BloomFilter) HashCount() uint64 {
	bf.mu.RLock()
	defer bf.mu.RUnlock()
	return bf.hashCount
}

// SetCount returns the number of bits currently set to 1.
func (bf *BloomFilter) SetCount() uint64 {
	bf.mu.RLock()
	defer bf.mu.RUnlock()

	var count uint64
	for _, word := range bf.bitSet {
		count += uint64(popcount(word))
	}
	return count
}

// popcount counts the number of set bits in a uint64 (population count).
func popcount(x uint64) uint64 {
	// SWAR (SIMD Within A Register) algorithm
	x -= ((x >> 1) & 0x5555555555555555)
	x = ((x >> 2) & 0x3333333333333333) + (x & 0x3333333333333333)
	x += (x >> 4)
	x &= 0x0f0f0f0f0f0f0f0f
	x *= 0x0101010101010101
	return x >> 56
}

// FalsePositiveRate computes the theoretical false positive rate.
//
// Uses the formula: p = (1 - e^(-kn/m))^k
//
// Parameters:
//   - n: number of elements inserted (use actual count or expected count)
//
// The false positive rate depends on the ratio of inserted elements to bit array size.
func (bf *BloomFilter) FalsePositiveRate(n uint64) float64 {
	if n == 0 {
		return 0
	}
	m := float64(bf.size)
	k := float64(bf.hashCount)

	// p = (1 - e^(-kn/m))^k
	exponent := -k * float64(n) / m
	p := math.Pow(1-math.Exp(exponent), k)
	return p
}

// ExpectedFalsePositiveRate computes the false positive rate using the actual
// number of inserted elements.
func (bf *BloomFilter) ExpectedFalsePositiveRate() float64 {
	return bf.FalsePositiveRate(bf.elementCount)
}

// OptimalK returns the optimal number of hash functions for the given number of elements.
//
// k_opt = (m/n) * ln(2) ≈ 0.693 * (m/n)
func (bf *BloomFilter) OptimalK(n uint64) uint64 {
	if n == 0 {
		return bf.hashCount
	}
	return uint64(math.Round((float64(bf.size) / float64(n)) * math.Log(2)))
}

// OptimalSize returns the optimal bit array size for the given number of elements
// and false positive rate.
//
// m = -(n * ln(p)) / (ln(2))^2
func OptimalSize(n uint64, p float64) uint64 {
	if n == 0 {
		return 0
	}
	if p <= 0 || p >= 1 {
		return 0
	}
	ln2 := math.Log(2)
	return uint64(math.Ceil(-float64(n) * math.Log(p) / (ln2 * ln2)))
}

// BitsPerElement returns the number of bits per element for the current filter.
func (bf *BloomFilter) BitsPerElement() float64 {
	if bf.elementCount == 0 {
		return float64(bf.size)
	}
	return float64(bf.size) / float64(bf.elementCount)
}

// Info returns a human-readable summary of the Bloom filter state.
func (bf *BloomFilter) Info() string {
	fp := bf.ExpectedFalsePositiveRate()
	return fmt.Sprintf(
		"BloomFilter{size: %d bits, k: %d, elements: %d, set_bits: %d, bpe: %.2f, fp_rate: %.6f}",
		bf.size, bf.hashCount, bf.elementCount, bf.SetCount(), bf.BitsPerElement(), fp,
	)
}

// --- Counting Bloom Filter ---

// CountingBloomFilter is a variant that uses counters instead of single bits.
// This allows deletion of elements, at the cost of more memory (n bits per counter).
//
// Each counter can hold a count of how many hash functions mapped to that position.
// When deleting, we decrement the counters. If all counters for an element reach 0,
// the element is considered removed.
//
// Trade-off: Supports deletion but uses more memory and has higher false positive rate.
type CountingBloomFilter struct {
	counters   []uint8       // array of counters (each 8 bits, max value 255)
	size       uint64        // total number of counters
	hashCount  uint64        // number of hash functions
	elementCount uint64     // number of elements inserted
	countBits  uint          // bits per counter (1, 2, 4, or 8)
	mu         sync.RWMutex
}

// CountingBloomConfig holds configuration for CountingBloomFilter.
type CountingBloomConfig struct {
	ExpectedElements uint64 // expected number of elements
	FalsePositiveRate float64 // target false positive rate
	CountBits        uint   // bits per counter (1, 2, 4, or 8). Default: 8
}

// NewCountingBloom creates a CountingBloomFilter with optimal parameters.
func NewCountingBloom(cfg CountingBloomConfig) (*CountingBloomFilter, error) {
	if cfg.ExpectedElements == 0 {
		return nil, fmt.Errorf("expected elements must be positive")
	}
	if cfg.FalsePositiveRate <= 0 || cfg.FalsePositiveRate >= 1 {
		return nil, fmt.Errorf("false positive rate must be in (0, 1)")
	}

	// Calculate optimal bit array size
	m := OptimalSize(cfg.ExpectedElements, cfg.FalsePositiveRate)
	k := uint64(math.Round((float64(m) / float64(cfg.ExpectedElements)) * math.Log(2)))
	if k < 1 {
		k = 1
	}

	// Determine bits per counter
	countBits := cfg.CountBits
	if countBits == 0 {
		countBits = 8 // default: 8 bits per counter (max value 255)
	}
	switch countBits {
	case 1, 2, 4, 8:
	default:
		return nil, fmt.Errorf("count bits must be 1, 2, 4, or 8, got %d", countBits)
	}

	// Total counters = m / countBits (each counter uses countBits bits)
	// But we need to be careful: size is in bits, each counter is countBits bits
	totalCounters := m / uint64(countBits)
	if totalCounters == 0 {
		totalCounters = 1
	}

	chunks := (totalCounters + 7) / 8 // number of uint64 chunks for counters
	return &CountingBloomFilter{
		counters:    make([]uint64, chunks),
		size:        totalCounters,
		hashCount:   k,
		countBits:   countBits,
	}, nil
}

// NewCountingBloomSimple creates a CountingBloomFilter with a simpler interface.
func NewCountingBloomSimple(expected uint64, fp float64) (*CountingBloomFilter, error) {
	return NewCountingBloom(CountingBloomConfig{
		ExpectedElements: expected,
		FalsePositiveRate: fp,
		CountBits:        8,
	})
}

// getCounterIndex returns the index and bit offset for a counter position.
func (cbf *CountingBloomFilter) getCounterIndex(pos uint64) (uint64, uint) {
	chunkIdx := pos / uint64(8)
	bitOffset := pos % uint64(8)
	return chunkIdx, uint(bitOffset)
}

// getCounterValue retrieves the value of a counter at the given position.
func (cbf *CountingBloomFilter) getCounterValue(chunkIdx uint64, bitOffset uint) uint8 {
	mask := uint64((1 << cbf.countBits) - 1)
	shift := (bitOffset * cbf.countBits) & 63 // mask by 63 to avoid overflow
	return uint8((cbf.counters[chunkIdx] >> shift) & mask)
}

// setCounterValue sets the value of a counter at the given position.
func (cbf *CountingBloomFilter) setCounterValue(chunkIdx uint64, bitOffset uint, value uint8) {
	mask := uint64((1 << cbf.countBits) - 1)
	shift := (bitOffset * cbf.countBits) & 63
	// Clear existing bits
	cbf.counters[chunkIdx] &^= (mask << shift)
	// Set new value
	cbf.counters[chunkIdx] |= uint64(value&mask) << shift
}

// addCounterValue increments a counter with saturation (max value).
func (cbf *CountingBloomFilter) addCounterValue(chunkIdx uint64, bitOffset uint, delta int8) {
	shift := (bitOffset * cbf.countBits) & 63
	mask := uint64((1 << cbf.countBits) - 1)
	current := (cbf.counters[chunkIdx] >> shift) & mask

	if delta > 0 {
		// Saturate at max value
		maxVal := uint8(mask)
		if current < maxVal {
			cbf.counters[chunkIdx] |= uint64(current+uint8(delta)) << shift
		}
	} else {
		// Decrement, but don't go below 0
		if current > 0 {
			cbf.counters[chunkIdx] &^= (mask << shift)
			cbf.counters[chunkIdx] |= uint64(current-uint8(-delta)) << shift
		}
	}
}

// Add inserts an element into the counting Bloom filter.
func (cbf *CountingBloomFilter) Add(data []byte) {
	cbf.mu.Lock()
	defer cbf.mu.Unlock()

	positions := cbf.hashPositions(data)
	for _, pos := range positions {
		chunkIdx, bitOffset := cbf.getCounterIndex(pos % cbf.size)
		cbf.addCounterValue(chunkIdx, bitOffset, 1)
	}
	cbf.elementCount++
}

// AddString inserts a string element into the counting Bloom filter.
func (cbf *CountingBloomFilter) AddString(s string) {
	cbf.Add([]byte(s))
}

// Remove removes an element from the counting Bloom filter.
//
// IMPORTANT: Only remove elements that were previously added.
// Incorrect removal (removing an element never added) can cause false negatives.
func (cbf *CountingBloomFilter) Remove(data []byte) {
	cbf.mu.Lock()
	defer cbf.mu.Unlock()

	positions := cbf.hashPositions(data)
	for _, pos := range positions {
		chunkIdx, bitOffset := cbf.getCounterIndex(pos % cbf.size)
		cbf.addCounterValue(chunkIdx, bitOffset, -1)
	}
}

// Contains checks if an element might be in the counting Bloom filter.
//
// For counting Bloom filters, we check if ALL corresponding counters are > 0.
// If any counter is 0, the element was definitely not inserted.
func (cbf *CountingBloomFilter) Contains(data []byte) bool {
	cbf.mu.RLock()
	defer cbf.mu.RUnlock()

	positions := cbf.hashPositions(data)
	for _, pos := range positions {
		chunkIdx, bitOffset := cbf.getCounterIndex(pos % cbf.size)
		val := cbf.getCounterValue(chunkIdx, bitOffset)
		if val == 0 {
			return false
		}
	}
	return true
}

// ContainsString checks if a string element might be in the counting Bloom filter.
func (cbf *CountingBloomFilter) ContainsString(s string) bool {
	return cbf.Contains([]byte(s))
}

// hashPositions generates hash positions for the counting Bloom filter.
func (cbf *CountingBloomFilter) hashPositions(data []byte) []uint64 {
	positions := make([]uint64, cbf.hashCount)
	for i := uint64(0); i < cbf.hashCount; i++ {
		salted := make([]byte, 8, 40)
		copy(salted, binary.BigEndian.AppendUint64(nil, i))
		salted = append(salted, data...)

		hash := sha256.Sum256(salted)
		h1 := binary.BigEndian.Uint32(hash[0:4])
		h2 := binary.BigEndian.Uint32(hash[4:8])

		if h2 == 0 {
			h2 = 1
		}
		h1Mod := h1 % uint32(cbf.size)
		iMod := i % uint32(cbf.size)
		h2Mod := h2 % uint32(cbf.size)
		positions[i] = uint64((uint64(h1Mod) + (uint64(iMod) * uint64(h2Mod)) % uint64(cbf.size)) % uint64(cbf.size))
	}
	return positions
}

// Reset clears all counters in the filter.
func (cbf *CountingBloomFilter) Reset() {
	cbf.mu.Lock()
	defer cbf.mu.Unlock()

	for i := range cbf.counters {
		cbf.counters[i] = 0
	}
	cbf.elementCount = 0
}

// ElementCount returns the number of elements inserted.
func (cbf *CountingBloomFilter) ElementCount() uint64 {
	cbf.mu.RLock()
	defer cbf.mu.RUnlock()
	return cbf.elementCount
}

// Size returns the number of counters.
func (cbf *CountingBloomFilter) Size() uint64 {
	cbf.mu.RLock()
	defer cbf.mu.RUnlock()
	return cbf.size
}

// HashCount returns the number of hash functions.
func (cbf *CountingBloomFilter) HashCount() uint64 {
	cbf.mu.RLock()
	defer cbf.mu.RUnlock()
	return cbf.hashCount
}

// CountBits returns the number of bits per counter.
func (cbf *CountingBloomFilter) CountBits() uint {
	cbf.mu.RLock()
	defer cbf.mu.RUnlock()
	return cbf.countBits
}

// Info returns a human-readable summary of the counting Bloom filter state.
func (cbf *CountingBloomFilter) Info() string {
	return fmt.Sprintf(
		"CountingBloomFilter{counters: %d, k: %d, elements: %d, count_bits: %d}",
		cbf.size, cbf.hashCount, cbf.elementCount, cbf.countBits,
	)
}

// --- Helper: bit operations ---

// setBit sets the bit at position pos in the bit array.
func setBit(bits []uint64, pos uint64) {
	chunkIdx := pos / 64
	bitOffset := pos % 64
	bits[chunkIdx] |= (1 << bitOffset)
}

// getBit checks if the bit at position pos is set.
func getBit(bits []uint64, pos uint64) bool {
	chunkIdx := pos / 64
	bitOffset := pos % 64
	return (bits[chunkIdx] & (1 << bitOffset)) != 0
}

// --- Utility functions for parameter calculation ---

// CalculateOptimalParams computes the optimal bit array size and hash count
// for a given number of expected elements and target false positive rate.
//
// Returns (m, k) where:
//   - m = bit array size
//   - k = number of hash functions
func CalculateOptimalParams(n uint64, p float64) (m uint64, k uint64) {
	if n == 0 || p <= 0 || p >= 1 {
		return 0, 0
	}
	ln2 := math.Log(2)
	m = uint64(math.Ceil(-float64(n) * math.Log(p) / (ln2 * ln2)))
	k = uint64(math.Round((float64(m) / float64(n)) * ln2))
	if k < 1 {
		k = 1
	}
	if m < uint64(k) {
		m = uint64(k)
	}
	return m, k
}

// CalculateFalsePositiveRate computes the false positive rate given m, k, and n.
//
// Formula: p = (1 - e^(-kn/m))^k
func CalculateFalsePositiveRate(m uint64, k uint64, n uint64) float64 {
	if m == 0 || n == 0 {
		return 0
	}
	exponent := -float64(k) * float64(n) / float64(m)
	p := math.Pow(1-math.Exp(exponent), float64(k))
	return p
}

// BitsPerElementRatio calculates the bits per element ratio for a given
// false positive rate. This is useful for comparing Bloom filter efficiency.
//
// For p = 0.01 (1%): ~9.6 bits per element
// For p = 0.001 (0.1%): ~14.4 bits per element
// For p = 0.0001 (0.01%): ~19.2 bits per element
func BitsPerElementRatio(p float64) float64 {
	if p <= 0 || p >= 1 {
		return 0
	}
	ln2 := math.Log(2)
	return -math.Log(p) / (ln2 * ln2)
}

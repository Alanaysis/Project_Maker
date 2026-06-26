package streaming

import (
	"fmt"
	"math"
	"sync"
)

// BloomFilter implements a Bloom filter probabilistic data structure.
//
// A Bloom filter is a space-efficient probabilistic structure for testing
// whether an element is a member of a set. It can return "definitely not in
// set" or "probably in set" (with a configurable false positive rate).
//
// Key properties:
//   - False negatives: impossible (never returns "not in set" for added elements)
//   - False positives: possible (may return "in set" for never-added elements)
//   - Space: much smaller than a hash set for large collections
//   - No deletions: standard Bloom filters do not support element removal
//
// The false positive rate depends on:
//   - n: number of inserted elements
//   - m: number of bits in the bit array
//   - k: number of hash functions
//
// Optimal k = (m/n) * ln(2)
// Optimal m = -(n * ln(p)) / (ln(2)^2) where p is the target false positive rate
//
// Example usage:
//
//	bf := NewBloomFilter(1000, 0.01) // expect 1000 items, 1% false positive rate
//	bf.Add("hello")
//	bf.Add("world")
//	bf.Contains("hello")  // true
//	bf.Contains("foo")    // false (or very rarely, true)
type BloomFilter struct {
	mu        sync.RWMutex
	bitSet    []bool
	size      int
	hashCount int
}

// NewBloomFilter creates a Bloom filter optimized for n expected insertions
// with a target false positive rate of p.
//
// The optimal number of hash functions is computed as k = (m/n) * ln(2).
func NewBloomFilter(n int, p float64) *BloomFilter {
	// Calculate optimal bit array size
	m := int(math.Ceil(-(float64(n) * math.Log(p)) / (math.Log(2) * math.Log(2))))
	// Calculate optimal number of hash functions
	k := int(math.Round(float64(m) / float64(n) * math.Log(2)))
	if k < 1 {
		k = 1
	}
	if m < 1 {
		m = 1
	}

	return &BloomFilter{
		bitSet:    make([]bool, m),
		size:      m,
		hashCount: k,
	}
}

// Add inserts an element into the Bloom filter.
//
// The element is hashed hashCount times, and each hash sets a bit in the
// bit array. All hash positions must be set for the element to be considered
// "in set".
func (b *BloomFilter) Add(element string) {
	b.mu.Lock()
	defer b.mu.Unlock()

	hashes := b.generateHashes(element)
	for _, h := range hashes {
		b.bitSet[h%b.size] = true
	}
}

// Contains checks if an element might be in the Bloom filter.
//
// Returns true if all hash positions are set (element might be in set).
// Returns false if any hash position is not set (element is definitely not in set).
func (b *BloomFilter) Contains(element string) bool {
	b.mu.RLock()
	defer b.mu.RUnlock()

	hashes := b.generateHashes(element)
	for _, h := range hashes {
		if !b.bitSet[h%b.size] {
			return false
		}
	}
	return true
}

// generateHashes produces hashCount distinct hash values using double hashing.
func (b *BloomFilter) generateHashes(s string) []uint32 {
	h1 := hash1(s)
	h2 := hash2(s)
	hashes := make([]uint32, b.hashCount)
	for i := 0; i < b.hashCount; i++ {
		hashes[i] = h1 + uint32(i)*h2
	}
	return hashes
}

// EstimatedFalsePositiveRate returns the estimated false positive rate
// given the current number of inserted elements.
func (b *BloomFilter) EstimatedFalsePositiveRate(n int) float64 {
	return math.Pow(1-math.Exp(-float64(b.hashCount)*float64(n)/float64(b.size)), float64(b.hashCount))
}

// Count returns the number of bits set to true in the bit array.
func (b *BloomFilter) Count() int {
	b.mu.RLock()
	defer b.mu.RUnlock()

	count := 0
	for _, bit := range b.bitSet {
		if bit {
			count++
		}
	}
	return count
}

// String returns a string representation of the Bloom filter.
func (b *BloomFilter) String() string {
	return fmt.Sprintf("BloomFilter{size: %d, hashes: %d, bits_set: %d}",
		b.size, b.hashCount, b.Count())
}

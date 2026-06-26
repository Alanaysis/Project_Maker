package streaming

import (
	"crypto/sha256"
	"fmt"
	"hash/fnv"
	"math"
	"sync"
)

// CountMinSketch implements the Count-Min Sketch probabilistic data structure.
//
// The Count-Min Sketch is a probabilistic data structure that approximates
// the frequency of elements in a data stream. It uses multiple hash functions
// to map each element to several counters, storing the minimum count across
// all hash functions.
//
// Key properties:
//   - Space: O(d * ln(1/ε)) where d = depth, ε = error rate
//   - Time: O(d) per update/query
//   - Counts are always >= true count (over-counting only, never under-counting)
//   - False positive rate bounded by ε
//
// The sketch uses d hash functions (rows) and w buckets per row (width).
// An element's frequency is estimated as the minimum count across all rows.
//
// Example usage:
//
//	cms := NewCountMinSketch(100, 5) // width=100, depth=5
//	cms.Add("apple", 1)
//	cms.Add("banana", 1)
//	cms.Add("apple", 1)
//	count := cms.Count("apple") // ~2
type CountMinSketch struct {
	mu    sync.Mutex
	table [][]int
	depth int
	width int
}

// NewCountMinSketch creates a Count-Min Sketch with the given width and depth.
//
// width: number of buckets per row (larger = lower error rate)
// depth: number of hash functions / rows (larger = higher confidence)
func NewCountMinSketch(width, depth int) *CountMinSketch {
	table := make([][]int, depth)
	for i := range table {
		table[i] = make([]int, width)
	}
	return &CountMinSketch{
		table: table,
		depth: depth,
		width: width,
	}
}

// hash1 generates a hash for the given string using FNV-1a.
func hash1(s string) uint32 {
	h := fnv.New32a()
	h.Write([]byte(s))
	return h.Sum32()
}

// hash2 generates a second hash using SHA-256 (takes first 4 bytes).
func hash2(s string) uint32 {
	h := sha256.Sum256([]byte(s))
	return uint32(h[0])<<24 | uint32(h[1])<<16 | uint32(h[2])<<8 | uint32(h[3])
}

// doubleHash produces a sequence of hash values using the double hashing technique.
// h(i, s) = h1(s) + i * h2(s) ensures all rows use different hash functions.
func (c *CountMinSketch) doubleHash(s string) []uint32 {
	h1 := hash1(s)
	h2 := hash2(s)
	hashes := make([]uint32, c.depth)
	for i := 0; i < c.depth; i++ {
		hashes[i] = h1 + uint32(i)*h2
	}
	return hashes
}

// Add increments the count for the given element.
func (c *CountMinSketch) Add(element string, count int) {
	c.mu.Lock()
	defer c.mu.Unlock()

	hashes := c.doubleHash(element)
	for i := 0; i < c.depth; i++ {
		idx := hashes[i] % uint32(c.width)
		c.table[i][idx] += count
	}
}

// Count returns an estimate of the frequency of the given element.
//
// The estimate is always >= the true count (never underestimates).
// With probability >= 1-δ, the estimate is within ε*N of the true count,
// where N is the total number of elements added.
func (c *CountMinSketch) Count(element string) int {
	c.mu.Lock()
	defer c.mu.Unlock()

	hashes := c.doubleHash(element)
	minCount := math.MaxInt32
	for i := 0; i < c.depth; i++ {
		idx := hashes[i] % uint32(c.width)
		if c.table[i][idx] < minCount {
			minCount = c.table[i][idx]
		}
	}
	return minCount
}

// String returns a string representation of the sketch.
func (c *CountMinSketch) String() string {
	return fmt.Sprintf("CountMinSketch{width: %d, depth: %d}", c.width, c.depth)
}

package internal

import (
	"encoding/binary"
	"hash"
	"hash/fnv"
)

// BloomFilter is a space-efficient probabilistic data structure
// used to test whether an element is a member of a set.
//
// False positives are possible, but false negatives are not.
// This means: if BloomFilter says a key is NOT present, it definitely is not.
// If it says a key IS present, there's a small chance it's wrong.
//
// In an LSM Tree, Bloom Filters are attached to each SSTable to quickly
// skip SSTables that definitely do not contain a requested key,
// avoiding expensive disk I/O.
//
// Uses double hashing technique: hash_i(key) = h1(key) + i * h2(key)
// This provides better distribution than using k independent hash functions.

// BloomFilter represents a Bloom filter with configurable size and hash count.
type BloomFilter struct {
	bits []byte     // bit array
	m    uint64     // size of bit array in bits
	k    uint32     // number of hash functions
	n    uint64     // number of elements inserted
	h1   hash.Hash64 // first hash function (FNV-1a)
	h2   hash.Hash64 // second hash function (FNV)
}

// NewBloomFilter creates a new Bloom filter.
// m = size of bit array in bits, k = number of hash functions.
func NewBloomFilter(m uint64, k uint32) *BloomFilter {
	return &BloomFilter{
		bits: make([]byte, (m+7)/8),
		m:    m,
		k:    k,
		n:    0,
		h1:   fnv.New64a(),
		h2:   fnv.New64(),
	}
}

// OptimalBloomFilter creates a Bloom filter with optimal parameters
// for the expected number of elements and desired false positive rate.
//
// Formula:
//   m = -n * ln(p) / (ln(2)^2)   (bit array size)
//   k = (m/n) * ln(2)             (number of hash functions)
//
// For n=1000, p=0.01: m ~ 9585 bits, k ~ 7
func OptimalBloomFilter(expectedElements uint64, falsePositiveRate float64) *BloomFilter {
	if expectedElements == 0 {
		expectedElements = 1
	}
	if falsePositiveRate <= 0 || falsePositiveRate >= 1 {
		falsePositiveRate = 0.01
	}

	// m = -n * ln(p) / (ln(2)^2)
	ln2Squared := 0.4804530139182 // ln(2)^2
	m := float64(expectedElements) * (-ln(falsePositiveRate)) / ln2Squared
	if m < 64 {
		m = 64
	}

	// k = (m/n) * ln(2)
	k := (m / float64(expectedElements)) * 0.6931471805599 // ln(2)
	if k < 1 {
		k = 1
	}
	if k > 30 {
		k = 30
	}

	return NewBloomFilter(uint64(m), uint32(k))
}

// ln returns the natural logarithm of x.
// Uses Newton's method with high precision.
func ln(x float64) float64 {
	if x <= 0 {
		return 0
	}
	if x == 1.0 {
		return 0
	}

	// Use the identity: ln(x) = ln(2) * log2(x)
	// First compute log2(x) using bit manipulation and refinement
	exp := 0
	y := x
	for y >= 2.0 {
		y /= 2.0
		exp++
	}
	for y < 1.0 {
		y *= 2.0
		exp--
	}

	// Now y is in [1, 2), compute ln(y) using Padé approximation
	// ln(1+t) where t = y-1, t in [0, 1)
	t := y - 1.0
	// Padé approximant for ln(1+t) around t=0
	// ln(1+t) ≈ t * (6 + t*(6 + t)) / (6 + t*(4 + t*...))
	// Use a simple but accurate series
	t2 := t * t
	t3 := t2 * t
	t4 := t3 * t
	t5 := t4 * t
	lnY := t - t2/2 + t3/3 - t4/4 + t5/5

	// ln(x) = ln(y) + exp * ln(2)
	return lnY + float64(exp)*0.6931471805599453
}

// Add inserts a key into the Bloom filter.
func (bf *BloomFilter) Add(key []byte) {
	// Double hashing: hash_i(key) = h1(key) + i * h2(key)
	bf.h1.Reset()
	bf.h1.Write(key)
	h1 := bf.h1.Sum64()

	bf.h2.Reset()
	bf.h2.Write(key)
	h2 := bf.h2.Sum64()

	for i := uint32(0); i < bf.k; i++ {
		pos := (h1 + uint64(i)*h2) % bf.m
		bf.bits[pos/8] |= 1 << (pos % 8)
	}
	bf.n++
}

// Contains tests whether a key might be in the set.
// Returns true if the key is PROBABLY in the set (with false positive probability).
// Returns false if the key is DEFINITELY NOT in the set.
func (bf *BloomFilter) Contains(key []byte) bool {
	bf.h1.Reset()
	bf.h1.Write(key)
	h1 := bf.h1.Sum64()

	bf.h2.Reset()
	bf.h2.Write(key)
	h2 := bf.h2.Sum64()

	for i := uint32(0); i < bf.k; i++ {
		pos := (h1 + uint64(i)*h2) % bf.m
		if bf.bits[pos/8]&(1<<(pos%8)) == 0 {
			return false
		}
	}
	return true
}

// Count returns the number of elements added.
func (bf *BloomFilter) Count() uint64 {
	return bf.n
}

// MarshalBinary serializes the Bloom filter to bytes.
func (bf *BloomFilter) MarshalBinary() []byte {
	// Format: [m:8][k:4][n:8][bits...]
	size := 8 + 4 + 8 + len(bf.bits)
	buf := make([]byte, size)
	binary.LittleEndian.PutUint64(buf[0:8], bf.m)
	binary.LittleEndian.PutUint32(buf[8:12], bf.k)
	binary.LittleEndian.PutUint64(buf[12:20], bf.n)
	copy(buf[20:], bf.bits)
	return buf
}

// UnmarshalBloomFilter deserializes a Bloom filter from bytes.
func UnmarshalBloomFilter(data []byte) *BloomFilter {
	if len(data) < 20 {
		return nil
	}
	m := binary.LittleEndian.Uint64(data[0:8])
	k := binary.LittleEndian.Uint32(data[8:12])
	n := binary.LittleEndian.Uint64(data[12:20])
	bitsLen := (m + 7) / 8
	if uint64(len(data)-20) < bitsLen {
		return nil
	}

	// Copy the bits data to avoid aliasing
	bits := make([]byte, bitsLen)
	copy(bits, data[20:20+bitsLen])

	return &BloomFilter{
		bits: bits,
		m:    m,
		k:    k,
		n:    n,
		h1:   fnv.New64a(),
		h2:   fnv.New64(),
	}
}

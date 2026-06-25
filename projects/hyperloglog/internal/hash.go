package hyperloglog

import (
	"hash/fnv"
)

// Hash computes a 64-bit hash of the given byte slice.
// Uses FNV-1a hash algorithm which provides good distribution
// and is fast for general-purpose hashing.
//
// For production use, consider using MurmurHash3 or xxHash for better
// performance and distribution properties.
func Hash(data []byte) uint64 {
	h := fnv.New64a()
	h.Write(data)
	return h.Sum64()
}

// HashString is a convenience function for hashing strings.
func HashString(s string) uint64 {
	return Hash([]byte(s))
}

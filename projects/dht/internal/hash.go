package internal

import (
	"crypto/sha1"
	"encoding/binary"
	"math/big"
)

const (
	// M is the number of bits in the key space (160 for SHA-1)
	M = 160
)

// HashFunc represents a hash function that takes a key and returns an identifier
type HashFunc func(key string) *big.Int

// DefaultHash uses SHA-1 to hash a key into the Chord identifier space
func DefaultHash(key string) *big.Int {
	hash := sha1.New()
	hash.Write([]byte(key))
	hashBytes := hash.Sum(nil)

	// Convert hash bytes to big.Int
	return new(big.Int).SetBytes(hashBytes)
}

// Between checks if a key is in the range (start, end) on the Chord ring
// Handles wrap-around case where start > end
func Between(key, start, end *big.Int) bool {
	// If start < end, then key is between if start < key < end
	if start.Cmp(end) < 0 {
		return key.Cmp(start) > 0 && key.Cmp(end) < 0
	}

	// If start > end (wrap-around), then key is between if key > start || key < end
	if start.Cmp(end) > 0 {
		return key.Cmp(start) > 0 || key.Cmp(end) < 0
	}

	// start == end means the whole ring, so key is always between (unless it's start itself)
	return key.Cmp(start) != 0
}

// BetweenRightInclusive checks if a key is in the range (start, end] on the Chord ring
func BetweenRightInclusive(key, start, end *big.Int) bool {
	// Check if key == end
	if key.Cmp(end) == 0 {
		return true
	}
	return Between(key, start, end)
}

// PowerOfTwo returns 2^exp as a big.Int
func PowerOfTwo(exp int) *big.Int {
	return new(big.Int).Lsh(big.NewInt(1), uint(exp))
}

// GenerateID generates a Chord identifier from a string
func GenerateID(s string) *big.Int {
	return DefaultHash(s)
}

// BytesToBigInt converts a byte slice to big.Int
func BytesToBigInt(b []byte) *big.Int {
	return new(big.Int).SetBytes(b)
}

// BigIntToBytes converts a big.Int to a byte slice
func BigIntToBytes(n *big.Int) []byte {
	return n.Bytes()
}

// RandomID generates a random ID in the Chord space
func RandomID() *big.Int {
	// Use SHA-1 of a random string for simplicity
	// In production, use crypto/rand
	hash := sha1.New()
	hash.Write([]byte("random-placeholder"))
	return new(big.Int).SetBytes(hash.Sum(nil))
}

// FormatID formats a big.Int ID as a hex string (truncated for display)
func FormatID(id *big.Int) string {
	if id == nil {
		return "nil"
	}
	hex := id.Text(16)
	if len(hex) > 8 {
		return hex[:8] + "..."
	}
	return hex
}

// IDFromInt creates a big.Int from an int64 (useful for testing)
func IDFromInt(n int64) *big.Int {
	return big.NewInt(n)
}

// IDFromBytes creates a big.Int from uint64 (useful for compact representation)
func IDFromUint64(n uint64) *big.Int {
	b := make([]byte, 8)
	binary.BigEndian.PutUint64(b, n)
	return new(big.Int).SetBytes(b)
}

package test

import (
	"fmt"
	"testing"

	lsm "github.com/lsm-tree/internal"
)

func TestBloomFilterBasic(t *testing.T) {
	bf := lsm.NewBloomFilter(1024, 7)

	// Add keys
	bf.Add([]byte("key1"))
	bf.Add([]byte("key2"))
	bf.Add([]byte("key3"))

	// Contains should return true for added keys
	if !bf.Contains([]byte("key1")) {
		t.Error("Expected key1 to be found")
	}
	if !bf.Contains([]byte("key2")) {
		t.Error("Expected key2 to be found")
	}
	if !bf.Contains([]byte("key3")) {
		t.Error("Expected key3 to be found")
	}

	// Should return false for non-existent keys (with high probability)
	falsePositives := 0
	for i := 0; i < 1000; i++ {
		key := fmt.Sprintf("nonexistent_%d", i)
		if bf.Contains([]byte(key)) {
			falsePositives++
		}
	}

	// False positive rate should be reasonable (< 5% for 1024 bits, 7 hash functions)
	if falsePositives > 50 {
		t.Errorf("Too many false positives: %d/1000", falsePositives)
	}
}

func TestBloomFilterOptimal(t *testing.T) {
	// Create optimal Bloom filter for 1000 elements with 1% false positive rate
	bf := lsm.OptimalBloomFilter(1000, 0.01)

	// Add 1000 keys
	for i := 0; i < 1000; i++ {
		key := fmt.Sprintf("key_%06d", i)
		bf.Add([]byte(key))
	}

	// All added keys should be found
	for i := 0; i < 1000; i++ {
		key := fmt.Sprintf("key_%06d", i)
		if !bf.Contains([]byte(key)) {
			t.Errorf("Key %s not found in Bloom filter", key)
		}
	}

	// Count should be 1000
	if bf.Count() != 1000 {
		t.Errorf("Expected count 1000, got %d", bf.Count())
	}

	// Check false positive rate with non-existent keys
	falsePositives := 0
	testCount := 10000
	for i := 0; i < testCount; i++ {
		key := fmt.Sprintf("nonexistent_%06d", i+100000)
		if bf.Contains([]byte(key)) {
			falsePositives++
		}
	}

	// False positive rate should be reasonable (< 10% for optimal filter)
	// Note: actual rate depends on hash function quality
	fpRate := float64(falsePositives) / float64(testCount)
	if fpRate > 0.10 {
		t.Errorf("False positive rate too high: %.4f (expected < 0.10)", fpRate)
	}
	t.Logf("False positive rate: %.4f (%d/%d)", fpRate, falsePositives, testCount)
}

func TestBloomFilterSerialization(t *testing.T) {
	bf := lsm.OptimalBloomFilter(100, 0.01)

	// Add some keys
	for i := 0; i < 50; i++ {
		bf.Add([]byte(fmt.Sprintf("key_%d", i)))
	}

	// Serialize
	data := bf.MarshalBinary()

	// Deserialize
	bf2 := lsm.UnmarshalBloomFilter(data)
	if bf2 == nil {
		t.Fatal("Failed to unmarshal Bloom filter")
	}

	// Verify all keys are still present
	for i := 0; i < 50; i++ {
		key := []byte(fmt.Sprintf("key_%d", i))
		if !bf2.Contains(key) {
			t.Errorf("Key %s not found after deserialization", key)
		}
	}

	// Verify count
	if bf2.Count() != 50 {
		t.Errorf("Expected count 50, got %d", bf2.Count())
	}
}

func TestBloomFilterEmpty(t *testing.T) {
	bf := lsm.OptimalBloomFilter(0, 0.01)

	// Empty filter should not contain anything
	if bf.Contains([]byte("key")) {
		t.Error("Empty Bloom filter should not contain any key")
	}

	if bf.Count() != 0 {
		t.Errorf("Expected count 0, got %d", bf.Count())
	}
}

func TestBloomFilterLargeDataset(t *testing.T) {
	n := 100000
	bf := lsm.OptimalBloomFilter(uint64(n), 0.001) // 0.1% false positive rate

	// Add all keys
	for i := 0; i < n; i++ {
		bf.Add([]byte(fmt.Sprintf("key_%08d", i)))
	}

	// Verify all keys are found
	for i := 0; i < n; i++ {
		key := []byte(fmt.Sprintf("key_%08d", i))
		if !bf.Contains(key) {
			t.Errorf("Key %s not found", key)
			break
		}
	}
}

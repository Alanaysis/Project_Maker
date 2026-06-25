package hyperloglog

import (
	"fmt"
	"math"
	"testing"
)

func TestNewHyperLogLog(t *testing.T) {
	tests := []struct {
		name      string
		precision uint8
		wantErr   bool
	}{
		{"valid precision 4", 4, false},
		{"valid precision 8", 8, false},
		{"valid precision 10", 10, false},
		{"valid precision 12", 12, false},
		{"valid precision 14", 14, false},
		{"valid precision 16", 16, false},
		{"invalid precision 3", 3, true},
		{"invalid precision 17", 17, true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			hll, err := New(tt.precision)
			if (err != nil) != tt.wantErr {
				t.Errorf("New(%d) error = %v, wantErr %v", tt.precision, err, tt.wantErr)
				return
			}
			if !tt.wantErr {
				if hll.Precision() != tt.precision {
					t.Errorf("Precision() = %d, want %d", hll.Precision(), tt.precision)
				}
				expectedRegisters := uint32(1) << tt.precision
				if hll.Registers() != expectedRegisters {
					t.Errorf("Registers() = %d, want %d", hll.Registers(), expectedRegisters)
				}
			}
		})
	}
}

func TestAddAndEstimate(t *testing.T) {
	hll, _ := New(12) // 4096 registers, ~1.6% error

	// Add 10000 distinct elements
	for i := 0; i < 10000; i++ {
		hll.Add([]byte(fmt.Sprintf("element-%d", i)))
	}

	estimate := hll.Estimate()
	errorRate := math.Abs(float64(estimate)-10000) / 10000

	t.Logf("Actual cardinality: 10000")
	t.Logf("Estimated cardinality: %d", estimate)
	t.Logf("Error rate: %.2f%%", errorRate*100)

	// Error should be within 5% for p=12
	if errorRate > 0.05 {
		t.Errorf("Error rate %.2f%% exceeds 5%% threshold", errorRate*100)
	}
}

func TestAddDuplicates(t *testing.T) {
	hll, _ := New(12)

	// Add the same element multiple times
	for i := 0; i < 1000; i++ {
		hll.Add([]byte("duplicate-element"))
	}

	estimate := hll.Estimate()
	// Should estimate close to 1, not 1000
	if estimate > 10 {
		t.Errorf("Duplicate elements should estimate near 1, got %d", estimate)
	}
}

func TestReset(t *testing.T) {
	hll, _ := New(12)

	// Add some elements
	for i := 0; i < 100; i++ {
		hll.Add([]byte(fmt.Sprintf("element-%d", i)))
	}

	// Reset
	hll.Reset()

	// Should estimate 0 or very small
	estimate := hll.Estimate()
	if estimate > 10 {
		t.Errorf("After reset, estimate should be near 0, got %d", estimate)
	}
}

func TestMerge(t *testing.T) {
	hll1, _ := New(12)
	hll2, _ := New(12)

	// Add distinct elements to each
	for i := 0; i < 5000; i++ {
		hll1.Add([]byte(fmt.Sprintf("set1-%d", i)))
	}
	for i := 0; i < 5000; i++ {
		hll2.Add([]byte(fmt.Sprintf("set2-%d", i)))
	}

	// Merge hll2 into hll1
	err := hll1.Merge(hll2)
	if err != nil {
		t.Fatalf("Merge failed: %v", err)
	}

	estimate := hll1.Estimate()
	errorRate := math.Abs(float64(estimate)-10000) / 10000

	t.Logf("Merged estimate: %d (expected ~10000)", estimate)
	t.Logf("Error rate: %.2f%%", errorRate*100)

	if errorRate > 0.05 {
		t.Errorf("Merged error rate %.2f%% exceeds 5%% threshold", errorRate*100)
	}
}

func TestMergeDifferentPrecision(t *testing.T) {
	hll1, _ := New(12)
	hll2, _ := New(10)

	err := hll1.Merge(hll2)
	if err == nil {
		t.Error("Merge with different precision should fail")
	}
}

func TestMemoryUsage(t *testing.T) {
	tests := []struct {
		precision uint8
		expected  uint32
	}{
		{4, 16},
		{8, 256},
		{12, 4096},
		{16, 65536},
	}

	for _, tt := range tests {
		t.Run(fmt.Sprintf("p=%d", tt.precision), func(t *testing.T) {
			hll, _ := New(tt.precision)
			if hll.MemoryUsage() != tt.expected {
				t.Errorf("MemoryUsage() = %d, want %d", hll.MemoryUsage(), tt.expected)
			}
		})
	}
}

func TestStandardError(t *testing.T) {
	tests := []struct {
		precision uint8
		maxError  float64
	}{
		{4, 0.26},
		{8, 0.065},
		{12, 0.016},
		{16, 0.004},
	}

	for _, tt := range tests {
		t.Run(fmt.Sprintf("p=%d", tt.precision), func(t *testing.T) {
			hll, _ := New(tt.precision)
			se := hll.StandardError()
			if se > tt.maxError*1.1 { // Allow 10% tolerance
				t.Errorf("StandardError() = %f, want <= %f", se, tt.maxError)
			}
		})
	}
}

func TestDensity(t *testing.T) {
	hll, _ := New(12)

	// Initially all registers are empty
	density := hll.Density()
	if density != 0 {
		t.Errorf("Initial density should be 0, got %f", density)
	}

	// Add some elements
	for i := 0; i < 1000; i++ {
		hll.Add([]byte(fmt.Sprintf("element-%d", i)))
	}

	density = hll.Density()
	t.Logf("Density after 1000 elements: %.2f%%", density*100)

	// Density should be between 0 and 1
	if density <= 0 || density >= 1 {
		t.Errorf("Density should be between 0 and 1, got %f", density)
	}
}

func TestRegisterStats(t *testing.T) {
	hll, _ := New(12)

	// Add some elements
	for i := 0; i < 1000; i++ {
		hll.Add([]byte(fmt.Sprintf("element-%d", i)))
	}

	stats := hll.GetRegisterStats()

	t.Logf("Register stats: Min=%d, Max=%d, Avg=%.2f, Empty=%d, NonEmpty=%d",
		stats.Min, stats.Max, stats.Average, stats.Empty, stats.NonEmpty)

	if stats.Min > stats.Max {
		t.Errorf("Min (%d) should be <= Max (%d)", stats.Min, stats.Max)
	}

	if stats.Empty+stats.NonEmpty != hll.Registers() {
		t.Errorf("Empty + NonEmpty should equal total registers")
	}
}

func TestDifferentPrecisions(t *testing.T) {
	precisions := []uint8{4, 8, 10, 12, 14, 16}
	cardinality := 10000

	for _, p := range precisions {
		t.Run(fmt.Sprintf("p=%d", p), func(t *testing.T) {
			hll, _ := New(p)

			for i := 0; i < cardinality; i++ {
				hll.Add([]byte(fmt.Sprintf("element-%d", i)))
			}

			estimate := hll.Estimate()
			errorRate := math.Abs(float64(estimate)-float64(cardinality)) / float64(cardinality)

			t.Logf("p=%d: Estimated %d (actual %d, error %.2f%%)",
				p, estimate, cardinality, errorRate*100)

			// Error should be within theoretical bounds (with some tolerance)
			maxError := hll.StandardError() * 3 // 3 sigma
			if errorRate > maxError*1.5 {        // Allow 50% tolerance on theoretical bound
				t.Errorf("Error rate %.2f%% exceeds expected bound %.2f%%",
					errorRate*100, maxError*100)
			}
		})
	}
}

func TestSmallCardinality(t *testing.T) {
	hll, _ := New(12)

	// For very small cardinalities, Linear Counting should be used
	for i := 0; i < 10; i++ {
		hll.Add([]byte(fmt.Sprintf("small-%d", i)))
	}

	estimate := hll.Estimate()
	errorRate := math.Abs(float64(estimate)-10) / 10

	t.Logf("Small cardinality estimate: %d (actual 10, error %.2f%%)", estimate, errorRate*100)

	// Small cardinality estimates should be reasonably accurate
	if errorRate > 0.5 {
		t.Errorf("Small cardinality error rate %.2f%% exceeds 50%%", errorRate*100)
	}
}

func TestLargeCardinality(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping large cardinality test in short mode")
	}

	hll, _ := New(14) // 16384 registers for better accuracy

	// Add many elements
	for i := 0; i < 1000000; i++ {
		hll.Add([]byte(fmt.Sprintf("large-%d", i)))
	}

	estimate := hll.Estimate()
	errorRate := math.Abs(float64(estimate)-1000000) / 1000000

	t.Logf("Large cardinality estimate: %d (actual 1000000, error %.2f%%)", estimate, errorRate*100)

	// Error should be within 2% for p=14
	if errorRate > 0.02 {
		t.Errorf("Large cardinality error rate %.2f%% exceeds 2%% threshold", errorRate*100)
	}
}

func TestAddHash(t *testing.T) {
	hll, _ := New(12)

	// Add using pre-computed hash
	hash := Hash([]byte("test-element"))
	hll.AddHash(hash)

	estimate := hll.Estimate()
	if estimate == 0 {
		t.Error("Estimate should not be 0 after adding an element")
	}
}

func TestHash(t *testing.T) {
	// Test that hash function produces consistent results
	data := []byte("test-data")
	hash1 := Hash(data)
	hash2 := Hash(data)

	if hash1 != hash2 {
		t.Errorf("Hash should be deterministic: %d != %d", hash1, hash2)
	}

	// Test that different data produces different hashes (usually)
	data2 := []byte("different-data")
	hash3 := Hash(data2)

	if hash1 == hash3 {
		t.Error("Different data should produce different hashes")
	}
}

func TestHashString(t *testing.T) {
	hash1 := HashString("test-string")
	hash2 := Hash([]byte("test-string"))

	if hash1 != hash2 {
		t.Errorf("HashString and Hash should produce same result: %d != %d", hash1, hash2)
	}
}

func BenchmarkAdd(b *testing.B) {
	hll, _ := New(12)
	data := []byte("benchmark-element")

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		hll.Add(data)
	}
}

func BenchmarkEstimate(b *testing.B) {
	hll, _ := New(12)

	// Add some elements first
	for i := 0; i < 10000; i++ {
		hll.Add([]byte(fmt.Sprintf("element-%d", i)))
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		hll.Estimate()
	}
}

func BenchmarkHash(b *testing.B) {
	data := []byte("benchmark-element")

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		Hash(data)
	}
}

func BenchmarkMerge(b *testing.B) {
	hll1, _ := New(12)
	hll2, _ := New(12)

	for i := 0; i < 10000; i++ {
		hll1.Add([]byte(fmt.Sprintf("set1-%d", i)))
		hll2.Add([]byte(fmt.Sprintf("set2-%d", i)))
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		hll1.Merge(hll2)
	}
}

package bloomfilter_test

import (
	"math"
	"testing"

	"bloom-filter/src"
)

// TestBloomFilter_BasicOperations tests basic insert and query operations.
func TestBloomFilter_BasicOperations(t *testing.T) {
	filter := bloomfilter.New(1000, 7)

	// Insert elements
	filter.AddString("hello")
	filter.AddString("world")
	filter.AddString("test")

	// Query inserted elements - should always return true
	if !filter.ContainsString("hello") {
		t.Error("Expected 'hello' to be found")
	}
	if !filter.ContainsString("world") {
		t.Error("Expected 'world' to be found")
	}
	if !filter.ContainsString("test") {
		t.Error("Expected 'test' to be found")
	}

	// Query non-inserted elements - might return false positive
	// (we don't assert because false positives are possible)
	_ = filter.ContainsString("not_exist")
}

// TestBloomFilter_NewOptimal tests the optimal parameter calculation.
func TestBloomFilter_NewOptimal(t *testing.T) {
	filter, err := bloomfilter.NewOptimal(10000, 0.01)
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}

	if filter.Size() == 0 {
		t.Error("Expected non-zero filter size")
	}
	if filter.HashCount() == 0 {
		t.Error("Expected non-zero hash count")
	}

	// Verify elements can be inserted and found
	filter.AddString("test_element")
	if !filter.ContainsString("test_element") {
		t.Error("Inserted element not found")
	}
}

// TestBloomFilter_NewOptimalErrors tests error handling.
func TestBloomFilter_NewOptimalErrors(t *testing.T) {
	_, err := bloomfilter.NewOptimal(0, 0.01)
	if err == nil {
		t.Error("Expected error for zero elements")
	}

	_, err = bloomfilter.NewOptimal(1000, 0)
	if err == nil {
		t.Error("Expected error for zero FP rate")
	}

	_, err = bloomfilter.NewOptimal(1000, 1.0)
	if err == nil {
		t.Error("Expected error for FP rate = 1.0")
	}

	_, err = bloomfilter.NewOptimal(1000, -0.01)
	if err == nil {
		t.Error("Expected error for negative FP rate")
	}
}

// TestBloomFilter_Reset tests the reset functionality.
func TestBloomFilter_Reset(t *testing.T) {
	filter := bloomfilter.New(1000, 7)

	filter.AddString("hello")
	filter.AddString("world")

	// Should find elements before reset
	if !filter.ContainsString("hello") {
		t.Error("Expected 'hello' to be found before reset")
	}

	// Reset and verify
	filter.Reset()

	// After reset, elements should not be found
	if filter.ContainsString("hello") {
		t.Error("Expected 'hello' to NOT be found after reset")
	}
	if filter.ContainsString("world") {
		t.Error("Expected 'world' to NOT be found after reset")
	}

	// Element count should be zero
	if filter.ElementCount() != 0 {
		t.Errorf("Expected element count 0, got %d", filter.ElementCount())
	}
}

// TestBloomFilter_Merge tests the merge (bitwise OR) operation.
func TestBloomFilter_Merge(t *testing.T) {
	filter1, _ := bloomfilter.NewOptimal(1000, 0.01)
	filter2, _ := bloomfilter.NewOptimal(1000, 0.01)

	filter1.AddString("from_filter1")
	filter2.AddString("from_filter2")

	// Merge filter2 into filter1
	err := filter1.Merge(filter2)
	if err != nil {
		t.Fatalf("Merge failed: %v", err)
	}

	// Both should be found in the merged filter
	if !filter1.ContainsString("from_filter1") {
		t.Error("Expected 'from_filter1' to be found after merge")
	}
	if !filter1.ContainsString("from_filter2") {
		t.Error("Expected 'from_filter2' to be found after merge")
	}
}

// TestBloomFilter_MergeDifferentSizes tests merging filters of different sizes.
func TestBloomFilter_MergeDifferentSizes(t *testing.T) {
	filter1 := bloomfilter.New(1000, 7)
	filter2 := bloomfilter.New(2000, 10)

	err := filter1.Merge(filter2)
	if err == nil {
		t.Error("Expected error when merging filters of different sizes")
	}
}

// TestBloomFilter_MergeMultiple tests merging multiple filters.
func TestBloomFilter_MergeMultiple(t *testing.T) {
	filter1, _ := bloomfilter.NewOptimal(1000, 0.01)
	filter2, _ := bloomfilter.NewOptimal(1000, 0.01)
	filter3, _ := bloomfilter.NewOptimal(1000, 0.01)

	filter1.AddString("only_in_1")
	filter2.AddString("only_in_2")
	filter3.AddString("only_in_3")

	err := filter1.MergeMultiple([]*bloomfilter.BloomFilter{filter2, filter3})
	if err != nil {
		t.Fatalf("MergeMultiple failed: %v", err)
	}

	if !filter1.ContainsString("only_in_1") {
		t.Error("Expected 'only_in_1' to be found")
	}
	if !filter1.ContainsString("only_in_2") {
		t.Error("Expected 'only_in_2' to be found")
	}
	if !filter1.ContainsString("only_in_3") {
		t.Error("Expected 'only_in_3' to be found")
	}
}

// TestBloomFilter_ElementCount tests the element count tracking.
func TestBloomFilter_ElementCount(t *testing.T) {
	filter := bloomfilter.New(1000, 7)

	if filter.ElementCount() != 0 {
		t.Errorf("Expected initial count 0, got %d", filter.ElementCount())
	}

	filter.AddString("a")
	filter.AddString("b")
	filter.AddString("c")

	if filter.ElementCount() != 3 {
		t.Errorf("Expected count 3, got %d", filter.ElementCount())
	}
}

// TestBloomFilter_SetCount tests the set bit count.
func TestBloomFilter_SetCount(t *testing.T) {
	filter := bloomfilter.New(1000, 7)

	// Initially no bits should be set
	if filter.SetCount() != 0 {
		t.Errorf("Expected 0 set bits initially, got %d", filter.SetCount())
	}

	// Insert elements and verify bits are set
	filter.AddString("hello")
	setCountBefore := filter.SetCount()
	if setCountBefore == 0 {
		t.Error("Expected some bits to be set after insertion")
	}

	filter.AddString("world")
	setCountAfter := filter.SetCount()
	if setCountAfter <= setCountBefore {
		t.Error("Expected more bits set after second insertion")
	}
}

// TestBloomFilter_FalsePositiveRate tests the FP rate calculation.
func TestBloomFilter_FalsePositiveRate(t *testing.T) {
	filter, err := bloomfilter.NewOptimal(10000, 0.01)
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}

	// Insert some elements
	for i := uint64(0); i < 5000; i++ {
		filter.AddString("item_" + string(rune('a'+i%26)))
	}

	// Get theoretical FP rate
	fpRate := filter.ExpectedFalsePositiveRate()

	// FP rate should be between 0 and 1
	if fpRate < 0 || fpRate > 1 {
		t.Errorf("FP rate out of range: %f", fpRate)
	}

	// For half-filled filter, FP rate should be less than target
	if fpRate > 0.01 {
		t.Logf("FP rate at 50%% fill: %.6f (target was 0.01)", fpRate)
	}
}

// TestBloomFilter_OptimalK tests optimal hash count calculation.
func TestBloomFilter_OptimalK(t *testing.T) {
	filter := bloomfilter.New(10000, 7)

	// For 10000 elements, optimal k should be computed
	optimalK := filter.OptimalK(10000)
	if optimalK == 0 {
		t.Error("Expected non-zero optimal k")
	}

	// For 0 elements, should return current k
	optimalK = filter.OptimalK(0)
	if optimalK != filter.HashCount() {
		t.Errorf("Expected k=%d for 0 elements, got %d", filter.HashCount(), optimalK)
	}
}

// TestBloomFilter_BitsPerElement tests bits per element calculation.
func TestBloomFilter_BitsPerElement(t *testing.T) {
	filter := bloomfilter.New(10000, 7)

	// Before any insertions
	bpe := filter.BitsPerElement()
	if bpe == 0 {
		t.Error("Expected non-zero bits per element ratio")
	}

	// Insert elements
	for i := uint64(0); i < 1000; i++ {
		filter.AddString("item_" + string(rune('a'+i%26)))
	}

	bpe = filter.BitsPerElement()
	expectedBPE := float64(10000) / 1000.0
	if bpe != expectedBPE {
		t.Errorf("Expected BPE %.1f, got %.1f", expectedBPE, bpe)
	}
}

// TestBloomFilter_BloomFilter_Merge_Multiple tests merging multiple filters.
func TestBloomFilter_BloomFilter_Merge_Multiple(t *testing.T) {
	filter1, _ := bloomfilter.NewOptimal(1000, 0.01)
	filter2, _ := bloomfilter.NewOptimal(1000, 0.01)
	filter3, _ := bloomfilter.NewOptimal(1000, 0.01)

	filter1.AddString("unique1")
	filter2.AddString("unique2")
	filter3.AddString("unique3")

	err := filter1.MergeMultiple([]*bloomfilter.BloomFilter{filter2, filter3})
	if err != nil {
		t.Fatalf("MergeMultiple failed: %v", err)
	}

	if !filter1.ContainsString("unique1") ||
		!filter1.ContainsString("unique2") ||
		!filter1.ContainsString("unique3") {
		t.Error("Expected all elements to be found after merge")
	}
}

// TestBloomFilter_CountingBloom_BasicOperations tests counting Bloom filter basics.
func TestBloomFilter_CountingBloom_BasicOperations(t *testing.T) {
	cbf, err := bloomfilter.NewCountingBloomSimple(1000, 0.01)
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}

	// Insert
	cbf.AddString("hello")
	cbf.AddString("world")

	// Verify
	if !cbf.ContainsString("hello") {
		t.Error("Expected 'hello' to be found")
	}
	if !cbf.ContainsString("world") {
		t.Error("Expected 'world' to be found")
	}

	// Remove and verify
	cbf.Remove("hello")
	if cbf.ContainsString("hello") {
		t.Error("Expected 'hello' to NOT be found after removal")
	}
}

// TestBloomFilter_CountingBloom_DuplicateHandling tests duplicate element handling.
func TestBloomFilter_CountingBloom_DuplicateHandling(t *testing.T) {
	cbf, err := bloomfilter.NewCountingBloomSimple(1000, 0.01)
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}

	// Insert "a" multiple times
	cbf.AddString("a")
	cbf.AddString("a")
	cbf.AddString("a")

	// Remove once - should still be found
	cbf.Remove("a")
	if !cbf.ContainsString("a") {
		t.Error("Expected 'a' to still be found after partial removal")
	}

	// Remove remaining times
	cbf.Remove("a")
	cbf.Remove("a")
	if cbf.ContainsString("a") {
		t.Error("Expected 'a' to NOT be found after full removal")
	}
}

// TestBloomFilter_CountingBloom_RemoveNeverInserted tests removing never-inserted elements.
func TestBloomFilter_CountingBloom_RemoveNeverInserted(t *testing.T) {
	cbf, err := bloomfilter.NewCountingBloomSimple(1000, 0.01)
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}

	cbf.AddString("existing")

	// Remove a never-inserted element
	cbf.Remove("never_inserted")

	// Existing element should still be found
	if !cbf.ContainsString("existing") {
		t.Error("Expected 'existing' to still be found after removing different element")
	}
}

// TestBloomFilter_CountingBloom_Reset tests counting Bloom filter reset.
func TestBloomFilter_CountingBloom_Reset(t *testing.T) {
	cbf, err := bloomfilter.NewCountingBloomSimple(1000, 0.01)
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}

	cbf.AddString("hello")
	cbf.Reset()

	if cbf.ContainsString("hello") {
		t.Error("Expected 'hello' to NOT be found after reset")
	}
	if cbf.ElementCount() != 0 {
		t.Errorf("Expected element count 0 after reset, got %d", cbf.ElementCount())
	}
}

// TestBloomFilter_CountingBloom_Config tests counting Bloom filter configuration.
func TestBloomFilter_CountingBloom_Config(t *testing.T) {
	cbf, err := bloomfilter.NewCountingBloom(bloomfilter.CountingBloomConfig{
		ExpectedElements:  1000,
		FalsePositiveRate: 0.01,
		CountBits:         4,
	})
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}

	if cbf.CountBits() != 4 {
		t.Errorf("Expected 4 count bits, got %d", cbf.CountBits())
	}
	if cbf.Size() == 0 {
		t.Error("Expected non-zero size")
	}
}

// TestBloomFilter_CountingBloom_ConfigErrors tests configuration error handling.
func TestBloomFilter_CountingBloom_ConfigErrors(t *testing.T) {
	_, err := bloomfilter.NewCountingBloom(bloomfilter.CountingBloomConfig{
		ExpectedElements:  0,
		FalsePositiveRate: 0.01,
	})
	if err == nil {
		t.Error("Expected error for zero expected elements")
	}

	_, err = bloomfilter.NewCountingBloom(bloomfilter.CountingBloomConfig{
		ExpectedElements:  1000,
		FalsePositiveRate: 1.5,
	})
	if err == nil {
		t.Error("Expected error for FP rate > 1")
	}

	_, err = bloomfilter.NewCountingBloom(bloomfilter.CountingBloomConfig{
		ExpectedElements:  1000,
		FalsePositiveRate: 0.01,
		CountBits:         3, // invalid value
	})
	if err == nil {
		t.Error("Expected error for invalid count bits")
	}
}

// TestBloomFilter_CalculateOptimalParams tests the utility function.
func TestBloomFilter_CalculateOptimalParams(t *testing.T) {
	m, k := bloomfilter.CalculateOptimalParams(10000, 0.01)

	if m == 0 || k == 0 {
		t.Error("Expected non-zero m and k")
	}

	// Verify the formula: k should be approximately (m/n) * ln(2)
	expectedK := uint64(math.Round(float64(m) / 10000 * math.Log(2)))
	if k != expectedK {
		t.Errorf("Expected k=%d, got %d", expectedK, k)
	}
}

// TestBloomFilter_CalculateOptimalParamsErrors tests error handling.
func TestBloomFilter_CalculateOptimalParamsErrors(t *testing.T) {
	m, k := bloomfilter.CalculateOptimalParams(0, 0.01)
	if m != 0 || k != 0 {
		t.Error("Expected zero m and k for zero elements")
	}

	m, k = bloomfilter.CalculateOptimalParams(1000, 0)
	if m != 0 || k != 0 {
		t.Error("Expected zero m and k for zero FP rate")
	}

	m, k = bloomfilter.CalculateOptimalParams(1000, 1.5)
	if m != 0 || k != 0 {
		t.Error("Expected zero m and k for FP rate > 1")
	}
}

// TestBloomFilter_CalculateFalsePositiveRate tests FP rate calculation.
func TestBloomFilter_CalculateFalsePositiveRate(t *testing.T) {
	// For m=1000, k=7, n=100
	fp := bloomfilter.CalculateFalsePositiveRate(1000, 7, 100)
	if fp < 0 || fp > 1 {
		t.Errorf("FP rate out of range: %f", fp)
	}

	// For zero elements, FP rate should be 0
	fp = bloomfilter.CalculateFalsePositiveRate(1000, 7, 0)
	if fp != 0 {
		t.Errorf("Expected FP rate 0 for zero elements, got %f", fp)
	}

	// For zero m, FP rate should be 0
	fp = bloomfilter.CalculateFalsePositiveRate(0, 7, 100)
	if fp != 0 {
		t.Errorf("Expected FP rate 0 for zero m, got %f", fp)
	}
}

// TestBloomFilter_BitsPerElementRatio tests the bits per element ratio.
func TestBloomFilter_BitsPerElementRatio(t *testing.T) {
	// For p=0.01, bits per element should be approximately 9.6
	bpe := bloomfilter.BitsPerElementRatio(0.01)
	expectedBPE := -math.Log(0.01) / (math.Log(2) * math.Log(2))
	if bpe < expectedBPE-0.1 || bpe > expectedBPE+0.1 {
		t.Errorf("Expected BPE ~%.1f for p=0.01, got %.1f", expectedBPE, bpe)
	}

	// For invalid FP rates, should return 0
	bpe = bloomfilter.BitsPerElementRatio(0)
	if bpe != 0 {
		t.Errorf("Expected BPE 0 for invalid FP rate, got %f", bpe)
	}

	bpe = bloomfilter.BitsPerElementRatio(1.5)
	if bpe != 0 {
		t.Errorf("Expected BPE 0 for FP rate > 1, got %f", bpe)
	}
}

// TestBloomFilter_Concurrency tests concurrent access safety.
func TestBloomFilter_Concurrency(t *testing.T) {
	filter := bloomfilter.New(10000, 7)
	done := make(chan bool, 10)

	// Concurrent writes
	for i := 0; i < 10; i++ {
		go func(start int) {
			for j := 0; j < 100; j++ {
				filter.AddString("concurrent_" + string(rune(start+'a')) + string(rune(j)))
			}
			done <- true
		}(i)
	}

	// Wait for all goroutines
	for i := 0; i < 10; i++ {
		<-done
	}

	// Verify element count
	expectedCount := uint64(1000)
	actualCount := filter.ElementCount()
	if actualCount != expectedCount {
		t.Errorf("Expected element count %d, got %d", expectedCount, actualCount)
	}
}

// TestBloomFilter_ConcurrencyCounting tests concurrent access for counting Bloom filter.
func TestBloomFilter_ConcurrencyCounting(t *testing.T) {
	cbf, _ := bloomfilter.NewCountingBloomSimple(1000, 0.01)
	done := make(chan bool, 5)

	for i := 0; i < 5; i++ {
		go func(id int) {
			for j := 0; j < 50; j++ {
				cbf.AddString("concurrent_" + string(rune(id+'a')) + string(rune(j)))
			}
			done <- true
		}(i)
	}

	for i := 0; i < 5; i++ {
		<-done
	}

	if cbf.ElementCount() != 250 {
		t.Errorf("Expected element count 250, got %d", cbf.ElementCount())
	}
}

// TestBloomFilter_Info tests the Info string output.
func TestBloomFilter_Info(t *testing.T) {
	filter := bloomfilter.New(1000, 7)
	filter.AddString("hello")
	filter.AddString("world")

	info := filter.Info()
	if len(info) == 0 {
		t.Error("Expected non-empty info string")
	}
}

// TestBloomFilter_CountingBloom_Info tests counting Bloom filter Info string.
func TestBloomFilter_CountingBloom_Info(t *testing.T) {
	cbf, _ := bloomfilter.NewCountingBloomSimple(1000, 0.01)
	cbf.AddString("hello")

	info := cbf.Info()
	if len(info) == 0 {
		t.Error("Expected non-empty info string")
	}
}

// TestBloomFilter_LargeScale tests the filter with a large number of elements.
func TestBloomFilter_LargeScale(t *testing.T) {
	filter, err := bloomfilter.NewOptimal(100000, 0.01)
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}

	// Insert 100000 elements
	for i := uint64(0); i < 100000; i++ {
		filter.AddString("item_" + string(rune('a'+i%26)))
	}

	// Verify all elements are found
	for i := uint64(0); i < 100000; i++ {
		key := "item_" + string(rune('a'+i%26))
		if !filter.ContainsString(key) {
			t.Errorf("Expected '%s' to be found", key)
			break
		}
	}
}

// TestBloomFilter_SizeAndHashCount tests Size() and HashCount() methods.
func TestBloomFilter_SizeAndHashCount(t *testing.T) {
	filter := bloomfilter.New(2000, 10)

	if filter.Size() != 2000 {
		t.Errorf("Expected size 2000, got %d", filter.Size())
	}
	if filter.HashCount() != 10 {
		t.Errorf("Expected hash count 10, got %d", filter.HashCount())
	}
}

// TestBloomFilter_CountingBloom_SizeAndHashCount tests counting Bloom filter Size() and HashCount().
func TestBloomFilter_CountingBloom_SizeAndHashCount(t *testing.T) {
	cbf, _ := bloomfilter.NewCountingBloomSimple(1000, 0.01)

	if cbf.Size() == 0 {
		t.Error("Expected non-zero size")
	}
	if cbf.HashCount() == 0 {
		t.Error("Expected non-zero hash count")
	}
}

// TestBloomFilter_AddString tests the AddString convenience method.
func TestBloomFilter_AddString(t *testing.T) {
	filter := bloomfilter.New(1000, 7)
	filter.AddString("test")

	if !filter.ContainsString("test") {
		t.Error("Expected 'test' to be found after AddString")
	}
}

// TestBloomFilter_CountingBloom_AddString tests counting Bloom filter AddString.
func TestBloomFilter_CountingBloom_AddString(t *testing.T) {
	cbf, _ := bloomfilter.NewCountingBloomSimple(1000, 0.01)
	cbf.AddString("test")

	if !cbf.ContainsString("test") {
		t.Error("Expected 'test' to be found after AddString")
	}
}

// TestBloomFilter_EmptyFilter tests behavior with empty filter.
func TestBloomFilter_EmptyFilter(t *testing.T) {
	filter := bloomfilter.New(1000, 7)

	// Empty filter should have 0 set bits
	if filter.SetCount() != 0 {
		t.Errorf("Expected 0 set bits, got %d", filter.SetCount())
	}

	// Empty filter should have 0 element count
	if filter.ElementCount() != 0 {
		t.Errorf("Expected 0 element count, got %d", filter.ElementCount())
	}

	// Empty filter should have 0 FP rate
	fp := filter.ExpectedFalsePositiveRate()
	if fp != 0 {
		t.Errorf("Expected 0 FP rate for empty filter, got %f", fp)
	}
}

// TestBloomFilter_CountingBloom_EmptyFilter tests empty counting Bloom filter.
func TestBloomFilter_CountingBloom_EmptyFilter(t *testing.T) {
	cbf, _ := bloomfilter.NewCountingBloomSimple(1000, 0.01)

	if cbf.ElementCount() != 0 {
		t.Errorf("Expected 0 element count, got %d", cbf.ElementCount())
	}
}

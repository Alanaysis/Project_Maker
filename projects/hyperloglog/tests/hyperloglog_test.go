package hyperloglog_test

import (
	"math"
	"testing"

	"hyperloglog/src"
)

// TestNewDefaultPrecision verifies that New() creates a sketch with default precision.
func TestNewDefaultPrecision(t *testing.T) {
	hll := hyperloglog.New()
	if hll.Precision() != hyperloglog.DefaultPrecision {
		t.Errorf("expected default precision %d, got %d", hyperloglog.DefaultPrecision, hll.Precision())
	}
	if hll.BucketCount() != (1<<hyperloglog.DefaultPrecision) {
		t.Errorf("expected %d buckets, got %d", 1<<hyperloglog.DefaultPrecision, hll.BucketCount())
	}
}

// TestNewWithPrecision verifies creation with various precision values.
func TestNewWithPrecision(t *testing.T) {
	testCases := []struct {
		p       hyperloglog.Precision
		wantM   uint32
		wantMem int
	}{
		{hyperloglog.MinPrecision, 1 << 4, (1 << 4) + 32},
		{hyperloglog.DefaultPrecision, 1 << 10, (1 << 10) + 32},
		{hyperloglog.MaxPrecision, 1 << 16, (1 << 16) + 32},
	}

	for _, tc := range testCases {
		t.Run("p="+string(tc.p), func(t *testing.T) {
			hll := hyperloglog.NewWithPrecision(tc.p)
			if hll.BucketCount() != tc.wantM {
				t.Errorf("bucket count: want %d, got %d", tc.wantM, hll.BucketCount())
			}
			if hll.MemoryBytes() != tc.wantMem {
				t.Errorf("memory: want %d, got %d", tc.wantMem, hll.MemoryBytes())
			}
		})
	}
}

// TestNewPrecisionClamping verifies that out-of-range precision is clamped.
func TestNewPrecisionClamping(t *testing.T) {
	// Below minimum
	hll := hyperloglog.NewWithPrecision(0)
	if hll.Precision() != hyperloglog.DefaultPrecision {
		t.Errorf("expected clamped to default %d, got %d", hyperloglog.DefaultPrecision, hll.Precision())
	}

	// Above maximum
	hll = hyperloglog.NewWithPrecision(20)
	if hll.Precision() != hyperloglog.DefaultPrecision {
		t.Errorf("expected clamped to default %d, got %d", hyperloglog.DefaultPrecision, hll.Precision())
	}
}

// TestAddEmptySketch verifies empty sketch returns zero estimate.
func TestAddEmptySketch(t *testing.T) {
	hll := hyperloglog.New()
	estimate := hll.Estimate()
	if estimate != 0 {
		t.Errorf("expected estimate 0 for empty sketch, got %d", estimate)
	}
}

// TestAddSingleElement verifies adding one element gives estimate of 1.
func TestAddSingleElement(t *testing.T) {
	hll := hyperloglog.New()
	hll.Add([]byte("hello"))
	estimate := hll.Estimate()
	if estimate != 1 {
		t.Errorf("expected estimate 1, got %d", estimate)
	}
}

// TestAddString verifies AddString works correctly.
func TestAddString(t *testing.T) {
	hll := hyperloglog.New()
	hll.AddString("world")
	estimate := hll.Estimate()
	if estimate != 1 {
		t.Errorf("expected estimate 1, got %d", estimate)
	}
}

// TestAddDuplicateElements verifies duplicates are not counted twice.
func TestAddDuplicateElements(t *testing.T) {
	hll := hyperloglog.New()
	for i := 0; i < 100; i++ {
		hll.Add([]byte("same-element"))
	}
	estimate := hll.Estimate()
	if estimate != 1 {
		t.Errorf("expected estimate 1 for duplicates, got %d", estimate)
	}
}

// TestAddUniqueElements verifies unique elements are counted.
func TestAddUniqueElements(t *testing.T) {
	hll := hyperloglog.New()
	n := 1000
	for i := 0; i < n; i++ {
		hll.Add([]byte("unique-" + string(rune('a' + i%26))))
	}
	estimate := hll.Estimate()
	// Allow 20% error for small cardinalities with p=10
	error := math.Abs(float64(estimate)-float64(n)) / float64(n)
	if error > 0.2 {
		t.Errorf("large error for %d unique elements: got %d (error %.2f)", n, estimate, error)
	}
}

// TestDeterministicHash verifies the hash function is deterministic.
func TestDeterministicHash(t *testing.T) {
	hll := hyperloglog.New()
	data := []byte("test-data")
	hash1 := hll.Hash(data)
	hash2 := hll.Hash(data)
	if hash1 != hash2 {
		t.Errorf("hash not deterministic: %x vs %x", hash1, hash2)
	}
}

// TestDeterministicEstimate verifies repeated estimation gives same result.
func TestDeterministicEstimate(t *testing.T) {
	hll := hyperloglog.New()
	for i := 0; i < 100; i++ {
		hll.Add([]byte("element-" + string(rune('a' + i%26))))
	}
	est1 := hll.Estimate()
	est2 := hll.Estimate()
	if est1 != est2 {
		t.Errorf("estimate not deterministic: %d vs %d", est1, est2)
	}
}

// TestReset verifies Reset clears all registers.
func TestReset(t *testing.T) {
	hll := hyperloglog.New()
	for i := 0; i < 100; i++ {
		hll.Add([]byte("element-" + string(rune('a' + i%26))))
	}
	estimateBefore := hll.Estimate()
	if estimateBefore == 0 {
		t.Fatal("expected non-zero estimate before reset")
	}

	hll.Reset()
	estimateAfter := hll.Estimate()
	if estimateAfter != 0 {
		t.Errorf("expected estimate 0 after reset, got %d", estimateAfter)
	}
}

// TestClone verifies Clone creates an independent copy.
func TestClone(t *testing.T) {
	hll := hyperloglog.New()
	for i := 0; i < 100; i++ {
		hll.Add([]byte("element-" + string(rune('a' + i%26))))
	}
	estimateBefore := hll.Estimate()

	clone := hll.Clone()
	estimateClone := clone.Estimate()

	if estimateBefore != estimateClone {
		t.Errorf("clone estimate mismatch: %d vs %d", estimateBefore, estimateClone)
	}

	// Modify original and verify clone is unaffected
	hll.Reset()
	if clone.Estimate() == 0 {
		t.Error("clone was affected by original reset")
	}
}

// TestMerge verifies merging two sketches works correctly.
func TestMerge(t *testing.T) {
	hll1 := hyperloglog.New()
	hll2 := hyperloglog.New()

	// Add elements to hll1
	for i := 0; i < 500; i++ {
		hll1.Add([]byte("element-" + string(rune('a' + i%26))))
	}

	// Add different elements to hll2
	for i := 0; i < 500; i++ {
		hll2.Add([]byte("other-" + string(rune('a' + i%26))))
	}

	est1 := hll1.Estimate()
	est2 := hll2.Estimate()

	err := hll1.Merge(hll2)
	if err != nil {
		t.Fatalf("merge failed: %v", err)
	}

	mergedEstimate := hll1.Estimate()
	// Merged estimate should be roughly the sum (allowing for overlap)
	if mergedEstimate < est1 || mergedEstimate < est2 {
		t.Errorf("merged estimate too low: %d (was %d + %d)", mergedEstimate, est1, est2)
	}
}

// TestMergePrecisionMismatch verifies merge fails with different precisions.
func TestMergePrecisionMismatch(t *testing.T) {
	hll1 := hyperloglog.NewWithPrecision(hyperloglog.Precision(4))
	hll2 := hyperloglog.NewWithPrecision(hyperloglog.Precision(10))

	err := hll1.Merge(hll2)
	if err == nil {
		t.Error("expected precision mismatch error, got nil")
	}
}

// TestPrecisionFromError verifies precision calculation for target error.
func TestPrecisionFromError(t *testing.T) {
	testCases := []struct {
		targetSE   float64
		wantMinP   hyperloglog.Precision
	}{
		{0.01, 14},  // 1% error
		{0.005, 16}, // 0.5% error
		{0.1, 6},    // 10% error
	}

	for _, tc := range testCases {
		p := hyperloglog.PrecisionFromError(tc.targetSE)
		if p < tc.wantMinP {
			t.Errorf("PrecisionFromError(%.3f): got p=%d, want at least p=%d", tc.targetSE, p, tc.wantMinP)
		}
	}
}

// TestStandardError verifies standard error formula.
func TestStandardError(t *testing.T) {
	testCases := []struct {
		p          hyperloglog.Precision
		wantApprox float64
	}{
		{hyperloglog.Precision(4), 0.128},
		{hyperloglog.Precision(8), 0.045},
		{hyperloglog.Precision(10), 0.0255},
		{hyperloglog.Precision(14), 0.0064},
		{hyperloglog.Precision(16), 0.0028},
	}

	for _, tc := range testCases {
		hll := hyperloglog.NewWithPrecision(tc.p)
		se := hll.StandardError()
		// Allow 20% tolerance for approximation
		if math.Abs(se-tc.wantApprox)/tc.wantApprox > 0.2 {
			t.Errorf("p=%d: standard error %.6f, expected ~%.6f", tc.p, se, tc.wantApprox)
		}
	}
}

// TestConfidenceInterval verifies confidence interval computation.
func TestConfidenceInterval(t *testing.T) {
	hll := hyperloglog.New()
	hll.Add([]byte("test"))
	estimate := hll.Estimate()

	// 95% confidence interval should be wider than 90%
	_, upper95 := hll.ConfidenceInterval(estimate, 0.95)
	_, upper90 := hll.ConfidenceInterval(estimate, 0.90)

	if upper95 <= upper90 {
		t.Errorf("95%% CI upper (%.2f) should be >= 90%% CI upper (%.2f)", upper95, upper90)
	}

	// Lower bound should be <= estimate
	lower95, _ := hll.ConfidenceInterval(estimate, 0.95)
	if lower95 > estimate {
		t.Errorf("lower bound %.2f > estimate %.2f", lower95, estimate)
	}
}

// TestExpectedCardinalityForMemory verifies memory-cardinality relationship.
func TestExpectedCardinalityForMemory(t *testing.T) {
	// With 1KB memory, should get p=10
	p, maxCard := hyperloglog.ExpectedCardinalityForMemory(1024)
	if p != hyperloglog.DefaultPrecision {
		t.Errorf("expected p=%d for 1KB, got p=%d", hyperloglog.DefaultPrecision, p)
	}
	if maxCard <= 0 {
		t.Error("expected positive max cardinality")
	}

	// With 64KB memory, should get p=16
	p, maxCard = hyperloglog.ExpectedCardinalityForMemory(65536)
	if p != hyperloglog.MaxPrecision {
		t.Errorf("expected p=%d for 64KB, got p=%d", hyperloglog.MaxPrecision, p)
	}
	if maxCard <= 0 {
		t.Error("expected positive max cardinality")
	}
}

// TestLargeCardinalityAccuracy tests accuracy with large number of elements.
func TestLargeCardinalityAccuracy(t *testing.T) {
	if testing.Short() {
		t.Skip("skipping in short mode")
	}

	testCases := []struct {
		p    hyperloglog.Precision
		n    int
		errF float64 // allowed relative error
	}{
		{hyperloglog.Precision(10), 10000, 0.1},
		{hyperloglog.Precision(14), 100000, 0.05},
	}

	for _, tc := range testCases {
		t.Run("p="+string(tc.p)+"_n="+string(tc.n), func(t *testing.T) {
			hll := hyperloglog.NewWithPrecision(tc.p)
			for i := 0; i < tc.n; i++ {
				hll.Add([]byte("unique-element-" + string(rune('a' + i%26)) + string(rune('0'+i/26%10))))
			}
			estimate := hll.Estimate()
			error := math.Abs(float64(estimate)-float64(tc.n)) / float64(tc.n)
			if error > tc.errF {
				t.Errorf("error %.4f exceeds allowed %.4f for n=%d", error, tc.errF, tc.n)
			}
		})
	}
}

// TestRegisterValues verifies register values are accessible.
func TestRegisterValues(t *testing.T) {
	hll := hyperloglog.New()
	hll.Add([]byte("test"))

	vals := hll.RegisterValues()
	if len(vals) != int(hll.BucketCount()) {
		t.Errorf("expected %d register values, got %d", hll.BucketCount(), len(vals))
	}

	// Modifying the returned slice should not affect the sketch
	vals[0] = 255
	if hll.RegisterValues()[0] == 255 {
		t.Error("RegisterValues should return a copy")
	}
}

// TestZeroBucketCount verifies zero bucket counting.
func TestZeroBucketCount(t *testing.T) {
	hll := hyperloglog.New()
	// Empty sketch should have all buckets at zero
	if hll.ZeroBucketCount() != int(hll.BucketCount()) {
		t.Errorf("expected all buckets zero, got %d zero", hll.ZeroBucketCount())
	}

	hll.Add([]byte("test"))
	zeroCount := hll.ZeroBucketCount()
	if zeroCount >= int(hll.BucketCount()) {
		t.Error("expected fewer zero buckets after adding element")
	}
}

// TestMaxRegister verifies max register value.
func TestMaxRegister(t *testing.T) {
	hll := hyperloglog.New()
	if hll.MaxRegister() != 0 {
		t.Errorf("expected max register 0 for empty sketch, got %d", hll.MaxRegister())
	}

	hll.Add([]byte("test"))
	if hll.MaxRegister() == 0 {
		t.Error("expected non-zero max register after adding element")
	}
}

// Package bloomfilter_test contains example programs demonstrating Bloom filter usage.
package main

import (
	"fmt"
	"math/rand"
	"time"

	"bloom-filter/src"
)

func main() {
	fmt.Println("=== False Positive Rate Demonstration ===")
	fmt.Println()

	rng := rand.New(rand.NewSource(12345))

	// Scenario 1: Different FP rates with same number of elements
	fmt.Println("--- Scenario 1: Same elements, different FP rates ---")
	nElements := uint64(10000)

	for _, fpRate := range []float64{0.1, 0.05, 0.01, 0.001} {
		filter, err := bloomfilter.NewOptimal(nElements, fpRate)
		if err != nil {
			panic(err)
		}

		// Insert elements
		for i := uint64(0); i < nElements; i++ {
			filter.AddString(fmt.Sprintf("item_%d", i))
		}

		// Test with non-inserted elements
		falsePos := 0
		testCount := 1000
		for i := 0; i < testCount; i++ {
			testKey := fmt.Sprintf("nonexistent_%d", rng.Intn(100000000))
			if filter.ContainsString(testKey) {
				falsePos++
			}
		}

		actualFP := float64(falsePos) / float64(testCount)
		m, k := bloomfilter.CalculateOptimalParams(nElements, fpRate)
		fmt.Printf("  Target FP: %.4f | Actual FP: %.4f | m=%d | k=%d | Mem=%.2f KB\n",
			fpRate, actualFP, m, k, float64(m)/8/1024)
	}

	fmt.Println()

	// Scenario 2: Same FP rate, different fill levels
	fmt.Println("--- Scenario 2: Same FP rate, different fill levels ---")
	targetFP := 0.01
	maxElements := uint64(10000)
	filter, _ := bloomfilter.NewOptimal(maxElements, targetFP)

	fillLevels := []uint64{1000, 2000, 5000, 8000, 10000}
	for _, fill := range fillLevels {
		filter.Reset()
		for i := uint64(0); i < fill; i++ {
			filter.AddString(fmt.Sprintf("item_%d", i))
		}

		// Measure actual FP rate
		falsePos := 0
		testCount := 5000
		for i := 0; i < testCount; i++ {
			testKey := fmt.Sprintf("nonexistent_%d", rng.Intn(100000000))
			if filter.ContainsString(testKey) {
				falsePos++
			}
		}

		actualFP := float64(falsePos) / float64(testCount)
		theoreticalFP := filter.ExpectedFalsePositiveRate()
		fmt.Printf("  Fill: %5.1f%% | Actual FP: %.4f | Theoretical FP: %.4f\n",
			float64(fill)/float64(maxElements)*100, actualFP, theoreticalFP)
	}

	fmt.Println()

	// Scenario 3: FP rate over time (as elements accumulate)
	fmt.Println("--- Scenario 3: FP rate evolution as elements accumulate ---")
	filter2, _ := bloomfilter.NewOptimal(100000, 0.01)
	steps := []uint64{1000, 5000, 10000, 25000, 50000, 75000, 100000}

	for _, step := range steps {
		// Insert up to this step
		for i := uint64(0); i < step; i++ {
			filter2.AddString(fmt.Sprintf("item_%d", i))
		}

		// Measure actual FP rate
		falsePos := 0
		testCount := 10000
		for i := 0; i < testCount; i++ {
			testKey := fmt.Sprintf("nonexistent_%d", rng.Intn(100000000))
			if filter2.ContainsString(testKey) {
				falsePos++
			}
		}

		actualFP := float64(falsePos) / float64(testCount)
		fillPct := float64(step) / float64(100000) * 100
		fmt.Printf("  Elements: %6d (%5.1f%%) | Actual FP: %.5f\n",
			step, fillPct, actualFP)
	}

	fmt.Println()
	fmt.Println("Key insight: False positive rate increases as the filter fills up.")
	fmt.Println("The theoretical formula provides an accurate prediction of actual FP rate.")
}

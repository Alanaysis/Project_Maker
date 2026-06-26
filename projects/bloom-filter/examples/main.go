// Package bloomfilter_test contains example programs demonstrating Bloom filter usage.
package bloomfilter_test

import (
	"fmt"
	"math/rand"
	"time"

	"bloom-filter/src"
)

func main() {
	fmt.Println("=== Bloom Filter Examples ===")
	fmt.Println()

	basicUsage()
	fmt.Println()
	falsePositiveDemo()
	fmt.Println()
	optimalSizeCalculation()
	fmt.Println()
	countingBloomDemo()
}

// basicUsage demonstrates the basic Bloom filter operations.
func basicUsage() {
	fmt.Println("--- Basic Bloom Filter Usage ---")

	// Create a Bloom filter optimized for 10,000 elements with 1% false positive rate
	filter, err := bloomfilter.NewOptimal(10000, 0.01)
	if err != nil {
		panic(err)
	}

	fmt.Printf("Created filter: %s\n", filter.Info())

	// Insert elements
	words := []string{"hello", "world", "golang", "bloom", "filter", "hash", "bits", "array"}
	for _, word := range words {
		filter.AddString(word)
	}

	// Query elements
	fmt.Println("\nQuerying inserted elements:")
	for _, word := range words {
		if filter.ContainsString(word) {
			fmt.Printf("  '%s': FOUND (correct)\n", word)
		} else {
			fmt.Printf("  '%s': NOT FOUND (ERROR!)\n", word)
		}
	}

	// Query non-inserted elements
	fmt.Println("\nQuerying non-inserted elements:")
	nonWords := []string{"rust", "python", "javascript", "c++"}
	for _, word := range nonWords {
		if filter.ContainsString(word) {
			fmt.Printf("  '%s': FOUND (false positive!)\n", word)
		} else {
			fmt.Printf("  '%s': NOT FOUND (correct)\n", word)
		}
	}

	fmt.Printf("\nFilter state: %s\n", filter.Info())
}

// falsePositiveDemo demonstrates the false positive rate with different fill levels.
func falsePositiveDemo() {
	fmt.Println("--- False Positive Rate Demonstration ---")

	// Create a filter for 100,000 elements with 0.1% target FP rate
	filter, err := bloomfilter.NewOptimal(100000, 0.001)
	if err != nil {
		panic(err)
	}

	// Generate test data
	rng := rand.New(rand.NewSource(42))
	allElements := make([]string, 100000)
	for i := 0; i < 100000; i++ {
		allElements[i] = fmt.Sprintf("element_%d", rng.Intn(1000000000))
	}

	// Test at different fill levels
	fillLevels := []uint64{10000, 25000, 50000, 75000, 100000}
	testCount := 10000
	falsePositives := make([]int, len(fillLevels))

	// Create a separate set of test elements (not in the filter)
	testElements := make([]string, testCount)
	for i := 0; i < testCount; i++ {
		testElements[i] = fmt.Sprintf("test_%d", rng.Intn(1000000000))
	}

	for fi, fill := range fillLevels {
		// Insert elements up to the fill level
		filter.Reset()
		for i := uint64(0); i < fill; i++ {
			filter.AddString(allElements[i])
		}

		// Count false positives
		for _, elem := range testElements {
			if filter.ContainsString(elem) {
				falsePositives[fi]++
			}
		}

		actualFP := float64(falsePositives[fi]) / float64(testCount)
		theoreticalFP := filter.ExpectedFalsePositiveRate()
		fmt.Printf("  Fill %5.1f%%: actual FP rate = %.4f, theoretical = %.4f\n",
			float64(fill)/float64(100000)*100, actualFP, theoreticalFP)
	}

	fmt.Printf("\nFilter state: %s\n", filter.Info())
}

// optimalSizeCalculation demonstrates how to calculate optimal parameters.
func optimalSizeCalculation() {
	fmt.Println("--- Optimal Filter Size Calculation ---")

	// Show how optimal parameters change with different requirements
	reqs := []struct {
		n uint64
		p float64
	}{
		{1000, 0.01},
		{10000, 0.01},
		{100000, 0.01},
		{1000000, 0.01},
		{10000000, 0.01},
		{100000, 0.001},
		{100000, 0.0001},
	}

	fmt.Printf("%-15s %-12s %-15s %-10s %-12s\n",
		"Elements", "FP Rate", "Bit Array Size", "Hash (k)", "Bits/Elem")
	fmt.Println(string(make([]byte, 70)))

	for _, req := range reqs {
		m, k := bloomfilter.CalculateOptimalParams(req.n, req.p)
		bpe := bloomfilter.BitsPerElementRatio(req.p)
		fmt.Printf("%-15d %-12.4f %-15d %-10d %-12.1f\n",
			req.n, req.p, m, k, bpe)
	}

	// Show bits per element for different FP rates
	fmt.Println("\nBits per element for different FP rates (n = 1,000,000):")
	fmt.Printf("%-15s %-12s\n", "FP Rate", "Bits/Element")
	fmt.Println(string(make([]byte, 30)))
	for _, p := range []float64{0.1, 0.05, 0.01, 0.005, 0.001, 0.0001} {
		bpe := bloomfilter.BitsPerElementRatio(p)
		fmt.Printf("%-15.4f %-12.1f\n", p, bpe)
	}
}

// countingBloomDemo demonstrates the counting Bloom filter with deletion.
func countingBloomDemo() {
	fmt.Println("--- Counting Bloom Filter Demo ---")

	// Create a counting Bloom filter
	cbf, err := bloomfilter.NewCountingBloomSimple(10000, 0.01)
	if err != nil {
		panic(err)
	}

	fmt.Printf("Created: %s\n", cbf.Info())

	// Insert elements
	words := []string{"apple", "banana", "cherry", "date", "elderberry"}
	for _, word := range words {
		cbf.AddString(word)
	}

	fmt.Println("\nAfter insertion:")
	for _, word := range words {
		if cbf.ContainsString(word) {
			fmt.Printf("  '%s': FOUND\n", word)
		}
	}

	// Remove an element
	fmt.Println("\nRemoving 'banana'...")
	cbf.Remove("banana")

	fmt.Println("\nAfter removal:")
	for _, word := range words {
		found := cbf.ContainsString(word)
		expected := word != "banana"
		status := "OK"
		if found != expected {
			status = "ERROR"
		}
		fmt.Printf("  '%s': %v (expected: %v) [%s]\n", word, found, expected, status)
	}

	// Try removing a non-inserted element (should not affect others)
	fmt.Println("\nRemoving 'fig' (never inserted)...")
	cbf.Remove("fig")

	fmt.Println("\nAfter removing 'fig':")
	for _, word := range words {
		found := cbf.ContainsString(word)
		expected := word != "banana"
		status := "OK"
		if found != expected {
			status = "ERROR"
		}
		fmt.Printf("  '%s': %v (expected: %v) [%s]\n", word, found, expected, status)
	}

	fmt.Printf("\nFilter state: %s\n", cbf.Info())
}

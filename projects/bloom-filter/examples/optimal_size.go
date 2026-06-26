// Package bloomfilter_test contains example programs demonstrating Bloom filter usage.
package main

import (
	"fmt"
	"math"
)

func main() {
	fmt.Println("=== Optimal Bloom Filter Size Calculator ===")
	fmt.Println()

	// Demonstrate the optimal size calculation for various scenarios
	scenarios := []struct {
		name string
		n    uint64
		p    float64
	}{
		{"Small cache", 1000, 0.01},
		{"URL dedup (small)", 10000, 0.001},
		{"URL dedup (large)", 1000000, 0.01},
		{"Log filtering", 10000000, 0.001},
		{"Email blacklist", 100000, 0.0001},
	}

	fmt.Printf("%-25s %-12s %-15s %-10s %-15s %-15s\n",
		"Scenario", "FP Rate", "Bit Array (bits)", "Hash k", "Memory (bytes)", "Memory (MB)")
	fmt.Println(string(make([]byte, 100)))

	for _, s := range scenarios {
		m, k := bloomfilter.CalculateOptimalParams(s.n, s.p)
		memoryBytes := m / 8
		memoryMB := float64(memoryBytes) / (1024 * 1024)

		// Calculate actual FP rate with optimal k
		actualFP := bloomfilter.CalculateFalsePositiveRate(m, k, s.n)

		fmt.Printf("%-25s %-12.4f %-15d %-10d %-15d %-15.4f\n",
			s.name, s.p, m, k, memoryBytes, memoryMB)

		// Show bits per element
		bpe := float64(m) / float64(s.n)
		fmt.Printf("  -> %.1f bits/element, actual FP rate: %.6f\n", bpe, actualFP)
	}

	fmt.Println()

	// Show the relationship between FP rate and memory
	fmt.Println("Memory vs False Positive Rate (n = 100,000 elements):")
	fmt.Printf("%-15s %-15s %-15s %-15s\n",
		"FP Rate", "Bits/Element", "Memory (MB)", "Hash k")
	fmt.Println(string(make([]byte, 65)))

	n := uint64(100000)
	for _, p := range []float64{0.1, 0.05, 0.01, 0.005, 0.001, 0.0005, 0.0001} {
		m, k := bloomfilter.CalculateOptimalParams(n, p)
		bpe := bloomfilter.BitsPerElementRatio(p)
		memoryMB := float64(m) / 8 / (1024 * 1024)
		actualFP := bloomfilter.CalculateFalsePositiveRate(m, k, n)

		fmt.Printf("%-15.4f %-15.1f %-15.4f %-15d\n",
			p, bpe, memoryMB, k)
		fmt.Printf("  (actual FP: %.6f)\n", actualFP)
	}

	fmt.Println()

	// Show the math behind the formulas
	fmt.Println("=== Bloom Filter Math ===")
	fmt.Println()
	fmt.Println("Optimal bit array size (m):")
	fmt.Println("  m = -(n * ln(p)) / (ln(2))^2")
	fmt.Println("  where n = number of elements, p = false positive rate")
	fmt.Println()
	fmt.Println("Optimal number of hash functions (k):")
	fmt.Println("  k = (m / n) * ln(2) ≈ 0.693 * (m/n)")
	fmt.Println()
	fmt.Println("False positive rate:")
	fmt.Println("  p = (1 - e^(-kn/m))^k")
	fmt.Println()

	// Demonstrate with a concrete example
	nExample := uint64(10000)
	pTarget := 0.01
	mExample, kExample := bloomfilter.CalculateOptimalParams(nExample, pTarget)

	fmt.Printf("Example: n=%d, target p=%.4f\n", nExample, pTarget)
	fmt.Printf("  Optimal m = %d bits\n", mExample)
	fmt.Printf("  Optimal k = %d\n", kExample)
	fmt.Printf("  Memory = %.2f bytes = %.2f KB\n", float64(mExample)/8, float64(mExample)/8/1024)

	// Verify the formula
	ln2 := math.Log(2)
	manualM := -float64(nExample) * math.Log(pTarget) / (ln2 * ln2)
	manualK := (manualM / float64(nExample)) * ln2
	fmt.Printf("  Manual calc: m=%.0f, k=%.0f\n", manualM, manualK)

	// Show the actual FP rate achieved
	actualFP := bloomfilter.CalculateFalsePositiveRate(mExample, kExample, nExample)
	fmt.Printf("  Achieved FP rate: %.6f (target: %.4f)\n", actualFP, pTarget)
}

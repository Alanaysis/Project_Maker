// DistinctCounting demonstrates HyperLogLog for cardinality estimation.
//
// HyperLogLog estimates the number of distinct elements in a stream using
// very little memory (~1.3 KB for 2% error rate). It uses probabilistic
// counting based on the distribution of leading zeros in hash values.
//
// Run: go run examples/distinct_counting.go
package main

import (
	"fmt"
	"math/rand"

	"streaming-algorithm/src"
)

func main() {
	fmt.Println("=== Distinct Elements Counting with HyperLogLog Demo ===")
	fmt.Println()

	// Demo 1: Basic cardinality estimation
	fmt.Println("--- Demo 1: Basic Cardinality Estimation ---")
	hll := streaming.NewHyperLogLog(14) // ~1% error rate

	trueDistinct := 10000
	rng := rand.New(rand.NewSource(42))

	// Generate a stream with known distinct elements
	for i := 0; i < 50000; i++ {
		// Cycle through 10000 distinct values
		val := fmt.Sprintf("item-%d", rng.Intn(trueDistinct))
		hll.Add(val)
	}

	estimated := hll.Count()
	errorPct := float64(estimated-trueDistinct) / float64(trueDistinct) * 100

	fmt.Printf("True distinct count:   %d\n", trueDistinct)
	fmt.Printf("HyperLogLog estimate:  %d\n", estimated)
	fmt.Printf("Error:                 %.2f%%\n", errorPct)

	fmt.Println()

	// Demo 2: Comparing precision parameters
	fmt.Println("--- Demo 2: Precision Parameter Comparison ---")
	trials := 100000
	trueCardinality := 50000

	for _, p := range []uint8{8, 10, 12, 14, 16} {
		hll := streaming.NewHyperLogLog(p)
		for i := 0; i < trials; i++ {
			hll.Add(fmt.Sprintf("item-%d", i%trueCardinality))
		}
		est := hll.Count()
		err := float64(est-trueCardinality) / float64(trueCardinality) * 100
		fmt.Printf("p=%2d: est=%8d, error=%7.3f%%\n", p, est, err)
	}

	fmt.Println()

	// Demo 3: Small cardinality correction
	fmt.Println("--- Demo 3: Small Cardinality Estimation ---")
	smallCardinality := 100

	for _, p := range []uint8{8, 10, 12} {
		hll := streaming.NewHyperLogLog(p)
		for i := 0; i < 500; i++ {
			hll.Add(fmt.Sprintf("item-%d", i%smallCardinality))
		}
		est := hll.Count()
		err := float64(est-smallCardinality) / float64(smallCardinality) * 100
		fmt.Printf("p=%2d: est=%4d, true=%4d, error=%6.2f%%\n", p, est, smallCardinality, err)
	}

	fmt.Println()
	fmt.Println("=== Demo Complete ===")
}

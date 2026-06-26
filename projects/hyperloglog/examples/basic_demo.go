package main

import (
	"fmt"
	"math"
	"math/rand"

	hyperloglog "hyperloglog/src"
)

// This example demonstrates basic cardinality estimation with HyperLogLog.
//
// We add a known set of elements and compare the estimate to the true count.
func main() {
	fmt.Println("=== HyperLogLog Basic Cardinality Estimation ===\n")

	// Create a HyperLogLog sketch with default precision (p=10)
	hll := hll.New()

	// Define the number of unique elements to add
	trueCardinality := 10000
	fmt.Printf("Adding %d unique elements...\n", trueCardinality)

	// Add unique elements
	for i := 0; i < trueCardinality; i++ {
		hll.Add([]byte(fmt.Sprintf("element-%d", i)))
	}

	// Get the estimate
	estimate := hll.Estimate()

	// Calculate error
	error := math.Abs(float64(estimate)-float64(trueCardinality)) / float64(trueCardinality) * 100

	// Print results
	fmt.Printf("\nTrue cardinality:     %d\n", trueCardinality)
	fmt.Printf("HLL estimate:         %.0f\n", estimate)
	fmt.Printf("Absolute error:       %d\n", int(math.Abs(float64(estimate)-float64(trueCardinality))))
	fmt.Printf("Relative error:       %.2f%%\n", error)
	fmt.Printf("Standard error:       %.2f%%\n", hll.StandardError()*100)

	// Print sketch info
	fmt.Println()
	hll.PrintInfo(estimate)

	// Print confidence interval
	hll.PrintConfidenceInterval(estimate, 0.95)

	// Show register distribution
	hll.PrintRegisterDistribution()

	// Demonstrate duplicate handling
	fmt.Println("\n--- Duplicate Handling ---")
	dupHLL := hyperloglog.New()
	for i := 0; i < 1000; i++ {
		dupHLL.Add([]byte("same-element")) // Always the same element
	}
	dupEstimate := dupHLL.Estimate()
	fmt.Printf("Adding 1000 copies of same element: estimate = %.0f (should be 1)\n", dupEstimate)

	// Demonstrate with random strings
	fmt.Println("\n--- Random String Test ---")
	randHLL := hyperloglog.New()
	rng := rand.New(rand.NewSource(42))
	numRandom := 50000

	for i := 0; i < numRandom; i++ {
		s := fmt.Sprintf("random-%d", rng.Intn(1000000))
		randHLL.Add([]byte(s))
	}

	randEstimate := randHLL.Estimate()
	randError := math.Abs(float64(randEstimate)-float64(numRandom)) / float64(numRandom) * 100

	fmt.Printf("Unique random strings: ~%d\n", numRandom)
	fmt.Printf("HLL estimate:          %.0f\n", randEstimate)
	fmt.Printf("Relative error:        %.2f%%\n", randError)
}

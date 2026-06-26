package main

import (
	"fmt"
	"math"
	"math/rand"
	"time"

	hyperloglog "hyperloglog/src"
)

// This example runs stress tests with various configurations.
//
// Tests include:
// - Scaling behavior (error vs cardinality)
// - Merge correctness
// - Precision sensitivity
// - Large-scale performance
func main() {
	fmt.Println("=== HyperLogLog Stress Tests ===\n")

	testScaling()
	testMergeAccuracy()
	testPrecisionSensitivity()
	testLargeScale()
}

// testScaling verifies that error decreases with more elements.
func testScaling() {
	fmt.Println("--- Scaling Test: Error vs Cardinality ---")
	fmt.Println("Cardinality | Estimate | Error % | Std Error %")
	fmt.Println("------------|----------|---------|------------")

	cardinalities := []int{100, 500, 1000, 5000, 10000, 50000, 100000}

	for _, n := range cardinalities {
		hll := hyperloglog.New()

		// Add elements
		for i := 0; i < n; i++ {
			hll.Add([]byte(fmt.Sprintf("scaling-element-%d", i)))
		}

		estimate := hll.Estimate()
		error := math.Abs(float64(estimate)-float64(n)) / float64(n) * 100

		fmt.Printf("   %7d | %8.0f | %7.2f%% | %8.2f%%\n", n, estimate, error, hll.StandardError()*100)
	}

	fmt.Println("\nNote: For small cardinalities (< 100), error is naturally larger.")
	fmt.Println("HyperLogLog is designed for large-scale cardinality estimation.")
}

// testMergeAccuracy verifies that merging sketches produces correct results.
func testMergeAccuracy() {
	fmt.Println("\n--- Merge Accuracy Test ---")

	trueCardinality := 100000

	// Create two separate sketches
	hll1 := hyperloglog.NewWithPrecision(hyperloglog.Precision(14))
	hll2 := hyperloglog.NewWithPrecision(hyperloglog.Precision(14))

	// Add elements to each (with some overlap)
	overlap := 25000
	for i := 0; i < trueCardinality/2; i++ {
		hll1.Add([]byte(fmt.Sprintf("set1-element-%d", i)))
		hll2.Add([]byte(fmt.Sprintf("set2-element-%d", i)))
	}

	// Add unique elements to each
	for i := 0; i < trueCardinality/2; i++ {
		hll1.Add([]byte(fmt.Sprintf("unique1-%d", i)))
		hll2.Add([]byte(fmt.Sprintf("unique2-%d", i)))
	}

	est1 := hll1.Estimate()
	est2 := hll2.Estimate()

	// Merge
	err := hll1.Merge(hll2)
	if err != nil {
		fmt.Printf("Merge error: %v\n", err)
		return
	}

	mergedEstimate := hll1.Estimate()

	// Expected: ~150,000 unique elements (100,000 + 100,000 - 25,000 overlap)
	expected := trueCardinality + trueCardinality/2 - overlap

	fmt.Printf("Sketch 1 estimate:  %.0f\n", est1)
	fmt.Printf("Sketch 2 estimate:  %.0f\n", est2)
	fmt.Printf("Merged estimate:    %.0f\n", mergedEstimate)
	fmt.Printf("Expected unique:    %d\n", expected)

	mergeError := math.Abs(float64(mergedEstimate)-float64(expected)) / float64(expected) * 100
	fmt.Printf("Merge error:        %.2f%%\n", mergeError)

	if mergeError < 5 {
		fmt.Println("✓ Merge accuracy: GOOD")
	} else {
		fmt.Println("✗ Merge accuracy: NEEDS ATTENTION")
	}
}

// testPrecisionSensitivity shows how precision affects accuracy.
func testPrecisionSensitivity() {
	fmt.Println("\n--- Precision Sensitivity Test ---")

	cardinality := 50000
	runs := 10

	precisions := []hyperloglog.Precision{6, 8, 10, 12, 14}

	for _, p := range precisions {
		var totalError float64
		var minError, maxError float64 = math.MaxFloat64, 0

		for run := 0; run < runs; run++ {
			hll := hyperloglog.NewWithPrecision(p)

			// Add elements
			for i := 0; i < cardinality; i++ {
				hll.Add([]byte(fmt.Sprintf("precision-test-%d-%d", run, i)))
			}

			estimate := hll.Estimate()
			error := math.Abs(float64(estimate)-float64(cardinality)) / float64(cardinality) * 100

			totalError += error
			if error < minError {
				minError = error
			}
			if error > maxError {
				maxError = error
			}
		}

		avgError := totalError / float64(runs)

		fmt.Printf("p=%-2d | avg error: %.2f%% | min: %.2f%% | max: %.2f%% | memory: %d KB\n",
			p, avgError, minError, maxError, float64(hyperloglog.NewWithPrecision(p).MemoryBytes())/1024)
	}
}

// testLargeScale demonstrates performance with large datasets.
func testLargeScale() {
	fmt.Println("\n--- Large Scale Performance Test ---")

	scales := []int{100000, 500000, 1000000}

	for _, n := range scales {
		hll := hyperloglog.NewWithPrecision(hyperloglog.Precision(14))

		start := time.Now()

		// Add elements
		rng := rand.New(rand.NewSource(42))
		for i := 0; i < n; i++ {
			// Use random strings to simulate real-world data
			s := fmt.Sprintf("large-scale-%d-%d", i, rng.Intn(1000))
			hll.Add([]byte(s))
		}

		elapsed := time.Since(start)
		estimate := hll.Estimate()

		// For random strings, true cardinality is approximately n (most are unique)
		trueCard := n
		error := math.Abs(float64(estimate)-float64(trueCard)) / float64(trueCard) * 100

		fmt.Printf("n=%7d | time: %8s | estimate: %10.0f | error: %5.2f%% | memory: %d KB\n",
			n, elapsed, estimate, error, float64(hll.MemoryBytes())/1024)
	}

	fmt.Println("\nNote: HyperLogLog processes millions of elements in seconds")
	fmt.Println("with constant memory usage regardless of cardinality.")
}

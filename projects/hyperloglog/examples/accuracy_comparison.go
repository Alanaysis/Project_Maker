package main

import (
	"fmt"
	"math"
	"time"

	hyperloglog "hyperloglog/src"
)

// This example compares accuracy across different precision values.
//
// Higher precision (more buckets) gives better accuracy but uses more memory.
// This demonstrates the precision-accuracy trade-off.
func main() {
	fmt.Println("=== HyperLogLog Accuracy vs Precision ===\n")

	trueCardinality := 100000
	numElements := trueCardinality

	// Test different precision values
	precisions := []hyperloglog.Precision{
		hyperloglog.Precision(4),
		hyperloglog.Precision(6),
		hyperloglog.Precision(8),
		hyperloglog.Precision(10),
		hyperloglog.Precision(12),
		hyperloglog.Precision(14),
		hyperloglog.Precision(16),
	}

	fmt.Printf("True cardinality: %d\n\n", trueCardinality)
	fmt.Printf("%-8s | %-10s | %-10s | %-10s | %-12s | %-12s\n",
		"Precision", "Buckets", "Estimate", "Error %", "Std Error %", "Memory (KB)")
	fmt.Println("-" + "-" + "--------+-------------+------------+------------+--------------+--------------")

	for _, p := range precisions {
		hll := hyperloglog.NewWithPrecision(p)

		// Add elements
		start := time.Now()
		for i := 0; i < numElements; i++ {
			hll.Add([]byte(fmt.Sprintf("unique-element-%d", i)))
		}
		elapsed := time.Since(start)

		// Get estimate
		estimate := hll.Estimate()
		error := math.Abs(float64(estimate)-float64(trueCardinality)) / float64(trueCardinality) * 100
		memoryKB := float64(hll.MemoryBytes()) / 1024

		fmt.Printf("p=%-5d | m=%-10d | %-10.0f | %-9.2f%% | %-11.2f%% | %.2f\n",
			p, hll.BucketCount(), estimate, error, hll.StandardError()*100, memoryKB)

		fmt.Printf("  Insert time: %s\n", elapsed)
	}

	fmt.Println("\n--- Key Observations ---")
	fmt.Println("1. Higher precision = more buckets = better accuracy")
	fmt.Println("2. Memory grows exponentially: each +2 in p = 4x more memory")
	fmt.Println("3. Accuracy improves logarithmically: each +2 in p = 2x better")
	fmt.Println("4. p=10 (1KB) is the sweet spot for most applications")
	fmt.Println("5. p=14 (16KB) for high-accuracy needs")
	fmt.Println("6. p=16 (64KB) for production-grade cardinality estimation")
}

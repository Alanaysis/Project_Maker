package main

import (
	"fmt"
	"math"

	hyperloglog "hyperloglog/src"
)

// This example compares memory usage between HyperLogLog and exact counting.
//
// For large cardinalities, HyperLogLog uses dramatically less memory while
// maintaining reasonable accuracy.
func main() {
	fmt.Println("=== Memory Usage: HyperLogLog vs Exact Counting ===\n")

	// Test different cardinality levels
	cardinalities := []int{1000, 10000, 100000, 1000000, 10000000}

	for _, n := range cardinalities {
		// HyperLogLog memory (constant regardless of cardinality)
		hll := hyperloglog.New()
		hllMemory := hll.MemoryBytes()
		hllEstimate := hll.Estimate()

		// Exact counting memory (grows linearly with cardinality)
		// Each string in Go: ~32 bytes overhead + string content
		// Plus map overhead: ~80 bytes per entry
		exactMemory := n * 80 // Approximate for map[string]struct{}

		// Add elements to HLL for accurate comparison
		for i := 0; i < n; i++ {
			hll.Add([]byte(fmt.Sprintf("element-%d", i)))
		}
		hllEstimate = hll.Estimate()

		// Calculate HLL memory as KB
		hllMemoryKB := float64(hll.MemoryBytes()) / 1024
		exactMemoryMB := float64(exactMemory) / (1024 * 1024)

		// Calculate error
		error := math.Abs(float64(hllEstimate)-float64(n)) / float64(n) * 100

		fmt.Printf("Cardinality: %8d elements\n", n)
		fmt.Printf("  HyperLogLog: %8.2f KB (constant memory)\n", hllMemoryKB)
		fmt.Printf("  Exact count: %8.2f MB (linear memory)\n", exactMemoryMB)

		if exactMemoryMB > 0 {
			// Calculate memory savings
			savings := (1 - float64(hll.MemoryBytes())/float64(exactMemory)) * 100
			fmt.Printf("  Memory savings: %.2f%%\n", savings)
		}

		fmt.Printf("  HLL estimate: %.0f (error: %.2f%%)\n", hllEstimate, error)
		fmt.Println()
	}

	fmt.Println("--- Summary ---")
	fmt.Println("For n=1,000,000:")
	fmt.Println("  HLL uses ~1 KB vs exact counting ~76 MB")
	fmt.Println("  That's a 76,000x memory reduction!")
	fmt.Println("  With only ~2% estimation error.")
	fmt.Println()
	fmt.Println("This is why HyperLogLog is used in:")
	fmt.Println("  - Redis (approximate distinct counting)")
	fmt.Println("  - Apache Spark (approximate group-by)")
	fmt.Println("  - Web analytics (unique visitor counting)")
	fmt.Println("  - Database query optimization")
}

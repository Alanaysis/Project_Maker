// QuantileEstimation demonstrates T-Digest for quantile estimation from streaming data.
//
// T-Digest maintains a compressed set of centroids that approximate the distribution
// of streaming data. It provides higher precision for extreme quantiles (tails) and
// lower (but still good) precision near the median.
//
// Run: go run examples/quantile_estimation.go
package main

import (
	"fmt"
	"math"
	"math/rand"
	"sort"

	"streaming-algorithm/src"
)

func main() {
	fmt.Println("=== Quantile Estimation with T-Digest Demo ===")
	fmt.Println()

	// Demo 1: Quantile estimation on normal distribution
	fmt.Println("--- Demo 1: Quantile Estimation (Normal Distribution) ---")
	td := streaming.NewTDigest(100)

	rng := rand.New(rand.NewSource(42))
	numPoints := 100000

	// Generate normally distributed data using Box-Muller transform
	data := make([]float64, numPoints)
	for i := 0; i < numPoints; i++ {
		u1 := rng.Float64()
		u2 := rng.Float64()
		z := math.Sqrt(-2*math.Log(u1)) * math.Cos(2*math.Pi*u2)
		val := 50.0 + 10.0*z // mean=50, std=10
		data[i] = val
		td.Add(val)
	}

	// Compare T-Digest estimates with exact quantiles
	quantiles := []float64{0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99}
	exactData := make([]float64, len(data))
	copy(exactData, data)
	sort.Float64s(exactData)

	fmt.Printf("Quantile | Exact   | T-Digest | Error\n")
	fmt.Printf("---------|---------|----------|------\n")
	for _, q := range quantiles {
		// Exact quantile
		idx := int(float64(len(exactData)-1) * q)
		exact := exactData[idx]

		// T-Digest estimate
		est := td.Quantile(q)

		// Error
		err := math.Abs(est - exact)
		fmt.Printf("  %.2f   | %7.2f | %8.2f | %6.2f\n", q, exact, est, err)
	}

	fmt.Println()

	// Demo 2: Comparison with different compression settings
	fmt.Println("--- Demo 2: Compression Parameter Comparison ---")
	testQuantiles := []float64{0.01, 0.05, 0.50, 0.95, 0.99}
	trueValues := map[float64]float64{
		0.01: 26.75, // approximate true values for N(50, 10)
		0.05: 33.50,
		0.50: 50.00,
		0.95: 66.50,
		0.99: 73.25,
	}

	for _, compression := range []int{10, 50, 100, 200} {
		td2 := streaming.NewTDigest(compression)
		for _, v := range data {
			td2.Add(v)
		}
		fmt.Printf("\nCompression=%3d:\n", compression)
		fmt.Printf("  %-8s | %-8s | %-10s | %-10s\n", "Quantile", "True", "Estimate", "Error")
		for _, q := range testQuantiles {
			est := td2.Quantile(q)
			trueVal := trueValues[q]
			err := math.Abs(est - trueVal)
			fmt.Printf("  %-8.2f | %7.2f | %9.2f | %8.2f\n", q, trueVal, est, err)
		}
	}

	fmt.Println()

	// Demo 3: Streaming quantiles over time
	fmt.Println("--- Demo 3: Streaming Quantile Updates ---")
	td3 := streaming.NewTDigest(50)

	for round := 0; round < 5; round++ {
		// Add a batch of data
		batchSize := 1000
		for i := 0; i < batchSize; i++ {
			val := 40.0 + float64(round)*5 + rng.Float64()*20
			td3.Add(val)
		}
		fmt.Printf("After %d batches (%d total): p50=%.2f, p99=%.2f\n",
			round+1, td3.Count(), td3.Quantile(0.50), td3.Quantile(0.99))
	}

	fmt.Println()
	fmt.Println("=== Demo Complete ===")
}

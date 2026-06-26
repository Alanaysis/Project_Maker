// ReservoirSamplingDemo demonstrates reservoir sampling for uniform random sampling.
//
// Reservoir sampling allows you to select k random elements from a stream of
// unknown size, where each element has an equal probability of being selected.
//
// Run: go run examples/reservoir_sampling.go
package main

import (
	"fmt"
	"math/rand"
	"sort"
	"time"

	"streaming-algorithm/src"
)

func main() {
	fmt.Println("=== Reservoir Sampling Demo ===")
	fmt.Println()

	// Demo 1: Sample 5 elements from a stream of 100
	fmt.Println("--- Demo 1: Sample 5 from 100 elements ---")
	r := streaming.NewReservoirSample(5)

	streamSize := 100
	rng := rand.New(rand.NewSource(42))

	for i := 0; i < streamSize; i++ {
		val := float64(i) + rng.Float64()
		r.Add(val)
	}

	sample := r.Get()
	sort.Float64s(sample)

	fmt.Printf("Stream size: %d\n", streamSize)
	fmt.Printf("Reservoir size: %d\n", r.Count())
	fmt.Printf("Reservoir sample (sorted): %v\n", sample)
	fmt.Printf("Is complete: %v\n", r.IsComplete())

	fmt.Println()

	// Demo 2: Sample from a very large stream
	fmt.Println("--- Demo 2: Sample 10 from 10000 elements ---")
	r2 := streaming.NewReservoirSample(10)

	for i := 0; i < 10000; i++ {
		r2.Add(float64(i))
	}

	sample2 := r2.Get()
	sort.Float64s(sample2)

	fmt.Printf("Stream size: 10000\n")
	fmt.Printf("Reservoir size: %d\n", r2.Count())
	fmt.Printf("Reservoir sample (sorted): %v\n", sample2)

	fmt.Println()

	// Demo 3: Verify uniform sampling with a histogram
	fmt.Println("--- Demo 3: Uniform Sampling Verification (1000 trials) ---")
	sampleCount := make(map[int]int)
	trials := 1000
	k := 5
	n := 20

	for t := 0; t < trials; t++ {
		r := streaming.NewReservoirSample(k)
		for i := 0; i < n; i++ {
			r.Add(float64(i))
		}
		s := r.Get()
		for _, v := range s {
			sampleCount[int(v)]++
		}
	}

	fmt.Printf("Each element should appear ~%.1f times\n", float64(trials*k)/float64(n))
	fmt.Println("Element | Count | Expected")
	fmt.Println("--------|-------|----------")
	for i := 0; i < n; i++ {
		count := sampleCount[i]
		fmt.Printf("  %d     | %5d | %5.1f\n", i, count, float64(trials*k)/float64(n))
	}

	fmt.Println()
	fmt.Println("=== Demo Complete ===")
}

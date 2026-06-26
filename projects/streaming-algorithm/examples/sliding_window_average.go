// SlidingWindowAverage demonstrates fixed-size and time-based sliding window aggregations.
//
// This example shows:
// 1. Fixed-size window: keeps the last N values
// 2. Time-based window: keeps values within a time window
// 3. Real-time aggregation (avg, min, max, sum) over the window
//
// Run: go run examples/sliding_window_average.go
package main

import (
	"fmt"
	"math/rand"
	"time"

	"streaming-algorithm/src"
)

func main() {
	fmt.Println("=== Sliding Window Average Demo ===")
	fmt.Println()

	// Demo 1: Fixed-size sliding window
	fmt.Println("--- Demo 1: Fixed-Size Window ---")
	w := streaming.NewSlidingWindow(10)

	// Simulate incoming data stream
	rng := rand.New(rand.NewSource(42))
	for i := 0; i < 20; i++ {
		val := 50.0 + rng.Float64()*20 // values between 50 and 70
		w.Add(val)
		fmt.Printf("Added: %.2f | Window: %d elements | Avg: %.2f | Min: %.2f | Max: %.2f | Sum: %.2f\n",
			val, w.Count(), w.Avg(), w.Min(), w.Max(), w.Sum())
	}

	fmt.Println()

	// Demo 2: Time-based sliding window
	fmt.Println("--- Demo 2: Time-Based Window (100ms) ---")
	timeWindow := streaming.NewTimeSlidingWindow(100 * time.Millisecond)

	// Add some values quickly
	for i := 0; i < 5; i++ {
		val := 100.0 + float64(i)*10
		timeWindow.Add(val)
		fmt.Printf("Added: %.2f | Window: %d elements | Avg: %.2f\n",
			val, timeWindow.Count(), timeWindow.Avg())
	}

	// Wait for window to expire
	fmt.Println("Waiting 150ms for window to expire...")
	time.Sleep(150 * time.Millisecond)

	// Add more values (old ones should be gone)
	for i := 0; i < 3; i++ {
		val := 200.0 + float64(i)*10
		timeWindow.Add(val)
		fmt.Printf("Added: %.2f | Window: %d elements | Avg: %.2f\n",
			val, timeWindow.Count(), timeWindow.Avg())
	}

	fmt.Println()
	fmt.Println("=== Demo Complete ===")
}

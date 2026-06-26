// FrequencyEstimation demonstrates Count-Min Sketch for approximate frequency counting.
//
// Count-Min Sketch is a probabilistic data structure that estimates the frequency
// of elements in a stream using less memory than a hash map, at the cost of
// possible false positives (over-counting).
//
// Run: go run examples/frequency_estimation.go
package main

import (
	"fmt"

	"streaming-algorithm/src"
)

func main() {
	fmt.Println("=== Frequency Estimation with Count-Min Sketch Demo ===")
	fmt.Println()

	// Demo 1: Basic frequency counting
	fmt.Println("--- Demo 1: Basic Frequency Counting ---")
	cms := streaming.NewCountMinSketch(100, 5)

	words := []string{
		"apple", "banana", "apple", "cherry", "apple",
		"banana", "apple", "date", "banana", "apple",
		"cherry", "apple", "elderberry", "banana", "apple",
		"fig", "apple", "grape", "apple", "honeydew",
	}

	trueCounts := map[string]int{
		"apple":      8,
		"banana":     4,
		"cherry":     2,
		"date":       1,
		"elderberry": 1,
		"fig":        1,
		"grape":      1,
		"honeydew":   1,
	}

	for _, w := range words {
		cms.Add(w, 1)
	}

	fmt.Println("Word        | True | Estimated | Error")
	fmt.Println("------------|------|-----------|------")
	for word, trueCnt := range trueCounts {
		est := cms.Count(word)
		err := est - trueCnt
		fmt.Printf("%-11s | %4d | %9d | %+d\n", word, trueCnt, est, err)
	}

	fmt.Println()

	// Demo 2: Heavy hitter detection
	fmt.Println("--- Demo 2: Heavy Hitter Detection ---")
	cms2 := streaming.NewCountMinSketch(200, 5)

	// Simulate a stream with heavy hitters
	items := []string{
		"google.com", "google.com", "google.com", "google.com", "google.com",
		"google.com", "google.com", "google.com",
		"facebook.com", "facebook.com", "facebook.com", "facebook.com",
		"facebook.com", "facebook.com",
		"twitter.com", "twitter.com", "twitter.com",
		"reddit.com", "reddit.com",
		"youtube.com", "youtube.com",
		"amazon.com",
		"wiki.org",
		"random1", "random2", "random3", "random4", "random5",
	}

	for _, item := range items {
		cms2.Add(item, 1)
	}

	fmt.Println("Top URLs by estimated frequency:")
	threshold := 3
	for _, item := range items {
		count := cms2.Count(item)
		if count >= threshold {
			fmt.Printf("  %-15s: %d (threshold: %d)\n", item, count, threshold)
		}
	}

	fmt.Println()

	// Demo 3: Impact of sketch parameters
	fmt.Println("--- Demo 3: Effect of Sketch Parameters ---")
	testWord := "apple"
	trueCount := 500

	for _, width := range []int{10, 50, 100, 500} {
		cms := streaming.NewCountMinSketch(width, 5)
		for i := 0; i < trueCount; i++ {
			cms.Add(testWord, 1)
		}
		est := cms.Count(testWord)
		err := float64(est-trueCount) / float64(trueCount) * 100
		fmt.Printf("Width=%4d: estimated=%4d, error=%6.2f%%\n", width, est, err)
	}

	fmt.Println()
	fmt.Println("=== Demo Complete ===")
}

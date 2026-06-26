package main

import (
	"fmt"
	"time"

	"tsdb/src"
)

func main() {
	fmt.Println("=== Compression Ratio Demonstration ===")
	fmt.Println()

	storage := tsdb.NewStorage()

	// Create series with different data patterns
	storage.CreateSeries("constant", "Constant Values (RLE-friendly)")
	storage.CreateSeries("regular", "Regular Interval (Delta-friendly)")
	storage.CreateSeries("random", "Random Walk (Hard to compress)")

	// Constant data - excellent for RLE
	constantPoints := tsdb.GenerateConstantData("constant", "Constant", 100, time.Minute, 42.0)
	storage.WritePoints("constant", constantPoints.Points)

	// Regular interval data - excellent for delta encoding
	regularPoints := tsdb.GenerateMockData("regular", "Regular", 100, time.Minute, 50.0, 5.0)
	storage.WritePoints("regular", regularPoints.Points)

	// Random data - harder to compress
	randomPoints := tsdb.GenerateRandomData("random", "Random", 100, time.Minute, 50.0)
	storage.WritePoints("random", randomPoints.Points)

	// Show compression stats for each
	fmt.Println("--- Timestamp Delta Encoding ---")
	fmt.Println()

	for _, id := range []string{"constant", "regular", "random"} {
		points, _ := storage.QueryAll(id)
		stats := tsdb.ComputeDeltaStats(points)

		fmt.Printf("Series: %s\n", id)
		fmt.Printf("  Original size:     %s\n", tsdb.FormatBytes(stats.OriginalSize))
		fmt.Printf("  Delta-encoded:     %s\n", tsdb.FormatBytes(stats.EncodedSize))
		fmt.Printf("  Compression ratio: %.2fx\n", stats.CompressionRatio)
		fmt.Printf("  Unique deltas:     %d\n", stats.UniqueDeltas)
		fmt.Printf("  Delta range:       [%d, %d]\n", stats.MinDelta, stats.MaxDelta)
		fmt.Printf("  Average delta:     %d ns (%s)\n", int64(stats.AvgDelta), tsdb.FormatDuration(time.Duration(int64(stats.AvgDelta))))
		fmt.Println()
	}

	fmt.Println("--- Value RLE Compression ---")
	fmt.Println()

	for _, id := range []string{"constant", "regular", "random"} {
		points, _ := storage.QueryAll(id)
		stats := tsdb.ComputeValueStats(points)

		fmt.Printf("Series: %s\n", id)
		fmt.Printf("  Original size:      %s\n", tsdb.FormatBytes(stats.OriginalSize))
		fmt.Printf("  RLE-encoded:        %s\n", tsdb.FormatBytes(stats.EncodedSize))
		fmt.Printf("  Compression ratio:  %.2fx\n", stats.CompressionRatio)
		fmt.Printf("  Unique values:      %d\n", stats.UniqueValues)
		fmt.Printf("  Value range:        [%s, %s]\n", tsdb.FormatFloat(stats.MinValue), tsdb.FormatFloat(stats.MaxValue))
		fmt.Println()
	}

	// Demonstrate delta-of-delta for regular intervals
	fmt.Println("--- Delta-of-Delta Encoding (Regular Intervals) ---")
	fmt.Println()

	// Regular 10-second intervals
	regularData := make([]tsdb.Point, 10)
	baseTime := time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)
	for i := 0; i < 10; i++ {
		regularData[i] = tsdb.Point{
			Timestamp: baseTime.Add(time.Duration(i*10) * time.Second).UnixNano(),
			Value:     float64(100 + i),
		}
	}

	originalSize := len(regularData) * 8
	deltas := tsdb.DeltaEncode(makeTimestamps(regularData))
	dod := tsdb.DeltaOfDeltaEncode(makeTimestamps(regularData))

	fmt.Printf("Original timestamps:  %v\n", makeTimestamps(regularData))
	fmt.Printf("Delta encoding:       %v\n", deltas)
	fmt.Printf("Delta-of-delta:       %v\n", dod)
	fmt.Printf("\nOriginal size:        %d bytes\n", originalSize)
	fmt.Printf("Delta size:           %d bytes\n", len(deltas)*8)
	fmt.Printf("Delta-of-delta size:  %d bytes\n", len(dod)*8)

	// Show unique values in each encoding
	uniqueDelta := len(make(map[int64]bool))
	for _, d := range deltas {
		uniqueDelta++
		_ = d
	}
	uniqueDOD := make(map[int64]bool)
	for _, d := range dod {
		uniqueDOD[d] = true
	}
	fmt.Printf("Unique delta values:  %d\n", uniqueDelta)
	fmt.Printf("Unique DOD values:    %d\n", len(uniqueDOD))
	fmt.Println()

	// Demonstrate RLE on constant data
	fmt.Println("--- RLE on Constant Values ---")
	constantVals := make([]float64, 10)
	for i := 0; i < 10; i++ {
		constantVals[i] = 42.0
	}
	encoded := tsdb.RLEEncode(constantVals)
	fmt.Printf("Original:             %v (%d values)\n", constantVals, len(constantVals))
	fmt.Printf("RLE encoded:          %v (%d pairs)\n", encoded, len(encoded)/2)
	fmt.Printf("Compression:          %d values -> %d encoded elements\n", len(constantVals), len(encoded))
	fmt.Println()

	fmt.Println("=== Demo Complete ===")
}

func makeTimestamps(points []tsdb.Point) []int64 {
	ts := make([]int64, len(points))
	for i, p := range points {
		ts[i] = p.Timestamp
	}
	return ts
}

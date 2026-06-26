package tsdb

import (
	"fmt"
)

func ExampleDeltaEncode() {
	original := []int64{1000, 1010, 1020, 1030}
	deltas := DeltaEncode(original)
	fmt.Println(deltas)
	// Output: [1000 10 10 10]
}

func ExampleRLEEncode() {
	values := []float64{1.0, 1.0, 1.0, 2.0, 2.0}
	encoded := RLEEncode(values)
	fmt.Println(encoded)
	// Output: [1 3 2 2]
}

func ExampleComputeDeltaStats() {
	points := []Point{
		{Timestamp: 1000, Value: 1.0},
		{Timestamp: 1010, Value: 2.0},
		{Timestamp: 1020, Value: 3.0},
	}
	stats := ComputeDeltaStats(points)
	fmt.Printf("Unique deltas: %d, Ratio: %.2fx\n", stats.UniqueDeltas, stats.CompressionRatio)
	// Output: Unique deltas: 2, Ratio: 1.00x
}

func ExampleFormatBytes() {
	fmt.Println(FormatBytes(500))
	fmt.Println(FormatBytes(1024))
	fmt.Println(FormatBytes(1024 * 1024))
	// Output:
	// 500 B
	// 1.0 KB
	// 1.0 MB
}

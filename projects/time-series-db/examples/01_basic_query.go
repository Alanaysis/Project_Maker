package main

import (
	"fmt"
	"time"

	"tsdb/src"
)

func main() {
	fmt.Println("=== Time Series Database - Basic Write and Query Demo ===")
	fmt.Println()

	// Create storage
	storage := tsdb.NewStorage()

	// Create a series for CPU temperature
	ser := storage.CreateSeries("cpu.temp.host1", "CPU Temperature - Host 1")
	fmt.Printf("Created series: ID=%s, Name=%s\n", ser.ID, ser.Name)
	fmt.Println()

	// Generate mock data points (one per minute for 10 minutes)
	start := time.Date(2024, 1, 1, 10, 0, 0, 0, time.UTC)
	points := make([]tsdb.Point, 10)
	baseTemp := 45.0
	for i := 0; i < 10; i++ {
		points[i] = tsdb.Point{
			Timestamp: start.Add(time.Duration(i) * time.Minute).UnixNano(),
			Value:     baseTemp + float64(i)*0.5,
			Tags: map[string]string{
				"host":   "host1",
				"region": "us-east",
				"sensor": "cpu_temp",
			},
		}
	}

	// Write data
	fmt.Println("--- Writing Data ---")
	if err := storage.WritePoints("cpu.temp.host1", points); err != nil {
		fmt.Printf("Error writing: %v\n", err)
		return
	}
	fmt.Printf("Wrote %d data points\n", len(points))
	fmt.Println()

	// Query all data
	fmt.Println("--- Query All ---")
	allPoints, _ := storage.QueryAll("cpu.temp.host1")
	for _, p := range allPoints {
		fmt.Printf("  %s  Value: %s\n", tsdb.FormatTime(p.Timestamp), tsdb.FormatFloat(p.Value))
	}
	fmt.Println()

	// Query time range
	fmt.Println("--- Query Time Range (10:02 - 10:06) ---")
	rangeStart := start.Add(2 * time.Minute)
	rangeEnd := start.Add(6 * time.Minute)
	rangePoints, err := storage.QueryRange("cpu.temp.host1", rangeStart, rangeEnd)
	if err != nil {
		fmt.Printf("Error querying: %v\n", err)
		return
	}
	for _, p := range rangePoints {
		fmt.Printf("  %s  Value: %s\n", tsdb.FormatTime(p.Timestamp), tsdb.FormatFloat(p.Value))
	}
	fmt.Printf("  Total points in range: %d\n", len(rangePoints))
	fmt.Println()

	// Query nonexistent series
	fmt.Println("--- Query Nonexistent Series ---")
	_, err = storage.QueryRange("nonexistent", start, start.Add(time.Hour))
	if err != nil {
		fmt.Printf("  Expected error: %v\n", err)
	}
	fmt.Println()

	// Tag-based filtering
	fmt.Println("--- Tag-Based Filtering ---")
	storage.CreateSeries("cpu.temp.host2", "CPU Temperature - Host 2")
	host2Points := []tsdb.Point{
		{Timestamp: start.UnixNano(), Value: 50.0, Tags: map[string]string{"host": "host2", "region": "us-west"}},
	}
	storage.WritePoints("cpu.temp.host2", host2Points)

	matches := storage.QueryByTag("host", "host1")
	fmt.Printf("  Series with host=host1: %v\n", matches)

	matches = storage.QueryByTag("region", "us-west")
	fmt.Printf("  Series with region=us-west: %v\n", matches)
	fmt.Println()

	fmt.Println("=== Demo Complete ===")
}

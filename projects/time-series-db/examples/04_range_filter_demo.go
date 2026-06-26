package main

import (
	"fmt"
	"math"
	"math/rand"
	"time"

	"tsdb/src"
)

func main() {
	fmt.Println("=== Time Range Queries with Filtering Demo ===")
	fmt.Println()

	storage := tsdb.NewStorage()

	// Create multiple series with different tags
	hosts := []string{"server1", "server2", "server3"}
	regions := []string{"us-east", "us-west", "eu-west"}

	for i, host := range hosts {
		id := fmt.Sprintf("cpu.temp.%s", host)
		storage.CreateSeries(id, fmt.Sprintf("CPU Temp - %s", host))

		start := time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)
		points := make([]tsdb.Point, 24)
		for j := 0; j < 24; j++ {
			// Simulate temperature pattern
			baseTemp := 40 + float64(i)*5
			dailyPattern := 10 * math.Sin(float64(j)*math.Pi/12)
			points[j] = tsdb.Point{
				Timestamp: start.Add(time.Duration(j) * time.Hour).UnixNano(),
				Value:     baseTemp + dailyPattern + (rand.Float64()-0.5)*2,
				Tags: map[string]string{
					"host":   host,
					"region": regions[i],
					"sensor": "cpu_temp",
					"unit":   "celsius",
				},
			}
		}
		storage.WritePoints(id, points)
	}

	// Also add memory series
	storage.CreateSeries("mem.used.server1", "Memory Used - Server 1")
	start := time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)
	memPoints := make([]tsdb.Point, 24)
	for i := 0; i < 24; i++ {
		memPoints[i] = tsdb.Point{
			Timestamp: start.Add(time.Duration(i) * time.Hour).UnixNano(),
			Value:     4096 + rand.Float64()*512,
			Tags: map[string]string{
				"host":   "server1",
				"metric": "memory_used",
				"unit":   "MB",
			},
		}
	}
	storage.WritePoints("mem.used.server1", memPoints)

	// Query by time range
	fmt.Println("--- Time Range Query (Jan 1, 12:00 - Jan 1, 18:00) ---")
	rangeStart := start.Add(12 * time.Hour)
	rangeEnd := start.Add(18 * time.Hour)

	for _, host := range hosts {
		id := fmt.Sprintf("cpu.temp.%s", host)
		points, err := storage.QueryRange(id, rangeStart, rangeEnd)
		if err != nil {
			fmt.Printf("  Error querying %s: %v\n", id, err)
			continue
		}
		fmt.Printf("  %s: %d points\n", id, len(points))
		for _, p := range points {
			fmt.Printf("    %s  %s°C\n", tsdb.FormatTime(p.Timestamp), tsdb.FormatFloat(p.Value))
		}
		fmt.Println()
	}

	// Tag-based filtering
	fmt.Println("--- Tag-Based Filtering ---")

	// Find all series with host=server1
	matches := storage.QueryByTag("host", "server1")
	fmt.Printf("  host=server1: %v\n", matches)

	// Find all series with region=us-east
	matches = storage.QueryByTag("region", "us-east")
	fmt.Printf("  region=us-east: %v\n", matches)

	// Find all series with sensor=cpu_temp
	matches = storage.QueryByTag("sensor", "cpu_temp")
	fmt.Printf("  sensor=cpu_temp: %v\n", matches)
	fmt.Println()

	// Cross-series query
	fmt.Println("--- Cross-Series Query ---")
	seriesIDs := []string{"cpu.temp.server1", "cpu.temp.server2", "cpu.temp.server3"}
	results, err := tsdb.NewSeriesManager(storage).QueryAcrossSeries(seriesIDs, rangeStart, rangeEnd)
	if err != nil {
		fmt.Printf("  Error: %v\n", err)
	} else {
		for id, pts := range results {
			fmt.Printf("  %s: %d points\n", id, len(pts))
		}
	}
	fmt.Println()

	// Query with no overlap
	fmt.Println("--- Query with No Overlap ---")
	emptyStart := time.Date(2024, 6, 1, 0, 0, 0, 0, time.UTC)
	emptyEnd := time.Date(2024, 6, 2, 0, 0, 0, 0, time.UTC)
	points, _ := storage.QueryRange("cpu.temp.server1", emptyStart, emptyEnd)
	fmt.Printf("  cpu.temp.server1 in Jun 2024: %d points (expected 0)\n", len(points))
	fmt.Println()

	fmt.Println("=== Demo Complete ===")
}

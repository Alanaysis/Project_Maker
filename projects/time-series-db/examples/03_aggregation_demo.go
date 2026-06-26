package main

import (
	"fmt"
	"math"
	"math/rand"
	"time"

	"tsdb/src"
)

func main() {
	fmt.Println("=== Aggregation Queries (Downsampling) Demo ===")
	fmt.Println()

	storage := tsdb.NewStorage()
	storage.CreateSeries("cpu.usage", "CPU Usage Over Time")

	// Generate 60 data points (one per minute for an hour)
	start := time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)
	end := start.Add(time.Hour)
	points := make([]tsdb.Point, 60)
	for i := 0; i < 60; i++ {
		// Simulate daily pattern: low at midnight, peak at noon
		hour := float64(i) / 60.0 * 24
		pattern := 30 + 40*math.Sin((hour-6)*math.Pi/12)
		points[i] = tsdb.Point{
			Timestamp: start.Add(time.Duration(i) * time.Minute).UnixNano(),
			Value:     math.Max(0, math.Min(100, pattern+(rand.Float64()-0.5)*5)),
			Tags: map[string]string{
				"host":   "server1",
				"metric": "cpu_usage",
			},
		}
	}
	storage.WritePoints("cpu.usage", points)

	fmt.Println("--- Raw Data (first 10 points) ---")
	allPoints, _ := storage.QueryAll("cpu.usage")
	for i := 0; i < 10 && i < len(allPoints); i++ {
		fmt.Printf("  %s  CPU: %s%%\n", tsdb.FormatTime(allPoints[i].Timestamp), tsdb.FormatFloat(allPoints[i].Value))
	}
	fmt.Printf("  ... (%d total points)\n", len(allPoints))
	fmt.Println()

	// Downsample with different aggregation functions
	intervals := []time.Duration{
		10 * time.Minute,
		15 * time.Minute,
		30 * time.Minute,
		1 * time.Hour,
	}

	aggTypes := []tsdb.AggregationType{tsdb.AggAvg, tsdb.AggMin, tsdb.AggMax, tsdb.AggSum}

	for _, interval := range intervals {
		fmt.Printf("--- Downsample: %s intervals ---\n", tsdb.FormatDuration(interval))

		for _, agg := range aggTypes {
			result, err := storage.Downsample("cpu.usage", agg, interval, start, end)
			if err != nil {
				fmt.Printf("  Error: %v\n", err)
				continue
			}

			fmt.Printf("  [%s]", agg)
			for _, r := range result.Results {
				fmt.Printf(" %s(%s)", tsdb.FormatFloat(r.Value), tsdb.FormatDuration(r.EndTime.Sub(r.StartTime)))
			}
			fmt.Println()
		}
		fmt.Println()
	}

	// Show detailed output for one downsample
	fmt.Println("--- Detailed: 30-min Average ---")
	result, _ := storage.Downsample("cpu.usage", tsdb.AggAvg, 30*time.Minute, start, end)
	for _, r := range result.Results {
		fmt.Printf("  [%s - %s]  Avg CPU: %s%%\n",
			r.StartTime.Format("15:04"),
			r.EndTime.Format("15:04"),
			tsdb.FormatFloat(r.Value))
	}
	fmt.Println()

	fmt.Println("=== Demo Complete ===")
}

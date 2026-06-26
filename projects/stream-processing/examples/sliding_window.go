// Package main demonstrates sliding window aggregation.
//
// This example shows sliding windows: each event belongs to multiple
// overlapping windows. This is useful for computing rolling metrics
// like a moving average.
//
// Processing pipeline:
//
//	sensor readings → sliding window(10s, slide 5s) → sum/avg → output
//
// Run with: go run examples/sliding_window.go
package main

import (
	"fmt"
	"time"

	"stream-processing/src"
)

func main() {
	fmt.Println("=== Sliding Window Aggregation ===")
	fmt.Println()

	// Simulated sensor readings arriving every 2 seconds.
	baseTime := time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)
	events := make([]stream.Event, 0)

	// Sensor readings: temperature values in Celsius.
	readings := []float64{20.5, 21.3, 19.8, 22.1, 20.9, 21.7, 19.5, 23.0, 20.2, 21.8}

	for i, reading := range readings {
		events = append(events, stream.Event{
			ID:            int64(i + 1),
			Payload:       reading,
			EventTime:     baseTime.Add(time.Duration(i) * 2 * time.Second),
			ProcessingTime: baseTime.Add(time.Duration(i) * 2 * time.Second),
			Partition:     0,
		})
	}

	source := stream.NewSliceSource(events, "sensor-source")

	// Sliding window: 10-second windows, sliding every 5 seconds.
	// Each event belongs to 2-3 overlapping windows.
	assigner := &stream.SlidingWindowAssigner{
		Size:  10 * time.Second,
		Slide: 5 * time.Second,
	}

	aggFactory := func() stream.Aggregator {
		return &sumAvgAggregator{}
	}

	trigger := &stream.WatermarkTrigger{}
	sink := &stream.ConsoleSink{}

	runner := stream.NewWindowRunner(source, sink, assigner, aggFactory, trigger)
	runner.Process()

	fmt.Println()
	fmt.Println("=== Sliding Window Complete ===")
}

// sumAvgAggregator tracks both sum and count for computing average.
type sumAvgAggregator struct {
	sum   float64
	count int64
}

func (a *sumAvgAggregator) Add(event stream.Event) {
	val := extractFloat(event.Payload)
	a.sum += val
	a.count++
}

func (a *sumAvgAggregator) Result() interface{} {
	avg := 0.0
	if a.count > 0 {
		avg = a.sum / float64(a.count)
	}
	return map[string]interface{}{
		"sum":   a.sum,
		"count": a.count,
		"avg":   avg,
	}
}

func (a *sumAvgAggregator) Copy() stream.Aggregator {
	return &sumAvgAggregator{
		sum:   a.sum,
		count: a.count,
	}
}

func extractFloat(payload interface{}) float64 {
	switch v := payload.(type) {
	case float64:
		return v
	case float32:
		return float64(v)
	case int:
		return float64(v)
	case int64:
		return float64(v)
	default:
		return 0
	}
}

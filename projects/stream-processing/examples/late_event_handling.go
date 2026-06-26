// Package main demonstrates late event handling with watermarks.
//
// Watermarks are a mechanism for handling out-of-order events in stream processing.
// A watermark represents a guarantee that "no events with timestamp before W will arrive."
//
// This example shows:
//  1. How watermarks advance as events arrive
//  2. How late events are detected and handled
//  3. Different late event policies (discard, output, side-output, update)
//
// Run with: go run examples/late_event_handling.go
package main

import (
	"fmt"
	"time"

	"stream-processing/src"
)

func main() {
	fmt.Println("=== Late Event Handling ===")
	fmt.Println()

	// Demonstrate watermark progression.
	fmt.Println("--- Watermark Progression ---")
	demoWatermarkProgression()

	fmt.Println()

	// Demonstrate late event handling with different policies.
	fmt.Println("--- Late Event Handling Policies ---")
	demoLateEventPolicies()

	fmt.Println()

	// Demonstrate windowing with late events.
	fmt.Println("--- Windowed Processing with Late Events ---")
	demoWindowedLateEvents()

	fmt.Println()
	fmt.Println("=== Late Event Handling Complete ===")
}

// demoWatermarkProgression shows how watermarks advance.
func demoWatermarkProgression() {
	wm := stream.NewWatermark(10 * time.Second)

	// Simulate events arriving out of order.
	type eventTime struct {
		id    int64
		event time.Duration
	}

	events := []eventTime{
		{1, 0 * time.Second},   // earliest event
		{2, 5 * time.Second},   // in order
		{3, 10 * time.Second},  // in order
		{4, 8 * time.Second},   // out of order! (event time < watermark)
		{5, 15 * time.Second},  // in order
		{6, 12 * time.Second},  // out of order!
		{7, 20 * time.Second},  // in order
		{8, 25 * time.Second},  // in order
		{9, 3 * time.Second},   // very late!
	}

	for _, et := range events {
		eventTime := time.Unix(int64(et.event.Seconds()), 0)
		isLate := wm.IsLate(eventTime)
		isTooLate := wm.IsTooLate(eventTime)

		status := "normal"
		if isTooLate {
			status = "TOO LATE (discarded)"
		} else if isLate {
			status = "LATE (handled)"
		}

		fmt.Printf("  Event %d: event_time=%s watermark=%s [%s]\n",
			et.id,
			eventTime.Format("15:04:05"),
			wm.WatermarkTime.Format("15:04:05"),
			status)

		wm.Update(eventTime)
	}

	fmt.Printf("\n  Final watermark: %s\n", wm.WatermarkTime.Format("15:04:05"))
	fmt.Printf("  Max out-of-orderness: %s\n", wm.MaxOutOfOrderness)
}

// demoLateEventPolicies shows different late event handling strategies.
func demoLateEventPolicies() {
	baseTime := time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)

	// Create a stream with late events.
	events := []stream.Event{
		{ID: 1, Payload: 10.0, EventTime: baseTime, ProcessingTime: baseTime, Partition: 0},
		{ID: 2, Payload: 20.0, EventTime: baseTime.Add(5 * time.Second), ProcessingTime: baseTime.Add(5 * time.Second), Partition: 0},
		{ID: 3, Payload: 30.0, EventTime: baseTime.Add(10 * time.Second), ProcessingTime: baseTime.Add(10 * time.Second), Partition: 0},
		// Late event: event time is before watermark
		{ID: 4, Payload: 15.0, EventTime: baseTime.Add(3 * time.Second), ProcessingTime: baseTime.Add(20 * time.Second), Partition: 0},
		// Very late event: past watermark + lateness
		{ID: 5, Payload: 5.0, EventTime: baseTime.Add(1 * time.Second), ProcessingTime: baseTime.Add(30 * time.Second), Partition: 0},
	}

	source := stream.NewSliceSource(events, "late-events")
	assigner := &stream.TumblingWindowAssigner{Size: 15 * time.Second}

	// Test each late event policy.
	policies := []struct {
		policy stream.LateEventPolicy
		name   string
	}{
		{stream.LateDiscard, "Discard"},
		{stream.LateOutput, "Output"},
		{stream.LateSideOutput, "Side-Output"},
		{stream.LateUpdate, "Update"},
	}

	for _, p := range policies {
		fmt.Printf("\n  Policy: %s\n", p.name)
		lateSink := &lateEventSink{}
		streamProc := stream.NewWindowedStream(source, assigner, func() stream.Aggregator {
			return &stream.SumAggregator{}
		}, &stream.WatermarkTrigger{})

		streamProc.WithLatePolicy(p.policy)
		streamProc.WithLateSink(lateSink)

		streamProc.Process()

		if lateSink.count > 0 {
			fmt.Printf("  Late events output: %d\n", lateSink.count)
		}

		// Reset source.
		source = stream.NewSliceSource(events, "late-events")
	}
}

// demoWindowedLateEvents shows late events in the context of windowed processing.
func demoWindowedLateEvents() {
	baseTime := time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)

	events := []stream.Event{
		{ID: 1, Payload: 100, EventTime: baseTime.Add(0 * time.Second), ProcessingTime: baseTime.Add(0 * time.Second), Partition: 0},
		{ID: 2, Payload: 200, EventTime: baseTime.Add(2 * time.Second), ProcessingTime: baseTime.Add(2 * time.Second), Partition: 0},
		{ID: 3, Payload: 150, EventTime: baseTime.Add(4 * time.Second), ProcessingTime: baseTime.Add(4 * time.Second), Partition: 0},
		// Late event for first window
		{ID: 4, Payload: 50, EventTime: baseTime.Add(1 * time.Second), ProcessingTime: baseTime.Add(10 * time.Second), Partition: 0},
		{ID: 5, Payload: 300, EventTime: baseTime.Add(8 * time.Second), ProcessingTime: baseTime.Add(12 * time.Second), Partition: 0},
		{ID: 6, Payload: 250, EventTime: baseTime.Add(10 * time.Second), ProcessingTime: baseTime.Add(14 * time.Second), Partition: 0},
	}

	source := stream.NewSliceSource(events, "windowed-late")
	assigner := &stream.TumblingWindowAssigner{Size: 5 * time.Second}

	streamProc := stream.NewWindowedStream(source, assigner, func() stream.Aggregator {
		return &stream.CountAggregator{}
	}, &stream.WatermarkTrigger{})

	// Track late events
	lateCount := 0
	streamProc.WithLateHandler(func(event stream.Event) {
		lateCount++
		fmt.Printf("  [Late] Event %d (value=%v) discarded as too late\n", event.ID, event.Payload)
	})

	results := streamProc.Process()
	fmt.Printf("  Total window results: %d\n", len(results))
	fmt.Printf("  Late events handled: %d\n", lateCount)
}

// lateEventSink collects late events for counting.
type lateEventSink struct {
	count int
}

func (s *lateEventSink) Write(window stream.Window, partition int64, result interface{}) error {
	s.count++
	return nil
}

func (s *lateEventSink) Name() string { return "late-sink" }

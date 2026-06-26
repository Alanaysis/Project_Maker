// Package main demonstrates session window analysis.
//
// Session windows group events that are close together in time.
// They are useful for analyzing user behavior patterns, such as
// grouping page views into a single visit/session.
//
// Processing pipeline:
//
//	user events → session window(gap=5s) → aggregate per session → output
//
// Run with: go run examples/session_window.go
package main

import (
	"fmt"
	"time"

	"stream-processing/src"
)

func main() {
	fmt.Println("=== Session Window Analysis ===")
	fmt.Println()

	// Simulated user activity events with varying time gaps.
	baseTime := time.Date(2024, 1, 1, 10, 0, 0, 0, time.UTC)
	events := make([]stream.Event, 0)

	// Session 1: rapid activity (page views within 2 seconds)
	events = append(events, stream.Event{ID: 1, Payload: "page:home", EventTime: baseTime.Add(0 * time.Second), ProcessingTime: baseTime.Add(0 * time.Second), Partition: 1})
	events = append(events, stream.Event{ID: 2, Payload: "page:products", EventTime: baseTime.Add(1 * time.Second), ProcessingTime: baseTime.Add(1 * time.Second), Partition: 1})
	events = append(events, stream.Event{ID: 3, Payload: "page:cart", EventTime: baseTime.Add(2 * time.Second), ProcessingTime: baseTime.Add(2 * time.Second), Partition: 1})

	// Gap of 10 seconds (exceeds 5-second session gap)

	// Session 2: activity after the gap
	events = append(events, stream.Event{ID: 4, Payload: "page:checkout", EventTime: baseTime.Add(12 * time.Second), ProcessingTime: baseTime.Add(12 * time.Second), Partition: 1})
	events = append(events, stream.Event{ID: 5, Payload: "page:confirmation", EventTime: baseTime.Add(14 * time.Second), ProcessingTime: baseTime.Add(14 * time.Second), Partition: 1})

	// Gap of 8 seconds

	// Session 3: another burst
	events = append(events, stream.Event{ID: 6, Payload: "page:home", EventTime: baseTime.Add(25 * time.Second), ProcessingTime: baseTime.Add(25 * time.Second), Partition: 1})
	events = append(events, stream.Event{ID: 7, Payload: "page:search", EventTime: baseTime.Add(27 * time.Second), ProcessingTime: baseTime.Add(27 * time.Second), Partition: 1})
	events = append(events, stream.Event{ID: 8, Payload: "page:products", EventTime: baseTime.Add(30 * time.Second), ProcessingTime: baseTime.Add(30 * time.Second), Partition: 1})

	source := stream.NewSliceSource(events, "user-events")

	// Session window with 5-second gap.
	assigner := &stream.SessionWindowAssigner{Gap: 5 * time.Second}

	aggFactory := func() stream.Aggregator {
		return &sessionAggregator{}
	}

	trigger := &stream.WatermarkTrigger{}
	sink := &stream.ConsoleSink{}

	runner := stream.NewWindowRunner(source, sink, assigner, aggFactory, trigger)
	runner.Process()

	fmt.Println()

	// Also demonstrate the SessionManager directly.
	fmt.Println("--- Session Manager Demo ---")
	demoSessionManager()

	fmt.Println()
	fmt.Println("=== Session Window Complete ===")
}

// sessionAggregator counts events and tracks page names.
type sessionAggregator struct {
	count   int64
	pages   map[string]int64
}

func (a *sessionAggregator) Add(event stream.Event) {
	a.count++
	if a.pages == nil {
		a.pages = make(map[string]int64)
	}
	page := fmt.Sprintf("%v", event.Payload)
	a.pages[page]++
}

func (a *sessionAggregator) Result() interface{} {
	return map[string]interface{}{
		"event_count": a.count,
		"pages":       a.pages,
	}
}

func (a *sessionAggregator) Copy() stream.Aggregator {
	copy := &sessionAggregator{
		count: a.count,
		pages: make(map[string]int64),
	}
	for k, v := range a.pages {
		copy.pages[k] = v
	}
	return copy
}

// demoSessionManager shows how session windows are managed dynamically.
func demoSessionManager() {
	gap := 5 * time.Second
	manager := stream.NewSessionManager(gap)

	baseTime := time.Date(2024, 1, 1, 10, 0, 0, 0, time.UTC)

	// Simulate events arriving in order.
	eventTimes := []time.Duration{0, 1, 2, 12, 14, 25, 27, 30}
	for i, t := range eventTimes {
		event := stream.Event{
			ID:            int64(i + 1),
			Payload:       fmt.Sprintf("event-%d", i+1),
			EventTime:     baseTime.Add(t),
			ProcessingTime: baseTime.Add(t),
			Partition:     0,
		}
		session := manager.ProcessEvent(event)
		fmt.Printf("  Event %d (t=%ds) → Session: %s to %s (active=%v)\n",
			event.ID, t.Seconds(),
			session.Start.Format("15:04:05"),
			session.End.Format("15:04:05"),
			session.Active)
	}

	fmt.Printf("  Active sessions: %d\n", manager.ActiveCount())
}

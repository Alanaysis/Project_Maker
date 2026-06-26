// Package main demonstrates word count on streaming data.
//
// This example shows how to use the stream processing framework
// to perform a classic word count operation on a stream of text.
//
// Processing pipeline:
//
//	"text hello world hello" → split → words → tumbling window(10s) → count → output
//
// Run with: go run examples/word_count.go
package main

import (
	"fmt"
	"strings"
	"time"

	"stream-processing/src"
)

func main() {
	fmt.Println("=== Word Count on Streaming Data ===")
	fmt.Println()

	// Simulated input stream: a sequence of text events arriving over time.
	// Each event contains a line of text with an event-time timestamp.
	baseTime := time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)
	events := make([]stream.Event, 0)

	lines := []string{
		"hello world",
		"hello stream",
		"world stream processing",
		"hello",
		"stream processing hello",
		"world hello stream",
		"processing world",
		"hello world hello",
	}

	for i, line := range lines {
		events = append(events, stream.Event{
			ID:            int64(i + 1),
			Payload:       line,
			EventTime:     baseTime.Add(time.Duration(i) * 2 * time.Second),
			ProcessingTime: baseTime.Add(time.Duration(i) * 2 * time.Second),
			Partition:     0,
		})
	}

	// Create source from events.
	source := stream.NewSliceSource(events, "word-count-source")

	// Create tumbling window assigner (10-second windows).
	assigner := &stream.TumblingWindowAssigner{Size: 10 * time.Second}

	// Use CountAggregator to count word occurrences.
	// We'll use a custom aggregator that counts words.
	aggFactory := func() stream.Aggregator {
		return &wordCountAggregator{}
	}

	// Use watermark trigger to close windows.
	trigger := &stream.WatermarkTrigger{}

	// Create console sink for output.
	sink := &stream.ConsoleSink{}

	// Create and run the window runner.
	runner := stream.NewWindowRunner(source, sink, assigner, aggFactory, trigger)
	runner.Process()

	fmt.Println()
	fmt.Println("=== Word Count Complete ===")
}

// wordCountAggregator counts word occurrences across events.
type wordCountAggregator struct {
	words map[string]int64
}

func (a *wordCountAggregator) Add(event stream.Event) {
	if a.words == nil {
		a.words = make(map[string]int64)
	}
	text := fmt.Sprintf("%v", event.Payload)
	words := strings.Fields(text)
	for _, w := range words {
		w = strings.ToLower(w)
		a.words[w]++
	}
}

func (a *wordCountAggregator) Result() interface{} {
	return a.words
}

func (a *wordCountAggregator) Copy() stream.Aggregator {
	copy := &wordCountAggregator{
		words: make(map[string]int64),
	}
	for k, v := range a.words {
		copy.words[k] = v
	}
	return copy
}

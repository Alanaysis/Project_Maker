package stream

import (
	"fmt"
	"math"
	"time"
)

// ---------------------------------------------------------------------------
// WindowedAggregationResult: the output of a windowed aggregation.
// ---------------------------------------------------------------------------

// WindowedAggregationResult holds the result of aggregating events in a window.
type WindowedAggregationResult struct {
	Window    Window
	Partition int64
	Result    interface{}
	Timestamp time.Time
}

// String returns a human-readable representation.
func (r WindowedAggregationResult) String() string {
	return fmt.Sprintf("Result{Window=%s, Partition=%d, Result=%v}",
		r.Window.String(), r.Partition, r.Result)
}

// ---------------------------------------------------------------------------
// WindowedStream: a higher-level stream abstraction with windowing support.
// ---------------------------------------------------------------------------

// WindowedStream represents a stream that has been windowed and is ready for aggregation.
type WindowedStream struct {
	source       Source
	assigner     WindowAssigner
	aggregator   func() Aggregator
	trigger      Trigger
	watermark    *Watermark
	state        *StateManager
	lateHandler  func(Event)
	latePolicy   LateEventPolicy
	lateSink     Sink
	results      []WindowedAggregationResult
}

// NewWindowedStream creates a new windowed stream processor.
func NewWindowedStream(source Source, assigner WindowAssigner, aggregator func() Aggregator, trigger Trigger) *WindowedStream {
	return &WindowedStream{
		source:      source,
		assigner:    assigner,
		aggregator:  aggregator,
		trigger:     trigger,
		watermark:   NewWatermark(1 * time.Minute),
		state:       NewStateManager(),
		latePolicy:  LateDiscard,
		results:     make([]WindowedAggregationResult, 0),
	}
}

// WithLateHandler sets the late event handler.
func (s *WindowedStream) WithLateHandler(handler func(Event)) *WindowedStream {
	s.lateHandler = handler
	return s
}

// WithLatePolicy sets the late event handling policy.
func (s *WindowedStream) WithLatePolicy(policy LateEventPolicy) *WindowedStream {
	s.latePolicy = policy
	return s
}

// WithLateSink sets a sink for late events.
func (s *WindowedStream) WithLateSink(sink Sink) *WindowedStream {
	s.lateSink = sink
	return s
}

// Process runs the windowed stream processing loop.
func (s *WindowedStream) Process() []WindowedAggregationResult {
	triggerStates := make(map[string]*TriggerState)

	for {
		event, ok := s.source.Read()
		if !ok {
			break
		}

		// Update watermark.
		s.watermark.Update(event.EventTime)

		// Handle late events.
		if s.watermark.IsTooLate(event.EventTime) {
			s.handleLateEvent(event)
			continue
		}

		// Assign event to windows.
		windows := s.assigner.AssignWindows(event.EventTime, event.ProcessingTime)
		for _, win := range windows {
			s.processEvent(event, win, triggerStates)
		}

		// Check watermark-based triggers.
		s.checkWatermarkTriggers(triggerStates)
	}

	// Flush remaining windows.
	s.flushRemaining(triggerStates)

	return s.results
}

// processEvent adds an event to a window.
func (s *WindowedStream) processEvent(event Event, window Window, triggerStates map[string]*TriggerState) {
	agg := s.state.Get(window, event.Partition, s.aggregator)
	agg.Add(event)

	wk := windowKey(window, event.Partition)
	ts := triggerStates[wk]
	if ts == nil {
		ts = &TriggerState{}
		triggerStates[wk] = ts
	}

	if s.trigger.OnEvent(ts, event, window) {
		s.emit(window, event.Partition, triggerStates)
	}
}

// checkWatermarkTriggers checks for watermark-triggered window completions.
func (s *WindowedStream) checkWatermarkTriggers(triggerStates map[string]*TriggerState) {
	for wk, ts := range triggerStates {
		if ts.Fired {
			continue
		}
		var startUnix, endUnix, wType int64
		_, err := fmt.Sscanf(wk, "%d:%d:%d", &startUnix, &endUnix, &wType)
		if err != nil {
			continue
		}
		win := Window{
			Start: time.Unix(startUnix, 0),
			End:   time.Unix(endUnix, 0),
			Type:  WindowType(wType),
		}
		if !s.watermark.WatermarkTime.Before(win.End) {
			ts.Fired = true
			s.emit(win, 0, triggerStates)
		}
	}
}

// emit outputs the result for a window.
func (s *WindowedStream) emit(window Window, partition int64, triggerStates map[string]*TriggerState) {
	result, ok := s.state.GetResult(window, partition)
	if !ok {
		return
	}

	wk := windowKey(window, partition)
	ts := triggerStates[wk]
	if ts != nil {
		ts.Fired = false
		ts.Count = 0
	}

	res := WindowedAggregationResult{
		Window:    window,
		Partition: partition,
		Result:    result,
		Timestamp: time.Now(),
	}
	s.results = append(s.results, res)
	fmt.Printf("[Result] %s\n", res.String())
}

// flushRemaining outputs all remaining window results.
func (s *WindowedStream) flushRemaining(triggerStates map[string]*TriggerState) {
	for wk, ts := range triggerStates {
		if ts.Fired {
			continue
		}
		var startUnix, endUnix, wType int64
		_, err := fmt.Sscanf(wk, "%d:%d:%d", &startUnix, &endUnix, &wType)
		if err != nil {
			continue
		}
		win := Window{
			Start: time.Unix(startUnix, 0),
			End:   time.Unix(endUnix, 0),
			Type:  WindowType(wType),
		}
		result, ok := s.state.GetResult(win, 0)
		if !ok {
			continue
		}
		res := WindowedAggregationResult{
			Window:    win,
			Partition: 0,
			Result:    result,
			Timestamp: time.Now(),
		}
		s.results = append(s.results, res)
		fmt.Printf("[Result] %s\n", res.String())
		ts.Fired = true
	}
}

// handleLateEvent processes a late-arriving event.
func (s *WindowedStream) handleLateEvent(event Event) {
	switch s.latePolicy {
	case LateDiscard:
		fmt.Printf("[Late] Discarded late event: %s\n", event.EventTime.Format(time.RFC3339))
	case LateOutput:
		if s.lateSink != nil {
			s.lateSink.Write(Window{}, 0, event)
		}
		fmt.Printf("[Late] Output late event: %s\n", event.EventTime.Format(time.RFC3339))
	case LateSideOutput:
		fmt.Printf("[Late] Side-output late event: %s\n", event.EventTime.Format(time.RFC3339))
	case LateUpdate:
		fmt.Printf("[Late] Updating state with late event: %s\n", event.EventTime.Format(time.RFC3339))
		// In a real system, we would re-open windows and re-aggregate.
	}
}

// ---------------------------------------------------------------------------
// Aggregation utilities
// ---------------------------------------------------------------------------

// AggregateStats holds descriptive statistics over a set of values.
type AggregateStats struct {
	Sum    float64
	Count  int64
	Avg    float64
	Min    float64
	Max    float64
	Variance float64
}

// ComputeStats computes descriptive statistics from a slice of float64 values.
func ComputeStats(values []float64) AggregateStats {
	if len(values) == 0 {
		return AggregateStats{}
	}

	sum := 0.0
	minVal := math.MaxFloat64
	maxVal := -math.MaxFloat64

	for _, v := range values {
		sum += v
		if v < minVal {
			minVal = v
		}
		if v > maxVal {
			maxVal = v
		}
	}

	avg := sum / float64(len(values))

	// Compute variance.
	varSum := 0.0
	for _, v := range values {
		diff := v - avg
		varSum += diff * diff
	}
	variance := varSum / float64(len(values))

	return AggregateStats{
		Sum:      sum,
		Count:    int64(len(values)),
		Avg:      avg,
		Min:      minVal,
		Max:      maxVal,
		Variance: variance,
	}
}

// Package stream provides a lightweight stream processing framework
// for learning windowed aggregation, state management, and watermarking.
//
// Core concepts:
//   - Event: A data point with a timestamp (event time).
//   - Window: A time-bounded bucket that groups events for aggregation.
//     Types: tumbling (non-overlapping), sliding (overlapping), session (gap-based).
//   - Trigger: Determines when a window's contents are ready for output.
//   - Watermark: A progress guarantee that "no more events before time T will arrive".
//     Used to handle late data and close windows.
//   - State: Per-window or global accumulators (sum, count, min, max, etc.).
//   - Source/Sink: Interfaces for reading input events and writing results.
//
// Processing pipeline:
//
//	data stream → event time assignment → window assignment → aggregation → output
//
// The framework supports event-time processing with watermarks, allowing
// correct results even when events arrive out of order.
package stream

import (
	"fmt"
	"time"
)

// ---------------------------------------------------------------------------
// Event: the fundamental unit of data in the stream.
// ---------------------------------------------------------------------------

// Event represents a single data point arriving in the stream.
// Each event carries an event-time timestamp (when it actually happened),
// a processing-time timestamp (when it was observed), and a payload.
type Event struct {
	ID            int64
	Payload       interface{}
	EventTime     time.Time // The time the event occurred (event time)
	ProcessingTime time.Time // The time the event was observed (processing time)
	Partition     int64     // Optional partition identifier for keyed streams
}

// String returns a human-readable representation of the event.
func (e Event) String() string {
	return fmt.Sprintf("Event{ID=%d, Payload=%v, EventTime=%s, ProcTime=%s, Partition=%d}",
		e.ID, e.Payload, e.EventTime.Format(time.RFC3339),
		e.ProcessingTime.Format(time.RFC3339), e.Partition)
}

// ---------------------------------------------------------------------------
// Window types
// ---------------------------------------------------------------------------

// WindowType identifies the kind of windowing strategy.
type WindowType int

const (
	// WindowTumbling assigns each event to exactly one non-overlapping window.
	// Tumbling windows have fixed size and no overlap.
	// Example: every 5-minute bucket.
	WindowTumbling WindowType = iota

	// WindowSliding assigns each event to multiple overlapping windows.
	// Sliding windows have a fixed size and a slide interval.
	// Example: 10-minute windows sliding every 2 minutes.
	WindowSliding

	// WindowSession groups events that are close together in time.
	// A session window opens on the first event and closes after a gap
	// of inactivity exceeds the session timeout.
	WindowSession
)

func (w WindowType) String() string {
	switch w {
	case WindowTumbling:
		return "tumbling"
	case WindowSliding:
		return "sliding"
	case WindowSession:
		return "session"
	default:
		return "unknown"
	}
}

// ---------------------------------------------------------------------------
// Window definition
// ---------------------------------------------------------------------------

// Window defines the time range of a window.
type Window struct {
	Start time.Time // Inclusive start
	End   time.Time // Exclusive end
	Type  WindowType
}

// Contains checks if a timestamp falls within this window.
func (w Window) Contains(ts time.Time) bool {
	return !ts.Before(w.Start) && ts.Before(w.End)
}

// Duration returns the length of the window.
func (w Window) Duration() time.Duration {
	return w.End.Sub(w.Start)
}

// String returns a human-readable representation.
func (w Window) String() string {
	return fmt.Sprintf("Window{%s → %s, type=%s}",
		w.Start.Format(time.RFC3339), w.End.Format(time.RFC3339), w.Type)
}

// ---------------------------------------------------------------------------
// Window assigner: maps events to windows
// ---------------------------------------------------------------------------

// WindowAssigner defines how events are assigned to windows.
type WindowAssigner interface {
	// AssignWindows returns all windows that an event belongs to.
	AssignWindows(eventTime time.Time, now time.Time) []Window
	// WindowDuration returns the size of each window (for tumbling/sliding).
	WindowDuration() time.Duration
}

// TumblingWindowAssigner creates non-overlapping fixed-size windows.
type TumblingWindowAssigner struct {
	Size time.Duration
}

func (a *TumblingWindowAssigner) AssignWindows(eventTime time.Time, _ time.Time) []Window {
	// Align to the start of the tumbling window by truncating.
	epoch := eventTime.Unix()
	sizeSec := int64(a.Size.Seconds())
	startUnix := (epoch / sizeSec) * sizeSec
	start := time.Unix(startUnix, 0)
	return []Window{{
		Start: start,
		End:   start.Add(a.Size),
		Type:  WindowTumbling,
	}}
}

func (a *TumblingWindowAssigner) WindowDuration() time.Duration { return a.Size }

// SlidingWindowAssigner creates overlapping fixed-size windows.
type SlidingWindowAssigner struct {
	Size   time.Duration
	Slide  time.Duration
}

func (a *SlidingWindowAssigner) AssignWindows(eventTime time.Time, _ time.Time) []Window {
	epoch := eventTime.Unix()
	sizeSec := int64(a.Size.Seconds())
	slideSec := int64(a.Slide.Seconds())

	// Find the start of the window that contains eventTime.
	// We iterate backwards to find all windows that contain this event.
	var windows []Window
	// The earliest window start that could contain eventTime.
	earliestStart := ((epoch - sizeSec) / slideSec + 1) * slideSec
	for s := earliestStart; s <= epoch; s += slideSec {
		start := time.Unix(s, 0)
		windows = append(windows, Window{
			Start: start,
			End:   start.Add(a.Size),
			Type:  WindowSliding,
		})
	}
	return windows
}

func (a *SlidingWindowAssigner) WindowDuration() time.Duration { return a.Size }

// SessionWindowAssigner creates gap-based session windows.
type SessionWindowAssigner struct {
	Gap time.Duration
}

func (a *SessionWindowAssigner) AssignWindows(eventTime time.Time, now time.Time) []Window {
	// For simplicity, a session window is centered on the event
	// with the configured gap as half-width. In a real system,
	// sessions would be dynamically grown as events arrive.
	start := eventTime.Add(-a.Gap / 2)
	end := eventTime.Add(a.Gap / 2)
	return []Window{{
		Start: start,
		End:   end,
		Type:  WindowSession,
	}}
}

func (a *SessionWindowAssigner) WindowDuration() time.Duration { return a.Gap }

// ---------------------------------------------------------------------------
// Aggregation
// ---------------------------------------------------------------------------

// Aggregator computes a running aggregate over events in a window.
type Aggregator interface {
	// Add incorporates a new event into the accumulator.
	Add(event Event)
	// Result returns the current aggregate value.
	Result() interface{}
	// Copy returns a deep copy of the aggregator state.
	Copy() Aggregator
}

// SumAggregator computes the running sum of numeric payloads.
type SumAggregator struct {
	sum float64
}

func (a *SumAggregator) Add(event Event) {
	val := extractFloat(event.Payload)
	a.sum += val
}

func (a *SumAggregator) Result() interface{} { return a.sum }
func (a *SumAggregator) Copy() Aggregator     { return &SumAggregator{sum: a.sum} }

// CountAggregator counts the number of events.
type CountAggregator struct {
	count int64
}

func (a *CountAggregator) Add(event Event) { a.count++ }
func (a *CountAggregator) Result() interface{} { return a.count }
func (a *CountAggregator) Copy() Aggregator  { return &CountAggregator{count: a.count} }

// AvgAggregator computes the running average.
type AvgAggregator struct {
	sum   float64
	count int64
}

func (a *AvgAggregator) Add(event Event) {
	a.sum += extractFloat(event.Payload)
	a.count++
}

func (a *AvgAggregator) Result() interface{} {
	if a.count == 0 {
		return 0.0
	}
	return a.sum / float64(a.count)
}

func (a *AvgAggregator) Copy() Aggregator {
	return &AvgAggregator{sum: a.sum, count: a.count}
}

// MinAggregator tracks the minimum value.
type MinAggregator struct {
	min  float64
	init bool
}

func (a *MinAggregator) Add(event Event) {
	val := extractFloat(event.Payload)
	if !a.init || val < a.min {
		a.min = val
		a.init = true
	}
}

func (a *MinAggregator) Result() interface{} {
	if !a.init {
		return 0.0
	}
	return a.min
}

func (a *MinAggregator) Copy() Aggregator {
	return &MinAggregator{min: a.min, init: a.init}
}

// MaxAggregator tracks the maximum value.
type MaxAggregator struct {
	max  float64
	init bool
}

func (a *MaxAggregator) Add(event Event) {
	val := extractFloat(event.Payload)
	if !a.init || val > a.max {
		a.max = val
		a.init = true
	}
}

func (a *MaxAggregator) Result() interface{} {
	if !a.init {
		return 0.0
	}
	return a.max
}

func (a *MaxAggregator) Copy() Aggregator {
	return &MaxAggregator{max: a.max, init: a.init}
}

// extractFloat converts an interface{} payload to a float64 value.
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
	case uint:
		return float64(v)
	case uint64:
		return float64(v)
	case string:
		// Attempt to parse as number
		for _, c := range v {
			if c >= '0' && c <= '9' {
				var n float64
				_, err := fmt.Sscanf(v, "%f", &n)
				if err == nil {
					return n
				}
				break
			}
		}
		return 0
	default:
		return 0
	}
}

// ---------------------------------------------------------------------------
// Trigger
// ---------------------------------------------------------------------------

// TriggerState holds the state of a trigger for a specific window.
type TriggerState struct {
	Fired       bool
	Count       int64
	LastTrigger time.Time
}

// Trigger determines when a window's contents should be evaluated and output.
type Trigger interface {
	// OnEvent is called when an event is added to a window.
	OnEvent(state *TriggerState, event Event, window Window) bool
	// OnTimer is called when a timer fires (for processing-time triggers).
	OnTimer(state *TriggerState, window Window) bool
	// Clear resets the trigger state (e.g., when a window is discarded).
	Clear(state *TriggerState, window Window)
	// String returns the trigger's name for logging.
	String() string
}

// CountTrigger fires after a specified number of elements in the window.
type CountTrigger struct {
	Count int64
}

func (t *CountTrigger) OnEvent(state *TriggerState, event Event, window Window) bool {
	state.Count++
	if state.Count >= t.Count {
		state.Fired = true
		return true
	}
	return false
}

func (t *CountTrigger) OnTimer(state *TriggerState, window Window) bool { return false }
func (t *CountTrigger) Clear(state *TriggerState, window Window)        { state.Count = 0; state.Fired = false }
func (t *CountTrigger) String() string                                  { return fmt.Sprintf("count(%d)", t.Count) }

// WatermarkTrigger fires when the watermark passes the window's end time.
// This is the most common trigger for event-time windowing.
type WatermarkTrigger struct{}

func (t *WatermarkTrigger) OnEvent(state *TriggerState, event Event, window Window) bool {
	return false // Triggered by watermark, not by individual events
}

func (t *WatermarkTrigger) OnTimer(state *TriggerState, window Window) bool {
	state.Fired = true
	return true
}

func (t *WatermarkTrigger) Clear(state *TriggerState, window Window) {
	state.Fired = false
}

func (t *WatermarkTrigger) String() string { return "watermark" }

// ---------------------------------------------------------------------------
// Watermark
// ---------------------------------------------------------------------------

// Watermark tracks the progress of event time in the stream.
// It represents the guarantee that no events with event-time before
// the watermark will arrive. Watermarks are monotonically increasing.
type Watermark struct {
	// WatermarkTime is the current watermark value.
	// All events with event-time < WatermarkTime are considered "late".
	WatermarkTime time.Time
	// MaxOutOfOrderness is the maximum expected out-of-order delay.
	// Watermarks are set to max(event_time_seen - maxOutOfOrderness).
	MaxOutOfOrderness time.Duration
	// Lateness allows events up to this delay past the watermark.
	Lateness time.Duration
}

// NewWatermark creates a new watermark tracker.
func NewWatermark(maxOutOfOrderness time.Duration) *Watermark {
	return &Watermark{
		WatermarkTime:       time.Unix(0, 0), // Initially epoch zero
		MaxOutOfOrderness:   maxOutOfOrderness,
		Lateness:            5 * time.Minute, // Allow 5 minutes of late data
	}
}

// Update advances the watermark if the event time exceeds the current watermark
// minus the allowed out-of-orderness.
func (w *Watermark) Update(eventTime time.Time) {
	minWatermark := eventTime.Add(-w.MaxOutOfOrderness)
	if minWatermark.After(w.WatermarkTime) {
		w.WatermarkTime = minWatermark
	}
}

// IsLate checks if an event is late (its event time is before the watermark).
func (w *Watermark) IsLate(eventTime time.Time) bool {
	return eventTime.Before(w.WatermarkTime)
}

// IsTooLate checks if an event is too late (past the watermark + lateness).
// These events would normally be discarded.
func (w *Watermark) IsTooLate(eventTime time.Time) bool {
	return eventTime.Before(w.WatermarkTime.Add(-w.Lateness))
}

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

// StateManager manages per-window state for continuous processing.
// It stores aggregators keyed by (window, partition).
type StateManager struct {
	// state maps a window-key string to the aggregator state.
	state map[string]Aggregator
}

// NewStateManager creates a new state manager.
func NewStateManager() *StateManager {
	return &StateManager{
		state: make(map[string]Aggregator),
	}
}

// Key generates a unique key for a (window, partition) pair.
func Key(window Window, partition int64) string {
	return fmt.Sprintf("%d:%d:%d:%d:%d",
		window.Start.Unix(), window.End.Unix(),
		window.Type, partition, window.Start.Nanosecond())
}

// Get retrieves the aggregator for a window/partition, creating one if it doesn't exist.
func (s *StateManager) Get(window Window, partition int64, factory func() Aggregator) Aggregator {
	k := Key(window, partition)
	if agg, ok := s.state[k]; ok {
		return agg
	}
	agg := factory()
	s.state[k] = agg
	return agg
}

// GetResult returns the aggregate result for a window/partition.
func (s *StateManager) GetResult(window Window, partition int64) (interface{}, bool) {
	k := Key(window, partition)
	if agg, ok := s.state[k]; ok {
		return agg.Result(), true
	}
	return nil, false
}

// ClearWindow removes all state for a given window.
func (s *StateManager) ClearWindow(window Window) {
	for k := range s.state {
		if k == Key(window, 0) || isWindowKey(k, window) {
			delete(s.state, k)
		}
	}
}

// ClearAll removes all state.
func (s *StateManager) ClearAll() {
	s.state = make(map[string]Aggregator)
}

// Size returns the number of active state entries.
func (s *StateManager) Size() int {
	return len(s.state)
}

// isWindowKey checks if a state key belongs to a given window.
func isWindowKey(key string, window Window) bool {
	// Simple check: compare the start time portion of the key.
	var startUnix int64
	fmt.Sscanf(key, "%d", &startUnix)
	return startUnix == window.Start.Unix()
}

// ---------------------------------------------------------------------------
// Source and Sink interfaces
// ---------------------------------------------------------------------------

// Source reads events from an input stream.
type Source interface {
	// Read returns the next event, or (nil, false) when the stream ends.
	Read() (Event, bool)
	// Name returns the source's identifier.
	Name() string
}

// Sink writes aggregated results to an output destination.
type Sink interface {
	// Write sends a result to the output destination.
	Write(window Window, partition int64, result interface{}) error
	// Name returns the sink's identifier.
	Name() string
}

// ---------------------------------------------------------------------------
// ConsoleSink: writes results to stdout for demonstration.
// ---------------------------------------------------------------------------

// ConsoleSink prints results to standard output.
type ConsoleSink struct{}

func (s *ConsoleSink) Write(window Window, partition int64, result interface{}) error {
	fmt.Printf("[Sink] Window=%s Partition=%d Result=%v\n",
		window.String(), partition, result)
	return nil
}

func (s *ConsoleSink) Name() string { return "console" }

// ---------------------------------------------------------------------------
// SliceSource: reads events from a pre-defined slice.
// ---------------------------------------------------------------------------

// SliceSource reads events from an in-memory slice.
type SliceSource struct {
	Events []Event
	Index  int
	name   string
}

// NewSliceSource creates a source from a slice of events.
func NewSliceSource(events []Event, name string) *SliceSource {
	return &SliceSource{Events: events, name: name}
}

func (s *SliceSource) Read() (Event, bool) {
	if s.Index >= len(s.Events) {
		return Event{}, false
	}
	e := s.Events[s.Index]
	s.Index++
	return e, true
}

func (s *SliceSource) Name() string { return s.name }

// ---------------------------------------------------------------------------
// WindowRunner: the main processing engine.
// ---------------------------------------------------------------------------

// WindowRunner orchestrates the core stream processing loop.
// It reads events from a Source, assigns them to windows, maintains state,
// and triggers output when conditions are met.
type WindowRunner struct {
	Source         Source
	Sink           Sink
	WindowAssigner WindowAssigner
	Aggregator      func() Aggregator // Factory function for new aggregators
	Trigger        Trigger
	Watermark      *Watermark
	State          *StateManager
	// Late event handler
	LateHandler func(Event)
}

// NewWindowRunner creates a new WindowRunner.
func NewWindowRunner(source Source, sink Sink, assigner WindowAssigner, aggregator func() Aggregator, trigger Trigger) *WindowRunner {
	return &WindowRunner{
		Source:         source,
		Sink:           sink,
		WindowAssigner: assigner,
		Aggregator:     aggregator,
		Trigger:        trigger,
		Watermark:      NewWatermark(1 * time.Minute),
		State:          NewStateManager(),
	}
}

// Process runs the stream processing loop.
// It reads events from the source, updates the watermark,
// assigns events to windows, accumulates state, and triggers output.
func (r *WindowRunner) Process() {
	// Track per-window trigger states.
	triggerStates := make(map[string]*TriggerState)

	for {
		event, ok := r.Source.Read()
		if !ok {
			break
		}

		// Update watermark based on event time.
		r.Watermark.Update(event.EventTime)

		// Check if event is too late.
		if r.Watermark.IsTooLate(event.EventTime) {
			if r.LateHandler != nil {
				r.LateHandler(event)
			}
			continue
		}

		// Assign event to windows.
		windows := r.WindowAssigner.AssignWindows(event.EventTime, event.ProcessingTime)
		for _, win := range windows {
			r.processEvent(event, win, triggerStates)
		}

		// Check watermarks for window completion.
		r.checkWatermarks(triggerStates)
	}

	// Output remaining window results.
	r.flushRemaining(triggerStates)
}

// processEvent adds an event to all relevant windows.
func (r *WindowRunner) processEvent(event Event, window Window, triggerStates map[string]*TriggerState) {
	// Get or create aggregator for this window/partition.
	agg := r.State.Get(window, event.Partition, r.Aggregator)
	agg.Add(event)

	// Get or create trigger state.
	wk := windowKey(window, event.Partition)
	ts := triggerStates[wk]
	if ts == nil {
		ts = &TriggerState{}
		triggerStates[wk] = ts
	}

	// Check if trigger should fire.
	if r.Trigger.OnEvent(ts, event, window) {
		r.emitResult(window, event.Partition, triggerStates)
	}
}

// checkWatermarks checks if any windows should be triggered by watermark progress.
func (r *WindowRunner) checkWatermarks(triggerStates map[string]*TriggerState) {
	for wk, ts := range triggerStates {
		if ts.Fired {
			continue
		}
		// Parse window from key to check watermark.
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
		// If watermark passes window end, trigger.
		if !r.Watermark.WatermarkTime.Before(win.End) {
			ts.Fired = true
			r.emitResult(win, 0, triggerStates)
		}
	}
}

// emitResult outputs the aggregate result for a window.
func (r *WindowRunner) emitResult(window Window, partition int64, triggerStates map[string]*TriggerState) {
	wk := windowKey(window, partition)
	ts := triggerStates[wk]
	if ts == nil {
		ts = &TriggerState{}
		triggerStates[wk] = ts
	}

	result, ok := r.State.GetResult(window, partition)
	if !ok {
		return
	}

	// Write result via sink.
	r.Sink.Write(window, partition, result)

	// Clear trigger state after emitting.
	ts.Fired = false
	ts.Count = 0

	// Clear late events from trigger state.
	for k, state := range triggerStates {
		if state.Count > 0 {
			// Keep state for events still in the window.
			_ = k
			_ = state
		}
	}
}

// flushRemaining outputs results for any remaining open windows.
func (r *WindowRunner) flushRemaining(triggerStates map[string]*TriggerState) {
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
		result, _ := r.State.GetResult(win, 0)
		r.Sink.Write(win, 0, result)
		ts.Fired = true
	}
}

// windowKey generates a unique key for a window/partition combination.
func windowKey(window Window, partition int64) string {
	return fmt.Sprintf("%d:%d:%d:%d",
		window.Start.Unix(), window.End.Unix(),
		window.Type, partition)
}

// ---------------------------------------------------------------------------
// Late event handling
// ---------------------------------------------------------------------------

// LateEventPolicy defines how to handle late-arriving events.
type LateEventPolicy int

const (
	// LateDiscard drops late events entirely.
	LateDiscard LateEventPolicy = iota
	// LateOutput outputs late events to a separate late sink.
	LateOutput
	// LateSideOutput sends late events to a side output stream.
	LateSideOutput
	// LateUpdate updates window state with late events (may produce duplicate results).
	LateUpdate
)

// LateEventResult holds information about a late event.
type LateEventResult struct {
	Event    Event
	Window   Window
	Policy   LateEventPolicy
	Handled  bool
}

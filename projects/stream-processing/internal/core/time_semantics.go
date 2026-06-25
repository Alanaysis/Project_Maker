package core

import (
	"time"
)

// TimeCharacteristic determines how time progresses in the stream.
type TimeCharacteristic int

const (
	// ProcessingTime uses the system clock of the machine processing the event.
	// Simplest mode, but results depend on processing speed.
	ProcessingTime TimeCharacteristic = iota

	// EventTime uses the timestamp embedded in each event.
	// Results are deterministic and handle out-of-order events.
	EventTime

	// IngestionTime uses the time when the event enters the system.
	// A middle ground between processing and event time.
	IngestionTime
)

func (tc TimeCharacteristic) String() string {
	switch tc {
	case ProcessingTime:
		return "ProcessingTime"
	case EventTime:
		return "EventTime"
	case IngestionTime:
		return "IngestionTime"
	default:
		return "Unknown"
	}
}

// TimeContext holds time-related configuration for a stream job.
type TimeContext struct {
	Characteristic     TimeCharacteristic
	MaxOutOfOrderness time.Duration
	WatermarkInterval time.Duration
}

// NewTimeContext creates a time context with the given characteristic.
func NewTimeContext(tc TimeCharacteristic) *TimeContext {
	return &TimeContext{
		Characteristic:     tc,
		MaxOutOfOrderness: 5 * time.Second,  // default
		WatermarkInterval: 200 * time.Millisecond, // default
	}
}

// WithMaxOutOfOrderness sets the max out-of-orderness duration.
func (tc *TimeContext) WithMaxOutOfOrderness(d time.Duration) *TimeContext {
	tc.MaxOutOfOrderness = d
	return tc
}

// WithWatermarkInterval sets the watermark emission interval.
func (tc *TimeContext) WithWatermarkInterval(d time.Duration) *TimeContext {
	tc.WatermarkInterval = d
	return tc
}

// CurrentTime returns the current time based on the characteristic.
func (tc *TimeContext) CurrentTime(event Event) time.Time {
	switch tc.Characteristic {
	case ProcessingTime:
		return time.Now()
	case EventTime:
		return event.Timestamp
	case IngestionTime:
		return time.Now() // Same as processing time at ingestion
	default:
		return time.Now()
	}
}

// LateEvent represents an event that arrived after its window closed.
type LateEvent struct {
	Event     Event
	Window    Window
	Watermark time.Time
	Lateness  time.Duration
}

// LateEventPolicy defines how to handle late-arriving events.
type LateEventPolicy int

const (
	// DropLateEvents discards events that arrive after the watermark.
	DropLateEvents LateEventPolicy = iota

	// AllowLateEvents processes late events within a allowed lateness window.
	AllowLateEvents

	// SideOutputLateEvents sends late events to a side output.
	SideOutputLateEvents
)

// LateEventHandler processes late events based on a policy.
type LateEventHandler struct {
	policy         LateEventPolicy
	allowedLateness time.Duration
	lateEvents     []LateEvent
}

// NewLateEventHandler creates a handler with the given policy.
func NewLateEventHandler(policy LateEventPolicy, allowedLateness time.Duration) *LateEventHandler {
	return &LateEventHandler{
		policy:          policy,
		allowedLateness: allowedLateness,
		lateEvents:      make([]LateEvent, 0),
	}
}

// Handle processes a potentially late event.
// Returns true if the event should be processed normally.
func (h *LateEventHandler) Handle(event Event, window Window, watermark time.Time) bool {
	lateness := watermark.Sub(event.Timestamp)

	if lateness <= 0 {
		// Not late
		return true
	}

	lateEvent := LateEvent{
		Event:     event,
		Window:    window,
		Watermark: watermark,
		Lateness:  lateness,
	}

	switch h.policy {
	case DropLateEvents:
		h.lateEvents = append(h.lateEvents, lateEvent)
		return false

	case AllowLateEvents:
		if lateness <= h.allowedLateness {
			return true
		}
		h.lateEvents = append(h.lateEvents, lateEvent)
		return false

	case SideOutputLateEvents:
		h.lateEvents = append(h.lateEvents, lateEvent)
		return false

	default:
		return false
	}
}

// GetLateEvents returns all events that were marked as late.
func (h *LateEventHandler) GetLateEvents() []LateEvent {
	return h.lateEvents
}

// LateEventCount returns the number of late events.
func (h *LateEventHandler) LateEventCount() int {
	return len(h.lateEvents)
}

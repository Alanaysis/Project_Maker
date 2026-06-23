package core

import (
	"time"
)

// Event represents a single data element in the stream.
// Every event carries a key, a value, and a timestamp that
// determines which window it belongs to.
type Event struct {
	Key       string
	Value     interface{}
	Timestamp time.Time
}

// NewEvent creates a new event with the current time.
func NewEvent(key string, value interface{}) Event {
	return Event{
		Key:       key,
		Value:     value,
		Timestamp: time.Now(),
	}
}

// NewEventWithTime creates a new event with a specific timestamp.
func NewEventWithTime(key string, value interface{}, ts time.Time) Event {
	return Event{
		Key:       key,
		Value:     value,
		Timestamp: ts,
	}
}

// Window represents a time window with a start and end time.
type Window struct {
	Start time.Time
	End   time.Time
}

// Contains checks if a timestamp falls within this window.
func (w Window) Contains(ts time.Time) bool {
	return !ts.Before(w.Start) && ts.Before(w.End)
}

// Duration returns the window duration.
func (w Window) Duration() time.Duration {
	return w.End.Sub(w.Start)
}

// Package tracker provides message state tracking for exactly-once processing.
//
// The Tracker maintains a complete audit trail of message lifecycle events.
// It records state transitions, timing information, and processing results.
// This is essential for:
// - Debugging processing issues
// - Auditing message handling
// - Implementing dead-letter queues
// - Monitoring system health
package tracker

import (
	"fmt"
	"sync"
	"time"

	"github.com/anthropic/exactly-once/internal/message"
)

// Event represents a state transition event in the message lifecycle.
type Event struct {
	// Timestamp is when the event occurred.
	Timestamp time.Time

	// FromState is the previous state.
	FromState message.State

	// ToState is the new state.
	ToState message.State

	// Message is additional information about the event.
	Message string
}

// Record is the complete tracking record for a message.
type Record struct {
	// MessageID is the unique message identifier.
	MessageID string

	// IdempotencyKey is the deduplication key.
	IdempotencyKey string

	// CurrentState is the current processing state.
	CurrentState message.State

	// Events is the ordered list of state transition events.
	Events []Event

	// FirstSeen is when the message was first tracked.
	FirstSeen time.Time

	// LastUpdated is when the record was last modified.
	LastUpdated time.Time

	// Result is the processing result (if completed).
	Result []byte

	// Error is the error message (if failed).
	Error string

	// RetryCount is the number of retries attempted.
	RetryCount int
}

// Tracker maintains message state records.
type Tracker struct {
	mu      sync.RWMutex
	records map[string]*Record
	stats   Stats
}

// Stats tracks overall tracking statistics.
type Stats struct {
	TotalTracked  int64
	Completed     int64
	Failed        int64
	Duplicates    int64
	InProgress    int64
}

// New creates a new Tracker.
func New() *Tracker {
	return &Tracker{
		records: make(map[string]*Record),
	}
}

// Track starts tracking a message. If the message is already tracked,
// this is a no-op.
func (t *Tracker) Track(msg *message.Message) {
	t.mu.Lock()
	defer t.mu.Unlock()

	if _, exists := t.records[msg.ID]; exists {
		return
	}

	record := &Record{
		MessageID:      msg.ID,
		IdempotencyKey: msg.IdempotencyKey,
		CurrentState:   msg.State,
		FirstSeen:      time.Now(),
		LastUpdated:    time.Now(),
		Events: []Event{
			{
				Timestamp: time.Now(),
				ToState:   msg.State,
				Message:   "message registered",
			},
		},
	}

	t.records[msg.ID] = record
	t.stats.TotalTracked++
	t.updateStateStats(msg.State, 1)
}

// Update records a state change for a tracked message.
func (t *Tracker) Update(msg *message.Message) {
	t.mu.Lock()
	defer t.mu.Unlock()

	record, exists := t.records[msg.ID]
	if !exists {
		// Auto-track if not already tracked
		t.mu.Unlock()
		t.Track(msg)
		t.mu.Lock()
		record = t.records[msg.ID]
	}

	oldState := record.CurrentState
	if oldState == msg.State {
		return // No state change
	}

	// Record the event
	event := Event{
		Timestamp:  time.Now(),
		FromState:  oldState,
		ToState:    msg.State,
		Message:    fmt.Sprintf("%s -> %s", oldState, msg.State),
	}
	record.Events = append(record.Events, event)

	// Update stats: decrement old state, increment new state
	t.updateStateStats(oldState, -1)
	t.updateStateStats(msg.State, 1)

	// Update record
	record.CurrentState = msg.State
	record.LastUpdated = time.Now()
	record.RetryCount = msg.RetryCount
	record.Result = msg.Result
	record.Error = msg.Error
}

// GetRecord returns the tracking record for a message, or nil if not found.
func (t *Tracker) GetRecord(messageID string) *Record {
	t.mu.RLock()
	defer t.mu.RUnlock()

	record, exists := t.records[messageID]
	if !exists {
		return nil
	}

	// Return a copy
	copy := *record
	copy.Events = make([]Event, len(record.Events))
	for i, e := range record.Events {
		copy.Events[i] = e
	}
	return &copy
}

// GetEvents returns all events for a message.
func (t *Tracker) GetEvents(messageID string) []Event {
	t.mu.RLock()
	defer t.mu.RUnlock()

	record, exists := t.records[messageID]
	if !exists {
		return nil
	}

	events := make([]Event, len(record.Events))
	copy(events, record.Events)
	return events
}

// GetByState returns all message IDs in the given state.
func (t *Tracker) GetByState(state message.State) []string {
	t.mu.RLock()
	defer t.mu.RUnlock()

	var ids []string
	for id, record := range t.records {
		if record.CurrentState == state {
			ids = append(ids, id)
		}
	}
	return ids
}

// GetFailedMessages returns all message IDs that are in the failed state.
func (t *Tracker) GetFailedMessages() []string {
	return t.GetByState(message.StateFailed)
}

// GetCompletedMessages returns all message IDs that completed successfully.
func (t *Tracker) GetCompletedMessages() []string {
	return t.GetByState(message.StateCompleted)
}

// Size returns the number of tracked messages.
func (t *Tracker) Size() int {
	t.mu.RLock()
	defer t.mu.RUnlock()
	return len(t.records)
}

// StatsSnapshot returns a copy of the current statistics.
func (t *Tracker) StatsSnapshot() Stats {
	t.mu.RLock()
	defer t.mu.RUnlock()
	return t.stats
}

// Clear removes all tracking records and resets statistics.
func (t *Tracker) Clear() {
	t.mu.Lock()
	defer t.mu.Unlock()

	t.records = make(map[string]*Record)
	t.stats = Stats{}
}

// Cleanup removes records older than the given duration.
func (t *Tracker) Cleanup(maxAge time.Duration) int {
	t.mu.Lock()
	defer t.mu.Unlock()

	removed := 0
	now := time.Now()
	for id, record := range t.records {
		if now.Sub(record.LastUpdated) > maxAge {
			t.updateStateStats(record.CurrentState, -1)
			delete(t.records, id)
			removed++
		}
	}
	return removed
}

func (t *Tracker) updateStateStats(state message.State, delta int64) {
	switch state {
	case message.StatePending, message.StateProcessing:
		t.stats.InProgress += delta
	case message.StateCompleted:
		t.stats.Completed += delta
	case message.StateFailed:
		t.stats.Failed += delta
	case message.StateDuplicate:
		t.stats.Duplicates += delta
	}
}

package stream

import (
	"fmt"
	"time"
)

// ---------------------------------------------------------------------------
// Session Window Manager
// ---------------------------------------------------------------------------

// SessionWindow tracks an active session window.
type SessionWindow struct {
	Start    time.Time
	End      time.Time
	Events   []Event
	Aggreg   Aggregator
	Active   bool
}

// NewSessionWindow creates a new session window.
func NewSessionWindow(event Event) *SessionWindow {
	agg := &SumAggregator{}
	agg.Add(event)
	return &SessionWindow{
		Start:  event.EventTime,
		End:    event.EventTime,
		Events: []Event{event},
		Aggreg: agg,
		Active: true,
	}
}

// AddEvent adds an event to the session, extending it if needed.
func (s *SessionWindow) AddEvent(event Event, gap time.Duration) bool {
	if !s.Active {
		return false
	}

	// Check if event falls within the session gap.
	if !event.EventTime.Before(s.End.Add(gap)) {
		// Event is outside the gap - session is closed.
		s.Active = false
		return false
	}

	// Add event to session.
	s.Events = append(s.Events, event)
	s.Aggreg.Add(event)

	// Extend the session end.
	if event.EventTime.After(s.End) {
		s.End = event.EventTime
	}

	return true
}

// Close marks the session as inactive.
func (s *SessionWindow) Close() {
	s.Active = false
}

// Result returns the aggregate result.
func (s *SessionWindow) Result() interface{} {
	return s.Aggreg.Result()
}

// ---------------------------------------------------------------------------
// Session Window Manager: manages multiple session windows.
// ---------------------------------------------------------------------------

// SessionManager manages a set of active session windows.
type SessionManager struct {
	sessions []*SessionWindow
	gap      time.Duration
	nextID   int64
}

// NewSessionManager creates a new session window manager.
func NewSessionManager(gap time.Duration) *SessionManager {
	return &SessionManager{
		sessions: make([]*SessionWindow, 0),
		gap:      gap,
	}
}

// ProcessEvent processes a single event, assigning it to a session window.
// Returns the session window the event was assigned to (if any).
func (m *SessionManager) ProcessEvent(event Event) *SessionWindow {
	// Try to find an existing session to add to.
	for _, session := range m.sessions {
		if session.AddEvent(event, m.gap) {
			return session
		}
	}

	// No existing session - create a new one.
	newSession := NewSessionWindow(event)
	newSession.Start = event.EventTime.Add(-m.gap / 2)
	newSession.End = event.EventTime.Add(m.gap / 2)
	m.sessions = append(m.sessions, newSession)
	return newSession
}

// CloseExpired closes sessions that have been inactive.
func (m *SessionManager) CloseExpired(now time.Time) {
	active := make([]*SessionWindow, 0)
	for _, session := range m.sessions {
		if session.Active {
			if now.After(session.End.Add(m.gap)) {
				fmt.Printf("[Session] Closed expired session: %s → %s (events=%d)\n",
					session.Start.Format(time.RFC3339),
					session.End.Format(time.RFC3339),
					len(session.Events))
			} else {
				active = append(active, session)
			}
		} else {
			active = append(active, session)
		}
	}
	m.sessions = active
}

// ActiveCount returns the number of active sessions.
func (m *SessionManager) ActiveCount() int {
	count := 0
	for _, s := range m.sessions {
		if s.Active {
			count++
		}
	}
	return count
}

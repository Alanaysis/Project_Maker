package window

import (
	"sort"
	"sync"
	"time"

	"github.com/learning/stream-processing/internal/core"
)

// SessionWindow groups events by activity gaps.
// A session window closes when no new events arrive within the
// specified gap duration. Unlike tumbling/sliding windows, session
// windows have dynamic boundaries that depend on the data.
//
// Example (gap=5s):
//   Events at: 0s, 2s, 3s, 10s, 12s
//   Session 1: [0s, 3s]  (gap of 7s > 5s triggers close)
//   Session 2: [10s, 12s]
type SessionWindow struct {
	gap    time.Duration
	mu     sync.Mutex
	sessions map[string]*sessionState // per-key sessions
}

type sessionState struct {
	windows []sessionEntry
}

type sessionEntry struct {
	start time.Time
	end   time.Time
}

// NewSessionWindow creates a session window with the given gap duration.
func NewSessionWindow(gap time.Duration) *SessionWindow {
	return &SessionWindow{
		gap:      gap,
		sessions: make(map[string]*sessionState),
	}
}

// ProcessEvent processes an event and returns any windows that were closed.
// A window closes when the new event's timestamp exceeds the gap from the
// last event in the session.
func (sw *SessionWindow) ProcessEvent(event core.Event) []core.Window {
	sw.mu.Lock()
	defer sw.mu.Unlock()

	key := event.Key
	ts := event.Timestamp

	state, exists := sw.sessions[key]
	if !exists {
		state = &sessionState{}
		sw.sessions[key] = state
	}

	// Check if we need to close existing windows
	var closedWindows []core.Window
	newWindows := make([]sessionEntry, 0, len(state.windows)+1)

	for _, w := range state.windows {
		if ts.Sub(w.end) > sw.gap {
			// Gap exceeded, close this window
			closedWindows = append(closedWindows, core.Window{
				Start: w.start,
				End:   w.end.Add(sw.gap), // Window end includes the gap
			})
		} else {
			newWindows = append(newWindows, w)
		}
	}

	// Merge with existing window or create new one
	if len(newWindows) > 0 {
		// Extend the last window
		last := &newWindows[len(newWindows)-1]
		if ts.After(last.end) {
			last.end = ts
		}
	} else {
		// Create new session
		newWindows = append(newWindows, sessionEntry{
			start: ts,
			end:   ts,
		})
	}

	state.windows = newWindows
	return closedWindows
}

// ForceClose closes all windows for the given key and returns them.
func (sw *SessionWindow) ForceClose(key string) []core.Window {
	sw.mu.Lock()
	defer sw.mu.Unlock()

	state, exists := sw.sessions[key]
	if !exists {
		return nil
	}

	var windows []core.Window
	for _, w := range state.windows {
		windows = append(windows, core.Window{
			Start: w.start,
			End:   w.end.Add(sw.gap),
		})
	}

	delete(sw.sessions, key)
	return windows
}

// ForceCloseAll closes all windows for all keys.
func (sw *SessionWindow) ForceCloseAll() []core.Window {
	sw.mu.Lock()
	defer sw.mu.Unlock()

	var allWindows []core.Window
	for key, state := range sw.sessions {
		for _, w := range state.windows {
			allWindows = append(allWindows, core.Window{
				Start: w.start,
				End:   w.end.Add(sw.gap),
			})
		}
		delete(sw.sessions, key)
	}

	// Sort by start time
	sort.Slice(allWindows, func(i, j int) bool {
		return allWindows[i].Start.Before(allWindows[j].Start)
	})

	return allWindows
}

// ActiveSessions returns the number of active session keys.
func (sw *SessionWindow) ActiveSessions() int {
	sw.mu.Lock()
	defer sw.mu.Unlock()
	return len(sw.sessions)
}

// Gap returns the session gap duration.
func (sw *SessionWindow) Gap() time.Duration {
	return sw.gap
}

// SessionWindowOperator is an operator that uses session windows.
// It buffers events per session and emits aggregated results when sessions close.
type SessionWindowOperator struct {
	sessions   *SessionWindow
	reduceFunc ReduceFunc
	buffers    map[string][]core.Event
	mu         sync.Mutex
}

// ReduceFunc combines two values into one.
type ReduceFunc func(a, b interface{}) interface{}

// NewSessionWindowOperator creates a session window operator.
func NewSessionWindowOperator(gap time.Duration, fn ReduceFunc) *SessionWindowOperator {
	return &SessionWindowOperator{
		sessions:   NewSessionWindow(gap),
		reduceFunc: fn,
		buffers:    make(map[string][]core.Event),
	}
}

// Process handles an event, buffering it and closing sessions as needed.
func (op *SessionWindowOperator) Process(event core.Event, out *core.Stream) {
	op.mu.Lock()
	defer op.mu.Unlock()

	// Buffer the event
	op.buffers[event.Key] = append(op.buffers[event.Key], event)

	// Process through session window
	closedWindows := op.sessions.ProcessEvent(event)

	// Emit results for closed windows
	for _, w := range closedWindows {
		op.emitWindowResult(event.Key, w, out)
	}
}

// Flush closes all remaining sessions and emits their results.
func (op *SessionWindowOperator) Flush(out *core.Stream) {
	op.mu.Lock()
	defer op.mu.Unlock()

	// Close all remaining sessions
	op.sessions.ForceCloseAll()

	// Emit all buffered events directly
	for key, events := range op.buffers {
		if len(events) > 0 {
			result := op.reduceEvents(events)
			if result != nil {
				out.Emit(core.NewEvent(key, result))
			}
		}
	}
	op.buffers = make(map[string][]core.Event)
}

func (op *SessionWindowOperator) emitWindowResult(key string, w core.Window, out *core.Stream) {
	events := op.buffers[key]
	if len(events) == 0 {
		return
	}

	// Filter events within this window
	var windowEvents []core.Event
	var remaining []core.Event
	for _, e := range events {
		if !e.Timestamp.Before(w.Start) && e.Timestamp.Before(w.End) {
			windowEvents = append(windowEvents, e)
		} else {
			remaining = append(remaining, e)
		}
	}
	op.buffers[key] = remaining

	if len(windowEvents) > 0 {
		result := op.reduceEvents(windowEvents)
		if result != nil {
			out.Emit(core.NewEventWithTime(key, result, w.End))
		}
	}
}

func (op *SessionWindowOperator) reduceEvents(events []core.Event) interface{} {
	if len(events) == 0 {
		return nil
	}

	acc := events[0].Value
	for _, e := range events[1:] {
		acc = op.reduceFunc(acc, e.Value)
	}
	return acc
}

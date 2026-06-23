package state

import (
	"sync"
	"time"

	"github.com/learning/stream-processing/internal/core"
)

// WindowState manages state that is scoped to time windows.
// It automatically cleans up expired window states.
type WindowState struct {
	mu        sync.Mutex
	windows   map[core.Window]*StateStore
	maxAge    time.Duration
}

// NewWindowState creates a new window state manager.
// maxAge controls how long window states are kept after the window closes.
func NewWindowState(maxAge time.Duration) *WindowState {
	return &WindowState{
		windows: make(map[core.Window]*StateStore),
		maxAge:  maxAge,
	}
}

// GetState returns the state store for a specific window.
// Creates a new store if the window doesn't exist yet.
func (ws *WindowState) GetState(w core.Window) *StateStore {
	ws.mu.Lock()
	defer ws.mu.Unlock()

	if store, ok := ws.windows[w]; ok {
		return store
	}

	store := NewStateStore()
	ws.windows[w] = store
	return store
}

// Expire removes window states that have been closed for longer than maxAge.
func (ws *WindowState) Expire(now time.Time) int {
	ws.mu.Lock()
	defer ws.mu.Unlock()

	expired := 0
	for w := range ws.windows {
		if now.Sub(w.End) > ws.maxAge {
			delete(ws.windows, w)
			expired++
		}
	}
	return expired
}

// ActiveWindows returns all windows that currently have state.
func (ws *WindowState) ActiveWindows() []core.Window {
	ws.mu.Lock()
	defer ws.mu.Unlock()

	windows := make([]core.Window, 0, len(ws.windows))
	for w := range ws.windows {
		windows = append(windows, w)
	}
	return windows
}

// Clear removes all window states.
func (ws *WindowState) Clear() {
	ws.mu.Lock()
	defer ws.mu.Unlock()
	ws.windows = make(map[core.Window]*StateStore)
}

// Count returns the number of active window states.
func (ws *WindowState) Count() int {
	ws.mu.Lock()
	defer ws.mu.Unlock()
	return len(ws.windows)
}

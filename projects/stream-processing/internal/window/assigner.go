package window

import (
	"time"

	"github.com/learning/stream-processing/internal/core"
)

// WindowAssigner determines which window(s) a timestamp belongs to.
type WindowAssigner struct {
	windowSize time.Duration
	slide      time.Duration
}

// Assign returns a single window for the given timestamp.
// Used by tumbling windows (where slide == size).
func (wa *WindowAssigner) Assign(ts time.Time) core.Window {
	start := wa.alignTimestamp(ts)
	return core.Window{
		Start: start,
		End:   start.Add(wa.windowSize),
	}
}

// AssignMultiple returns all windows that contain the given timestamp.
// Used by sliding windows (where slide < size).
func (wa *WindowAssigner) AssignMultiple(ts time.Time) []core.Window {
	var windows []core.Window

	// Find the latest window end that is <= ts
	// Then walk backwards by slide intervals
	end := wa.alignTimestamp(ts).Add(wa.windowSize)

	for !end.Before(ts) {
		start := end.Add(-wa.windowSize)
		if start.Before(ts) || start.Equal(ts) {
			w := core.Window{Start: start, End: end}
			if w.Contains(ts) || ts.Equal(start) {
				windows = append([]core.Window{w}, windows...)
			}
		}
		end = end.Add(-wa.slide)
		// Safety: stop if we've gone too far back
		if end.Add(wa.windowSize).Before(ts.Add(-wa.windowSize)) {
			break
		}
	}

	// Simpler approach: iterate forward
	windows = nil
	firstEnd := wa.alignTimestamp(ts).Add(wa.windowSize)
	// Go back enough to cover all possible windows
	currentEnd := firstEnd
	earliest := ts.Add(-wa.windowSize)

	for currentEnd.After(earliest) {
		start := currentEnd.Add(-wa.windowSize)
		if start.Before(ts) && (ts.Before(currentEnd) || ts.Equal(start)) {
			w := core.Window{Start: start, End: currentEnd}
			if w.Contains(ts) {
				windows = append([]core.Window{w}, windows...)
			}
		}
		currentEnd = currentEnd.Add(-wa.slide)
	}

	return windows
}

// alignTimestamp snaps a timestamp to the nearest window boundary.
// Alignment is done relative to the Unix epoch, preserving the input location.
func (wa *WindowAssigner) alignTimestamp(ts time.Time) time.Time {
	nanos := ts.UnixNano()
	slideNanos := wa.slide.Nanoseconds()
	aligned := (nanos / slideNanos) * slideNanos
	return time.Unix(0, aligned).In(ts.Location())
}

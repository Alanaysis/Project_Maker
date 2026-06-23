package window

import (
	"time"

	"github.com/learning/stream-processing/internal/core"
)

// TumblingWindow divides time into fixed-size, non-overlapping windows.
// Each event belongs to exactly one window.
//
// Example (5-second windows):
//   Time:  0  1  2  3  4  5  6  7  8  9  10
//   Win 1: [-----)
//   Win 2:       [-----)
//   Win 3:             [-----)
type TumblingWindow struct {
	size     time.Duration
	assigner WindowAssigner
}

// NewTumblingWindow creates a tumbling window with the given size.
func NewTumblingWindow(size time.Duration) *TumblingWindow {
	return &TumblingWindow{
		size: size,
		assigner: WindowAssigner{
			windowSize: size,
			slide:      size, // tumbling: slide == size
		},
	}
}

// Assign returns the window that the given timestamp belongs to.
func (tw *TumblingWindow) Assign(ts time.Time) core.Window {
	return tw.assigner.Assign(ts)
}

// Size returns the window size.
func (tw *TumblingWindow) Size() time.Duration {
	return tw.size
}

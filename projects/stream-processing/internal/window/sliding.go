package window

import (
	"time"

	"github.com/learning/stream-processing/internal/core"
)

// SlidingWindow divides time into fixed-size windows that advance by a slide interval.
// An event can belong to multiple windows if slide < size.
//
// Example (size=10s, slide=5s):
//   Time:  0  1  2  3  4  5  6  7  8  9  10  11  12  13  14  15
//   Win 1: [-------------------)
//   Win 2:           [-------------------)
//   Win 3:                     [-------------------)
type SlidingWindow struct {
	size     time.Duration
	slide    time.Duration
	assigner WindowAssigner
}

// NewSlidingWindow creates a sliding window with the given size and slide interval.
func NewSlidingWindow(size, slide time.Duration) *SlidingWindow {
	return &SlidingWindow{
		size:  size,
		slide: slide,
		assigner: WindowAssigner{
			windowSize: size,
			slide:      slide,
		},
	}
}

// Assign returns all windows that the given timestamp belongs to.
func (sw *SlidingWindow) Assign(ts time.Time) []core.Window {
	return sw.assigner.AssignMultiple(ts)
}

// Size returns the window size.
func (sw *SlidingWindow) Size() time.Duration {
	return sw.size
}

// Slide returns the slide interval.
func (sw *SlidingWindow) Slide() time.Duration {
	return sw.slide
}

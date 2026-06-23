package operator

import (
	"sort"
	"sync"
	"time"

	"github.com/learning/stream-processing/internal/core"
	"github.com/learning/stream-processing/internal/window"
)

// WindowedReduceOperator performs aggregation within time windows.
// It buffers events by window, applies a reduce function when the
// window closes, and emits the aggregated result.
type WindowedReduceOperator struct {
	mu         sync.Mutex
	windowSize time.Duration
	slide      time.Duration
	reduceFn   ReduceFunc
	buffers    map[core.Window][]core.Event
	watermark  time.Time
}

// NewWindowedReduceOperator creates a windowed reduce operator.
// Use slide == size for tumbling windows, slide < size for sliding windows.
func NewWindowedReduceOperator(windowSize, slide time.Duration, fn ReduceFunc) *WindowedReduceOperator {
	return &WindowedReduceOperator{
		windowSize: windowSize,
		slide:      slide,
		reduceFn:   fn,
		buffers:    make(map[core.Window][]core.Event),
	}
}

func (wr *WindowedReduceOperator) Process(event core.Event, out *core.Stream) {
	wr.mu.Lock()
	defer wr.mu.Unlock()

	var windows []core.Window
	if wr.slide == wr.windowSize {
		// Tumbling window
		tw := window.NewTumblingWindow(wr.windowSize)
		windows = []core.Window{tw.Assign(event.Timestamp)}
	} else {
		// Sliding window
		sw := window.NewSlidingWindow(wr.windowSize, wr.slide)
		windows = sw.Assign(event.Timestamp)
	}

	for _, w := range windows {
		wr.buffers[w] = append(wr.buffers[w], event)
	}

	// Update watermark
	if event.Timestamp.After(wr.watermark) {
		wr.watermark = event.Timestamp
	}
}

// Flush emits results for all windows that have closed (i.e., their end time
// has been passed by the watermark).
func (wr *WindowedReduceOperator) Flush(out *core.Stream) {
	wr.mu.Lock()
	defer wr.mu.Unlock()

	for w, events := range wr.buffers {
		if !w.End.After(wr.watermark) || len(events) > 0 {
			result := wr.reduceEvents(events)
			if result != nil {
				out.Emit(core.Event{
					Key:       "window_result",
					Value:     result,
					Timestamp: w.End,
				})
			}
			delete(wr.buffers, w)
		}
	}
}

// EmitWindows forces emission of all current window results.
// Useful for testing or when the stream is ending.
func (wr *WindowedReduceOperator) EmitWindows(out *core.Stream) {
	wr.mu.Lock()
	defer wr.mu.Unlock()

	// Sort windows by start time for deterministic output
	windows := make([]core.Window, 0, len(wr.buffers))
	for w := range wr.buffers {
		windows = append(windows, w)
	}
	sort.Slice(windows, func(i, j int) bool {
		return windows[i].Start.Before(windows[j].Start)
	})

	for _, w := range windows {
		events := wr.buffers[w]
		result := wr.reduceEvents(events)
		if result != nil {
			out.Emit(core.Event{
				Key:       "window_result",
				Value:     result,
				Timestamp: w.End,
			})
		}
		delete(wr.buffers, w)
	}
}

// reduceEvents applies the reduce function to a slice of events.
func (wr *WindowedReduceOperator) reduceEvents(events []core.Event) interface{} {
	if len(events) == 0 {
		return nil
	}

	acc := events[0].Value
	for _, e := range events[1:] {
		acc = wr.reduceFn(acc, e.Value)
	}
	return acc
}

// BufferSize returns the number of buffered windows (for testing).
func (wr *WindowedReduceOperator) BufferSize() int {
	wr.mu.Lock()
	defer wr.mu.Unlock()
	return len(wr.buffers)
}

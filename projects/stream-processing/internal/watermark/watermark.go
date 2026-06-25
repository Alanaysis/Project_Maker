package watermark

import (
	"sync"
	"time"
)

// Watermark tracks the progress of event time in a stream.
// It represents a guarantee that no events with timestamps
// before the watermark will arrive in the future.
//
// This is essential for:
// - Determining when to close time windows
// - Handling late-arriving events
// - Triggering time-based computations
type Watermark struct {
	mu             sync.Mutex
	currentTime    time.Time
	maxOutOfOrderness time.Duration
	lastUpdateTime time.Time
}

// NewWatermark creates a new watermark tracker.
// maxOutOfOrderness specifies the maximum expected delay for out-of-order events.
func NewWatermark(maxOutOfOrderness time.Duration) *Watermark {
	return &Watermark{
		currentTime:       time.Time{},
		maxOutOfOrderness: maxOutOfOrderness,
	}
}

// Update advances the watermark based on a new event timestamp.
// The watermark is set to: eventTime - maxOutOfOrderness
// It only moves forward, never backward.
func (w *Watermark) Update(eventTime time.Time) time.Time {
	w.mu.Lock()
	defer w.mu.Unlock()

	newWatermark := eventTime.Add(-w.maxOutOfOrderness)

	if newWatermark.After(w.currentTime) {
		w.currentTime = newWatermark
	}

	w.lastUpdateTime = time.Now()
	return w.currentTime
}

// Current returns the current watermark time.
func (w *Watermark) Current() time.Time {
	w.mu.Lock()
	defer w.mu.Unlock()
	return w.currentTime
}

// IsLate checks if an event timestamp is late (before the watermark).
func (w *Watermark) IsLate(eventTime time.Time) bool {
	w.mu.Lock()
	defer w.mu.Unlock()
	return eventTime.Before(w.currentTime)
}

// GetMaxOutOfOrderness returns the configured max out-of-orderness.
func (w *Watermark) GetMaxOutOfOrderness() time.Duration {
	return w.maxOutOfOrderness
}

// Progress returns the watermark progress as a ratio (0.0 to 1.0).
// Useful for monitoring.
func (w *Watermark) Progress(startTime time.Time) float64 {
	w.mu.Lock()
	defer w.mu.Unlock()

	if startTime.IsZero() {
		return 0.0
	}

	elapsed := w.currentTime.Sub(startTime)
	total := time.Since(startTime)
	if total == 0 {
		return 0.0
	}
	return float64(elapsed) / float64(total)
}

// WatermarkPolicy defines how the watermark advances.
type WatermarkPolicy interface {
	// ComputeWatermark computes the new watermark from observed timestamps.
	ComputeWatermark(timestamps []time.Time) time.Time
}

// BoundedOutOfOrdernessPolicy sets watermark to max(timestamp) - outOfOrderness.
type BoundedOutOfOrdernessPolicy struct {
	outOfOrderness time.Duration
}

// NewBoundedOutOfOrdernessPolicy creates a bounded out-of-orderness policy.
func NewBoundedOutOfOrdernessPolicy(d time.Duration) *BoundedOutOfOrdernessPolicy {
	return &BoundedOutOfOrdernessPolicy{outOfOrderness: d}
}

func (p *BoundedOutOfOrdernessPolicy) ComputeWatermark(timestamps []time.Time) time.Time {
	if len(timestamps) == 0 {
		return time.Time{}
	}

	maxTs := timestamps[0]
	for _, ts := range timestamps[1:] {
		if ts.After(maxTs) {
			maxTs = ts
		}
	}

	return maxTs.Add(-p.outOfOrderness)
}

// PeriodicWatermarkGenerator generates watermarks at fixed intervals.
// Useful for processing-time based watermark emission.
type PeriodicWatermarkGenerator struct {
	interval time.Duration
	watermark *Watermark
	stopCh    chan struct{}
}

// NewPeriodicWatermarkGenerator creates a generator that emits watermarks.
func NewPeriodicWatermarkGenerator(interval time.Duration, watermark *Watermark) *PeriodicWatermarkGenerator {
	return &PeriodicWatermarkGenerator{
		interval:  interval,
		watermark: watermark,
		stopCh:    make(chan struct{}),
	}
}

// Start begins periodic watermark emission. Returns a channel that
// receives the current watermark at each interval.
func (g *PeriodicWatermarkGenerator) Start() <-chan time.Time {
	ch := make(chan time.Time, 1)

	go func() {
		defer close(ch)

		ticker := time.NewTicker(g.interval)
		defer ticker.Stop()

		for {
			select {
			case <-g.stopCh:
				return
			case t := <-ticker.C:
				_ = t
				ch <- g.watermark.Current()
			}
		}
	}()

	return ch
}

// Stop stops the generator.
func (g *PeriodicWatermarkGenerator) Stop() {
	close(g.stopCh)
}

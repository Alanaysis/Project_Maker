// Package processor implements idempotent message processing.
//
// The Processor ensures that each message is processed exactly once by
// combining deduplication with idempotent handler functions. Even if
// a message is delivered multiple times (at-least-once delivery), the
// Processor guarantees the side effects occur only once.
//
// Idempotency means: processing the same message N times produces the
// same result as processing it once. This is achieved by:
// 1. Checking the deduplicator before processing
// 2. Using handlers that are designed to be idempotent
// 3. Recording the result so duplicates can return the cached result
package processor

import (
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/anthropic/exactly-once/internal/dedup"
	"github.com/anthropic/exactly-once/internal/message"
	"github.com/anthropic/exactly-once/internal/tracker"
)

// Handler is a function that processes a message payload and returns
// a result. Handlers MUST be idempotent: calling them multiple times
// with the same input must produce the same output without additional
// side effects.
type Handler func(msg *message.Message) ([]byte, error)

// Processor coordinates deduplication and idempotent processing.
type Processor struct {
	mu       sync.RWMutex
	dedup    *dedup.Deduplicator
	tracker  *tracker.Tracker
	handlers map[string]Handler
	stats    Stats
	onSuccess func(msg *message.Message)
	onDuplicate func(msg *message.Message)
	onFailure func(msg *message.Message, err error)
}

// Stats tracks processing statistics.
type Stats struct {
	Processed   int64
	Succeeded   int64
	Failed      int64
	Duplicated  int64
	Retried     int64
	TotalTimeNs int64
}

// Option configures a Processor.
type Option func(*Processor)

// WithDeduplicator sets a custom deduplicator.
func WithDeduplicator(d *dedup.Deduplicator) Option {
	return func(p *Processor) {
		p.dedup = d
	}
}

// WithTracker sets a custom tracker.
func WithTracker(t *tracker.Tracker) Option {
	return func(p *Processor) {
		p.tracker = t
	}
}

// WithOnSuccess sets a callback for successful processing.
func WithOnSuccess(fn func(msg *message.Message)) Option {
	return func(p *Processor) {
		p.onSuccess = fn
	}
}

// WithOnDuplicate sets a callback for duplicate detection.
func WithOnDuplicate(fn func(msg *message.Message)) Option {
	return func(p *Processor) {
		p.onDuplicate = fn
	}
}

// WithOnFailure sets a callback for processing failures.
func WithOnFailure(fn func(msg *message.Message, err error)) Option {
	return func(p *Processor) {
		p.onFailure = fn
	}
}

// New creates a new Processor with the given options.
func New(opts ...Option) *Processor {
	p := &Processor{
		handlers: make(map[string]Handler),
		stats:    Stats{},
	}
	for _, opt := range opts {
		opt(p)
	}
	if p.dedup == nil {
		p.dedup = dedup.New()
	}
	if p.tracker == nil {
		p.tracker = tracker.New()
	}
	return p
}

// Register adds a named handler for message processing.
func (p *Processor) Register(name string, handler Handler) {
	p.mu.Lock()
	defer p.mu.Unlock()
	p.handlers[name] = handler
}

// Process handles a message with exactly-once semantics.
//
// The flow is:
// 1. Check deduplication - is this a duplicate?
// 2. Track the message state
// 3. Execute the handler (idempotent)
// 4. Record the result
// 5. Handle retries for failures
func (p *Processor) Process(msg *message.Message, handlerName string) error {
	start := time.Now()

	p.mu.RLock()
	handler, exists := p.handlers[handlerName]
	p.mu.RUnlock()

	if !exists {
		return fmt.Errorf("handler '%s' not registered", handlerName)
	}

	// Step 1: Deduplication check
	dedupResult := p.dedup.Check(msg.IdempotencyKey)
	switch dedupResult {
	case dedup.ResultDuplicate:
		msg.MarkDuplicate()
		p.mu.Lock()
		p.stats.Duplicated++
		p.mu.Unlock()
		if p.onDuplicate != nil {
			p.onDuplicate(msg)
		}
		log.Printf("[processor] duplicate detected: key=%s id=%s", msg.IdempotencyKey, msg.ID)
		return nil

	case dedup.ResultInProgress:
		return fmt.Errorf("message %s is already being processed", msg.ID)
	}

	// Step 2: Track message
	p.tracker.Track(msg)

	// Step 3: Process with retry logic
	var lastErr error
	for attempt := 0; attempt <= msg.MaxRetries; attempt++ {
		if attempt > 0 {
			msg.IncrementRetry()
			p.mu.Lock()
			p.stats.Retried++
			p.mu.Unlock()
			log.Printf("[processor] retrying message: id=%s attempt=%d", msg.ID, attempt)
		}

		msg.MarkProcessing()
		p.tracker.Update(msg)

		result, err := handler(msg)
		if err != nil {
			lastErr = err
			msg.MarkFailed(err.Error())
			p.tracker.Update(msg)
			p.dedup.MarkFailed(msg.IdempotencyKey, err.Error())
			log.Printf("[processor] processing failed: id=%s error=%v", msg.ID, err)

			if !msg.CanRetry() {
				break
			}
			continue
		}

		// Step 4: Success
		msg.MarkCompleted(result)
		p.dedup.MarkCompleted(msg.IdempotencyKey, result)
		p.tracker.Update(msg)

		p.mu.Lock()
		p.stats.Processed++
		p.stats.Succeeded++
		p.stats.TotalTimeNs += time.Since(start).Nanoseconds()
		p.mu.Unlock()

		if p.onSuccess != nil {
			p.onSuccess(msg)
		}
		log.Printf("[processor] message processed: id=%s duration=%v", msg.ID, time.Since(start))
		return nil
	}

	// All retries exhausted
	p.mu.Lock()
	p.stats.Processed++
	p.stats.Failed++
	p.stats.TotalTimeNs += time.Since(start).Nanoseconds()
	p.mu.Unlock()

	if p.onFailure != nil {
		p.onFailure(msg, lastErr)
	}
	return fmt.Errorf("message %s failed after %d retries: %w", msg.ID, msg.RetryCount, lastErr)
}

// ProcessWithHandler processes a message with an inline handler function.
// This is useful for one-off processing without registering a handler.
func (p *Processor) ProcessWithHandler(msg *message.Message, handler Handler) error {
	// Temporarily register with a unique name
	name := fmt.Sprintf("inline-%s", msg.ID)
	p.Register(name, handler)
	return p.Process(msg, name)
}

// GetHandler returns the named handler, or nil if not found.
func (p *Processor) GetHandler(name string) Handler {
	p.mu.RLock()
	defer p.mu.RUnlock()
	return p.handlers[name]
}

// StatsSnapshot returns a copy of the current statistics.
func (p *Processor) StatsSnapshot() Stats {
	p.mu.RLock()
	defer p.mu.RUnlock()
	return p.stats
}

// AverageProcessingTime returns the average processing time in nanoseconds.
func (p *Processor) AverageProcessingTime() time.Duration {
	p.mu.RLock()
	defer p.mu.RUnlock()
	if p.stats.Processed == 0 {
		return 0
	}
	return time.Duration(p.stats.TotalTimeNs / p.stats.Processed)
}

// Deduplicator returns the underlying deduplicator.
func (p *Processor) Deduplicator() *dedup.Deduplicator {
	return p.dedup
}

// Tracker returns the underlying tracker.
func (p *Processor) Tracker() *tracker.Tracker {
	return p.tracker
}

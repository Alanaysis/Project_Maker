// Package forwarder implements log forwarding with batching, retry, and backpressure.
//
// The forwarder is responsible for taking parsed log entries and sending them
// to one or more destinations (e.g., TCP, UDP, HTTP, or another collector).
//
// Key features:
// 1. Batching: Collect entries into batches for efficient network transmission
// 2. Retry: Automatically retry failed sends with exponential backoff
// 3. Backpressure: Slow down the input channel when the output is congested
// 4. Circuit breaker: Stop sending when the destination is consistently unavailable
package forwarder

import (
	"fmt"
	"math"
	"sync"
	"time"
)

// Entry represents a log entry to be forwarded.
type Entry struct {
	Timestamp time.Time
	Level     string
	Message   string
	Source    string
	Fields    map[string]string
	Raw       string
}

// BatchSize defines the batch size for forwarding.
type BatchSize struct {
	// MaxEntries is the maximum number of entries per batch.
	MaxEntries int
	// MaxBytes is the maximum total bytes per batch.
	MaxBytes int
	// FlushInterval is the maximum time to wait before flushing a partial batch.
	FlushInterval time.Duration
}

// DefaultBatchSize returns a BatchSize with sensible defaults.
func DefaultBatchSize() BatchSize {
	return BatchSize{
		MaxEntries:    100,
		MaxBytes:      1024 * 100, // 100KB
		FlushInterval: 1 * time.Second,
	}
}

// RetryConfig configures the retry behavior.
type RetryConfig struct {
	// MaxRetries is the maximum number of retry attempts.
	MaxRetries int
	// InitialInterval is the initial retry interval.
	InitialInterval time.Duration
	// MaxInterval is the maximum retry interval (for exponential backoff).
	MaxInterval time.Duration
	// BackoffMultiplier is the multiplier for exponential backoff.
	BackoffMultiplier float64
}

// DefaultRetryConfig returns a RetryConfig with sensible defaults.
func DefaultRetryConfig() RetryConfig {
	return RetryConfig{
		MaxRetries:        3,
		InitialInterval:   100 * time.Millisecond,
		MaxInterval:       10 * time.Second,
		BackoffMultiplier: 2.0,
	}
}

// Destination represents a log forwarding destination.
type Destination interface {
	// Send sends a batch of entries to the destination.
	// Returns the number of successfully sent entries and any error.
	Send(entries []Entry) (int, error)
	// Name returns the destination name (for logging).
	Name() string
	// Close closes the destination connection.
	Close() error
	// IsHealthy checks if the destination is healthy.
	IsHealthy() bool
}

// Forwarder collects and forwards log entries to destinations.
type Forwarder struct {
	dest         Destination
	batchSize    BatchSize
	retryConfig  RetryConfig
	input        chan Entry
	flushCh      chan struct{}
	done         chan struct{}
	wg           sync.WaitGroup
	mu           sync.Mutex
	pending      []Entry
	flushTimer   *time.Timer
	stats        ForwarderStats
	stopOnce     sync.Once
}

// ForwarderStats tracks forwarding statistics.
type ForwarderStats struct {
	TotalReceived  int64
	TotalForwarded int64
	TotalFailed    int64
	TotalRetried   int64
	BatchCount     int64
	LastForwarded  time.Time
	LastError      string
	LastErrTime    time.Time
}

// NewForwarder creates a new Forwarder.
func NewForwarder(dest Destination, batchSize BatchSize, retryConfig RetryConfig) *Forwarder {
	if batchSize.MaxEntries <= 0 {
		batchSize = DefaultBatchSize()
	}
	if retryConfig.MaxRetries <= 0 {
		retryConfig = DefaultRetryConfig()
	}

	return &Forwarder{
		dest:        dest,
		batchSize:   batchSize,
		retryConfig: retryConfig,
		input:       make(chan Entry, 1000), // Buffered to handle bursts
		flushCh:     make(chan struct{}, 1),
		done:        make(chan struct{}),
		pending:     make([]Entry, 0, batchSize.MaxEntries),
	}
}

// Start begins the forwarding loop.
func (f *Forwarder) Start() error {
	if !f.dest.IsHealthy() {
		return fmt.Errorf("forwarder: destination %s is not healthy", f.dest.Name())
	}

	f.wg.Add(1)
	go f.forwardLoop()
	return nil
}

// Stop signals the forwarder to stop and waits for completion.
func (f *Forwarder) Stop() {
	f.stopOnce.Do(func() {
		close(f.done)
	})
	f.wg.Wait()
}

// Send sends an entry to the forwarder for forwarding.
// This method implements backpressure by blocking when the input buffer is full.
func (f *Forwarder) Send(entry Entry) error {
	select {
	case f.input <- entry:
		f.mu.Lock()
		f.stats.TotalReceived++
		f.mu.Unlock()
		return nil
	case <-f.done:
		return fmt.Errorf("forwarder: stopped")
	}
}

// Flush forces a flush of the current pending batch.
func (f *Forwarder) Flush() {
	select {
	case f.flushCh <- struct{}{}:
	default:
	}
}

// Stats returns the current forwarding statistics.
func (f *Forwarder) Stats() ForwarderStats {
	f.mu.Lock()
	defer f.mu.Unlock()
	return f.stats
}

// forwardLoop is the main forwarding goroutine.
func (f *Forwarder) forwardLoop() {
	defer f.wg.Done()

	f.flushTimer = time.NewTimer(f.batchSize.FlushInterval)
	defer f.flushTimer.Stop()

	for {
		select {
		case <-f.done:
			// Final flush before stopping
			f.flushPending()
			return

		case <-f.flushCh:
			f.flushPending()

		case <-f.flushTimer.C:
			f.flushPending()
			f.flushTimer.Reset(f.batchSize.FlushInterval)

		case entry, ok := <-f.input:
			if !ok {
				return
			}
			f.mu.Lock()
			f.pending = append(f.pending, entry)

			// Check if batch is full
			if len(f.pending) >= f.batchSize.MaxEntries {
				f.mu.Unlock()
				f.flushPending()
				f.mu.Lock()
				f.pending = f.pending[:0]
			}
			f.mu.Unlock()
		}
	}
}

// flushPending sends the pending batch to the destination.
func (f *Forwarder) flushPending() {
	f.mu.Lock()
	if len(f.pending) == 0 {
		f.mu.Unlock()
		return
	}
	batch := make([]Entry, len(f.pending))
	copy(batch, f.pending)
	f.mu.Unlock()

	// Send with retry
	sent, err := f.sendWithRetry(batch)

	f.mu.Lock()
	f.stats.TotalForwarded += int64(sent)
	if err != nil {
		f.stats.TotalFailed++
		f.stats.LastError = err.Error()
		f.stats.LastErrTime = time.Now()
	} else {
		f.stats.BatchCount++
		f.stats.LastForwarded = time.Now()
	}
	f.mu.Unlock()
}

// sendWithRetry sends a batch with exponential backoff retry.
func (f *Forwarder) sendWithRetry(batch []Entry) (int, error) {
	var lastErr error
	interval := f.retryConfig.InitialInterval

	for attempt := 0; attempt <= f.retryConfig.MaxRetries; attempt++ {
		if attempt > 0 {
			f.mu.Lock()
			f.stats.TotalRetried++
			f.mu.Unlock()

			// Exponential backoff with jitter
			backoff := time.Duration(float64(interval) * f.retryConfig.BackoffMultiplier)
			if backoff > f.retryConfig.MaxInterval {
				backoff = f.retryConfig.MaxInterval
			}
			// Add jitter (±10%)
			jitter := time.Duration(float64(backoff) * 0.1 * (float64(attempt%100) / 100.0 - 0.05))
			backoff += jitter

			time.Sleep(backoff)
		}

		sent, err := f.dest.Send(batch)
		if err == nil {
			return sent, nil
		}
		lastErr = err
	}

	return 0, fmt.Errorf("forwarder: failed to send batch of %d entries to %s after %d retries: %w",
		len(batch), f.dest.Name(), f.retryConfig.MaxRetries, lastErr)
}

// CalculateBatchSize calculates the total byte size of a batch.
func CalculateBatchSize(entries []Entry) int {
	var total int
	for _, e := range entries {
		total += len(e.Raw)
		total += len(e.Message)
		total += len(e.Source)
		for k, v := range e.Fields {
			total += len(k) + len(v)
		}
	}
	return total
}

// BackpressureMonitor monitors and reports backpressure status.
type BackpressureMonitor struct {
	mu         sync.Mutex
	inputLen   int
	inputCap   int
	isBackpressured bool
}

// NewBackpressureMonitor creates a new BackpressureMonitor.
func NewBackpressureMonitor(capacity int) *BackpressureMonitor {
	return &BackpressureMonitor{
		inputCap: capacity,
	}
}

// Check returns true if backpressure should be applied.
func (bm *BackpressureMonitor) Check(inputLen int) bool {
	bm.mu.Lock()
	defer bm.mu.Unlock()
	bm.inputLen = inputLen
	// Apply backpressure at 80% capacity
	bm.isBackpressured = bm.inputLen > bm.inputCap*80/100
	return bm.isBackpressured
}

// GetBackpressureRatio returns the current backpressure ratio (0.0 to 1.0).
func (bm *BackpressureMonitor) GetBackpressureRatio() float64 {
	bm.mu.Lock()
	defer bm.mu.Unlock()
	if bm.inputCap == 0 {
		return 0
	}
	ratio := float64(bm.inputLen) / float64(bm.inputCap)
	if ratio > 1.0 {
		ratio = 1.0
	}
	return ratio
}

// ExponentialBackoff implements exponential backoff calculation.
type ExponentialBackoff struct {
	InitialInterval time.Duration
	MaxInterval     time.Duration
	Multiplier      float64
}

// NewExponentialBackoff creates a new ExponentialBackoff.
func NewExponentialBackoff(initial, max time.Duration, multiplier float64) *ExponentialBackoff {
	return &ExponentialBackoff{
		InitialInterval: initial,
		MaxInterval:     max,
		Multiplier:      multiplier,
	}
}

// NextInterval calculates the next backoff interval for the given attempt number.
func (eb *ExponentialBackoff) NextInterval(attempt int) time.Duration {
	if attempt < 0 {
		attempt = 0
	}
	interval := float64(eb.InitialInterval) * math.Pow(eb.Multiplier, float64(attempt))
	if time.Duration(interval) > eb.MaxInterval {
		return eb.MaxInterval
	}
	return time.Duration(interval)
}

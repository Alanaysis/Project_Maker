// Package dedup implements message deduplication using idempotency keys.
//
// The Deduplicator tracks seen idempotency keys and determines whether
// a message has already been processed. This is the first line of defense
// in achieving exactly-once semantics: before processing any message,
// we check if we've already seen an equivalent operation.
//
// Two deduplication strategies are supported:
//   - Memory-based: Fast, in-process, lost on restart
//   - Key-based: Uses the message's idempotency key directly
package dedup

import (
	"sync"
	"time"
)

// Result represents the outcome of a deduplication check.
type Result int

const (
	// ResultNew indicates this is a new, unseen message.
	ResultNew Result = iota
	// ResultDuplicate indicates this message has been seen before.
	ResultDuplicate
	// ResultInProgress indicates this message is currently being processed.
	ResultInProgress
)

// String returns a human-readable representation of the dedup result.
func (r Result) String() string {
	switch r {
	case ResultNew:
		return "NEW"
	case ResultDuplicate:
		return "DUPLICATE"
	case ResultInProgress:
		return "IN_PROGRESS"
	default:
		return "UNKNOWN"
	}
}

// Entry tracks the state of a seen idempotency key.
type Entry struct {
	// Key is the idempotency key.
	Key string

	// State is the current processing state.
	State string

	// FirstSeen is when this key was first encountered.
	FirstSeen time.Time

	// LastSeen is when this key was last encountered.
	LastSeen time.Time

	// SeenCount tracks how many times this key has been seen.
	SeenCount int

	// Result stores the processing result (if completed).
	Result []byte

	// Error stores the error (if failed).
	Error string
}

// Deduplicator tracks seen messages and detects duplicates.
type Deduplicator struct {
	mu         sync.RWMutex
	entries    map[string]*Entry
	maxEntries int
	ttl        time.Duration
	stats      Stats
}

// Stats tracks deduplication statistics.
type Stats struct {
	TotalChecks   int64
	NewMessages   int64
	Duplicates    int64
	InProgress    int64
	Evictions     int64
}

// Option configures a Deduplicator.
type Option func(*Deduplicator)

// WithMaxEntries sets the maximum number of tracked entries.
// Oldest entries are evicted when this limit is reached.
func WithMaxEntries(n int) Option {
	return func(d *Deduplicator) {
		d.maxEntries = n
	}
}

// WithTTL sets the time-to-live for entries. After TTL expires,
// entries are eligible for eviction on the next check.
func WithTTL(ttl time.Duration) Option {
	return func(d *Deduplicator) {
		d.ttl = ttl
	}
}

// New creates a new Deduplicator with the given options.
func New(opts ...Option) *Deduplicator {
	d := &Deduplicator{
		entries:    make(map[string]*Entry),
		maxEntries: 10000,
		ttl:        24 * time.Hour,
	}
	for _, opt := range opts {
		opt(d)
	}
	return d
}

// Check determines whether a message with the given idempotency key
// is new, a duplicate, or currently in progress.
func (d *Deduplicator) Check(key string) Result {
	d.mu.Lock()
	defer d.mu.Unlock()

	d.stats.TotalChecks++

	entry, exists := d.entries[key]
	if !exists {
		// New message - register it as in-progress
		d.entries[key] = &Entry{
			Key:       key,
			State:     "processing",
			FirstSeen: time.Now(),
			LastSeen:  time.Now(),
			SeenCount: 1,
		}
		d.stats.NewMessages++
		return ResultNew
	}

	// Check if entry has expired
	if d.ttl > 0 && time.Since(entry.FirstSeen) > d.ttl {
		// Replace expired entry
		d.entries[key] = &Entry{
			Key:       key,
			State:     "processing",
			FirstSeen: time.Now(),
			LastSeen:  time.Now(),
			SeenCount: 1,
		}
		d.stats.NewMessages++
		return ResultNew
	}

	// Entry exists - update tracking
	entry.LastSeen = time.Now()
	entry.SeenCount++

	switch entry.State {
	case "processing":
		d.stats.InProgress++
		return ResultInProgress
	case "completed", "failed":
		d.stats.Duplicates++
		return ResultDuplicate
	default:
		d.stats.Duplicates++
		return ResultDuplicate
	}
}

// MarkCompleted records that processing for the given key succeeded.
func (d *Deduplicator) MarkCompleted(key string, result []byte) {
	d.mu.Lock()
	defer d.mu.Unlock()

	if entry, exists := d.entries[key]; exists {
		entry.State = "completed"
		entry.Result = result
		entry.LastSeen = time.Now()
	}
}

// MarkFailed records that processing for the given key failed.
func (d *Deduplicator) MarkFailed(key string, err string) {
	d.mu.Lock()
	defer d.mu.Unlock()

	if entry, exists := d.entries[key]; exists {
		entry.State = "failed"
		entry.Error = err
		entry.LastSeen = time.Now()
	}
}

// Reset removes a key from tracking, allowing it to be reprocessed.
// This is useful for retry scenarios where a failed message should
// be given another chance.
func (d *Deduplicator) Reset(key string) {
	d.mu.Lock()
	defer d.mu.Unlock()
	delete(d.entries, key)
}

// IsSeen returns true if the key has been seen before (in any state).
func (d *Deduplicator) IsSeen(key string) bool {
	d.mu.RLock()
	defer d.mu.RUnlock()

	entry, exists := d.entries[key]
	if !exists {
		return false
	}
	if d.ttl > 0 && time.Since(entry.FirstSeen) > d.ttl {
		return false
	}
	return true
}

// GetEntry returns the entry for the given key, or nil if not found.
func (d *Deduplicator) GetEntry(key string) *Entry {
	d.mu.RLock()
	defer d.mu.RUnlock()

	entry, exists := d.entries[key]
	if !exists {
		return nil
	}
	// Return a copy to avoid data races
	copy := *entry
	return &copy
}

// Size returns the number of tracked entries.
func (d *Deduplicator) Size() int {
	d.mu.RLock()
	defer d.mu.RUnlock()
	return len(d.entries)
}

// StatsSnapshot returns a copy of the current statistics.
func (d *Deduplicator) StatsSnapshot() Stats {
	d.mu.RLock()
	defer d.mu.RUnlock()
	return d.stats
}

// Cleanup removes expired entries. Call this periodically to reclaim memory.
func (d *Deduplicator) Cleanup() int {
	if d.ttl <= 0 {
		return 0
	}

	d.mu.Lock()
	defer d.mu.Unlock()

	removed := 0
	now := time.Now()
	for key, entry := range d.entries {
		if now.Sub(entry.FirstSeen) > d.ttl {
			delete(d.entries, key)
			removed++
			d.stats.Evictions++
		}
	}
	return removed
}

// Clear removes all entries and resets statistics.
func (d *Deduplicator) Clear() {
	d.mu.Lock()
	defer d.mu.Unlock()

	d.entries = make(map[string]*Entry)
	d.stats = Stats{}
}

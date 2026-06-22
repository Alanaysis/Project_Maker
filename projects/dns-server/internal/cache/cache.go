// Package cache implements a thread-safe in-memory DNS cache with TTL-based
// expiration. This is a key component of any DNS server -- caching answers
// avoids repeated upstream queries and dramatically reduces latency.
//
// Design decisions:
//   - Use sync.RWMutex for concurrent access (read-heavy workload)
//   - TTL is stored per-entry and checked on Get, not with a background goroutine
//   - Entries are lazily evicted (cleaned up on access and via periodic sweep)
//   - Cache key is "domain:type" to distinguish A vs AAAA for the same domain
package cache

import (
	"fmt"
	"sync"
	"time"

	"github.com/anthropic/dns-server/internal/protocol"
)

// Entry represents a cached DNS response.
type Entry struct {
	Records []protocol.ResourceRecord
	ExpiresAt time.Time
}

// IsExpired reports whether the cache entry has passed its TTL.
func (e *Entry) IsExpired() bool {
	return time.Now().After(e.ExpiresAt)
}

// Cache is a thread-safe in-memory DNS cache.
type Cache struct {
	mu      sync.RWMutex
	entries map[string]*Entry
	// maxSize limits memory usage; 0 means unlimited.
	maxSize int
	// stats tracks cache performance.
	stats Stats
}

// Stats tracks cache hit/miss statistics.
type Stats struct {
	Hits     uint64
	Misses   uint64
	Evictions uint64
}

// Option is a functional option for Cache configuration.
type Option func(*Cache)

// WithMaxSize sets the maximum number of cache entries.
func WithMaxSize(size int) Option {
	return func(c *Cache) {
		c.maxSize = size
	}
}

// New creates a new Cache with the given options.
func New(opts ...Option) *Cache {
	c := &Cache{
		entries: make(map[string]*Entry),
	}
	for _, opt := range opts {
		opt(c)
	}
	return c
}

// makeKey creates a cache key from domain name and record type.
func makeKey(name string, qtype uint16) string {
	return fmt.Sprintf("%s:%d", name, qtype)
}

// Get retrieves cached records for the given domain and type.
// Returns the records and true if found and not expired, nil and false otherwise.
func (c *Cache) Get(name string, qtype uint16) ([]protocol.ResourceRecord, bool) {
	key := makeKey(name, qtype)

	c.mu.RLock()
	entry, exists := c.entries[key]
	c.mu.RUnlock()

	if !exists {
		c.mu.Lock()
		c.stats.Misses++
		c.mu.Unlock()
		return nil, false
	}

	if entry.IsExpired() {
		// Expired entry; remove it lazily.
		c.mu.Lock()
		delete(c.entries, key)
		c.stats.Misses++
		c.stats.Evictions++
		c.mu.Unlock()
		return nil, false
	}

	c.mu.Lock()
	c.stats.Hits++
	c.mu.Unlock()

	return entry.Records, true
}

// Set stores DNS resource records in the cache with a TTL.
// The TTL of the entry is the minimum TTL across all records.
func (c *Cache) Set(name string, qtype uint16, records []protocol.ResourceRecord) {
	if len(records) == 0 {
		return
	}

	key := makeKey(name, qtype)

	// Use the minimum TTL among all records, with a floor of 30 seconds.
	var minTTL uint32 = 0xFFFFFFFF
	for _, rr := range records {
		if rr.TTL < minTTL {
			minTTL = rr.TTL
		}
	}
	if minTTL < 30 {
		minTTL = 30 // Minimum cache time to avoid thrashing
	}

	entry := &Entry{
		Records:   records,
		ExpiresAt: time.Now().Add(time.Duration(minTTL) * time.Second),
	}

	c.mu.Lock()
	defer c.mu.Unlock()

	// Evict if at capacity
	if c.maxSize > 0 && len(c.entries) >= c.maxSize {
		c.evictOldest()
	}

	c.entries[key] = entry
}

// Delete removes a specific entry from the cache.
func (c *Cache) Delete(name string, qtype uint16) {
	key := makeKey(name, qtype)
	c.mu.Lock()
	delete(c.entries, key)
	c.mu.Unlock()
}

// Clear removes all entries from the cache.
func (c *Cache) Clear() {
	c.mu.Lock()
	c.entries = make(map[string]*Entry)
	c.mu.Unlock()
}

// Size returns the number of entries currently in the cache.
func (c *Cache) Size() int {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return len(c.entries)
}

// Stats returns a snapshot of cache statistics.
func (c *Cache) StatsSnapshot() Stats {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.stats
}

// PurgeExpired removes all expired entries. This can be called periodically
// to reclaim memory from expired entries that haven't been accessed.
func (c *Cache) PurgeExpired() int {
	c.mu.Lock()
	defer c.mu.Unlock()

	now := time.Now()
	removed := 0
	for key, entry := range c.entries {
		if now.After(entry.ExpiresAt) {
			delete(c.entries, key)
			removed++
			c.stats.Evictions++
		}
	}
	return removed
}

// evictOldest removes the entry with the soonest expiration.
// Must be called with c.mu held for writing.
func (c *Cache) evictOldest() {
	var oldestKey string
	var oldestTime time.Time
	first := true
	for key, entry := range c.entries {
		if first || entry.ExpiresAt.Before(oldestTime) {
			oldestKey = key
			oldestTime = entry.ExpiresAt
			first = false
		}
	}
	if oldestKey != "" {
		delete(c.entries, oldestKey)
		c.stats.Evictions++
	}
}

// StartCleanup starts a background goroutine that periodically purges
// expired entries. Returns a stop function.
func (c *Cache) StartCleanup(interval time.Duration) func() {
	done := make(chan struct{})
	go func() {
		ticker := time.NewTicker(interval)
		defer ticker.Stop()
		for {
			select {
			case <-done:
				return
			case <-ticker.C:
				c.PurgeExpired()
			}
		}
	}()
	return func() { close(done) }
}

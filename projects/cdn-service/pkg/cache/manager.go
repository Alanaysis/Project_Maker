package cache

import (
	"sync"
	"sync/atomic"
	"time"
)

// CacheStats holds statistics about cache usage.
type CacheStats struct {
	Hits      int64 // Number of cache hits
	Misses    int64 // Number of cache misses
	Evictions int64 // Number of evictions
	Size      int64 // Current cache size in bytes
}

// HitRate calculates the cache hit rate.
func (s *CacheStats) HitRate() float64 {
	total := s.Hits + s.Misses
	if total == 0 {
		return 0
	}
	return float64(s.Hits) / float64(total)
}

// CacheManager manages the lifecycle of cached items.
// It handles TTL (Time To Live), cleanup of expired items,
// and provides cache statistics.
//
// ⭐ Key Responsibilities:
// 1. Manage cache TTL (Time To Live)
// 2. Periodically clean up expired items
// 3. Track cache statistics (hits, misses, evictions)
// 4. Control cache size
//
// 💡 Why CacheManager?
// - Separates cache logic from HTTP logic
// - Provides a clean interface for cache operations
// - Handles expiration and cleanup automatically
type CacheManager struct {
	cache          *LRUCache
	defaultTTL     time.Duration
	cleanupTicker  *time.Ticker
	stopCleanup    chan struct{}
	stats          CacheStats
	mutex          sync.RWMutex
	maxSize        int64
	currentSize    int64
}

// NewCacheManager creates a new cache manager.
//
// Parameters:
//   - capacity: maximum number of items in the cache
//   - defaultTTL: default time-to-live for cached items
//   - cleanupInterval: how often to clean up expired items
//
// Returns:
//   - *CacheManager: a new cache manager instance
func NewCacheManager(capacity int, defaultTTL, cleanupInterval time.Duration) *CacheManager {
	cm := &CacheManager{
		cache:       NewLRUCache(capacity),
		defaultTTL:  defaultTTL,
		stopCleanup: make(chan struct{}),
	}

	// Start background cleanup goroutine
	cm.cleanupTicker = time.NewTicker(cleanupInterval)
	go cm.cleanupLoop()

	return cm
}

// Get retrieves an item from the cache.
// It checks if the item exists and if it has expired.
//
// ⭐ Algorithm:
// 1. Look up the item in the LRU cache
// 2. If found, check if it has expired
// 3. If expired, remove it and return miss
// 4. If not expired, update stats and return hit
//
// Parameters:
//   - key: the cache key
//
// Returns:
//   - *CacheItem: the cached item (nil if not found)
//   - bool: true if the item was found and not expired
func (cm *CacheManager) Get(key string) (*CacheItem, bool) {
	cm.mutex.RLock()
	item, ok := cm.cache.Get(key)
	cm.mutex.RUnlock()

	if !ok {
		atomic.AddInt64(&cm.stats.Misses, 1)
		return nil, false
	}

	// Check if the item has expired
	if item.ExpiresAt.Before(time.Now()) {
		// Item has expired, remove it
		cm.Delete(key)
		atomic.AddInt64(&cm.stats.Misses, 1)
		return nil, false
	}

	atomic.AddInt64(&cm.stats.Hits, 1)
	return item, true
}

// Set adds or updates an item in the cache with the specified TTL.
// If TTL is 0, the default TTL is used.
//
// Parameters:
//   - key: the cache key
//   - item: the item to cache
//   - ttl: time-to-live (0 for default)
func (cm *CacheManager) Set(key string, item *CacheItem, ttl time.Duration) {
	if ttl == 0 {
		ttl = cm.defaultTTL
	}

	// Set expiration time
	item.ExpiresAt = time.Now().Add(ttl)

	cm.mutex.Lock()
	cm.cache.Put(key, item)
	cm.currentSize += item.Size
	cm.mutex.Unlock()
}

// Delete removes an item from the cache.
//
// Parameters:
//   - key: the cache key to remove
func (cm *CacheManager) Delete(key string) {
	cm.mutex.Lock()
	cm.cache.Delete(key)
	cm.mutex.Unlock()
}

// Clear removes all items from the cache.
func (cm *CacheManager) Clear() {
	cm.mutex.Lock()
	cm.cache.Clear()
	cm.currentSize = 0
	cm.mutex.Unlock()
}

// Stats returns a copy of the cache statistics.
func (cm *CacheManager) Stats() CacheStats {
	return CacheStats{
		Hits:      atomic.LoadInt64(&cm.stats.Hits),
		Misses:    atomic.LoadInt64(&cm.stats.Misses),
		Evictions: atomic.LoadInt64(&cm.stats.Evictions),
		Size:      atomic.LoadInt64(&cm.currentSize),
	}
}

// Len returns the current number of items in the cache.
func (cm *CacheManager) Len() int {
	return cm.cache.Len()
}

// Stop stops the cache manager and its background cleanup goroutine.
func (cm *CacheManager) Stop() {
	close(cm.stopCleanup)
	cm.cleanupTicker.Stop()
}

// cleanupLoop runs in a background goroutine to periodically
// clean up expired cache items.
//
// 💡 Why background cleanup?
// - Prevents expired items from accumulating
// - Keeps memory usage under control
// - Runs periodically without blocking requests
func (cm *CacheManager) cleanupLoop() {
	for {
		select {
		case <-cm.cleanupTicker.C:
			cm.cleanupExpired()
		case <-cm.stopCleanup:
			return
		}
	}
}

// cleanupExpired removes all expired items from the cache.
func (cm *CacheManager) cleanupExpired() {
	cm.mutex.Lock()
	defer cm.mutex.Unlock()

	now := time.Now()
	keys := cm.cache.Keys()

	for _, key := range keys {
		elem, ok := cm.cache.Get(key)
		if ok && elem.ExpiresAt.Before(now) {
			cm.cache.Delete(key)
			cm.currentSize -= elem.Size
			atomic.AddInt64(&cm.stats.Evictions, 1)
		}
	}
}
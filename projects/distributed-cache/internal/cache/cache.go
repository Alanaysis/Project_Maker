package cache

import (
	"fmt"
	"sync"
	"time"
)

// CacheStats holds cache statistics
type CacheStats struct {
	Hits       int64
	Misses     int64
	Evictions  int64
	Size       int
	Capacity   int
	HitRate    float64
}

// Cache represents an in-memory cache
type Cache struct {
	mu          sync.RWMutex
	items       map[string]*Item
	eviction    EvictionPolicy
	capacity    int
	stats       CacheStats
	onEvicted   func(key string, value interface{})
	cleanupTick time.Duration
	stopCh      chan struct{}
}

// CacheConfig holds cache configuration
type CacheConfig struct {
	Capacity     int
	EvictionType string
	DefaultTTL   time.Duration
	CleanupTick  time.Duration
	OnEvicted    func(key string, value interface{})
}

// NewCache creates a new cache instance
func NewCache(config CacheConfig) *Cache {
	if config.Capacity <= 0 {
		config.Capacity = 1000
	}
	if config.CleanupTick == 0 {
		config.CleanupTick = time.Minute
	}

	var eviction EvictionPolicy
	switch config.EvictionType {
	case "lru":
		eviction = NewLRUPolicy()
	case "lfu":
		eviction = NewLFUPolicy()
	case "fifo":
		eviction = NewFIFOPolicy()
	case "ttl":
		eviction = NewTTLPolicy(config.DefaultTTL)
	default:
		eviction = NewLRUPolicy()
	}

	c := &Cache{
		items:       make(map[string]*Item),
		eviction:    eviction,
		capacity:    config.Capacity,
		cleanupTick: config.CleanupTick,
		onEvicted:   config.OnEvicted,
		stopCh:      make(chan struct{}),
	}

	go c.cleanup()
	return c
}

// Get retrieves an item from the cache
func (c *Cache) Get(key string) (interface{}, bool) {
	c.mu.RLock()
	item, exists := c.items[key]
	c.mu.RUnlock()

	if !exists {
		c.mu.Lock()
		c.stats.Misses++
		c.updateHitRate()
		c.mu.Unlock()
		return nil, false
	}

	if item.IsExpired() {
		c.Delete(key)
		c.mu.Lock()
		c.stats.Misses++
		c.updateHitRate()
		c.mu.Unlock()
		return nil, false
	}

	c.mu.Lock()
	item.AccessAt = time.Now()
	item.Frequency++
	c.stats.Hits++
	c.updateHitRate()
	c.mu.Unlock()

	c.eviction.Access(key)
	return item.Value, true
}

// Set adds an item to the cache
func (c *Cache) Set(key string, value interface{}, ttl time.Duration) {
	c.mu.Lock()
	if _, exists := c.items[key]; exists {
		c.items[key] = value
		c.items[key].Expiration = 0
		if ttl > 0 {
			c.items[key].Expiration = time.Now().Add(ttl).UnixNano()
		}
		c.items[key].AccessAt = time.Now()
		c.items[key].Frequency++
		c.mu.Unlock()
		c.eviction.Access(key)
		return
	}

	if len(c.items) >= c.capacity {
		c.evict()
	}

	item := NewItem(key, value, ttl)
	c.items[key] = item
	c.mu.Unlock()
	c.eviction.Add(key)
}

// Delete removes an item from the cache
func (c *Cache) Delete(key string) bool {
	c.mu.Lock()
	item, exists := c.items[key]
	if !exists {
		c.mu.Unlock()
		return false
	}
	delete(c.items, key)
	c.mu.Unlock()
	c.eviction.Remove(key)

	if c.onEvicted != nil {
		c.onEvicted(key, item.Value)
	}
	return true
}

// Has checks if a key exists in the cache
func (c *Cache) Has(key string) bool {
	c.mu.RLock()
	defer c.mu.RUnlock()
	item, exists := c.items[key]
	if !exists {
		return false
	}
	return !item.IsExpired()
}

// Len returns the number of items in the cache
func (c *Cache) Len() int {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return len(c.items)
}

// Keys returns all keys in the cache
func (c *Cache) Keys() []string {
	c.mu.RLock()
	defer c.mu.RUnlock()
	keys := make([]string, 0, len(c.items))
	for k := range c.items {
		keys = append(keys, k)
	}
	return keys
}

// Clear removes all items from the cache
func (c *Cache) Clear() {
	c.mu.Lock()
	c.items = make(map[string]*Item)
	c.stats = CacheStats{Capacity: c.capacity}
	c.mu.Unlock()
}

// Stats returns cache statistics
func (c *Cache) Stats() CacheStats {
	c.mu.RLock()
	defer c.mu.RUnlock()
	c.stats.Size = len(c.items)
	return c.stats
}

// evict removes items based on eviction policy
func (c *Cache) evict() {
	key := c.eviction.Evict()
	if key == "" {
		return
	}
	item, exists := c.items[key]
	if exists {
		delete(c.items, key)
		c.stats.Evictions++
		if c.onEvicted != nil {
			c.onEvicted(key, item.Value)
		}
	}
}

// cleanup periodically removes expired items
func (c *Cache) cleanup() {
	ticker := time.NewTicker(c.cleanupTick)
	defer ticker.Stop()
	for {
		select {
		case <-ticker.C:
			c.mu.Lock()
			for key, item := range c.items {
				if item.IsExpired() {
					delete(c.items, key)
					c.eviction.Remove(key)
					if c.onEvicted != nil {
						c.onEvicted(key, item.Value)
					}
				}
			}
			c.mu.Unlock()
		case <-c.stopCh:
			return
		}
	}
}

func (c *Cache) updateHitRate() {
	total := c.stats.Hits + c.stats.Misses
	if total > 0 {
		c.stats.HitRate = float64(c.stats.Hits) / float64(total)
	}
}

// Stop stops the cache cleanup goroutine
func (c *Cache) Stop() {
	close(c.stopCh)
}

// String returns a string representation of the cache
func (c *Cache) String() string {
	stats := c.Stats()
	return fmt.Sprintf("Cache{size: %d/%d, hits: %d, misses: %d, hit_rate: %.2f%%, evictions: %d}",
		stats.Size, stats.Capacity, stats.Hits, stats.Misses, stats.HitRate*100, stats.Evictions)
}

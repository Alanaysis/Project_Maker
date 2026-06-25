package application

import (
	"sync"
	"sync/atomic"
	"time"

	"github.com/distributed-cache/internal/cache"
)

// HotCache manages hot data caching
type HotCache struct {
	cache      *cache.Cache
	hotKeys    map[string]*HotKeyStats
	mu         sync.RWMutex
	threshold  int64
	hotTTL     time.Duration
	coldTTL    time.Duration
	stopCh     chan struct{}
	wg         sync.WaitGroup
}

// HotKeyStats tracks statistics for a key
type HotKeyStats struct {
	Key         string
	AccessCount int64
	LastAccess  time.Time
	IsHot       bool
}

// NewHotCache creates a new hot data cache
func NewHotCache(c *cache.Cache, threshold int64, hotTTL, coldTTL time.Duration) *HotCache {
	hc := &HotCache{
		cache:     c,
		hotKeys:   make(map[string]*HotKeyStats),
		threshold: threshold,
		hotTTL:    hotTTL,
		coldTTL:   coldTTL,
		stopCh:    make(chan struct{}),
	}

	// Start hot key detection
	hc.wg.Add(1)
	go hc.detectHotKeys()

	return hc
}

// Get retrieves a value and tracks access
func (hc *HotCache) Get(key string) (interface{}, bool) {
	val, ok := hc.cache.Get(key)
	if ok {
		hc.trackAccess(key)
	}
	return val, ok
}

// Set stores a value with appropriate TTL based on hotness
func (hc *HotCache) Set(key string, value interface{}) {
	hc.mu.RLock()
	stats, exists := hc.hotKeys[key]
	hc.mu.RUnlock()

	ttl := hc.coldTTL
	if exists && stats.IsHot {
		ttl = hc.hotTTL
	}

	hc.cache.Set(key, value, ttl)
}

// trackAccess tracks key access
func (hc *HotCache) trackAccess(key string) {
	hc.mu.Lock()
	defer hc.mu.Unlock()

	stats, exists := hc.hotKeys[key]
	if !exists {
		stats = &HotKeyStats{Key: key}
		hc.hotKeys[key] = stats
	}

	atomic.AddInt64(&stats.AccessCount, 1)
	stats.LastAccess = time.Now()
}

// detectHotKeys periodically detects hot keys
func (hc *HotCache) detectHotKeys() {
	defer hc.wg.Done()
	ticker := time.NewTicker(10 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			hc.mu.Lock()
			for key, stats := range hc.hotKeys {
				count := atomic.LoadInt64(&stats.AccessCount)
				if count >= hc.threshold {
					if !stats.IsHot {
						stats.IsHot = true
						// Extend TTL for hot key
						if val, ok := hc.cache.Get(key); ok {
							hc.cache.Set(key, val, hc.hotTTL)
						}
					}
				} else {
					stats.IsHot = false
				}
				// Reset counter
				atomic.StoreInt64(&stats.AccessCount, 0)
			}
			hc.mu.Unlock()
		case <-hc.stopCh:
			return
		}
	}
}

// GetHotKeys returns all hot keys
func (hc *HotCache) GetHotKeys() []string {
	hc.mu.RLock()
	defer hc.mu.RUnlock()

	var hotKeys []string
	for key, stats := range hc.hotKeys {
		if stats.IsHot {
			hotKeys = append(hotKeys, key)
		}
	}
	return hotKeys
}

// Stop stops the hot cache
func (hc *HotCache) Stop() {
	close(hc.stopCh)
	hc.wg.Wait()
}

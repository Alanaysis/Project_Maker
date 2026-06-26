// Package cache implements an in-memory cache with multiple eviction policies.
//
// Caching Basics:
// A cache stores frequently accessed data in fast storage (memory) to reduce
// the need to fetch it from slower sources (database, network, disk).
// The core cache flow is:
//
//	Request → Cache Lookup → [Hit] Return → [Miss] Fetch from source → Cache result → Return
//
// Eviction Policies:
// When a cache is full, it must evict old entries. Common strategies:
//   - LRU (Least Recently Used): Evicts the least recently accessed item
//   - LFU (Least Frequently Used): Evicts the least frequently accessed item
//   - TTL (Time To Live): Entries expire after a set duration
package cache

import (
	"sync"
	"time"
)

// EvictionPolicy defines the cache eviction strategy.
type EvictionPolicy int

const (
	LRU EvictionPolicy = iota // Least Recently Used
	LFU                       // Least Frequently Used
	TTL                       // Time To Live
)

// Node represents a single cache node in the system.
// It manages an in-memory store with configurable eviction policy.
type Node struct {
	id            string
	policy        EvictionPolicy
	capacity      int
	items         map[string]*item
	stats         *Stats
	mu            sync.RWMutex
	clock         clock
	accessOrder   []string // For LRU: order of access (most recent at end)
	freqMap       map[string]int // For LFU: access frequency map
	minFreq       int          // For LFU: minimum frequency
	freqGroups    map[int][]string // For LFU: groups keyed by frequency
}

// item represents a cached entry with its value and expiration time.
type item struct {
	value     string
	createdAt time.Time
	expiresAt time.Time
}

// Stats tracks cache performance metrics.
type Stats struct {
	mu          sync.Mutex
	Gets        int
	Hits        int
	Misses      int
	Sets        int
	Deletes     int
	Evictions   int
	TotalItems  int
}

// HotKey represents a key that has been accessed frequently.
type HotKey struct {
	Key   string
	Count int
}

// clock is an interface for time operations, allowing testability.
type clock interface {
	Now() time.Time
}

// realClock uses actual system time.
type realClock struct{}

func (realClock) Now() time.Time { return time.Now() }

// NewNode creates a new cache node with the given ID, capacity, and eviction policy.
// Capacity of 0 means unlimited (no eviction).
func NewNode(id string, capacity int, policy EvictionPolicy) *Node {
	n := &Node{
		id:       id,
		policy:   policy,
		capacity: capacity,
		items:    make(map[string]*item),
		stats:    &Stats{},
		clock:    realClock{},
	}

	if policy == LFU {
		n.freqMap = make(map[string]int)
		n.freqGroups = make(map[int][]string)
		n.minFreq = 0
	}

	return n
}

// ID returns the node's identifier.
func (n *Node) ID() string {
	return n.id
}

// Policy returns the eviction policy of this node.
func (n *Node) Policy() EvictionPolicy {
	return n.policy
}

// Capacity returns the maximum number of items this cache can hold.
func (n *Node) Capacity() int {
	return n.capacity
}

// Size returns the current number of items in the cache.
func (n *Node) Size() int {
	n.mu.RLock()
	defer n.mu.RUnlock()
	return len(n.items)
}

// Get retrieves a value from the cache.
// Returns the value and true if found (cache hit), or empty string and false if not found (cache miss).
// For LRU policy, this updates the access order to mark the item as recently used.
// For LFU policy, this increments the access frequency counter.
func (n *Node) Get(key string) (string, bool) {
	n.mu.Lock()
	defer n.mu.Unlock()

	n.stats.mu.Lock()
	n.stats.Gets++
	n.stats.mu.Unlock()

	item, ok := n.items[key]
	if !ok {
		n.stats.mu.Lock()
		n.stats.Misses++
		n.stats.mu.Unlock()
		return "", false
	}

	// Check TTL expiry
	if n.policy == TTL && !item.expiresAt.IsZero() && n.clock.Now().After(item.expiresAt) {
		// Item has expired, remove it
		delete(n.items, key)
		n.stats.mu.Lock()
		n.stats.Misses++
		n.stats.Evictions++
		n.stats.TotalItems--
		n.stats.mu.Unlock()
		return "", false
	}

	n.stats.mu.Lock()
	n.stats.Hits++
	n.stats.mu.Unlock()

	// Update access tracking based on eviction policy
	switch n.policy {
	case LRU:
		n.updateLRUAccess(key)
	case LFU:
		n.updateLFUAccess(key)
	}

	return item.value, true
}

// Set adds or updates a key-value pair in the cache.
// If the cache is at capacity, it evicts an item based on the eviction policy.
func (n *Node) Set(key, value string) {
	n.SetWithTTL(key, value, 0)
}

// SetWithTTL adds or updates a key-value pair with a time-to-live duration.
// A TTL of 0 means the item never expires.
func (n *Node) SetWithTTL(key, value string, ttl time.Duration) {
	n.mu.Lock()
	defer n.mu.Unlock()

	n.stats.mu.Lock()
	n.stats.Sets++
	n.stats.mu.Unlock()

	// If key already exists, update it
	if _, ok := n.items[key]; ok {
		n.items[key].value = value
		n.items[key].createdAt = n.clock.Now()
		if ttl > 0 {
			n.items[key].expiresAt = n.clock.Now().Add(ttl)
		}
		switch n.policy {
		case LRU:
			n.updateLRUAccess(key)
		case LFU:
			n.updateLFUAccess(key)
		}
		return
	}

	// Evict if at capacity
	if n.capacity > 0 && len(n.items) >= n.capacity {
		n.evict()
	}

	// Add new item
	item := &item{
		value:     value,
		createdAt: n.clock.Now(),
	}
	if ttl > 0 {
		item.expiresAt = n.clock.Now().Add(ttl)
	}
	n.items[key] = item

	// Update access tracking
	switch n.policy {
	case LRU:
		n.accessOrder = append(n.accessOrder, key)
	case LFU:
		n.freqMap[key] = 1
		n.freqGroups[1] = append(n.freqGroups[1], key)
		n.minFreq = 1
	}

	n.stats.mu.Lock()
	n.stats.TotalItems++
	n.stats.mu.Unlock()
}

// Delete removes a key from the cache.
func (n *Node) Delete(key string) bool {
	n.mu.Lock()
	defer n.mu.Unlock()

	if _, ok := n.items[key]; !ok {
		return false
	}

	delete(n.items, key)
	n.stats.mu.Lock()
	n.stats.Deletes++
	n.stats.TotalItems--
	n.stats.mu.Unlock()

	// Clean up access tracking data structures
	switch n.policy {
	case LRU:
		n.removeFromAccessOrder(key)
	case LFU:
		n.removeFromFreqMap(key)
	}

	return true
}

// Stats returns a snapshot of the cache statistics.
func (n *Node) Stats() Stats {
	n.stats.mu.Lock()
	defer n.stats.mu.Unlock()
	return Stats{
		Gets:       n.stats.Gets,
		Hits:       n.stats.Hits,
		Misses:     n.stats.Misses,
		Sets:       n.stats.Sets,
		Deletes:    n.stats.Deletes,
		Evictions:  n.stats.Evictions,
		TotalItems: n.stats.TotalItems,
	}
}

// HotKeys returns keys that have been accessed more than minAccesses times.
// This helps identify "hot" keys that might benefit from dedicated caching.
func (n *Node) HotKeys(minAccesses int) []HotKey {
	n.mu.RLock()
	defer n.mu.RUnlock()

	var hotKeys []HotKey

	switch n.policy {
	case LFU:
		for key, count := range n.freqMap {
			if count >= minAccesses {
				hotKeys = append(hotKeys, HotKey{Key: key, Count: count})
			}
		}
	case LRU:
		// For LRU, we approximate hot keys by checking recent access order
		// In a production system, you'd track access counts
		half := len(n.accessOrder) / 2
		if half > 0 {
			recent := n.accessOrder[half:]
			seen := make(map[string]int)
			for _, key := range recent {
				seen[key]++
			}
			for key, count := range seen {
				if count >= minAccesses/10 { // Scale down for recent window
					hotKeys = append(hotKeys, HotKey{Key: key, Count: count})
				}
			}
		}
	}

	return hotKeys
}

// Warm pre-populates the cache with the given data.
// This is useful for bootstrapping the cache with known important data.
func (n *Node) Warm(data map[string]string) {
	for key, value := range data {
		n.Set(key, value)
	}
}

// evict removes the least appropriate item based on the eviction policy.
func (n *Node) evict() {
	var victim string

	switch n.policy {
	case LRU:
		victim = n.evictLRU()
	case LFU:
		victim = n.evictLFU()
	case TTL:
		victim = n.evictTTL()
	}

	if victim != "" {
		delete(n.items, victim)
		n.stats.mu.Lock()
		n.stats.Evictions++
		n.stats.TotalItems--
		n.stats.mu.Unlock()
	}
}

// evictLRU removes the least recently used item.
// LRU works on the principle that items not accessed recently are unlikely
// to be accessed in the near future.
func (n *Node) evictLRU() string {
	if len(n.accessOrder) == 0 {
		return ""
	}
	// First item in accessOrder is the least recently used
	victim := n.accessOrder[0]
	n.accessOrder = n.accessOrder[1:]
	return victim
}

// evictLFU removes the least frequently used item.
// LFU works on the principle that items with low access frequency are
// less valuable than those accessed often.
func (n *Node) evictLFU() string {
	if len(n.freqGroups) == 0 {
		return ""
	}

	// Find the group with minimum frequency
	minGroup := n.freqGroups[n.minFreq]
	if len(minGroup) == 0 {
		// Fallback: scan all groups
		return ""
	}

	// Remove the first item from the minimum frequency group
	victim := minGroup[0]
	n.freqGroups[n.minFreq] = minGroup[1:]
	if len(n.freqGroups[n.minFreq]) == 0 {
		delete(n.freqGroups, n.minFreq)
	}
	delete(n.freqMap, victim)

	// Clean up empty groups
	for freq := range n.freqGroups {
		if len(n.freqGroups[freq]) == 0 {
			delete(n.freqGroups, freq)
		}
	}

	return victim
}

// evictTTL removes the item with the earliest expiration time.
// This ensures expired items are cleaned up first.
func (n *Node) evictTTL() string {
	var victim string
	var earliest time.Time
	found := false

	for key, item := range n.items {
		if !item.expiresAt.IsZero() {
			if !found || item.expiresAt.Before(earliest) {
				victim = key
				earliest = item.expiresAt
				found = true
			}
		}
	}

	return victim
}

// updateLRUAccess marks a key as recently accessed by moving it to the end
// of the access order list.
func (n *Node) updateLRUAccess(key string) {
	// Remove from current position
	for i, k := range n.accessOrder {
		if k == key {
			n.accessOrder = append(n.accessOrder[:i], n.accessOrder[i+1:]...)
			break
		}
	}
	// Add to end (most recently used)
	n.accessOrder = append(n.accessOrder, key)
}

// removeFromAccessOrder removes a key from the access order tracking.
func (n *Node) removeFromAccessOrder(key string) {
	for i, k := range n.accessOrder {
		if k == key {
			n.accessOrder = append(n.accessOrder[:i], n.accessOrder[i+1:]...)
			break
		}
	}
}

// updateLFUAccess increments the frequency counter for a key and updates
// its position in the frequency groups.
func (n *Node) updateLFUAccess(key string) {
	oldFreq := n.freqMap[key]
	newFreq := oldFreq + 1
	n.freqMap[key] = newFreq

	// Remove from old frequency group
	oldGroup := n.freqGroups[oldFreq]
	for i, k := range oldGroup {
		if k == key {
			n.freqGroups[oldFreq] = append(oldGroup[:i], oldGroup[i+1:]...)
			break
		}
	}

	// Add to new frequency group
	n.freqGroups[newFreq] = append(n.freqGroups[newFreq], key)

	// Update minimum frequency if needed
	if oldFreq == n.minFreq && len(n.freqGroups[n.minFreq]) == 0 {
		delete(n.freqGroups, n.minFreq)
		n.minFreq = newFreq
	}
}

// removeFromFreqMap removes a key from the LFU frequency tracking.
func (n *Node) removeFromFreqMap(key string) {
	freq := n.freqMap[key]
	delete(n.freqMap, key)

	group := n.freqGroups[freq]
	for i, k := range group {
		if k == key {
			n.freqGroups[freq] = append(group[:i], group[i+1:]...)
			break
		}
	}

	if len(n.freqGroups[freq]) == 0 {
		delete(n.freqGroups, freq)
	}
}

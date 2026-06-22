package cache

import (
	"container/list"
	"sync"
)

// CacheItem represents an item stored in the cache.
type CacheItem struct {
	Key        string      // Cache key
	Value      []byte      // Cached content
	Headers    map[string][]string // HTTP headers
	StatusCode int         // HTTP status code
	Size       int64       // Size of the cached item
}

// entry is an internal structure used by the LRU cache.
type entry struct {
	key   string
	value *CacheItem
}

// LRUCache implements a thread-safe Least Recently Used cache.
// It uses a combination of a doubly-linked list and a hash map
// to achieve O(1) time complexity for both Get and Put operations.
//
// ⭐ Key Data Structure:
// - hash map: for O(1) lookup by key
// - doubly-linked list: for maintaining access order
//
// 💡 Why LRU?
// - LRU is a good approximation of the "optimal" caching algorithm
// - It's simple to implement and has predictable performance
// - Works well for many real-world access patterns
type LRUCache struct {
	capacity int                      // Maximum number of items
	size     int                      // Current number of items
	cache    map[string]*list.Element // Hash map for O(1) lookup
	list     *list.List               // Doubly-linked list for LRU order
	mutex    sync.RWMutex             // Read-write lock for thread safety
}

// NewLRUCache creates a new LRU cache with the specified capacity.
//
// Parameters:
//   - capacity: maximum number of items the cache can hold
//
// Returns:
//   - *LRUCache: a new LRU cache instance
func NewLRUCache(capacity int) *LRUCache {
	return &LRUCache{
		capacity: capacity,
		cache:    make(map[string]*list.Element),
		list:     list.New(),
	}
}

// Get retrieves an item from the cache.
// If the item is found, it is moved to the front of the LRU list.
//
// ⭐ Algorithm:
// 1. Acquire read lock
// 2. Look up the key in the hash map
// 3. If found, move the element to the front (most recently used)
// 4. Return the item and true, or nil and false
//
// Time Complexity: O(1)
func (c *LRUCache) Get(key string) (*CacheItem, bool) {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	if elem, ok := c.cache[key]; ok {
		// Move to front (most recently used)
		c.list.MoveToFront(elem)
		return elem.Value.(*entry).value, true
	}
	return nil, false
}

// Put adds or updates an item in the cache.
// If the cache is full, the least recently used item is evicted.
//
// ⭐ Algorithm:
// 1. Acquire write lock
// 2. If key exists, update value and move to front
// 3. If cache is full, remove the least recently used item (back of list)
// 4. Insert new item at the front
//
// Time Complexity: O(1)
func (c *LRUCache) Put(key string, item *CacheItem) {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	// If key already exists, update and move to front
	if elem, ok := c.cache[key]; ok {
		c.list.MoveToFront(elem)
		elem.Value.(*entry).value = item
		return
	}

	// If cache is full, remove the least recently used item
	if c.list.Len() >= c.capacity {
		c.removeOldest()
	}

	// Add new item to the front
	elem := c.list.PushFront(&entry{key, item})
	c.cache[key] = elem
	c.size++
}

// Delete removes an item from the cache.
//
// Time Complexity: O(1)
func (c *LRUCache) Delete(key string) {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	if elem, ok := c.cache[key]; ok {
		c.removeElement(elem)
	}
}

// Clear removes all items from the cache.
func (c *LRUCache) Clear() {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	c.cache = make(map[string]*list.Element)
	c.list.Init()
	c.size = 0
}

// Len returns the current number of items in the cache.
func (c *LRUCache) Len() int {
	c.mutex.RLock()
	defer c.mutex.RUnlock()

	return c.list.Len()
}

// Capacity returns the maximum capacity of the cache.
func (c *LRUCache) Capacity() int {
	return c.capacity
}

// Keys returns all keys in the cache (for debugging/testing).
func (c *LRUCache) Keys() []string {
	c.mutex.RLock()
	defer c.mutex.RUnlock()

	keys := make([]string, 0, c.list.Len())
	for elem := c.list.Front(); elem != nil; elem = elem.Next() {
		keys = append(keys, elem.Value.(*entry).key)
	}
	return keys
}

// removeOldest removes the least recently used item (back of list).
// Must be called with write lock held.
func (c *LRUCache) removeOldest() {
	if elem := c.list.Back(); elem != nil {
		c.removeElement(elem)
	}
}

// removeElement removes a specific element from the cache.
// Must be called with write lock held.
func (c *LRUCache) removeElement(elem *list.Element) {
	c.list.Remove(elem)
	delete(c.cache, elem.Value.(*entry).key)
	c.size--
}
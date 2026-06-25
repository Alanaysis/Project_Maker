package cache

import (
	"container/heap"
	"sync"
	"time"
)

// EvictionPolicy defines the cache eviction strategy
type EvictionPolicy interface {
	// Add adds an item to the eviction tracker
	Add(key string)
	// Remove removes an item from the eviction tracker
	Remove(key string)
	// Access records an access to the item
	Access(key string)
	// Evict returns the key to evict
	Evict() string
	// Len returns the number of tracked items
	Len() int
}

// ============ LRU Eviction ============

// LRUPolicy implements Least Recently Used eviction
type LRUPolicy struct {
	mu       sync.Mutex
	items    map[string]*lruItem
	head     *lruItem
	tail     *lruItem
	capacity int
}

type lruItem struct {
	key  string
	prev *lruItem
	next *lruItem
}

// NewLRUPolicy creates a new LRU eviction policy
func NewLRUPolicy() *LRUPolicy {
	head := &lruItem{}
	tail := &lruItem{}
	head.next = tail
	tail.prev = head
	return &LRUPolicy{
		items: make(map[string]*lruItem),
		head:  head,
		tail:  tail,
	}
}

func (l *LRUPolicy) Add(key string) {
	l.mu.Lock()
	defer l.mu.Unlock()
	if _, exists := l.items[key]; exists {
		l.moveToFront(key)
		return
	}
	item := &lruItem{key: key}
	l.items[key] = item
	l.addToFront(item)
}

func (l *LRUPolicy) Remove(key string) {
	l.mu.Lock()
	defer l.mu.Unlock()
	if item, exists := l.items[key]; exists {
		l.removeItem(item)
		delete(l.items, key)
	}
}

func (l *LRUPolicy) Access(key string) {
	l.mu.Lock()
	defer l.mu.Unlock()
	l.moveToFront(key)
}

func (l *LRUPolicy) Evict() string {
	l.mu.Lock()
	defer l.mu.Unlock()
	if l.tail.prev == l.head {
		return ""
	}
	item := l.tail.prev
	l.removeItem(item)
	delete(l.items, item.key)
	return item.key
}

func (l *LRUPolicy) Len() int {
	l.mu.Lock()
	defer l.mu.Unlock()
	return len(l.items)
}

func (l *LRUPolicy) addToFront(item *lruItem) {
	item.next = l.head.next
	item.prev = l.head
	l.head.next.prev = item
	l.head.next = item
}

func (l *LRUPolicy) removeItem(item *lruItem) {
	item.prev.next = item.next
	item.next.prev = item.prev
}

func (l *LRUPolicy) moveToFront(key string) {
	if item, exists := l.items[key]; exists {
		l.removeItem(item)
		l.addToFront(item)
	}
}

// ============ LFU Eviction ============

// LFUPolicy implements Least Frequently Used eviction
type LFUPolicy struct {
	mu          sync.Mutex
	freq        map[string]int64
	minFreq     int64
	freqBuckets map[int64]map[string]struct{}
}

// NewLFUPolicy creates a new LFU eviction policy
func NewLFUPolicy() *LFUPolicy {
	return &LFUPolicy{
		freq:        make(map[string]int64),
		freqBuckets: make(map[int64]map[string]struct{}),
		minFreq:     0,
	}
}

func (l *LFUPolicy) Add(key string) {
	l.mu.Lock()
	defer l.mu.Unlock()
	if _, exists := l.freq[key]; exists {
		return
	}
	l.freq[key] = 1
	l.addToBucket(key, 1)
	l.minFreq = 1
}

func (l *LFUPolicy) Remove(key string) {
	l.mu.Lock()
	defer l.mu.Unlock()
	if freq, exists := l.freq[key]; exists {
		l.removeFromBucket(key, freq)
		delete(l.freq, key)
	}
}

func (l *LFUPolicy) Access(key string) {
	l.mu.Lock()
	defer l.mu.Unlock()
	oldFreq := l.freq[key]
	newFreq := oldFreq + 1
	l.freq[key] = newFreq
	l.removeFromBucket(key, oldFreq)
	l.addToBucket(key, newFreq)
	if l.minFreq == oldFreq && len(l.freqBuckets[oldFreq]) == 0 {
		l.minFreq = newFreq
	}
}

func (l *LFUPolicy) Evict() string {
	l.mu.Lock()
	defer l.mu.Unlock()
	bucket := l.freqBuckets[l.minFreq]
	if len(bucket) == 0 {
		return ""
	}
	for key := range bucket {
		l.removeFromBucket(key, l.minFreq)
		delete(l.freq, key)
		return key
	}
	return ""
}

func (l *LFUPolicy) Len() int {
	l.mu.Lock()
	defer l.mu.Unlock()
	return len(l.freq)
}

func (l *LFUPolicy) addToBucket(key string, freq int64) {
	if l.freqBuckets[freq] == nil {
		l.freqBuckets[freq] = make(map[string]struct{})
	}
	l.freqBuckets[freq][key] = struct{}{}
}

func (l *LFUPolicy) removeFromBucket(key string, freq int64) {
	if bucket, exists := l.freqBuckets[freq]; exists {
		delete(bucket, key)
		if len(bucket) == 0 {
			delete(l.freqBuckets, freq)
		}
	}
}

// ============ FIFO Eviction ============

// FIFOPolicy implements First In First Out eviction
type FIFOPolicy struct {
	mu    sync.Mutex
	queue []string
	index map[string]int
}

// NewFIFOPolicy creates a new FIFO eviction policy
func NewFIFOPolicy() *FIFOPolicy {
	return &FIFOPolicy{
		queue: make([]string, 0),
		index: make(map[string]int),
	}
}

func (f *FIFOPolicy) Add(key string) {
	f.mu.Lock()
	defer f.mu.Unlock()
	if _, exists := f.index[key]; exists {
		return
	}
	f.index[key] = len(f.queue)
	f.queue = append(f.queue, key)
}

func (f *FIFOPolicy) Remove(key string) {
	f.mu.Lock()
	defer f.mu.Unlock()
	if idx, exists := f.index[key]; exists {
		f.queue = append(f.queue[:idx], f.queue[idx+1:]...)
		delete(f.index, key)
		// Rebuild index
		for i := idx; i < len(f.queue); i++ {
			f.index[f.queue[i]] = i
		}
	}
}

func (f *FIFOPolicy) Access(key string) {
	// FIFO doesn't care about access
}

func (f *FIFOPolicy) Evict() string {
	f.mu.Lock()
	defer f.mu.Unlock()
	if len(f.queue) == 0 {
		return ""
	}
	key := f.queue[0]
	f.queue = f.queue[1:]
	delete(f.index, key)
	// Rebuild index
	for i := 0; i < len(f.queue); i++ {
		f.index[f.queue[i]] = i
	}
	return key
}

func (f *FIFOPolicy) Len() int {
	f.mu.Lock()
	defer f.mu.Unlock()
	return len(f.queue)
}

// ============ TTL Eviction ============

// TTLItem represents an item with TTL
type TTLItem struct {
	key       string
	expiresAt time.Time
}

// TTLHeap implements heap.Interface for TTL items
type TTLHeap []TTLItem

func (h TTLHeap) Len() int           { return len(h) }
func (h TTLHeap) Less(i, j int) bool { return h[i].expiresAt.Before(h[j].expiresAt) }
func (h TTLHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }

func (h *TTLHeap) Push(x interface{}) {
	*h = append(*h, x.(TTLItem))
}

func (h *TTLHeap) Pop() interface{} {
	old := *h
	n := len(old)
	item := old[n-1]
	*h = old[:n-1]
	return item
}

// TTLPolicy implements Time To Live eviction
type TTLPolicy struct {
	mu      sync.Mutex
	heap    *TTLHeap
	ttlMap  map[string]time.Duration
	itemMap map[string]*TTLItem
	ttl     time.Duration
}

// NewTTLPolicy creates a new TTL eviction policy
func NewTTLPolicy(defaultTTL time.Duration) *TTLPolicy {
	h := &TTLHeap{}
	heap.Init(h)
	return &TTLPolicy{
		heap:    h,
		ttlMap:  make(map[string]time.Duration),
		itemMap: make(map[string]*TTLItem),
		ttl:     defaultTTL,
	}
}

func (t *TTLPolicy) Add(key string) {
	t.mu.Lock()
	defer t.mu.Unlock()
	ttl := t.ttl
	if existingTTL, exists := t.ttlMap[key]; exists {
		ttl = existingTTL
	}
	item := TTLItem{
		key:       key,
		expiresAt: time.Now().Add(ttl),
	}
	heap.Push(t.heap, item)
	t.itemMap[key] = &item
}

func (t *TTLPolicy) AddWithTTL(key string, ttl time.Duration) {
	t.mu.Lock()
	defer t.mu.Unlock()
	t.ttlMap[key] = ttl
	item := TTLItem{
		key:       key,
		expiresAt: time.Now().Add(ttl),
	}
	heap.Push(t.heap, item)
	t.itemMap[key] = &item
}

func (t *TTLPolicy) Remove(key string) {
	t.mu.Lock()
	defer t.mu.Unlock()
	delete(t.ttlMap, key)
	delete(t.itemMap, key)
	// Note: We can't efficiently remove from heap, will be cleaned up on Evict
}

func (t *TTLPolicy) Access(key string) {
	// TTL doesn't change on access
}

func (t *TTLPolicy) Evict() string {
	t.mu.Lock()
	defer t.mu.Unlock()
	now := time.Now()
	for t.heap.Len() > 0 {
		item := heap.Pop(t.heap).(TTLItem)
		delete(t.itemMap, item.key)
		if item.expiresAt.Before(now) {
			return item.key
		}
		// Not expired yet, push back
		heap.Push(t.heap, item)
		t.itemMap[item.key] = &item
		break
	}
	// If no expired items, evict the oldest
	if t.heap.Len() > 0 {
		item := heap.Pop(t.heap).(TTLItem)
		delete(t.itemMap, item.key)
		return item.key
	}
	return ""
}

func (t *TTLPolicy) Len() int {
	t.mu.Lock()
	defer t.mu.Unlock()
	return t.heap.Len()
}

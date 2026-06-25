package problem

import (
	"fmt"
	"sync"
	"time"

	"github.com/distributed-cache/internal/cache"
)

// CacheProblemSolver provides solutions for common cache problems
type CacheProblemSolver struct {
	cache      *cache.Cache
	bloom      *BloomFilter
	singleFlight map[string]*flight
	mu         sync.Mutex
	nullCache  map[string]bool
}

// NewCacheProblemSolver creates a new problem solver
func NewCacheProblemSolver(c *cache.Cache) *CacheProblemSolver {
	return &CacheProblemSolver{
		cache:        c,
		bloom:        NewBloomFilter(10000, 0.01),
		singleFlight: make(map[string]*flight),
		nullCache:    make(map[string]bool),
	}
}

// ============ Cache Penetration (缓存穿透) ============

// Cache Penetration: Querying for data that doesn't exist in cache or storage
// Solution: Bloom Filter + Cache Null Values

// BloomFilter is a probabilistic data structure
type BloomFilter struct {
	bits    []bool
	size    uint
	hashNum uint
}

// NewBloomFilter creates a new bloom filter
func NewBloomFilter(expectedItems int, fpRate float64) *BloomFilter {
	// Calculate optimal size and hash count
	size := uint(-float64(expectedItems) * 0.01 / (0.693147 * 0.693147))
	if size < 1024 {
		size = 1024
	}
	hashNum := uint(float64(size) / float64(expectedItems) * 0.693147)
	if hashNum < 1 {
		hashNum = 1
	}
	return &BloomFilter{
		bits:    make([]bool, size),
		size:    size,
		hashNum: hashNum,
	}
}

// Add adds an item to the bloom filter
func (bf *BloomFilter) Add(key string) {
	for i := uint(0); i < bf.hashNum; i++ {
		idx := bf.hash(key, i) % bf.size
		bf.bits[idx] = true
	}
}

// Contains checks if an item might be in the set
func (bf *BloomFilter) Contains(key string) bool {
	for i := uint(0); i < bf.hashNum; i++ {
		idx := bf.hash(key, i) % bf.size
		if !bf.bits[idx] {
			return false
		}
	}
	return true
}

func (bf *BloomFilter) hash(key string, seed uint) uint {
	var hash uint = 5381
	for i := 0; i < len(key); i++ {
		hash = ((hash << 5) + hash) + uint(key[i]) + seed
	}
	return hash
}

// PreventPenetrationWithBloom uses bloom filter to prevent cache penetration
func (cps *CacheProblemSolver) PreventPenetrationWithBloom(key string, loader func(string) (interface{}, error)) (interface{}, error) {
	// Check bloom filter first
	if !cps.bloom.Contains(key) {
		return nil, fmt.Errorf("key not found: %s", key)
	}

	// Try cache
	if val, ok := cps.cache.Get(key); ok {
		return val, nil
	}

	// Load from storage
	val, err := loader(key)
	if err != nil {
		return nil, err
	}

	// Add to bloom filter and cache
	cps.bloom.Add(key)
	cps.cache.Set(key, val, 0)
	return val, nil
}

// PreventPenetrationWithNullCache caches null values to prevent penetration
func (cps *CacheProblemSolver) PreventPenetrationWithNullCache(key string, ttl time.Duration, loader func(string) (interface{}, error)) (interface{}, error) {
	// Check if we know this key is null
	if cps.nullCache[key] {
		return nil, fmt.Errorf("key not found (cached null): %s", key)
	}

	// Try cache
	if val, ok := cps.cache.Get(key); ok {
		return val, nil
	}

	// Load from storage
	val, err := loader(key)
	if err != nil {
		// Cache null value
		cps.nullCache[key] = true
		cps.cache.Set(key, nil, ttl)
		return nil, err
	}

	cps.cache.Set(key, val, ttl)
	return val, nil
}

// ============ Cache Breakdown (缓存击穿) ============

// Cache Breakdown: Hot key expires, many requests hit storage simultaneously
// Solution: Single Flight / Mutex

type flight struct {
	done chan struct{}
	val  interface{}
	err  error
}

// PreventBreakdownWithSingleFlight uses single flight to prevent cache breakdown
func (cps *CacheProblemSolver) PreventBreakdownWithSingleFlight(key string, loader func(string) (interface{}, error)) (interface{}, error) {
	// Try cache first
	if val, ok := cps.cache.Get(key); ok {
		return val, nil
	}

	// Single flight
	cps.mu.Lock()
	if f, ok := cps.singleFlight[key]; ok {
		cps.mu.Unlock()
		<-f.done
		return f.val, f.err
	}

	f := &flight{done: make(chan struct{})}
	cps.singleFlight[key] = f
	cps.mu.Unlock()

	// Load from storage
	val, err := loader(key)
	if err != nil {
		f.err = err
		cps.mu.Lock()
		delete(cps.singleFlight, key)
		cps.mu.Unlock()
		close(f.done)
		return nil, err
	}

	// Store in cache
	cps.cache.Set(key, val, 0)
	f.val = val

	cps.mu.Lock()
	delete(cps.singleFlight, key)
	cps.mu.Unlock()
	close(f.done)

	return val, nil
}

// PreventBreakdownWithMutex uses mutex to prevent cache breakdown
func (cps *CacheProblemSolver) PreventBreakdownWithMutex(key string, mu *sync.Mutex, loader func(string) (interface{}, error)) (interface{}, error) {
	// Try cache first
	if val, ok := cps.cache.Get(key); ok {
		return val, nil
	}

	// Acquire lock
	mu.Lock()
	defer mu.Unlock()

	// Double check
	if val, ok := cps.cache.Get(key); ok {
		return val, nil
	}

	// Load from storage
	val, err := loader(key)
	if err != nil {
		return nil, err
	}

	cps.cache.Set(key, val, 0)
	return val, nil
}

// ============ Cache Avalanche (缓存雪崩) ============

// Cache Avalanche: Many keys expire at the same time
// Solution: Random TTL + Multi-level Cache

// RandomTTL adds jitter to TTL to prevent avalanche
func RandomTTL(baseTTL, jitter time.Duration) time.Duration {
	if jitter <= 0 {
		return baseTTL
	}
	// Add random jitter: baseTTL ± jitter
	jitterRange := int64(jitter) * 2
	randomJitter := time.Duration(jitterRange/2 - int64(jitter))
	return baseTTL + randomJitter
}

// PreventAvalancheWithRandomTTL sets cache with random TTL
func (cps *CacheProblemSolver) PreventAvalancheWithRandomTTL(key string, value interface{}, baseTTL, jitter time.Duration) {
	ttl := RandomTTL(baseTTL, jitter)
	cps.cache.Set(key, value, ttl)
}

// MultiLevelCache implements a multi-level cache to prevent avalanche
type MultiLevelCache struct {
	l1      *cache.Cache // Fast, small
	l2      *cache.Cache // Slower, larger
	loader  func(string) (interface{}, error)
}

// NewMultiLevelCache creates a new multi-level cache
func NewMultiLevelCache(l1, l2 *cache.Cache, loader func(string) (interface{}, error)) *MultiLevelCache {
	return &MultiLevelCache{
		l1:     l1,
		l2:     l2,
		loader: loader,
	}
}

func (mlc *MultiLevelCache) Get(key string) (interface{}, error) {
	// Try L1
	if val, ok := mlc.l1.Get(key); ok {
		return val, nil
	}

	// Try L2
	if val, ok := mlc.l2.Get(key); ok {
		// Promote to L1
		mlc.l1.Set(key, val, 0)
		return val, nil
	}

	// Load from storage
	val, err := mlc.loader(key)
	if err != nil {
		return nil, err
	}

	// Store in both levels
	mlc.l1.Set(key, val, 0)
	mlc.l2.Set(key, val, 0)
	return val, nil
}

func (mlc *MultiLevelCache) Set(key string, value interface{}, ttl time.Duration) {
	mlc.l1.Set(key, value, ttl)
	mlc.l2.Set(key, value, ttl)
}

func (mlc *MultiLevelCache) Delete(key string) {
	mlc.l1.Delete(key)
	mlc.l2.Delete(key)
}

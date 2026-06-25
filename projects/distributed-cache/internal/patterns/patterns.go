package patterns

import (
	"fmt"
	"sync"
	"time"

	"github.com/distributed-cache/internal/cache"
)

// DataLoader loads data from the underlying storage
type DataLoader func(key string) (interface{}, error)

// DataWriter writes data to the underlying storage
type DataWriter func(key string, value interface{}) error

// CachePattern defines the cache pattern interface
type CachePattern interface {
	Get(key string) (interface{}, error)
	Set(key string, value interface{}, ttl time.Duration) error
	Delete(key string) error
}

// ============ Cache-Aside Pattern ============

// CacheAside implements the Cache-Aside pattern
// Application manages the cache explicitly
type CacheAside struct {
	cache    *cache.Cache
	loader   DataLoader
	writer   DataWriter
	mu       sync.Mutex
	flybacks map[string]*singleFlight
}

type singleFlight struct {
	done chan struct{}
	val  interface{}
	err  error
}

// NewCacheAside creates a new Cache-Aside pattern
func NewCacheAside(c *cache.Cache, loader DataLoader, writer DataWriter) *CacheAside {
	return &CacheAside{
		cache:    c,
		loader:   loader,
		writer:   writer,
		flybacks: make(map[string]*singleFlight),
	}
}

func (ca *CacheAside) Get(key string) (interface{}, error) {
	// Try cache first
	if val, ok := ca.cache.Get(key); ok {
		return val, nil
	}

	// Single flight to prevent cache stampede
	ca.mu.Lock()
	if flight, ok := ca.flybacks[key]; ok {
		ca.mu.Unlock()
		<-flight.done
		return flight.val, flight.err
	}

	flight := &singleFlight{done: make(chan struct{})}
	ca.flybacks[key] = flight
	ca.mu.Unlock()

	// Load from storage
	val, err := ca.loader(key)
	if err != nil {
		ca.mu.Lock()
		delete(ca.flybacks, key)
		ca.mu.Unlock()
		close(flight.done)
		return nil, err
	}

	// Store in cache
	ca.cache.Set(key, val, 0)
	flight.val = val

	ca.mu.Lock()
	delete(ca.flybacks, key)
	ca.mu.Unlock()
	close(flight.done)

	return val, nil
}

func (ca *CacheAside) Set(key string, value interface{}, ttl time.Duration) error {
	// Write to storage first
	if ca.writer != nil {
		if err := ca.writer(key, value); err != nil {
			return err
		}
	}
	// Then update cache
	ca.cache.Set(key, value, ttl)
	return nil
}

func (ca *CacheAside) Delete(key string) error {
	// Delete from cache
	ca.cache.Delete(key)
	return nil
}

// ============ Read-Through Pattern ============

// ReadThrough implements the Read-Through pattern
// Cache automatically loads data on miss
type ReadThrough struct {
	cache  *cache.Cache
	loader DataLoader
}

// NewReadThrough creates a new Read-Through pattern
func NewReadThrough(c *cache.Cache, loader DataLoader) *ReadThrough {
	return &ReadThrough{
		cache:  c,
		loader: loader,
	}
}

func (rt *ReadThrough) Get(key string) (interface{}, error) {
	// Try cache first
	if val, ok := rt.cache.Get(key); ok {
		return val, nil
	}

	// Auto-load on miss
	val, err := rt.loader(key)
	if err != nil {
		return nil, err
	}

	// Store in cache
	rt.cache.Set(key, val, 0)
	return val, nil
}

func (rt *ReadThrough) Set(key string, value interface{}, ttl time.Duration) error {
	rt.cache.Set(key, value, ttl)
	return nil
}

func (rt *ReadThrough) Delete(key string) error {
	rt.cache.Delete(key)
	return nil
}

// ============ Write-Through Pattern ============

// WriteThrough implements the Write-Through pattern
// Writes go to both cache and storage synchronously
type WriteThrough struct {
	cache  *cache.Cache
	writer DataWriter
	loader DataLoader
}

// NewWriteThrough creates a new Write-Through pattern
func NewWriteThrough(c *cache.Cache, writer DataWriter, loader DataLoader) *WriteThrough {
	return &WriteThrough{
		cache:  c,
		writer: writer,
		loader: loader,
	}
}

func (wt *WriteThrough) Get(key string) (interface{}, error) {
	// Try cache first
	if val, ok := wt.cache.Get(key); ok {
		return val, nil
	}

	// Load from storage
	if wt.loader != nil {
		val, err := wt.loader(key)
		if err != nil {
			return nil, err
		}
		wt.cache.Set(key, val, 0)
		return val, nil
	}

	return nil, fmt.Errorf("key not found: %s", key)
}

func (wt *WriteThrough) Set(key string, value interface{}, ttl time.Duration) error {
	// Write to storage first
	if wt.writer != nil {
		if err := wt.writer(key, value); err != nil {
			return err
		}
	}
	// Then write to cache
	wt.cache.Set(key, value, ttl)
	return nil
}

func (wt *WriteThrough) Delete(key string) error {
	wt.cache.Delete(key)
	return nil
}

// ============ Write-Behind Pattern ============

// WriteBehind implements the Write-Behind (Write-Back) pattern
// Writes go to cache immediately, then asynchronously to storage
type WriteBehind struct {
	cache     *cache.Cache
	writer    DataWriter
	loader    DataLoader
	writeCh   chan writeRequest
	batchSize int
	flushInt  time.Duration
	stopCh    chan struct{}
	wg        sync.WaitGroup
}

type writeRequest struct {
	key   string
	value interface{}
}

// NewWriteBehind creates a new Write-Behind pattern
func NewWriteBehind(c *cache.Cache, writer DataWriter, loader DataLoader, batchSize int, flushInt time.Duration) *WriteBehind {
	if batchSize <= 0 {
		batchSize = 100
	}
	if flushInt <= 0 {
		flushInt = 5 * time.Second
	}

	wb := &WriteBehind{
		cache:     c,
		writer:    writer,
		loader:    loader,
		writeCh:   make(chan writeRequest, 1000),
		batchSize: batchSize,
		flushInt:  flushInt,
		stopCh:    make(chan struct{}),
	}

	wb.wg.Add(1)
	go wb.flushLoop()

	return wb
}

func (wb *WriteBehind) Get(key string) (interface{}, error) {
	// Try cache first
	if val, ok := wb.cache.Get(key); ok {
		return val, nil
	}

	// Load from storage
	if wb.loader != nil {
		val, err := wb.loader(key)
		if err != nil {
			return nil, err
		}
		wb.cache.Set(key, val, 0)
		return val, nil
	}

	return nil, fmt.Errorf("key not found: %s", key)
}

func (wb *WriteBehind) Set(key string, value interface{}, ttl time.Duration) error {
	// Write to cache immediately
	wb.cache.Set(key, value, ttl)

	// Queue async write to storage
	select {
	case wb.writeCh <- writeRequest{key: key, value: value}:
	default:
		// Channel full, drop oldest or log warning
	}

	return nil
}

func (wb *WriteBehind) Delete(key string) error {
	wb.cache.Delete(key)
	return nil
}

func (wb *WriteBehind) flushLoop() {
	defer wb.wg.Done()
	ticker := time.NewTicker(wb.flushInt)
	defer ticker.Stop()

	batch := make([]writeRequest, 0, wb.batchSize)

	for {
		select {
		case req := <-wb.writeCh:
			batch = append(batch, req)
			if len(batch) >= wb.batchSize {
				wb.flush(batch)
				batch = batch[:0]
			}
		case <-ticker.C:
			if len(batch) > 0 {
				wb.flush(batch)
				batch = batch[:0]
			}
		case <-wb.stopCh:
			// Flush remaining
			if len(batch) > 0 {
				wb.flush(batch)
			}
			return
		}
	}
}

func (wb *WriteBehind) flush(batch []writeRequest) {
	for _, req := range batch {
		if wb.writer != nil {
			wb.writer(req.key, req.value)
		}
	}
}

// Stop stops the write-behind goroutine
func (wb *WriteBehind) Stop() {
	close(wb.stopCh)
	wb.wg.Wait()
}

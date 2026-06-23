package gc

import (
	"log"
	"sync"
	"time"

	"mvcc/internal/store"
	"mvcc/internal/transaction"
)

// GarbageCollector removes old versions that are no longer visible to any active transaction
type GarbageCollector struct {
	store    *store.Store
	txMgr    *transaction.TransactionManager
	interval time.Duration
	stopCh   chan struct{}
	wg       sync.WaitGroup
	stats    GCStats
	mu       sync.RWMutex
}

// GCStats tracks garbage collection statistics
type GCStats struct {
	TotalRuns      uint64
	TotalRemoved   uint64
	LastRunTime    time.Time
	LastRunRemoved int
	LastRunDuration time.Duration
}

// NewGarbageCollector creates a new garbage collector
func NewGarbageCollector(s *store.Store, txMgr *transaction.TransactionManager, interval time.Duration) *GarbageCollector {
	return &GarbageCollector{
		store:    s,
		txMgr:    txMgr,
		interval: interval,
		stopCh:   make(chan struct{}),
	}
}

// Start begins the garbage collection loop in a background goroutine
func (gc *GarbageCollector) Start() {
	gc.wg.Add(1)
	go func() {
		defer gc.wg.Done()
		ticker := time.NewTicker(gc.interval)
		defer ticker.Stop()

		for {
			select {
			case <-ticker.C:
				gc.Run()
			case <-gc.stopCh:
				return
			}
		}
	}()
	log.Printf("GC started with interval %v", gc.interval)
}

// Stop stops the garbage collector
func (gc *GarbageCollector) Stop() {
	close(gc.stopCh)
	gc.wg.Wait()
	log.Println("GC stopped")
}

// Run performs a single garbage collection cycle
func (gc *GarbageCollector) Run() int {
	start := time.Now()

	// Get the minimum active timestamp - versions older than this can be GC'd
	minActiveTS := gc.txMgr.MinActiveTimestamp()

	// Remove old versions
	removed := gc.store.RemoveVersions(minActiveTS)

	duration := time.Since(start)

	// Update stats
	gc.mu.Lock()
	gc.stats.TotalRuns++
	gc.stats.TotalRemoved += uint64(removed)
	gc.stats.LastRunTime = start
	gc.stats.LastRunRemoved = removed
	gc.stats.LastRunDuration = duration
	gc.mu.Unlock()

	if removed > 0 {
		log.Printf("GC run completed: removed %d versions in %v (minActiveTS=%d)", removed, duration, minActiveTS)
	}

	return removed
}

// Stats returns a copy of the current GC statistics
func (gc *GarbageCollector) Stats() GCStats {
	gc.mu.RLock()
	defer gc.mu.RUnlock()
	return gc.stats
}

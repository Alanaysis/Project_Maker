package redis

import (
	"context"
	"sync"
	"time"
)

// ExtensibleLock is a lock that supports TTL extension.
type ExtensibleLock interface {
	Extend(ctx context.Context, ttl time.Duration) (bool, error)
}

// Watchdog automatically extends a lock's TTL while business logic is running.
type Watchdog struct {
	lock     ExtensibleLock
	ttl      time.Duration
	interval time.Duration
	stopCh   chan struct{}
	done     chan struct{}
	mu       sync.Mutex
	running  bool
}

// NewWatchdog creates a new Watchdog for automatic lock renewal.
// ttl is the lock's TTL, interval is how often to renew (typically ttl/3).
func NewWatchdog(lock ExtensibleLock, ttl time.Duration, interval time.Duration) *Watchdog {
	return &Watchdog{
		lock:     lock,
		ttl:      ttl,
		interval: interval,
		stopCh:   make(chan struct{}),
		done:     make(chan struct{}),
	}
}

// Start begins the watchdog goroutine.
func (w *Watchdog) Start(ctx context.Context) {
	w.mu.Lock()
	if w.running {
		w.mu.Unlock()
		return
	}
	w.running = true
	w.stopCh = make(chan struct{})
	w.done = make(chan struct{})
	w.mu.Unlock()

	go w.run(ctx)
}

// Stop stops the watchdog goroutine.
func (w *Watchdog) Stop() {
	w.mu.Lock()
	if !w.running {
		w.mu.Unlock()
		return
	}
	w.running = false
	close(w.stopCh)
	w.mu.Unlock()

	<-w.done
}

// run is the main watchdog loop.
func (w *Watchdog) run(ctx context.Context) {
	defer close(w.done)

	ticker := time.NewTicker(w.interval)
	defer ticker.Stop()

	for {
		select {
		case <-w.stopCh:
			return
		case <-ctx.Done():
			return
		case <-ticker.C:
			_, err := w.lock.Extend(ctx, w.ttl)
			if err != nil {
				// Log error but continue trying
				// In production, use proper logging
				continue
			}
		}
	}
}

// IsRunning returns whether the watchdog is currently running.
func (w *Watchdog) IsRunning() bool {
	w.mu.Lock()
	defer w.mu.Unlock()
	return w.running
}

package tests

import (
	"context"
	"sync"
	"testing"
	"time"

	"github.com/redis/go-redis/v9"
	"github.com/alicebob/miniredis/v2"
)

// Watchdog provides automatic lock renewal
type Watchdog struct {
	lock     *RedisLock
	interval time.Duration
	stopCh   chan struct{}
	doneCh   chan struct{}
	running  bool
	mu       sync.Mutex
}

// NewWatchdog creates a new Watchdog instance
func NewWatchdog(lock *RedisLock, interval time.Duration) *Watchdog {
	return &Watchdog{
		lock:     lock,
		interval: interval,
	}
}

// Start begins the watchdog goroutine
func (w *Watchdog) Start(ctx context.Context) {
	w.mu.Lock()
	if w.running {
		w.mu.Unlock()
		return
	}
	w.running = true
	w.stopCh = make(chan struct{})
	w.doneCh = make(chan struct{})
	w.mu.Unlock()

	go w.run(ctx)
}

// Stop stops the watchdog goroutine
func (w *Watchdog) Stop() {
	w.mu.Lock()
	if !w.running {
		w.mu.Unlock()
		return
	}
	w.running = false
	close(w.stopCh)
	w.mu.Unlock()

	<-w.doneCh
}

func (w *Watchdog) run(ctx context.Context) {
	defer close(w.doneCh)

	ticker := time.NewTicker(w.interval)
	defer ticker.Stop()

	for {
		select {
		case <-w.stopCh:
			return
		case <-ticker.C:
			ttl, err := w.lock.TTL(ctx)
			if err != nil || ttl <= 0 {
				return
			}

			// Renew lock
			renewScript := `
				if redis.call("GET", KEYS[1]) == ARGV[1] then
					return redis.call("EXPIRE", KEYS[1], ARGV[2])
				else
					return 0
				end
			`
			w.lock.client.Eval(ctx, renewScript,
				[]string{w.lock.key}, w.lock.value, int(w.lock.ttl.Seconds()))
		}
	}
}

func TestWatchdog_BasicRenewal(t *testing.T) {
	s := miniredis.RunT(t)
	client := redis.NewClient(&redis.Options{Addr: s.Addr()})
	defer client.Close()

	ctx := context.Background()
	lock := NewRedisLock(client, "watchdog-resource", "id-1", 2*time.Second)

	// Acquire lock
	acquired, _ := lock.Acquire(ctx)
	if !acquired {
		t.Fatal("expected to acquire lock")
	}

	// Start watchdog
	wd := NewWatchdog(lock, 500*time.Millisecond)
	wd.Start(ctx)
	defer wd.Stop()

	// Wait for several renewal cycles
	time.Sleep(3 * time.Second)

	// Lock should still be held
	ttl, _ := lock.TTL(ctx)
	if ttl <= 0 {
		t.Error("expected lock to be renewed by watchdog")
	}
}

func TestWatchdog_Stop(t *testing.T) {
	s := miniredis.RunT(t)
	client := redis.NewClient(&redis.Options{Addr: s.Addr()})
	defer client.Close()

	ctx := context.Background()
	lock := NewRedisLock(client, "stop-resource", "id-1", 10*time.Second)
	lock.Acquire(ctx)

	wd := NewWatchdog(lock, 500*time.Millisecond)
	wd.Start(ctx)

	// Stop should return without blocking
	done := make(chan struct{})
	go func() {
		wd.Stop()
		close(done)
	}()

	select {
	case <-done:
		// OK
	case <-time.After(5 * time.Second):
		t.Error("watchdog stop timed out")
	}
}

func TestWatchdog_NoRenewalAfterStop(t *testing.T) {
	s := miniredis.RunT(t)
	client := redis.NewClient(&redis.Options{Addr: s.Addr()})
	defer client.Close()

	ctx := context.Background()
	lock := NewRedisLock(client, "no-renew-resource", "id-1", 2*time.Second)
	lock.Acquire(ctx)

	wd := NewWatchdog(lock, 500*time.Millisecond)
	wd.Start(ctx)

	// Stop watchdog
	wd.Stop()

	// Fast-forward time past lock TTL
	s.FastForward(3 * time.Second)

	// Lock should be expired
	ttl, _ := lock.TTL(ctx)
	if ttl > 0 {
		t.Error("expected lock to expire after watchdog stopped")
	}
}

func TestWatchdog_MultipleStartStop(t *testing.T) {
	s := miniredis.RunT(t)
	client := redis.NewClient(&redis.Options{Addr: s.Addr()})
	defer client.Close()

	ctx := context.Background()
	lock := NewRedisLock(client, "multi-start-stop", "id-1", 10*time.Second)
	lock.Acquire(ctx)

	wd := NewWatchdog(lock, 500*time.Millisecond)

	// Multiple start/stop cycles
	for i := 0; i < 3; i++ {
		wd.Start(ctx)
		time.Sleep(100 * time.Millisecond)
		wd.Stop()
	}
}

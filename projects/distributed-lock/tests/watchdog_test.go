package tests

import (
	"context"
	"testing"
	"time"

	"github.com/alicebob/miniredis/v2"
	goredis "github.com/redis/go-redis/v9"

	"github.com/example/distributed-lock/internal/lock"
	"github.com/example/distributed-lock/internal/redis"
)

func TestWatchdog_BasicRenewal(t *testing.T) {
	s := miniredis.RunT(t)
	client := goredis.NewClient(&goredis.Options{Addr: s.Addr()})
	defer client.Close()

	ctx := context.Background()
	distLock := redis.NewRedisLock(client, "watchdog-resource",
		lock.WithTTL(2*time.Second),
		lock.WithOwnerID("watchdog-owner"))

	// Acquire lock
	acquired, _ := distLock.Acquire(ctx)
	if !acquired {
		t.Fatal("expected to acquire lock")
	}

	// Start watchdog
	wd := redis.NewWatchdog(distLock, 2*time.Second, 500*time.Millisecond)
	wd.Start(ctx)
	defer wd.Stop()

	// Wait for several renewal cycles
	time.Sleep(3 * time.Second)

	// Lock should still be held
	ttl, _ := distLock.TTL(ctx)
	if ttl <= 0 {
		t.Error("expected lock to be renewed by watchdog")
	}
}

func TestWatchdog_Stop(t *testing.T) {
	s := miniredis.RunT(t)
	client := goredis.NewClient(&goredis.Options{Addr: s.Addr()})
	defer client.Close()

	ctx := context.Background()
	distLock := redis.NewRedisLock(client, "stop-resource",
		lock.WithTTL(10*time.Second),
		lock.WithOwnerID("stop-owner"))
	distLock.Acquire(ctx)

	wd := redis.NewWatchdog(distLock, 10*time.Second, 500*time.Millisecond)
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
	client := goredis.NewClient(&goredis.Options{Addr: s.Addr()})
	defer client.Close()

	ctx := context.Background()
	distLock := redis.NewRedisLock(client, "no-renew-resource",
		lock.WithTTL(2*time.Second),
		lock.WithOwnerID("no-renew-owner"))
	distLock.Acquire(ctx)

	wd := redis.NewWatchdog(distLock, 2*time.Second, 500*time.Millisecond)
	wd.Start(ctx)

	// Stop watchdog
	wd.Stop()

	// Fast-forward time past lock TTL
	s.FastForward(3 * time.Second)

	// Lock should be expired
	ttl, _ := distLock.TTL(ctx)
	if ttl > 0 {
		t.Error("expected lock to expire after watchdog stopped")
	}
}

func TestWatchdog_MultipleStartStop(t *testing.T) {
	s := miniredis.RunT(t)
	client := goredis.NewClient(&goredis.Options{Addr: s.Addr()})
	defer client.Close()

	ctx := context.Background()
	distLock := redis.NewRedisLock(client, "multi-start-stop",
		lock.WithTTL(10*time.Second),
		lock.WithOwnerID("multi-owner"))
	distLock.Acquire(ctx)

	wd := redis.NewWatchdog(distLock, 10*time.Second, 500*time.Millisecond)

	// Multiple start/stop cycles
	for i := 0; i < 3; i++ {
		wd.Start(ctx)
		time.Sleep(100 * time.Millisecond)
		wd.Stop()
	}
}

func TestWatchdog_IsRunning(t *testing.T) {
	s := miniredis.RunT(t)
	client := goredis.NewClient(&goredis.Options{Addr: s.Addr()})
	defer client.Close()

	ctx := context.Background()
	distLock := redis.NewRedisLock(client, "running-check",
		lock.WithTTL(10*time.Second),
		lock.WithOwnerID("running-owner"))
	distLock.Acquire(ctx)

	wd := redis.NewWatchdog(distLock, 10*time.Second, 500*time.Millisecond)

	if wd.IsRunning() {
		t.Error("watchdog should not be running initially")
	}

	wd.Start(ctx)
	if !wd.IsRunning() {
		t.Error("watchdog should be running after Start")
	}

	wd.Stop()
	if wd.IsRunning() {
		t.Error("watchdog should not be running after Stop")
	}
}

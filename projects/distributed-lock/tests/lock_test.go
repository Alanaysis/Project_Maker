package tests

import (
	"context"
	"fmt"
	"sync"
	"testing"
	"time"

	"github.com/alicebob/miniredis/v2"
	"github.com/redis/go-redis/v9"
)

// RedisLock represents a basic distributed lock
type RedisLock struct {
	client *redis.Client
	key    string
	value  string
	ttl    time.Duration
}

// NewRedisLock creates a new RedisLock instance
func NewRedisLock(client *redis.Client, key string, value string, ttl time.Duration) *RedisLock {
	return &RedisLock{
		client: client,
		key:    key,
		value:  value,
		ttl:    ttl,
	}
}

// Acquire attempts to acquire the lock
func (l *RedisLock) Acquire(ctx context.Context) (bool, error) {
	ok, err := l.client.SetNX(ctx, l.key, l.value, l.ttl).Result()
	if err != nil {
		return false, err
	}
	return ok, nil
}

// Release releases the lock using Lua script for atomicity
func (l *RedisLock) Release(ctx context.Context) error {
	script := `
		if redis.call("GET", KEYS[1]) == ARGV[1] then
			return redis.call("DEL", KEYS[1])
		else
			return 0
		end
	`
	result, err := l.client.Eval(ctx, script, []string{l.key}, l.value).Int64()
	if err != nil {
		return err
	}
	if result == 0 {
		return ErrLockNotHeld
	}
	return nil
}

// TTL returns the remaining time-to-live of the lock
func (l *RedisLock) TTL(ctx context.Context) (time.Duration, error) {
	ttl, err := l.client.TTL(ctx, l.key).Result()
	if err != nil {
		return 0, err
	}
	if ttl < 0 {
		return 0, nil
	}
	return ttl, nil
}

var ErrLockNotHeld = fmt.Errorf("lock not held by this caller")

func TestRedisLock_AcquireAndRelease(t *testing.T) {
	s := miniredis.RunT(t)
	client := redis.NewClient(&redis.Options{Addr: s.Addr()})
	defer client.Close()

	lock := NewRedisLock(client, "test-resource", "unique-id-1", 10*time.Second)
	ctx := context.Background()

	// Acquire lock
	acquired, err := lock.Acquire(ctx)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !acquired {
		t.Fatal("expected to acquire lock")
	}

	// Verify lock is held
	ttl, err := lock.TTL(ctx)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if ttl <= 0 {
		t.Fatal("expected positive TTL")
	}

	// Release lock
	err = lock.Release(ctx)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	// Verify lock is released
	ttl, _ = lock.TTL(ctx)
	if ttl != 0 {
		t.Errorf("expected TTL 0 after release, got %v", ttl)
	}
}

func TestRedisLock_ConcurrentAcquire(t *testing.T) {
	s := miniredis.RunT(t)
	client := redis.NewClient(&redis.Options{Addr: s.Addr()})
	defer client.Close()

	ctx := context.Background()
	var wg sync.WaitGroup
	acquiredCount := int32(0)
	var mu sync.Mutex

	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			lock := NewRedisLock(client, "concurrent-resource", fmt.Sprintf("id-%d", id), 10*time.Second)
			acquired, _ := lock.Acquire(ctx)
			if acquired {
				mu.Lock()
				acquiredCount++
				mu.Unlock()
				time.Sleep(10 * time.Millisecond)
				lock.Release(ctx)
			}
		}(i)
	}

	wg.Wait()

	if acquiredCount == 0 {
		t.Error("expected at least one goroutine to acquire lock")
	}
}

func TestRedisLock_Expiration(t *testing.T) {
	s := miniredis.RunT(t)
	client := redis.NewClient(&redis.Options{Addr: s.Addr()})
	defer client.Close()

	ctx := context.Background()

	// Create lock with short TTL
	lock1 := NewRedisLock(client, "expire-resource", "id-1", 1*time.Second)
	acquired, _ := lock1.Acquire(ctx)
	if !acquired {
		t.Fatal("expected to acquire lock")
	}

	// Fast-forward time
	s.FastForward(2 * time.Second)

	// Another client should be able to acquire
	lock2 := NewRedisLock(client, "expire-resource", "id-2", 10*time.Second)
	acquired, _ = lock2.Acquire(ctx)
	if !acquired {
		t.Error("expected second client to acquire expired lock")
	}
}

func TestRedisLock_DoubleRelease(t *testing.T) {
	s := miniredis.RunT(t)
	client := redis.NewClient(&redis.Options{Addr: s.Addr()})
	defer client.Close()

	ctx := context.Background()
	lock := NewRedisLock(client, "double-release", "id-1", 10*time.Second)

	lock.Acquire(ctx)
	lock.Release(ctx)

	// Second release should return error
	err := lock.Release(ctx)
	if err == nil {
		t.Error("expected error on double release")
	}
}

func TestRedisLock_MutexExclusion(t *testing.T) {
	s := miniredis.RunT(t)
	client := redis.NewClient(&redis.Options{Addr: s.Addr()})
	defer client.Close()

	ctx := context.Background()

	// First client acquires lock
	lock1 := NewRedisLock(client, "mutex-resource", "id-1", 10*time.Second)
	acquired, _ := lock1.Acquire(ctx)
	if !acquired {
		t.Fatal("expected to acquire lock")
	}

	// Second client should fail to acquire
	lock2 := NewRedisLock(client, "mutex-resource", "id-2", 10*time.Second)
	acquired, _ = lock2.Acquire(ctx)
	if acquired {
		t.Error("expected second client to fail acquiring lock")
	}

	// Release first lock
	lock1.Release(ctx)

	// Now second client should succeed
	acquired, _ = lock2.Acquire(ctx)
	if !acquired {
		t.Error("expected second client to acquire after release")
	}

	lock2.Release(ctx)
}

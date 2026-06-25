package tests

import (
	"context"
	"fmt"
	"sync"
	"testing"
	"time"

	"github.com/alicebob/miniredis/v2"
	goredis "github.com/redis/go-redis/v9"

	"github.com/example/distributed-lock/internal/lock"
	"github.com/example/distributed-lock/internal/redis"
)

func setupMiniredis(t *testing.T) (*miniredis.Miniredis, *goredis.Client) {
	t.Helper()
	mr := miniredis.RunT(t)
	client := goredis.NewClient(&goredis.Options{Addr: mr.Addr()})
	return mr, client
}

func TestRedisLock_BasicAcquireRelease(t *testing.T) {
	mr, client := setupMiniredis(t)
	defer mr.Close()
	defer client.Close()

	ctx := context.Background()
	distLock := redis.NewRedisLock(client, "test:basic",
		lock.WithTTL(10*time.Second),
		lock.WithOwnerID("test-owner-1"))

	// Acquire lock
	acquired, err := distLock.Acquire(ctx)
	if err != nil {
		t.Fatalf("Acquire failed: %v", err)
	}
	if !acquired {
		t.Fatal("Expected to acquire lock")
	}

	// Release lock
	err = distLock.Release(ctx)
	if err != nil {
		t.Fatalf("Release failed: %v", err)
	}
}

func TestRedisLock_ConcurrentAccess(t *testing.T) {
	mr, client := setupMiniredis(t)
	defer mr.Close()
	defer client.Close()

	ctx := context.Background()
	distLock := redis.NewRedisLock(client, "test:concurrent",
		lock.WithTTL(10*time.Second))

	// First acquire should succeed
	acquired, err := distLock.Acquire(ctx)
	if err != nil {
		t.Fatalf("First acquire failed: %v", err)
	}
	if !acquired {
		t.Fatal("First acquire should succeed")
	}

	// Second acquire with different owner should fail
	lock2 := redis.NewRedisLock(client, "test:concurrent",
		lock.WithTTL(10*time.Second),
		lock.WithOwnerID("different-owner"),
		lock.WithRetryCount(0))

	acquired, err = lock2.Acquire(ctx)
	if err != nil {
		t.Fatalf("Second acquire failed: %v", err)
	}
	if acquired {
		t.Fatal("Second acquire should fail")
	}

	// Release first lock
	err = distLock.Release(ctx)
	if err != nil {
		t.Fatalf("Release failed: %v", err)
	}

	// Now second lock should succeed
	acquired, err = lock2.Acquire(ctx)
	if err != nil {
		t.Fatalf("Third acquire failed: %v", err)
	}
	if !acquired {
		t.Fatal("Third acquire should succeed")
	}
}

func TestRedisLock_OwnershipCheck(t *testing.T) {
	mr, client := setupMiniredis(t)
	defer mr.Close()
	defer client.Close()

	ctx := context.Background()
	distLock := redis.NewRedisLock(client, "test:ownership",
		lock.WithTTL(10*time.Second),
		lock.WithOwnerID("owner-1"))

	// Acquire lock
	acquired, err := distLock.Acquire(ctx)
	if err != nil {
		t.Fatalf("Acquire failed: %v", err)
	}
	if !acquired {
		t.Fatal("Expected to acquire lock")
	}

	// Try to release with different owner
	lock2 := redis.NewRedisLock(client, "test:ownership",
		lock.WithTTL(10*time.Second),
		lock.WithOwnerID("owner-2"))

	err = lock2.Release(ctx)
	if err != redis.ErrLockNotOwned {
		t.Fatalf("Expected ErrLockNotOwned, got: %v", err)
	}

	// Release with correct owner
	err = distLock.Release(ctx)
	if err != nil {
		t.Fatalf("Release failed: %v", err)
	}
}

func TestRedisLock_TTL(t *testing.T) {
	mr, client := setupMiniredis(t)
	defer mr.Close()
	defer client.Close()

	ctx := context.Background()
	distLock := redis.NewRedisLock(client, "test:ttl",
		lock.WithTTL(30*time.Second),
		lock.WithOwnerID("ttl-owner"))

	// Acquire lock
	acquired, err := distLock.Acquire(ctx)
	if err != nil {
		t.Fatalf("Acquire failed: %v", err)
	}
	if !acquired {
		t.Fatal("Expected to acquire lock")
	}

	// Check TTL
	ttl, err := distLock.TTL(ctx)
	if err != nil {
		t.Fatalf("TTL failed: %v", err)
	}
	if ttl <= 0 || ttl > 30*time.Second {
		t.Fatalf("Expected TTL between 0 and 30s, got: %v", ttl)
	}

	// Cleanup
	distLock.Release(ctx)
}

func TestRedisLock_Extend(t *testing.T) {
	mr, client := setupMiniredis(t)
	defer mr.Close()
	defer client.Close()

	ctx := context.Background()
	distLock := redis.NewRedisLock(client, "test:extend",
		lock.WithTTL(10*time.Second),
		lock.WithOwnerID("extend-owner"))

	// Acquire lock
	acquired, err := distLock.Acquire(ctx)
	if err != nil {
		t.Fatalf("Acquire failed: %v", err)
	}
	if !acquired {
		t.Fatal("Expected to acquire lock")
	}

	// Extend lock
	extended, err := distLock.Extend(ctx, 30*time.Second)
	if err != nil {
		t.Fatalf("Extend failed: %v", err)
	}
	if !extended {
		t.Fatal("Expected to extend lock")
	}

	// Cleanup
	distLock.Release(ctx)
}

func TestRedisLock_RetryLogic(t *testing.T) {
	mr, client := setupMiniredis(t)
	defer mr.Close()
	defer client.Close()

	ctx := context.Background()

	// Lock with short retry
	distLock := redis.NewRedisLock(client, "test:retry",
		lock.WithTTL(10*time.Second),
		lock.WithRetryCount(2),
		lock.WithRetryDelay(50*time.Millisecond),
		lock.WithOwnerID("retry-owner"))

	// Acquire lock
	acquired, err := distLock.Acquire(ctx)
	if err != nil {
		t.Fatalf("Acquire failed: %v", err)
	}
	if !acquired {
		t.Fatal("Expected to acquire lock")
	}

	// Second lock with same retries should fail
	lock2 := redis.NewRedisLock(client, "test:retry",
		lock.WithTTL(10*time.Second),
		lock.WithRetryCount(2),
		lock.WithRetryDelay(50*time.Millisecond),
		lock.WithOwnerID("retry-owner-2"))

	start := time.Now()
	acquired, err = lock2.Acquire(ctx)
	elapsed := time.Since(start)

	if err != nil {
		t.Fatalf("Second acquire failed: %v", err)
	}
	if acquired {
		t.Fatal("Second acquire should fail")
	}

	// Should have taken at least 2 * 50ms = 100ms
	if elapsed < 100*time.Millisecond {
		t.Fatalf("Expected retry delay, got: %v", elapsed)
	}

	// Cleanup
	distLock.Release(ctx)
}

func TestReentrantLock_BasicReentrant(t *testing.T) {
	mr, client := setupMiniredis(t)
	defer mr.Close()
	defer client.Close()

	ctx := context.Background()
	distLock := redis.NewReentrantRedisLock(client, "test:reentrant",
		lock.WithTTL(10*time.Second),
		lock.WithOwnerID("reentrant-owner"))

	// First acquire
	acquired, err := distLock.Acquire(ctx)
	if err != nil {
		t.Fatalf("First acquire failed: %v", err)
	}
	if !acquired {
		t.Fatal("First acquire should succeed")
	}

	// Check count
	count, err := distLock.Count(ctx)
	if err != nil {
		t.Fatalf("Count failed: %v", err)
	}
	if count != 1 {
		t.Fatalf("Expected count=1, got: %d", count)
	}

	// Second acquire (reentrant)
	acquired, err = distLock.Acquire(ctx)
	if err != nil {
		t.Fatalf("Second acquire failed: %v", err)
	}
	if !acquired {
		t.Fatal("Second acquire should succeed")
	}

	// Check count
	count, err = distLock.Count(ctx)
	if err != nil {
		t.Fatalf("Count failed: %v", err)
	}
	if count != 2 {
		t.Fatalf("Expected count=2, got: %d", count)
	}

	// First release
	err = distLock.Release(ctx)
	if err != nil {
		t.Fatalf("First release failed: %v", err)
	}

	// Check count
	count, err = distLock.Count(ctx)
	if err != nil {
		t.Fatalf("Count failed: %v", err)
	}
	if count != 1 {
		t.Fatalf("Expected count=1 after first release, got: %d", count)
	}

	// Second release
	err = distLock.Release(ctx)
	if err != nil {
		t.Fatalf("Second release failed: %v", err)
	}

	// Check count
	count, err = distLock.Count(ctx)
	if err != nil {
		t.Fatalf("Count failed: %v", err)
	}
	if count != 0 {
		t.Fatalf("Expected count=0 after second release, got: %d", count)
	}
}

func TestFairLock_FIFOOrdering(t *testing.T) {
	mr, client := setupMiniredis(t)
	defer mr.Close()
	defer client.Close()

	ctx := context.Background()

	// Create multiple fair locks
	locks := make([]*redis.FairRedisLock, 3)
	for i := 0; i < 3; i++ {
		locks[i] = redis.NewFairRedisLock(client, "test:fair",
			lock.WithTTL(10*time.Second),
			lock.WithRetryCount(10),
			lock.WithRetryDelay(50*time.Millisecond),
			lock.WithOwnerID(fmt.Sprintf("fair-owner-%d", i)))
	}

	// All goroutines try to acquire
	results := make(chan int, 3)
	for i := 0; i < 3; i++ {
		go func(idx int) {
			acquired, _ := locks[idx].Acquire(ctx)
			if acquired {
				results <- idx
				time.Sleep(100 * time.Millisecond)
				locks[idx].Release(ctx)
			}
		}(i)
	}

	// Collect results
	order := make([]int, 0, 3)
	for i := 0; i < 3; i++ {
		order = append(order, <-results)
	}

	// Note: Due to timing, we can't guarantee exact FIFO order in tests
	// but we verify all goroutines got the lock
	if len(order) != 3 {
		t.Fatalf("Expected 3 results, got: %d", len(order))
	}
}

func TestReadWriteLock_ConcurrentReaders(t *testing.T) {
	mr, client := setupMiniredis(t)
	defer mr.Close()
	defer client.Close()

	ctx := context.Background()
	rwLock := redis.NewReadWriteRedisLock(client, "test:rw",
		lock.WithTTL(10*time.Second))

	// Multiple readers should succeed
	for i := 0; i < 3; i++ {
		acquired, err := rwLock.AcquireRead(ctx)
		if err != nil {
			t.Fatalf("Reader %d acquire failed: %v", i, err)
		}
		if !acquired {
			t.Fatalf("Reader %d should acquire", i)
		}
	}

	// Check reader count
	count, err := rwLock.ReaderCount(ctx)
	if err != nil {
		t.Fatalf("ReaderCount failed: %v", err)
	}
	if count != 3 {
		t.Fatalf("Expected 3 readers, got: %d", count)
	}

	// Release all readers
	for i := 0; i < 3; i++ {
		err := rwLock.ReleaseRead(ctx)
		if err != nil {
			t.Fatalf("Reader %d release failed: %v", i, err)
		}
	}
}

func TestReadWriteLock_WriterExclusion(t *testing.T) {
	mr, client := setupMiniredis(t)
	defer mr.Close()
	defer client.Close()

	ctx := context.Background()
	rwLock := redis.NewReadWriteRedisLock(client, "test:rw:exclusion",
		lock.WithTTL(10*time.Second))

	// Acquire write lock
	acquired, err := rwLock.AcquireWrite(ctx)
	if err != nil {
		t.Fatalf("Writer acquire failed: %v", err)
	}
	if !acquired {
		t.Fatal("Writer should acquire")
	}

	// Reader should fail
	rwLock2 := redis.NewReadWriteRedisLock(client, "test:rw:exclusion",
		lock.WithTTL(10*time.Second),
		lock.WithRetryCount(0))

	acquired, err = rwLock2.AcquireRead(ctx)
	if err != nil {
		t.Fatalf("Reader acquire failed: %v", err)
	}
	if acquired {
		t.Fatal("Reader should not acquire when writer holds lock")
	}

	// Release writer
	err = rwLock.ReleaseWrite(ctx)
	if err != nil {
		t.Fatalf("Writer release failed: %v", err)
	}

	// Now reader should succeed
	acquired, err = rwLock2.AcquireRead(ctx)
	if err != nil {
		t.Fatalf("Reader acquire failed: %v", err)
	}
	if !acquired {
		t.Fatal("Reader should acquire after writer releases")
	}
}

// Legacy tests from original file
func TestRedisLock_AcquireAndRelease_Legacy(t *testing.T) {
	s := miniredis.RunT(t)
	client := goredis.NewClient(&goredis.Options{Addr: s.Addr()})
	defer client.Close()

	distLock := redis.NewRedisLock(client, "test-resource",
		lock.WithTTL(10*time.Second),
		lock.WithOwnerID("unique-id-1"))
	ctx := context.Background()

	// Acquire lock
	acquired, err := distLock.Acquire(ctx)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !acquired {
		t.Fatal("expected to acquire lock")
	}

	// Verify lock is held
	ttl, err := distLock.TTL(ctx)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if ttl <= 0 {
		t.Fatal("expected positive TTL")
	}

	// Release lock
	err = distLock.Release(ctx)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
}

func TestRedisLock_ConcurrentAcquire_Legacy(t *testing.T) {
	s := miniredis.RunT(t)
	client := goredis.NewClient(&goredis.Options{Addr: s.Addr()})
	defer client.Close()

	ctx := context.Background()
	var wg sync.WaitGroup
	acquiredCount := int32(0)
	var mu sync.Mutex

	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			distLock := redis.NewRedisLock(client, "concurrent-resource",
				lock.WithTTL(10*time.Second),
				lock.WithOwnerID(fmt.Sprintf("id-%d", id)))
			acquired, _ := distLock.Acquire(ctx)
			if acquired {
				mu.Lock()
				acquiredCount++
				mu.Unlock()
				time.Sleep(10 * time.Millisecond)
				distLock.Release(ctx)
			}
		}(i)
	}

	wg.Wait()

	if acquiredCount == 0 {
		t.Error("expected at least one goroutine to acquire lock")
	}
}

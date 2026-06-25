package main

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"

	goredis "github.com/redis/go-redis/v9"

	"github.com/example/distributed-lock/internal/lock"
	"github.com/example/distributed-lock/internal/redis"
)

func main() {
	fmt.Println("=== Distributed Lock Examples ===")
	fmt.Println()

	// Note: This example requires a running Redis server
	// Ensure Redis is running on localhost:6379

	client := goredis.NewClient(&goredis.Options{
		Addr: "localhost:6379",
	})
	defer client.Close()

	ctx := context.Background()

	// Test connection
	if err := client.Ping(ctx).Err(); err != nil {
		log.Fatalf("Cannot connect to Redis: %v", err)
	}
	fmt.Println("Connected to Redis")
	fmt.Println()

	// Example 1: Basic Distributed Lock
	basicLockExample(client, ctx)

	// Example 2: Concurrent Lock Contention
	concurrentLockExample(client, ctx)

	// Example 3: Lock Renewal (Watchdog)
	watchdogExample(client, ctx)

	// Example 4: Reentrant Lock
	reentrantLockExample(client, ctx)

	// Example 5: Fair Lock
	fairLockExample(client, ctx)

	// Example 6: Read-Write Lock
	readWriteLockExample(client, ctx)
}

func basicLockExample(client *goredis.Client, ctx context.Context) {
	fmt.Println("--- Example 1: Basic Distributed Lock ---")

	distLock := redis.NewRedisLock(client, "example:basic-lock",
		lock.WithTTL(10*time.Second),
		lock.WithOwnerID("client-001"))

	// Acquire lock
	acquired, err := distLock.Acquire(ctx)
	if err != nil {
		log.Printf("Failed to acquire lock: %v", err)
		return
	}
	if !acquired {
		fmt.Println("Lock is held by another client")
		return
	}
	fmt.Println("Lock acquired successfully")

	// Check TTL
	ttl, _ := distLock.TTL(ctx)
	fmt.Printf("Lock TTL: %v\n", ttl)

	// Simulate business logic
	fmt.Println("Executing business logic...")
	time.Sleep(500 * time.Millisecond)

	// Release lock
	err = distLock.Release(ctx)
	if err != nil {
		log.Printf("Failed to release lock: %v", err)
		return
	}
	fmt.Println("Lock released")
	fmt.Println()
}

func concurrentLockExample(client *goredis.Client, ctx context.Context) {
	fmt.Println("--- Example 2: Concurrent Lock Contention ---")

	numWorkers := 5
	var wg sync.WaitGroup
	successCount := 0
	var mu sync.Mutex

	for i := 0; i < numWorkers; i++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()

			distLock := redis.NewRedisLock(client, "example:concurrent-lock",
				lock.WithTTL(5*time.Second),
				lock.WithOwnerID(fmt.Sprintf("worker-%d", workerID)))

			acquired, _ := distLock.Acquire(ctx)
			if acquired {
				mu.Lock()
				successCount++
				mu.Unlock()

				fmt.Printf("  Worker %d: Lock acquired\n", workerID)

				// Simulate work
				time.Sleep(100 * time.Millisecond)

				distLock.Release(ctx)
				fmt.Printf("  Worker %d: Lock released\n", workerID)
			} else {
				fmt.Printf("  Worker %d: Failed to acquire lock\n", workerID)
			}
		}(i)
	}

	wg.Wait()
	fmt.Printf("Workers that acquired lock: %d/%d\n", successCount, numWorkers)
	fmt.Println()
}

func watchdogExample(client *goredis.Client, ctx context.Context) {
	fmt.Println("--- Example 3: Lock Renewal (Watchdog) ---")

	distLock := redis.NewRedisLock(client, "example:watchdog-lock",
		lock.WithTTL(2*time.Second),
		lock.WithOwnerID("client-003"))

	// Acquire lock
	acquired, _ := distLock.Acquire(ctx)
	if !acquired {
		fmt.Println("Failed to acquire lock")
		return
	}
	fmt.Println("Lock acquired")

	// Start watchdog
	wd := redis.NewWatchdog(distLock, 2*time.Second, 600*time.Millisecond)
	wd.Start(ctx)

	// Simulate long-running task
	fmt.Println("Executing long-running task (5 seconds)...")
	time.Sleep(5 * time.Second)

	// Stop watchdog
	wd.Stop()

	// Release lock
	err := distLock.Release(ctx)
	if err != nil {
		log.Printf("Failed to release lock: %v", err)
		return
	}
	fmt.Println("Lock released")
	fmt.Println()
}

func reentrantLockExample(client *goredis.Client, ctx context.Context) {
	fmt.Println("--- Example 4: Reentrant Lock ---")

	distLock := redis.NewReentrantRedisLock(client, "example:reentrant-lock",
		lock.WithTTL(10*time.Second),
		lock.WithOwnerID("client-004"))

	// First acquisition
	acquired, _ := distLock.Acquire(ctx)
	fmt.Printf("First acquire: %v\n", acquired)

	// Second acquisition (reentrant)
	acquired, _ = distLock.Acquire(ctx)
	fmt.Printf("Second acquire (reentrant): %v\n", acquired)

	// Third acquisition (reentrant)
	acquired, _ = distLock.Acquire(ctx)
	fmt.Printf("Third acquire (reentrant): %v\n", acquired)

	// Check count
	count, _ := distLock.Count(ctx)
	fmt.Printf("Reentrant count: %d\n", count)

	// Release
	distLock.Release(ctx)
	count, _ = distLock.Count(ctx)
	fmt.Printf("After first release, count: %d\n", count)

	distLock.Release(ctx)
	count, _ = distLock.Count(ctx)
	fmt.Printf("After second release, count: %d\n", count)

	distLock.Release(ctx)
	count, _ = distLock.Count(ctx)
	fmt.Printf("After third release, count: %d\n", count)

	fmt.Println()
}

func fairLockExample(client *goredis.Client, ctx context.Context) {
	fmt.Println("--- Example 5: Fair Lock ---")

	numWorkers := 3
	var wg sync.WaitGroup

	for i := 0; i < numWorkers; i++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()

			distLock := redis.NewFairRedisLock(client, "example:fair-lock",
				lock.WithTTL(10*time.Second),
				lock.WithRetryCount(10),
				lock.WithRetryDelay(100*time.Millisecond),
				lock.WithOwnerID(fmt.Sprintf("fair-worker-%d", workerID)))

			acquired, _ := distLock.Acquire(ctx)
			if acquired {
				fmt.Printf("  Worker %d: Lock acquired (FIFO)\n", workerID)
				time.Sleep(100 * time.Millisecond)
				distLock.Release(ctx)
				fmt.Printf("  Worker %d: Lock released\n", workerID)
			}
		}(i)
	}

	wg.Wait()
	fmt.Println()
}

func readWriteLockExample(client *goredis.Client, ctx context.Context) {
	fmt.Println("--- Example 6: Read-Write Lock ---")

	rwLock := redis.NewReadWriteRedisLock(client, "example:rw-lock",
		lock.WithTTL(10*time.Second))

	var wg sync.WaitGroup

	// Multiple readers
	for i := 0; i < 3; i++ {
		wg.Add(1)
		go func(readerID int) {
			defer wg.Done()
			acquired, _ := rwLock.AcquireRead(ctx)
			if acquired {
				fmt.Printf("  Reader %d: Read lock acquired\n", readerID)
				time.Sleep(100 * time.Millisecond)
				rwLock.ReleaseRead(ctx)
				fmt.Printf("  Reader %d: Read lock released\n", readerID)
			}
		}(i)
	}

	// One writer
	wg.Add(1)
	go func() {
		defer wg.Done()
		acquired, _ := rwLock.AcquireWrite(ctx)
		if acquired {
			fmt.Println("  Writer: Write lock acquired")
			time.Sleep(100 * time.Millisecond)
			rwLock.ReleaseWrite(ctx)
			fmt.Println("  Writer: Write lock released")
		}
	}()

	wg.Wait()
}

package examples

import (
	"context"
	"fmt"
	"log"
	"time"

	goredis "github.com/redis/go-redis/v9"

	"github.com/example/distributed-lock/internal/lock"
	"github.com/example/distributed-lock/internal/redis"
)

// Example_basicLock demonstrates basic distributed lock usage
func Example_basicLock() {
	// Create Redis client
	client := goredis.NewClient(&goredis.Options{
		Addr: "localhost:6379",
	})
	defer client.Close()

	ctx := context.Background()

	// Create distributed lock
	distLock := redis.NewRedisLock(client, "my-resource-lock",
		lock.WithTTL(10*time.Second),
		lock.WithOwnerID("unique-client-id"))

	// Acquire lock
	acquired, err := distLock.Acquire(ctx)
	if err != nil {
		log.Fatalf("Failed to acquire lock: %v", err)
	}
	if !acquired {
		log.Fatal("Lock is already held by another client")
	}
	fmt.Println("Lock acquired successfully")

	// Simulate business logic
	fmt.Println("Executing business logic...")
	time.Sleep(1 * time.Second)

	// Release lock
	err = distLock.Release(ctx)
	if err != nil {
		log.Fatalf("Failed to release lock: %v", err)
	}
	fmt.Println("Lock released successfully")
}

// Example_redlock demonstrates Redlock algorithm usage
func Example_redlock() {
	// Create multiple Redis clients (typically on different machines)
	clients := []*goredis.Client{
		goredis.NewClient(&goredis.Options{Addr: "redis1:6379"}),
		goredis.NewClient(&goredis.Options{Addr: "redis2:6379"}),
		goredis.NewClient(&goredis.Options{Addr: "redis3:6379"}),
	}
	defer func() {
		for _, c := range clients {
			c.Close()
		}
	}()

	ctx := context.Background()

	// Create Redlock
	rl := redis.NewRedLock(clients, "distributed-resource",
		lock.WithTTL(10*time.Second),
		lock.WithOwnerID("client-uuid-123"))

	// Acquire lock (requires majority of nodes)
	acquired, err := rl.Acquire(ctx)
	if err != nil {
		log.Fatalf("Failed to acquire lock: %v", err)
	}
	if !acquired {
		log.Fatal("Failed to acquire lock (quorum not reached)")
	}
	fmt.Println("Lock acquired using Redlock")

	// Execute business logic
	fmt.Println("Executing business logic...")

	// Release lock on all nodes
	err = rl.Release(ctx)
	if err != nil {
		log.Fatalf("Failed to release lock: %v", err)
	}
	fmt.Println("Lock released on all nodes")
}

// Example_watchdog demonstrates lock renewal with watchdog
func Example_watchdog() {
	client := goredis.NewClient(&goredis.Options{
		Addr: "localhost:6379",
	})
	defer client.Close()

	ctx := context.Background()

	// Create lock
	distLock := redis.NewRedisLock(client, "long-running-task",
		lock.WithTTL(10*time.Second),
		lock.WithOwnerID("client-id"))

	// Acquire lock
	acquired, _ := distLock.Acquire(ctx)
	if !acquired {
		log.Fatal("Failed to acquire lock")
	}
	fmt.Println("Lock acquired")

	// Create and start watchdog
	wd := redis.NewWatchdog(distLock, 10*time.Second, 3*time.Second)
	wd.Start(ctx)

	// Simulate long-running task
	fmt.Println("Executing long-running task...")
	time.Sleep(25 * time.Second)

	// Stop watchdog
	wd.Stop()

	// Release lock
	err := distLock.Release(ctx)
	if err != nil {
		log.Fatalf("Failed to release lock: %v", err)
	}
	fmt.Println("Lock released")
}

// Example_reentrantLock demonstrates reentrant lock usage
func Example_reentrantLock() {
	client := goredis.NewClient(&goredis.Options{
		Addr: "localhost:6379",
	})
	defer client.Close()

	ctx := context.Background()

	// Create reentrant lock
	distLock := redis.NewReentrantRedisLock(client, "reentrant-resource",
		lock.WithTTL(10*time.Second),
		lock.WithOwnerID("client-1"))

	// First acquisition
	acquired, _ := distLock.Acquire(ctx)
	fmt.Printf("First acquire: %v\n", acquired)

	// Second acquisition (reentrant)
	acquired, _ = distLock.Acquire(ctx)
	fmt.Printf("Second acquire (reentrant): %v\n", acquired)

	// Check count
	count, _ := distLock.Count(ctx)
	fmt.Printf("Reentrant count: %d\n", count)

	// First release (count decreases)
	distLock.Release(ctx)
	count, _ = distLock.Count(ctx)
	fmt.Printf("After first release, count: %d\n", count)

	// Second release (lock fully released)
	distLock.Release(ctx)
	count, _ = distLock.Count(ctx)
	fmt.Printf("After second release, count: %d\n", count)
}

// Example_fairLock demonstrates fair lock with waiting queue
func Example_fairLock() {
	client := goredis.NewClient(&goredis.Options{
		Addr: "localhost:6379",
	})
	defer client.Close()

	ctx := context.Background()

	// Create fair lock
	distLock := redis.NewFairRedisLock(client, "fair-resource",
		lock.WithTTL(10*time.Second),
		lock.WithOwnerID("client-1"))

	// Acquire lock (FIFO ordering)
	acquired, _ := distLock.Acquire(ctx)
	if acquired {
		fmt.Println("Lock acquired (FIFO order)")

		// Execute business logic
		fmt.Println("Executing business logic...")

		// Release lock
		distLock.Release(ctx)
		fmt.Println("Lock released")
	}
}

// Example_readWriteLock demonstrates reader-writer lock usage
func Example_readWriteLock() {
	client := goredis.NewClient(&goredis.Options{
		Addr: "localhost:6379",
	})
	defer client.Close()

	ctx := context.Background()

	// Create read-write lock
	rwLock := redis.NewReadWriteRedisLock(client, "rw-resource",
		lock.WithTTL(10*time.Second))

	// Multiple readers can acquire simultaneously
	acquired, _ := rwLock.AcquireRead(ctx)
	if acquired {
		fmt.Println("Read lock acquired")
		// Read data...
		rwLock.ReleaseRead(ctx)
		fmt.Println("Read lock released")
	}

	// Writer has exclusive access
	acquired, _ = rwLock.AcquireWrite(ctx)
	if acquired {
		fmt.Println("Write lock acquired")
		// Write data...
		rwLock.ReleaseWrite(ctx)
		fmt.Println("Write lock released")
	}
}

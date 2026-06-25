// Demo application for distributed lock.
package main

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/example/distributed-lock/internal/lock"
	"github.com/example/distributed-lock/internal/redis"
)

func main() {
	fmt.Println("=== Distributed Lock Demo ===")
	fmt.Println()

	// Demo 1: Basic Lock
	demoBasicLock()

	// Demo 2: Reentrant Lock
	demoReentrantLock()

	// Demo 3: Fair Lock
	demoFairLock()

	// Demo 4: Read-Write Lock
	demoReadWriteLock()
}

func demoBasicLock() {
	fmt.Println("--- Demo 1: Basic Lock ---")
	fmt.Println("Shows concurrent access with a distributed lock")
	fmt.Println()

	// Note: This demo requires a running Redis instance
	// For demonstration purposes, we show the code pattern

	fmt.Println("Code Pattern:")
	fmt.Println(`
  // Create Redis client
  client := redis.NewClient(&redis.Options{Addr: "localhost:6379"})
  defer client.Close()

  // Create lock
  distLock := lock.NewRedisLock(client, "demo:resource",
      lock.WithTTL(10*time.Second),
      lock.WithRetryCount(3),
      lock.WithRetryDelay(200*time.Millisecond))

  // Acquire lock
  ctx := context.Background()
  acquired, err := distLock.Acquire(ctx)
  if err != nil {
      log.Fatal(err)
  }
  if !acquired {
      fmt.Println("Could not acquire lock")
      return
  }
  defer distLock.Release(ctx)

  // Do work
  fmt.Println("Lock acquired, doing work...")
  time.Sleep(1 * time.Second)
  fmt.Println("Work complete")
`)
	fmt.Println()
}

func demoReentrantLock() {
	fmt.Println("--- Demo 2: Reentrant Lock ---")
	fmt.Println("Shows recursive lock acquisition")
	fmt.Println()

	fmt.Println("Code Pattern:")
	fmt.Println(`
  // Create reentrant lock
  distLock := lock.NewReentrantRedisLock(client, "demo:reentrant",
      lock.WithTTL(10*time.Second))

  // First acquisition
  acquired, _ := distLock.Acquire(ctx)
  fmt.Printf("First acquire: %v\n", acquired)  // true

  // Second acquisition (reentrant)
  acquired, _ = distLock.Acquire(ctx)
  fmt.Printf("Second acquire: %v\n", acquired)  // true

  // Check count
  count, _ := distLock.Count(ctx)
  fmt.Printf("Count: %d\n", count)  // 2

  // First release (decrements count)
  distLock.Release(ctx)
  count, _ = distLock.Count(ctx)
  fmt.Printf("Count after first release: %d\n", count)  // 1

  // Second release (actually releases lock)
  distLock.Release(ctx)
  count, _ = distLock.Count(ctx)
  fmt.Printf("Count after second release: %d\n", count)  // 0
`)
	fmt.Println()
}

func demoFairLock() {
	fmt.Println("--- Demo 3: Fair Lock ---")
	fmt.Println("Shows FIFO ordering of lock acquisition")
	fmt.Println()

	fmt.Println("Code Pattern:")
	fmt.Println(`
  // Create fair lock
  distLock := lock.NewFairRedisLock(client, "demo:fair",
      lock.WithTTL(10*time.Second))

  // Multiple goroutines try to acquire
  var wg sync.WaitGroup
  for i := 0; i < 5; i++ {
      wg.Add(1)
      go func(id int) {
          defer wg.Done()
          acquired, _ := distLock.Acquire(ctx)
          if acquired {
              fmt.Printf("Goroutine %d acquired lock\n", id)
              time.Sleep(100 * time.Millisecond)
              distLock.Release(ctx)
          }
      }(i)
  }
  wg.Wait()

  // Output (FIFO order):
  // Goroutine 0 acquired lock
  // Goroutine 1 acquired lock
  // Goroutine 2 acquired lock
  // Goroutine 3 acquired lock
  // Goroutine 4 acquired lock
`)
	fmt.Println()
}

func demoReadWriteLock() {
	fmt.Println("--- Demo 4: Read-Write Lock ---")
	fmt.Println("Shows multiple readers or single writer")
	fmt.Println()

	fmt.Println("Code Pattern:")
	fmt.Println(`
  // Create read-write lock
  rwLock := lock.NewReadWriteRedisLock(client, "demo:rw",
      lock.WithTTL(10*time.Second))

  // Multiple readers can acquire simultaneously
  var wg sync.WaitGroup
  for i := 0; i < 3; i++ {
      wg.Add(1)
      go func(id int) {
          defer wg.Done()
          acquired, _ := rwLock.AcquireRead(ctx)
          if acquired {
              fmt.Printf("Reader %d acquired lock\n", id)
              time.Sleep(100 * time.Millisecond)
              rwLock.ReleaseRead(ctx)
          }
      }(i)
  }

  // Writer must wait for all readers
  wg.Add(1)
  go func() {
      defer wg.Done()
      acquired, _ := rwLock.AcquireWrite(ctx)
      if acquired {
          fmt.Println("Writer acquired lock")
          time.Sleep(100 * time.Millisecond)
          rwLock.ReleaseWrite(ctx)
      }
  }()

  wg.Wait()

  // Output:
  // Reader 0 acquired lock
  // Reader 1 acquired lock
  // Reader 2 acquired lock
  // Writer acquired lock
`)
}

// simulateConcurrentAccess demonstrates concurrent lock usage.
func simulateConcurrentAccess() {
	fmt.Println("=== Simulating Concurrent Access ===")
	fmt.Println()

	// This would use a real Redis client in production
	// client := redis.NewClient(&redis.Options{Addr: "localhost:6379"})
	// defer client.Close()

	// distLock := lock.NewRedisLock(client, "concurrent:demo",
	//     lock.WithTTL(5*time.Second))

	var wg sync.WaitGroup
	for i := 0; i < 5; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			// acquired, _ := distLock.Acquire(context.Background())
			// if acquired {
			//     fmt.Printf("Worker %d acquired lock\n", id)
			//     time.Sleep(100 * time.Millisecond)
			//     distLock.Release(context.Background())
			// }
			fmt.Printf("Worker %d would acquire lock\n", id)
		}(i)
	}
	wg.Wait()
}

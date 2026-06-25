# Distributed Lock

A comprehensive distributed lock library supporting multiple backends (Redis, ZooKeeper, etcd) with various lock types (basic, reentrant, fair, read-write).

## Features

### Backend Support
- **Redis**: Single-node and Redlock algorithm
- **ZooKeeper**: Ephemeral sequential nodes with Watch mechanism
- **etcd**: Lease-based with Revision comparison

### Lock Types
- **Basic Lock**: Simple mutex with TTL expiration
- **Reentrant Lock**: Same client can acquire multiple times
- **Fair Lock**: FIFO ordering guarantees
- **Read-Write Lock**: Multiple readers or single writer

### Advanced Features
- **Watchdog**: Automatic lock renewal for long-running tasks
- **Retry Logic**: Configurable retry count and delay
- **Ownership Verification**: Only lock holder can release
- **Atomic Operations**: Lua scripts for Redis, transactions for others

## Project Structure

```
distributed-lock/
├── README.md
├── go.mod
├── go.sum
├── internal/
│   ├── lock/
│   │   └── lock.go              # Core interfaces
│   ├── redis/
│   │   ├── lock.go              # Basic Redis lock
│   │   ├── redlock.go           # Redlock algorithm
│   │   ├── reentrant.go         # Reentrant lock
│   │   ├── fair.go              # Fair (FIFO) lock
│   │   ├── rwlock.go            # Read-write lock
│   │   └── watchdog.go          # Auto-renewal
│   ├── zookeeper/
│   │   └── lock.go              # ZooKeeper lock
│   └── etcd/
│       └── lock.go              # etcd lock
├── pkg/
│   └── utils/
│       └── id.go                # ID generation
├── cmd/
│   └── demo/
│       └── main.go              # Demo application
├── examples/
│   ├── task_scheduler.go        # Task scheduling example
│   ├── inventory.go             # Inventory management example
│   ├── ratelimiter.go           # Rate limiter example
│   └── main.go                  # Usage examples
├── tests/
│   ├── lock_test.go             # Lock tests
│   ├── redlock_test.go          # Redlock tests
│   └── watchdog_test.go         # Watchdog tests
└── docs/
    ├── 01-RESEARCH.md
    ├── 02-DESIGN.md
    ├── 03-IMPLEMENTATION.md
    ├── 04-TESTING.md
    └── 05-DEVELOPMENT.md
```

## Quick Start

### Prerequisites

- Go 1.21+
- Redis 6.0+ (for Redis backend)
- ZooKeeper 3.6+ (for ZooKeeper backend)
- etcd 3.5+ (for etcd backend)

### Installation

```bash
go mod tidy
```

### Basic Usage

```go
package main

import (
    "context"
    "fmt"
    "time"

    "github.com/example/distributed-lock/internal/lock"
    "github.com/example/distributed-lock/internal/redis"
    goredis "github.com/redis/go-redis/v9"
)

func main() {
    // Create Redis client
    client := goredis.NewClient(&goredis.Options{
        Addr: "localhost:6379",
    })
    defer client.Close()

    // Create distributed lock
    ctx := context.Background()
    distLock := redis.NewRedisLock(client, "my-resource",
        lock.WithTTL(10*time.Second),
        lock.WithOwnerID("my-client-id"))

    // Acquire lock
    acquired, err := distLock.Acquire(ctx)
    if err != nil {
        panic(err)
    }
    if !acquired {
        fmt.Println("Could not acquire lock")
        return
    }
    defer distLock.Release(ctx)

    // Execute business logic
    fmt.Println("Lock acquired, executing business logic...")
}
```

### Using Redlock

```go
// Create multiple Redis clients
clients := []*goredis.Client{
    goredis.NewClient(&goredis.Options{Addr: "redis1:6379"}),
    goredis.NewClient(&goredis.Options{Addr: "redis2:6379"}),
    goredis.NewClient(&goredis.Options{Addr: "redis3:6379"}),
}

// Create Redlock
rl := redis.NewRedLock(clients, "my-resource",
    lock.WithTTL(10*time.Second))

// Acquire lock (requires majority of nodes)
acquired, err := rl.Acquire(ctx)
```

### Using Reentrant Lock

```go
// Create reentrant lock
distLock := redis.NewReentrantRedisLock(client, "my-resource",
    lock.WithTTL(10*time.Second))

// First acquisition
acquired, _ := distLock.Acquire(ctx) // true

// Second acquisition (reentrant)
acquired, _ = distLock.Acquire(ctx) // true

// Check count
count, _ := distLock.Count(ctx) // 2

// Release (decrements count)
distLock.Release(ctx)
count, _ = distLock.Count(ctx) // 1

// Final release (actually releases lock)
distLock.Release(ctx)
count, _ = distLock.Count(ctx) // 0
```

### Using Fair Lock

```go
// Create fair lock with FIFO ordering
distLock := redis.NewFairRedisLock(client, "my-resource",
    lock.WithTTL(10*time.Second),
    lock.WithRetryCount(10),
    lock.WithRetryDelay(100*time.Millisecond))

// Acquire lock (waits for turn in queue)
acquired, _ := distLock.Acquire(ctx)
```

### Using Read-Write Lock

```go
// Create read-write lock
rwLock := redis.NewReadWriteRedisLock(client, "my-resource",
    lock.WithTTL(10*time.Second))

// Multiple readers can acquire simultaneously
acquired, _ := rwLock.AcquireRead(ctx)

// Writer has exclusive access
acquired, _ = rwLock.AcquireWrite(ctx)
```

### Using Watchdog for Auto-Renewal

```go
// Create lock
distLock := redis.NewRedisLock(client, "long-task",
    lock.WithTTL(10*time.Second))

// Acquire lock
acquired, _ := distLock.Acquire(ctx)

// Start watchdog (renews lock every 3 seconds)
wd := redis.NewWatchdog(distLock, 10*time.Second, 3*time.Second)
wd.Start(ctx)

// Execute long-running task
time.Sleep(5 * time.Minute)

// Stop watchdog and release lock
wd.Stop()
distLock.Release(ctx)
```

## Practical Applications

### Distributed Task Scheduler

```go
// Create scheduler with distributed lock
scheduler := NewTaskScheduler(distLock, "daily-report", 1*time.Hour)

// Start scheduler with task function
scheduler.Start(ctx, func(ctx context.Context) error {
    return generateDailyReport()
})
```

### Inventory Management

```go
// Create inventory manager with distributed lock
manager := NewInventoryManager(distLock)
manager.SetStock("SKU001", 100)

// Deduct stock atomically
err := manager.DeductStock(ctx, "SKU001", 1)
if err == ErrInsufficientStock {
    return errors.New("out of stock")
}
```

### Rate Limiter

```go
// Create rate limiter: 100 requests per minute
limiter := NewRateLimiter(distLock, "api:user123", 100, 1*time.Minute)

// Check if request is allowed
allowed, _ := limiter.Allow(ctx)
if !allowed {
    return errors.New("rate limit exceeded")
}
```

## Running Tests

```bash
# Run all tests
go test ./...

# Run specific package tests
go test ./tests/...
go test ./internal/redis/...

# Run with race detection
go test -race ./...

# Run with verbose output
go test -v ./...
```

## Architecture

### Lock Lifecycle

```
Acquire Request → Try Acquire → Success/Fail
       ↓              ↓
   Wait/Retry    Execute Business Logic
       ↓              ↓
   Try Again      Release Lock
```

### Redlock Algorithm

1. Get current timestamp T1
2. Try to acquire lock on N Redis nodes sequentially
3. Calculate time spent: T2 - T1
4. Lock is acquired if:
   - Acquired on majority (N/2 + 1) of nodes
   - Total time < lock TTL
5. Effective TTL = TTL - (T2 - T1)

### ZooKeeper Lock

1. Create ephemeral sequential node under /lock/
2. List all children of /lock/
3. If created node is smallest, acquire lock
4. Otherwise, watch the node just before ours
5. When watched node is deleted, retry

### etcd Lock

1. Create a lease with TTL
2. Create key with lease using transaction
3. If key was created (revision check), acquire lock
4. Keep lease alive with KeepAlive
5. On release, delete key and revoke lease

## Design Decisions

### Interface-Based Design

```go
type Lock interface {
    Acquire(ctx context.Context) (bool, error)
    Release(ctx context.Context) error
    TTL(ctx context.Context) (time.Duration, error)
}
```

### Functional Options Pattern

```go
func WithTTL(ttl time.Duration) Option
func WithRetryCount(count int) Option
func WithRetryDelay(delay time.Duration) Option
func WithOwnerID(id string) Option
```

### Lua Scripts for Atomicity

All multi-step Redis operations are implemented as Lua scripts to ensure atomicity.

## References

- [Distributed locks with Redis](https://redis.io/docs/manual/patterns/distributed-locks/)
- [Redlock Algorithm](https://redis.io/topics/distlock)
- [Apache ZooKeeper Recipes - Locks](https://zookeeper.apache.org/doc/current/recipes.html#sc_recipes_Locks)
- [etcd Concurrency Primitives](https://etcd.io/docs/latest/dev-guide/api_concurrency_reference_v3/)
- Martin Kleppmann: [How to do distributed locking](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html)

## License

MIT

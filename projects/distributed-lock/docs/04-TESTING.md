# Distributed Lock Testing

## Test Strategy

### Unit Tests

Each package has focused unit tests:

1. **Lock Tests**: Basic acquire/release, TTL, ownership verification
2. **Reentrant Tests**: Multiple acquire/release cycles, count tracking
3. **Fair Lock Tests**: FIFO ordering, queue management
4. **Read-Write Tests**: Concurrent readers, exclusive writer
5. **Redlock Tests**: Multi-node acquisition, quorum, failure handling
6. **Watchdog Tests**: Renewal, stop, timeout
7. **Utils Tests**: ID generation

### Integration Tests

End-to-end tests with real or simulated backends:

1. **Single Lock Lifecycle**: Acquire -> Use -> Release
2. **Concurrent Access**: Multiple goroutines competing for locks
3. **Lock Expiration**: TTL-based automatic release
4. **Redlock Failover**: Node failures during acquisition
5. **ZooKeeper Cluster**: Real ZooKeeper ensemble tests
6. **etcd Cluster**: Real etcd cluster tests

## Running Tests

### All Tests

```bash
go test ./...
```

### Verbose Output

```bash
go test ./... -v
```

### Specific Package

```bash
go test ./tests/... -v
go test ./internal/redis/... -v
go test ./internal/zookeeper/... -v
go test ./internal/etcd/... -v
go test ./pkg/utils/... -v
```

### With Race Detection

```bash
go test ./... -race
```

### With Coverage

```bash
go test ./... -coverprofile=coverage.out
go tool cover -html=coverage.out
```

## Test Infrastructure

### miniredis

For unit tests, use [miniredis](https://github.com/alicebob/miniredis) - an in-memory Redis server written in Go:

```go
import "github.com/alicebob/miniredis/v2"

func TestRedisLock(t *testing.T) {
    s := miniredis.RunT(t)
    client := goredis.NewClient(&goredis.Options{Addr: s.Addr()})

    distLock := redis.NewRedisLock(client, "test-key",
        lock.WithTTL(10*time.Second))

    acquired, err := distLock.Acquire(context.Background())
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }
    if !acquired {
        t.Fatal("expected to acquire lock")
    }
}
```

### Time Control

miniredis supports time manipulation for testing TTL:

```go
func TestLockExpiration(t *testing.T) {
    s := miniredis.RunT(t)
    client := goredis.NewClient(&goredis.Options{Addr: s.Addr()})

    distLock := redis.NewRedisLock(client, "test-key",
        lock.WithTTL(1*time.Second))
    distLock.Acquire(context.Background())

    // Fast-forward time
    s.FastForward(2 * time.Second)

    // Lock should be expired
    ttl, _ := distLock.TTL(context.Background())
    if ttl != 0 {
        t.Errorf("expected lock to be expired, got TTL %v", ttl)
    }
}
```

### Multiple Redis Instances

For Redlock tests, create multiple miniredis instances:

```go
func TestRedlock(t *testing.T) {
    servers := make([]*miniredis.Miniredis, 5)
    clients := make([]*goredis.Client, 5)
    for i := 0; i < 5; i++ {
        servers[i] = miniredis.RunT(t)
        clients[i] = goredis.NewClient(&goredis.Options{Addr: servers[i].Addr()})
    }

    rl := redis.NewRedLock(clients, "test-key",
        lock.WithTTL(10*time.Second))
    // ...
}
```

## Test Cases

### Lock Tests

#### Basic Acquire and Release

```go
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
```

#### Concurrent Access

```go
func TestRedisLock_ConcurrentAccess(t *testing.T) {
    mr, client := setupMiniredis(t)
    defer mr.Close()
    defer client.Close()

    ctx := context.Background()
    distLock := redis.NewRedisLock(client, "test:concurrent",
        lock.WithTTL(10*time.Second))

    // First acquire should succeed
    acquired, _ := distLock.Acquire(ctx)
    if !acquired {
        t.Fatal("First acquire should succeed")
    }

    // Second acquire with different owner should fail
    lock2 := redis.NewRedisLock(client, "test:concurrent",
        lock.WithTTL(10*time.Second),
        lock.WithOwnerID("different-owner"),
        lock.WithRetryCount(0))

    acquired, _ = lock2.Acquire(ctx)
    if acquired {
        t.Fatal("Second acquire should fail")
    }

    // Release first lock
    distLock.Release(ctx)

    // Now second lock should succeed
    acquired, _ = lock2.Acquire(ctx)
    if !acquired {
        t.Fatal("Third acquire should succeed")
    }
}
```

#### Ownership Verification

```go
func TestRedisLock_OwnershipCheck(t *testing.T) {
    mr, client := setupMiniredis(t)
    defer mr.Close()
    defer client.Close()

    ctx := context.Background()
    distLock := redis.NewRedisLock(client, "test:ownership",
        lock.WithTTL(10*time.Second),
        lock.WithOwnerID("owner-1"))

    distLock.Acquire(ctx)

    // Try to release with different owner
    lock2 := redis.NewRedisLock(client, "test:ownership",
        lock.WithTTL(10*time.Second),
        lock.WithOwnerID("owner-2"))

    err := lock2.Release(ctx)
    if err != redis.ErrLockNotOwned {
        t.Fatalf("Expected ErrLockNotOwned, got: %v", err)
    }
}
```

#### Lock Expiration

```go
func TestRedisLock_Expiration(t *testing.T) {
    s := miniredis.RunT(t)
    client := goredis.NewClient(&goredis.Options{Addr: s.Addr()})

    distLock := redis.NewRedisLock(client, "test:expire",
        lock.WithTTL(1*time.Second))
    distLock.Acquire(context.Background())

    // Fast-forward time
    s.FastForward(2 * time.Second)

    // Another client should be able to acquire
    lock2 := redis.NewRedisLock(client, "test:expire",
        lock.WithTTL(10*time.Second))
    acquired, _ := lock2.Acquire(context.Background())
    if !acquired {
        t.Error("expected second client to acquire expired lock")
    }
}
```

#### Double Release

```go
func TestRedisLock_DoubleRelease(t *testing.T) {
    mr, client := setupMiniredis(t)
    defer mr.Close()
    defer client.Close()

    distLock := redis.NewRedisLock(client, "test:double",
        lock.WithOwnerID("owner-1"))
    distLock.Acquire(context.Background())
    distLock.Release(context.Background())

    // Second release should return error
    err := distLock.Release(context.Background())
    if err != redis.ErrLockNotOwned {
        t.Errorf("expected ErrLockNotOwned, got %v", err)
    }
}
```

### Reentrant Lock Tests

```go
func TestReentrantLock_BasicReentrant(t *testing.T) {
    mr, client := setupMiniredis(t)
    defer mr.Close()
    defer client.Close()

    ctx := context.Background()
    distLock := redis.NewReentrantRedisLock(client, "test:reentrant",
        lock.WithTTL(10*time.Second),
        lock.WithOwnerID("reentrant-owner"))

    // First acquire
    acquired, _ := distLock.Acquire(ctx)
    if !acquired {
        t.Fatal("First acquire should succeed")
    }

    // Check count
    count, _ := distLock.Count(ctx)
    if count != 1 {
        t.Fatalf("Expected count=1, got: %d", count)
    }

    // Second acquire (reentrant)
    acquired, _ = distLock.Acquire(ctx)
    if !acquired {
        t.Fatal("Second acquire should succeed")
    }

    // Check count
    count, _ = distLock.Count(ctx)
    if count != 2 {
        t.Fatalf("Expected count=2, got: %d", count)
    }

    // First release
    distLock.Release(ctx)
    count, _ = distLock.Count(ctx)
    if count != 1 {
        t.Fatalf("Expected count=1 after first release, got: %d", count)
    }

    // Second release
    distLock.Release(ctx)
    count, _ = distLock.Count(ctx)
    if count != 0 {
        t.Fatalf("Expected count=0 after second release, got: %d", count)
    }
}
```

### Fair Lock Tests

```go
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

    if len(order) != 3 {
        t.Fatalf("Expected 3 results, got: %d", len(order))
    }
}
```

### Read-Write Lock Tests

```go
func TestReadWriteLock_ConcurrentReaders(t *testing.T) {
    mr, client := setupMiniredis(t)
    defer mr.Close()
    defer client.Close()

    ctx := context.Background()
    rwLock := redis.NewReadWriteRedisLock(client, "test:rw",
        lock.WithTTL(10*time.Second))

    // Multiple readers should succeed
    for i := 0; i < 3; i++ {
        acquired, _ := rwLock.AcquireRead(ctx)
        if !acquired {
            t.Fatalf("Reader %d should acquire", i)
        }
    }

    // Check reader count
    count, _ := rwLock.ReaderCount(ctx)
    if count != 3 {
        t.Fatalf("Expected 3 readers, got: %d", count)
    }

    // Release all readers
    for i := 0; i < 3; i++ {
        rwLock.ReleaseRead(ctx)
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
    acquired, _ := rwLock.AcquireWrite(ctx)
    if !acquired {
        t.Fatal("Writer should acquire")
    }

    // Reader should fail
    rwLock2 := redis.NewReadWriteRedisLock(client, "test:rw:exclusion",
        lock.WithTTL(10*time.Second),
        lock.WithRetryCount(0))

    acquired, _ = rwLock2.AcquireRead(ctx)
    if acquired {
        t.Fatal("Reader should not acquire when writer holds lock")
    }

    // Release writer
    rwLock.ReleaseWrite(ctx)

    // Now reader should succeed
    acquired, _ = rwLock2.AcquireRead(ctx)
    if !acquired {
        t.Fatal("Reader should acquire after writer releases")
    }
}
```

### Redlock Tests

#### Quorum Success

```go
func TestRedLock_QuorumSuccess(t *testing.T) {
    servers, clients := setupMultipleMiniredis(t, 5)
    for _, s := range servers {
        defer s.Close()
    }
    for _, c := range clients {
        defer c.Close()
    }

    ctx := context.Background()
    rl := redis.NewRedLock(clients, "redlock-resource",
        lock.WithTTL(10*time.Second),
        lock.WithOwnerID("redlock-owner"))

    acquired, err := rl.Acquire(ctx)
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }
    if !acquired {
        t.Fatal("expected to acquire lock with quorum")
    }

    rl.Release(ctx)
}
```

#### Quorum Failure

```go
func TestRedLock_QuorumFailure(t *testing.T) {
    servers, clients := setupMultipleMiniredis(t, 5)
    for _, s := range servers {
        defer s.Close()
    }
    for _, c := range clients {
        defer c.Close()
    }

    ctx := context.Background()

    // Pre-acquire on 3 nodes (more than quorum)
    for i := 0; i < 3; i++ {
        clients[i].Set(ctx, "lock:redlock-resource", "other-value", 10*time.Second)
    }

    rl := redis.NewRedLock(clients, "redlock-resource",
        lock.WithTTL(10*time.Second),
        lock.WithOwnerID("redlock-owner"),
        lock.WithRetryCount(0))

    acquired, _ := rl.Acquire(ctx)
    if acquired {
        t.Error("expected acquisition to fail (quorum not reached)")
    }
}
```

### Watchdog Tests

#### Basic Renewal

```go
func TestWatchdog_BasicRenewal(t *testing.T) {
    s := miniredis.RunT(t)
    client := goredis.NewClient(&goredis.Options{Addr: s.Addr()})

    ctx := context.Background()
    distLock := redis.NewRedisLock(client, "watchdog-resource",
        lock.WithTTL(2*time.Second),
        lock.WithOwnerID("watchdog-owner"))

    distLock.Acquire(ctx)

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
```

#### Watchdog Stop

```go
func TestWatchdog_Stop(t *testing.T) {
    s := miniredis.RunT(t)
    client := goredis.NewClient(&goredis.Options{Addr: s.Addr()})

    ctx := context.Background()
    distLock := redis.NewRedisLock(client, "stop-resource",
        lock.WithTTL(10*time.Second))
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
```

## Manual Testing

### Using redis-cli

```bash
# Start Redis
redis-server

# Monitor lock operations
redis-cli MONITOR

# Check lock state
redis-cli GET lock:my-resource
redis-cli TTL lock:my-resource
```

### Using the Demo Application

```bash
# Run demo
go run examples/main.go

# Expected output:
# === Distributed Lock Examples ===
#
# Connected to Redis
#
# --- Example 1: Basic Distributed Lock ---
# Lock acquired successfully
# Lock TTL: 10s
# Executing business logic...
# Lock released
```

### Concurrent Testing

```bash
# Run multiple instances
go run examples/main.go &
go run examples/main.go &
go run examples/main.go &

# Monitor Redis
redis-cli MONITOR
```

## Test Coverage

Run with coverage report:

```bash
go test ./... -coverprofile=coverage.out
go tool cover -html=coverage.out
```

Target coverage:
- Lock interfaces: >95%
- Redis implementations: >90%
- Redlock algorithm: >85%
- Watchdog: >80%
- Utils: >95%

## Continuous Integration

Example GitHub Actions workflow:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.21'
      - run: go test ./... -race -cover
```

## Debugging Tests

### Verbose Output

```bash
go test ./tests/... -v -run TestRedisLock_BasicAcquireRelease
```

### Print Redis Commands

```bash
# Monitor Redis commands during test
redis-cli MONITOR &
go test ./tests/... -v
kill %1
```

### Race Detection

```bash
go test ./... -race
```

### Memory Leak Detection

```bash
go test ./... -memprofile=mem.out
go tool pprof mem.out
```

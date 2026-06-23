# Distributed Lock Testing

## Test Strategy

### Unit Tests

Each package has focused unit tests:

1. **Lock Tests**: Basic acquire/release, TTL, reentrant behavior
2. **Redlock Tests**: Multi-node acquisition, quorum, failure handling
3. **Watchdog Tests**: Renewal, stop, timeout
4. **Utils Tests**: UUID generation

### Integration Tests

End-to-end tests with real or simulated Redis:

1. **Single Lock Lifecycle**: Acquire -> Use -> Release
2. **Concurrent Access**: Multiple goroutines competing for locks
3. **Lock Expiration**: TTL-based automatic release
4. **Redlock Failover**: Node failures during acquisition

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
go test ./internal/lock -v
go test ./internal/redlock -v
go test ./internal/watchdog -v
go test ./pkg/utils -v
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
    client := redis.NewClient(&redis.Options{Addr: s.Addr()})

    lock := NewRedisLock(client, "test-key", 10*time.Second)

    acquired, err := lock.Acquire(context.Background())
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
    client := redis.NewClient(&redis.Options{Addr: s.Addr()})

    lock := NewRedisLock(client, "test-key", 10*time.Second)
    lock.Acquire(context.Background())

    // Fast-forward time
    s.FastForward(11 * time.Second)

    // Lock should be expired
    ttl, _ := lock.TTL(context.Background())
    if ttl != 0 {
        t.Errorf("expected lock to be expired, got TTL %v", ttl)
    }
}
```

## Test Cases

### Lock Tests

#### Basic Acquire and Release

```go
func TestRedisLock_AcquireRelease(t *testing.T) {
    s := miniredis.RunT(t)
    client := redis.NewClient(&redis.Options{Addr: s.Addr()})

    lock := NewRedisLock(client, "resource-1", 10*time.Second)
    ctx := context.Background()

    // Acquire
    acquired, err := lock.Acquire(ctx)
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }
    if !acquired {
        t.Fatal("expected to acquire lock")
    }

    // Verify held
    ttl, err := lock.TTL(ctx)
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }
    if ttl <= 0 {
        t.Fatal("expected positive TTL")
    }

    // Release
    err = lock.Release(ctx)
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }

    // Verify released
    ttl, _ = lock.TTL(ctx)
    if ttl != 0 {
        t.Errorf("expected TTL 0 after release, got %v", ttl)
    }
}
```

#### Concurrent Acquisition

```go
func TestRedisLock_ConcurrentAcquire(t *testing.T) {
    s := miniredis.RunT(t)
    client := redis.NewClient(&redis.Options{Addr: s.Addr()})

    lock := NewRedisLock(client, "resource-1", 10*time.Second)
    ctx := context.Background()

    var wg sync.WaitGroup
    acquiredCount := int32(0)

    for i := 0; i < 10; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            acquired, _ := lock.Acquire(ctx)
            if acquired {
                atomic.AddInt32(&acquiredCount, 1)
                time.Sleep(10 * time.Millisecond)
                lock.Release(ctx)
            }
        }()
    }

    wg.Wait()

    // Only one goroutine should have acquired at a time
    // (sequential execution due to lock)
}
```

#### Lock Expiration

```go
func TestRedisLock_Expiration(t *testing.T) {
    s := miniredis.RunT(t)
    client := redis.NewClient(&redis.Options{Addr: s.Addr()})

    lock := NewRedisLock(client, "resource-1", 1*time.Second)
    ctx := context.Background()

    // Acquire
    lock.Acquire(ctx)

    // Fast-forward time
    s.FastForward(2 * time.Second)

    // Another client should be able to acquire
    lock2 := NewRedisLock(client, "resource-1", 10*time.Second)
    acquired, _ := lock2.Acquire(ctx)
    if !acquired {
        t.Error("expected second client to acquire expired lock")
    }
}
```

#### Double Release

```go
func TestRedisLock_DoubleRelease(t *testing.T) {
    s := miniredis.RunT(t)
    client := redis.NewClient(&redis.Options{Addr: s.Addr()})

    lock := NewRedisLock(client, "resource-1", 10*time.Second)
    ctx := context.Background()

    lock.Acquire(ctx)
    lock.Release(ctx)

    // Second release should return error
    err := lock.Release(ctx)
    if err != ErrLockNotHeld {
        t.Errorf("expected ErrLockNotHeld, got %v", err)
    }
}
```

### Watchdog Tests

#### Basic Renewal

```go
func TestWatchdog_Renewal(t *testing.T) {
    s := miniredis.RunT(t)
    client := redis.NewClient(&redis.Options{Addr: s.Addr()})

    lock := NewRedisLock(client, "resource-1", 2*time.Second)
    wd := NewWatchdog(lock, 500*time.Millisecond)

    ctx := context.Background()
    lock.Acquire(ctx)

    wd.Start(ctx)
    defer wd.Stop()

    // Wait for several renewal cycles
    time.Sleep(3 * time.Second)

    // Lock should still be held
    ttl, _ := lock.TTL(ctx)
    if ttl <= 0 {
        t.Error("expected lock to be renewed")
    }
}
```

#### Watchdog Stop

```go
func TestWatchdog_Stop(t *testing.T) {
    s := miniredis.RunT(t)
    client := redis.NewClient(&redis.Options{Addr: s.Addr()})

    lock := NewRedisLock(client, "resource-1", 2*time.Second)
    wd := NewWatchdog(lock, 500*time.Millisecond)

    ctx := context.Background()
    lock.Acquire(ctx)

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

### Redlock Tests

#### Quorum Success

```go
func TestRedLock_QuorumSuccess(t *testing.T) {
    // Create 5 miniredis instances
    servers := make([]*miniredis.Miniredis, 5)
    clients := make([]*redis.Client, 5)
    for i := 0; i < 5; i++ {
        servers[i] = miniredis.RunT(t)
        clients[i] = redis.NewClient(&redis.Options{Addr: servers[i].Addr()})
    }

    rl := NewRedLock(clients, "resource-1", 10*time.Second)
    ctx := context.Background()

    acquired, err := rl.Acquire(ctx)
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }
    if !acquired {
        t.Fatal("expected to acquire lock")
    }

    rl.Release(ctx)
}
```

#### Quorum Failure

```go
func TestRedLock_QuorumFailure(t *testing.T) {
    // Create 5 miniredis instances
    servers := make([]*miniredis.Miniredis, 5)
    clients := make([]*redis.Client, 5)
    for i := 0; i < 5; i++ {
        servers[i] = miniredis.RunT(t)
        clients[i] = redis.NewClient(&redis.Options{Addr: servers[i].Addr()})
    }

    rl := NewRedLock(clients, "resource-1", 10*time.Second)
    ctx := context.Background()

    // Pre-acquire on 3 nodes (more than quorum)
    for i := 0; i < 3; i++ {
        clients[i].Set(ctx, "resource-1", "other-value", 10*time.Second)
    }

    acquired, _ := rl.Acquire(ctx)
    if acquired {
        t.Error("expected acquisition to fail (quorum not reached)")
    }
}
```

### Utils Tests

#### UUID Generation

```go
func TestGenerateUUID(t *testing.T) {
    uuid1 := GenerateUUID()
    uuid2 := GenerateUUID()

    // Should be different
    if uuid1 == uuid2 {
        t.Error("expected different UUIDs")
    }

    // Should be valid format
    if len(uuid1) != 36 {
        t.Errorf("expected UUID length 36, got %d", len(uuid1))
    }

    // Should contain dashes at correct positions
    if uuid1[8] != '-' || uuid1[13] != '-' || uuid1[18] != '-' || uuid1[23] != '-' {
        t.Errorf("invalid UUID format: %s", uuid1)
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
redis-cli GET resource-1
redis-cli TTL resource-1
```

### Using the Demo Application

```bash
# Run demo
go run cmd/demo/main.go

# Expected output:
# Acquiring lock...
# Lock acquired, TTL: 10s
# Performing work...
# Releasing lock...
# Lock released
```

### Concurrent Testing

```bash
# Run multiple instances
go run cmd/demo/main.go &
go run cmd/demo/main.go &
go run cmd/demo/main.go &

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
- Lock package: >90%
- Redlock package: >85%
- Watchdog package: >80%
- Utils package: >95%

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

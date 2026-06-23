# Distributed Lock Implementation

## Overview

This document describes the implementation details of the distributed lock system.

## Single-Node Redis Lock

### Lock Structure

```go
type RedisLock struct {
    client    *redis.Client
    key       string
    value     string        // Unique lock identifier (UUID)
    ttl       time.Duration
    opts      Options
}
```

### Lock Acquisition

```go
func (l *RedisLock) Acquire(ctx context.Context) (bool, error) {
    ok, err := l.client.SetNX(ctx, l.key, l.value, l.ttl).Result()
    if err != nil {
        return false, fmt.Errorf("acquire lock: %w", err)
    }
    return ok, nil
}
```

The `SET NX EX` command is atomic in Redis, ensuring no race condition between checking existence and setting the value.

### Lock Release

```go
const releaseScript = `
if redis.call("GET", KEYS[1]) == ARGV[1] then
    return redis.call("DEL", KEYS[1])
else
    return 0
end
`

func (l *RedisLock) Release(ctx context.Context) error {
    result, err := l.client.Eval(ctx, releaseScript, []string{l.key}, l.value).Int64()
    if err != nil {
        return fmt.Errorf("release lock: %w", err)
    }
    if result == 0 {
        return ErrLockNotHeld
    }
    return nil
}
```

**Why Lua Script?** The release operation requires atomic GET + DEL. Without a Lua script, another client could acquire the lock between GET and DEL.

### TTL Query

```go
func (l *RedisLock) TTL(ctx context.Context) (time.Duration, error) {
    ttl, err := l.client.TTL(ctx, l.key).Result()
    if err != nil {
        return 0, fmt.Errorf("get ttl: %w", err)
    }
    if ttl == -2 {
        return 0, nil  // Key does not exist
    }
    if ttl == -1 {
        return 0, nil  // Key exists but no TTL
    }
    return ttl, nil
}
```

### Lock Renewal

```go
const renewScript = `
if redis.call("GET", KEYS[1]) == ARGV[1] then
    return redis.call("PEXPIRE", KEYS[1], ARGV[2])
else
    return 0
end
`

func (l *RedisLock) Renew(ctx context.Context) (bool, error) {
    result, err := l.client.Eval(ctx, renewScript,
        []string{l.key}, l.value, l.ttl.Milliseconds()).Int64()
    if err != nil {
        return false, fmt.Errorf("renew lock: %w", err)
    }
    return result == 1, nil
}
```

## Redlock Algorithm

### RedLock Structure

```go
type RedLock struct {
    clients []*redis.Client
    key     string
    value   string
    ttl     time.Duration
    quorum  int
}
```

### Quorum Calculation

```go
func NewRedLock(clients []*redis.Client, key string, ttl time.Duration) *RedLock {
    n := len(clients)
    return &RedLock{
        clients: clients,
        key:     key,
        value:   generateUUID(),
        ttl:     ttl,
        quorum:  n/2 + 1,
    }
}
```

### Lock Acquisition

```go
func (rl *RedLock) Acquire(ctx context.Context) (bool, error) {
    startTime := time.Now()
    acquired := 0

    // Try to acquire lock on each node
    for _, client := range rl.clients {
        ok, err := client.SetNX(ctx, rl.key, rl.value, rl.ttl).Result()
        if err != nil {
            continue  // Skip failed nodes
        }
        if ok {
            acquired++
        }
    }

    // Check time budget
    elapsed := time.Since(startTime)
    if elapsed >= rl.ttl {
        // Time exceeded, release all acquired locks
        rl.releaseAll(ctx)
        return false, nil
    }

    // Check quorum
    if acquired < rl.quorum {
        rl.releaseAll(ctx)
        return false, nil
    }

    // Calculate effective TTL
    rl.effectiveTTL = rl.ttl - elapsed
    return true, nil
}
```

### Lock Release

```go
func (rl *RedLock) Release(ctx context.Context) error {
    for _, client := range rl.clients {
        // Use Lua script to ensure we only delete our own lock
        client.Eval(ctx, releaseScript, []string{rl.key}, rl.value)
    }
    return nil
}
```

### Effective TTL Calculation

```
TTL = 10 seconds
Acquisition start: T1 = 1000ms
Acquisition end: T2 = 1200ms
Elapsed: 200ms
Effective TTL: 10s - 200ms = 9.8s
```

The effective TTL is always less than the original TTL to account for the time spent acquiring locks across multiple nodes.

## Watchdog Implementation

### Watchdog Structure

```go
type Watchdog struct {
    lock     Lock
    interval time.Duration
    stopCh   chan struct{}
    doneCh   chan struct{}
    running  bool
    mu       sync.Mutex
}
```

### Start Watchdog

```go
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
```

### Watchdog Loop

```go
func (w *Watchdog) run(ctx context.Context) {
    defer close(w.doneCh)

    ticker := time.NewTicker(w.interval)
    defer ticker.Stop()

    for {
        select {
        case <-w.stopCh:
            return
        case <-ticker.C:
            // Check if lock still exists
            ttl, err := w.lock.TTL(ctx)
            if err != nil || ttl <= 0 {
                // Lock expired or error
                return
            }

            // Renew lock
            ok, err := w.lock.Renew(ctx)
            if err != nil || !ok {
                // Renewal failed
                return
            }
        }
    }
}
```

### Stop Watchdog

```go
func (w *Watchdog) Stop() {
    w.mu.Lock()
    if !w.running {
        w.mu.Unlock()
        return
    }
    w.running = false
    close(w.stopCh)
    w.mu.Unlock()

    // Wait for goroutine to finish
    <-w.doneCh
}
```

## Unique ID Generation

### UUID v4 Generation

```go
func GenerateUUID() string {
    uuid := make([]byte, 16)
    rand.Read(uuid)

    // Set version (4) and variant (RFC 4122)
    uuid[6] = (uuid[6] & 0x0f) | 0x40
    uuid[8] = (uuid[8] & 0x3f) | 0x80

    return fmt.Sprintf("%x-%x-%x-%x-%x",
        uuid[0:4], uuid[4:6], uuid[6:8], uuid[8:10], uuid[10:16])
}
```

### Why UUID?

- Globally unique across all clients
- No coordination needed between lock holders
- Can be used to identify lock owner for debugging

## Retry Strategy

### Basic Retry

```go
func AcquireWithRetry(ctx context.Context, lock Lock, maxRetries int, delay time.Duration) (bool, error) {
    for i := 0; i < maxRetries; i++ {
        acquired, err := lock.Acquire(ctx)
        if err != nil {
            return false, err
        }
        if acquired {
            return true, nil
        }

        select {
        case <-ctx.Done():
            return false, ctx.Err()
        case <-time.After(delay):
            // Retry
        }
    }
    return false, nil
}
```

### Exponential Backoff

```go
func AcquireWithBackoff(ctx context.Context, lock Lock, maxRetries int, baseDelay time.Duration) (bool, error) {
    delay := baseDelay
    for i := 0; i < maxRetries; i++ {
        acquired, err := lock.Acquire(ctx)
        if err != nil {
            return false, err
        }
        if acquired {
            return true, nil
        }

        select {
        case <-ctx.Done():
            return false, ctx.Err()
        case <-time.After(delay):
            delay *= 2  // Exponential backoff
        }
    }
    return false, nil
}
```

## Error Definitions

```go
var (
    ErrLockNotHeld    = errors.New("lock not held by this caller")
    ErrLockExpired    = errors.New("lock has expired")
    ErrAcquireFailed  = errors.New("failed to acquire lock")
    ErrReleaseFailed  = errors.New("failed to release lock")
    ErrRenewFailed    = errors.New("failed to renew lock")
    ErrTimeout        = errors.New("lock operation timed out")
)
```

## Thread Safety

### Lock State

The `RedisLock` struct is safe for concurrent use because:
- All state is stored in Redis, not locally
- Each operation is independent
- No shared mutable state in the struct

### Watchdog State

The `Watchdog` struct uses mutex for thread safety:

```go
type Watchdog struct {
    mu      sync.Mutex  // Protects running state
    running bool
    stopCh  chan struct{}
    doneCh  chan struct{}
}
```

### Reentrant Lock State

The reentrant lock tracks count locally:

```go
type ReentrantLock struct {
    mu      sync.Mutex  // Protects count
    count   int
    ownerID string
}
```

## Performance Considerations

### Latency

- Single lock acquire: ~1-2ms (local Redis)
- Redlock acquire: ~5-10ms (5 Redis nodes)
- Lock release: ~1-2ms
- Lock renewal: ~1-2ms

### Throughput

- Single Redis: ~100k ops/sec
- Redlock (5 nodes): ~20k locks/sec
- With watchdog: Overhead per active lock

### Memory

- Per lock: ~100 bytes in Redis
- Per watchdog: ~1KB in Go heap

## Known Limitations

1. **No Fencing Tokens**: Current implementation does not support fencing tokens
2. **No Cluster Mode**: Does not support Redis Cluster key hashing
3. **Clock Dependency**: Redlock assumes bounded clock drift
4. **No Shared Lock**: Only exclusive locks, no read/write lock separation
5. **No Lock Escalation**: Cannot upgrade from shared to exclusive lock

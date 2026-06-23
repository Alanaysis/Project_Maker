# Distributed Lock Design

## Goals

1. Implement a production-grade distributed lock system in Go
2. Support single-node Redis lock and Redlock algorithm
3. Provide automatic lock renewal (watchdog)
4. Support reentrant locks and fair queuing
5. Keep code clean, testable, and extensible

## Architecture

### Component Overview

```
┌────────────────────────────────────────────────────────────────┐
│                    Distributed Lock System                       │
│                                                                │
│  ┌──────────┐    ┌──────────────┐    ┌────────────────────┐   │
│  │  Lock     │───▶│  Redlock     │───▶│  Watchdog          │   │
│  │  Interface│    │  Algorithm   │    │  (Auto-renewal)    │   │
│  └──────────┘    └──────────────┘    └────────────────────┘   │
│       │                 │                      │               │
│       ▼                 ▼                      ▼               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Redis Client                           │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │  │
│  │  │ Node 1  │  │ Node 2  │  │ Node 3  │  │ Node N  │   │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Utilities                              │  │
│  │  ┌──────────┐  ┌──────────────┐  ┌──────────────────┐   │  │
│  │  │ ID Gen   │  │ Lua Scripts  │  │ Retry Strategy   │   │  │
│  │  └──────────┘  └──────────────┘  └──────────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### Package Structure

```
distributed-lock/
├── internal/
│   ├── lock/          # Single-node Redis lock
│   ├── redlock/       # Redlock algorithm
│   └── watchdog/      # Lock renewal mechanism
├── pkg/
│   └── utils/         # Shared utilities (ID generation)
└── cmd/
    └── demo/          # Demo application
```

## Lock Interface

### Core Interface

```go
// Lock defines the interface for all distributed lock implementations
type Lock interface {
    // Acquire attempts to acquire the lock
    // Returns true if acquired, false if already held
    Acquire(ctx context.Context) (bool, error)

    // Release releases the lock
    // Only releases if the caller is the current holder
    Release(ctx context.Context) error

    // TTL returns the remaining time-to-live of the lock
    // Returns 0 if the lock is not held
    TTL(ctx context.Context) (time.Duration, error)
}
```

### Implementation Hierarchy

```
Lock (interface)
├── RedisLock (single-node Redis)
│   ├── Basic lock (SET NX EX)
│   ├── Reentrant lock (count-based)
│   └── Fair lock (queue-based)
└── RedLock (multi-node Redlock)
    └── Uses multiple RedisLock instances
```

## Single-Node Redis Lock

### Design

```go
type RedisLock struct {
    client     *redis.Client
    key        string
    value      string  // Unique identifier
    ttl        time.Duration
    reentrant  bool
    count      int     // Reentrant count
}
```

### Lock Acquisition Flow

```
1. Generate unique lock value (UUID)
2. Execute SET key value NX EX ttl
3. If OK, lock acquired
4. If nil, lock already held
```

### Lock Release Flow

```
1. Execute Lua script:
   if GET(key) == value then
       DEL(key)
       return 1
   else
       return 0
   end
2. If 1, lock released
3. If 0, lock not owned by this caller
```

### Design Decisions

1. **Lua Scripts**: All multi-step operations use Lua scripts for atomicity
2. **Unique Values**: Each lock holder has a unique UUID to prevent accidental release
3. **TTL Enforcement**: Every lock has a TTL to prevent deadlocks from crashes
4. **Reentrant Support**: Optional reentrant mode for recursive acquisition

## Redlock Algorithm

### Design

```go
type RedLock struct {
    clients   []*redis.Client
    key       string
    value     string
    ttl       time.Duration
    quorum    int  // Majority count
}
```

### Algorithm Flow

```
1. Record start time T1
2. For each Redis node:
   a. Try to acquire lock (SET NX EX)
   b. Record time spent
3. Calculate total time: T2 - T1
4. Check success criteria:
   - Acquired on >= quorum nodes
   - Total time < TTL
5. If successful:
   - Effective TTL = TTL - (T2 - T1)
   - Return success
6. If failed:
   - Release all acquired locks
   - Return failure
```

### Design Decisions

1. **Quorum Calculation**: (N/2) + 1, where N is the number of nodes
2. **Sequential Acquisition**: Acquire locks one by one to detect failures early
3. **Time Budget**: Total acquisition time must be less than TTL
4. **Cleanup on Failure**: Release all acquired locks if quorum not reached

### Failure Scenarios

```
Scenario 1: Node failure during acquisition
├── Node 1: Acquired ✓
├── Node 2: Failed (connection error)
├── Node 3: Acquired ✓
├── Node 4: Acquired ✓
├── Node 5: Acquired ✓
└── Result: Success (4/5 >= quorum of 3)

Scenario 2: Too many failures
├── Node 1: Acquired ✓
├── Node 2: Failed
├── Node 3: Failed
├── Node 4: Acquired ✓
├── Node 5: Failed
└── Result: Failure (2/5 < quorum of 3)

Scenario 3: Time exceeded
├── Total time: 12 seconds
├── TTL: 10 seconds
└── Result: Failure (time exceeded TTL)
```

## Watchdog (Lock Renewal)

### Design

```go
type Watchdog struct {
    lock       Lock
    interval   time.Duration
    stopCh     chan struct{}
    running    bool
    mu         sync.Mutex
}
```

### Renewal Flow

```
1. Start watchdog goroutine
2. Every interval/3 seconds:
   a. Check if lock still exists (TTL > 0)
   b. If exists, renew TTL (SET EX)
   c. If not exists, stop watchdog
3. On stop signal:
   a. Stop goroutine
   b. Release lock (optional)
```

### Design Decisions

1. **Proactive Renewal**: Renew at TTL/3 intervals to prevent expiry
2. **Graceful Stop**: Use channel-based stop signaling
3. **Lock Verification**: Check lock existence before renewal
4. **Thread Safety**: Mutex for state management

### Renewal Strategy

```
Timeline:
|--TTL/3--|--TTL/3--|--TTL/3--|
|         |         |         |
Acquire   Renew 1   Renew 2   Expire (if not renewed)

Watchdog:
|--interval--|--interval--|--interval--|
|            |            |            |
Check+Renew  Check+Renew  Check+Renew
```

## Reentrant Lock

### Design

```go
type ReentrantLock struct {
    baseLock  Lock
    ownerID   string
    count     int
    mu        sync.Mutex
}
```

### Behavior

```
Lock(key) by client-A: count=1, acquired
Lock(key) by client-A: count=2, already held
Lock(key) by client-B: blocked, waiting
Unlock(key) by client-A: count=1, still held
Unlock(key) by client-A: count=0, released
Lock(key) by client-B: acquired
```

### Implementation

Uses Lua script for atomic count tracking:

```lua
local key = KEYS[1]
local owner = ARGV[1]
local ttl = ARGV[2]

local current = redis.call('HGET', key, 'owner')
if current == owner then
    redis.call('HINCRBY', key, 'count', 1)
    redis.call('EXPIRE', key, ttl)
    return 1
elseif current == false then
    redis.call('HSET', key, 'owner', owner, 'count', 1)
    redis.call('EXPIRE', key, ttl)
    return 1
else
    return 0
end
```

## Fair Lock

### Design

```go
type FairLock struct {
    client    *redis.Client
    key       string
    queueKey  string  // key + ":queue"
    value     string
    ttl       time.Duration
}
```

### Behavior

```
1. Client A joins queue: RPUSH lock:queue "client-A"
2. Client B joins queue: RPUSH lock:queue "client-B"
3. Client A checks position: LINDEX lock:queue 0 == "client-A"
4. Client A acquires lock
5. Client A releases lock: DEL lock + LPOP lock:queue
6. Client B is now first in queue
```

### Implementation

Uses Redis List for FIFO ordering:

```lua
-- Join queue
redis.call('RPUSH', KEYS[2], ARGV[1])

-- Check if first in queue
local first = redis.call('LINDEX', KEYS[2], 0)
if first == ARGV[1] then
    -- Try to acquire lock
    local acquired = redis.call('SET', KEYS[1], ARGV[1], 'NX', 'EX', ARGV[2])
    if acquired then
        return 1
    end
end
return 0
```

## Error Handling

### Lock Acquisition Errors

| Error | Cause | Action |
|-------|-------|--------|
| Connection refused | Redis down | Return error, let caller retry |
| Lock already held | Contention | Return false, caller can retry |
| Timeout | Network issue | Return error with context |
| Context cancelled | Caller cancelled | Return context error |

### Lock Release Errors

| Error | Cause | Action |
|-------|-------|--------|
| Lock not owned | Expired or stolen | Return specific error |
| Connection error | Redis down | Return error, lock will expire via TTL |
| Already released | Double release | Return nil (idempotent) |

### Watchdog Errors

| Error | Cause | Action |
|-------|-------|--------|
| Renewal failed | Lock expired | Stop watchdog, notify caller |
| Connection lost | Redis down | Retry with backoff |
| Lock stolen | Another holder | Stop watchdog, notify caller |

## Testing Strategy

### Unit Tests

1. **Lock Interface Tests**: Verify interface compliance
2. **Acquire/Release Tests**: Basic lock operations
3. **Reentrant Tests**: Multiple acquire/release cycles
4. **Fair Lock Tests**: Queue ordering verification
5. **Watchdog Tests**: Renewal behavior
6. **Error Handling Tests**: Connection failures, timeouts

### Integration Tests

1. **End-to-End**: Full lock lifecycle with real Redis
2. **Redlock Tests**: Multi-node lock acquisition
3. **Concurrent Tests**: Multiple goroutines competing for locks
4. **Failure Simulation**: Redis node failures during lock operations

### Test Infrastructure

- **miniredis**: In-memory Redis for fast unit tests
- **testcontainers**: Real Redis instances for integration tests
- **Race Detection**: `go test -race` for concurrency issues

## Future Improvements

1. **Fencing Tokens**: Monotonically increasing tokens for stale write prevention
2. **Redis Cluster Support**: Key hashing for cluster mode
3. **Exponential Backoff**: Smarter retry strategies
4. **Metrics**: Lock acquisition latency, contention rate
5. **Distributed Semaphore**: Multiple permits instead of exclusive lock
6. **Lock Escalation**: Upgrade from shared to exclusive lock

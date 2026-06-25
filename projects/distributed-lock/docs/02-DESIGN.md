# Distributed Lock Design

## Goals

1. Implement a production-grade distributed lock system in Go
2. Support multiple backends: Redis, ZooKeeper, etcd
3. Provide various lock types: basic, reentrant, fair, read-write
4. Include automatic lock renewal (watchdog)
5. Support practical applications: task scheduling, inventory, rate limiting
6. Keep code clean, testable, and extensible

## Architecture

### Component Overview

```
┌────────────────────────────────────────────────────────────────────┐
│                    Distributed Lock System                         │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Lock Interfaces                            │  │
│  │  ┌─────────┐  ┌──────────────┐  ┌─────────┐  ┌───────────┐ │  │
│  │  │  Lock   │  │ReentrantLock │  │FairLock │  │ReadWrite  │ │  │
│  │  └─────────┘  └──────────────┘  └─────────┘  └───────────┘ │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              │                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Backend Implementations                    │  │
│  │  ┌─────────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │     Redis        │  │  ZooKeeper   │  │     etcd     │   │  │
│  │  │  ┌───────────┐  │  │  ┌────────┐  │  │  ┌────────┐  │   │  │
│  │  │  │ Basic     │  │  │  │Ephemeral│  │  │  │ Lease  │  │   │  │
│  │  │  │ Redlock   │  │  │  │Sequential│ │  │  │Revision│  │   │  │
│  │  │  │ Reentrant │  │  │  │ Watch   │  │  │  │ Compare│  │   │  │
│  │  │  │ Fair      │  │  │  └────────┘  │  │  └────────┘  │   │  │
│  │  │  │ ReadWrite │  │  │              │  │              │   │  │
│  │  │  └───────────┘  │  │              │  │              │   │  │
│  │  └─────────────────┘  └──────────────┘  └──────────────┘   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              │                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Supporting Components                      │  │
│  │  ┌──────────┐  ┌──────────────┐  ┌──────────────────────┐   │  │
│  │  │ Watchdog │  │ ID Generator │  │   Applications       │   │  │
│  │  │(Auto-    │  │ (UUID-based) │  │ ┌──────────────────┐ │   │  │
│  │  │ renewal) │  │              │  │ │ Task Scheduler   │ │   │  │
│  │  └──────────┘  └──────────────┘  │ │ Inventory Mgmt   │ │   │  │
│  │                                   │ │ Rate Limiter     │ │   │  │
│  │                                   │ └──────────────────┘ │   │  │
│  │                                   └──────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

### Package Structure

```
distributed-lock/
├── internal/
│   ├── lock/              # Core interfaces and types
│   │   └── lock.go
│   ├── redis/             # Redis-based implementations
│   │   ├── lock.go        # Basic Redis lock
│   │   ├── redlock.go     # Redlock algorithm
│   │   ├── reentrant.go   # Reentrant lock
│   │   ├── fair.go        # Fair (FIFO) lock
│   │   ├── rwlock.go      # Read-write lock
│   │   └── watchdog.go    # Auto-renewal mechanism
│   ├── zookeeper/         # ZooKeeper-based implementation
│   │   └── lock.go
│   └── etcd/              # etcd-based implementation
│       └── lock.go
├── pkg/
│   └── utils/             # Shared utilities
│       └── id.go          # ID generation
├── examples/              # Practical applications
│   ├── task_scheduler.go
│   ├── inventory.go
│   └── ratelimiter.go
└── tests/                 # Test files
    ├── lock_test.go
    ├── redlock_test.go
    └── watchdog_test.go
```

## Lock Interfaces

### Base Lock Interface

```go
type Lock interface {
    Acquire(ctx context.Context) (bool, error)
    Release(ctx context.Context) error
    TTL(ctx context.Context) (time.Duration, error)
}
```

### Extended Interfaces

```go
type ReentrantLock interface {
    Lock
    Count(ctx context.Context) (int, error)
}

type ReadWriteLock interface {
    AcquireRead(ctx context.Context) (bool, error)
    AcquireWrite(ctx context.Context) (bool, error)
    ReleaseRead(ctx context.Context) error
    ReleaseWrite(ctx context.Context) error
}

type FairLock interface {
    Lock
    Position(ctx context.Context) (int, error)
    QueueLength(ctx context.Context) (int, error)
}
```

### Functional Options

```go
type Option func(*Config)

func WithTTL(ttl time.Duration) Option
func WithRetryCount(count int) Option
func WithRetryDelay(delay time.Duration) Option
func WithOwnerID(id string) Option
```

## Redis Backend

### Basic Redis Lock

**Algorithm**: SET NX EX with ownership verification

```
Acquire:
1. Generate unique owner ID
2. SET key owner_id NX EX ttl
3. Return true if OK, false if nil

Release:
1. Lua script: if GET(key) == owner_id then DEL(key)
2. Return error if not owned

Extend:
1. Lua script: if GET(key) == owner_id then EXPIRE(key, ttl)
2. Return true if extended
```

**Lua Scripts**:
```lua
-- Acquire
if redis.call("SET", KEYS[1], ARGV[1], "NX", "EX", ARGV[2]) then
    return 1
end
return 0

-- Release
if redis.call("GET", KEYS[1]) == ARGV[1] then
    return redis.call("DEL", KEYS[1])
end
return 0

-- Extend
if redis.call("GET", KEYS[1]) == ARGV[1] then
    return redis.call("EXPIRE", KEYS[1], ARGV[2])
end
return 0
```

### Redlock Algorithm

**Algorithm**: Multi-node consensus with time budget

```
1. Record start time T1
2. For each Redis node (N total):
   a. Try to acquire lock (SET NX EX)
   b. Skip failed nodes
3. Calculate elapsed time: T2 - T1
4. Check success criteria:
   - Acquired on >= N/2 + 1 nodes (quorum)
   - Elapsed time < TTL
5. If successful:
   - Effective TTL = TTL - elapsed
   - Store acquired node indices
6. If failed:
   - Release all acquired locks
   - Return failure

Release:
- Release lock on all stored node indices
```

**Quorum Calculation**:
- N = 5 nodes → quorum = 3
- N = 3 nodes → quorum = 2
- N = 1 node → quorum = 1 (degrades to single-node)

### Reentrant Lock

**Algorithm**: Count-based reentrant tracking

```
Keys:
- lock:reentrant:{name} → owner_id
- lock:reentrant:{name}:count → count

Acquire:
1. GET lock:reentrant:{name}
2. If empty: SET owner_id, count=1, return acquired
3. If matches owner: INCR count, return acquired
4. If different owner: return not acquired

Release:
1. GET lock:reentrant:{name}
2. If not owned: return error
3. DECR count
4. If count <= 0: DEL both keys
5. Return success
```

### Fair Lock

**Algorithm**: FIFO queue with ordered acquisition

```
Keys:
- lock:fair:{name} → owner_id (the actual lock)
- lock:fair:{name}:queue → List of waiters

Acquire:
1. RPUSH queue entry_id (join queue)
2. Loop:
   a. LINDEX queue 0 (check first)
   b. If first == entry_id:
      - SET NX lock owner_id
      - If acquired: LPOP queue, return success
   c. Wait and retry

Release:
1. DEL lock key
2. (Entry already removed from queue on acquire)
```

### Read-Write Lock

**Algorithm**: Reader count + writer mutex

```
Keys:
- lock:rw:{name}:readers → reader count
- lock:rw:{name}:writer → writer owner_id

AcquireRead:
1. Check if writer exists
2. If no writer: INCR readers, return success
3. If writer exists: return not acquired

AcquireWrite:
1. Check if readers > 0
2. If readers > 0: return not acquired
3. SET NX writer owner_id
4. Return success/failure

ReleaseRead:
1. DECR readers
2. If count <= 0: DEL readers key

ReleaseWrite:
1. Verify ownership
2. DEL writer key
```

### Watchdog

**Algorithm**: Periodic TTL renewal

```
Configuration:
- ttl: Lock's time-to-live
- interval: Renewal interval (typically ttl/3)

Flow:
1. Start goroutine
2. Every interval:
   a. Call lock.Extend(ttl)
   b. If failed: stop watchdog
3. On stop signal: exit goroutine
```

## ZooKeeper Backend

### Lock Algorithm

**Algorithm**: Ephemeral sequential nodes with Watch

```
Acquire:
1. Ensure base path exists
2. Create ephemeral sequential node: /lock/{name}/lock-
3. List all children of /lock/{name}
4. Sort children lexicographically
5. If created node is smallest:
   - Lock acquired
6. Otherwise:
   - Watch the node just before ours
   - Wait for watch event
   - Retry from step 3

Release:
1. Delete our ephemeral node
2. Node auto-deletes on session expiry

Properties:
- Ephemeral nodes auto-cleanup on crash
- Sequential nodes ensure FIFO ordering
- Watch mechanism avoids thundering herd
```

### Key Design Decisions

1. **Ephemeral Nodes**: Auto-cleanup on session expiry prevents deadlocks
2. **Sequential Ordering**: Natural FIFO ordering without external queue
3. **Watch on Previous**: Only watch one node, not all nodes (avoid thundering herd)
4. **Session-Based TTL**: TTL is session timeout, not per-key

## etcd Backend

### Lock Algorithm (Concurrency Package)

**Algorithm**: etcd mutex with session/lease

```
Acquire:
1. Create session with TTL
2. Create mutex with session
3. Try to acquire mutex
4. If success: lock acquired
5. If locked: return not acquired

Release:
1. Unlock mutex
2. Close session (revokes lease)

Properties:
- Session auto-renews lease
- Mutex uses etcd's revision for ordering
- Strong consistency via Raft consensus
```

### Lock Algorithm (Revision-Based)

**Algorithm**: Key creation with lease and revision comparison

```
Acquire:
1. Create lease with TTL
2. Try to create key with lease (transaction):
   - If key doesn't exist: create, success
   - If key exists: watch for deletion
3. Start KeepAlive for lease

Release:
1. Delete key
2. Revoke lease

Properties:
- Lease-based expiration
- Revision provides global ordering
- Transaction ensures atomicity
```

## Practical Applications

### Distributed Task Scheduler

```
Problem: Only one instance should run scheduled tasks

Solution:
1. Create lock for each task
2. Before executing task, try to acquire lock
3. If acquired: execute task
4. If not acquired: skip (another instance is running)

Features:
- Configurable task interval
- Lock TTL > task execution time
- Watchdog for long-running tasks
```

### Inventory Management

```
Problem: Prevent overselling in distributed e-commerce

Solution:
1. Create lock for each SKU
2. Before deducting stock, acquire lock
3. Check stock >= requested quantity
4. Deduct stock
5. Release lock

Features:
- Atomic stock operations
- Batch deduction support
- Refund support
```

### Rate Limiter

```
Problem: Enforce rate limits across multiple servers

Solution:
1. Create lock for each rate limit key
2. Before allowing request, acquire lock
3. Check current count < max requests
4. Increment count
5. Release lock

Algorithms:
- Fixed Window: Simple counter per time window
- Sliding Window: Track individual request timestamps
- Token Bucket: Allow bursts while maintaining average
```

## Error Handling

### Error Types

```go
var (
    ErrLockNotAcquired = errors.New("lock not acquired")
    ErrLockNotOwned    = errors.New("lock not owned by this caller")
    ErrSessionExpired  = errors.New("session expired")
)
```

### Error Handling Strategy

| Error | Cause | Action |
|-------|-------|--------|
| Connection refused | Backend down | Return error, caller retries |
| Lock already held | Contention | Return false, caller can retry |
| Timeout | Network issue | Return error with context |
| Context cancelled | Caller cancelled | Return context error |
| Lock not owned | Expired/stolen | Return specific error |
| Session expired | ZooKeeper session | Return error, recreate session |

## Testing Strategy

### Unit Tests

1. **Lock Interface Compliance**: Verify all implementations
2. **Basic Operations**: Acquire, release, TTL
3. **Concurrent Access**: Multiple goroutines competing
4. **Reentrant Behavior**: Multiple acquire/release cycles
5. **Fair Ordering**: FIFO verification
6. **Read-Write Semantics**: Concurrent readers, exclusive writer
7. **Watchdog Renewal**: Auto-renewal behavior
8. **Error Handling**: Connection failures, timeouts

### Integration Tests

1. **End-to-End**: Full lifecycle with real backends
2. **Redlock Consensus**: Multi-node acquisition
3. **ZooKeeper Cluster**: Real ZooKeeper ensemble
4. **etcd Cluster**: Real etcd cluster

### Test Infrastructure

- **miniredis**: In-memory Redis for fast unit tests
- **testcontainers**: Real backend instances for integration tests
- **Race Detection**: `go test -race` for concurrency issues

## Performance Considerations

### Redis

- **Latency**: Sub-millisecond for single-node
- **Throughput**: 100K+ ops/sec per node
- **Redlock Overhead**: N * single-node latency

### ZooKeeper

- **Latency**: 10-100ms (depends on ensemble size)
- **Throughput**: 10K+ ops/sec
- **Watch Efficiency**: No polling required

### etcd

- **Latency**: 10-50ms (Raft consensus)
- **Throughput**: 10K+ ops/sec
- **Lease Renewal**: Background KeepAlive

## Future Improvements

1. **Fencing Tokens**: Monotonically increasing tokens for stale write prevention
2. **Redis Cluster Support**: Key hashing for cluster mode
3. **Exponential Backoff**: Smarter retry strategies with jitter
4. **Metrics**: Lock acquisition latency, contention rate, renewal success
5. **Distributed Semaphore**: Multiple permits instead of exclusive lock
6. **Lock Escalation**: Upgrade from shared to exclusive lock
7. **Multi-Key Locks**: Atomic acquisition of multiple locks
8. **Lock Hierarchies**: Parent-child lock relationships

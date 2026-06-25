# Distributed Lock Implementation

## Overview

This document describes the implementation details of the distributed lock system with multiple backends (Redis, ZooKeeper, etcd) and various lock types (basic, reentrant, fair, read-write).

## Redis Backend

### Basic Redis Lock

**Structure**:
```go
type RedisLock struct {
    client     *goredis.Client
    key        string
    ownerID    string
    ttl        time.Duration
    retryCount int
    retryDelay time.Duration
}
```

**Acquisition**:
```go
func (l *RedisLock) Acquire(ctx context.Context) (bool, error) {
    for i := 0; i <= l.retryCount; i++ {
        result, err := acquireScript.Run(ctx, l.client, []string{l.key}, l.ownerID, int(l.ttl.Seconds())).Int()
        if err != nil {
            return false, err
        }
        if result == 1 {
            return true, nil
        }
        if i < l.retryCount {
            select {
            case <-ctx.Done():
                return false, ctx.Err()
            case <-time.After(l.retryDelay):
            }
        }
    }
    return false, nil
}
```

**Lua Scripts**:
```lua
-- Acquire (atomic SET NX EX)
if redis.call("SET", KEYS[1], ARGV[1], "NX", "EX", ARGV[2]) then
    return 1
end
return 0

-- Release (atomic ownership check + delete)
if redis.call("GET", KEYS[1]) == ARGV[1] then
    return redis.call("DEL", KEYS[1])
end
return 0

-- Extend (atomic ownership check + expire)
if redis.call("GET", KEYS[1]) == ARGV[1] then
    return redis.call("EXPIRE", KEYS[1], ARGV[2])
end
return 0
```

### Redlock Algorithm

**Structure**:
```go
type RedLock struct {
    clients    []*goredis.Client
    key        string
    ownerID    string
    ttl        time.Duration
    quorum     int
    retryCount int
    retryDelay time.Duration
    acquiredOn []int
}
```

**Algorithm**:
```go
func (rl *RedLock) tryAcquire(ctx context.Context) (bool, error) {
    startTime := time.Now()
    acquiredNodes := make([]int, 0, len(rl.clients))

    // Step 1: Try to acquire lock on all nodes
    for i, client := range rl.clients {
        result, err := acquireScript.Run(ctx, client, []string{rl.key}, rl.ownerID, int(rl.ttl.Seconds())).Int()
        if err != nil {
            continue
        }
        if result == 1 {
            acquiredNodes = append(acquiredNodes, i)
        }
    }

    // Step 2: Calculate elapsed time
    elapsed := time.Since(startTime)

    // Step 3: Check quorum and time validity
    validityTime := rl.ttl - elapsed

    if len(acquiredNodes) < rl.quorum || validityTime <= 0 {
        rl.releaseAll(ctx, acquiredNodes)
        return false, nil
    }

    rl.acquiredOn = acquiredNodes
    return true, nil
}
```

**Quorum Calculation**:
- N = 5 nodes → quorum = 3 (5/2 + 1)
- N = 3 nodes → quorum = 2 (3/2 + 1)
- N = 1 node → quorum = 1 (degrades to single-node)

### Reentrant Lock

**Structure**:
```go
type ReentrantRedisLock struct {
    client     *goredis.Client
    key        string
    countKey   string
    ownerID    string
    ttl        time.Duration
    retryCount int
    retryDelay time.Duration
}
```

**Lua Scripts**:
```lua
-- Acquire (reentrant)
local current = redis.call("GET", KEYS[1])
if current == false then
    redis.call("SET", KEYS[1], "1", "EX", ARGV[2])
    return 1
end
if current == ARGV[1] then
    redis.call("INCR", KEYS[2])
    redis.call("EXPIRE", KEYS[1], ARGV[2])
    return redis.call("GET", KEYS[2])
end
return 0

-- Release (reentrant)
if redis.call("GET", KEYS[1]) ~= ARGV[1] then
    return -1
end
local count = redis.call("DECR", KEYS[2])
if count <= 0 then
    redis.call("DEL", KEYS[1])
    redis.call("DEL", KEYS[2])
    return 0
end
return count
```

**Keys**:
- `lock:reentrant:{name}` → owner_id
- `lock:reentrant:{name}:count` → reentrant count

### Fair Lock

**Structure**:
```go
type FairRedisLock struct {
    client     *goredis.Client
    key        string
    queueKey   string
    ownerID    string
    ttl        time.Duration
    retryCount int
    retryDelay time.Duration
    entryID    string
}
```

**Algorithm**:
```go
func (l *FairRedisLock) Acquire(ctx context.Context) (bool, error) {
    // Join waiting queue
    l.client.RPush(ctx, l.queueKey, l.entryID)

    // Wait for our turn
    for i := 0; i <= l.retryCount; i++ {
        // Check if first in queue
        first, _ := l.client.LIndex(ctx, l.queueKey, 0).Result()
        if first != l.entryID {
            continue
        }

        // Try to acquire lock
        result, _ := acquireScript.Run(ctx, l.client, []string{l.key}, l.ownerID, int(l.ttl.Seconds())).Int()
        if result == 1 {
            l.client.LRem(ctx, l.queueKey, 0, l.entryID)
            return true, nil
        }
    }

    // Cleanup on failure
    l.client.LRem(ctx, l.queueKey, 0, l.entryID)
    return false, nil
}
```

**Keys**:
- `lock:fair:{name}` → owner_id (the actual lock)
- `lock:fair:{name}:queue` → List of waiters (FIFO)

### Read-Write Lock

**Structure**:
```go
type ReadWriteRedisLock struct {
    client     *goredis.Client
    readKey    string
    writeKey   string
    ownerID    string
    ttl        time.Duration
    retryCount int
    retryDelay time.Duration
}
```

**Lua Scripts**:
```lua
-- Acquire Read
local writer = redis.call("GET", KEYS[2])
if writer == false or writer == ARGV[1] then
    redis.call("INCR", KEYS[1])
    redis.call("EXPIRE", KEYS[1], ARGV[2])
    return 1
end
return 0

-- Release Read
local count = redis.call("GET", KEYS[1])
if count == false or tonumber(count) <= 0 then
    return 0
end
count = redis.call("DECR", KEYS[1])
if count <= 0 then
    redis.call("DEL", KEYS[1])
end
return 1

-- Acquire Write
local readers = redis.call("GET", KEYS[1])
if readers ~= false and tonumber(readers) > 0 then
    return 0
end
if redis.call("SET", KEYS[2], ARGV[1], "NX", "EX", ARGV[2]) then
    return 1
end
return 0

-- Release Write
if redis.call("GET", KEYS[1]) == ARGV[1] then
    return redis.call("DEL", KEYS[1])
end
return 0
```

**Keys**:
- `lock:rw:{name}:readers` → reader count
- `lock:rw:{name}:writer` → writer owner_id

### Watchdog

**Structure**:
```go
type Watchdog struct {
    lock     ExtensibleLock
    ttl      time.Duration
    interval time.Duration
    stopCh   chan struct{}
    done     chan struct{}
    mu       sync.Mutex
    running  bool
}
```

**Implementation**:
```go
func (w *Watchdog) run(ctx context.Context) {
    defer close(w.done)

    ticker := time.NewTicker(w.interval)
    defer ticker.Stop()

    for {
        select {
        case <-w.stopCh:
            return
        case <-ctx.Done():
            return
        case <-ticker.C:
            w.lock.Extend(ctx, w.ttl)
        }
    }
}
```

**Renewal Strategy**:
- Renewal interval: ttl/3
- Example: TTL=10s, interval=3.3s
- Ensures lock doesn't expire during normal operation

## ZooKeeper Backend

### Lock Structure

```go
type ZkLock struct {
    conn       *zk.Conn
    basePath   string
    lockPath   string
    ownerID    string
    ttl        time.Duration
    retryCount int
    retryDelay time.Duration
    nodePath   string
}
```

### Lock Algorithm

```go
func (l *ZkLock) Acquire(ctx context.Context) (bool, error) {
    // 1. Ensure base path exists
    l.ensurePath(l.basePath)

    // 2. Create ephemeral sequential node
    nodePath, _ := l.conn.CreateProtectedEphemeralSequential(
        l.lockPath+"/lock-",
        []byte(l.ownerID),
        &zk.WorldACL(zk.PermAll),
    )
    l.nodePath = nodePath

    // 3. Try to acquire
    for i := 0; i <= l.retryCount; i++ {
        acquired, _ := l.tryAcquire(ctx)
        if acquired {
            return true, nil
        }
    }

    l.cleanup()
    return false, nil
}

func (l *ZkLock) tryAcquire(ctx context.Context) (bool, error) {
    // List all children
    children, _, _ := l.conn.Children(l.lockPath)
    sort.Strings(children)

    // Find our node
    myNode := path.Base(l.nodePath)
    myIndex := -1
    for i, child := range children {
        if child == myNode {
            myIndex = i
            break
        }
    }

    // If smallest, we have the lock
    if myIndex == 0 {
        return true, nil
    }

    // Watch the node just before ours
    prevNode := children[myIndex-1]
    prevPath := l.lockPath + "/" + prevNode

    exists, _, watchCh, _ := l.conn.ExistsW(prevPath)
    if !exists {
        return false, nil
    }

    // Wait for watch event
    select {
    case event := <-watchCh:
        if event.Type == zk.EventNodeDeleted {
            return false, nil // Retry
        }
    case <-ctx.Done():
        return false, ctx.Err()
    }

    return false, nil
}
```

### Key Design Decisions

1. **Ephemeral Nodes**: Auto-cleanup on session expiry
2. **Sequential Ordering**: Natural FIFO without external queue
3. **Watch on Previous**: Avoid thundering herd problem
4. **Session-Based TTL**: TTL is session timeout

## etcd Backend

### Lock Structure (Concurrency Package)

```go
type EtcdLock struct {
    client     *clientv3.Client
    key        string
    ownerID    string
    ttl        int64
    retryCount int
    retryDelay time.Duration
    session    *concurrency.Session
    mutex      *concurrency.Mutex
    leaseID    clientv3.LeaseID
}
```

### Lock Algorithm (Concurrency Package)

```go
func (l *EtcdLock) tryAcquire(ctx context.Context) (bool, error) {
    // Create session with TTL
    session, _ := concurrency.NewSession(l.client, concurrency.WithTTL(int(l.ttl)))

    // Create mutex
    mutex := concurrency.NewMutex(session, l.key)

    // Try to acquire
    err := mutex.TryLock(ctx)
    if err != nil {
        session.Close()
        if err == concurrency.ErrLocked {
            return false, nil
        }
        return false, err
    }

    l.session = session
    l.mutex = mutex
    l.leaseID = session.Lease()
    return true, nil
}
```

### Lock Structure (Revision-Based)

```go
type EtcdLockByRevision struct {
    client     *clientv3.Client
    key        string
    ownerID    string
    ttl        int64
    retryCount int
    retryDelay time.Duration
    leaseID    clientv3.LeaseID
    rev        int64
}
```

### Lock Algorithm (Revision-Based)

```go
func (l *EtcdLockByRevision) Acquire(ctx context.Context) (bool, error) {
    // Create lease
    leaseResp, _ := l.client.Grant(ctx, l.ttl)

    // Try to create key with lease
    txnResp, _ := l.client.Txn(ctx).
        If(clientv3.Compare(clientv3.CreateRevision(l.key), "=", 0)).
        Then(clientv3.OpPut(l.key, l.ownerID, clientv3.WithLease(leaseResp.ID))).
        Commit()

    if txnResp.Succeeded {
        // We created the key, we have the lock
        l.client.KeepAlive(ctx, leaseResp.ID)
        return true, nil
    }

    // Key exists, watch for deletion
    // ...
}
```

### Key Design Decisions

1. **Lease-Based Expiration**: TTL via lease, auto-renewed with KeepAlive
2. **Revision Ordering**: Global ordering via etcd revision
3. **Transaction Atomicity**: Atomic create-or-watch
4. **Strong Consistency**: Raft consensus guarantees

## Unique ID Generation

### UUID v4

```go
func GenerateID() string {
    hostname, _ := os.Hostname()
    return fmt.Sprintf("%s-%d-%s", hostname, os.Getpid(), uuid.New().String())
}
```

### Why UUID?

- Globally unique across all clients
- No coordination needed between lock holders
- Contains hostname and PID for debugging

## Retry Strategy

### Basic Retry

```go
for i := 0; i <= retryCount; i++ {
    acquired, err := lock.Acquire(ctx)
    if err != nil {
        return false, err
    }
    if acquired {
        return true, nil
    }
    if i < retryCount {
        select {
        case <-ctx.Done():
            return false, ctx.Err()
        case <-time.After(retryDelay):
        }
    }
}
return false, nil
```

### Exponential Backoff (Future)

```go
delay := baseDelay
for i := 0; i < maxRetries; i++ {
    acquired, err := lock.Acquire(ctx)
    if acquired {
        return true, nil
    }
    time.After(delay)
    delay *= 2
}
```

## Error Definitions

```go
var (
    ErrLockNotAcquired = errors.New("lock not acquired")
    ErrLockNotOwned    = errors.New("lock not owned by this caller")
    ErrSessionExpired  = errors.New("zookeeper session expired")
)
```

## Thread Safety

### Lock State

All lock implementations are safe for concurrent use because:
- State is stored in the backend (Redis/ZooKeeper/etcd), not locally
- Each operation is independent
- No shared mutable state in the struct (except for tracking acquired nodes)

### Watchdog State

Uses mutex for thread safety:
```go
type Watchdog struct {
    mu      sync.Mutex
    running bool
    stopCh  chan struct{}
    done    chan struct{}
}
```

## Performance Characteristics

### Redis

- **Latency**: 1-2ms per operation (local Redis)
- **Throughput**: 100K+ ops/sec per node
- **Redlock Overhead**: N * single-node latency
- **Memory**: ~100 bytes per lock in Redis

### ZooKeeper

- **Latency**: 10-100ms (depends on ensemble size)
- **Throughput**: 10K+ ops/sec
- **Watch Efficiency**: No polling required
- **Memory**: ~1KB per ephemeral node

### etcd

- **Latency**: 10-50ms (Raft consensus)
- **Throughput**: 10K+ ops/sec
- **Lease Renewal**: Background KeepAlive
- **Memory**: ~100 bytes per key

## Known Limitations

1. **No Fencing Tokens**: Current implementation doesn't support fencing tokens
2. **No Redis Cluster**: Doesn't support Redis Cluster key hashing
3. **Clock Dependency**: Redlock assumes bounded clock drift
4. **No Lock Escalation**: Cannot upgrade from read to write lock
5. **No Multi-Key Locks**: Cannot atomically acquire multiple locks

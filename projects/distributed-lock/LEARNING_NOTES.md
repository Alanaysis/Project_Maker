# Learning Notes - Distributed Lock

## What I Learned

### 1. Distributed Lock Fundamentals

A distributed lock is a mechanism for coordinating access to shared resources across multiple processes or machines in a distributed system. Unlike local locks (e.g., mutex in a single process), distributed locks must handle network partitions, process crashes, and clock drift.

**Key Takeaway**: Distributed locking is fundamentally harder than local locking because there is no shared memory. Every lock operation requires network communication, which introduces latency and failure modes that don't exist in local locking.

### 2. Redis SET NX EX Command

The basic building block for a Redis-based distributed lock is the `SET key value NX EX` command:

- `NX`: Only set if the key does NOT exist (atomic acquire)
- `EX`: Set expiration in seconds (prevents deadlock if holder crashes)
- `value`: A unique identifier to ensure only the holder can release the lock

```
SET lock:resource "uuid-1234" NX EX 10
```

**Key Takeaway**: The atomicity of `SET NX EX` is critical. Without atomicity, there would be a race condition between checking existence and setting the value.

### 3. Lock Identity and Safe Release

A lock must have a unique identity (usually a UUID). When releasing:

```lua
-- Lua script for atomic release
if redis.call("GET", KEYS[1]) == ARGV[1] then
    return redis.call("DEL", KEYS[1])
else
    return 0
end
```

**Key Takeaway**: Never release a lock without verifying ownership. Without identity checking, a process could release a lock that was acquired by another process after the original lock expired.

### 4. Redlock Algorithm

Redlock is an algorithm for distributed locking across multiple independent Redis nodes:

1. Get current timestamp T1
2. Try to acquire lock on N Redis nodes sequentially
3. Calculate time spent: T2 - T1
4. Lock is acquired if:
   - Acquired on majority (N/2 + 1) of nodes
   - Total time < lock TTL
5. Effective TTL = TTL - (T2 - T1)

**Key Takeaway**: Single-node Redis locks are vulnerable to Redis failures. Redlock provides fault tolerance by requiring consensus across multiple independent Redis instances.

### 5. Clock Drift Problem

Redlock assumes that clock drift between Redis nodes is small relative to the TTL. If clocks diverge significantly, locks may expire prematurely or be held too long.

**Key Takeaway**: In practice, use NTP to keep clocks synchronized, and set TTLs large enough to absorb reasonable clock drift.

### 6. Watchdog (Lock Renewal)

A watchdog goroutine periodically extends the lock TTL while the business logic is still running:

```
Business Logic Start -> Acquire Lock -> Start Watchdog
Watchdog: every TTL/3 seconds, extend lock TTL
Business Logic End -> Stop Watchdog -> Release Lock
```

**Key Takeaway**: Without renewal, long-running operations risk losing the lock mid-execution. The watchdog pattern prevents this by extending the TTL proactively.

### 7. Reentrant Locks

A reentrant lock allows the same client to acquire the lock multiple times without deadlocking. Implementation tracks a count:

```
Lock resource owner=client-A count=1
Lock resource owner=client-A count=2  (reentrant)
Unlock resource owner=client-A count=1
Unlock resource owner=client-A count=0  (actually released)
```

**Key Takeaway**: Reentrant locks are essential for recursive algorithms or callback-heavy code where the same goroutine may need to re-acquire the lock.

### 8. Fair Locks with Waiting Queue

Fair locks ensure FIFO ordering of lock acquisition using a Redis List:

```
RPUSH lock:resource:queue "client-A"    -- Join queue
BLPOP lock:resource:queue 0             -- Wait for turn
SET lock:resource "client-A" NX EX 10   -- Acquire
```

**Key Takeaway**: Without fairness guarantees, lock starvation can occur where some clients repeatedly lose the race to acquire the lock.

## Challenges Faced

### 1. Lock Expiry During Business Logic

The most common problem: the lock expires before the business logic completes, allowing another process to acquire the lock.

**Solution**: Use the watchdog pattern to renew the lock TTL periodically. Set TTL to 3x the expected execution time as a safety margin.

### 2. Split-Brain Scenarios

In Redis Cluster or Sentinel mode, a network partition can cause two clients to believe they hold the same lock.

**Solution**: Use Redlock with independent Redis nodes (not replicas). Accept that there is a small window of vulnerability.

### 3. Testing Distributed Systems

Unit testing distributed locks is inherently difficult because you need to simulate Redis behavior, timing, and failure modes.

**Solution**: Use miniredis (in-memory Redis for Go testing) for unit tests. Use real Redis instances for integration tests.

## Design Decisions

### 1. Interface-Based Design

```go
type Lock interface {
    Acquire(ctx context.Context) (bool, error)
    Release(ctx context.Context) error
    TTL(ctx context.Context) (time.Duration, error)
}
```

This allows different implementations (single-node, Redlock, fair lock) to be used interchangeably.

### 2. Functional Options Pattern

```go
func WithTTL(ttl time.Duration) Option
func WithRetryCount(count int) Option
func WithRetryDelay(delay time.Duration) Option
```

Clean configuration API with sensible defaults.

### 3. Lua Scripts for Atomicity

All lock operations that require multiple Redis commands are implemented as Lua scripts. This ensures atomicity without requiring transactions.

## What I Would Do Differently

1. **Use Fencing Tokens**: Martin Kleppmann's critique of Redlock suggests using fencing tokens to prevent stale lock holders from corrupting data.

2. **Add Observability**: Lock acquisition latency, contention rate, and watchdog renewal success rate should be exposed as metrics.

3. **Support Redis Cluster Mode**: Current implementation assumes standalone Redis or Sentinel. Cluster mode requires key hashing.

4. **Implement Backoff Strategy**: Instead of fixed retry delay, use exponential backoff with jitter to reduce contention.

## Next Steps

1. Add fencing token support
2. Implement Redis Cluster mode
3. Add Prometheus metrics
4. Create benchmarks for lock contention scenarios
5. Add context-aware cancellation support
6. Implement distributed semaphore (multiple permits)

## Resources That Helped

1. [Distributed locks with Redis](https://redis.io/docs/manual/patterns/distributed-locks/) - Official Redis documentation
2. [Redlock Algorithm](https://redis.io/topics/distlock) - Antirez's original Redlock specification
3. Martin Kleppmann: [How to do distributed locking](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html) - Critical analysis of Redlock
4. [go-redis](https://github.com/redis/go-redis) - Go Redis client library
5. [miniredis](https://github.com/alicebob/miniredis) - In-memory Redis for testing

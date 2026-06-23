# Distributed Lock Research

## What is a Distributed Lock?

A distributed lock is a synchronization mechanism used in distributed systems to control access to shared resources. It ensures that only one process (or a limited number of processes) can access a resource at any given time, even when processes are running on different machines.

## Why Distributed Locks?

### Use Cases

1. **Leader Election**: Select a single leader among multiple nodes
2. **Resource Partitioning**: Ensure only one node processes a specific partition
3. **Task Deduplication**: Prevent duplicate processing of the same task
4. **Configuration Updates**: Ensure only one node applies configuration changes
5. **Rate Limiting**: Coordinate rate limits across multiple instances

### Problems Without Distributed Locks

- **Race Conditions**: Two processes modify the same data simultaneously
- **Duplicate Processing**: Same task processed by multiple workers
- **Inconsistent State**: Partial updates from multiple sources
- **Resource Waste**: Redundant operations consuming compute resources

## Distributed Lock Implementations

### 1. Redis-Based Locks

#### Single Node Redis Lock

```
SET resource_name "unique_value" NX EX 30
```

- **Pros**: Simple, fast, well-understood
- **Cons**: Single point of failure, not strongly consistent

#### Redlock Algorithm

```
1. Get current timestamp
2. Try to acquire lock on N independent Redis nodes
3. If acquired on majority and time < TTL, success
4. Otherwise, release all acquired locks
```

- **Pros**: Fault-tolerant, no single point of failure
- **Cons**: Complex, assumes bounded clock drift

### 2. ZooKeeper-Based Locks

Uses ZooKeeper's sequential ephemeral nodes:

```
1. Create sequential ephemeral node /lock/lock-
2. List all children of /lock
3. If created node is smallest, acquire lock
4. Otherwise, watch the node just before ours
```

- **Pros**: Strong consistency, automatic cleanup on session expiry
- **Cons**: Heavier dependency, more complex setup

### 3. etcd-Based Locks

Uses etcd's lease and revision mechanisms:

```
1. Create a key with a lease
2. If revision is smallest among competing keys, acquire lock
3. Renew lease to extend lock
```

- **Pros**: Strong consistency (Raft), TTL-based expiration
- **Cons**: More complex than Redis, higher latency

### 4. Database-Based Locks

Uses database row-level locks or advisory locks:

```sql
-- PostgreSQL advisory lock
SELECT pg_advisory_lock(12345);
-- ... do work ...
SELECT pg_advisory_unlock(12345);
```

- **Pros**: No additional infrastructure, ACID guarantees
- **Cons**: Higher latency, database load

## Redis Lock Commands

### SET with NX and EX

```redis
SET key value NX EX seconds
```

- `NX`: Only set if key does not exist
- `EX`: Expire after N seconds
- Returns `OK` if set, `nil` if not

### SETNX (Legacy)

```redis
SETNX key value
EXPIRE key seconds
```

**Problem**: Not atomic. Between SETNX and EXPIRE, the process could crash, leaving a lock without expiration.

### EVAL (Lua Scripts)

```redis
EVAL "if redis.call('get',KEYS[1]) == ARGV[1] then return redis.call('del',KEYS[1]) else return 0 end" 1 key value
```

Provides atomic multi-step operations.

## Comparison

| Feature | Redis | ZooKeeper | etcd | Database |
|---------|-------|-----------|------|----------|
| Latency | Very Low | Medium | Medium | High |
| Consistency | Eventual | Strong | Strong | Strong |
| Fault Tolerance | Configurable | High | High | Medium |
| Complexity | Low | High | Medium | Low |
| Infrastructure | Redis | ZooKeeper Cluster | etcd Cluster | Database |
| Auto-Expiration | Yes (TTL) | Yes (Ephemeral) | Yes (Lease) | Manual |

## Failure Modes

### 1. Lock Holder Crashes

**Problem**: Lock is never released, causing deadlock.

**Solution**: Use TTL-based expiration (Redis), ephemeral nodes (ZooKeeper), or leases (etcd).

### 2. Network Partition

**Problem**: Lock holder cannot communicate with lock server to release or renew.

**Solution**: TTL ensures eventual release. Redlock provides fault tolerance.

### 3. Clock Drift

**Problem**: Different machines have different clocks, causing TTL calculations to be incorrect.

**Solution**: Use NTP for clock synchronization. Set TTLs large enough to absorb drift.

### 4. GC Pause

**Problem**: Long GC pause causes lock to expire while business logic is still running.

**Solution**: Use fencing tokens. Implement watchdog renewal.

### 5. Split Brain

**Problem**: Network partition causes two nodes to believe they hold the lock.

**Solution**: Use consensus-based systems (ZooKeeper, etcd) or accept the window of vulnerability with Redlock.

## Martin Kleppmann's Critique of Redlock

Martin Kleppmann argued that Redlock is fundamentally flawed because:

1. **Clock Assumption**: Redlock assumes bounded clock drift, which is not guaranteed in practice.
2. **GC Pauses**: A process could acquire a lock, experience a long GC pause, and the lock expires. Another process acquires the lock, and both processes believe they hold it.
3. **No Fencing Tokens**: Without fencing tokens, stale lock holders can corrupt data.

**Proposed Solution**: Use fencing tokens - monotonically increasing tokens that the resource server checks before accepting writes.

```
Client A acquires lock, gets token=33
Client A pauses (GC, network)
Lock expires
Client B acquires lock, gets token=34
Client B writes to resource with token=34
Client A resumes, writes to resource with token=33
Resource server rejects token=33 < 34
```

## Best Practices

1. **Always Set TTL**: Never create a lock without expiration
2. **Use Unique Identifiers**: Each lock holder should have a unique ID
3. **Verify Before Release**: Only release locks you own
4. **Use Watchdog for Long Operations**: Renew locks proactively
5. **Set Appropriate TTL**: Balance between safety (long TTL) and availability (short TTL)
6. **Handle Errors Gracefully**: Lock failures should not crash the application
7. **Use Fencing Tokens**: When possible, use fencing to prevent stale writes

## Tools and Libraries

### Go Libraries

- [go-redis](https://github.com/redis/go-redis): Redis client for Go
- [redsync](https://github.com/go-redsync/redsync): Redis-based distributed locks using Redlock
- [miniredis](https://github.com/alicebob/miniredis): In-memory Redis for testing

### Redis Tools

- `redis-cli`: Command-line Redis client
- `redis-benchmark`: Redis performance testing
- `redis-sentinel`: Redis high availability

## RFCs and Specifications

- [Distributed locks with Redis](https://redis.io/docs/manual/patterns/distributed-locks/)
- [Redlock Algorithm](https://redis.io/topics/distlock)
- [Apache ZooKeeper Recipes - Locks](https://zookeeper.apache.org/doc/current/recipes.html#sc_recipes_Locks)
- [etcd Concurrency Primitives](https://etcd.io/docs/latest/dev-guide/api_concurrency_reference_v3/)

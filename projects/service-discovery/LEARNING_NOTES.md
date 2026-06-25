# Learning Notes - Service Discovery Implementation

## What I Learned

### 1. Service Discovery Fundamentals

Service discovery is the backbone of microservices architecture. It solves a fundamental problem: how do services find each other in a dynamic environment where instances come and go?

**Key Takeaway**: Service discovery is not just about finding services -- it's about maintaining a real-time view of the system's health and topology.

### 2. Registration Patterns

There are two main patterns:

**Self-Registration (Push)**:
- Service registers itself on startup
- Service sends heartbeats
- Service deregisters on shutdown

**Third-Party Registration (Pull)**:
- A separate component monitors services
- More decoupled but more complex

**Key Takeaway**: Self-registration is simpler but couples the service to the registry. Third-party registration is more flexible but requires additional infrastructure.

### 3. TTL and Leases

The lease mechanism is central to service discovery:
- A lease is a time-based contract
- Services must renew their lease before it expires
- If a service fails to renew, it's automatically removed

```go
// Register with a 10-second lease
leaseID, _ := store.GrantLease(ctx, 10*time.Second)
store.Put(ctx, key, value, leaseID)

// Heartbeat every 3 seconds (TTL / 3)
go func() {
    for {
        time.Sleep(3 * time.Second)
        store.KeepAlive(ctx, leaseID)
    }
}()
```

**Key Takeaway**: TTL/3 is the standard heartbeat interval. This gives the service 3 attempts to renew before expiration.

### 4. Health Checking

Two approaches to health checking:

**Passive (Heartbeat/TTL)**:
- Service proves liveness by refreshing its lease
- Simple, low overhead
- Only detects complete failures

**Active (Probing)**:
- Registry periodically checks services
- TCP: Can the service accept connections?
- HTTP: Does the health endpoint return 200?
- More reliable, detects partial failures

**Key Takeaway**: Use both. Heartbeats for basic liveness, active probes for deeper health checks.

### 5. Watch-Based Discovery

Instead of polling, use watches:
```go
ch, _ := store.Watch(ctx, "/services/")
for event := range ch {
    switch event.Type {
    case EventPut:
        // New or updated service
    case EventDelete:
        // Service removed
    }
}
```

**Key Takeaway**: Watches are event-driven and much more efficient than polling. They provide real-time updates with minimal overhead.

### 6. Load Balancing Strategies

**Round Robin**:
- Simple, fair distribution
- Uses atomic counter for lock-free operation
- Good for homogeneous clusters

**Random**:
- Statistically fair with enough requests
- Simpler than round robin
- Good for stateless services

**Weighted Round Robin**:
- Accounts for different instance capacities
- Weight from metadata (e.g., `{"weight": "3"}`)
- Expanded list pattern: weight 3 = 3 entries in the list

**Key Takeaway**: Round robin is the default choice. Use weighted when instances have different capacities.

### 7. Interface-Based Design

The Store interface allows swapping implementations:
```go
type Store interface {
    Put(ctx, key, value, leaseID) error
    Get(ctx, key) ([]byte, error)
    // ...
}
```

- `MemStore` for testing (no external dependencies)
- `EtcdStore` for production (distributed consistency)

**Key Takeaway**: Interface-based design makes testing trivial. Tests use in-memory store, production uses etcd.

### 8. Key Design Patterns

**Prefix-Based Organization**:
```
/services/web/svc-1
/services/web/svc-2
/services/api/svc-3
```

Prefix listing: `List("/services/web/")` returns all web services.

**Goroutine per Service**:
Each registered service gets its own heartbeat goroutine. This is simpler than a centralized heartbeat manager.

**Context Cancellation**:
Use `context.WithCancel` to control goroutine lifecycle:
```go
ctx, cancel := context.WithCancel(context.Background())
go r.heartbeat(ctx, svc, leaseID, ttl)
// Later:
cancel() // Stop the heartbeat
```

### 9. Tag-Based Service Filtering

Services can have metadata tags that enable fine-grained filtering:
```go
// Register with tags
svc := &Service{
    ID:   "api-v2-1",
    Name: "api-service",
    Metadata: map[string]string{
        "version": "2.0",
        "env":     "prod",
        "canary":  "true",
    },
}

// Discover by tags (AND logic)
services := discoverer.GetServicesByTags("api-service", map[string]string{
    "env": "prod",
})
```

**Key Takeaway**: Tag-based filtering enables powerful routing patterns like canary deployments, A/B testing, and environment-specific routing without changing the service discovery infrastructure.

### 10. API Gateway Pattern

An API gateway uses service discovery to route requests:
```
Client -> Gateway -> [Discover + Load Balance] -> Backend Service
```

The gateway:
1. Receives client request
2. Discovers healthy backend services
3. Applies routing rules (tags, version, canary)
4. Selects an instance via load balancer
5. Proxies the request

**Key Takeaway**: The gateway pattern centralizes cross-cutting concerns (auth, rate limiting, routing) and uses service discovery for dynamic backend selection.

## Challenges Faced

### 1. Lease Expiration in Tests

The most complex part was testing lease expiration. In-memory store needs to manually expire leases for testing:
```go
func (m *MemStore) ExpireLeases() {
    for id, lease := range m.leases {
        if time.Now().After(lease.ExpireAt) {
            // Delete associated keys
        }
    }
}
```

**Solution**: Added `ExpireLeases()` method for testing. In production, etcd handles this automatically.

### 2. Watch Event Ordering

Watch events can arrive out of order or be missed during startup. The solution is an initial load before starting the watch:
```go
func (d *Discoverer) Start(ctx) {
    d.loadAll(ctx)  // Load existing services
    go d.watchLoop(ctx, ch)  // Then watch for changes
}
```

### 3. Thread Safety

Multiple goroutines access shared state:
- Registry: heartbeat goroutines per service
- Discovery: watch goroutine updates cache
- Load balancer: concurrent Select calls

**Solution**: Use `sync.RWMutex` for read-heavy workloads, `atomic` for counters, `mutex` for random generators.

### 4. Graceful Shutdown

On shutdown, we need to:
1. Stop all heartbeat goroutines
2. Revoke all leases
3. Close the store connection

**Solution**: Use `context.WithCancel` for goroutine lifecycle, `Stop()` method that cleans up everything.

## Design Decisions

### 1. In-Memory Store for Testing

Instead of requiring etcd for tests, we use an in-memory implementation:
- No external dependencies
- Tests run fast
- Same interface as etcd

### 2. Lease-Based Registration

Using leases instead of simple keys means:
- Automatic cleanup of dead services
- No manual TTL management
- Matches etcd's model

### 3. Status Filtering in Discovery

Only return `StatusUp` services to clients:
- Clients don't need to check health status
- Health checker updates status
- Discovery returns only healthy services

### 4. Weight from Metadata

Load balancer reads weight from service metadata:
- No separate weight configuration
- Service controls its own weight
- Easy to change at runtime

## What I Would Do Differently

1. **Use etcd client library**: This implementation uses a memory store. For production, integrate `go.etcd.io/etcd/client/v3`.

2. **Add gRPC health checking**: HTTP health checks are good, but gRPC has a standard health check protocol.

3. **Implement consistent hashing**: For stateful services, consistent hashing would be better than round robin.

4. **Add circuit breaker**: If a service fails health checks repeatedly, stop routing to it temporarily.

5. **Add metrics**: Registration count, health check latency, load balancer distribution.

## Next Steps

To extend this project:
1. Integrate real etcd client
2. Add gRPC health checking
3. Implement consistent hashing
4. Add service mesh integration
5. Add TLS for secure communication
6. Create a CLI tool for service management
7. Add Prometheus metrics
8. Implement service versioning

## Resources That Helped

1. **etcd Documentation**: Understanding leases, watches, and key organization
2. **Consul Documentation**: Service discovery patterns and health checking
3. **Microservices Patterns** by Chris Richardson: Service discovery chapter
4. **Go Concurrency Patterns**: Goroutines, channels, and sync primitives

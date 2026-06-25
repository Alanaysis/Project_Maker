# Service Discovery Implementation

## Overview

This document describes the implementation details of the service discovery system.

## Store Implementation

### In-Memory Store

The `MemStore` provides a full implementation of the `Store` interface without requiring etcd:

```go
type MemStore struct {
    mu       sync.RWMutex
    data     map[string]*memEntry
    leases   map[int64]*Lease
    watchers []watcher
    nextID   int64
}
```

**Key Features**:
- Thread-safe with `sync.RWMutex`
- Lease-based key expiration
- Watch notification via channels
- Prefix-based listing

**Lease Mechanism**:
```go
func (m *MemStore) Get(ctx, key) ([]byte, error) {
    entry := m.data[key]
    if entry.LeaseID != 0 {
        lease := m.leases[entry.LeaseID]
        if time.Now().After(lease.ExpireAt) {
            return nil, ErrKeyExpired
        }
    }
    return entry.Value, nil
}
```

**Watch Mechanism**:
```go
func (m *MemStore) Watch(ctx, prefix) (<-chan Event, error) {
    ch := make(chan Event, 100)
    m.watchers = append(m.watchers, watcher{prefix, ch})

    // Clean up on context cancellation
    go func() {
        <-ctx.Done()
        // Remove watcher and close channel
    }()

    return ch, nil
}
```

## Registry Implementation

### Service Registration Flow

1. Validate service fields
2. Marshal service to JSON
3. Create a lease with TTL
4. Put service key with lease
5. Start heartbeat goroutine

```go
func (r *Registry) Register(ctx, svc, ttl) error {
    if err := svc.Validate(); err != nil {
        return err
    }

    data, _ := svc.Marshal()
    leaseID, _ := r.store.GrantLease(ctx, ttl)
    r.store.Put(ctx, svc.Key(), data, leaseID)

    // Start heartbeat
    go r.heartbeat(ctx, svc, leaseID, ttl)
}
```

### Heartbeat

The heartbeat goroutine runs at TTL/3 intervals to ensure the lease is renewed before expiration:

```go
func (r *Registry) heartbeat(ctx, svc, leaseID, ttl) {
    interval := ttl / 3
    ticker := time.NewTicker(interval)

    for {
        select {
        case <-ctx.Done():
            return
        case <-ticker.C:
            r.store.KeepAlive(ctx, leaseID)
        }
    }
}
```

### Deregistration

1. Stop the heartbeat goroutine
2. Revoke the lease (this deletes all associated keys)

## Health Check Implementation

### Check Types

**TCP Check**:
```go
func (c *Checker) checkTCP(ctx, svc) (bool, error) {
    conn, err := net.DialTimeout("tcp", svc.Endpoint(), c.config.Timeout)
    if err != nil {
        return false, err
    }
    conn.Close()
    return true, nil
}
```

**HTTP Check**:
```go
func (c *Checker) checkHTTP(ctx, svc) (bool, error) {
    url := fmt.Sprintf("http://%s%s", svc.Endpoint(), c.config.HTTPPath)
    resp, err := http.Get(url)
    if err != nil {
        return false, err
    }
    return resp.StatusCode >= 200 && resp.StatusCode < 300, nil
}
```

### Watch Integration

The health checker watches for service changes:
- On `EventPut`: Immediately check the new service
- On `EventDelete`: Remove from results

## Discovery Implementation

### Initial Load

On start, load all existing services:
```go
func (d *Discoverer) loadAll(ctx) error {
    data, _ := d.store.List(ctx, "/services/")
    for _, v := range data {
        svc, _ := UnmarshalService(v)
        d.addServiceLocked(svc)
    }
}
```

### Watch Loop

Process events to keep the local cache up to date:
```go
func (d *Discoverer) watchLoop(ctx, ch) {
    for {
        select {
        case event := <-ch:
            d.handleEvent(event)
        }
    }
}
```

### Status Filtering

Only return healthy services:
```go
func (d *Discoverer) GetServices(name) []*Service {
    for _, svc := range d.services[name] {
        if svc.Status == StatusUp {
            result = append(result, svc)
        }
    }
    return result
}
```

### Tag-Based Filtering

Filter services by metadata tags (AND logic):
```go
func (d *Discoverer) GetServicesByTags(name string, tags map[string]string) []*Service {
    for _, svc := range d.services[name] {
        if svc.Status != StatusUp {
            continue
        }
        if matchTags(svc, tags) {
            result = append(result, svc)
        }
    }
    return result
}

func matchTags(svc *Service, tags map[string]string) bool {
    for k, v := range tags {
        if svc.Metadata[k] != v {
            return false
        }
    }
    return true
}
```

Use cases:
- Environment routing: `env=prod` vs `env=staging`
- Version routing: `version=2.0` for API versioning
- Canary deployments: `canary=true` for testing new releases

## Load Balancer Implementation

### Round Robin

Uses atomic counter for lock-free operation:
```go
func (b *RoundRobinBalancer) Select(services) (*Service, error) {
    idx := atomic.AddUint64(&b.counter, 1)
    return services[idx % uint64(len(services))], nil
}
```

### Random

Uses mutex-protected random for thread safety:
```go
func (b *RandomBalancer) Select(services) (*Service, error) {
    b.mu.Lock()
    idx := b.random.Intn(len(services))
    b.mu.Unlock()
    return services[idx], nil
}
```

### Weighted Round Robin

Expands the service list by weight:
```go
// Services: A(weight=3), B(weight=1)
// Weighted list: [A, A, A, B]
// Selection cycles through: A, A, A, B, A, A, A, B, ...
```

## HTTP API Implementation

### Handler Pattern

Each handler follows the same pattern:
1. Check HTTP method
2. Parse request (query params or JSON body)
3. Call domain logic
4. Return JSON response or error

```go
func (s *Server) handleDiscover(w, r) {
    if r.Method != http.MethodGet {
        http.Error(w, "method not allowed", 405)
        return
    }

    name := r.URL.Query().Get("name")
    if name == "" {
        http.Error(w, "missing name", 400)
        return
    }

    services := s.discoverer.GetServices(name)
    json.NewEncoder(w).Encode(services)
}
```

## Testing Approach

### Store Tests

- Put/Get/Delete basic operations
- Lease creation and expiration
- KeepAlive renewal
- RevokeLease deletes associated keys
- Watch events for Put/Delete
- Concurrent access safety

### Registry Tests

- Service validation
- Registration puts service in store
- Deregistration removes from store
- Heartbeat keeps service alive
- Stop deregisters all services

### Health Check Tests

- TCP check with real listener
- HTTP check with httptest.Server
- Unhealthy detection (closed port, 500 status)
- Result caching

### Discovery Tests

- Initial load of existing services
- Watch for new services
- Watch for removed services
- Status filtering (only StatusUp)
- Change notification callback

### Load Balancer Tests

- Round robin distribution
- Random distribution
- Weighted distribution
- Empty service list error
- Concurrent access

### Server Tests

- Handler method validation
- Request parsing
- Response format
- Error responses (400, 404, 503)

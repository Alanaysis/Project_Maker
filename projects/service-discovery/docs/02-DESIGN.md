# Service Discovery Design

## Goals

1. Learn service discovery concepts
2. Implement service registration with TTL-based leases
3. Implement health checking (TCP and HTTP)
4. Implement service discovery with watch-based updates
5. Implement multiple load balancing strategies
6. Keep code clean and testable

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Service Discovery System                   │
│                                                              │
│  ┌──────────┐    ┌───────────┐    ┌──────────────────────┐  │
│  │ Registry  │───▶│   Store   │◀───│    Discoverer        │  │
│  │ (Register │    │ (etcd /   │    │  (Watch & Cache)     │  │
│  │ Heartbeat)│    │  Memory)  │    │                      │  │
│  └──────────┘    └───────────┘    └──────────┬───────────┘  │
│                                              │               │
│  ┌──────────┐    ┌───────────┐    ┌──────────▼───────────┐  │
│  │  Health  │    │    HTTP   │    │    Load Balancer      │  │
│  │  Checker │    │    API    │    │  (RoundRobin/Random/  │  │
│  │          │    │           │    │   Weighted)           │  │
│  └──────────┘    └───────────┘    └──────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Core Loop

```
Service Register → Health Check → Service Discovery → Load Balance
     │                  │                │                  │
     ▼                  ▼                ▼                  ▼
  Put key in      Probe services    Watch for changes   Select instance
  store with      and update        and update local    using strategy
  lease (TTL)     status            cache               (RR/Random/WRR)
```

### Package Structure

```
internal/
├── store/           # Key-value store interface and memory implementation
├── registry/        # Service registration and heartbeat
├── healthcheck/     # Active health checking (TCP/HTTP)
├── discovery/       # Service discovery with watch
├── loadbalancer/    # Load balancing strategies
└── server/          # HTTP API server
```

## Store Package

### Interface

```go
type Store interface {
    Put(ctx, key, value, leaseID) error
    Get(ctx, key) ([]byte, error)
    Delete(ctx, key) error
    List(ctx, prefix) (map[string][]byte, error)
    GrantLease(ctx, ttl) (int64, error)
    KeepAlive(ctx, leaseID) error
    RevokeLease(ctx, leaseID) error
    Watch(ctx, prefix) (<-chan Event, error)
    Close() error
}
```

### Design Decisions

1. **Interface-based**: Allows swapping etcd with in-memory for testing
2. **Lease support**: TTL-based key expiration, matching etcd's model
3. **Watch API**: Event channel for change notifications
4. **Prefix-based operations**: List and Watch operate on key prefixes

### Key Format

```
/services/{service-name}/{instance-id}
```

Example:
```
/services/user-service/instance-abc123
/services/user-service/instance-def456
/services/order-service/instance-xyz789
```

## Registry Package

### Responsibilities

- Register services with the store
- Maintain heartbeats to keep leases alive
- Deregister services on shutdown

### Design

```go
type Registry struct {
    store   store.Store
    entries map[string]*registryEntry // service ID -> entry
    stopCh  chan struct{}
}

type registryEntry struct {
    Service *Service
    LeaseID int64
    cancel  context.CancelFunc
}
```

### Design Decisions

1. **Per-service goroutine**: Each service has its own heartbeat goroutine
2. **Lease-based**: Using store leases for automatic expiration
3. **Graceful shutdown**: Stop() deregisters all services and revokes leases
4. **Heartbeat interval**: TTL / 3 to ensure timely renewal

## Health Check Package

### Responsibilities

- Actively probe service health
- Support TCP and HTTP check types
- Track check results and latency

### Design

```go
type Checker struct {
    store   store.Store
    config  Config
    results map[string]*CheckResult
}

type Config struct {
    Interval time.Duration  // How often to check
    Timeout  time.Duration  // Check timeout
    Type     CheckType      // TCP or HTTP
    HTTPPath string         // HTTP health endpoint
}
```

### Design Decisions

1. **Watch-based**: Reacts to store events for new/removed services
2. **Parallel checks**: Uses goroutines for concurrent health checks
3. **Result caching**: Stores last check result per service
4. **Configurable**: TCP or HTTP checks, configurable intervals

## Discovery Package

### Responsibilities

- Watch the store for service changes
- Maintain a local cache of available services
- Notify listeners of changes
- Support tag-based service filtering

### Design

```go
type Discoverer struct {
    store    store.Store
    services map[string]map[string]*registry.Service // name -> id -> service
    onChange ServiceListChangedFunc
}
```

### Design Decisions

1. **Initial load**: Load all services before starting watch
2. **Watch loop**: Process events to update local cache
3. **Change callback**: Optional callback for service list changes
4. **Status filtering**: Only return StatusUp services
5. **Tag filtering**: Filter services by metadata tags (AND logic)

### Tag-Based Filtering

Services can be filtered by metadata tags:
```go
// Get services with matching tags
services := d.GetServicesByTags("web", map[string]string{
    "env": "prod",
    "version": "2.0",
})
```

All specified tags must match (AND logic). This enables:
- Environment routing (prod vs staging)
- Version routing (v1 vs v2)
- Canary deployments (canary=true)

## Load Balancer Package

### Strategies

**Round Robin**:
```go
type RoundRobinBalancer struct {
    counter uint64
}
func (b *RoundRobinBalancer) Select(services) -> atomic counter % len
```

**Random**:
```go
type RandomBalancer struct {
    random *rand.Rand
}
func (b *RandomBalancer) Select(services) -> random.Intn(len)
```

**Weighted Round Robin**:
```go
type WeightedRoundRobinBalancer struct {
    weighted []*registry.Service  // expanded list by weight
    current  int
}
```

### Design Decisions

1. **Interface-based**: Easy to add new strategies
2. **Atomic counter**: Thread-safe round-robin without locks
3. **Weight from metadata**: Read weight from service metadata
4. **Default weight 1**: Services without weight get equal share

## Server Package

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /register | Register a service |
| DELETE | /deregister?id=X | Deregister a service |
| GET | /services | List all services |
| GET | /services/{name} | Get services by name |
| GET | /discover?name=X | Discover services |
| GET | /discover/tags?name=X&tag=value | Discover services by tags |
| GET | /choose?name=X | Choose a service (load balanced) |
| GET | /choose/tags?name=X&tag=value | Choose a service by tags |
| GET | /health | Server health check |

### Request/Response Examples

**Register**:
```json
POST /register
{
  "id": "user-svc-1",
  "name": "user-service",
  "address": "10.0.0.1",
  "port": 8080,
  "metadata": {"version": "1.0"}
}
```

**Discover**:
```json
GET /discover?name=user-service
[
  {"id": "user-svc-1", "address": "10.0.0.1", "port": 8080},
  {"id": "user-svc-2", "address": "10.0.0.2", "port": 8080}
]
```

## Error Handling

| Error | Response | Cause |
|-------|----------|-------|
| Invalid request | 400 Bad Request | Missing fields, bad JSON |
| Service not found | 404 Not Found | Unknown service name |
| No services | 503 Service Unavailable | All instances down |
| Method not allowed | 405 | Wrong HTTP method |

## Concurrency Model

- **Store**: Thread-safe with internal locking
- **Registry**: Per-service heartbeat goroutines
- **Health Checker**: Parallel checks with sync.WaitGroup
- **Discoverer**: Watch goroutine updates cache
- **Load Balancer**: Atomic counter for round-robin, mutex for random

## Testing Strategy

- **Store**: In-memory implementation for all tests
- **Registry**: Test register/deregister/heartbeat with mem store
- **Health Check**: Use net.Listener and httptest.Server
- **Discovery**: Test watch, load, and change notifications
- **Load Balancer**: Test distribution patterns
- **Server**: Use httptest.NewRecorder for handler tests

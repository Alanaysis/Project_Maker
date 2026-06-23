# Service Discovery Testing

## Test Strategy

### Unit Tests

Each package has focused unit tests:

1. **Store Tests**: Key-value operations, leases, watches
2. **Registry Tests**: Service registration, heartbeat, deregistration
3. **Health Check Tests**: TCP/HTTP checks, result tracking
4. **Discovery Tests**: Service loading, watch updates, filtering
5. **Load Balancer Tests**: Distribution strategies
6. **Server Tests**: HTTP handlers

### Integration Tests

End-to-end tests that verify the full pipeline:
- Register -> Discover -> Choose -> Deregister

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
go test ./internal/store -v
go test ./internal/registry -v
go test ./internal/healthcheck -v
go test ./internal/discovery -v
go test ./internal/loadbalancer -v
go test ./internal/server -v
```

### With Coverage

```bash
go test ./... -cover
```

### Race Detection

```bash
go test ./... -race
```

## Test Cases

### Store Tests

#### Basic Operations

```go
func TestMemStorePutGet(t *testing.T) {
    s := NewMemStore()
    ctx := context.Background()

    s.Put(ctx, "/test/key1", []byte("value1"), 0)
    val, _ := s.Get(ctx, "/test/key1")

    assertEqual(t, string(val), "value1")
}
```

#### Lease Expiration

```go
func TestMemStoreLeaseExpiration(t *testing.T) {
    s := NewMemStore()
    ctx := context.Background()

    leaseID, _ := s.GrantLease(ctx, 50*time.Millisecond)
    s.Put(ctx, "/test/key1", []byte("value1"), leaseID)

    time.Sleep(100 * time.Millisecond)

    _, err := s.Get(ctx, "/test/key1")
    assertEqual(t, err, ErrKeyExpired)
}
```

#### Watch Events

```go
func TestMemStoreWatch(t *testing.T) {
    s := NewMemStore()
    ctx, cancel := context.WithCancel(context.Background())
    ch, _ := s.Watch(ctx, "/test/")

    s.Put(ctx, "/test/key1", []byte("value1"), 0)

    event := <-ch
    assertEqual(t, event.Type, EventPut)
    assertEqual(t, event.Key, "/test/key1")
}
```

### Registry Tests

#### Register Service

```go
func TestRegistryRegister(t *testing.T) {
    s := store.NewMemStore()
    r := New(s)
    ctx := context.Background()

    svc := &Service{ID: "svc-1", Name: "web", Address: "127.0.0.1", Port: 8080}
    r.Register(ctx, svc, 10*time.Second)

    // Verify in store
    data, _ := s.Get(ctx, svc.Key())
    stored, _ := UnmarshalService(data)
    assertEqual(t, stored.ID, "svc-1")
}
```

#### Heartbeat Keeps Service Alive

```go
func TestRegistryHeartbeat(t *testing.T) {
    s := store.NewMemStore()
    r := New(s)
    ctx := context.Background()

    svc := &Service{ID: "svc-1", Name: "web", Address: "127.0.0.1", Port: 8080}
    r.Register(ctx, svc, 100*time.Millisecond)

    time.Sleep(150 * time.Millisecond) // Heartbeat should keep it alive

    _, err := s.Get(ctx, svc.Key())
    assertEqual(t, err, nil) // Should still exist
}
```

### Health Check Tests

#### TCP Healthy

```go
func TestCheckerTCPHealthy(t *testing.T) {
    listener, _ := net.Listen("tcp", "127.0.0.1:0")
    defer listener.Close()

    svc := &Service{Address: "127.0.0.1", Port: listener.Addr().Port}
    checker := New(s, Config{Timeout: 500*time.Millisecond})

    result := checker.check(ctx, svc)
    assertTrue(t, result.Healthy)
}
```

#### HTTP Unhealthy

```go
func TestCheckerHTTPUnhealthy(t *testing.T) {
    ts := httptest.NewServer(http.HandlerFunc(func(w, r) {
        w.WriteHeader(500)
    }))
    defer ts.Close()

    svc := &Service{Address: addr.IP, Port: addr.Port}
    checker := New(s, Config{Type: CheckHTTP})

    result := checker.check(ctx, svc)
    assertFalse(t, result.Healthy)
}
```

### Discovery Tests

#### Watch New Service

```go
func TestDiscovererWatchNewService(t *testing.T) {
    s := store.NewMemStore()
    d := New(s)
    d.Start(ctx)

    // Add service after start
    putService(t, s, ctx, svc)
    time.Sleep(100 * time.Millisecond)

    services := d.GetServices("web")
    assertEqual(t, len(services), 1)
}
```

#### Status Filtering

```go
func TestDiscovererGetServicesFiltersDown(t *testing.T) {
    // Register one up, one down
    putService(t, s, ctx, &Service{Status: StatusUp})
    putService(t, s, ctx, &Service{Status: StatusDown})

    services := d.GetServices("web")
    assertEqual(t, len(services), 1) // Only up service
}
```

### Load Balancer Tests

#### Round Robin Distribution

```go
func TestRoundRobinBalancer(t *testing.T) {
    b := NewRoundRobinBalancer()
    services := []*Service{svc1, svc2, svc3}

    selected := make(map[string]int)
    for i := 0; i < 9; i++ {
        svc, _ := b.Select(services)
        selected[svc.ID]++
    }

    // Each selected 3 times
    assertEqual(t, selected["svc-1"], 3)
    assertEqual(t, selected["svc-2"], 3)
    assertEqual(t, selected["svc-3"], 3)
}
```

#### Weighted Distribution

```go
func TestWeightedRoundRobinBalancer(t *testing.T) {
    b := NewWeightedRoundRobinBalancer()
    services := []*Service{
        {Weight: 3}, // svc-1
        {Weight: 1}, // svc-2
    }

    for i := 0; i < 8; i++ {
        svc, _ := b.Select(services)
        selected[svc.ID]++
    }

    assertEqual(t, selected["svc-1"], 6) // 3/4 of 8
    assertEqual(t, selected["svc-2"], 2) // 1/4 of 8
}
```

### Server Tests

#### Register Endpoint

```go
func TestHandleRegister(t *testing.T) {
    srv, _ := setupTestServer(t)

    body := `{"id":"svc-1","name":"web","address":"10.0.0.1","port":8080}`
    req := httptest.NewRequest("POST", "/register", bytes.NewBufferString(body))
    w := httptest.NewRecorder()

    srv.handleRegister(w, req)

    assertEqual(t, w.Code, 201)
}
```

#### Choose Endpoint

```go
func TestHandleChoose(t *testing.T) {
    // Register multiple services
    // Call /choose multiple times
    // Verify both services are selected
}
```

## Manual Testing

### Start Server

```bash
go run ./cmd/server
```

### Register a Service

```bash
curl -X POST http://localhost:8500/register \
  -H "Content-Type: application/json" \
  -d '{
    "id": "user-svc-1",
    "name": "user-service",
    "address": "10.0.0.1",
    "port": 8080,
    "metadata": {"version": "1.0"}
  }'
```

### Discover Services

```bash
curl http://localhost:8500/discover?name=user-service
```

### Choose a Service (Load Balanced)

```bash
curl http://localhost:8500/choose?name=user-service
```

### List All Services

```bash
curl http://localhost:8500/services
```

### Deregister a Service

```bash
curl -X DELETE http://localhost:8500/deregister?id=user-svc-1
```

## Test Coverage

Run with coverage report:

```bash
go test ./... -coverprofile=coverage.out
go tool cover -html=coverage.out
```

## Continuous Integration

Example GitHub Actions workflow:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-go@v2
        with:
          go-version: 1.21
      - run: go test ./... -race -cover
```

# Service Discovery Development Guide

## Development Setup

### Prerequisites

- Go 1.21 or later
- Git

### Clone and Build

```bash
# Clone
git clone <repository-url>
cd service-discovery

# Build
go build -o service-discovery ./cmd/server

# Run
./service-discovery
```

### IDE Setup

Recommended VS Code extensions:
- Go (golang.go)
- Go Test Explorer

## Project Structure

```
service-discovery/
├── cmd/
│   └── server/
│       └── main.go              # Entry point
├── internal/
│   ├── store/
│   │   ├── store.go             # Store interface + memory impl
│   │   └── store_test.go
│   ├── registry/
│   │   ├── types.go             # Service types
│   │   ├── registry.go          # Registration + heartbeat
│   │   └── registry_test.go
│   ├── healthcheck/
│   │   ├── healthcheck.go       # Health checking
│   │   └── healthcheck_test.go
│   ├── discovery/
│   │   ├── discovery.go         # Service discovery
│   │   └── discovery_test.go
│   ├── loadbalancer/
│   │   ├── balancer.go          # Load balancing strategies
│   │   └── balancer_test.go
│   └── server/
│       ├── server.go            # HTTP API
│       └── server_test.go
├── docs/
├── examples/
├── go.mod
├── README.md
└── LEARNING_NOTES.md
```

## Development Workflow

### 1. Make Changes

Edit the relevant files:
- `internal/store/`: Key-value store operations
- `internal/registry/`: Service registration
- `internal/healthcheck/`: Health checking
- `internal/discovery/`: Service discovery
- `internal/loadbalancer/`: Load balancing
- `internal/server/`: HTTP API

### 2. Run Tests

```bash
# All tests
go test ./...

# Specific package
go test ./internal/store -v

# With race detection
go test ./... -race

# With coverage
go test ./... -cover
```

### 3. Build and Test

```bash
# Build
go build -o service-discovery ./cmd/server

# Run
./service-discovery

# Test with curl
curl http://localhost:8500/health
```

### 4. Commit Changes

```bash
git add .
git commit -m "Description of changes"
```

## Code Style

### Go Conventions

- Use `gofmt` for formatting
- Use `go vet` for static analysis
- Follow [Effective Go](https://go.dev/doc/effective_go)

### Naming

- Package names: lowercase, single word
- Exported names: CamelCase
- Unexported names: camelCase
- Constants: CamelCase or UPPER_SNAKE_CASE

### Error Handling

```go
// Return errors, don't panic
result, err := doSomething()
if err != nil {
    return fmt.Errorf("do something: %w", err)
}

// Log errors at the boundary
log.Printf("[component] operation failed: %v", err)
```

### Testing

```go
func TestSomething(t *testing.T) {
    // Arrange
    input := "test"

    // Act
    result, err := DoSomething(input)

    // Assert
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }
    if result != expected {
        t.Errorf("expected %v, got %v", expected, result)
    }
}
```

## Adding Features

### Adding a New Load Balancing Strategy

1. Add strategy constant in `internal/loadbalancer/balancer.go`:

```go
const (
    RoundRobin Strategy = iota
    Random
    WeightedRoundRobin
    LeastConnections  // New
)
```

2. Implement the Balancer interface:

```go
type LeastConnectionsBalancer struct {
    connections map[string]int64
}

func (b *LeastConnectionsBalancer) Select(services) (*Service, error) {
    // Find service with fewest connections
}
```

3. Register in the factory:

```go
case LeastConnections:
    return NewLeastConnectionsBalancer()
```

4. Add tests

### Adding a New Health Check Type

1. Add check type in `internal/healthcheck/healthcheck.go`:

```go
const (
    CheckTCP CheckType = iota
    CheckHTTP
    CheckGRPC  // New
)
```

2. Implement the check:

```go
func (c *Checker) checkGRPC(ctx, svc) (bool, error) {
    // gRPC health check
}
```

3. Add to the check switch:

```go
case CheckGRPC:
    healthy, err = c.checkGRPC(ctx, svc)
```

4. Add tests

### Integrating Real etcd

1. Create `internal/store/etcd.go`:

```go
type EtcdStore struct {
    client *clientv3.Client
}

func NewEtcdStore(endpoints []string) (*EtcdStore, error) {
    client, err := clientv3.New(clientv3.Config{
        Endpoints: endpoints,
    })
    // ...
}
```

2. Implement the Store interface using etcd client

3. Update `cmd/server/main.go` to use etcd:

```go
var s store.Store
if *useEtcd {
    s, _ = store.NewEtcdStore(*etcdEndpoints)
} else {
    s = store.NewMemStore()
}
```

## Debugging

### Enable Verbose Logging

```bash
# Set log level
export SD_LOG_LEVEL=debug

# Run
./service-discovery
```

### Delve Debugger

```bash
# Install dlv
go install github.com/go-delve/delve/cmd/dlv@latest

# Debug
dlv debug ./cmd/server

# Set breakpoint
(dlv) break main.main
(dlv) continue
```

## Performance Profiling

### CPU Profiling

```go
import "runtime/pprof"

// Start CPU profile
f, _ := os.Create("cpu.prof")
pprof.StartCPUProfile(f)
defer pprof.StopCPUProfile()
```

### Analyze Profiles

```bash
go tool pprof cpu.prof
go tool pprof mem.prof
```

## Common Issues

### Port Already in Use

```bash
# Find process using port
lsof -i :8500

# Kill process
kill -9 <PID>
```

### Race Conditions

```bash
# Run with race detector
go test ./... -race
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Add tests
5. Run tests: `go test ./...`
6. Submit pull request

## Resources

- [Go Documentation](https://go.dev/doc/)
- [Effective Go](https://go.dev/doc/effective_go)
- [etcd Documentation](https://etcd.io/docs/)
- [Consul Documentation](https://www.consul.io/docs)

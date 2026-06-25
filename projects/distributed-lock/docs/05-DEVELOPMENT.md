# Distributed Lock Development Guide

## Development Setup

### Prerequisites

- Go 1.21 or later
- Redis 6.0+ (for integration tests)
- ZooKeeper 3.6+ (for ZooKeeper backend)
- etcd 3.5+ (for etcd backend)
- Git

### Clone and Build

```bash
# Clone
git clone <repository-url>
cd distributed-lock

# Download dependencies
go mod tidy

# Build
go build -o demo ./cmd/demo

# Run demo
./demo
```

### IDE Setup

Recommended VS Code extensions:
- Go (golang.go)
- Go Test Explorer
- Redis (for monitoring)
- ZooKeeper (for monitoring)

## Project Structure

```
distributed-lock/
├── cmd/
│   └── demo/
│       └── main.go              # Demo application
├── internal/
│   ├── lock/
│   │   └── lock.go              # Core interfaces
│   ├── redis/
│   │   ├── lock.go              # Basic Redis lock
│   │   ├── redlock.go           # Redlock algorithm
│   │   ├── reentrant.go         # Reentrant lock
│   │   ├── fair.go              # Fair (FIFO) lock
│   │   ├── rwlock.go            # Read-write lock
│   │   └── watchdog.go          # Auto-renewal
│   ├── zookeeper/
│   │   └── lock.go              # ZooKeeper lock
│   └── etcd/
│       └── lock.go              # etcd lock
├── pkg/
│   └── utils/
│       └── id.go                # ID generation
├── tests/
│   ├── lock_test.go             # Lock tests
│   ├── redlock_test.go          # Redlock tests
│   └── watchdog_test.go         # Watchdog tests
├── examples/
│   ├── task_scheduler.go        # Task scheduling
│   ├── inventory.go             # Inventory management
│   ├── ratelimiter.go           # Rate limiter
│   └── main.go                  # Usage examples
├── docs/                        # Documentation
├── go.mod
├── go.sum
└── README.md
```

## Development Workflow

### 1. Make Changes

Edit the relevant files:
- `internal/lock/`: Core interfaces
- `internal/redis/`: Redis implementations
- `internal/zookeeper/`: ZooKeeper implementation
- `internal/etcd/`: etcd implementation
- `pkg/utils/`: Shared utilities
- `examples/`: Practical applications

### 2. Run Tests

```bash
# All tests
go test ./...

# Specific package
go test ./tests/... -v
go test ./internal/redis/... -v

# With race detection
go test ./... -race

# With coverage
go test ./... -cover
```

### 3. Build and Test

```bash
# Build
go build -o demo ./cmd/demo

# Run demo (requires Redis)
./demo

# Run examples
go run examples/main.go
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
- Use `golangci-lint` for linting
- Follow [Effective Go](https://go.dev/doc/effective_go)

### Naming

- Package names: lowercase, single word
- Exported names: CamelCase
- Unexported names: camelCase
- Constants: CamelCase or UPPER_SNAKE_CASE
- Interfaces: -er suffix (e.g., `Locker`)

### Error Handling

```go
// Return errors, don't panic
acquired, err := lock.Acquire(ctx)
if err != nil {
    return fmt.Errorf("acquire lock: %w", err)
}

// Define sentinel errors
var ErrLockNotOwned = errors.New("lock not owned by this caller")

// Wrap errors for context
return fmt.Errorf("release lock %s: %w", lock.Key(), err)
```

### Testing

```go
func TestSomething(t *testing.T) {
    // Arrange
    s := miniredis.RunT(t)
    client := goredis.NewClient(&goredis.Options{Addr: s.Addr()})

    // Act
    distLock := redis.NewRedisLock(client, "test-key",
        lock.WithTTL(10*time.Second))
    acquired, err := distLock.Acquire(context.Background())

    // Assert
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }
    if !acquired {
        t.Error("expected to acquire lock")
    }
}
```

## Adding Features

### Adding a New Lock Type

1. Implement the `Lock` interface in `internal/redis/`:

```go
type MyLock struct {
    client     *goredis.Client
    key        string
    ownerID    string
    ttl        time.Duration
}

func (l *MyLock) Acquire(ctx context.Context) (bool, error) {
    // implementation
}

func (l *MyLock) Release(ctx context.Context) error {
    // implementation
}

func (l *MyLock) TTL(ctx context.Context) (time.Duration, error) {
    // implementation
}
```

2. Add tests:

```go
func TestMyLock_Acquire(t *testing.T) {
    s := miniredis.RunT(t)
    client := goredis.NewClient(&goredis.Options{Addr: s.Addr()})

    distLock := NewMyLock(client, "test-key",
        lock.WithTTL(10*time.Second))
    acquired, _ := distLock.Acquire(context.Background())

    if !acquired {
        t.Error("expected to acquire lock")
    }
}
```

3. Update documentation

### Adding a New Backend

1. Create package in `internal/`:

```
internal/
└── mybackend/
    └── lock.go
```

2. Implement the `Lock` interface:

```go
package mybackend

import "github.com/example/distributed-lock/internal/lock"

type MyBackendLock struct {
    // fields
}

func (l *MyBackendLock) Acquire(ctx context.Context) (bool, error) {
    // implementation
}

func (l *MyBackendLock) Release(ctx context.Context) error {
    // implementation
}

func (l *MyBackendLock) TTL(ctx context.Context) (time.Duration, error) {
    // implementation
}
```

3. Add tests
4. Update documentation

### Adding a New Lua Script

1. Define the script:

```go
var myScript = goredis.NewScript(`
    -- Lua script logic here
    return redis.call('GET', KEYS[1])
`)
```

2. Use the script:

```go
result, err := myScript.Run(ctx, client, []string{key}, args...).Result()
```

3. Add tests for the script

### Adding Exponential Backoff

1. Add retry option:

```go
func WithRetryStrategy(strategy RetryStrategy) Option {
    return func(c *Config) {
        c.RetryStrategy = strategy
    }
}
```

2. Implement the strategy:

```go
type ExponentialBackoff struct {
    BaseDelay  time.Duration
    MaxDelay   time.Duration
    MaxRetries int
}

func (b *ExponentialBackoff) NextDelay(attempt int) time.Duration {
    delay := b.BaseDelay * time.Duration(1<<uint(attempt))
    if delay > b.MaxDelay {
        delay = b.MaxDelay
    }
    return delay
}
```

3. Add tests

## Debugging

### Enable Verbose Logging

```go
import "log"

func (l *RedisLock) Acquire(ctx context.Context) (bool, error) {
    log.Printf("[lock] acquiring %s", l.key)
    // ...
    log.Printf("[lock] acquired %s, success=%v", l.key, ok)
    return ok, nil
}
```

### Redis Monitoring

```bash
# Monitor all commands
redis-cli MONITOR

# Check specific key
redis-cli GET lock:my-resource
redis-cli TTL lock:my-resource
redis-cli TYPE lock:my-resource

# List all keys
redis-cli KEYS "*lock*"
```

### ZooKeeper Monitoring

```bash
# List lock nodes
zkCli.sh ls /locks

# Check node data
zkCli.sh get /locks/my-resource/lock-0000000001

# Watch for changes
zkCli.sh watch /locks/my-resource
```

### etcd Monitoring

```bash
# List lock keys
etcdctl get /lock/ --prefix

# Check lease
etcdctl lease list

# Watch for changes
etcdctl watch /lock/
```

### Delve Debugger

```bash
# Install dlv
go install github.com/go-delve/delve/cmd/dlv@latest

# Debug demo
dlv debug ./cmd/demo

# Debug tests
dlv test ./tests

# Set breakpoint
(dlv) break lock.go:42
(dlv) continue
```

## Performance Profiling

### CPU Profiling

```go
import "runtime/pprof"

func main() {
    f, _ := os.Create("cpu.prof")
    pprof.StartCPUProfile(f)
    defer pprof.StopCPUProfile()

    // Run workload
}
```

### Analyze Profiles

```bash
go tool pprof cpu.prof
(pprof) top
(pprof) web
```

## Common Issues

### Redis Connection Refused

```bash
# Check if Redis is running
redis-cli ping

# Start Redis
redis-server

# Check Redis logs
tail -f /var/log/redis/redis-server.log
```

### Lock Not Released

```bash
# Check lock state
redis-cli GET lock:my-resource
redis-cli TTL lock:my-resource

# Manually release (emergency)
redis-cli DEL lock:my-resource
```

### Race Conditions

```bash
# Run with race detector
go test ./... -race

# Common causes:
# - Shared state without synchronization
# - Goroutine access to test assertions
# - Redis connection pool issues
```

### miniredis Issues

```go
// Ensure miniredis is properly cleaned up
func TestSomething(t *testing.T) {
    s := miniredis.RunT(t)  // Auto-cleanup with t.Cleanup
    // ...
}
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes
4. Add tests
5. Run tests: `go test ./... -race`
6. Submit pull request

### Pull Request Checklist

- [ ] Code follows Go conventions
- [ ] Tests added for new functionality
- [ ] All tests pass: `go test ./...`
- [ ] No race conditions: `go test ./... -race`
- [ ] Documentation updated
- [ ] Commit messages are clear

## Resources

- [Go Documentation](https://go.dev/doc/)
- [Effective Go](https://go.dev/doc/effective_go)
- [go-redis Documentation](https://redis.uptrace.dev/)
- [go-zookeeper Documentation](https://github.com/go-zookeeper/zk)
- [etcd Client Documentation](https://etcd.io/docs/latest/dev-guide/)
- [Distributed locks with Redis](https://redis.io/docs/manual/patterns/distributed-locks/)
- [Redlock Algorithm](https://redis.io/topics/distlock)
- [Apache ZooKeeper Recipes](https://zookeeper.apache.org/doc/current/recipes.html)
- [etcd Concurrency Primitives](https://etcd.io/docs/latest/dev-guide/api_concurrency_reference_v3/)

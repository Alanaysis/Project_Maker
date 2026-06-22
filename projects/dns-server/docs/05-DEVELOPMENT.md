# DNS Server Development Guide

## Development Setup

### Prerequisites

- Go 1.21 or later
- Git

### Clone and Build

```bash
# Clone
git clone <repository-url>
cd dns-server

# Build
go build -o dns-server ./cmd/server

# Run
./dns-server
```

### IDE Setup

Recommended VS Code extensions:
- Go (golang.go)
- Go Test Explorer

## Project Structure

```
dns-server/
├── cmd/
│   └── server/
│       └── main.go          # Entry point
├── internal/
│   ├── protocol/
│   │   ├── message.go       # DNS message parsing
│   │   └── message_test.go
│   ├── cache/
│   │   ├── cache.go         # DNS cache
│   │   └── cache_test.go
│   ├── resolver/
│   │   ├── resolver.go      # Name resolution
│   │   └── resolver_test.go
│   └── server/
│       ├── server.go        # UDP server
│       └── server_test.go
├── docs/
├── go.mod
├── README.md
└── LEARNING_NOTES.md
```

## Development Workflow

### 1. Make Changes

Edit the relevant files:
- `internal/protocol/`: DNS message handling
- `internal/cache/`: Caching logic
- `internal/resolver/`: Resolution logic
- `internal/server/`: Server logic

### 2. Run Tests

```bash
# All tests
go test ./...

# Specific package
go test ./internal/protocol -v

# With race detection
go test ./... -race
```

### 3. Build and Test

```bash
# Build
go build -o dns-server ./cmd/server

# Run
./dns-server

# Test with dig
dig @127.0.0.1 -p 5353 example.com A
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

### Adding a New Record Type

1. Add constant in `internal/protocol/message.go`:

```go
const TypeSRV uint16 = 33
```

2. Add to `TypeName` function:

```go
case TypeSRV:
    return "SRV"
```

3. Add parsing logic in `unpackResourceRecord`

4. Add tests

### Adding a New Cache Strategy

1. Add option in `internal/cache/cache.go`:

```go
func WithEvictionStrategy(strategy EvictionStrategy) Option {
    return func(c *Cache) {
        c.strategy = strategy
    }
}
```

2. Implement the strategy

3. Add tests

### Adding TCP Support

1. Add TCP listener in `internal/server/server.go`:

```go
func (s *Server) startTCP() error {
    addr, _ := net.ResolveTCPAddr("tcp", s.addr)
    listener, _ := net.ListenTCP("tcp", addr)

    for {
        conn, _ := listener.Accept()
        go s.handleTCPConnection(conn)
    }
}
```

2. Handle TCP-specific logic (message length prefix)

3. Add tests

## Debugging

### Enable Verbose Logging

```bash
# Set log level
export DNS_LOG_LEVEL=debug

# Run
./dns-server
```

### Packet Capture

```bash
# Capture DNS traffic
sudo tcpdump -i lo -n port 5353 -v

# Save to file
sudo tcpdump -i lo -n port 5353 -w capture.pcap
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

// Run workload
```

### Memory Profiling

```go
import "runtime/pprof"

// Write memory profile
f, _ := os.Create("mem.prof")
pprof.WriteHeapProfile(f)
f.Close()
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
lsof -i :5353

# Kill process
kill -9 <PID>
```

### Permission Denied (Port 53)

```bash
# Use sudo
sudo ./dns-server -addr ":53"

# Or use non-privileged port
./dns-server -addr ":5353"
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
- [Go Test Examples](https://go.dev/doc/examples)
- [RFC 1035](https://tools.ietf.org/html/rfc1035)

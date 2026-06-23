# Exactly-Once Semantics Development Guide

## Development Setup

### Prerequisites

- Go 1.21 or later
- Git

### Clone and Build

```bash
# Clone
git clone <repository-url>
cd exactly-once

# Build demo
go build -o demo ./cmd/demo

# Run demo
./demo
```

### IDE Setup

Recommended VS Code extensions:
- Go (golang.go)
- Go Test Explorer

## Project Structure

```
exactly-once/
├── cmd/
│   └── demo/
│       └── main.go              # Demo program
├── internal/
│   ├── message/
│   │   ├── message.go           # Core message types
│   │   └── message_test.go
│   ├── dedup/
│   │   ├── dedup.go             # Deduplication
│   │   └── dedup_test.go
│   ├── processor/
│   │   ├── processor.go         # Idempotent processing
│   │   └── processor_test.go
│   ├── transaction/
│   │   ├── transaction.go       # Two-phase commit
│   │   └── transaction_test.go
│   └── tracker/
│       ├── tracker.go           # State tracking
│       └── tracker_test.go
├── docs/                        # Documentation
├── go.mod                       # Go module file
├── README.md                    # This file
└── LEARNING_NOTES.md            # Learning notes
```

## Development Workflow

### 1. Make Changes

Edit the relevant files:
- `internal/message/`: Core message types
- `internal/dedup/`: Deduplication logic
- `internal/processor/`: Processing pipeline
- `internal/transaction/`: Transaction management
- `internal/tracker/`: State tracking

### 2. Run Tests

```bash
# All tests
go test ./...

# Specific package
go test ./internal/dedup -v

# With race detection
go test ./... -race
```

### 3. Build and Test

```bash
# Build
go build -o demo ./cmd/demo

# Run
./demo
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

### Adding a New Message State

1. Add constant in `internal/message/message.go`:

```go
const StateRetrying State = iota
```

2. Update `String()` method

3. Update `IsTerminal()` if needed

4. Update tracker stats in `internal/tracker/tracker.go`

5. Add tests

### Adding a New Dedup Strategy

1. Add strategy interface in `internal/dedup/dedup.go`:

```go
type Strategy interface {
    Check(key string) Result
    MarkCompleted(key string, result []byte)
}
```

2. Implement the strategy (e.g., BloomFilter, Redis-backed)

3. Add option to select strategy

4. Add tests

### Adding Persistent Storage

1. Add storage interface:

```go
type Storage interface {
    Get(key string) (*Entry, error)
    Set(key string, entry *Entry) error
    Delete(key string) error
}
```

2. Implement with Redis/PostgreSQL/etc.

3. Add configuration option

4. Add tests with mock storage

## Debugging

### Enable Verbose Logging

```bash
# Set log level
export EXACTLY_ONCE_LOG_LEVEL=debug

# Run
./demo
```

### Race Detection

```bash
go test ./... -race
```

### Delve Debugger

```bash
# Install dlv
go install github.com/go-delve/delve/cmd/dlv@latest

# Debug
dlv debug ./cmd/demo

# Set breakpoint
(dlv) break main.main
(dlv) continue
```

## Performance Profiling

### CPU Profiling

```go
import "runtime/pprof"

f, _ := os.Create("cpu.prof")
pprof.StartCPUProfile(f)
defer pprof.StopCPUProfile()
```

### Memory Profiling

```go
import "runtime/pprof"

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

### Race Conditions

```bash
# Run with race detector
go test ./... -race
```

### Memory Leaks

If dedup/tracker entries accumulate:
- Check TTL configuration
- Call Cleanup() periodically
- Set appropriate maxEntries

### Duplicate Processing

If messages are processed more than once:
- Verify IdempotencyKey is consistent
- Check dedup TTL is long enough
- Ensure MarkCompleted is called after processing

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
- [Kafka Exactly-Once Semantics](https://kafka.apache.org/documentation/#semantics)
- [Two Generals Problem](https://en.wikipedia.org/wiki/Two_Generals%27_Problem)

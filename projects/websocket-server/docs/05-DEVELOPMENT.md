# WebSocket Server Development Guide

## Development Setup

### Prerequisites

- Go 1.22 or later
- Git

### Clone and Build

```bash
# Clone
git clone <repository-url>
cd websocket-server

# Build
go build -o websocket-server ./cmd/server

# Run
./websocket-server
```

### IDE Setup

Recommended VS Code extensions:
- Go (golang.go)
- Go Test Explorer

## Project Structure

```
websocket-server/
├── cmd/
│   └── server/
│       └── main.go          # Entry point
├── internal/
│   ├── server/
│   │   └── server.go        # HTTP/WebSocket server
│   ├── websocket/
│   │   ├── conn.go          # WebSocket connection
│   │   ├── frame.go         # Frame encoding/decoding
│   │   └── handshake.go     # WebSocket handshake
│   ├── client/
│   │   └── client.go        # Client management
│   └── room/
│       └── room.go          # Room/channel management
├── pkg/
│   └── websocket/
│       └── frame.go         # Reusable frame utilities
├── examples/
│   └── client.html          # Browser test client
├── docs/
├── tests/
├── go.mod
├── README.md
└── LEARNING_NOTES.md
```

## Development Workflow

### 1. Make Changes

Edit the relevant files:
- `pkg/websocket/`: Core WebSocket frame handling
- `internal/server/`: HTTP server and upgrade logic
- `internal/client/`: Connection management
- `internal/room/`: Room/channel logic

### 2. Run Tests

```bash
# All tests
go test ./...

# Specific package
go test ./pkg/websocket -v

# With race detection
go test ./... -race

# With coverage
go test ./... -coverprofile=coverage.out
go tool cover -html=coverage.out
```

### 3. Build and Test

```bash
# Build
go build -o websocket-server ./cmd/server

# Run
./websocket-server

# Test with websocat
websocat ws://localhost:8080/ws

# Test with browser
# Open examples/client.html in browser
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
func TestReadFrame(t *testing.T) {
    // Arrange
    data := []byte{0x81, 0x05, 0x48, 0x65, 0x6c, 0x6c, 0x6f}
    reader := bytes.NewReader(data)

    // Act
    frame, err := ReadFrame(reader)

    // Assert
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }
    if !frame.Fin {
        t.Error("expected FIN bit to be set")
    }
    if frame.Opcode != OpcodeText {
        t.Errorf("expected opcode 0x1, got 0x%x", frame.Opcode)
    }
    if string(frame.Payload) != "Hello" {
        t.Errorf("expected payload 'Hello', got '%s'", string(frame.Payload))
    }
}
```

## Adding Features

### Adding a New Frame Type

1. Add opcode constant in `pkg/websocket/frame.go`:

```go
const OpcodeCustom byte = 0x3
```

2. Add handling in `ReadFrame` and `WriteFrame`

3. Add convenience constructor:

```go
func NewCustomFrame(payload []byte) *Frame {
    return &Frame{
        Fin:     true,
        Opcode:  OpcodeCustom,
        Payload: payload,
    }
}
```

4. Add tests

### Adding a New Room Feature

1. Add method in `internal/room/room.go`:

```go
func (r *Room) BroadcastExcept(sender *Client, msg []byte) {
    r.mu.RLock()
    defer r.mu.RUnlock()
    for client := range r.clients {
        if client != sender {
            client.Send(msg)
        }
    }
}
```

2. Add tests

### Adding Authentication

1. Add auth middleware in `internal/server/server.go`:

```go
func (s *Server) authMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        token := r.URL.Query().Get("token")
        if !s.validateToken(token) {
            http.Error(w, "Unauthorized", http.StatusUnauthorized)
            return
        }
        next.ServeHTTP(w, r)
    })
}
```

2. Add token validation logic

3. Add tests

## Debugging

### Enable Verbose Logging

```bash
# Set log level
export WS_LOG_LEVEL=debug

# Run
./websocket-server
```

### Browser DevTools

1. Open Chrome DevTools (F12)
2. Go to Network tab
3. Filter by "WS"
4. Click on WebSocket connection
5. View Messages tab for frame data

### websocat Debugging

```bash
# Install websocat
cargo install websocat

# Connect with verbose output
websocat -v ws://localhost:8080/ws

# Send message
echo "Hello" | websocat ws://localhost:8080/ws
```

### Delve Debugger

```bash
# Install dlv
go install github.com/go-delve/delve/cmd/dlv@latest

# Debug
dlv debug ./cmd/server

# Set breakpoint
(dlv) break main.main
(dlv) break pkg/websocket.ReadFrame
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
lsof -i :8080

# Kill process
kill -9 <PID>
```

### Race Conditions

```bash
# Run with race detector
go test ./... -race
```

### Connection Limit

```bash
# Check system limits
ulimit -n

# Increase limit
ulimit -n 65536
```

### WebSocket Handshake Fails

Common causes:
- Missing `Upgrade: websocket` header
- Incorrect `Sec-WebSocket-Key` calculation
- Wrong `Sec-WebSocket-Version` (must be 13)
- CORS issues (check `Origin` header)

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
- [RFC 6455](https://tools.ietf.org/html/rfc6455)
- [MDN WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)

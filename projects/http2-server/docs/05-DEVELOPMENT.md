# HTTP/2 Server Development Guide

## 1. Development Setup

### Prerequisites

```bash
# Install Go
brew install go  # macOS
# or
sudo apt install golang-go  # Ubuntu

# Verify installation
go version

# Install OpenSSL (for certificate generation)
brew install openssl  # macOS
# or
sudo apt install openssl  # Ubuntu
```

### Project Setup

```bash
# Clone repository
git clone <repository-url>
cd http2-server

# Initialize Go module
go mod init github.com/anthropic/http2-server

# Install dependencies
go mod tidy
```

### Generate TLS Certificate

```bash
# Generate self-signed certificate for development
openssl req -x509 -newkey rsa:2048 -keyout server.key -out server.crt -days 365 -nodes -subj "/CN=localhost"

# For production, use Let's Encrypt or proper CA
```

## 2. Building

### Build Server

```bash
# Build server binary
go build -o server ./cmd/server

# Build with version info
go build -ldflags "-X main.Version=1.0.0" -o server ./cmd/server

# Cross-compile for Linux
GOOS=linux GOARCH=amd64 go build -o server-linux ./cmd/server
```

### Build Client

```bash
# Build client binary
go build -o client ./cmd/client
```

## 3. Running

### Start Server

```bash
# Run with default settings
./server

# Run with custom settings
./server -addr :8443 -cert server.crt -key server.key

# Run with verbose logging
./server -v
```

### Test with Client

```bash
# Run client
./client -addr localhost:8443 -skip-verify

# Test specific endpoint
./client -addr localhost:8443 -skip-verify -path /health
```

### Test with curl

```bash
# Test with curl (requires HTTP/2 support)
curl --http2 -k https://localhost:8443/
curl --http2 -k https://localhost:8443/health
curl --http2 -k https://localhost:8443/info
```

## 4. Development Workflow

### Code Organization

```
http2-server/
├── cmd/                    # Entry points
│   ├── server/            # Server main
│   └── client/            # Client main
├── internal/              # Internal packages
│   ├── frame/            # Frame parsing
│   ├── connection/       # Connection management
│   └── handler/          # Request handling
├── docs/                  # Documentation
├── examples/              # Usage examples
└── tests/                 # Integration tests
```

### Adding New Features

1. **Create feature branch**
   ```bash
   git checkout -b feature/new-feature
   ```

2. **Implement feature**
   - Add code in appropriate package
   - Write tests
   - Update documentation

3. **Run tests**
   ```bash
   go test ./...
   ```

4. **Commit changes**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

5. **Create pull request**

## 5. Code Style

### Go Conventions

1. **Package names**: Lowercase, single word
2. **Function names**: CamelCase, exported functions start with uppercase
3. **Variable names**: CamelCase, unexported start with lowercase
4. **Comments**: Full sentences, start with name

### Example

```go
// Package frame implements HTTP/2 frame parsing and serialization.
package frame

// Frame represents an HTTP/2 frame.
type Frame struct {
    // Length is the frame payload length.
    Length uint32
    // Type is the frame type.
    Type uint8
}

// NewFrame creates a new frame with the given parameters.
func NewFrame(frameType uint8, payload []byte) *Frame {
    return &Frame{
        Type:    frameType,
        Length:  uint32(len(payload)),
        Payload: payload,
    }
}
```

### Error Handling

```go
// Always handle errors
result, err := doSomething()
if err != nil {
    return fmt.Errorf("failed to do something: %w", err)
}

// Use custom error types
type ValidationError struct {
    Field   string
    Message string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation failed: %s - %s", e.Field, e.Message)
}
```

## 6. Debugging

### Logging

```go
import "log"

// Use structured logging
log.Printf("Connection from %s", conn.RemoteAddr())
log.Printf("Stream %d: %s", streamID, state)
```

### Debug Mode

```go
var debug = os.Getenv("HTTP2_DEBUG") == "true"

func debugf(format string, args ...interface{}) {
    if debug {
        log.Printf("[DEBUG] "+format, args...)
    }
}
```

### Frame Logging

```go
func logFrame(f *Frame) {
    if debug {
        log.Printf("Frame: Type=%d Flags=0x%02x StreamID=%d Length=%d",
            f.Type, f.Flags, f.StreamID, f.Length)
    }
}
```

## 7. Testing

### Run Tests

```bash
# Run all tests
go test ./...

# Run specific package
go test ./internal/frame/...

# Run with verbose output
go test -v ./...

# Run with race detection
go test -race ./...

# Run benchmarks
go test -bench=. ./...
```

### Test Coverage

```bash
# Generate coverage report
go test -coverprofile=coverage.out ./...

# View coverage
go tool cover -html=coverage.out

# Show coverage percentage
go test -cover ./...
```

### Writing Tests

```go
func TestFeature(t *testing.T) {
    // Arrange
    input := "test"
    expected := "expected"

    // Act
    result, err := DoSomething(input)

    // Assert
    if err != nil {
        t.Fatalf("Unexpected error: %v", err)
    }
    if result != expected {
        t.Errorf("Expected %s, got %s", expected, result)
    }
}
```

## 8. Performance Profiling

### CPU Profiling

```bash
# Run with CPU profiling
go test -cpuprofile=cpu.out ./...

# Analyze profile
go tool pprof cpu.out
```

### Memory Profiling

```bash
# Run with memory profiling
go test -memprofile=mem.out ./...

# Analyze profile
go tool pprof mem.out
```

### Benchmark Analysis

```bash
# Run benchmarks
go test -bench=. ./... > bench.txt

# Compare benchmarks
benchstat bench_old.txt bench_new.txt
```

## 9. Documentation

### Generate Documentation

```bash
# Generate godoc
godoc -http=:6060

# View at http://localhost:6060/pkg/github.com/anthropic/http2-server/
```

### Writing Documentation

```go
// Package frame implements HTTP/2 frame parsing and serialization.
//
// HTTP/2 frames are the basic unit of communication in the protocol.
// Each frame has a 9-byte header followed by an optional payload.
//
// Example:
//
//	frame := NewFrame(FrameData, []byte("Hello"))
//	err := WriteFrame(conn, frame)
package frame
```

## 10. Deployment

### Docker

```dockerfile
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY . .
RUN go build -o server ./cmd/server

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /app/server .
COPY server.crt server.key ./
CMD ["./server"]
```

### Systemd Service

```ini
[Unit]
Description=HTTP/2 Server
After=network.target

[Service]
Type=simple
User=http2
ExecStart=/usr/local/bin/server -addr :8443
Restart=always

[Install]
WantedBy=multi-user.target
```

## 11. Monitoring

### Metrics

```go
import "expvar"

var (
    connectionsTotal = expvar.NewInt("connections_total")
    streamsActive    = expvar.NewInt("streams_active")
    framesProcessed  = expvar.NewInt("frames_processed")
)
```

### Health Check

```go
func healthHandler(w http.ResponseWriter, r *http.Request) {
    w.WriteHeader(http.StatusOK)
    w.Write([]byte(`{"status": "healthy"}`))
}
```

## 12. Security

### TLS Configuration

```go
tlsConfig := &tls.Config{
    MinVersion:               tls.VersionTLS12,
    CurvePreferences:         []tls.CurveID{tls.X25519, tls.CurveP256},
    PreferServerCipherSuites: true,
    CipherSuites: []uint16{
        tls.TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,
        tls.TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,
    },
}
```

### Input Validation

```go
func validateFrame(f *Frame) error {
    if f.Length > MaxFrameSize {
        return fmt.Errorf("frame too large: %d", f.Length)
    }
    if f.StreamID > MaxStreamID {
        return fmt.Errorf("invalid stream ID: %d", f.StreamID)
    }
    return nil
}
```

## 13. Common Issues

### Connection Refused

```bash
# Check if server is running
ps aux | grep server

# Check port
lsof -i :8443

# Check firewall
sudo iptables -L
```

### TLS Errors

```bash
# Verify certificate
openssl x509 -in server.crt -text -noout

# Test TLS connection
openssl s_client -connect localhost:8443 -servername localhost
```

### Performance Issues

```bash
# Check CPU usage
top -p $(pgrep server)

# Check memory usage
ps aux | grep server

# Profile CPU
go tool pprof http://localhost:6060/debug/pprof/profile
```

## 14. Contributing

### Code Review Checklist

1. [ ] Code compiles without errors
2. [ ] Tests pass
3. [ ] No race conditions
4. [ ] Error handling is complete
5. [ ] Documentation is updated
6. [ ] Code style is consistent

### Pull Request Template

```markdown
## Description
Brief description of changes

## Changes
- List of changes

## Testing
How to test the changes

## Checklist
- [ ] Code compiles
- [ ] Tests pass
- [ ] Documentation updated
```

## 15. Resources

### Go Resources

1. [Effective Go](https://golang.org/doc/effective_go.html)
2. [Go Code Review Comments](https://github.com/golang/go/wiki/CodeReviewComments)
3. [Go Standard Library](https://pkg.go.dev/std)

### HTTP/2 Resources

1. [RFC 7540](https://tools.ietf.org/html/rfc7540)
2. [RFC 7541](https://tools.ietf.org/html/rfc7541)
3. [HTTP/2 FAQ](https://http2.github.io/faq/)

### Tools

1. [curl](https://curl.se/) - HTTP client
2. [nghttp2](https://nghttp2.org/) - HTTP/2 library
3. [Wireshark](https://www.wireshark.org/) - Packet analyzer

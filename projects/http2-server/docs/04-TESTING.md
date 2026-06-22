# HTTP/2 Server Testing Guide

## 1. Testing Strategy

### Test Types

1. **Unit Tests**: Test individual components
2. **Integration Tests**: Test component interactions
3. **End-to-End Tests**: Test complete workflows
4. **Performance Tests**: Benchmark critical paths

### Test Coverage Goals

- Frame parsing: 100%
- HPACK encoding/decoding: 100%
- Stream management: 95%
- Connection handling: 90%

## 2. Unit Tests

### Frame Parsing Tests

```go
func TestFrameReadWrite(t *testing.T) {
    // Create test frame
    payload := []byte("Hello, HTTP/2!")
    frame := NewFrame(FrameData, FlagEndStream, 1, payload)

    // Write frame to buffer
    var buf bytes.Buffer
    if err := WriteFrame(&buf, frame); err != nil {
        t.Fatalf("WriteFrame failed: %v", err)
    }

    // Read frame back
    readFrame, err := ReadFrame(&buf)
    if err != nil {
        t.Fatalf("ReadFrame failed: %v", err)
    }

    // Verify fields
    if readFrame.Type != FrameData {
        t.Errorf("Expected type %d, got %d", FrameData, readFrame.Type)
    }
    if readFrame.Flags != FlagEndStream {
        t.Errorf("Expected flags %d, got %d", FlagEndStream, readFrame.Flags)
    }
    if readFrame.StreamID != 1 {
        t.Errorf("Expected stream ID 1, got %d", readFrame.StreamID)
    }
    if !bytes.Equal(readFrame.Payload, payload) {
        t.Errorf("Payload mismatch")
    }
}
```

### HPACK Tests

```go
func TestHPACK(t *testing.T) {
    encoder := NewHPACKEncoder(4096)
    decoder := NewHPACKDecoder(4096)

    headers := []HeaderField{
        {Name: ":method", Value: "GET"},
        {Name: ":path", Value: "/test"},
        {Name: ":scheme", Value: "https"},
        {Name: "host", Value: "example.com"},
    }

    // Encode headers
    encoded, err := encoder.EncodeHeaders(headers)
    if err != nil {
        t.Fatalf("EncodeHeaders failed: %v", err)
    }

    // Decode headers
    decoded, err := decoder.DecodeHeaders(encoded)
    if err != nil {
        t.Fatalf("DecodeHeaders failed: %v", err)
    }

    // Verify
    if len(decoded) != len(headers) {
        t.Fatalf("Header count mismatch")
    }

    for i, h := range decoded {
        if h.Name != headers[i].Name || h.Value != headers[i].Value {
            t.Errorf("Header %d mismatch", i)
        }
    }
}
```

### Stream Tests

```go
func TestStreamStateTransitions(t *testing.T) {
    stream := NewStream(1, 65535)

    // Initial state
    if stream.State != StreamIdle {
        t.Errorf("Expected Idle, got %d", stream.State)
    }

    // Open
    stream.State = StreamOpen
    if stream.State != StreamOpen {
        t.Errorf("Expected Open, got %d", stream.State)
    }

    // Half-closed
    stream.State = StreamHalfClosedRemote
    if stream.State != StreamHalfClosedRemote {
        t.Errorf("Expected HalfClosedRemote, got %d", stream.State)
    }

    // Closed
    stream.State = StreamClosed
    if stream.State != StreamClosed {
        t.Errorf("Expected Closed, got %d", stream.State)
    }
}
```

### Multiplexer Tests

```go
func TestMultiplexerRoundRobin(t *testing.T) {
    mux := NewMultiplexer()

    mux.AddStream(NewStream(1, 65535))
    mux.AddStream(NewStream(3, 65535))
    mux.AddStream(NewStream(5, 65535))

    // Test round-robin
    s1 := mux.GetNextStream()
    s2 := mux.GetNextStream()
    s3 := mux.GetNextStream()
    s4 := mux.GetNextStream() // Wraps around

    if s1.ID != 1 {
        t.Errorf("Expected stream 1, got %d", s1.ID)
    }
    if s2.ID != 3 {
        t.Errorf("Expected stream 3, got %d", s2.ID)
    }
    if s3.ID != 5 {
        t.Errorf("Expected stream 5, got %d", s3.ID)
    }
    if s4.ID != 1 {
        t.Errorf("Expected stream 1 (wrap), got %d", s4.ID)
    }
}
```

## 3. Integration Tests

### Connection Lifecycle Test

```go
func TestConnectionLifecycle(t *testing.T) {
    // Create mock connection
    mock := newMockConn()

    // Write client preface
    preface := []byte("PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n")
    mock.readBuf.Write(preface)

    // Write client settings
    settings := frame.DefaultSettings()
    settingsFrame := frame.CreateSettingsFrame(settings, 0)
    frame.WriteFrame(mock.readBuf, settingsFrame)

    // Create connection
    handler := func(stream *Stream) error {
        stream.ResponseCode = 200
        stream.ResponseHeaders = []frame.HeaderField{
            {Name: ":status", Value: "200"},
        }
        return nil
    }

    conn := NewConnection(mock, handler)

    // Process frames
    go conn.Start()

    // Wait for processing
    time.Sleep(100 * time.Millisecond)

    // Verify settings were sent
    // Verify connection is ready
}
```

### Request/Response Test

```go
func TestRequestResponse(t *testing.T) {
    mock := newMockConn()
    conn := NewConnection(mock, handler)

    // Create HEADERS frame
    encoder := frame.NewHPACKEncoder(4096)
    headers := []frame.HeaderField{
        {Name: ":method", Value: "GET"},
        {Name: ":path", Value: "/"},
    }
    encoded, _ := encoder.EncodeHeaders(headers)
    headersFrame := frame.NewFrame(frame.FrameHeaders, 
                                   frame.FlagEndHeaders|frame.FlagEndStream, 
                                   1, encoded)

    // Write to connection
    frame.WriteFrame(mock.readBuf, headersFrame)

    // Process
    go conn.Start()
    time.Sleep(100 * time.Millisecond)

    // Verify response was sent
    // Check mock.writeBuf for response frames
}
```

## 4. End-to-End Tests

### Server Test

```go
func TestServerE2E(t *testing.T) {
    // Generate self-signed cert
    cert, key := generateSelfSignedCert()

    // Start server
    go func() {
        server := &Server{
            Addr:    ":0",
            CertFile: cert,
            KeyFile:  key,
        }
        server.ListenAndServe()
    }()

    // Wait for server to start
    time.Sleep(100 * time.Millisecond)

    // Create client
    client := &Client{
        Addr:       "localhost:8443",
        SkipVerify: true,
    }

    // Make request
    resp, err := client.Get("/")
    if err != nil {
        t.Fatal(err)
    }

    // Verify response
    if resp.StatusCode != 200 {
        t.Errorf("Expected status 200, got %d", resp.StatusCode)
    }
}
```

## 5. Performance Tests

### Frame Parsing Benchmark

```go
func BenchmarkFrameReadWrite(b *testing.B) {
    payload := make([]byte, 1024)
    frame := NewFrame(FrameData, 0, 1, payload)

    var buf bytes.Buffer

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        buf.Reset()
        WriteFrame(&buf, frame)
        ReadFrame(&buf)
    }
}
```

### HPACK Benchmark

```go
func BenchmarkHPACKEncode(b *testing.B) {
    encoder := NewHPACKEncoder(4096)
    headers := []HeaderField{
        {Name: ":method", Value: "GET"},
        {Name: ":path", Value: "/"},
        {Name: "host", Value: "example.com"},
    }

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        encoder.EncodeHeaders(headers)
    }
}
```

### Multiplexer Benchmark

```go
func BenchmarkMultiplexerGetNext(b *testing.B) {
    mux := NewMultiplexer()
    for i := 0; i < 100; i++ {
        mux.AddStream(NewStream(uint32(i*2+1), 65535))
    }

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        mux.GetNextStream()
    }
}
```

## 6. Mock Objects

### Mock Connection

```go
type mockConn struct {
    readBuf  *bytes.Buffer
    writeBuf *bytes.Buffer
    mu       sync.Mutex
}

func (m *mockConn) Read(b []byte) (n int, err error) {
    m.mu.Lock()
    defer m.mu.Unlock()
    return m.readBuf.Read(b)
}

func (m *mockConn) Write(b []byte) (n int, err error) {
    m.mu.Lock()
    defer m.mu.Unlock()
    return m.writeBuf.Write(b)
}

func (m *mockConn) Close() error                       { return nil }
func (m *mockConn) LocalAddr() net.Addr                { return &net.TCPAddr{} }
func (m *mockConn) RemoteAddr() net.Addr               { return &net.TCPAddr{} }
func (m *mockConn) SetDeadline(t time.Time) error      { return nil }
func (m *mockConn) SetReadDeadline(t time.Time) error  { return nil }
func (m *mockConn) SetWriteDeadline(t time.Time) error { return nil }
```

## 7. Test Utilities

### Frame Helpers

```go
func createHeadersFrame(streamID uint32, headers []frame.HeaderField) *frame.Frame {
    encoder := frame.NewHPACKEncoder(4096)
    encoded, _ := encoder.EncodeHeaders(headers)
    return frame.NewFrame(frame.FrameHeaders, 
                          frame.FlagEndHeaders|frame.FlagEndStream, 
                          streamID, encoded)
}

func createDataFrame(streamID uint32, data []byte, endStream bool) *frame.Frame {
    flags := uint8(0)
    if endStream {
        flags = frame.FlagEndStream
    }
    return frame.NewFrame(frame.FrameData, flags, streamID, data)
}
```

### Assertion Helpers

```go
func assertFrameType(t *testing.T, f *frame.Frame, expectedType uint8) {
    t.Helper()
    if f.Type != expectedType {
        t.Errorf("Expected frame type %d, got %d", expectedType, f.Type)
    }
}

func assertStreamState(t *testing.T, s *Stream, expectedState StreamState) {
    t.Helper()
    if s.State != expectedState {
        t.Errorf("Expected stream state %d, got %d", expectedState, s.State)
    }
}
```

## 8. Test Configuration

### Environment Variables

```bash
# Skip TLS verification in tests
export HTTP2_TEST_SKIP_TLS_VERIFY=true

# Enable verbose logging
export HTTP2_TEST_VERBOSE=true

# Set test timeout
export HTTP2_TEST_TIMEOUT=30s
```

### Test Flags

```go
var (
    skipTLSVerify = flag.Bool("skip-tls-verify", false, "Skip TLS verification")
    verbose       = flag.Bool("verbose", false, "Verbose output")
    timeout       = flag.Duration("timeout", 30*time.Second, "Test timeout")
)
```

## 9. Continuous Integration

### GitHub Actions

```yaml
name: Test HTTP/2 Server

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-go@v2
        with:
          go-version: '1.21'
      - run: go test ./...
      - run: go test -bench=. ./...
```

### Test Coverage

```bash
# Generate coverage report
go test -coverprofile=coverage.out ./...

# View coverage
go tool cover -html=coverage.out
```

## 10. Debugging Tests

### Verbose Output

```bash
go test -v ./...
```

### Race Condition Detection

```bash
go test -race ./...
```

### Memory Leak Detection

```bash
go test -memprofile=mem.out ./...
go tool pprof mem.out
```

## 11. Test Data

### Sample Frames

```go
var sampleFrames = map[string]*frame.Frame{
    "headers": {
        Type:     frame.FrameHeaders,
        Flags:    frame.FlagEndHeaders | frame.FlagEndStream,
        StreamID: 1,
        Payload:  []byte{0x82, 0x86, 0x84, 0x41, 0x0f, 0x77, 0x77, 0x77, 0x2e, 0x65, 0x78, 0x61, 0x6d, 0x70, 0x6c, 0x65, 0x2e, 0x63, 0x6f, 0x6d},
    },
    "data": {
        Type:     frame.FrameData,
        Flags:    frame.FlagEndStream,
        StreamID: 1,
        Payload:  []byte("Hello, HTTP/2!"),
    },
    "settings": {
        Type:     frame.FrameSettings,
        Flags:    0,
        StreamID: 0,
        Payload:  []byte{0x00, 0x03, 0x00, 0x00, 0x00, 0x64},
    },
}
```

### Sample Headers

```go
var sampleHeaders = []frame.HeaderField{
    {Name: ":method", Value: "GET"},
    {Name: ":path", Value: "/"},
    {Name: ":scheme", Value: "https"},
    {Name: ":authority", Value: "example.com"},
    {Name: "accept", Value: "text/html"},
}
```

## 12. Test Best Practices

1. **Test One Thing**: Each test should test one behavior
2. **Use Descriptive Names**: Test names should describe what they test
3. **Arrange-Act-Assert**: Clear test structure
4. **Avoid Dependencies**: Tests should be independent
5. **Use Table Tests**: For testing multiple inputs
6. **Mock External Dependencies**: Don't rely on external services
7. **Test Edge Cases**: Empty inputs, maximum values, errors
8. **Keep Tests Fast**: Unit tests should run in milliseconds

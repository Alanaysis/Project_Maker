# HTTP/2 Server Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    HTTP/2 Server                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Frame     │  │   HPACK     │  │  Connection │         │
│  │   Parser    │  │   Codec     │  │  Manager    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│         │                │                │                 │
│         ▼                ▼                ▼                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Stream Multiplexer                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Request Handler / Router                │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Component Design

### 1. Frame Parser (`internal/frame/`)

**Responsibilities:**
- Parse HTTP/2 frame headers
- Serialize frames to bytes
- Validate frame types and flags

**Key Types:**
```go
type Frame struct {
    Length   uint32
    Type     uint8
    Flags    uint8
    StreamID uint32
    Payload  []byte
}
```

**Frame Types:**
- DATA (0x0): Request/response bodies
- HEADERS (0x1): Header fields
- SETTINGS (0x4): Connection settings
- WINDOW_UPDATE (0x8): Flow control
- GOAWAY (0x7): Connection shutdown

### 2. HPACK Codec (`internal/frame/hpack.go`)

**Responsibilities:**
- Encode headers to HPACK format
- Decode HPACK to headers
- Manage dynamic table

**Key Types:**
```go
type HPACKEncoder struct {
    dynamicTable []HeaderField
    maxSize      uint32
    currentSize  uint32
}

type HPACKDecoder struct {
    dynamicTable []HeaderField
    maxSize      uint32
    currentSize  uint32
}
```

**Compression Techniques:**
1. Static table indexing
2. Dynamic table indexing
3. Literal encoding with indexing

### 3. Connection Manager (`internal/connection/`)

**Responsibilities:**
- Manage TCP/TLS connection
- Process frames
- Handle connection lifecycle

**Key Types:**
```go
type Connection struct {
    conn          net.Conn
    streams       map[uint32]*Stream
    settings      *Settings
    peerSettings  *Settings
    encoder       *HPACKEncoder
    decoder       *HPACKDecoder
    lastStreamID  uint32
}
```

**Connection States:**
1. Initial
2. Preface received
3. Settings exchanged
4. Active
5. Goaway sent/received
6. Closed

### 4. Stream Manager (`internal/connection/multiplexer.go`)

**Responsibilities:**
- Create and manage streams
- Track stream states
- Implement multiplexing

**Key Types:**
```go
type Stream struct {
    ID            uint32
    State         StreamState
    Headers       []HeaderField
    Body          []byte
    ResponseCode  int
    SendWindow    int32
    ReceiveWindow int32
}
```

**Stream States:**
- idle
- open
- half-closed (local)
- half-closed (remote)
- closed

### 5. Request Handler (`internal/handler/`)

**Responsibilities:**
- Route requests to handlers
- Process request headers and body
- Generate responses

**Key Types:**
```go
type Router struct {
    routes map[string]map[string]HandlerFunc
}

type HandlerFunc func(stream *Stream) error
```

## Data Flow

### Request Processing

```
Client Request
      │
      ▼
┌─────────────┐
│ Read Frame  │
└─────────────┘
      │
      ▼
┌─────────────┐
│ Parse Frame │
└─────────────┘
      │
      ▼
┌─────────────┐
│ Route to    │
│ Handler     │
└─────────────┘
      │
      ▼
┌─────────────┐
│ Process     │
│ Request     │
└─────────────┘
      │
      ▼
┌─────────────┐
│ Send        │
│ Response    │
└─────────────┘
```

### Multiplexing Flow

```
Stream 1: HEADERS ──────────────────────────►
Stream 2: HEADERS ──────────────────────────►
Stream 1: DATA    ──────────────────────────►
Stream 2: DATA    ──────────────────────────►
Stream 1: DATA    ──────────────────────────►
Stream 2: END     ──────────────────────────►
Stream 1: END     ──────────────────────────►

Connection: [F1][F2][F3][F4][F5][F6][F7] ──►
```

## Concurrency Model

### Goroutines

1. **Connection Goroutine**: One per connection
   - Reads frames
   - Dispatches to handlers

2. **Stream Goroutines**: One per active stream
   - Processes request
   - Sends response

3. **Handler Goroutines**: Per-request
   - Executes business logic

### Synchronization

```go
type Connection struct {
    mu      sync.RWMutex
    streams map[uint32]*Stream
}

// Read lock for frame processing
c.mu.RLock()
stream := c.streams[frame.StreamID]
c.mu.RUnlock()

// Write lock for stream creation
c.mu.Lock()
c.streams[id] = newStream
c.mu.Unlock()
```

## Memory Management

### Frame Buffers

```go
// Reuse buffers where possible
var bufferPool = sync.Pool{
    New: func() interface{} {
        return make([]byte, 16384)
    },
}
```

### Dynamic Table

- Bounded size (default 4096 bytes)
- Eviction policy: LRU
- Memory pressure handling

## Error Handling

### Connection Errors

```go
func (c *Connection) sendGoaway(errCode uint32) error {
    payload := make([]byte, 8)
    // Last stream ID + error code
    goaway := frame.NewFrame(frame.FrameGoAway, 0, 0, payload)
    return frame.WriteFrame(c.conn, goaway)
}
```

### Stream Errors

```go
func (c *Connection) sendRstStream(streamID, errCode uint32) error {
    payload := make([]byte, 4)
    binary.BigEndian.PutUint32(payload, errCode)
    rst := frame.NewFrame(frame.FrameRSTStream, 0, streamID, payload)
    return frame.WriteFrame(c.conn, rst)
}
```

## Configuration

### Server Settings

```go
type Settings struct {
    HeaderTableSize      uint32
    EnablePush           uint32
    MaxConcurrentStreams uint32
    InitialWindowSize    uint32
    MaxFrameSize         uint32
    MaxHeaderListSize    uint32
}
```

### Default Values

- HeaderTableSize: 4096
- EnablePush: 1 (enabled)
- MaxConcurrentStreams: 100
- InitialWindowSize: 65535
- MaxFrameSize: 16384
- MaxHeaderListSize: unlimited

## Security Considerations

### TLS Requirements

1. TLS 1.2 or later
2. Strong cipher suites
3. Certificate validation
4. ALPN negotiation (h2)

### Input Validation

1. Frame size limits
2. Stream ID validation
3. Header size limits
4. Flow control bounds

## Performance Optimizations

### Header Compression

1. Static table: 1-2 bytes for common headers
2. Dynamic table: Learned from requests
3. Huffman coding: Variable-length encoding

### Multiplexing

1. Single connection: Reduce overhead
2. No head-of-line blocking: Independent streams
3. Fair scheduling: Round-robin or weighted

### Flow Control

1. Window-based: Prevent overwhelming
2. Adaptive windows: Match processing speed
3. Prioritization: Important streams first

## Testing Strategy

### Unit Tests

1. Frame parsing/serialization
2. HPACK encoding/decoding
3. Stream state management
4. Flow control logic

### Integration Tests

1. Connection lifecycle
2. Multiplexing scenarios
3. Error handling
4. Performance benchmarks

### Tools

1. curl: HTTP/2 client testing
2. nghttp: Debugging
3. Wireshark: Packet analysis

## Extension Points

### Custom Handlers

```go
type Handler interface {
    Handle(stream *Stream) error
}
```

### Middleware

```go
type Middleware func(Handler) Handler
```

### Custom Frame Types

```go
const FrameCustom uint8 = 0x10
```

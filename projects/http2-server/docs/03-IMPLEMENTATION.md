# HTTP/2 Server Implementation Guide

## 1. Project Setup

### Directory Structure

```
http2-server/
├── cmd/
│   ├── server/         # Server entry point
│   └── client/         # Client for testing
├── internal/
│   ├── frame/          # HTTP/2 frame parsing
│   ├── connection/     # Connection management
│   └── handler/        # Request handling
├── docs/               # Documentation
├── go.mod
└── README.md
```

### Go Module

```go
module github.com/anthropic/http2-server

go 1.21
```

## 2. Frame Parsing Implementation

### Frame Structure

```go
type Frame struct {
    Length   uint32 // 24 bits
    Type     uint8  // 8 bits
    Flags    uint8  // 8 bits
    StreamID uint32 // 31 bits
    Payload  []byte
}
```

### Reading Frames

```go
func ReadFrame(r io.Reader) (*Frame, error) {
    // Read 9-byte header
    header := make([]byte, FrameHeaderSize)
    if _, err := io.ReadFull(r, header); err != nil {
        return nil, err
    }

    // Parse header
    length := uint32(header[0])<<16 | uint32(header[1])<<8 | uint32(header[2])
    frameType := header[3]
    flags := header[4]
    streamID := binary.BigEndian.Uint32(header[5:9]) & 0x7FFFFFFF

    // Read payload
    payload := make([]byte, length)
    if length > 0 {
        if _, err := io.ReadFull(r, payload); err != nil {
            return nil, err
        }
    }

    return &Frame{
        Length:   length,
        Type:     frameType,
        Flags:    flags,
        StreamID: streamID,
        Payload:  payload,
    }, nil
}
```

### Writing Frames

```go
func WriteFrame(w io.Writer, f *Frame) error {
    // Create header
    header := make([]byte, FrameHeaderSize)
    header[0] = byte(f.Length >> 16)
    header[1] = byte(f.Length >> 8)
    header[2] = byte(f.Length)
    header[3] = f.Type
    header[4] = f.Flags
    binary.BigEndian.PutUint32(header[5:9], f.StreamID&0x7FFFFFFF)

    // Write header
    if _, err := w.Write(header); err != nil {
        return err
    }

    // Write payload
    if len(f.Payload) > 0 {
        if _, err := w.Write(f.Payload); err != nil {
            return err
        }
    }

    return nil
}
```

## 3. HPACK Implementation

### Static Table

```go
var staticTable = []HeaderField{
    {":authority", ""},                    // 1
    {":method", "GET"},                    // 2
    {":method", "POST"},                   // 3
    {":path", "/"},                        // 4
    {":path", "/index.html"},              // 5
    {":scheme", "http"},                   // 6
    {":scheme", "https"},                  // 7
    {":status", "200"},                    // 8
    // ... more entries
}
```

### Integer Encoding

```go
func writeInt(buf *bytes.Buffer, value uint64, n uint8) {
    if value < (1<<n)-1 {
        buf.WriteByte(byte(value))
        return
    }

    buf.WriteByte(byte((1 << n) - 1))
    value -= (1 << n) - 1
    for value >= 128 {
        buf.WriteByte(byte(value&0x7f) | 0x80)
        value >>= 7
    }
    buf.WriteByte(byte(value))
}
```

### String Encoding

```go
func writeString(buf *bytes.Buffer, s string) {
    writeInt(buf, uint64(len(s)), 7)
    buf.WriteString(s)
}
```

### Dynamic Table Management

```go
func (e *HPACKEncoder) addToDynamicTable(hf HeaderField) {
    entrySize := uint32(len(hf.Name) + len(hf.Value) + 32)

    // Evict entries if necessary
    for e.currentSize+entrySize > e.maxSize && len(e.dynamicTable) > 0 {
        e.currentSize -= uint32(len(e.dynamicTable[0].Name) + 
                               len(e.dynamicTable[0].Value) + 32)
        e.dynamicTable = e.dynamicTable[1:]
    }

    if entrySize <= e.maxSize {
        e.dynamicTable = append([]HeaderField{hf}, e.dynamicTable...)
        e.currentSize += entrySize
    }
}
```

## 4. Connection Management

### Connection Structure

```go
type Connection struct {
    conn          net.Conn
    streams       map[uint32]*Stream
    mu            sync.RWMutex
    settings      *Settings
    peerSettings  *Settings
    encoder       *HPACKEncoder
    decoder       *HPACKDecoder
    lastStreamID  uint32
}
```

### Connection Lifecycle

```go
func (c *Connection) Start() error {
    // Send settings
    if err := c.sendSettings(); err != nil {
        return err
    }

    // Read loop
    return c.readLoop()
}

func (c *Connection) readLoop() error {
    for {
        f, err := frame.ReadFrame(c.conn)
        if err != nil {
            return err
        }

        if err := c.handleFrame(f); err != nil {
            return err
        }
    }
}
```

### Frame Handling

```go
func (c *Connection) handleFrame(f *frame.Frame) error {
    switch f.Type {
    case frame.FrameSettings:
        return c.handleSettings(f)
    case frame.FrameHeaders:
        return c.handleHeaders(f)
    case frame.FrameData:
        return c.handleData(f)
    case frame.FrameWindowUpdate:
        return c.handleWindowUpdate(f)
    case frame.FramePing:
        return c.handlePing(f)
    case frame.FrameGoAway:
        return c.handleGoAway(f)
    default:
        return nil
    }
}
```

## 5. Stream Management

### Stream States

```go
type StreamState int

const (
    StreamIdle            StreamState = iota
    StreamReservedLocal
    StreamReservedRemote
    StreamOpen
    StreamHalfClosedLocal
    StreamHalfClosedRemote
    StreamClosed
)
```

### Stream Creation

```go
func NewStream(id uint32, initialWindowSize int32) *Stream {
    return &Stream{
        ID:            id,
        State:         StreamIdle,
        SendWindow:    initialWindowSize,
        ReceiveWindow: initialWindowSize,
        dataChan:      make(chan []byte, 10),
        headersChan:   make(chan []HeaderField, 10),
        doneChan:      make(chan struct{}),
    }
}
```

### Stream Processing

```go
func (c *Connection) handleHeaders(f *frame.Frame) error {
    streamID := f.StreamID

    // Validate stream ID
    if streamID%2 == 0 {
        return fmt.Errorf("client stream ID must be odd")
    }

    // Create stream
    stream := NewStream(streamID, c.settings.InitialWindowSize)
    stream.State = StreamOpen

    // Decode headers
    headers, err := c.decoder.DecodeHeaders(f.Payload)
    if err != nil {
        return err
    }

    stream.Headers = headers
    c.streams[streamID] = stream

    // Process if complete
    if f.Flags&frame.FlagEndStream != 0 {
        stream.State = StreamHalfClosedRemote
        go c.processRequest(stream)
    }

    return nil
}
```

## 6. Multiplexing Implementation

### Multiplexer Structure

```go
type Multiplexer struct {
    streams map[uint32]*Stream
    mu      sync.RWMutex
    currentIndex int
    streamOrder  []uint32
}
```

### Round-Robin Scheduling

```go
func (m *Multiplexer) GetNextStream() *Stream {
    m.mu.Lock()
    defer m.mu.Unlock()

    if len(m.streamOrder) == 0 {
        return nil
    }

    streamID := m.streamOrder[m.currentIndex]
    m.currentIndex = (m.currentIndex + 1) % len(m.streamOrder)

    return m.streams[streamID]
}
```

### Frame Interleaving

```go
func (m *Multiplexer) InterleaveFrames(streams []*Stream) []*frame.Frame {
    var frames []*frame.Frame

    for _, stream := range streams {
        if stream.State == StreamOpen && len(stream.Body) > 0 {
            f := frame.NewFrame(frame.FrameData, 0, stream.ID, stream.Body)
            frames = append(frames, f)
        }
    }

    return frames
}
```

## 7. Flow Control

### Window Management

```go
func (c *Connection) handleWindowUpdate(f *frame.Frame) error {
    increment := int32(f.Payload[0])<<24 | int32(f.Payload[1])<<16 |
                 int32(f.Payload[2])<<8 | int32(f.Payload[3])

    if f.StreamID == 0 {
        c.sendWindowSize += increment
    } else {
        stream := c.streams[f.StreamID]
        stream.SendWindow += increment
    }

    return nil
}
```

### Window Update Sending

```go
func (c *Connection) sendWindowUpdate(streamID uint32, increment int32) error {
    payload := make([]byte, 4)
    payload[0] = byte(increment >> 24)
    payload[1] = byte(increment >> 16)
    payload[2] = byte(increment >> 8)
    payload[3] = byte(increment)

    wu := frame.NewFrame(frame.FrameWindowUpdate, 0, streamID, payload)
    return frame.WriteFrame(c.conn, wu)
}
```

## 8. Request Handling

### Router

```go
type Router struct {
    routes map[string]map[string]HandlerFunc
}

func (r *Router) Get(path string, handler HandlerFunc) {
    r.addRoute("GET", path, handler)
}

func (r *Router) Handle(stream *Stream) error {
    var method, path string
    for _, h := range stream.Headers {
        switch h.Name {
        case ":method":
            method = h.Value
        case ":path":
            path = h.Value
        }
    }

    handler := r.routes[method][path]
    return handler(stream)
}
```

### Response Sending

```go
func (c *Connection) SendResponse(stream *Stream) error {
    // Encode headers
    encoded, err := c.encoder.EncodeHeaders(stream.ResponseHeaders)
    if err != nil {
        return err
    }

    // Send HEADERS frame
    headersFrame := frame.NewFrame(frame.FrameHeaders, 
                                   frame.FlagEndHeaders, 
                                   stream.ID, encoded)
    if err := frame.WriteFrame(c.conn, headersFrame); err != nil {
        return err
    }

    // Send DATA frame
    if len(stream.ResponseBody) > 0 {
        dataFrame := frame.NewFrame(frame.FrameData, 
                                    frame.FlagEndStream, 
                                    stream.ID, stream.ResponseBody)
        return frame.WriteFrame(c.conn, dataFrame)
    }

    return nil
}
```

## 9. TLS Configuration

### Certificate Loading

```go
cert, err := tls.LoadX509KeyPair("server.crt", "server.key")
if err != nil {
    log.Fatal(err)
}

tlsConfig := &tls.Config{
    Certificates: []tls.Certificate{cert},
    NextProtos:   []string{"h2"},
}
```

### TLS Listener

```go
listener, err := tls.Listen("tcp", ":8443", tlsConfig)
if err != nil {
    log.Fatal(err)
}
```

## 10. Testing

### Unit Tests

```go
func TestFrameReadWrite(t *testing.T) {
    payload := []byte("Hello, HTTP/2!")
    frame := NewFrame(FrameData, FlagEndStream, 1, payload)

    var buf bytes.Buffer
    WriteFrame(&buf, frame)

    readFrame, err := ReadFrame(&buf)
    if err != nil {
        t.Fatal(err)
    }

    if readFrame.Type != FrameData {
        t.Error("Type mismatch")
    }
}
```

### Integration Tests

```go
func TestConnectionLifecycle(t *testing.T) {
    // Create mock connection
    mock := newMockConn()

    // Create HTTP/2 connection
    conn := NewConnection(mock, handler)

    // Test settings exchange
    // Test stream creation
    // Test request/response
}
```

## 11. Error Handling

### Connection Errors

```go
func (c *Connection) sendGoaway(errCode uint32) error {
    payload := make([]byte, 8)
    binary.BigEndian.PutUint32(payload[0:4], c.lastStreamID)
    binary.BigEndian.PutUint32(payload[4:8], errCode)

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

## 12. Performance Considerations

### Buffer Pooling

```go
var bufferPool = sync.Pool{
    New: func() interface{} {
        return make([]byte, 16384)
    },
}
```

### Connection Pooling

```go
type ConnectionPool struct {
    connections chan *Connection
    maxSize     int
}
```

### Header Compression

- Use static table for common headers
- Dynamic table for repeated headers
- Huffman coding for values

## 13. Debugging

### Frame Logging

```go
func (f *Frame) String() string {
    return fmt.Sprintf("Frame{Type: %s, Flags: 0x%02x, StreamID: %d, Length: %d}",
        typeName, f.Flags, f.StreamID, f.Length)
}
```

### State Tracking

```go
func (s *Stream) SetState(state StreamState) {
    log.Printf("Stream %d: %d -> %d", s.ID, s.State, state)
    s.State = state
}
```

## 14. Future Enhancements

1. **Server Push**: Push resources to client
2. **Priority Handling**: Stream prioritization
3. **Huffman Coding**: Better compression
4. **Connection Draining**: Graceful shutdown
5. **Metrics**: Performance monitoring
6. **Rate Limiting**: Request throttling

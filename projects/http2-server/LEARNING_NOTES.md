# Learning Notes: HTTP/2 Server Implementation

## Key Concepts Learned

### 1. HTTP/2 Frame Structure

HTTP/2 frames are the basic unit of communication. Each frame has:

```
+-----------------------------------------------+
|                 Length (24)                    |
+---------------+---------------+---------------+
|   Type (8)    |   Flags (8)   |
+-+-------------+---------------+-------------------------------+
|R|                 Stream Identifier (31)                      |
+-+-------------------------------------------------------------+
|                   Frame Payload (0...)                      ...
+---------------------------------------------------------------+
```

**Key frame types:**
- DATA: Carries request/response bodies
- HEADERS: Carries header fields
- SETTINGS: Connection configuration
- WINDOW_UPDATE: Flow control
- PING: Connection liveness
- GOAWAY: Graceful shutdown

### 2. HPACK Header Compression

HPACK uses three techniques:

1. **Static Table**: 61 pre-defined header entries
   - Common headers like `:method GET`, `:path /`, `:status 200`
   - Indexed by position (1-based)

2. **Dynamic Table**: Learned from previous requests
   - Evicted when table size exceeds limit
   - Most recently used entries at the beginning

3. **Huffman Coding**: Variable-length encoding
   - Common characters use fewer bits
   - Applied to header values

**Encoding types:**
- Indexed Header Field (1xxxxxxx): Reference to table
- Literal with Incremental Indexing (01xxxxxx): Add to dynamic table
- Literal without Indexing (0000xxxx): Don't add to table
- Dynamic Table Size Update (001xxxxx): Change table size

### 3. Stream Multiplexing

**Stream States:**
```
       idle
        |
        v
    +-------+
    | open  |
    +-------+
        |
        v
    +-----------+
    | half-     |
    | closed    |
    +-----------+
        |
        v
    +-----------+
    | closed    |
    +-----------+
```

**Key points:**
- Client streams use odd IDs (1, 3, 5, ...)
- Server streams use even IDs (2, 4, 6, ...)
- Frames from different streams can be interleaved
- No head-of-line blocking at the HTTP layer

### 4. Flow Control

**Window-based mechanism:**
- Sender can only send data up to window size
- Receiver sends WINDOW_UPDATE to increase window
- Both connection-level and stream-level windows

**Window management:**
1. Initial window size: 65,535 bytes
2. SETTINGS frame can change initial window
3. WINDOW_UPDATE can increase window
4. Window cannot exceed 2^31 - 1

### 5. Connection Lifecycle

**Connection setup:**
1. Client sends connection preface
2. Client sends SETTINGS frame
3. Server sends SETTINGS frame
4. Both send SETTINGS ACK
5. Connection is ready

**Connection teardown:**
1. Send GOAWAY frame
2. Process remaining streams
3. Close connection

## Implementation Challenges

### Challenge 1: Frame Parsing

**Problem:** Reading exact number of bytes for frame header and payload.

**Solution:** Use `io.ReadFull` to ensure complete reads:
```go
header := make([]byte, 9)
if _, err := io.ReadFull(r, header); err != nil {
    return nil, err
}
```

### Challenge 2: HPACK Integer Encoding

**Problem:** Variable-length integer encoding.

**Solution:** Use prefix bits to determine encoding:
```go
func writeInt(buf *bytes.Buffer, value uint64, n uint8) {
    if value < (1<<n)-1 {
        buf.WriteByte(byte(value))
        return
    }
    // Multi-byte encoding
    buf.WriteByte(byte((1 << n) - 1))
    value -= (1 << n) - 1
    for value >= 128 {
        buf.WriteByte(byte(value&0x7f) | 0x80)
        value >>= 7
    }
    buf.WriteByte(byte(value))
}
```

### Challenge 3: Multiplexing

**Problem:** Managing multiple streams on a single connection.

**Solution:** Use a map of streams with mutex protection:
```go
type Connection struct {
    streams map[uint32]*Stream
    mu      sync.RWMutex
}
```

### Challenge 4: Flow Control

**Problem:** Preventing overwhelming the receiver.

**Solution:** Track window size and send WINDOW_UPDATE:
```go
if c.receiveWindowSize < threshold {
    c.sendWindowUpdate(0, increment)
}
```

## Performance Considerations

### 1. Header Compression Efficiency

**Static table hits:** Common headers are encoded in 1-2 bytes
**Dynamic table:** Repeated headers are encoded efficiently
**Trade-off:** Memory for compression tables

### 2. Multiplexing Benefits

**Without multiplexing (HTTP/1.1):**
- One request at a time per connection
- Head-of-line blocking
- Multiple connections needed

**With multiplexing (HTTP/2):**
- Multiple concurrent requests
- No head-of-line blocking
- Single connection

### 3. Flow Control Tuning

**Too small window:** Limits throughput
**Too large window:** Can cause memory issues
**Optimal:** Match sender/receiver processing speeds

## Debugging Tips

### 1. Frame Inspection

```go
fmt.Printf("Frame: Type=%d, Flags=0x%02x, StreamID=%d, Length=%d\n",
    f.Type, f.Flags, f.StreamID, f.Length)
```

### 2. HPACK Debugging

```go
// Log static table hits
if idx <= len(staticTable) {
    fmt.Printf("Static table hit: %d -> %s: %s\n",
        idx, staticTable[idx-1].Name, staticTable[idx-1].Value)
}
```

### 3. Stream State Tracking

```go
fmt.Printf("Stream %d state: %d -> %d\n", stream.ID, oldState, newState)
```

## Further Reading

1. **RFC 7540**: HTTP/2 specification
2. **RFC 7541**: HPACK specification
3. **HTTP/2 FAQ**: Common questions and answers
4. **gRPC**: Uses HTTP/2 for RPC

## Exercises

1. **Add Huffman coding** to HPACK encoder
2. **Implement server push** for static assets
3. **Add priority** and dependency handling
4. **Implement connection draining** for graceful shutdown
5. **Add metrics** for monitoring

## Summary

HTTP/2 is a significant improvement over HTTP/1.1:
- **Multiplexing** eliminates head-of-line blocking
- **Header compression** reduces overhead
- **Flow control** prevents overwhelming receivers
- **Binary framing** is more efficient than text

The implementation demonstrates these core concepts while providing a foundation for more advanced features.

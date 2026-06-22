# HTTP/2 Server Research

## 1. HTTP/2 Protocol Overview

### History
- HTTP/1.1 (1997): Text-based, one request per connection (with pipelining)
- SPDY (2009): Google's experimental protocol
- HTTP/2 (2015): Standardized as RFC 7540

### Key Improvements over HTTP/1.1

| Feature | HTTP/1.1 | HTTP/2 |
|---------|----------|--------|
| Protocol | Text-based | Binary |
| Multiplexing | No (pipelining issues) | Yes |
| Header Compression | No | Yes (HPACK) |
| Server Push | No | Yes |
| Flow Control | No | Yes |
| Prioritization | No | Yes |

## 2. HTTP/2 Frame Format

### Frame Structure (9 bytes header)
```
+-----------------------------------------------+
|                 Length (24)                    |
+---------------+---------------+---------------+
|   Type (8)    |   Flags (8)   |
+-+-------------+---------------+-------------------------------+
|R|                 Stream Identifier (31)                      |
+-+-------------------------------------------------------------+
```

### Frame Types
1. **DATA (0x0)**: Carries request/response bodies
2. **HEADERS (0x1)**: Carries header fields
3. **PRIORITY (0x2)**: Stream priority
4. **RST_STREAM (0x3)**: Stream termination
5. **SETTINGS (0x4)**: Connection configuration
6. **PUSH_PROMISE (0x5)**: Server push
7. **PING (0x6)**: Connection liveness
8. **GOAWAY (0x7)**: Graceful shutdown
9. **WINDOW_UPDATE (0x8)**: Flow control
10. **CONTINUATION (0x9)**: Continued header blocks

### Maximum Frame Size
- Default: 16,384 bytes (16 KB)
- Minimum: 16,384 bytes
- Maximum: 16,777,215 bytes (2^24 - 1)

## 3. HPACK Header Compression

### Static Table
61 pre-defined header entries:
- Common headers like `:method GET`, `:path /`
- Frequently used values like `:status 200`
- Indexed from 1 to 61

### Dynamic Table
- Learned from previous requests
- Evicted when size exceeds limit
- Most recently used at the beginning

### Encoding Types
1. **Indexed Header Field (1xxxxxxx)**:
   - References table entry
   - 1 byte for common headers

2. **Literal with Incremental Indexing (01xxxxxx)**:
   - Adds to dynamic table
   - Used for repeated headers

3. **Literal without Indexing (0000xxxx)**:
   - Doesn't add to table
   - Used for sensitive headers

4. **Dynamic Table Size Update (001xxxxx)**:
   - Changes table size limit

### Integer Encoding
Variable-length encoding with prefix:
```
  0   1   2   3   4   5   6   7
+---+---+---+---+---+---+---+---+
| 0 | 0 | 0 | 1 |   Value (4+)  |
+---+---+---+---+---+---+---+---+
```

## 4. Stream Multiplexing

### Stream States
1. **idle**: Initial state
2. **open**: Active stream
3. **half-closed (local)**: Sent END_STREAM
4. **half-closed (remote)**: Received END_STREAM
5. **closed**: Stream completed

### Stream Identifiers
- Client-initiated: Odd numbers (1, 3, 5, ...)
- Server-initiated: Even numbers (2, 4, 6, ...)
- Stream 0: Connection control

### Multiplexing Benefits
1. **No head-of-line blocking**: Streams are independent
2. **Single connection**: Reduces overhead
3. **Better resource utilization**: Concurrent requests

## 5. Flow Control

### Window-based Mechanism
- Sender can only send data up to window size
- Receiver sends WINDOW_UPDATE to increase window
- Both connection-level and stream-level windows

### Window Management
1. **Initial window size**: 65,535 bytes
2. **SETTINGS frame**: Can change initial window
3. **WINDOW_UPDATE**: Can increase window
4. **Maximum window**: 2^31 - 1 bytes

### Flow Control Rules
1. Sender MUST NOT send data exceeding window
2. Receiver MUST NOT reduce window size
3. WINDOW_UPDATE applies to future data

## 6. Connection Lifecycle

### Connection Setup
1. Client sends connection preface:
   ```
   PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n
   ```
2. Client sends SETTINGS frame
3. Server sends SETTINGS frame
4. Both send SETTINGS ACK
5. Connection is ready

### Connection Teardown
1. Send GOAWAY frame
2. Process remaining streams
3. Close connection

### Error Handling
1. **Connection errors**: Send GOAWAY
2. **Stream errors**: Send RST_STREAM
3. **Protocol errors**: Connection error

## 7. Implementation Considerations

### Performance
1. **Header compression**: Reduces bandwidth
2. **Multiplexing**: Reduces latency
3. **Flow control**: Prevents overwhelming

### Security
1. **TLS required**: HTTP/2 over TLS (h2)
2. **Cipher suites**: Modern, secure ciphers
3. **Certificate validation**: Proper TLS validation

### Debugging
1. **Frame logging**: Log all frames
2. **State tracking**: Track stream states
3. **Error handling**: Proper error reporting

## 8. Existing Implementations

### Go Libraries
1. **golang.org/x/net/http2**: Official HTTP/2 package
2. **github.com/valyala/fasthttp**: High-performance HTTP
3. **github.com/lucas-clemente/quic-go**: QUIC implementation

### Reference Implementations
1. **nghttp2**: C library
2. **h2o**: High-performance server
3. **Envoy**: Service proxy

## 9. Testing Strategy

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
1. **curl**: HTTP/2 client
2. **nghttp**: HTTP/2 debugging
3. **Wireshark**: Packet analysis

## 10. References

1. [RFC 7540 - HTTP/2](https://tools.ietf.org/html/rfc7540)
2. [RFC 7541 - HPACK](https://tools.ietf.org/html/rfc7541)
3. [HTTP/2 FAQ](https://http2.github.io/faq/)
4. [HPACK Static Table](https://httpwg.org/specs/rfc7541.html#static.table)

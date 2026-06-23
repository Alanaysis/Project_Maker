# Learning Notes - WebSocket Server Implementation

## What I Learned

### 1. WebSocket Protocol Fundamentals

WebSocket is a communication protocol that provides full-duplex communication channels over a single TCP connection. Unlike HTTP's request-response model, WebSocket allows persistent connections where both client and server can send data at any time.

**Key Takeaway**: WebSocket is not a replacement for HTTP -- it starts as an HTTP connection and upgrades to WebSocket via a handshake. After the upgrade, the connection stays open for bidirectional communication.

### 2. HTTP Upgrade Handshake

The WebSocket connection begins with an HTTP upgrade request:

```
GET /ws HTTP/1.1
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13
```

The server responds with:
```
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

**Key Takeaway**: The `Sec-WebSocket-Key` is base64-encoded random bytes. The server concatenates it with a magic GUID (`258EAFA5-E914-47DA-95CA-C5AB0DC85B11`), SHA-1 hashes it, and base64-encodes the result for `Sec-WebSocket-Accept`.

### 3. WebSocket Frame Format

All WebSocket data is transmitted as frames. Each frame has a specific structure:

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-------+-+-------------+-------------------------------+
|F|R|R|R| opcode|M| Payload len |    Extended payload length    |
|I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
|N|V|V|V|       |S|             |   (if payload len==126/127)   |
| |1|2|3|       |K|             |                               |
+-+-+-+-+-------+-+-------------+-------------------------------+
```

**Key Takeaway**: The payload length field uses a variable-length encoding:
- 0-125: length is the value itself
- 126: next 2 bytes are the length (16-bit)
- 127: next 8 bytes are the length (64-bit)

### 4. Frame Opcodes

WebSocket defines several frame types via opcodes:

| Opcode | Type | Description |
|--------|------|-------------|
| 0x0 | Continuation | Fragment continuation |
| 0x1 | Text | UTF-8 text data |
| 0x2 | Binary | Binary data |
| 0x8 | Close | Connection close |
| 0x9 | Ping | Heartbeat request |
| 0xA | Pong | Heartbeat response |

**Key Takeaway**: Control frames (0x8-0xF) must not be fragmented and their payload must be 125 bytes or less.

### 5. Masking

Client-to-server frames MUST be masked. Server-to-client frames MUST NOT be masked.

The masking key is a 4-byte random value. Each payload byte is XORed with the corresponding mask byte:

```
masked[i] = original[i] XOR mask[i % 4]
```

**Key Takeaway**: Masking prevents cache poisoning attacks on intermediary proxies. The XOR operation is its own inverse, so the same function works for both masking and unmasking.

### 6. Connection Management

Managing multiple WebSocket connections requires:

- **Thread-safe storage**: Using `sync.RWMutex` to protect the connection map
- **Graceful cleanup**: Removing connections when clients disconnect
- **Heartbeat detection**: Using ping/pong frames to detect dead connections

**Key Takeaway**: The server must handle concurrent access to shared connection state. Goroutines per connection is the idiomatic Go approach.

### 7. Concurrency in Go

Go's goroutines make WebSocket server implementation straightforward:

```go
// Each connection gets its own goroutine
go func() {
    defer conn.Close()
    for {
        msg, err := readMessage(conn)
        if err != nil {
            break
        }
        broadcast(msg)
    }
}()
```

**Key Takeaway**: Use `sync.RWMutex` for read-heavy workloads (many reads, few writes). The broadcast pattern benefits from this optimization.

### 8. Room/Channel System

A room system allows grouping connections for targeted message delivery:

- Each room maintains a set of connections
- Clients can join/leave rooms
- Messages can be broadcast to specific rooms

**Key Takeaway**: This pattern is common in chat applications, live dashboards, and multiplayer games.

## Challenges Faced

### 1. Parsing Variable-Length Payload Lengths

The WebSocket frame format uses three different encoding schemes for payload length depending on the value. This required careful bit manipulation.

**Solution**: Used a switch statement on the initial 7-bit value to determine the encoding scheme.

### 2. Byte Order

WebSocket uses big-endian (network byte order) for multi-byte values, consistent with network protocols.

**Solution**: Used `encoding/binary.BigEndian` for all multi-byte value encoding/decoding.

### 3. Control Frame Restrictions

Control frames (ping, pong, close) have strict rules:
- Must not be fragmented (FIN bit must be set)
- Payload must be 125 bytes or less
- Must not have the MASK bit set (server frames)

**Solution**: Added validation in `WriteFrame` to enforce these constraints.

### 4. Masking Implementation

The masking algorithm is simple but must be applied correctly:
- Client frames MUST be masked
- Server frames MUST NOT be masked
- Masking key is 4 bytes, cycled with modulo

**Solution**: Implemented masking/unmasking in `ReadFrame` with clear documentation.

## Design Decisions

### 1. Package Structure

Organized into focused packages:
- `pkg/websocket`: Core WebSocket protocol (frame encoding/decoding)
- `internal/server`: HTTP server and upgrade handling
- `internal/client`: Client connection management
- `internal/room`: Room/channel management

This separation makes the protocol implementation reusable.

### 2. No Third-Party Dependencies

The entire implementation uses only the Go standard library:
- `encoding/binary` for byte order conversion
- `crypto/sha1` for WebSocket accept key generation
- `encoding/base64` for key encoding
- `net/http` for HTTP server

**Key Takeaway**: WebSocket protocol is simple enough to implement from scratch. This approach provides better learning value and avoids dependency bloat.

### 3. Functional Options Pattern

Used functional options for server configuration:

```go
type Option func(*Server)

func WithAddr(addr string) Option {
    return func(s *Server) {
        s.addr = addr
    }
}
```

This provides a clean API with sensible defaults.

## What I Would Do Differently

1. **Add compression support**: Per-message deflate (RFC 7692) would reduce bandwidth.

2. **Implement subprotocol negotiation**: The `Sec-WebSocket-Protocol` header allows protocol negotiation.

3. **Add TLS support**: Production WebSocket servers should use `wss://` (WebSocket Secure).

4. **Implement backpressure**: When clients are slow readers, the server should buffer or drop messages.

5. **Add metrics**: Connection count, message rate, latency would be useful for monitoring.

## Next Steps

To extend this project:
1. Add TLS support for `wss://` connections
2. Implement WebSocket compression (per-message deflate)
3. Add authentication middleware
4. Implement rate limiting per connection
5. Add Prometheus metrics
6. Create a load testing tool

## Resources That Helped

1. **RFC 6455**: The definitive WebSocket specification. Essential reading.
2. **MDN WebSocket API**: Excellent browser-side reference.
3. **Go standard library**: `net/http`, `encoding/binary`, `crypto/sha1`, `sync` packages.
4. **gorilla/websocket**: Studied for design patterns (not used as dependency).

# WebSocket Server Research

## What is WebSocket?

WebSocket is a communication protocol that provides full-duplex communication channels over a single TCP connection. It was standardized by the IETF as RFC 6455 in 2011 and is supported by all modern browsers.

## How WebSocket Works

### Connection Flow

1. Client sends HTTP request with `Upgrade: websocket` header
2. Server responds with `101 Switching Protocols`
3. Both sides can now send messages at any time
4. Either side can close the connection with a close frame

```
Client                     Server
  |                          |
  |--- HTTP Upgrade -------->|
  |<-- 101 Switching --------|
  |                          |
  |<====== WebSocket ========>|
  |      (full-duplex)       |
```

### Key Differences from HTTP

| Feature | HTTP | WebSocket |
|---------|------|-----------|
| Direction | Request-Response | Full-Duplex |
| Connection | Short-lived | Persistent |
| Overhead | Headers each request | Minimal after handshake |
| Use Case | REST APIs, web pages | Real-time apps, chat, games |

## WebSocket Protocol Details

### Handshake (RFC 6455 Section 4)

Client sends:
```http
GET /chat HTTP/1.1
Host: server.example.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Protocol: chat, superchat
Sec-WebSocket-Version: 13
Origin: http://example.com
```

Server responds:
```http
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
Sec-WebSocket-Protocol: chat
```

### Sec-WebSocket-Key Calculation

1. Client generates 16-byte random value, base64-encodes it
2. Server concatenates key with magic GUID: `258EAFA5-E914-47DA-95CA-C5AB0DC85B11`
3. Server SHA-1 hashes the result
4. Server base64-encodes the hash

```
Accept = base64(SHA1(Key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"))
```

### Frame Format

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-------+-+-------------+-------------------------------+
|F|R|R|R| opcode|M| Payload len |    Extended payload length    |
|I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
|N|V|V|V|       |S|             |   (if payload len==126/127)   |
| |1|2|3|       |K|             |                               |
+-+-+-+-+-------+-+-------------+-------------------------------+
|     Extended payload length continued, if payload len == 127  |
+-------------------------------+-------------------------------+
|                               |Masking-key, if MASK set to 1  |
+-------------------------------+-------------------------------+
| Masking-key (continued)       |          Payload Data         |
+-------------------------------+-------------------------------+
```

### Frame Opcodes

| Opcode | Type | Description |
|--------|------|-------------|
| 0x0 | Continuation | Fragment continuation |
| 0x1 | Text | UTF-8 text data |
| 0x2 | Binary | Binary data |
| 0x8 | Close | Connection close |
| 0x9 | Ping | Heartbeat request |
| 0xA | Pong | Heartbeat response |
| 0xB-0xF | Reserved | Reserved for future use |

### Payload Length Encoding

- **0-125**: Length is the value itself
- **126**: Next 2 bytes are the length (16-bit unsigned, big-endian)
- **127**: Next 8 bytes are the length (64-bit unsigned, big-endian)

### Masking

Client-to-server frames MUST be masked:
- 4-byte masking key included in frame
- Each payload byte XORed with mask byte: `payload[i] ^= mask[i % 4]`

Server-to-client frames MUST NOT be masked.

Purpose: Prevents cache poisoning attacks on intermediary proxies.

## WebSocket vs Other Real-Time Technologies

| Technology | Protocol | Direction | Overhead | Browser Support |
|------------|----------|-----------|----------|-----------------|
| WebSocket | WS/WSS | Full-Duplex | Low | All modern |
| Server-Sent Events | HTTP | Server->Client | Medium | All modern |
| Long Polling | HTTP | Pseudo-duplex | High | All |
| WebRTC | UDP | Full-Duplex | Low | Most modern |

## Use Cases

### Real-Time Applications

1. **Chat applications**: Instant message delivery
2. **Live dashboards**: Real-time data updates
3. **Multiplayer games**: Low-latency player synchronization
4. **Collaborative editing**: Google Docs-style editing
5. **Financial tickers**: Live stock prices
6. **IoT telemetry**: Device status updates
7. **Notifications**: Push notifications

### When NOT to Use WebSocket

- Simple request-response APIs (use HTTP)
- Infrequent updates (use SSE or polling)
- Large file transfers (use HTTP)
- Unidirectional server push (use SSE)

## Security Considerations

1. **Origin checking**: Validate `Origin` header to prevent CSWSH (Cross-Site WebSocket Hijacking)
2. **Input validation**: Sanitize all incoming messages
3. **Rate limiting**: Prevent abuse from malicious clients
4. **Message size limits**: Prevent memory exhaustion attacks
5. **Authentication**: Implement during HTTP upgrade or via messages
6. **TLS**: Use `wss://` in production for encryption

## Browser Support

WebSocket is supported in all modern browsers:
- Chrome 16+
- Firefox 11+
- Safari 7+
- Edge 12+
- iOS Safari 7+
- Android Browser 4.4+

## Tools for Testing

- **websocat**: Command-line WebSocket client
- **wscat**: Node.js WebSocket client
- **Postman**: GUI WebSocket client
- **Browser DevTools**: Network tab shows WebSocket frames
- **Wireshark**: Packet capture and analysis

## RFCs to Read

- [RFC 6455](https://tools.ietf.org/html/rfc6455): The WebSocket Protocol
- [RFC 7692](https://tools.ietf.org/html/rfc7692): Compression Extensions for WebSocket
- [RFC 8441](https://tools.ietf.org/html/rfc8441): Bootstrapping WebSockets with HTTP/2

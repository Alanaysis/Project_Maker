# HTTP/2 Server

A Go implementation of an HTTP/2 server that demonstrates multiplexing, header compression, and flow control.

## Overview

This project implements a minimal HTTP/2 server from scratch, focusing on understanding the core concepts of the HTTP/2 protocol:

- **Frame Parsing**: Reading and writing HTTP/2 frames
- **HPACK Header Compression**: Efficient header encoding/decoding
- **Stream Multiplexing**: Multiple streams on a single connection
- **Flow Control**: Window-based flow control mechanism

## Features

- HTTP/2 frame parsing and serialization
- HPACK header compression (static and dynamic tables)
- Stream multiplexing with round-robin scheduling
- Flow control with window updates
- TLS support (required for HTTP/2)
- Built-in request router
- Example endpoints

## Project Structure

```
http2-server/
├── cmd/
│   ├── server/         # Server entry point
│   └── client/         # Client for testing
├── internal/
│   ├── frame/          # HTTP/2 frame parsing
│   │   ├── frame.go    # Frame read/write
│   │   ├── settings.go # Settings frame
│   │   ├── hpack.go    # HPACK compression
│   │   └── frames_test.go
│   ├── connection/     # Connection management
│   │   ├── connection.go     # Connection handling
│   │   ├── multiplexer.go    # Stream multiplexing
│   │   └── connection_test.go
│   └── handler/        # Request handling
│       └── handler.go  # Router and handlers
├── docs/               # Documentation
├── examples/           # Usage examples
├── go.mod
└── README.md
```

## Quick Start

### Prerequisites

- Go 1.21 or later
- OpenSSL (for generating certificates)

### Generate TLS Certificate

```bash
# Generate self-signed certificate for testing
openssl req -x509 -newkey rsa:2048 -keyout server.key -out server.crt -days 365 -nodes -subj "/CN=localhost"
```

### Build and Run

```bash
# Build the server
go build -o server ./cmd/server

# Run the server
./server -addr :8443 -cert server.crt -key server.key
```

### Test with Client

```bash
# Build the client
go build -o client ./cmd/client

# Run the client
./client -addr localhost:8443 -skip-verify
```

## API Endpoints

### GET /
Returns a welcome HTML page.

### GET /health
Health check endpoint.
```json
{"status": "healthy", "version": "1.0.0"}
```

### GET /info
Server information.
```json
{
  "protocol": "HTTP/2",
  "features": ["multiplexing", "header_compression", "flow_control", "server_push"],
  "streams": {
    "max_concurrent": 100,
    "initial_window_size": 65535
  }
}
```

### POST /echo
Echoes back the request body.

## HTTP/2 Concepts

### Frames
HTTP/2 communication is based on frames. Each frame has:
- Length (24 bits)
- Type (8 bits)
- Flags (8 bits)
- Stream ID (31 bits)
- Payload

### Stream Multiplexing
Multiple streams can share a single connection. Frames from different streams can be interleaved, allowing concurrent request/response handling without head-of-line blocking.

### HPACK Header Compression
Headers are compressed using:
1. **Static Table**: Pre-defined common headers
2. **Dynamic Table**: Learned from previous requests
3. **Huffman Coding**: Efficient encoding of header values

### Flow Control
Window-based flow control prevents overwhelming receivers:
- Connection-level window
- Stream-level windows
- WINDOW_UPDATE frames

## Running Tests

```bash
# Run all tests
go test ./...

# Run specific package tests
go test ./internal/frame/...
go test ./internal/connection/...

# Run with verbose output
go test -v ./...
```

## Learning Resources

- [RFC 7540 - HTTP/2](https://tools.ietf.org/html/rfc7540)
- [RFC 7541 - HPACK](https://tools.ietf.org/html/rfc7541)
- [HTTP/2 Specification](https://httpwg.org/specs/rfc7540.html)

## License

This project is for educational purposes.

## Contributing

This is a learning project. Feel free to experiment and extend it!

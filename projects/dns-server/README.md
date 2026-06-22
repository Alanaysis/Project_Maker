# DNS Server

A simple DNS server implementation in Go, built for learning DNS protocol internals.

## Overview

This project implements a working DNS server that can:
- Parse and serialize DNS messages (RFC 1035 compliant)
- Resolve domain names via upstream DNS servers
- Cache DNS responses with TTL-based expiration
- Serve local zone records authoritatively

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    DNS Server                            │
│                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────┐  │
│  │  UDP      │───▶│ Protocol │───▶│    Resolver      │  │
│  │  Listener │    │ Parser   │    │  ┌────────────┐  │  │
│  └──────────┘    └──────────┘    │  │ Local Zones│  │  │
│                                  │  └────────────┘  │  │
│  ┌──────────┐                    │  ┌────────────┐  │  │
│  │  Cache   │◀───────────────────│  │  Upstream  │  │  │
│  │  Layer   │                    │  │  (8.8.8.8) │  │  │
│  └──────────┘                    │  └────────────┘  │  │
│                                  └──────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Project Structure

```
dns-server/
├── cmd/
│   └── server/
│       └── main.go          # Entry point
├── internal/
│   ├── protocol/
│   │   ├── message.go       # DNS message parsing/serialization
│   │   └── message_test.go  # Protocol tests
│   ├── cache/
│   │   ├── cache.go         # DNS cache with TTL
│   │   └── cache_test.go    # Cache tests
│   ├── resolver/
│   │   ├── resolver.go      # Name resolution logic
│   │   └── resolver_test.go # Resolver tests
│   └── server/
│       ├── server.go        # UDP server implementation
│       └── server_test.go   # Server tests
├── docs/                    # Documentation
├── go.mod                   # Go module file
├── README.md                # This file
└── LEARNING_NOTES.md        # Learning notes
```

## Quick Start

### Prerequisites

- Go 1.21 or later

### Build and Run

```bash
# Build
go build -o dns-server ./cmd/server

# Run (default: listen on :5353, upstream 8.8.8.8:53)
./dns-server

# Run with custom options
./dns-server -addr ":5353" -upstream "8.8.4.4:53" -cache 2048
```

### Test with dig

```bash
# Query the local server
dig @127.0.0.1 -p 5353 example.com A

# Query local zone records
dig @127.0.0.1 -p 5353 localhost.dns A
dig @127.0.0.1 -p 5353 test.local A
```

### Run Tests

```bash
# Run all tests
go test ./...

# Run tests with verbose output
go test ./... -v

# Run tests for a specific package
go test ./internal/protocol -v
```

## Command Line Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-addr` | `:5353` | UDP address to listen on |
| `-upstream` | `8.8.8.8:53` | Upstream DNS server address |
| `-cache` | `1024` | Maximum number of cache entries |

## DNS Protocol

### Message Format

```
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                      ID                           |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|QR|   Opcode  |AA|TC|RD| RA|   Z    |   RCODE    |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                    QDCOUNT                         |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                    ANCOUNT                         |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                    NSCOUNT                         |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                    ARCOUNT                         |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
```

### Supported Record Types

| Type | Code | Description |
|------|------|-------------|
| A | 1 | IPv4 address |
| AAAA | 28 | IPv6 address |
| CNAME | 5 | Canonical name |
| MX | 15 | Mail exchange |
| NS | 2 | Name server |
| TXT | 16 | Text record |
| SOA | 6 | Start of authority |

## Key Concepts

### DNS Resolution Flow

1. Client sends query to DNS server
2. Server checks local zone records (authoritative)
3. If not found, checks cache
4. If cache miss, forwards to upstream DNS server
5. Caches the response with appropriate TTL
6. Returns response to client

### DNS Cache

- Thread-safe with `sync.RWMutex`
- TTL-based expiration (minimum 30 seconds)
- Lazy eviction on access
- Periodic cleanup of expired entries
- Configurable maximum size

### Domain Name Encoding

DNS uses a specific wire format for domain names:
- Each label is prefixed with its length
- Labels are terminated with a zero byte
- Example: `www.example.com` = `\x03www\x07example\x03com\x00`

## Learning Resources

- [RFC 1035](https://tools.ietf.org/html/rfc1035) - Domain Names - Implementation and Specification
- [RFC 1034](https://tools.ietf.org/html/rfc1034) - Domain Names - Concepts and Facilities
- [DNS in One Picture](https://github.com/AdrianGafo/DNS-in-one-picture)

## License

This project is for educational purposes.

---

[返回 NLP 模块](../NLP_README.md) | [返回主目录](../../README.md)

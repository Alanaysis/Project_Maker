# DNS Server Design

## Goals

1. Learn DNS protocol internals
2. Implement a working DNS server
3. Support DNS caching
4. Keep code clean and testable

## Architecture

### Component Overview

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

### Package Structure

```
internal/
├── protocol/      # DNS message parsing/serialization
├── cache/         # DNS cache with TTL
├── resolver/      # Name resolution logic
└── server/        # UDP server implementation
```

## Protocol Package

### Responsibilities
- Parse DNS messages from bytes
- Serialize DNS messages to bytes
- Handle domain name encoding/decoding
- Handle compression pointers

### Key Types

```go
type Header struct {
    ID      uint16
    QR      uint8
    Opcode  uint8
    AA      bool
    TC      bool
    RD      bool
    RA      bool
    Z       uint8
    RCODE   uint8
    QDCount uint16
    ANCount uint16
    NSCount uint16
    ARCount uint16
}

type Question struct {
    Name  string
    Type  uint16
    Class uint16
}

type ResourceRecord struct {
    Name   string
    Type   uint16
    Class  uint16
    TTL    uint32
    RDLen  uint16
    RData  []byte
}

type Message struct {
    Header     Header
    Question   []Question
    Answer     []ResourceRecord
    Authority  []ResourceRecord
    Additional []ResourceRecord
}
```

### Design Decisions

1. **Separate Pack/Unpack**: Clear separation between parsing and serialization
2. **Immutable after parse**: Parsed messages should not be modified
3. **Compression support**: Handle pointers in parsing, avoid in serialization (simpler)

## Cache Package

### Responsibilities
- Store DNS records with TTL
- Thread-safe access
- TTL-based expiration
- Size-based eviction

### Design

```go
type Cache struct {
    mu      sync.RWMutex
    entries map[string]*Entry
    maxSize int
    stats   Stats
}

type Entry struct {
    Records   []ResourceRecord
    ExpiresAt time.Time
}
```

### Design Decisions

1. **RWMutex**: Read-heavy workload benefits from RWMutex
2. **Lazy eviction**: Evict on access, not background goroutine
3. **Key format**: `domain:type` to distinguish A vs AAAA
4. **Minimum TTL**: 30 seconds to prevent cache thrashing

## Resolver Package

### Responsibilities
- Check local zone records
- Forward to upstream DNS
- Build responses

### Design

```go
type Resolver struct {
    upstream string
    zones    map[string][]ResourceRecord
    timeout  time.Duration
}
```

### Design Decisions

1. **Local zones first**: Check authoritative records before forwarding
2. **Functional options**: Clean configuration API
3. **Timeout handling**: 5 second timeout for upstream queries

## Server Package

### Responsibilities
- Listen for UDP queries
- Parse incoming messages
- Resolve queries (with cache)
- Send responses

### Design

```go
type Server struct {
    addr     string
    conn     *net.UDPConn
    resolver *resolver.Resolver
    cache    *cache.Cache
    stopCh   chan struct{}
}
```

### Design Decisions

1. **Goroutine per query**: Handle concurrent queries
2. **Graceful shutdown**: Use channel to signal stop
3. **Read deadline**: Allow periodic stop checks

## Request Flow

```
1. Receive UDP packet
2. Parse DNS message (protocol.Unpack)
3. Validate: Is it a query? (QR == 0)
4. For each question:
   a. Check cache
   b. If cache miss, resolve via resolver
   c. Cache the result
5. Build response message
6. Serialize and send
```

## Error Handling

### Protocol Errors
- Malformed message: Log and drop
- Too short: Log and drop
- Compression loop: Return SERVFAIL

### Resolution Errors
- Upstream timeout: Return SERVFAIL
- NXDOMAIN: Return NXDOMAIN
- Format error: Return FORMERR

## Testing Strategy

### Unit Tests
- Protocol parsing/serialization
- Cache operations
- Resolver logic

### Integration Tests
- Full query resolution
- Cache hit/miss scenarios
- Concurrent access

### What We Don't Test
- Network I/O (mocked in unit tests)
- Real DNS queries (tested manually with dig)

## Future Improvements

1. **TCP support**: For responses > 512 bytes
2. **EDNS**: Extension mechanisms for larger payloads
3. **DNSSEC**: Security extensions
4. **Metrics**: Cache hit rate, query latency
5. **Zone file parsing**: Load zones from files

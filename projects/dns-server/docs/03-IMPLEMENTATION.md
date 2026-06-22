# DNS Server Implementation

## Overview

This document describes the implementation details of the DNS server.

## Protocol Implementation

### Parsing DNS Messages

The `Unpack` function parses raw bytes into a `Message`:

```go
func Unpack(data []byte) (*Message, error) {
    // 1. Parse header (fixed 12 bytes)
    header, err := UnpackHeader(data)

    // 2. Parse questions (variable length)
    questions, offset, err := unpackQuestions(data, offset, header.QDCount)

    // 3. Parse answers
    answers, offset, err := unpackResourceRecords(data, offset, header.ANCount)

    // 4. Parse authority
    authority, offset, err := unpackResourceRecords(data, offset, header.NSCount)

    // 5. Parse additional
    additional, _, err := unpackResourceRecords(data, offset, header.ARCount)

    return &Message{...}, nil
}
```

### Domain Name Parsing

Domain names use a special encoding with length-prefixed labels:

```go
func unpackDomainName(data []byte, offset int) (string, int, error) {
    var name []byte

    for {
        length := data[offset]

        // Compression pointer (top 2 bits = 11)
        if length&0xC0 == 0xC0 {
            pointer := int(binary.BigEndian.Uint16(data[offset:offset+2]) & 0x3FFF)
            offset = pointer
            continue
        }

        // End of name
        if length == 0 {
            break
        }

        // Normal label
        offset++
        name = append(name, data[offset:offset+int(length)]...)
        offset += int(length)
    }

    return string(name), offset, nil
}
```

### Compression Pointers

Compression pointers reuse domain name parts:
- Top 2 bits = 11 indicate a pointer
- Remaining 14 bits = offset into message
- Prevent infinite loops with jump counter

```go
if length&0xC0 == 0xC0 {
    pointer := int(binary.BigEndian.Uint16(data[offset:offset+2]) & 0x3FFF)
    if pointer >= offset {
        return "", 0, ErrCompressionLoop
    }
    offset = pointer
    jumps++
    if jumps > maxJumps {
        return "", 0, ErrCompressionLoop
    }
    continue
}
```

## Cache Implementation

### Thread-Safe Access

```go
type Cache struct {
    mu      sync.RWMutex
    entries map[string]*Entry
}

func (c *Cache) Get(name string, qtype uint16) ([]ResourceRecord, bool) {
    c.mu.RLock()
    defer c.mu.RUnlock()

    entry, exists := c.entries[key]
    if !exists {
        return nil, false
    }

    if entry.IsExpired() {
        return nil, false
    }

    return entry.Records, true
}
```

### TTL Handling

```go
func (c *Cache) Set(name string, qtype uint16, records []ResourceRecord) {
    // Use minimum TTL across all records
    var minTTL uint32 = 0xFFFFFFFF
    for _, rr := range records {
        if rr.TTL < minTTL {
            minTTL = rr.TTL
        }
    }

    // Minimum 30 seconds to prevent cache thrashing
    if minTTL < 30 {
        minTTL = 30
    }

    entry := &Entry{
        Records:   records,
        ExpiresAt: time.Now().Add(time.Duration(minTTL) * time.Second),
    }

    c.mu.Lock()
    c.entries[key] = entry
    c.mu.Unlock()
}
```

## Resolver Implementation

### Resolution Strategy

```go
func (r *Resolver) Resolve(q Question) ([]ResourceRecord, uint8) {
    // 1. Check local zones
    if records, ok := r.zones[q.Name]; ok {
        // Filter by type
        var matched []ResourceRecord
        for _, rr := range records {
            if rr.Type == q.Type {
                matched = append(matched, rr)
            }
        }
        if len(matched) > 0 {
            return matched, RcodeNoError
        }
    }

    // 2. Forward to upstream
    records, rcode := r.forwardToUpstream(q)
    return records, rcode
}
```

### Upstream Forwarding

```go
func (r *Resolver) forwardToUpstream(q Question) ([]ResourceRecord, uint8) {
    // Build query
    query := &Message{
        Header: Header{
            ID:      generateID(),
            QR:      QRQuery,
            RD:      true,
            QDCount: 1,
        },
        Question: []Question{q},
    }

    // Send via UDP
    conn, err := net.DialTimeout("udp", r.upstream, r.timeout)
    conn.Write(queryData)

    // Read response
    buf := make([]byte, MaxUDPPayloadSize)
    n, err := conn.Read(buf)

    // Parse response
    resp, err := Unpack(buf[:n])
    return resp.Answer, resp.Header.RCODE
}
```

## Server Implementation

### Main Loop

```go
func (s *Server) Start() error {
    addr, _ := net.ResolveUDPAddr("udp", s.addr)
    s.conn, _ = net.ListenUDP("udp", addr)

    for {
        select {
        case <-s.stopCh:
            return nil
        default:
        }

        // Read with deadline for stop checks
        s.conn.SetReadDeadline(time.Now().Add(1 * time.Second))
        n, remoteAddr, err := s.conn.ReadFromUDP(buf)

        // Handle in goroutine
        go s.handleQuery(buf[:n], remoteAddr)
    }
}
```

### Query Handling

```go
func (s *Server) handleQuery(data []byte, remoteAddr *net.UDPAddr) {
    // Parse query
    query, err := Unpack(data)

    // Build response
    response := &Message{
        Header: Header{
            ID:      query.Header.ID,
            QR:      QRResponse,
            RA:      true,
        },
        Question: query.Question,
    }

    // Resolve each question
    for _, q := range query.Question {
        answers, rcode := s.resolveWithCache(q)
        response.Answer = append(response.Answer, answers...)
    }

    // Send response
    respData, _ := response.Pack()
    s.conn.WriteToUDP(respData, remoteAddr)
}
```

### Cache Integration

```go
func (s *Server) resolveWithCache(q Question) ([]ResourceRecord, uint8) {
    // Check cache
    if cached, found := s.cache.Get(q.Name, q.Type); found {
        return cached, RcodeNoError
    }

    // Resolve via upstream
    records, rcode := s.resolver.Resolve(q)

    // Cache result
    if rcode == RcodeNoError && len(records) > 0 {
        s.cache.Set(q.Name, q.Type, records)
    }

    return records, rcode
}
```

## Testing

### Unit Tests

Each package has comprehensive tests:
- `protocol_test.go`: Parsing, serialization, compression
- `cache_test.go`: TTL, eviction, concurrency
- `resolver_test.go`: Local zones, upstream forwarding
- `server_test.go`: Integration, cache hit/miss

### Running Tests

```bash
# All tests
go test ./...

# Verbose
go test ./... -v

# Specific package
go test ./internal/protocol -v

# With coverage
go test ./... -cover
```

## Performance Considerations

1. **Goroutine per query**: Good for I/O-bound work
2. **RWMutex**: Allows concurrent reads
3. **Buffer pooling**: Reuse buffers (not implemented)
4. **Lazy eviction**: Minimal background work

## Known Limitations

1. **UDP only**: No TCP support
2. **512 byte limit**: No EDNS support
3. **No recursion**: Forwards to upstream, doesn't iterate
4. **No DNSSEC**: No security extensions

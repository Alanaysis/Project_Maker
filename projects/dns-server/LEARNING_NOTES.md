# Learning Notes - DNS Server Implementation

## What I Learned

### 1. DNS Protocol Fundamentals

DNS (Domain Name System) is a hierarchical, decentralized naming system for computers, services, or other resources connected to the Internet or a private network. It translates human-readable domain names (like `www.example.com`) into numerical IP addresses (like `93.184.216.34`).

**Key Takeaway**: DNS is essentially a distributed database that maps names to values. The "distributed" part is key -- no single server knows everything.

### 2. DNS Message Format

The DNS message format is defined in RFC 1035 and has a fixed 12-byte header followed by variable-length sections:

```
Header (12 bytes)
├── ID (16 bits): Transaction identifier
├── Flags (16 bits): QR, OPCODE, AA, TC, RD, RA, Z, RCODE
├── QDCOUNT (16 bits): Number of questions
├── ANCOUNT (16 bits): Number of answers
├── NSCOUNT (16 bits): Number of authority records
└── ARCOUNT (16 bits): Number of additional records

Question Section
├── Name: Domain name (variable length)
├── Type: Record type (A, AAAA, CNAME, etc.)
└── Class: Record class (usually IN=1)

Answer/Authority/Additional Sections
├── Name: Domain name
├── Type: Record type
├── Class: Record class
├── TTL: Time to live (seconds)
├── RDLength: Length of RDATA
└── RDATA: Record data
```

**Key Takeaway**: The header is always 12 bytes. Everything after is variable length and must be parsed carefully.

### 3. Domain Name Encoding

Domain names in DNS messages use a special encoding:
- Each label is prefixed with its length (1 byte)
- Labels are separated by their length, not by dots
- The name is terminated with a zero byte

Example: `www.example.com` becomes:
```
\x03www\x07example\x03com\x00
```

**Key Takeaway**: The encoding is efficient but requires careful parsing. Off-by-one errors are common.

### 4. DNS Compression (RFC 1035 Section 4.1.4)

DNS uses compression pointers to reduce message size:
- Top 2 bits of a byte indicate if it's a pointer (11xxxxxx)
- Remaining 14 bits are an offset into the message
- Allows reuse of domain name suffixes

Example: If `mail.example.com` appears after `www.example.com`, the `example.com` part can be replaced with a pointer to where it first appeared.

**Key Takeaway**: Compression is optional but important for efficiency. Must handle it correctly to parse real DNS messages.

### 5. UDP Transport

DNS primarily uses UDP (User Datagram Protocol) on port 53:
- Simple request/response model
- No connection setup overhead
- Maximum payload 512 bytes (without EDNS)
- TCP fallback for larger messages

**Key Takeaway**: UDP is connectionless, so each query is independent. This simplifies the server but means we can't rely on TCP's reliability.

### 6. DNS Caching

Caching is crucial for DNS performance:
- Reduces upstream queries
- Decreases latency for repeated lookups
- TTL (Time To Live) controls cache duration
- Minimum TTL of 30 seconds prevents cache thrashing

**Key Takeaway**: Cache invalidation is hard. TTL-based expiration is simple but effective.

### 7. Concurrency in Go

The server uses goroutines to handle multiple queries concurrently:
- Each query is handled in its own goroutine
- Cache uses `sync.RWMutex` for thread-safe access
- Read-heavy workload benefits from RWMutex vs Mutex

**Key Takeaway**: Go's goroutines make concurrent programming straightforward. The RWMutex pattern is essential for shared data structures.

### 8. Error Handling

DNS has specific error codes (RCODE):
- 0: No error
- 1: Format error
- 2: Server failure
- 3: Non-existent domain (NXDOMAIN)
- 4: Not implemented
- 5: Query refused

**Key Takeaway**: Proper error handling is critical. Return meaningful error codes to clients.

## Challenges Faced

### 1. Parsing Domain Names with Compression

The most complex part was implementing domain name parsing with compression pointers. The algorithm needs to:
- Handle normal labels
- Detect compression pointers (top 2 bits = 11)
- Follow pointers to earlier positions in the message
- Prevent infinite loops from malformed messages

**Solution**: Added a jump counter with a maximum limit (10 jumps) to prevent infinite loops.

### 2. Byte Order

DNS uses big-endian (network byte order) for multi-byte values. Go's `encoding/binary` package provides `BigEndian` for this.

**Solution**: Consistently use `binary.BigEndian.Uint16()` and `binary.BigEndian.PutUint16()`.

### 3. Buffer Management

Building DNS messages requires careful buffer management:
- Pre-allocate buffers when possible
- Use `append()` for dynamic growth
- Be careful with slice references

**Solution**: Use `make([]byte, 0, 512)` for initial allocation and `append()` for growth.

## Design Decisions

### 1. Package Structure

I chose to organize the code into focused packages:
- `protocol`: DNS message parsing/serialization
- `cache`: Caching layer
- `resolver`: Name resolution logic
- `server`: UDP server implementation

This separation makes the code easier to understand and test.

### 2. Functional Options Pattern

Used functional options for configuration:
```go
type Option func(*Cache)

func WithMaxSize(size int) Option {
    return func(c *Cache) {
        c.maxSize = size
    }
}
```

This provides a clean API with sensible defaults.

### 3. Lazy Cache Eviction

Instead of actively monitoring TTLs, the cache evicts entries on access:
- Reduces background work
- Simpler implementation
- Combined with periodic cleanup for memory reclamation

## What I Would Do Differently

1. **Use `encoding/binary` more**: Initially tried manual byte manipulation, but `encoding/binary` is cleaner.

2. **Add more comprehensive tests**: The tests cover the basics but could include more edge cases.

3. **Implement EDNS**: EDNS (Extension mechanisms for DNS) allows larger UDP payloads and is widely used.

4. **Add metrics**: Cache hit rate, query latency, etc. would be useful for production.

5. **Support TCP**: Currently only UDP. TCP is needed for responses > 512 bytes.

## Next Steps

To extend this project:
1. Add TCP support for large responses
2. Implement recursive resolution (iterative queries to root servers)
3. Add DNSSEC validation
4. Implement zone file parsing
5. Add Prometheus metrics
6. Create a web UI for monitoring

## Resources That Helped

1. **RFC 1035**: The definitive DNS specification. Essential reading.
2. **Wireshark**: Capturing real DNS traffic helped understand the protocol.
3. **Go standard library**: `net`, `encoding/binary`, `sync` packages.
4. **Existing DNS servers**: Studying `dnsmasq` and `coredns` for design patterns.

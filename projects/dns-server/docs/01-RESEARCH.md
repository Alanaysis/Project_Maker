# DNS Server Research

## What is DNS?

DNS (Domain Name System) is a hierarchical, decentralized naming system for computers, services, or other resources connected to the Internet or a private network. It translates human-readable domain names into numerical IP addresses.

## How DNS Works

### Basic Flow

1. User types `www.example.com` in browser
2. Browser checks local cache
3. If not cached, queries recursive resolver (ISP or 8.8.8.8)
4. Resolver checks its cache
5. If not cached, resolver queries root servers
6. Root servers direct to TLD servers (.com, .org, etc.)
7. TLD servers direct to authoritative nameserver
8. Authoritative nameserver returns IP address
9. Resolver caches and returns to client

### DNS Hierarchy

```
Root Servers (13 worldwide)
├── .com TLD
│   ├── example.com
│   ├── google.com
│   └── ...
├── .org TLD
├── .net TLD
└── ...
```

## DNS Protocol Details

### Message Format (RFC 1035)

DNS messages have a fixed 12-byte header:

```
                                1  1  1  1  1  1
  0  1  2  3  4  5  6  7  8  9  0  1  2  3  4  5
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

### Header Fields

- **ID**: 16-bit transaction identifier
- **QR**: Query (0) or Response (1)
- **Opcode**: Operation code (0=Query, 1=Inverse Query, 2=Status)
- **AA**: Authoritative Answer
- **TC**: Truncation (message too large for UDP)
- **RD**: Recursion Desired
- **RA**: Recursion Available
- **Z**: Reserved (must be zero)
- **RCODE**: Response code (0=No Error, 3=NXDOMAIN, etc.)

### Domain Name Encoding

Domain names are encoded as a sequence of labels:
- Each label prefixed with length (1 byte)
- Terminated with zero byte
- Example: `www.example.com` = `\x03www\x07example\x03com\x00`

### DNS Compression

Compression pointers save space by reusing domain name parts:
- Top 2 bits = 11 indicates a pointer
- Remaining 14 bits = offset into message
- Allows reusing suffixes (e.g., `example.com`)

## Record Types

| Type | Code | Purpose |
|------|------|---------|
| A | 1 | IPv4 address |
| AAAA | 28 | IPv6 address |
| CNAME | 5 | Canonical name (alias) |
| MX | 15 | Mail exchange |
| NS | 2 | Nameserver |
| TXT | 16 | Text record |
| SOA | 6 | Start of authority |
| PTR | 12 | Pointer (reverse DNS) |

## UDP vs TCP

- **UDP**: Default, port 53, max 512 bytes (without EDNS)
- **TCP**: Fallback for large responses, zone transfers

## Caching

### TTL (Time to Live)

- Specified in each resource record (seconds)
- Controls how long to cache
- Typical values: 300 (5 min) to 86400 (24 hours)

### Cache Strategies

1. **TTL-based expiration**: Simple, effective
2. **LRU eviction**: Remove least recently used
3. **Size-based limits**: Prevent memory exhaustion

## Security Considerations

1. **DNS Spoofing**: Attacker sends fake responses
2. **Cache Poisoning**: Corrupting cached entries
3. **DDoS**: Amplification attacks using open resolvers

## Tools for Testing

- `dig`: Command-line DNS lookup tool
- `nslookup`: DNS lookup utility
- `wireshark`: Packet capture and analysis
- `tcpdump`: Command-line packet capture

## RFCs to Read

- [RFC 1034](https://tools.ietf.org/html/rfc1034): Domain Names - Concepts and Facilities
- [RFC 1035](https://tools.ietf.org/html/rfc1035): Domain Names - Implementation and Specification
- [RFC 2181](https://tools.ietf.org/html/rfc2181): Clarifications to the DNS Specification
- [RFC 2308](https://tools.ietf.org/html/rfc2308): Negative Caching of DNS Queries

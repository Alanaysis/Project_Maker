# DNS Server Testing

## Test Strategy

### Unit Tests

Each package has focused unit tests:

1. **Protocol Tests**: Parsing, serialization, compression
2. **Cache Tests**: TTL, eviction, concurrency
3. **Resolver Tests**: Local zones, upstream forwarding
4. **Server Tests**: Integration, cache hit/miss

### Integration Tests

End-to-end tests that verify the full pipeline:
- Query parsing -> Cache lookup -> Resolution -> Response

## Running Tests

### All Tests

```bash
go test ./...
```

### Verbose Output

```bash
go test ./... -v
```

### Specific Package

```bash
go test ./internal/protocol -v
go test ./internal/cache -v
go test ./internal/resolver -v
go test ./internal/server -v
```

### With Coverage

```bash
go test ./... -cover
```

### Race Detection

```bash
go test ./... -race
```

## Test Cases

### Protocol Tests

#### Header Pack/Unpack

```go
func TestHeaderPackUnpack(t *testing.T) {
    original := Header{
        ID:      0xABCD,
        QR:      QRResponse,
        Opcode:  OpcodeQuery,
        AA:      true,
        RD:      true,
        RA:      true,
        QDCount: 1,
        ANCount: 2,
    }

    packed := original.Pack()
    parsed, _ := UnpackHeader(packed)

    // Verify all fields match
    assertEqual(t, "ID", original.ID, parsed.ID)
    assertEqual(t, "QR", original.QR, parsed.QR)
    // ... more assertions
}
```

#### Domain Name Encoding

```go
func TestPackDomainName(t *testing.T) {
    tests := []struct {
        name     string
        expected []byte
    }{
        {"www.example.com", []byte("\x03www\x07example\x03com\x00")},
        {"example.com", []byte("\x07example\x03com\x00")},
        {".", []byte{0}},
    }

    for _, tt := range tests {
        result := packDomainName(tt.name)
        // Verify bytes match
    }
}
```

#### Compression Pointers

```go
func TestCompressionPointer(t *testing.T) {
    // Build message with compression:
    // Question: www.example.com
    // Answer: mail.example.com -> pointer to offset 16

    data := make([]byte, 12) // Header
    // ... build message with compression

    msg, err := Unpack(data)
    // Verify parsing works correctly
}
```

#### Round Trip

```go
func TestRoundTrip(t *testing.T) {
    original := &Message{
        Header: Header{ID: 1234, QR: QRResponse, RD: true, RA: true},
        Question: []Question{{Name: "example.com", Type: TypeA}},
        Answer: []ResourceRecord{{Name: "example.com", Type: TypeA, TTL: 300}},
    }

    packed, _ := original.Pack()
    parsed, _ := Unpack(packed)

    // Verify all fields match
}
```

### Cache Tests

#### Basic Set/Get

```go
func TestCacheSetGet(t *testing.T) {
    c := New()
    records := []ResourceRecord{{Name: "test.com", Type: TypeA}}

    c.Set("test.com", TypeA, records)
    result, found := c.Get("test.com", TypeA)

    if !found {
        t.Error("expected cache hit")
    }
    if len(result) != 1 {
        t.Errorf("expected 1 record, got %d", len(result))
    }
}
```

#### TTL Expiration

```go
func TestCacheExpiry(t *testing.T) {
    c := New()
    records := []ResourceRecord{{Name: "test.com", Type: TypeA, TTL: 1}}

    c.Set("test.com", TypeA, records)

    // Manually expire
    c.mu.Lock()
    c.entries["test.com:1"].ExpiresAt = time.Now().Add(-1 * time.Second)
    c.mu.Unlock()

    _, found := c.Get("test.com", TypeA)
    if found {
        t.Error("expected cache miss for expired entry")
    }
}
```

#### Max Size Eviction

```go
func TestCacheMaxSize(t *testing.T) {
    c := New(WithMaxSize(3))

    for i := 0; i < 5; i++ {
        records := []ResourceRecord{{RData: []byte{byte(i)}}}
        c.Set("test.com", TypeA, records)
    }

    if c.Size() > 3 {
        t.Errorf("expected cache size <= 3, got %d", c.Size())
    }
}
```

### Resolver Tests

#### Local Zone Lookup

```go
func TestResolverLocalZone(t *testing.T) {
    r := New()
    r.AddARecord("local.test", net.ParseIP("10.0.0.1"))

    q := Question{Name: "local.test", Type: TypeA}
    records, rcode := r.Resolve(q)

    if rcode != RcodeNoError {
        t.Fatalf("expected NOERROR, got %d", rcode)
    }
    if len(records) != 1 {
        t.Fatalf("expected 1 record, got %d", len(records))
    }
}
```

### Server Tests

#### Cache Integration

```go
func TestResolveWithCache(t *testing.T) {
    srv := New(Config{CacheSize: 100})
    srv.Resolver().AddARecord("cached.test", net.ParseIP("10.0.0.1"))

    q := Question{Name: "cached.test", Type: TypeA}

    // First call - cache miss
    records, _ := srv.resolveWithCache(q)

    // Second call - cache hit
    records, _ = srv.resolveWithCache(q)

    stats := srv.Cache().StatsSnapshot()
    if stats.Hits != 1 {
        t.Errorf("expected 1 cache hit, got %d", stats.Hits)
    }
}
```

#### Server Start/Stop

```go
func TestServerStartStop(t *testing.T) {
    srv := New(Config{ListenAddr: ":0"})

    errCh := make(chan error, 1)
    go func() {
        errCh <- srv.Start()
    }()

    time.Sleep(100 * time.Millisecond)
    srv.Stop()

    select {
    case err := <-errCh:
        if err != nil {
            t.Fatalf("server error: %v", err)
        }
    case <-time.After(5 * time.Second):
        t.Fatal("server did not stop")
    }
}
```

## Manual Testing

### Using dig

```bash
# Start server
./dns-server

# Query A record
dig @127.0.0.1 -p 5353 example.com A

# Query local zone
dig @127.0.0.1 -p 5353 localhost.dns A
dig @127.0.0.1 -p 5353 test.local A

# Query with recursion
dig @127.0.0.1 -p 5353 google.com A +norecurse
```

### Using nslookup

```bash
nslookup -port=5353 example.com 127.0.0.1
```

### Packet Capture

```bash
# Capture DNS traffic
sudo tcpdump -i lo -n port 5353

# With wireshark
sudo wireshark -i lo -f "port 5353"
```

## Test Coverage

Run with coverage report:

```bash
go test ./... -coverprofile=coverage.out
go tool cover -html=coverage.out
```

## Continuous Integration

Example GitHub Actions workflow:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-go@v2
        with:
          go-version: 1.21
      - run: go test ./... -race -cover
```

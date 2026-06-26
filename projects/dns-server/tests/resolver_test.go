package dns

import (
	"testing"
)

// TestResolver tests the DNS resolver functionality.
func TestResolverBasic(t *testing.T) {
	forwarder := NewForwarder([]string{"8.8.8.8:53"}, 5)
	resolver := NewResolver(100, 3600, forwarder)

	// Register a zone
	zoneContent := `
$ORIGIN example.com.
$TTL 3600

www     IN  A       93.184.216.34
mail    IN  A       192.168.1.1
`
	zone, _ := ParseZoneFile(zoneContent)
	resolver.AddZone("example.com", zone)

	// Resolve a known name
	resp, err := resolver.Resolve("www.example.com", TypeA)
	if err != nil {
		t.Fatalf("Resolve error: %v", err)
	}

	if resp == nil {
		t.Fatal("Expected non-nil response")
	}

	if len(resp.Answers) == 0 {
		t.Error("Expected at least one answer")
	}
}

// TestResolverCache tests resolver caching behavior.
func TestResolverCache(t *testing.T) {
	forwarder := NewForwarder([]string{"8.8.8.8:53"}, 5)
	resolver := NewResolver(100, 3600, forwarder)

	zoneContent := `
$ORIGIN example.com.
$TTL 3600

www     IN  A       93.184.216.34
`
	zone, _ := ParseZoneFile(zoneContent)
	resolver.AddZone("example.com", zone)

	// First resolution (populates cache)
	resp1, err := resolver.Resolve("www.example.com", TypeA)
	if err != nil || resp1 == nil {
		t.Fatalf("First resolve error: %v", err)
	}

	// Second resolution (should use cache)
	resp2, err := resolver.Resolve("www.example.com", TypeA)
	if err != nil || resp2 == nil {
		t.Fatalf("Second resolve error: %v", err)
	}

	// Cache should have an entry
	if resolver.Cache().Size() == 0 {
		t.Error("Expected cached entry")
	}
}

// TestResolverNXDomain tests NXDOMAIN response.
func TestResolverNXDomain(t *testing.T) {
	forwarder := NewForwarder([]string{"8.8.8.8:53"}, 5)
	resolver := NewResolver(100, 3600, forwarder)

	zoneContent := `
$ORIGIN example.com.
$TTL 3600

www     IN  A       93.184.216.34
`
	zone, _ := ParseZoneFile(zoneContent)
	resolver.AddZone("example.com", zone)

	resp, err := resolver.Resolve("nonexistent.example.com", TypeA)
	if err != nil {
		t.Fatalf("Resolve error: %v", err)
	}

	if resp != nil && resp.IsResponse() {
		rcode := RCode(resp.Header.Flags & 0xF)
		if rcode != RCodeNXDomain {
			t.Errorf("Expected NXDOMAIN, got %s", rcode)
		}
	}
}

// TestResolverCNAME tests CNAME resolution.
func TestResolverCNAME(t *testing.T) {
	forwarder := NewForwarder([]string{"8.8.8.8:53"}, 5)
	resolver := NewResolver(100, 3600, forwarder)

	zoneContent := `
$ORIGIN example.com.
$TTL 3600

www     IN  A       93.184.216.34
blog    IN  CNAME   www.example.com.
`
	zone, _ := ParseZoneFile(zoneContent)
	resolver.AddZone("example.com", zone)

	resp, err := resolver.Resolve("blog.example.com", TypeCNAME)
	if err != nil {
		t.Fatalf("Resolve error: %v", err)
	}

	if resp != nil && len(resp.Answers) > 0 {
		// Should have at least a CNAME record
		found := false
		for _, ans := range resp.Answers {
			if ans.Type == TypeCNAME {
				found = true
				break
			}
		}
		if !found {
			t.Error("Expected CNAME record in answers")
		}
	}
}

// TestResolverMX tests MX record resolution.
func TestResolverMX(t *testing.T) {
	forwarder := NewForwarder([]string{"8.8.8.8:53"}, 5)
	resolver := NewResolver(100, 3600, forwarder)

	zoneContent := `
$ORIGIN example.com.
$TTL 3600

@       IN  MX      10  mail.example.com.
mail    IN  A       192.168.1.1
`
	zone, _ := ParseZoneFile(zoneContent)
	resolver.AddZone("example.com", zone)

	resp, err := resolver.Resolve("example.com", TypeMX)
	if err != nil {
		t.Fatalf("Resolve error: %v", err)
	}

	if resp != nil && len(resp.Answers) > 0 {
		mxFound := false
		for _, ans := range resp.Answers {
			if ans.Type == TypeMX {
				mxFound = true
				break
			}
		}
		if !mxFound {
			t.Error("Expected MX record in answers")
		}
	}
}

// TestResolverNS tests NS record resolution.
func TestResolverNS(t *testing.T) {
	forwarder := NewForwarder([]string{"8.8.8.8:53"}, 5)
	resolver := NewResolver(100, 3600, forwarder)

	zoneContent := `
$ORIGIN example.com.
$TTL 3600

@       IN  NS      ns1.example.com.
ns1     IN  A       192.168.1.1
`
	zone, _ := ParseZoneFile(zoneContent)
	resolver.AddZone("example.com", zone)

	resp, err := resolver.Resolve("example.com", TypeNS)
	if err != nil {
		t.Fatalf("Resolve error: %v", err)
	}

	if resp != nil && len(resp.Answers) > 0 {
		nsFound := false
		for _, ans := range resp.Answers {
			if ans.Type == TypeNS {
				nsFound = true
				break
			}
		}
		if !nsFound {
			t.Error("Expected NS record in answers")
		}
	}
}

// TestForwarder tests the DNS forwarder.
func TestForwarder(t *testing.T) {
	f := NewForwarder([]string{"8.8.8.8:53", "1.1.1.1:53"}, 5)

	upstreams := f.GetUpstreams()
	if len(upstreams) != 2 {
		t.Errorf("Expected 2 upstreams, got %d", len(upstreams))
	}

	f.AddUpstream("9.9.9.9:53")
	upstreams = f.GetUpstreams()
	if len(upstreams) != 3 {
		t.Errorf("Expected 3 upstreams, got %d", len(upstreams))
	}

	f.SetTimeout(10)
	if true {
		// Timeout is set, just verify no panic
	}
}

// TestForwarderNoUpstreams tests forwarder with no upstreams.
func TestForwarderNoUpstreams(t *testing.T) {
	f := NewForwarder([]string{}, 5)
	_, err := f.Forward(NewMessage(0))
	if err == nil {
		t.Error("Expected error with no upstreams")
	}
}

// TestHandleDNSQuery tests the DNS query handling.
func TestHandleDNSQuery(t *testing.T) {
	forwarder := NewForwarder([]string{"8.8.8.8:53"}, 5)
	resolver := NewResolver(100, 3600, forwarder)

	zoneContent := `
$ORIGIN example.com.
$TTL 3600

www     IN  A       93.184.216.34
`
	zone, _ := ParseZoneFile(zoneContent)
	resolver.AddZone("example.com", zone)

	server := &DNSServer{
		resolver: resolver,
	}

	// Create a query packet
	query := NewMessage(0x1234)
	query.Header.QDCount = 1
	query.Questions = []Question{
		{Name: "www.example.com", Type: TypeA, Class: ClassIN},
	}

	queryBytes, err := query.Encode()
	if err != nil {
		t.Fatalf("Encode error: %v", err)
	}

	// Handle the query
	respBytes, err := server.HandleDNSQuery(queryBytes)
	if err != nil {
		t.Fatalf("HandleDNSQuery error: %v", err)
	}

	if respBytes == nil {
		t.Fatal("Expected non-nil response bytes")
	}

	// Decode and verify response
	var resp Message
	if err := resp.Decode(respBytes); err != nil {
		t.Fatalf("Decode response error: %v", err)
	}

	if !resp.IsResponse() {
		t.Error("Expected response message")
	}
}

// TestHandleDNSQueryFormatError tests handling of malformed queries.
func TestHandleDNSQueryFormatError(t *testing.T) {
	forwarder := NewForwarder([]string{"8.8.8.8:53"}, 5)
	resolver := NewResolver(100, 3600, forwarder)

	server := &DNSServer{
		resolver: resolver,
	}

	// Send a too-short packet
	badQuery := []byte{0x00, 0x01}

	respBytes, err := server.HandleDNSQuery(badQuery)
	if err != nil {
		t.Fatalf("HandleDNSQuery error: %v", err)
	}

	if respBytes == nil {
		t.Fatal("Expected response even for bad query")
	}

	var resp Message
	if err := resp.Decode(respBytes); err != nil {
		t.Fatalf("Decode response error: %v", err)
	}

	if !resp.IsResponse() {
		t.Error("Expected response message")
	}
}

// TestHandleDNSQueryAlreadyResponse tests handling of response packets.
func TestHandleDNSQueryAlreadyResponse(t *testing.T) {
	forwarder := NewForwarder([]string{"8.8.8.8:53"}, 5)
	resolver := NewResolver(100, 3600, forwarder)

	server := &DNSServer{
		resolver: resolver,
	}

	// Create a response packet (QR=1)
	resp := NewResponse(0x1234)
	respBytes, _ := resp.Encode()

	_, err := server.HandleDNSQuery(respBytes)
	if err == nil {
		t.Error("Expected error for response packet")
	}
}

// TestNewDNSServer tests server creation.
func TestNewDNSServer(t *testing.T) {
	config := ServerConfig{
		Address:    ":5353",
		CacheSize:  512,
		DefaultTTL: 1800,
		Timeout:    3,
		Upstreams:  []string{"8.8.8.8:53"},
	}

	server := NewServer(config)
	if server == nil {
		t.Fatal("Expected non-nil server")
	}
	if server.Resolver() == nil {
		t.Fatal("Expected non-nil resolver")
	}
	if server.Cache() == nil {
		t.Fatal("Expected non-nil cache")
	}
}

// TestMessageStringEmpty tests String() for empty message.
func TestMessageStringEmpty(t *testing.T) {
	msg := NewMessage(0)
	s := msg.String()
	if len(s) == 0 {
		t.Error("Expected non-empty string")
	}
}

// TestHeaderString tests Header.String().
func TestHeaderString(t *testing.T) {
	h := Header{
		ID:      0x1234,
		QDCount: 1,
		ANCount: 2,
		NSCount: 3,
		ARCount: 4,
	}
	s := h.String()
	if s == "" {
		t.Error("Expected non-empty string")
	}
}

// TestNewErrorResponse tests error response creation.
func TestNewErrorResponse(t *testing.T) {
	resp := NewErrorResponse(0x1234, RCodeRefused)
	if !resp.IsResponse() {
		t.Error("Expected response")
	}
	if resp.Header.ID != 0x1234 {
		t.Errorf("ID: got %d, want 0x1234", resp.Header.ID)
	}
}

// TestEncodeDecodeMultipleQuestions tests encoding/decoding with multiple questions.
func TestEncodeDecodeMultipleQuestions(t *testing.T) {
	msg := NewMessage(0)
	msg.Header.QDCount = 3
	msg.Questions = []Question{
		{Name: "a.com", Type: TypeA, Class: ClassIN},
		{Name: "b.com", Type: TypeAAAA, Class: ClassIN},
		{Name: "c.com", Type: TypeMX, Class: ClassIN},
	}

	encoded, err := msg.Encode()
	if err != nil {
		t.Fatalf("Encode error: %v", err)
	}

	var decoded Message
	if err := decoded.Decode(encoded); err != nil {
		t.Fatalf("Decode error: %v", err)
	}

	if decoded.Header.QDCount != 3 {
		t.Errorf("QDCount: got %d, want 3", decoded.Header.QDCount)
	}

	if len(decoded.Questions) != 3 {
		t.Errorf("Questions count: got %d, want 3", len(decoded.Questions))
	}
}

// TestEncodeDecodeAdditionalSection tests encoding/decoding with additional section.
func TestEncodeDecodeAdditionalSection(t *testing.T) {
	msg := NewMessage(0)
	msg.Header.QDCount = 1
	msg.Questions = []Question{
		{Name: "example.com", Type: TypeA, Class: ClassIN},
	}
	msg.Header.ANCount = 1
	msg.Answers = []ResourceRecord{
		{Name: "example.com", Type: TypeA, Class: ClassIN, TTL: 300, Data: []byte{1, 2, 3, 4}},
	}
	msg.Header.ARCount = 1
	msg.Additional = []ResourceRecord{
		{Name: "ns1.example.com", Type: TypeA, Class: ClassIN, TTL: 3600, Data: []byte{10, 0, 0, 1}},
	}

	encoded, err := msg.Encode()
	if err != nil {
		t.Fatalf("Encode error: %v", err)
	}

	var decoded Message
	if err := decoded.Decode(encoded); err != nil {
		t.Fatalf("Decode error: %v", err)
	}

	if decoded.Header.ARCount != 1 {
		t.Errorf("ARCount: got %d, want 1", decoded.Header.ARCount)
	}

	if len(decoded.Additional) != 1 {
		t.Errorf("Additional count: got %d, want 1", len(decoded.Additional))
	}
}

// TestCacheKeyConsistency tests that cache keys are consistent.
func TestCacheKeyConsistency(t *testing.T) {
	key1 := CacheKey("example.com", TypeA, ClassIN)
	key2 := CacheKey("example.com", TypeA, ClassIN)
	if key1 != key2 {
		t.Errorf("Cache keys should be equal: %q vs %q", key1, key2)
	}

	key3 := CacheKey("example.com", TypeAAAA, ClassIN)
	if key1 == key3 {
		t.Error("Cache keys for different types should differ")
	}
}

// TestResolverAddZone tests zone registration.
func TestResolverAddZone(t *testing.T) {
	resolver := NewResolver(100, 3600, nil)

	zoneContent := `
$ORIGIN test.com.
$TTL 3600

www     IN  A       1.2.3.4
`
	zone, _ := ParseZoneFile(zoneContent)
	resolver.AddZone("test.com", zone)

	// Should resolve without error
	resp, err := resolver.Resolve("www.test.com", TypeA)
	if err != nil {
		t.Fatalf("Resolve error: %v", err)
	}

	if resp == nil {
		t.Fatal("Expected non-nil response")
	}
}

// TestResolverResolveNonExistent tests resolving a non-existent domain.
func TestResolverResolveNonExistent(t *testing.T) {
	forwarder := NewForwarder([]string{}, 5)
	resolver := NewResolver(100, 3600, forwarder)

	// No zones registered
	resp, err := resolver.Resolve("nonexistent.example.com", TypeA)
	if err != nil {
		t.Fatalf("Resolve error: %v", err)
	}

	if resp != nil && resp.IsResponse() {
		rcode := RCode(resp.Header.Flags & 0xF)
		if rcode != RCodeNXDomain {
			t.Errorf("Expected NXDOMAIN, got %s", rcode)
		}
	}
}

// TestResolverCACHESize tests cache size limits.
func TestResolverCACHESize(t *testing.T) {
	forwarder := NewForwarder([]string{"8.8.8.8:53"}, 5)
	resolver := NewResolver(5, 3600, forwarder) // Small cache

	zoneContent := `
$ORIGIN example.com.
$TTL 3600

www     IN  A       93.184.216.34
`
	zone, _ := ParseZoneFile(zoneContent)
	resolver.AddZone("example.com", zone)

	// Fill the cache
	for i := 0; i < 10; i++ {
		name := "host" + string(rune('a'+i)) + ".example.com"
		resp, err := resolver.Resolve(name, TypeA)
		if err != nil || resp == nil {
			t.Fatalf("Resolve error for %s: %v", name, err)
		}
		_ = resp
	}

	// Cache should be limited
	if resolver.Cache().Size() > 5 {
		t.Errorf("Cache size: got %d, expected <= 5", resolver.Cache().Size())
	}
}

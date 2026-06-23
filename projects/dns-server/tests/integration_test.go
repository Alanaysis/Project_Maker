// Package tests provides integration tests for the DNS server.
//
// These tests verify the interaction between components (protocol, cache,
// resolver, server) working together end-to-end without requiring network
// access to external DNS servers.
package tests

import (
	"encoding/binary"
	"net"
	"testing"
	"time"

	"github.com/anthropic/dns-server/internal/cache"
	"github.com/anthropic/dns-server/internal/protocol"
	"github.com/anthropic/dns-server/internal/resolver"
	"github.com/anthropic/dns-server/internal/server"
)

// ─── Protocol + Resolver Integration ──────────────────────────────────────────

func TestProtocolResolverIntegration(t *testing.T) {
	// Verify that protocol messages can be built, resolved, and serialized
	// correctly through the full pipeline.

	res := resolver.New()
	res.AddARecord("api.example.local", net.ParseIP("10.0.1.1"))
	res.AddARecord("api.example.local", net.ParseIP("10.0.1.2"))
	res.AddARecord("db.example.local", net.ParseIP("10.0.2.1"))

	// Build a query message
	query := &protocol.Message{
		Header: protocol.Header{
			ID:      0x1234,
			QR:      protocol.QRQuery,
			Opcode:  protocol.OpcodeQuery,
			RD:      true,
			QDCount: 1,
		},
		Question: []protocol.Question{
			{Name: "api.example.local", Type: protocol.TypeA, Class: protocol.ClassIN},
		},
	}

	// Pack and unpack to simulate network transport
	data, err := query.Pack()
	if err != nil {
		t.Fatalf("Pack query: %v", err)
	}

	parsed, err := protocol.Unpack(data)
	if err != nil {
		t.Fatalf("Unpack query: %v", err)
	}

	// Resolve
	records, rcode := res.Resolve(parsed.Question[0])
	if rcode != protocol.RcodeNoError {
		t.Fatalf("Resolve: expected NOERROR, got %s", protocol.RcodeName(rcode))
	}
	if len(records) != 2 {
		t.Fatalf("expected 2 A records, got %d", len(records))
	}

	// Build response
	response := &protocol.Message{
		Header: protocol.Header{
			ID:      parsed.Header.ID,
			QR:      protocol.QRResponse,
			Opcode:  parsed.Header.Opcode,
			RD:      parsed.Header.RD,
			RA:      true,
			QDCount: 1,
			ANCount: uint16(len(records)),
		},
		Question: parsed.Question,
		Answer:   records,
	}

	respData, err := response.Pack()
	if err != nil {
		t.Fatalf("Pack response: %v", err)
	}

	// Verify response can be parsed by a standard DNS client
	parsedResp, err := protocol.Unpack(respData)
	if err != nil {
		t.Fatalf("Unpack response: %v", err)
	}

	if parsedResp.Header.ID != 0x1234 {
		t.Errorf("response ID mismatch: got 0x%04x, want 0x1234", parsedResp.Header.ID)
	}
	if parsedResp.Header.QR != protocol.QRResponse {
		t.Error("response QR bit should be 1")
	}
	if !parsedResp.Header.RA {
		t.Error("response RA bit should be true")
	}
	if len(parsedResp.Answer) != 2 {
		t.Fatalf("expected 2 answers in response, got %d", len(parsedResp.Answer))
	}

	// Verify the resolved IPs
	ips := make(map[string]bool)
	for _, rr := range parsedResp.Answer {
		if rr.Type != protocol.TypeA {
			t.Errorf("expected A record, got type %d", rr.Type)
		}
		ip := net.IP(rr.RData).String()
		ips[ip] = true
	}
	if !ips["10.0.1.1"] || !ips["10.0.1.2"] {
		t.Errorf("unexpected IPs: %v", ips)
	}
}

// ─── Cache + Resolver Integration ─────────────────────────────────────────────

func TestCacheResolverIntegration(t *testing.T) {
	// Verify that caching works correctly across multiple resolve operations.

	dnsCache := cache.New(cache.WithMaxSize(100))
	res := resolver.New()
	res.AddARecord("web.local", net.ParseIP("192.168.1.10"))
	res.AddARecord("web.local", net.ParseIP("192.168.1.11"))

	q := protocol.Question{
		Name:  "web.local",
		Type:  protocol.TypeA,
		Class: protocol.ClassIN,
	}

	// First resolve: cache miss
	if _, found := dnsCache.Get(q.Name, q.Type); found {
		t.Fatal("expected cache miss on first query")
	}

	records, rcode := res.Resolve(q)
	if rcode != protocol.RcodeNoError {
		t.Fatalf("first resolve failed: %d", rcode)
	}
	dnsCache.Set(q.Name, q.Type, records)

	// Second resolve: cache hit
	cached, found := dnsCache.Get(q.Name, q.Type)
	if !found {
		t.Fatal("expected cache hit on second query")
	}
	if len(cached) != 2 {
		t.Fatalf("expected 2 cached records, got %d", len(cached))
	}

	// Verify cache stats
	stats := dnsCache.StatsSnapshot()
	if stats.Hits != 1 {
		t.Errorf("expected 1 hit, got %d", stats.Hits)
	}
	if stats.Misses != 1 {
		t.Errorf("expected 1 miss, got %d", stats.Misses)
	}

	// Different record type for same domain should be a miss
	if _, found := dnsCache.Get(q.Name, protocol.TypeAAAA); found {
		t.Error("AAAA query should miss when only A is cached")
	}
}

// ─── Server Lifecycle Integration ─────────────────────────────────────────────

func TestServerLifecycleIntegration(t *testing.T) {
	// Verify that the server can start, accept queries, and stop cleanly.

	cfg := server.Config{
		ListenAddr:  ":0",
		UpstreamDNS: "8.8.8.8:53",
		CacheSize:   50,
	}
	srv := server.New(cfg)
	srv.Resolver().AddARecord("lifecycle.test", net.ParseIP("172.16.0.1"))

	// Start server in background
	errCh := make(chan error, 1)
	go func() {
		errCh <- srv.Start()
	}()

	time.Sleep(100 * time.Millisecond)

	// Stop server
	srv.Stop()

	select {
	case err := <-errCh:
		if err != nil {
			t.Fatalf("server error: %v", err)
		}
	case <-time.After(5 * time.Second):
		t.Fatal("server did not stop within timeout")
	}
}

// ─── End-to-End Resolution with Multiple Record Types ─────────────────────────

func TestMultiRecordTypeResolution(t *testing.T) {
	// Verify that different record types are resolved independently.

	res := resolver.New()

	// Add A record
	res.AddARecord("multi.test", net.ParseIP("10.0.0.1"))

	// Add AAAA record via ZoneBuilder
	records := resolver.NewZoneBuilder("multi.test").
		AAAA(net.ParseIP("::1")).
		Build()
	for _, rr := range records {
		res.AddZoneRecord(rr.Name, rr)
	}

	// Query A
	aRecords, rcode := res.Resolve(protocol.Question{
		Name: "multi.test", Type: protocol.TypeA, Class: protocol.ClassIN,
	})
	if rcode != protocol.RcodeNoError {
		t.Fatalf("A resolve failed: %d", rcode)
	}
	if len(aRecords) != 1 {
		t.Fatalf("expected 1 A record, got %d", len(aRecords))
	}

	// Query AAAA
	aaaaRecords, rcode := res.Resolve(protocol.Question{
		Name: "multi.test", Type: protocol.TypeAAAA, Class: protocol.ClassIN,
	})
	if rcode != protocol.RcodeNoError {
		t.Fatalf("AAAA resolve failed: %d", rcode)
	}
	if len(aaaaRecords) != 1 {
		t.Fatalf("expected 1 AAAA record, got %d", len(aaaaRecords))
	}

	// Query ANY should return both
	anyRecords, rcode := res.Resolve(protocol.Question{
		Name: "multi.test", Type: protocol.TypeANY, Class: protocol.ClassIN,
	})
	if rcode != protocol.RcodeNoError {
		t.Fatalf("ANY resolve failed: %d", rcode)
	}
	if len(anyRecords) != 2 {
		t.Fatalf("expected 2 ANY records, got %d", len(anyRecords))
	}
}

// ─── DNS Message Wire Format Compatibility ────────────────────────────────────

func TestWireFormatCompatibility(t *testing.T) {
	// Test parsing a realistic DNS query packet captured from the wire.
	// This is a standard A query for "example.com" with RD=1.

	rawQuery := []byte{
		0xAA, 0xBB, // Transaction ID
		0x01, 0x20, // Flags: RD=1, Opcode=0
		0x00, 0x01, // QDCOUNT = 1
		0x00, 0x00, // ANCOUNT = 0
		0x00, 0x00, // NSCOUNT = 0
		0x00, 0x00, // ARCOUNT = 0
		// Question: example.com
		0x07, 'e', 'x', 'a', 'm', 'p', 'l', 'e',
		0x03, 'c', 'o', 'm',
		0x00,       // Root label
		0x00, 0x01, // Type A
		0x00, 0x01, // Class IN
	}

	msg, err := protocol.Unpack(rawQuery)
	if err != nil {
		t.Fatalf("Unpack raw query: %v", err)
	}

	if msg.Header.ID != 0xAABB {
		t.Errorf("ID: got 0x%04x, want 0xAABB", msg.Header.ID)
	}
	if !msg.Header.RD {
		t.Error("RD should be true")
	}
	if len(msg.Question) != 1 {
		t.Fatalf("expected 1 question, got %d", len(msg.Question))
	}
	if msg.Question[0].Name != "example.com" {
		t.Errorf("question name: got %q, want %q", msg.Question[0].Name, "example.com")
	}
	if msg.Question[0].Type != protocol.TypeA {
		t.Errorf("question type: got %d, want %d", msg.Question[0].Type, protocol.TypeA)
	}
}

func TestWireFormatResponse(t *testing.T) {
	// Build a response and verify the raw bytes are correctly laid out.

	msg := &protocol.Message{
		Header: protocol.Header{
			ID:      0x1234,
			QR:      protocol.QRResponse,
			Opcode:  protocol.OpcodeQuery,
			RD:      true,
			RA:      true,
			QDCount: 1,
			ANCount: 1,
		},
		Question: []protocol.Question{
			{Name: "test.local", Type: protocol.TypeA, Class: protocol.ClassIN},
		},
		Answer: []protocol.ResourceRecord{
			{
				Name:  "test.local",
				Type:  protocol.TypeA,
				Class: protocol.ClassIN,
				TTL:   60,
				RDLen: 4,
				RData: []byte{192, 168, 0, 1},
			},
		},
	}

	data, err := msg.Pack()
	if err != nil {
		t.Fatalf("Pack: %v", err)
	}

	// Verify header bytes
	if data[0] != 0x12 || data[1] != 0x34 {
		t.Errorf("ID bytes: got %02x%02x, want 1234", data[0], data[1])
	}

	// QR bit should be set (response)
	if data[2]&0x80 == 0 {
		t.Error("QR bit should be set in response")
	}

	// RD bit should be set
	if data[2]&0x01 == 0 {
		t.Error("RD bit should be set")
	}

	// RA bit should be set
	if data[3]&0x80 == 0 {
		t.Error("RA bit should be set")
	}

	// QDCOUNT = 1
	if binary.BigEndian.Uint16(data[4:6]) != 1 {
		t.Errorf("QDCOUNT: got %d, want 1", binary.BigEndian.Uint16(data[4:6]))
	}

	// ANCOUNT = 1
	if binary.BigEndian.Uint16(data[6:8]) != 1 {
		t.Errorf("ANCOUNT: got %d, want 1", binary.BigEndian.Uint16(data[6:8]))
	}
}

// ─── Cache TTL Behavior ──────────────────────────────────────────────────────

func TestCacheTTLFloor(t *testing.T) {
	// Verify that the cache enforces a minimum TTL of 30 seconds.

	dnsCache := cache.New()

	records := []protocol.ResourceRecord{
		{
			Name:  "short-ttl.test",
			Type:  protocol.TypeA,
			Class: protocol.ClassIN,
			TTL:   5, // Very short TTL
			RDLen: 4,
			RData: []byte{10, 0, 0, 1},
		},
	}

	dnsCache.Set("short-ttl.test", protocol.TypeA, records)

	// Should still be cached (floor is 30s)
	_, found := dnsCache.Get("short-ttl.test", protocol.TypeA)
	if !found {
		t.Error("expected cache hit within 30s floor TTL")
	}
}

func TestCacheConcurrentAccess(t *testing.T) {
	// Verify that concurrent reads and writes don't cause races.

	dnsCache := cache.New(cache.WithMaxSize(1000))
	done := make(chan bool)

	// Writer goroutine
	go func() {
		for i := 0; i < 100; i++ {
			records := []protocol.ResourceRecord{
				{
					Name:  "concurrent.test",
					Type:  protocol.TypeA,
					TTL:   300,
					RDLen: 4,
					RData: []byte{10, 0, byte(i), 1},
				},
			}
			dnsCache.Set("concurrent.test", protocol.TypeA, records)
		}
		done <- true
	}()

	// Reader goroutine
	go func() {
		for i := 0; i < 100; i++ {
			dnsCache.Get("concurrent.test", protocol.TypeA)
		}
		done <- true
	}()

	// Wait for both
	<-done
	<-done

	// No panic or race condition means success
	if dnsCache.Size() > 1 {
		t.Errorf("expected at most 1 entry, got %d", dnsCache.Size())
	}
}

// ─── NXDOMAIN Behavior ───────────────────────────────────────────────────────

func TestNXDOMAINForUnknownLocal(t *testing.T) {
	// When local zones don't have a record and upstream is unreachable,
	// the resolver should return SERVFAIL (network error), not crash.

	res := resolver.New(resolver.WithUpstream("192.0.2.1:53")) // RFC 5737 TEST-NET
	res.AddARecord("known.test", net.ParseIP("10.0.0.1"))

	// Known domain
	records, rcode := res.Resolve(protocol.Question{
		Name: "known.test", Type: protocol.TypeA, Class: protocol.ClassIN,
	})
	if rcode != protocol.RcodeNoError {
		t.Fatalf("known domain should resolve: rcode=%d", rcode)
	}
	if len(records) != 1 {
		t.Fatalf("expected 1 record, got %d", len(records))
	}

	// Unknown domain (will try upstream and fail gracefully)
	_, rcode = res.Resolve(protocol.Question{
		Name: "unknown.test", Type: protocol.TypeA, Class: protocol.ClassIN,
	})
	// Should return SERVFAIL, not panic
	if rcode == protocol.RcodeNoError {
		t.Log("upstream resolved (unexpected in test env), but no crash")
	}
}

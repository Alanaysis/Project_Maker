package server

import (
	"net"
	"testing"
	"time"

	"github.com/anthropic/dns-server/internal/cache"
	"github.com/anthropic/dns-server/internal/protocol"
	"github.com/anthropic/dns-server/internal/resolver"
)

func TestDefaultConfig(t *testing.T) {
	cfg := DefaultConfig()
	if cfg.ListenAddr != ":5353" {
		t.Errorf("expected default listen addr :5353, got %s", cfg.ListenAddr)
	}
	if cfg.UpstreamDNS != "8.8.8.8:53" {
		t.Errorf("expected default upstream 8.8.8.8:53, got %s", cfg.UpstreamDNS)
	}
	if cfg.CacheSize != 1024 {
		t.Errorf("expected default cache size 1024, got %d", cfg.CacheSize)
	}
}

func TestServerCreation(t *testing.T) {
	cfg := Config{
		ListenAddr:  ":0",
		UpstreamDNS: "8.8.8.8:53",
		CacheSize:   100,
	}
	srv := New(cfg)
	if srv == nil {
		t.Fatal("expected non-nil server")
	}
	if srv.Cache() == nil {
		t.Error("expected non-nil cache")
	}
	if srv.Resolver() == nil {
		t.Error("expected non-nil resolver")
	}
}

func TestResolveWithCache(t *testing.T) {
	// Create a server with local zone records
	cfg := Config{
		ListenAddr:  ":0",
		UpstreamDNS: "8.8.8.8:53",
		CacheSize:   100,
	}
	srv := New(cfg)

	// Add local zone record
	srv.Resolver().AddARecord("cached.test", net.ParseIP("10.0.0.1"))

	q := protocol.Question{
		Name:  "cached.test",
		Type:  protocol.TypeA,
		Class: protocol.ClassIN,
	}

	// First call -- cache miss, should resolve from local zone
	records, rcode := srv.resolveWithCache(q)
	if rcode != protocol.RcodeNoError {
		t.Fatalf("expected NOERROR, got %d", rcode)
	}
	if len(records) != 1 {
		t.Fatalf("expected 1 record, got %d", len(records))
	}

	// Second call -- should be a cache hit
	records, rcode = srv.resolveWithCache(q)
	if rcode != protocol.RcodeNoError {
		t.Fatalf("expected NOERROR on cache hit, got %d", rcode)
	}
	if len(records) != 1 {
		t.Fatalf("expected 1 record on cache hit, got %d", len(records))
	}

	// Verify cache stats
	stats := srv.Cache().StatsSnapshot()
	if stats.Hits != 1 {
		t.Errorf("expected 1 cache hit, got %d", stats.Hits)
	}
}

func TestServerStartStop(t *testing.T) {
	cfg := Config{
		ListenAddr:  ":0", // Let OS pick port
		UpstreamDNS: "8.8.8.8:53",
		CacheSize:   100,
	}
	srv := New(cfg)

	// Start server in background
	errCh := make(chan error, 1)
	go func() {
		errCh <- srv.Start()
	}()

	// Give it a moment to start
	time.Sleep(100 * time.Millisecond)

	// Stop it
	srv.Stop()

	// Wait for it to finish
	select {
	case err := <-errCh:
		if err != nil {
			t.Fatalf("server.Start() error: %v", err)
		}
	case <-time.After(5 * time.Second):
		t.Fatal("server did not stop within timeout")
	}
}

func TestCacheIntegration(t *testing.T) {
	// Test that the cache layer works correctly in isolation
	dnsCache := cache.New(cache.WithMaxSize(50))

	records := []protocol.ResourceRecord{
		{
			Name:  "integration.test",
			Type:  protocol.TypeA,
			Class: protocol.ClassIN,
			TTL:   300,
			RDLen: 4,
			RData: []byte{172, 16, 0, 1},
		},
	}

	// Set
	dnsCache.Set("integration.test", protocol.TypeA, records)

	// Get
	result, found := dnsCache.Get("integration.test", protocol.TypeA)
	if !found {
		t.Fatal("expected cache hit")
	}
	if len(result) != 1 {
		t.Fatalf("expected 1 record, got %d", len(result))
	}
	if result[0].RData[3] != 1 {
		t.Errorf("expected last octet 1, got %d", result[0].RData[3])
	}
}

func TestEndToEndLocalResolution(t *testing.T) {
	// This test creates a server, adds local records, and verifies
	// the full resolution pipeline works without network access.

	dnsCache := cache.New(cache.WithMaxSize(100))
	res := resolver.New()
	res.AddARecord("e2e.test", net.ParseIP("10.10.10.10"))
	res.AddARecord("e2e.test", net.ParseIP("10.10.10.11"))

	// Simulate what the server does: resolve + cache
	q := protocol.Question{
		Name:  "e2e.test",
		Type:  protocol.TypeA,
		Class: protocol.ClassIN,
	}

	// First: cache miss
	if _, found := dnsCache.Get(q.Name, q.Type); found {
		t.Error("expected cache miss")
	}

	// Resolve
	records, rcode := res.Resolve(q)
	if rcode != protocol.RcodeNoError {
		t.Fatalf("expected NOERROR, got %d", rcode)
	}
	if len(records) != 2 {
		t.Fatalf("expected 2 records, got %d", len(records))
	}

	// Cache it
	dnsCache.Set(q.Name, q.Type, records)

	// Second: cache hit
	cached, found := dnsCache.Get(q.Name, q.Type)
	if !found {
		t.Fatal("expected cache hit")
	}
	if len(cached) != 2 {
		t.Fatalf("expected 2 cached records, got %d", len(cached))
	}
}

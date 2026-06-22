package cache

import (
	"testing"
	"time"

	"github.com/anthropic/dns-server/internal/protocol"
)

func TestCacheSetGet(t *testing.T) {
	c := New()

	records := []protocol.ResourceRecord{
		{
			Name:  "example.com",
			Type:  protocol.TypeA,
			Class: protocol.ClassIN,
			TTL:   300,
			RDLen: 4,
			RData: []byte{93, 184, 216, 34},
		},
	}

	// Miss on empty cache
	_, found := c.Get("example.com", protocol.TypeA)
	if found {
		t.Error("expected cache miss on empty cache")
	}

	// Set and Get
	c.Set("example.com", protocol.TypeA, records)
	result, found := c.Get("example.com", protocol.TypeA)
	if !found {
		t.Fatal("expected cache hit after Set")
	}
	if len(result) != 1 {
		t.Fatalf("expected 1 record, got %d", len(result))
	}
	if result[0].RData[0] != 93 {
		t.Errorf("expected RData[0]=93, got %d", result[0].RData[0])
	}

	stats := c.StatsSnapshot()
	if stats.Hits != 1 {
		t.Errorf("expected 1 hit, got %d", stats.Hits)
	}
	if stats.Misses != 1 {
		t.Errorf("expected 1 miss, got %d", stats.Misses)
	}
}

func TestCacheExpiry(t *testing.T) {
	c := New()

	records := []protocol.ResourceRecord{
		{
			Name:  "test.com",
			Type:  protocol.TypeA,
			TTL:   300,
			RDLen: 4,
			RData: []byte{1, 2, 3, 4},
		},
	}

	c.Set("test.com", protocol.TypeA, records)

	// Manually expire the entry by setting its expiration to the past
	c.mu.Lock()
	key := makeKey("test.com", protocol.TypeA)
	c.entries[key].ExpiresAt = time.Now().Add(-1 * time.Second)
	c.mu.Unlock()

	_, found := c.Get("test.com", protocol.TypeA)
	if found {
		t.Error("expected cache miss for expired entry")
	}

	// The entry should have been removed
	if c.Size() != 0 {
		t.Errorf("expected cache size 0 after expiry, got %d", c.Size())
	}
}

func TestCacheDifferentTypes(t *testing.T) {
	c := New()

	aRecord := []protocol.ResourceRecord{
		{Name: "example.com", Type: protocol.TypeA, TTL: 300, RDLen: 4, RData: []byte{1, 2, 3, 4}},
	}
	aaaaRecord := []protocol.ResourceRecord{
		{Name: "example.com", Type: protocol.TypeAAAA, TTL: 300, RDLen: 16,
			RData: []byte{0x20, 0x01, 0x0d, 0xb8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1}},
	}

	c.Set("example.com", protocol.TypeA, aRecord)
	c.Set("example.com", protocol.TypeAAAA, aaaaRecord)

	// A record
	result, found := c.Get("example.com", protocol.TypeA)
	if !found || len(result) != 1 || result[0].Type != protocol.TypeA {
		t.Error("failed to get A record")
	}

	// AAAA record
	result, found = c.Get("example.com", protocol.TypeAAAA)
	if !found || len(result) != 1 || result[0].Type != protocol.TypeAAAA {
		t.Error("failed to get AAAA record")
	}
}

func TestCacheDelete(t *testing.T) {
	c := New()
	records := []protocol.ResourceRecord{
		{Name: "x.com", Type: protocol.TypeA, TTL: 300, RDLen: 4, RData: []byte{1, 2, 3, 4}},
	}
	c.Set("x.com", protocol.TypeA, records)

	c.Delete("x.com", protocol.TypeA)
	if c.Size() != 0 {
		t.Errorf("expected size 0 after delete, got %d", c.Size())
	}
}

func TestCacheClear(t *testing.T) {
	c := New()
	for i := 0; i < 10; i++ {
		records := []protocol.ResourceRecord{
			{Name: "x.com", Type: protocol.TypeA, TTL: 300, RDLen: 4, RData: []byte{1, 2, 3, 4}},
		}
		c.Set("x.com", protocol.TypeA, records)
	}

	c.Clear()
	if c.Size() != 0 {
		t.Errorf("expected size 0 after clear, got %d", c.Size())
	}
}

func TestCacheMaxSize(t *testing.T) {
	c := New(WithMaxSize(3))

	for i := 0; i < 5; i++ {
		records := []protocol.ResourceRecord{
			{
				Name:  "test.com",
				Type:  protocol.TypeA,
				TTL:   300,
				RDLen: 4,
				RData: []byte{byte(i), 2, 3, 4},
			},
		}
		c.Set("test.com", protocol.TypeA, records)
	}

	// Should have evicted some entries; cache should not exceed maxSize
	if c.Size() > 3 {
		t.Errorf("expected cache size <= 3, got %d", c.Size())
	}
}

func TestPurgeExpired(t *testing.T) {
	c := New()

	// Add entries with short TTL
	for i := 0; i < 5; i++ {
		records := []protocol.ResourceRecord{
			{
				Name:  "test.com",
				Type:  protocol.TypeA,
				TTL:   1, // 1 second
				RDLen: 4,
				RData: []byte{byte(i), 2, 3, 4},
			},
		}
		c.Set("test.com", protocol.TypeA, records)
	}

	// Manually expire all entries
	c.mu.Lock()
	for _, entry := range c.entries {
		entry.ExpiresAt = time.Now().Add(-1 * time.Second)
	}
	c.mu.Unlock()

	removed := c.PurgeExpired()
	if removed != 1 { // All share the same key, so only 1 entry
		t.Errorf("expected 1 removed, got %d", removed)
	}
	if c.Size() != 0 {
		t.Errorf("expected size 0 after purge, got %d", c.Size())
	}
}

func TestStartCleanup(t *testing.T) {
	c := New()

	records := []protocol.ResourceRecord{
		{Name: "x.com", Type: protocol.TypeA, TTL: 1, RDLen: 4, RData: []byte{1, 2, 3, 4}},
	}
	c.Set("x.com", protocol.TypeA, records)

	// Manually expire
	c.mu.Lock()
	key := makeKey("x.com", protocol.TypeA)
	c.entries[key].ExpiresAt = time.Now().Add(-1 * time.Second)
	c.mu.Unlock()

	stop := c.StartCleanup(50 * time.Millisecond)
	defer stop()

	// Wait for cleanup to run
	time.Sleep(200 * time.Millisecond)

	if c.Size() != 0 {
		t.Errorf("expected size 0 after cleanup, got %d", c.Size())
	}
}

func TestEmptyRecordsNotCached(t *testing.T) {
	c := New()
	c.Set("empty.com", protocol.TypeA, nil)
	if c.Size() != 0 {
		t.Errorf("expected empty records not cached, got size %d", c.Size())
	}
}

func TestMakeKey(t *testing.T) {
	key := makeKey("example.com", protocol.TypeA)
	expected := "example.com:1"
	if key != expected {
		t.Errorf("expected %q, got %q", expected, key)
	}
}

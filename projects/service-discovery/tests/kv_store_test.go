package service_discovery

import (
	"testing"
	"time"
)

// TestConsulKVStore tests the Consul-like KV store.
func TestConsulKVStore(t *testing.T) {
	kv := NewConsulKVStore()

	// Test Put and Get
	entry, err := kv.Put("key1", []byte("value1"), 0, "", 0)
	if err != nil {
		t.Fatalf("Put: unexpected error: %v", err)
	}
	if entry.Key != "key1" {
		t.Errorf("Put: expected key 'key1', got '%s'", entry.Key)
	}
	if string(entry.Value) != "value1" {
		t.Errorf("Put: expected value 'value1', got '%s'", string(entry.Value))
	}

	// Test Get
	retrieved, ok := kv.Get("key1")
	if !ok {
		t.Error("Get: should find existing key")
	}
	if string(retrieved.Value) != "value1" {
		t.Errorf("Get: expected value 'value1', got '%s'", string(retrieved.Value))
	}

	// Test Get non-existent
	_, ok = kv.Get("non-existent")
	if ok {
		t.Error("Get: should not find non-existent key")
	}

	// Test Delete
	if !kv.Delete("key1") {
		t.Error("Delete: should return true for existing key")
	}
	if _, ok := kv.Get("key1"); ok {
		t.Error("Delete: key should be deleted")
	}

	// Test Delete non-existent
	if kv.Delete("non-existent") {
		t.Error("Delete: should return false for non-existent key")
	}
}

// TestConsulKVStoreList tests listing entries by prefix.
func TestConsulKVStoreList(t *testing.T) {
	kv := NewConsulKVStore()

	kv.Put("services/user/1", []byte("192.168.1.1:8080"), 0, "", 0)
	kv.Put("services/user/2", []byte("192.168.1.2:8080"), 0, "", 0)
	kv.Put("services/order/1", []byte("192.168.1.3:9090"), 0, "", 0)

	// List by prefix
	entries := kv.List("services/user/")
	if len(entries) != 2 {
		t.Errorf("List: expected 2 entries, got %d", len(entries))
	}

	// List with no matches
	entries = kv.List("services/nonexistent/")
	if len(entries) != 0 {
		t.Errorf("List: expected 0 entries, got %d", len(entries))
	}
}

// TestConsulKVStoreCAS tests compare-and-swap.
func TestConsulKVStoreCAS(t *testing.T) {
	kv := NewConsulKVStore()

	// Put initial value
	entry, _ := kv.Put("key1", []byte("value1"), 0, "", 0)
	expectedIndex := entry.ModifyIndex

	// CAS with correct index should succeed
	_, err := kv.CompareAndSwap("key1", []byte("value2"), 0, expectedIndex)
	if err != nil {
		t.Errorf("CAS: unexpected error: %v", err)
	}

	// CAS with wrong index should fail
	_, err = kv.CompareAndSwap("key1", []byte("value3"), 0, expectedIndex+1)
	if err == nil {
		t.Error("CAS: should fail with wrong index")
	}

	// Verify value was updated
	entry, _ = kv.Get("key1")
	if string(entry.Value) != "value2" {
		t.Errorf("CAS: expected value 'value2', got '%s'", string(entry.Value))
	}
}

// TestConsulKVStoreFlags tests flag handling.
func TestConsulKVStoreFlags(t *testing.T) {
	kv := NewConsulKVStore()

	kv.Put("key1", []byte("value1"), 42, "session-1", 0)
	entry, _ := kv.Get("key1")

	if entry.Flags != 42 {
		t.Errorf("Flags: expected 42, got %d", entry.Flags)
	}
	if entry.Session != "session-1" {
		t.Errorf("Session: expected 'session-1', got '%s'", entry.Session)
	}
}

// TestConsulKVStoreModifyIndex tests modify index increment.
func TestConsulKVStoreModifyIndex(t *testing.T) {
	kv := NewConsulKVStore()

	kv.Put("key1", []byte("v1"), 0, "", 0)
	index1 := kv.Get("key1").ModifyIndex

	kv.Put("key1", []byte("v2"), 0, "", 0)
	index2 := kv.Get("key1").ModifyIndex

	if index2 <= index1 {
		t.Errorf("ModifyIndex: expected %d > %d", index2, index1)
	}
}

// TestConsulKVStoreTTL tests TTL storage.
func TestConsulKVStoreTTL(t *testing.T) {
	kv := NewConsulKVStore()

	ttl := 30 * time.Second
	kv.Put("key1", []byte("value1"), 0, "", ttl)
	entry, _ := kv.Get("key1")

	if entry.TTL != ttl {
		t.Errorf("TTL: expected %v, got %v", ttl, entry.TTL)
	}
}

// TestConsulKVStoreEmptyPrefix tests listing with empty prefix.
func TestConsulKVStoreEmptyPrefix(t *testing.T) {
	kv := NewConsulKVStore()

	kv.Put("key1", []byte("v1"), 0, "", 0)
	kv.Put("key2", []byte("v2"), 0, "", 0)

	entries := kv.List("")
	if len(entries) != 2 {
		t.Errorf("List with empty prefix: expected 2, got %d", len(entries))
	}
}

// TestDiscoveryCache tests the discovery cache.
func TestDiscoveryCache(t *testing.T) {
	cache := NewDiscoveryCache(10 * time.Second)

	// Test empty cache
	_, ok := cache.Get("service")
	if ok {
		t.Error("Get: should not find in empty cache")
	}

	// Test Set and Get
	instances := []*ServiceInstance{
		{ID: "inst-1", Service: "service", Address: "127.0.0.1", Port: 8080, TTL: 30 * time.Second},
	}
	cache.Set("service", instances)

	retrieved, ok := cache.Get("service")
	if !ok {
		t.Error("Get: should find in cache")
	}
	if len(retrieved) != 1 {
		t.Errorf("Get: expected 1 instance, got %d", len(retrieved))
	}

	// Test IsExpired
	if cache.IsExpired() {
		t.Error("IsExpired: should not be expired for fresh cache")
	}

	// Test Clear
	cache.Clear()
	_, ok = cache.Get("service")
	if ok {
		t.Error("Get: should not find after Clear")
	}
}

// TestDiscoveryCacheTTL tests cache expiration.
func TestDiscoveryCacheTTL(t *testing.T) {
	cache := NewDiscoveryCache(1 * time.Millisecond)

	cache.Set("service", []*ServiceInstance{})

	// Wait for cache to expire
	time.Sleep(10 * time.Millisecond)

	if !cache.IsExpired() {
		t.Error("IsExpired: should be expired after TTL")
	}
}

// TestHealthCheckConfig tests health check configuration.
func TestHealthCheckConfig(t *testing.T) {
	config := HealthCheckConfig{
		Type:    HealthCheckTCP,
		Interval: 10 * time.Second,
		Timeout:  5 * time.Second,
	}

	if config.Type != HealthCheckTCP {
		t.Errorf("Type: expected %s, got %s", HealthCheckTCP, config.Type)
	}
	if config.Interval != 10*time.Second {
		t.Errorf("Interval: expected 10s, got %v", config.Interval)
	}
	if config.Timeout != 5*time.Second {
		t.Errorf("Timeout: expected 5s, got %v", config.Timeout)
	}
}

// TestServiceStatus tests service status constants.
func TestServiceStatus(t *testing.T) {
	statuses := []ServiceStatus{
		StatusHealthy,
		StatusUnhealthy,
		StatusSuspect,
		StatusDeregistered,
	}

	for _, status := range statuses {
		if len(status) == 0 {
			t.Errorf("Status: empty status value")
		}
	}
}

// TestLoadBalancerType tests load balancer type constants.
func TestLoadBalancerType(t *testing.T) {
	types := []LoadBalancerType{
		LoadBalancerRoundRobin,
		LoadBalancerWeighted,
		LoadBalancerLeastConn,
		LoadBalancerRandom,
	}

	for _, t := range types {
		if len(t) == 0 {
			t.Errorf("LoadBalancerType: empty type value")
		}
	}
}

// TestHealthCheckType tests health check type constants.
func TestHealthCheckType(t *testing.T) {
	types := []HealthCheckType{
		HealthCheckTCP,
		HealthCheckHTTP,
		HealthCheckCustom,
	}

	for _, t := range types {
		if len(t) == 0 {
			t.Errorf("HealthCheckType: empty type value")
		}
	}
}

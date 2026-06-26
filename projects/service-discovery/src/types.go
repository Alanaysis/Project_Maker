// Package main contains the core types for the service discovery system.
//
// Service discovery is a fundamental building block in microservices architecture.
// It enables automatic detection and location of services in a distributed system.
//
// Core concepts:
//   - Service Registry: Stores information about available service instances
//   - Health Check: Verifies that service instances are still operational
//   - Service Discovery: Retrieves available instances for a given service
//   - Load Balancing: Distributes requests across healthy instances
//
// Architecture overview:
//
//	┌─────────────┐     ┌──────────────┐     ┌─────────────┐
//	│  Service A   │────▶│ Service      │────▶│  Service B   │
//	│  (Client)    │     │ Registry     │     │  (Provider)  │
//	│              │◀────│ (Registry)   │◀────│              │
//	└─────────────┘     └──────────────┘     └─────────────┘
//	                    ┌──────────────┐
//	                    │ Health       │
//	                    │ Checker      │
//	                    └──────────────┘
//
// Service registration flow:
//   1. Service instance starts
//   2. Registers with registry (address, port, metadata, TTL)
//   3. Registry stores instance info
//   4. Health checker monitors instance
//
// Service discovery flow:
//   1. Client queries registry for service
//   2. Registry returns list of healthy instances
//   3. Load balancer selects an instance
//   4. Client connects to selected instance
package main

import (
	"fmt"
	"time"
)

// ServiceStatus represents the status of a service instance.
type ServiceStatus string

const (
	StatusHealthy  ServiceStatus = "healthy"   // Instance is healthy and can receive traffic
	StatusUnhealthy ServiceStatus = "unhealthy" // Instance has failed health checks
	StatusSuspect   ServiceStatus = "suspect"   // Instance health is uncertain
	StatusDeregistered ServiceStatus = "deregistered" // Instance has been removed
)

// HealthCheckType represents the type of health check mechanism.
type HealthCheckType string

const (
	HealthCheckTCP  HealthCheckType = "tcp"  // TCP connection check
	HealthCheckHTTP HealthCheckType = "http" // HTTP endpoint check
	HealthCheckCustom HealthCheckType = "custom" // Custom health check function
)

// ServiceInstance represents a single instance of a service.
// Each instance has a unique ID, network address, and metadata.
type ServiceInstance struct {
	ID         string            // Unique identifier for this instance
	Service    string            // Service name (e.g., "user-service")
	Address    string            // IP address of the instance
	Port       int               // Port number
	Metadata   map[string]string // Key-value metadata (version, region, datacenter, etc.)
	Status     ServiceStatus     // Current health status
	TTL        time.Duration     // Time-to-live for this registration
	CreatedAt  time.Time         // Registration timestamp
	LastUpdate time.Time         // Last health check update time
}

// Copy returns a deep copy of the ServiceInstance.
func (si *ServiceInstance) Copy() *ServiceInstance {
	meta := make(map[string]string, len(si.Metadata))
	for k, v := range si.Metadata {
		meta[k] = v
	}
	return &ServiceInstance{
		ID:         si.ID,
		Service:    si.Service,
		Address:    si.Address,
		Port:       si.Port,
		Metadata:   meta,
		Status:     si.Status,
		TTL:        si.TTL,
		CreatedAt:  si.CreatedAt,
		LastUpdate: si.LastUpdate,
	}
}

// String returns a human-readable representation of the service instance.
func (si *ServiceInstance) String() string {
	return fmt.Sprintf("%s[%s:%d] status=%s ttl=%v",
		si.Service, si.Address, si.Port, si.Status, si.TTL)
}

// IsExpired checks if the service instance has exceeded its TTL.
func (si *ServiceInstance) IsExpired() bool {
	return time.Since(si.LastUpdate) > si.TTL
}

// Weight represents the weight of a service instance for weighted load balancing.
func (si *ServiceInstance) Weight() int {
	if w, ok := si.Metadata["weight"]; ok {
		var weight int
		fmt.Sscanf(w, "%d", &weight)
		return weight
	}
	return 1 // Default weight is 1
}

// ActiveConnections represents the number of active connections for least-connections load balancing.
func (si *ServiceInstance) ActiveConnections() int {
	if c, ok := si.Metadata["active_connections"]; ok {
		var connections int
		fmt.Sscanf(c, "%d", &connections)
		return connections
	}
	return 0
}

// AddActiveConnection increments the active connection count.
func (si *ServiceInstance) AddActiveConnection() {
	if c, ok := si.Metadata["active_connections"]; ok {
		var connections int
		fmt.Sscanf(c, "%d", &connections)
		si.Metadata["active_connections"] = fmt.Sprintf("%d", connections+1)
	} else {
		si.Metadata["active_connections"] = "1"
	}
}

// RemoveActiveConnection decrements the active connection count.
func (si *ServiceInstance) RemoveActiveConnection() {
	if c, ok := si.Metadata["active_connections"]; ok {
		var connections int
		fmt.Sscanf(c, "%d", &connections)
		if connections > 0 {
			si.Metadata["active_connections"] = fmt.Sprintf("%d", connections-1)
		}
	}
}

// HealthCheckConfig holds configuration for health checks.
type HealthCheckConfig struct {
	Type             HealthCheckType // Type of health check
	Interval         time.Duration   // How often to perform health checks
	Timeout          time.Duration   // Maximum time to wait for health check response
	UnhealthyThreshold int           // Number of consecutive failures before marking unhealthy
	HealthyThreshold   int           // Number of consecutive successes before marking healthy
	CustomChecker      func() bool     // Custom health check function
	HTTPPath          string          // HTTP health check path (e.g., "/health")
	HTTPPort          int             // HTTP health check port (0 = use service port)
}

// LoadBalancerType represents the type of load balancing algorithm.
type LoadBalancerType string

const (
	LoadBalancerRoundRobin  LoadBalancerType = "round-robin"  // Distribute requests evenly in order
	LoadBalancerWeighted    LoadBalancerType = "weighted"      // Distribute based on instance weights
	LoadBalancerLeastConn   LoadBalancerType = "least-connections" // Route to instance with fewest connections
	LoadBalancerRandom      LoadBalancerType = "random"        // Randomly select an instance
)

// DiscoveryCache caches discovered service instances for performance.
type DiscoveryCache struct {
	instances   map[string][]*ServiceInstance // service name -> list of instances
	lastRefresh time.Time                     // When the cache was last refreshed
	ttl         time.Duration                 // How long the cache is valid
}

// NewDiscoveryCache creates a new discovery cache with the given TTL.
func NewDiscoveryCache(ttl time.Duration) *DiscoveryCache {
	return &DiscoveryCache{
		instances:   make(map[string][]*ServiceInstance),
		lastRefresh: time.Now(),
		ttl:         ttl,
	}
}

// IsExpired checks if the cache has expired.
func (dc *DiscoveryCache) IsExpired() bool {
	return time.Since(dc.lastRefresh) > dc.ttl
}

// Set stores instances for a service in the cache.
func (dc *DiscoveryCache) Set(service string, instances []*ServiceInstance) {
	dc.instances[service] = instances
	dc.lastRefresh = time.Now()
}

// Get retrieves instances for a service from the cache.
func (dc *DiscoveryCache) Get(service string) ([]*ServiceInstance, bool) {
	instances, ok := dc.instances[service]
	if !ok {
		return nil, false
	}
	return instances, true
}

// Clear removes all cached data.
func (dc *DiscoveryCache) Clear() {
	dc.instances = make(map[string][]*ServiceInstance)
	dc.lastRefresh = time.Now()
}

// ConsulKVEntry represents a key-value pair in a Consul-like KV store.
// The KV store is used for distributed coordination between service registry nodes.
type ConsulKVEntry struct {
	Key       string    // Key in the KV store
	Value     []byte    // Value stored at the key
	ModifyIndex uint64  // Monotonically increasing index (like etcd revision)
	CreateIndex uint64  // Index when the key was first created
	Flags     uint64    // Custom flags for application use
	Session   string    // Optional session ID for leases
	TTL       time.Duration // Optional TTL for auto-expiration
	CreatedAt time.Time
	UpdatedAt time.Time
}

// ConsulKVStore provides a Consul-like key-value store for distributed coordination.
// This simulates the KV store that would normally be backed by etcd or Consul.
type ConsulKVStore struct {
	entries map[string]*ConsulKVEntry
	index   uint64
	mu      interface{} // Reserved for future mutex support
}

// NewConsulKVStore creates a new Consul-like KV store.
func NewConsulKVStore() *ConsulKVStore {
	return &ConsulKVStore{
		entries: make(map[string]*ConsulKVEntry),
		index:   0,
	}
}

// Put stores a key-value pair in the KV store.
func (kv *ConsulKVStore) Put(key string, value []byte, flags uint64, session string, ttl time.Duration) (*ConsulKVEntry, error) {
	kv.index++
	entry := &ConsulKVEntry{
		Key:         key,
		Value:       value,
		ModifyIndex: kv.index,
		CreateIndex: kv.index,
		Flags:       flags,
		Session:     session,
		TTL:         ttl,
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}
	kv.entries[key] = entry
	return entry, nil
}

// Get retrieves a value by key from the KV store.
func (kv *ConsulKVStore) Get(key string) (*ConsulKVEntry, bool) {
	entry, ok := kv.entries[key]
	if !ok {
		return nil, false
	}
	return entry, true
}

// Delete removes a key from the KV store.
func (kv *ConsulKVStore) Delete(key string) bool {
	_, ok := kv.entries[key]
	if ok {
		delete(kv.entries, key)
	}
	return ok
}

// List returns all entries whose keys start with the given prefix.
func (kv *ConsulKVStore) List(prefix string) []*ConsulKVEntry {
	var result []*ConsulKVEntry
	for _, entry := range kv.entries {
		if len(entry.Key) >= len(prefix) && entry.Key[:len(prefix)] == prefix {
			result = append(result, entry)
		}
	}
	return result
}

// CompareAndSwap atomically updates a value if the modify index matches.
func (kv *ConsulKVStore) CompareAndSwap(key string, value []byte, flags uint64, expectedIndex uint64) (*ConsulKVEntry, error) {
	entry, ok := kv.entries[key]
	if !ok || entry.ModifyIndex != expectedIndex {
		return nil, fmt.Errorf("compare and swap failed: expected index %d, got %d", expectedIndex, entry.ModifyIndex)
	}
	kv.index++
	entry.Value = value
	entry.Flags = flags
	entry.ModifyIndex = kv.index
	entry.UpdatedAt = time.Now()
	return entry, nil
}

package main

import (
	"fmt"
	"sync"
	"time"
)

// ServiceBroker is the main orchestrator that ties together service
// registration, health checking, discovery, and load balancing.
//
// This is the primary API that users of this library will interact with.
// It provides a high-level interface for service discovery operations.
//
// Architecture:
//
//	ServiceBroker
//	  ├── ServiceRegistry (stores instances)
//	  ├── HealthChecker (monitors instance health)
//	  ├── DiscoveryCache (caches discovery results)
//	  └── LoadBalancerFactory (creates load balancers)
//
// Usage:
//
//	broker := NewServiceBroker(...)
//	broker.Start()
//	defer broker.Stop()
//
//	// Register a service
//	broker.Register(instance)
//
//	// Discover services
//	instances := broker.Discover("user-service")
//
//	// Get a load-balanced instance
//	inst := broker.GetNextInstance("user-service")
type ServiceBroker struct {
	registry     *ServiceRegistry
	healthChecker *HealthChecker
	cache        *DiscoveryCache
	kvStore      *ConsulKVStore
	stopCh       chan struct{}
	stopped      chan struct{}
	isRunning    bool
	mu           sync.RWMutex
}

// BrokerConfig holds configuration for the ServiceBroker.
type BrokerConfig struct {
	// Registry configuration
	RegistryTTL           time.Duration // Default TTL for registrations
	ExpirationGrace       time.Duration // Grace period after TTL expires

	// Health check configuration
	HealthCheckInterval   time.Duration // Interval between health checks
	HealthCheckTimeout    time.Duration // Timeout for each health check

	// Cache configuration
	DiscoveryCacheTTL     time.Duration // How long discovery cache is valid

	// KV store (for distributed coordination)
	UseKVStore            bool          // Enable Consul-like KV store
}

// NewServiceBroker creates a new service broker with the given configuration.
func NewServiceBroker(config *BrokerConfig) *ServiceBroker {
	if config == nil {
		config = &BrokerConfig{
			RegistryTTL:         30 * time.Second,
			ExpirationGrace:     10 * time.Second,
			HealthCheckInterval: 10 * time.Second,
			HealthCheckTimeout:  5 * time.Second,
			DiscoveryCacheTTL:   10 * time.Second,
			UseKVStore:          false,
		}
	}

	registry := NewServiceRegistry(&RegistryConfig{
		DefaultTTL:      config.RegistryTTL,
		ExpirationGrace: config.ExpirationGrace,
	})

	healthChecker := NewHealthChecker(registry)
	cache := NewDiscoveryCache(config.DiscoveryCacheTTL)

	var kvStore *ConsulKVStore
	if config.UseKVStore {
		kvStore = NewConsulKVStore()
	}

	return &ServiceBroker{
		registry:      registry,
		healthChecker: healthChecker,
		cache:         cache,
		kvStore:       kvStore,
		stopCh:        make(chan struct{}),
		stopped:       make(chan struct{}),
	}
}

// Start initializes and starts all components.
func (sb *ServiceBroker) Start() {
	sb.mu.Lock()
	if sb.isRunning {
		sb.mu.Unlock()
		return
	}
	sb.isRunning = true
	sb.mu.Unlock()

	sb.healthChecker.Start()

	// Start expiration checker goroutine
	go sb.expireLoop()

	fmt.Println("[ServiceBroker] Started")
}

// Stop gracefully shuts down all components.
func (sb *ServiceBroker) Stop() {
	sb.mu.Lock()
	if !sb.isRunning {
		sb.mu.Unlock()
		return
	}
	sb.mu.Unlock()

	close(sb.stopCh)
	<-sb.stopped
	fmt.Println("[ServiceBroker] Stopped")
}

// Register registers a service instance with the broker.
// This performs registration, health check setup, and KV store sync.
func (sb *ServiceBroker) Register(instance *ServiceInstance) error {
	// Register in the service registry
	if err := sb.registry.Register(instance); err != nil {
		return err
	}

	// Register health check (default to TCP)
	config := HealthCheckConfig{
		Type:    HealthCheckTCP,
		Interval: 10 * time.Second,
		Timeout:  5 * time.Second,
	}
	sb.healthChecker.RegisterCheck(instance.ID, config)

	// Sync to KV store if enabled
	if sb.kvStore != nil {
		key := fmt.Sprintf("services/%s/%s", instance.Service, instance.ID)
		value := []byte(fmt.Sprintf("%s:%d", instance.Address, instance.Port))
		sb.kvStore.Put(key, value, 0, instance.ID, instance.TTL)
	}

	// Invalidate cache for this service
	sb.cache.Set(instance.Service, nil)

	return nil
}

// Deregister removes a service instance from the broker.
func (sb *ServiceBroker) Deregister(instanceID string) {
	sb.healthChecker.UnregisterCheck(instanceID)
	sb.registry.Deregister(instanceID)

	if sb.kvStore != nil {
		// Find and delete from KV store
		key := fmt.Sprintf("services/%s/", instanceID)
		for _, entry := range sb.kvStore.List(key) {
			sb.kvStore.Delete(entry.Key)
		}
	}
}

// Discover retrieves all healthy instances for a given service.
// Uses caching to reduce registry lookups.
func (sb *ServiceBroker) Discover(service string) []*ServiceInstance {
	// Check cache first
	if !sb.cache.IsExpired() {
		if instances, ok := sb.cache.Get(service); ok && instances != nil {
			return instances
		}
	}

	// Query the registry
	instances := sb.registry.GetInstancesByService(service)

	// Update cache
	sb.cache.Set(service, instances)

	return instances
}

// GetNextInstance returns the next instance for a service using load balancing.
func (sb *ServiceBroker) GetNextInstance(service string, strategy LoadBalancerType) *ServiceInstance {
	instances := sb.Discover(service)
	if len(instances) == 0 {
		return nil
	}

	lb := NewLoadBalancer(strategy)
	lb.SetInstances(instances)
	return lb.Next()
}

// GetNextInstanceRR returns the next instance using round-robin load balancing.
func (sb *ServiceBroker) GetNextInstanceRR(service string) *ServiceInstance {
	return sb.GetNextInstance(service, LoadBalancerRoundRobin)
}

// GetNextInstanceWeighted returns the next instance using weighted load balancing.
func (sb *ServiceBroker) GetNextInstanceWeighted(service string) *ServiceInstance {
	return sb.GetNextInstance(service, LoadBalancerWeighted)
}

// GetNextInstanceLeastConn returns the next instance using least-connections load balancing.
func (sb *ServiceBroker) GetNextInstanceLeastConn(service string) *ServiceInstance {
	return sb.GetNextInstance(service, LoadBalancerLeastConn)
}

// GetNextInstanceRandom returns the next instance using random load balancing.
func (sb *ServiceBroker) GetNextInstanceRandom(service string) *ServiceInstance {
	return sb.GetNextInstance(service, LoadBalancerRandom)
}

// expireLoop periodically expires stale instances.
func (sb *ServiceBroker) expireLoop() {
	defer close(sb.stopped)

	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-sb.stopCh:
			return
		case <-ticker.C:
			count := sb.registry.ExpireStaleInstances()
			if count > 0 {
				fmt.Printf("[ServiceBroker] Expired %d stale instances\n", count)
			}
		}
	}
}

// Registry returns the underlying service registry for direct access.
func (sb *ServiceBroker) Registry() *ServiceRegistry {
	return sb.registry
}

// HealthChecker returns the underlying health checker for direct access.
func (sb *ServiceBroker) HealthChecker() *HealthChecker {
	return sb.healthChecker
}

// PrintStatus prints the current state of the service broker.
func (sb *ServiceBroker) PrintStatus() {
	fmt.Println("=== Service Broker Status ===")
	fmt.Printf("Registry: %d services, %d instances\n",
		sb.registry.GetServiceCount(), sb.registry.GetInstanceCount())

	if sb.cache.IsExpired() {
		fmt.Println("Cache: expired")
	} else {
		fmt.Println("Cache: active")
	}

	if sb.kvStore != nil {
		fmt.Printf("KV Store: %d entries\n", len(sb.kvStore.List("")))
	}

	sb.registry.PrintStatus()
}

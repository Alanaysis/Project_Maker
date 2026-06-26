package main

import (
	"fmt"
	"sync"
	"time"
)

// ServiceRegistry manages the registration and lookup of service instances.
//
// The service registry is the core component of service discovery. It acts as
// a directory of available services and their network locations.
//
// Key responsibilities:
//   - Register new service instances
//   - Deregister service instances
//   - Track service instance health status
//   - Expire stale registrations based on TTL
//   - Provide lookup of healthy instances by service name
//
// Thread safety: All public methods are safe for concurrent use.
type ServiceRegistry struct {
	mu            sync.RWMutex
	instances     map[string]*ServiceInstance // instance ID -> instance
	serviceIndex  map[string]map[string]bool  // service name -> set of instance IDs
	ttl           time.Duration               // default TTL for registrations
	expireHandler func(string)                // callback when instance expires
}

// RegistryConfig holds configuration for the ServiceRegistry.
type RegistryConfig struct {
	DefaultTTL      time.Duration // Default TTL for service registrations
	ExpirationGrace time.Duration // Additional grace period after TTL expires
	ExpireHandler   func(string)  // Callback when an instance expires
}

// NewServiceRegistry creates a new service registry with the given configuration.
// If config is nil, sensible defaults are used:
//
//	DefaultTTL = 30s, ExpirationGrace = 10s
func NewServiceRegistry(config *RegistryConfig) *ServiceRegistry {
	if config == nil {
		config = &RegistryConfig{
			DefaultTTL:      30 * time.Second,
			ExpirationGrace: 10 * time.Second,
		}
	}
	return &ServiceRegistry{
		instances:    make(map[string]*ServiceInstance),
		serviceIndex: make(map[string]map[string]bool),
		ttl:          config.DefaultTTL,
		expireHandler: config.ExpireHandler,
	}
}

// Register adds a new service instance to the registry.
// If the instance already exists, it will be updated with new metadata.
//
// Registration flow:
//   1. Validate the instance
//   2. Add to instances map and service index
//   3. Set initial status to healthy
//   4. Update timestamps
func (sr *ServiceRegistry) Register(instance *ServiceInstance) error {
	sr.mu.Lock()
	defer sr.mu.Unlock()

	if instance == nil {
		return fmt.Errorf("cannot register nil instance")
	}
	if instance.Service == "" {
		return fmt.Errorf("service name cannot be empty")
	}
	if instance.Address == "" {
		return fmt.Errorf("address cannot be empty")
	}
	if instance.Port <= 0 {
		return fmt.Errorf("port must be positive")
	}

	// Set default TTL if not specified
	if instance.TTL == 0 {
		instance.TTL = sr.ttl
	}

	isNew := false
	if _, exists := sr.instances[instance.ID]; !exists {
		isNew = true
		// Initialize service index
		if sr.serviceIndex[instance.Service] == nil {
			sr.serviceIndex[instance.Service] = make(map[string]bool)
		}
	}

	instance.Status = StatusHealthy
	instance.LastUpdate = time.Now()

	sr.instances[instance.ID] = instance
	sr.serviceIndex[instance.Service][instance.ID] = true

	if isNew {
		fmt.Printf("[Registry] Registered: %s\n", instance.String())
	} else {
		fmt.Printf("[Registry] Re-registered: %s\n", instance.String())
	}

	return nil
}

// Deregister removes a service instance from the registry.
// Returns true if the instance was found and removed.
func (sr *ServiceRegistry) Deregister(instanceID string) bool {
	sr.mu.Lock()
	defer sr.mu.Unlock()

	instance, exists := sr.instances[instanceID]
	if !exists {
		return false
	}

	service := instance.Service
	delete(sr.instances, instanceID)
	delete(sr.serviceIndex[service], instanceID)

	// Clean up empty service entries
	if len(sr.serviceIndex[service]) == 0 {
		delete(sr.serviceIndex, service)
	}

	fmt.Printf("[Registry] Deregistered: %s (id=%s)\n", service, instanceID)
	return true
}

// GetInstance retrieves a specific service instance by ID.
func (sr *ServiceRegistry) GetInstance(instanceID string) (*ServiceInstance, bool) {
	sr.mu.RLock()
	defer sr.mu.RUnlock()

	instance, exists := sr.instances[instanceID]
	if !exists {
		return nil, false
	}
	return instance.Copy(), true
}

// GetInstancesByService retrieves all healthy instances for a given service.
// This is the core service discovery query.
func (sr *ServiceRegistry) GetInstancesByService(service string) []*ServiceInstance {
	sr.mu.RLock()
	defer sr.mu.RUnlock()

	instanceIDs, exists := sr.serviceIndex[service]
	if !exists {
		return nil
	}

	var instances []*ServiceInstance
	for id := range instanceIDs {
		instance := sr.instances[id]
		// Only return healthy instances
		if instance.Status == StatusHealthy && !instance.IsExpired() {
			instances = append(instances, instance.Copy())
		}
	}

	return instances
}

// GetAllServices returns a list of all registered service names.
func (sr *ServiceRegistry) GetAllServices() []string {
	sr.mu.RLock()
	defer sr.mu.RUnlock()

	services := make([]string, 0, len(sr.serviceIndex))
	for service := range sr.serviceIndex {
		services = append(services, service)
	}
	return services
}

// GetServiceCount returns the number of registered services.
func (sr *ServiceRegistry) GetServiceCount() int {
	sr.mu.RLock()
	defer sr.mu.RUnlock()
	return len(sr.serviceIndex)
}

// GetInstanceCount returns the total number of registered instances.
func (sr *ServiceRegistry) GetInstanceCount() int {
	sr.mu.RLock()
	defer sr.mu.RUnlock()
	return len(sr.instances)
}

// UpdateHealth updates the health status of a service instance.
// This is called by the health checker after each health check.
func (sr *ServiceRegistry) UpdateHealth(instanceID string, healthy bool) {
	sr.mu.Lock()
	defer sr.mu.Unlock()

	instance, exists := sr.instances[instanceID]
	if !exists {
		return
	}

	if healthy {
		instance.Status = StatusHealthy
	} else {
		instance.Status = StatusUnhealthy
	}
	instance.LastUpdate = time.Now()
}

// ExpireStaleInstances removes instances that have exceeded their TTL.
// This should be called periodically by a background goroutine.
func (sr *ServiceRegistry) ExpireStaleInstances() int {
	sr.mu.Lock()
	defer sr.mu.Unlock()

	count := 0
	now := time.Now()

	for id, instance := range sr.instances {
		// Check if instance has exceeded TTL + grace period
		if now.Sub(instance.LastUpdate) > instance.TTL+sr.ttl/2 {
			delete(sr.instances, id)
			delete(sr.serviceIndex[instance.Service], id)

			if len(sr.serviceIndex[instance.Service]) == 0 {
				delete(sr.serviceIndex, instance.Service)
			}

			count++
			fmt.Printf("[Registry] Expired: %s (id=%s)\n", instance.Service, id)

			if sr.expireHandler != nil {
				sr.expireHandler(id)
			}
		}
	}

	return count
}

// RefreshInstance updates the last update time of an instance (heartbeat).
func (sr *ServiceRegistry) RefreshInstance(instanceID string) bool {
	sr.mu.Lock()
	defer sr.mu.Unlock()

	instance, exists := sr.instances[instanceID]
	if !exists {
		return false
	}

	instance.LastUpdate = time.Now()
	return true
}

// PrintStatus prints the current state of the registry for debugging.
func (sr *ServiceRegistry) PrintStatus() {
	sr.mu.RLock()
	defer sr.mu.RUnlock()

	fmt.Println("=== Service Registry Status ===")
	fmt.Printf("Total services: %d\n", len(sr.serviceIndex))
	fmt.Printf("Total instances: %d\n", len(sr.instances))
	fmt.Println()

	for service, instanceIDs := range sr.serviceIndex {
		fmt.Printf("Service: %s (%d instances)\n", service, len(instanceIDs))
		for id := range instanceIDs {
			instance := sr.instances[id]
			fmt.Printf("  - %s [%s:%d] status=%s\n",
				id, instance.Address, instance.Port, instance.Status)
		}
		fmt.Println()
	}
}

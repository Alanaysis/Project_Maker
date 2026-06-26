package service_discovery

import (
	"testing"
	"time"
)

// TestServiceInstance tests basic ServiceInstance operations.
func TestServiceInstance(t *testing.T) {
	instance := &ServiceInstance{
		ID:       "test-1",
		Service:  "test-service",
		Address:  "127.0.0.1",
		Port:     8080,
		Metadata: map[string]string{"version": "1.0"},
		Status:   StatusHealthy,
		TTL:      30 * time.Second,
		CreatedAt: time.Now(),
		LastUpdate: time.Now(),
	}

	// Test Copy
	copy := instance.Copy()
	if copy.ID != instance.ID {
		t.Errorf("Copy: expected ID %s, got %s", instance.ID, copy.ID)
	}
	if copy.Metadata["version"] != "1.0" {
		t.Error("Copy: metadata not copied correctly")
	}
	// Verify deep copy
	copy.Metadata["version"] = "2.0"
	if instance.Metadata["version"] == "2.0" {
		t.Error("Copy: metadata should be deep copied")
	}

	// Test String
	s := instance.String()
	if s == "" {
		t.Error("String: should not be empty")
	}

	// Test Weight
	if instance.Weight() != 1 {
		t.Errorf("Weight: expected default weight 1, got %d", instance.Weight())
	}

	// Test Weight with custom value
	instanceWithWeight := &ServiceInstance{
		ID:       "test-2",
		Service:  "test-service",
		Address:  "127.0.0.1",
		Port:     8080,
		Metadata: map[string]string{"weight": "5"},
		Status:   StatusHealthy,
		TTL:      30 * time.Second,
		CreatedAt: time.Now(),
		LastUpdate: time.Now(),
	}
	if instanceWithWeight.Weight() != 5 {
		t.Errorf("Weight: expected 5, got %d", instanceWithWeight.Weight())
	}

	// Test ActiveConnections
	if instance.ActiveConnections() != 0 {
		t.Errorf("ActiveConnections: expected 0, got %d", instance.ActiveConnections())
	}

	// Test AddActiveConnection
	instance.AddActiveConnection()
	if instance.ActiveConnections() != 1 {
		t.Errorf("AddActiveConnection: expected 1, got %d", instance.ActiveConnections())
	}

	// Test RemoveActiveConnection
	instance.RemoveActiveConnection()
	if instance.ActiveConnections() != 0 {
		t.Errorf("RemoveActiveConnection: expected 0, got %d", instance.ActiveConnections())
	}
}

// TestServiceInstanceExpiration tests TTL-based expiration.
func TestServiceInstanceExpiration(t *testing.T) {
	instance := &ServiceInstance{
		ID:         "test-exp",
		Service:    "test-service",
		Address:    "127.0.0.1",
		Port:       8080,
		Metadata:   map[string]string{},
		Status:     StatusHealthy,
		TTL:        1 * time.Second,
		CreatedAt:  time.Now().Add(-2 * time.Second),
		LastUpdate: time.Now().Add(-2 * time.Second),
	}

	if !instance.IsExpired() {
		t.Error("IsExpired: expected true for stale instance")
	}

	freshInstance := &ServiceInstance{
		ID:         "test-fresh",
		Service:    "test-service",
		Address:    "127.0.0.1",
		Port:       8080,
		Metadata:   map[string]string{},
		Status:     StatusHealthy,
		TTL:        30 * time.Second,
		CreatedAt:  time.Now(),
		LastUpdate: time.Now(),
	}

	if freshInstance.IsExpired() {
		t.Error("IsExpired: expected false for fresh instance")
	}
}

// TestServiceRegistry tests basic registry operations.
func TestServiceRegistry(t *testing.T) {
	registry := NewServiceRegistry(&RegistryConfig{
		DefaultTTL:      30 * time.Second,
		ExpirationGrace: 10 * time.Second,
	})

	// Test Register
	instance := &ServiceInstance{
		ID:       "reg-test-1",
		Service:  "test-service",
		Address:  "127.0.0.1",
		Port:     8080,
		Metadata: map[string]string{"version": "1.0"},
		TTL:      30 * time.Second,
	}

	if err := registry.Register(instance); err != nil {
		t.Fatalf("Register: unexpected error: %v", err)
	}

	if registry.GetInstanceCount() != 1 {
		t.Errorf("GetInstanceCount: expected 1, got %d", registry.GetInstanceCount())
	}

	// Test GetInstance
	retrieved, ok := registry.GetInstance("reg-test-1")
	if !ok {
		t.Error("GetInstance: instance not found")
	}
	if retrieved.Service != "test-service" {
		t.Errorf("GetInstance: expected service 'test-service', got '%s'", retrieved.Service)
	}

	// Test GetInstancesByService
	instances := registry.GetInstancesByService("test-service")
	if len(instances) != 1 {
		t.Errorf("GetInstancesByService: expected 1 instance, got %d", len(instances))
	}

	// Test GetInstancesByService for non-existent service
	instances = registry.GetInstancesByService("non-existent")
	if len(instances) != 0 {
		t.Errorf("GetInstancesByService: expected 0 instances, got %d", len(instances))
	}

	// Test Deregister
	if !registry.Deregister("reg-test-1") {
		t.Error("Deregister: should return true for existing instance")
	}
	if registry.GetInstanceCount() != 0 {
		t.Errorf("GetInstanceCount: expected 0 after deregister, got %d", registry.GetInstanceCount())
	}

	// Test Deregister non-existent
	if registry.Deregister("non-existent") {
		t.Error("Deregister: should return false for non-existent instance")
	}

	// Test GetServiceCount
	if registry.GetServiceCount() != 0 {
		t.Errorf("GetServiceCount: expected 0, got %d", registry.GetServiceCount())
	}
}

// TestServiceRegistryValidation tests registry validation.
func TestServiceRegistryValidation(t *testing.T) {
	registry := NewServiceRegistry(nil)

	// Test nil instance
	if err := registry.Register(nil); err == nil {
		t.Error("Register: should reject nil instance")
	}

	// Test empty service name
	instance := &ServiceInstance{
		ID:       "test-1",
		Service:  "",
		Address:  "127.0.0.1",
		Port:     8080,
		Metadata: map[string]string{},
		TTL:      30 * time.Second,
	}
	if err := registry.Register(instance); err == nil {
		t.Error("Register: should reject empty service name")
	}

	// Test empty address
	instance.Service = "test-service"
	instance.Address = ""
	if err := registry.Register(instance); err == nil {
		t.Error("Register: should reject empty address")
	}

	// Test invalid port
	instance.Address = "127.0.0.1"
	instance.Port = 0
	if err := registry.Register(instance); err == nil {
		t.Error("Register: should reject invalid port")
	}
}

// TestServiceRegistryHealthUpdate tests health status updates.
func TestServiceRegistryHealthUpdate(t *testing.T) {
	registry := NewServiceRegistry(nil)

	instance := &ServiceInstance{
		ID:       "health-test-1",
		Service:  "test-service",
		Address:  "127.0.0.1",
		Port:     8080,
		Metadata: map[string]string{},
		TTL:      30 * time.Second,
	}
	registry.Register(instance)

	// Update to unhealthy
	registry.UpdateHealth("health-test-1", false)
	retrieved, _ := registry.GetInstance("health-test-1")
	if retrieved.Status != StatusUnhealthy {
		t.Errorf("UpdateHealth: expected unhealthy, got %s", retrieved.Status)
	}

	// Update to healthy
	registry.UpdateHealth("health-test-1", true)
	retrieved, _ = registry.GetInstance("health-test-1")
	if retrieved.Status != StatusHealthy {
		t.Errorf("UpdateHealth: expected healthy, got %s", retrieved.Status)
	}

	// Update non-existent instance (should not panic)
	registry.UpdateHealth("non-existent", true)
}

// TestServiceRegistryExpiration tests TTL-based expiration.
func TestServiceRegistryExpiration(t *testing.T) {
	registry := NewServiceRegistry(&RegistryConfig{
		DefaultTTL:      100 * time.Millisecond,
		ExpirationGrace: 50 * time.Millisecond,
	})

	instance := &ServiceInstance{
		ID:         "exp-test-1",
		Service:    "test-service",
		Address:    "127.0.0.1",
		Port:       8080,
		Metadata:   map[string]string{},
		TTL:        100 * time.Millisecond,
		LastUpdate: time.Now().Add(-200 * time.Millisecond),
	}
	registry.Register(instance)

	// Instance should still be there
	if registry.GetInstanceCount() != 1 {
		t.Error("Expected 1 instance before expiration")
	}

	// Wait for expiration
	time.Sleep(200 * time.Millisecond)

	// Expire stale instances
	count := registry.ExpireStaleInstances()
	if count != 1 {
		t.Errorf("ExpireStaleInstances: expected 1 expired, got %d", count)
	}

	if registry.GetInstanceCount() != 0 {
		t.Errorf("Expected 0 instances after expiration, got %d", registry.GetInstanceCount())
	}
}

// TestRefreshInstance tests the heartbeat mechanism.
func TestRefreshInstance(t *testing.T) {
	registry := NewServiceRegistry(nil)

	instance := &ServiceInstance{
		ID:       "refresh-test-1",
		Service:  "test-service",
		Address:  "127.0.0.1",
		Port:     8080,
		Metadata: map[string]string{},
		TTL:      30 * time.Second,
	}
	registry.Register(instance)

	// Refresh the instance
	if !registry.RefreshInstance("refresh-test-1") {
		t.Error("RefreshInstance: should return true for existing instance")
	}

	// Refresh non-existent instance
	if registry.RefreshInstance("non-existent") {
		t.Error("RefreshInstance: should return false for non-existent instance")
	}
}

// TestGetAllServices tests getting all registered services.
func TestGetAllServices(t *testing.T) {
	registry := NewServiceRegistry(nil)

	// Empty registry
	services := registry.GetAllServices()
	if len(services) != 0 {
		t.Errorf("GetAllServices: expected 0 services, got %d", len(services))
	}

	// Register services
	instance1 := &ServiceInstance{
		ID:       "svc-test-1",
		Service:  "service-a",
		Address:  "127.0.0.1",
		Port:     8080,
		Metadata: map[string]string{},
		TTL:      30 * time.Second,
	}
	instance2 := &ServiceInstance{
		ID:       "svc-test-2",
		Service:  "service-b",
		Address:  "127.0.0.1",
		Port:     8081,
		Metadata: map[string]string{},
		TTL:      30 * time.Second,
	}
	registry.Register(instance1)
	registry.Register(instance2)

	services = registry.GetAllServices()
	if len(services) != 2 {
		t.Errorf("GetAllServices: expected 2 services, got %d", len(services))
	}
}

// Package main demonstrates the health check mechanism.
//
// Health checking ensures that only healthy service instances receive traffic.
// This example shows:
//  1. TCP health checks (connection-based)
//  2. HTTP health checks (endpoint-based)
//  3. Custom health checks (user-defined)
//  4. Health status transitions (healthy -> unhealthy -> healthy)
//
// In production, health checks run continuously in the background.
// When an instance fails enough consecutive checks, it's marked unhealthy
// and removed from the discovery pool.
package main

import (
	"fmt"
	"net/http"
	"sync"
	"time"

	"service-discovery/src"
)

func main() {
	fmt.Println("=== Health Check Demo ===")
	fmt.Println()

	// Create registry and health checker
	registry := service_discovery.NewServiceRegistry(&service_discovery.RegistryConfig{
		DefaultTTL:      30 * time.Second,
		ExpirationGrace: 10 * time.Second,
	})
	healthChecker := service_discovery.NewHealthChecker(registry)

	// Start the health checker
	healthChecker.Start()
	defer healthChecker.Stop()

	fmt.Println("--- Step 1: Register Service Instances ---")
	fmt.Println()

	// Register a service with an HTTP health endpoint
	instance1 := &service_discovery.ServiceInstance{
		ID:       "http-svc-1",
		Service:  "http-service",
		Address:  "127.0.0.1",
		Port:     8888,
		Metadata: map[string]string{"version": "1.0"},
		TTL:      30 * time.Second,
	}
	registry.Register(instance1)

	// Register a service with TCP health check
	instance2 := &service_discovery.ServiceInstance{
		ID:       "tcp-svc-1",
		Service:  "tcp-service",
		Address:  "127.0.0.1",
		Port:     9999,
		Metadata: map[string]string{"version": "1.0"},
		TTL:      30 * time.Second,
	}
	registry.Register(instance2)

	// Register a service with custom health check
	instance3 := &service_discovery.ServiceInstance{
		ID:       "custom-svc-1",
		Service:  "custom-service",
		Address:  "127.0.0.1",
		Port:     7777,
		Metadata: map[string]string{"version": "1.0"},
		TTL:      30 * time.Second,
	}
	registry.Register(instance3)

	fmt.Println()
	fmt.Println("--- Step 2: Register Health Checks ---")
	fmt.Println()

	// Register HTTP health check for instance1
	healthChecker.RegisterCheck(instance1.ID, service_discovery.HealthCheckConfig{
		Type:     service_discovery.HealthCheckHTTP,
		Interval: 5 * time.Second,
		Timeout:  3 * time.Second,
		HTTPPath: "/health",
		HTTPPort: 8888,
	})

	// Register TCP health check for instance2
	healthChecker.RegisterCheck(instance2.ID, service_discovery.HealthCheckConfig{
		Type:     service_discovery.HealthCheckTCP,
		Interval: 5 * time.Second,
		Timeout:  3 * time.Second,
	})

	// Register custom health check for instance3 (always healthy)
	alwaysHealthy := true
	healthChecker.RegisterCheck(instance3.ID, service_discovery.HealthCheckConfig{
		Type: service_discovery.HealthCheckCustom,
		Interval: 5 * time.Second,
		CustomChecker: func() bool {
			return alwaysHealthy
		},
	})

	fmt.Println()
	fmt.Println("--- Step 3: HTTP Health Check Setup ---")
	fmt.Println()

	// Start a simple HTTP health endpoint for demonstration
	var mu sync.Mutex
	healthy := true
	go func() {
		http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
			mu.Lock()
			defer mu.Unlock()
			if healthy {
				w.WriteHeader(http.StatusOK)
				w.Write([]byte("OK"))
			} else {
				w.WriteHeader(http.StatusServiceUnavailable)
				w.Write([]byte("FAIL"))
			}
		})
		http.ListenAndServe(":8888", nil)
	}()

	time.Sleep(500 * time.Millisecond)
	fmt.Println("HTTP health endpoint started on :8888")
	fmt.Println()

	// Wait for health checks to run
	fmt.Println("--- Step 4: Waiting for Health Checks ---")
	fmt.Println()
	time.Sleep(12 * time.Second)

	// Check the status of each instance
	fmt.Println("--- Step 5: Check Instance Status ---")
	fmt.Println()
	for _, id := range []string{instance1.ID, instance2.ID, instance3.ID} {
		inst, exists := registry.GetInstance(id)
		if exists {
			fmt.Printf("Instance %s: status=%s\n", id, inst.Status)
		} else {
			fmt.Printf("Instance %s: not found\n", id)
		}
	}

	fmt.Println()
	fmt.Println("--- Step 6: Simulate Service Failure ---")
	fmt.Println()

	// Simulate the HTTP service going down
	mu.Lock()
	healthy = false
	mu.Unlock()
	fmt.Println("HTTP service health endpoint now returns 503")
	fmt.Println()

	// Wait for health checks to detect the failure
	fmt.Println("--- Step 7: Waiting for Failure Detection ---")
	fmt.Println()
	time.Sleep(12 * time.Second)

	// Check the status again
	fmt.Println("--- Step 8: Check Instance Status After Failure ---")
	fmt.Println()
	for _, id := range []string{instance1.ID, instance2.ID, instance3.ID} {
		inst, exists := registry.GetInstance(id)
		if exists {
			fmt.Printf("Instance %s: status=%s\n", id, inst.Status)
		} else {
			fmt.Printf("Instance %s: not found\n", id)
		}
	}

	fmt.Println()
	fmt.Println("--- Step 9: Simulate Service Recovery ---")
	fmt.Println()

	// Bring the service back up
	mu.Lock()
	healthy = true
	mu.Unlock()
	fmt.Println("HTTP service health endpoint now returns 200")
	fmt.Println()

	// Wait for health checks to detect recovery
	fmt.Println("--- Step 10: Waiting for Recovery Detection ---")
	fmt.Println()
	time.Sleep(12 * time.Second)

	// Check the status again
	fmt.Println("--- Step 11: Check Instance Status After Recovery ---")
	fmt.Println()
	for _, id := range []string{instance1.ID, instance2.ID, instance3.ID} {
		inst, exists := registry.GetInstance(id)
		if exists {
			fmt.Printf("Instance %s: status=%s\n", id, inst.Status)
		} else {
			fmt.Printf("Instance %s: not found\n", id)
		}
	}

	fmt.Println()
	fmt.Println("Demo complete!")
}

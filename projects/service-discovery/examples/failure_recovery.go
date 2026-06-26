// Package main demonstrates service failure and recovery.
//
// This example simulates the full lifecycle of a service instance:
//  1. Service starts and registers
//  2. Service is healthy and receiving traffic
//  3. Service fails (simulated)
//  4. Health checker detects the failure
//  5. Service is removed from discovery
//  6. Service recovers and re-registers
//  7. Service is back in the discovery pool
//
// This demonstrates the core resilience pattern in microservices:
// automatic failure detection and recovery.
package main

import (
	"fmt"
	"time"

	"service-discovery/src"
)

func main() {
	fmt.Println("=== Service Failure & Recovery Demo ===")
	fmt.Println()

	// Create broker
	broker := service_discovery.NewServiceBroker(&service_discovery.BrokerConfig{
		RegistryTTL:         10 * time.Second,
		ExpirationGrace:     5 * time.Second,
		HealthCheckInterval: 3 * time.Second,
		HealthCheckTimeout:  2 * time.Second,
		DiscoveryCacheTTL:   5 * time.Second,
	})

	broker.Start()
	defer broker.Stop()

	fmt.Println("--- Phase 1: Service Registration ---")
	fmt.Println()

	// Register a service instance
	instance := &service_discovery.ServiceInstance{
		ID:       "app-svc-1",
		Service:  "app-service",
		Address:  "127.0.0.1",
		Port:     8080,
		Metadata: map[string]string{"version": "1.0", "status": "healthy"},
		TTL:      10 * time.Second,
	}

	broker.Register(instance)
	fmt.Println("Instance registered and marked healthy")
	fmt.Println()

	// Simulate a TCP health check endpoint using a custom checker
	var checkHealthy = true
	broker.HealthChecker().RegisterCheck(instance.ID, service_discovery.HealthCheckConfig{
		Type: service_discovery.HealthCheckCustom,
		Interval: 3 * time.Second,
		CustomChecker: func() bool {
			return checkHealthy
		},
	})

	fmt.Println("--- Phase 2: Normal Operation ---")
	fmt.Println()

	// Simulate normal operation: discover and use the service
	for i := 0; i < 3; i++ {
		inst := broker.GetNextInstanceRR("app-service")
		if inst != nil {
			fmt.Printf("Request %d -> %s (status: %s)\n", i+1, inst.String(), inst.Status)
		}
		time.Sleep(100 * time.Millisecond)
	}

	fmt.Println()
	fmt.Println("--- Phase 3: Simulating Service Failure ---")
	fmt.Println()

	// Simulate the service failing
	checkHealthy = false
	fmt.Println("Service instance has failed (custom health check returns false)")
	fmt.Println("Waiting for health checker to detect the failure...")
	time.Sleep(5 * time.Second)

	// Check the status
	inst, _ := broker.Registry().GetInstance(instance.ID)
	fmt.Printf("Instance status after failure: %s\n", inst.Status)
	fmt.Println()

	fmt.Println("--- Phase 4: Service Not Discovered ---")
	fmt.Println()

	// Try to discover the service - should not find the failed instance
	discovered := broker.Discover("app-service")
	fmt.Printf("Discovered instances: %d\n", len(discovered))
	if len(discovered) == 0 {
		fmt.Println("  (No healthy instances available - service is down)")
	}
	fmt.Println()

	fmt.Println("--- Phase 5: Service Recovery ---")
	fmt.Println()

	// Simulate the service recovering
	checkHealthy = true
	fmt.Println("Service instance has recovered (custom health check returns true)")
	fmt.Println("Waiting for health checker to detect recovery...")
	time.Sleep(5 * time.Second)

	// Check the status again
	inst, _ = broker.Registry().GetInstance(instance.ID)
	fmt.Printf("Instance status after recovery: %s\n", inst.Status)
	fmt.Println()

	fmt.Println("--- Phase 6: Service Discovered Again ---")
	fmt.Println()

	// Discover the service again - should find the recovered instance
	discovered = broker.Discover("app-service")
	fmt.Printf("Discovered instances: %d\n", len(discovered))
	for _, inst := range discovered {
		fmt.Printf("  - %s (status: %s)\n", inst.String(), inst.Status)
	}
	fmt.Println()

	fmt.Println("--- Phase 7: Service Deregistration ---")
	fmt.Println()

	// Deregister the service
	fmt.Println("Deregistering service instance...")
	broker.Deregister(instance.ID)

	// Try to discover again
	discovered = broker.Discover("app-service")
	fmt.Printf("Discovered instances after deregistration: %d\n", len(discovered))
	fmt.Println()

	fmt.Println("Demo complete!")
}

// Helper: access health checker (using reflection-like approach since it's unexported)
// In a real implementation, this would be a proper getter method.

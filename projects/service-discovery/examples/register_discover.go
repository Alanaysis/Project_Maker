// Package main demonstrates service registration and discovery.
//
// This example shows the core flow of service discovery:
//  1. Services register themselves with the registry
//  2. Clients discover available instances for a service
//  3. The registry returns healthy instances
//
// In a real system, services would register themselves on startup
// and deregister on shutdown. Clients would periodically discover
// new instances as they become available.
package main

import (
	"fmt"
	"time"

	"service-discovery/src"
)

func main() {
	fmt.Println("=== Service Registration & Discovery Demo ===")
	fmt.Println()

	// Create a service broker (the main orchestrator)
	broker := service_discovery.NewServiceBroker(&service_discovery.BrokerConfig{
		RegistryTTL:         30 * time.Second,
		ExpirationGrace:     10 * time.Second,
		HealthCheckInterval: 10 * time.Second,
		HealthCheckTimeout:  5 * time.Second,
		DiscoveryCacheTTL:   10 * time.Second,
	})

	broker.Start()
	defer broker.Stop()

	fmt.Println("--- Step 1: Register Service Instances ---")
	fmt.Println()

	// Simulate registering multiple instances of "user-service"
	instances := []*service_discovery.ServiceInstance{
		{
			ID:       "user-svc-1",
			Service:  "user-service",
			Address:  "192.168.1.10",
			Port:     8080,
			Metadata: map[string]string{"version": "1.0", "region": "us-east-1"},
			TTL:      30 * time.Second,
		},
		{
			ID:       "user-svc-2",
			Service:  "user-service",
			Address:  "192.168.1.11",
			Port:     8080,
			Metadata: map[string]string{"version": "1.0", "region": "us-west-2"},
			TTL:      30 * time.Second,
		},
		{
			ID:       "user-svc-3",
			Service:  "user-service",
			Address:  "192.168.1.12",
			Port:     8081,
			Metadata: map[string]string{"version": "1.1", "region": "eu-west-1"},
			TTL:      30 * time.Second,
		},
	}

	for _, inst := range instances {
		broker.Register(inst)
	}

	fmt.Println()
	fmt.Println("--- Step 2: Discover Service Instances ---")
	fmt.Println()

	// Discover all healthy instances for "user-service"
	discovered := broker.Discover("user-service")
	fmt.Printf("Discovered %d instances for 'user-service':\n", len(discovered))
	for _, inst := range discovered {
		fmt.Printf("  - %s\n", inst.String())
	}

	fmt.Println()
	fmt.Println("--- Step 3: Register Another Service ---")
	fmt.Println()

	// Register "order-service" instances
	orderInstances := []*service_discovery.ServiceInstance{
		{
			ID:       "order-svc-1",
			Service:  "order-service",
			Address:  "192.168.1.20",
			Port:     9090,
			Metadata: map[string]string{"version": "2.0", "region": "us-east-1"},
			TTL:      30 * time.Second,
		},
		{
			ID:       "order-svc-2",
			Service:  "order-service",
			Address:  "192.168.1.21",
			Port:     9090,
			Metadata: map[string]string{"version": "2.0", "region": "us-east-1"},
			TTL:      30 * time.Second,
		},
	}

	for _, inst := range orderInstances {
		broker.Register(inst)
	}

	fmt.Println()
	fmt.Println("--- Step 4: Discover Services ---")
	fmt.Println()

	// Discover both services
	for _, svc := range []string{"user-service", "order-service"} {
		instances := broker.Discover(svc)
		fmt.Printf("Service '%s': %d instances\n", svc, len(instances))
		for _, inst := range instances {
			fmt.Printf("  - %s\n", inst.String())
		}
	}

	fmt.Println()
	fmt.Println("--- Step 5: Get Load-Balanced Instance ---")
	fmt.Println()

	// Get a single instance using round-robin
	for i := 0; i < 5; i++ {
		inst := broker.GetNextInstanceRR("user-service")
		if inst != nil {
			fmt.Printf("Request %d -> %s\n", i+1, inst.String())
		}
	}

	fmt.Println()
	fmt.Println("Demo complete!")
}

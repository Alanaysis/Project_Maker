// Package main demonstrates load balancing strategies.
//
// This example shows all four load balancing algorithms:
//  1. Round Robin: Sequential distribution across instances
//  2. Weighted: Distribution proportional to instance weights
//  3. Least Connections: Route to instance with fewest active connections
//  4. Random: Random selection from available instances
//
// Each algorithm has different trade-offs:
//   - Round Robin: Simple and fair, but doesn't account for instance capacity
//   - Weighted: Accounts for different instance capacities
//   - Least Connections: Best for uneven workloads with variable request durations
//   - Random: Simple, good for uniform workloads
package main

import (
	"fmt"
	"time"

	"service-discovery/src"
)

func main() {
	fmt.Println("=== Load Balancing Demo ===")
	fmt.Println()

	// Create service instances with different weights
	instances := []*service_discovery.ServiceInstance{
		{
			ID:       "web-1",
			Service:  "web-service",
			Address:  "192.168.1.1",
			Port:     8080,
			Metadata: map[string]string{"weight": "3", "version": "1.0"},
			TTL:      30 * time.Second,
		},
		{
			ID:       "web-2",
			Service:  "web-service",
			Address:  "192.168.1.2",
			Port:     8080,
			Metadata: map[string]string{"weight": "2", "version": "1.0"},
			TTL:      30 * time.Second,
		},
		{
			ID:       "web-3",
			Service:  "web-service",
			Address:  "192.168.1.3",
			Port:     8080,
			Metadata: map[string]string{"weight": "1", "version": "1.0"},
			TTL:      30 * time.Second,
		},
	}

	fmt.Println("--- Available Instances ---")
	for _, inst := range instances {
		fmt.Printf("  %s: weight=%d\n", inst.String(), inst.Weight())
	}
	fmt.Println()

	// Demonstrate each load balancing strategy
	fmt.Println("=== Strategy 1: Round Robin ===")
	fmt.Println()
	service_discovery.LoadBalanceDemo(instances)

	fmt.Println("=== Strategy 2: Weighted ===")
	fmt.Println()
	// Create instances with explicit weights for weighted demo
	weightedInstances := []*service_discovery.ServiceInstance{
		{
			ID:       "web-1",
			Service:  "web-service",
			Address:  "192.168.1.1",
			Port:     8080,
			Metadata: map[string]string{"weight": "5", "version": "1.0"},
			TTL:      30 * time.Second,
		},
		{
			ID:       "web-2",
			Service:  "web-service",
			Address:  "192.168.1.2",
			Port:     8080,
			Metadata: map[string]string{"weight": "3", "version": "1.0"},
			TTL:      30 * time.Second,
		},
		{
			ID:       "web-3",
			Service:  "web-service",
			Address:  "192.168.1.3",
			Port:     8080,
			Metadata: map[string]string{"weight": "2", "version": "1.0"},
			TTL:      30 * time.Second,
		},
	}
	service_discovery.LoadBalanceDemo(weightedInstances)

	fmt.Println("=== Strategy 3: Least Connections ===")
	fmt.Println()
	// Create instances with different connection counts
	leastConnInstances := []*service_discovery.ServiceInstance{
		{
			ID:       "web-1",
			Service:  "web-service",
			Address:  "192.168.1.1",
			Port:     8080,
			Metadata: map[string]string{"active_connections": "10", "version": "1.0"},
			TTL:      30 * time.Second,
		},
		{
			ID:       "web-2",
			Service:  "web-service",
			Address:  "192.168.1.2",
			Port:     8080,
			Metadata: map[string]string{"active_connections": "3", "version": "1.0"},
			TTL:      30 * time.Second,
		},
		{
			ID:       "web-3",
			Service:  "web-service",
			Address:  "192.168.1.3",
			Port:     8080,
			Metadata: map[string]string{"active_connections": "7", "version": "1.0"},
			TTL:      30 * time.Second,
		},
	}

	fmt.Println("Initial connection counts:")
	for _, inst := range leastConnInstances {
		fmt.Printf("  %s: %d connections\n", inst.String(), inst.ActiveConnections())
	}
	fmt.Println()

	lb := service_discovery.NewLoadBalancer(service_discovery.LoadBalancerLeastConn)
	lb.SetInstances(leastConnInstances)

	fmt.Println("Routing 10 requests (should prefer web-2 with fewest connections):")
	for i := 0; i < 10; i++ {
		inst := lb.Next()
		if inst != nil {
			inst.AddActiveConnection()
			fmt.Printf("  Request %d -> %s (connections=%d)\n",
				i+1, inst.String(), inst.ActiveConnections())
		}
	}

	fmt.Println()
	fmt.Println("=== Strategy 4: Random ===")
	fmt.Println()
	service_discovery.LoadBalanceDemo(instances)

	fmt.Println()
	fmt.Println("Demo complete!")
}

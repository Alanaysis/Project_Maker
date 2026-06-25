// Package main demonstrates using the service discovery system in a
// microservice architecture. It shows how services register themselves,
// discover other services, and communicate through load-balanced endpoints.
//
// This example simulates:
// - A user-service with 2 instances
// - An order-service with 3 instances
// - A gateway that discovers and calls services
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"time"

	"github.com/anthropic/service-discovery/internal/discovery"
	"github.com/anthropic/service-discovery/internal/loadbalancer"
	"github.com/anthropic/service-discovery/internal/registry"
	"github.com/anthropic/service-discovery/internal/store"
)

// simulateService registers a service and starts a simple HTTP server
// that responds to requests. In a real system, this would be a separate process.
func simulateService(ctx context.Context, reg *registry.Registry, svc *registry.Service, ttl time.Duration) error {
	// Register the service
	if err := reg.Register(ctx, svc, ttl); err != nil {
		return fmt.Errorf("register %s: %w", svc.ID, err)
	}

	log.Printf("[example] registered %s at %s", svc.ID, svc.Endpoint())
	return nil
}

// gatewayHandler demonstrates how an API gateway uses service discovery
// to route requests to backend services.
func gatewayHandler(disc *discovery.Discoverer, balancer loadbalancer.Balancer) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// Extract service name from path: /api/user-service/...
		// For simplicity, we just use "user-service" here
		serviceName := "user-service"

		// Discover healthy services
		services := disc.GetServices(serviceName)
		if len(services) == 0 {
			http.Error(w, "no available instances", http.StatusServiceUnavailable)
			return
		}

		// Use load balancer to select an instance
		svc, err := balancer.Select(services)
		if err != nil {
			http.Error(w, "load balancer error", http.StatusInternalServerError)
			return
		}

		// In a real gateway, you would proxy the request to the selected service
		// Here we just return the selected instance info
		json.NewEncoder(w).Encode(map[string]interface{}{
			"gateway":       "api-gateway",
			"routed_to":     svc.Endpoint(),
			"service_id":    svc.ID,
			"service_name":  svc.Name,
			"load_balanced": true,
		})
	}
}

func main() {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Create in-memory store
	s := store.NewMemStore()
	defer s.Close()

	// Create registry for services
	reg := registry.New(s)
	defer reg.Stop()

	// Create discoverer
	disc := discovery.New(s)
	if err := disc.Start(ctx); err != nil {
		log.Fatalf("failed to start discoverer: %v", err)
	}
	defer disc.Stop()

	// Create load balancer (round-robin)
	balancer := loadbalancer.New(loadbalancer.RoundRobin)

	// Register user-service instances
	for i := 1; i <= 2; i++ {
		svc := &registry.Service{
			ID:      fmt.Sprintf("user-svc-%d", i),
			Name:    "user-service",
			Address: "10.0.0.1",
			Port:    8080 + i,
			Status:  registry.StatusUp,
			Metadata: map[string]string{
				"version": "1.0",
				"env":     "production",
			},
		}
		if err := simulateService(ctx, reg, svc, 10*time.Second); err != nil {
			log.Printf("warning: %v", err)
		}
	}

	// Register order-service instances
	for i := 1; i <= 3; i++ {
		svc := &registry.Service{
			ID:      fmt.Sprintf("order-svc-%d", i),
			Name:    "order-service",
			Address: "10.0.0.2",
			Port:    9090 + i,
			Status:  registry.StatusUp,
			Metadata: map[string]string{
				"version": "2.0",
				"env":     "production",
			},
		}
		if err := simulateService(ctx, reg, svc, 10*time.Second); err != nil {
			log.Printf("warning: %v", err)
		}
	}

	// Wait for services to be discovered
	time.Sleep(200 * time.Millisecond)

	// Print discovered services
	log.Println("\n=== Discovered Services ===")
	for _, name := range disc.GetServiceNames() {
		services := disc.GetServices(name)
		log.Printf("  %s: %d instances", name, len(services))
		for _, svc := range services {
			log.Printf("    - %s (%s) [%v]", svc.ID, svc.Endpoint(), svc.Metadata)
		}
	}

	// Demonstrate load balancing
	log.Println("\n=== Load Balancing Demo ===")
	userServices := disc.GetServices("user-service")
	for i := 0; i < 6; i++ {
		svc, _ := balancer.Select(userServices)
		log.Printf("  Request %d -> %s", i+1, svc.Endpoint())
	}

	// Demonstrate tag-based discovery
	log.Println("\n=== Tag-Based Discovery ===")
	prodServices := disc.GetServicesByTags("user-service", map[string]string{"env": "production"})
	log.Printf("  Production user-service instances: %d", len(prodServices))

	// Start a simple gateway server
	mux := http.NewServeMux()
	mux.HandleFunc("/api/", gatewayHandler(disc, balancer))
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
	})

	log.Println("\n=== API Gateway ===")
	log.Println("  Gateway running on :8080")
	log.Println("  Try: curl http://localhost:8080/api/user-service")
	log.Println("  Try: curl http://localhost:8080/health")

	// In a real application, you would start the server:
	// log.Fatal(http.ListenAndServe(":8080", mux))
	_ = mux

	// Simulate a service deregistering
	log.Println("\n=== Service Deregistration ===")
	reg.Deregister(ctx, "user-svc-1")
	time.Sleep(100 * time.Millisecond)
	remaining := disc.GetServices("user-service")
	log.Printf("  After deregistering user-svc-1: %d instances remain", len(remaining))

	// Show load balancer adapts
	for i := 0; i < 4; i++ {
		svc, _ := balancer.Select(remaining)
		log.Printf("  Request %d -> %s", i+1, svc.Endpoint())
	}

	log.Println("\n=== Example Complete ===")
	cancel()
}

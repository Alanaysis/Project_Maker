// Package main demonstrates an API gateway pattern using service discovery.
// The gateway discovers backend services, performs health-aware routing,
// and supports tag-based service selection for canary deployments.
//
// Features demonstrated:
// - Service registration with metadata (version, weight)
// - Health-aware service discovery
// - Tag-based routing (canary deployment)
// - Load balancing across healthy instances
// - Graceful degradation when services are unavailable
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"strings"
	"time"

	"github.com/anthropic/service-discovery/internal/discovery"
	"github.com/anthropic/service-discovery/internal/loadbalancer"
	"github.com/anthropic/service-discovery/internal/registry"
	"github.com/anthropic/service-discovery/internal/store"
)

// GatewayConfig holds gateway configuration.
type GatewayConfig struct {
	ListenAddr string
}

// Gateway is an API gateway that uses service discovery for routing.
type Gateway struct {
	store      store.Store
	registry   *registry.Registry
	discoverer *discovery.Discoverer
	balancer   loadbalancer.Balancer
	config     GatewayConfig
}

// NewGateway creates a new API gateway.
func NewGateway(s store.Store, config GatewayConfig) *Gateway {
	return &Gateway{
		store:      s,
		registry:   registry.New(s),
		discoverer: discovery.New(s),
		balancer:   loadbalancer.New(loadbalancer.WeightedRoundRobin),
		config:     config,
	}
}

// Start starts the gateway and all its components.
func (g *Gateway) Start(ctx context.Context) error {
	if err := g.discoverer.Start(ctx); err != nil {
		return fmt.Errorf("start discoverer: %w", err)
	}
	log.Println("[gateway] started")
	return nil
}

// Stop gracefully stops the gateway.
func (g *Gateway) Stop() {
	g.discoverer.Stop()
	g.registry.Stop()
	log.Println("[gateway] stopped")
}

// RegisterBackend registers a backend service with the gateway.
func (g *Gateway) RegisterBackend(ctx context.Context, svc *registry.Service, ttl time.Duration) error {
	svc.Status = registry.StatusUp
	svc.RegisteredAt = time.Now()
	return g.registry.Register(ctx, svc, ttl)
}

// RouteRequest routes an incoming request to a healthy backend service.
func (g *Gateway) RouteRequest(serviceName string, tags map[string]string) (*registry.Service, error) {
	var services []*registry.Service

	if len(tags) > 0 {
		services = g.discoverer.GetServicesByTags(serviceName, tags)
	} else {
		services = g.discoverer.GetServices(serviceName)
	}

	if len(services) == 0 {
		return nil, fmt.Errorf("no healthy instances of %s", serviceName)
	}

	return g.balancer.Select(services)
}

// handler returns an HTTP handler that routes requests to backend services.
func (g *Gateway) handler() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// Parse service name from path: /v1/{service-name}/...
		parts := strings.Split(strings.TrimPrefix(r.URL.Path, "/"), "/")
		if len(parts) < 2 {
			http.Error(w, "invalid path, expected /v1/{service}/...", http.StatusBadRequest)
			return
		}

		version := parts[0] // "v1" or "v2"
		serviceName := parts[1]

		// Support canary routing via header
		tags := make(map[string]string)
		if canary := r.Header.Get("X-Canary"); canary == "true" {
			tags["canary"] = "true"
		}
		if version == "v2" {
			tags["version"] = "2.0"
		}

		// Route to a healthy backend
		svc, err := g.RouteRequest(serviceName, tags)
		if err != nil {
			http.Error(w, err.Error(), http.StatusServiceUnavailable)
			return
		}

		// Return routing information
		json.NewEncoder(w).Encode(map[string]interface{}{
			"gateway":         "api-gateway",
			"target_service":  svc.Name,
			"target_endpoint": svc.Endpoint(),
			"target_id":       svc.ID,
			"target_version":  svc.Metadata["version"],
			"tags_matched":    tags,
		})
	}
}

// healthHandler returns gateway health status including backend service counts.
func (g *Gateway) healthHandler() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		status := map[string]interface{}{
			"gateway": "ok",
			"services": map[string]int{},
		}

		for _, name := range g.discoverer.GetServiceNames() {
			status["services"].(map[string]int)[name] = g.discoverer.Count(name)
		}

		json.NewEncoder(w).Encode(status)
	}
}

// servicesHandler returns all discovered services.
func (g *Gateway) servicesHandler() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		all := g.discoverer.GetAllServices()
		json.NewEncoder(w).Encode(all)
	}
}

func main() {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Create store and gateway
	s := store.NewMemStore()
	defer s.Close()

	gw := NewGateway(s, GatewayConfig{ListenAddr: ":8080"})
	if err := gw.Start(ctx); err != nil {
		log.Fatalf("failed to start gateway: %v", err)
	}
	defer gw.Stop()

	// Register backend services with different versions and weights
	backends := []struct {
		id       string
		name     string
		address  string
		port     int
		version  string
		weight   string
		canary   string
	}{
		// Stable v1 instances
		{"api-v1-1", "api-service", "10.0.0.1", 8001, "1.0", "3", "false"},
		{"api-v1-2", "api-service", "10.0.0.2", 8002, "1.0", "3", "false"},
		{"api-v1-3", "api-service", "10.0.0.3", 8003, "1.0", "2", "false"},
		// Canary v2 instance
		{"api-v2-1", "api-service", "10.0.0.4", 8004, "2.0", "1", "true"},
		// Database service
		{"db-1", "db-service", "10.0.1.1", 5432, "1.0", "5", "false"},
		{"db-2", "db-service", "10.0.1.2", 5433, "1.0", "5", "false"},
	}

	for _, b := range backends {
		svc := &registry.Service{
			ID:      b.id,
			Name:    b.name,
			Address: b.address,
			Port:    b.port,
			Status:  registry.StatusUp,
			Metadata: map[string]string{
				"version": b.version,
				"weight":  b.weight,
				"canary":  b.canary,
			},
		}
		if err := gw.RegisterBackend(ctx, svc, 15*time.Second); err != nil {
			log.Printf("warning: failed to register %s: %v", b.id, err)
		}
	}

	// Wait for services to be discovered
	time.Sleep(200 * time.Millisecond)

	// Print discovered services
	log.Println("\n=== Discovered Services ===")
	for _, name := range gw.discoverer.GetServiceNames() {
		services := gw.discoverer.GetServices(name)
		log.Printf("  %s: %d healthy instances", name, len(services))
		for _, svc := range services {
			log.Printf("    - %s (%s) weight=%s version=%s canary=%s",
				svc.ID, svc.Endpoint(),
				svc.Metadata["weight"], svc.Metadata["version"], svc.Metadata["canary"])
		}
	}

	// Demonstrate routing
	log.Println("\n=== Routing Demo ===")

	// Regular request (stable version)
	log.Println("  Regular requests (stable):")
	for i := 0; i < 5; i++ {
		svc, err := gw.RouteRequest("api-service", nil)
		if err != nil {
			log.Printf("    Request %d: %v", i+1, err)
		} else {
			log.Printf("    Request %d -> %s (v%s)", i+1, svc.Endpoint(), svc.Metadata["version"])
		}
	}

	// Canary request
	log.Println("\n  Canary requests (v2):")
	for i := 0; i < 3; i++ {
		svc, err := gw.RouteRequest("api-service", map[string]string{"canary": "true"})
		if err != nil {
			log.Printf("    Request %d: %v", i+1, err)
		} else {
			log.Printf("    Request %d -> %s (v%s, canary=%s)",
				i+1, svc.Endpoint(), svc.Metadata["version"], svc.Metadata["canary"])
		}
	}

	// Database service routing
	log.Println("\n  Database requests:")
	for i := 0; i < 4; i++ {
		svc, err := gw.RouteRequest("db-service", nil)
		if err != nil {
			log.Printf("    Request %d: %v", i+1, err)
		} else {
			log.Printf("    Request %d -> %s", i+1, svc.Endpoint())
		}
	}

	// Start HTTP server
	mux := http.NewServeMux()
	mux.HandleFunc("/v1/", gw.handler())
	mux.HandleFunc("/v2/", gw.handler())
	mux.HandleFunc("/health", gw.healthHandler())
	mux.HandleFunc("/services", gw.servicesHandler())

	log.Println("\n=== API Gateway Server ===")
	log.Println("  Listening on :8080")
	log.Println("")
	log.Println("  Try these commands:")
	log.Println("    curl http://localhost:8080/v1/api-service/users")
	log.Println("    curl http://localhost:8080/v2/api-service/users")
	log.Println("    curl -H 'X-Canary: true' http://localhost:8080/v1/api-service/users")
	log.Println("    curl http://localhost:8080/health")
	log.Println("    curl http://localhost:8080/services")
	log.Println("")

	// In a real application:
	// log.Fatal(http.ListenAndServe(":8080", mux))
	_ = mux

	log.Println("=== Example Complete ===")
	cancel()
}

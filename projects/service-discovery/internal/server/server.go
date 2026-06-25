// Package server provides an HTTP API for the service discovery system.
// It exposes endpoints for service registration, discovery, and health status.
package server

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

// Server is the HTTP API server for the service discovery system.
type Server struct {
	store      store.Store
	registry   *registry.Registry
	discoverer *discovery.Discoverer
	balancer   loadbalancer.Balancer
	httpServer *http.Server
	addr       string
}

// Config holds configuration for the API server.
type Config struct {
	ListenAddr string
}

// DefaultConfig returns a Config with sensible defaults.
func DefaultConfig() Config {
	return Config{
		ListenAddr: ":8500",
	}
}

// New creates a new API server.
func New(s store.Store, config Config) *Server {
	srv := &Server{
		store:      s,
		registry:   registry.New(s),
		discoverer: discovery.New(s),
		balancer:   loadbalancer.New(loadbalancer.RoundRobin),
		addr:       config.ListenAddr,
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/register", srv.handleRegister)
	mux.HandleFunc("/deregister", srv.handleDeregister)
	mux.HandleFunc("/services", srv.handleListServices)
	mux.HandleFunc("/services/", srv.handleGetService)
	mux.HandleFunc("/discover", srv.handleDiscover)
	mux.HandleFunc("/discover/tags", srv.handleDiscoverByTags)
	mux.HandleFunc("/choose", srv.handleChoose)
	mux.HandleFunc("/choose/tags", srv.handleChooseByTags)
	mux.HandleFunc("/health", srv.handleHealth)

	srv.httpServer = &http.Server{
		Addr:    config.ListenAddr,
		Handler: mux,
	}

	return srv
}

// Start starts the HTTP server and the service discoverer.
func (s *Server) Start(ctx context.Context) error {
	if err := s.discoverer.Start(ctx); err != nil {
		return fmt.Errorf("start discoverer: %w", err)
	}

	log.Printf("[server] listening on %s", s.addr)

	go func() {
		if err := s.httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Printf("[server] HTTP server error: %v", err)
		}
	}()

	return nil
}

// Stop gracefully stops the server.
func (s *Server) Stop() {
	s.discoverer.Stop()
	s.registry.Stop()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := s.httpServer.Shutdown(ctx); err != nil {
		log.Printf("[server] shutdown error: %v", err)
	}
}

// Registry returns the server's registry.
func (s *Server) Registry() *registry.Registry {
	return s.registry
}

// Discoverer returns the server's discoverer.
func (s *Server) Discoverer() *discovery.Discoverer {
	return s.discoverer
}

// --- HTTP Handlers ---

// handleRegister handles POST /register requests.
func (s *Server) handleRegister(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var svc registry.Service
	if err := json.NewDecoder(r.Body).Decode(&svc); err != nil {
		http.Error(w, fmt.Sprintf("invalid request body: %v", err), http.StatusBadRequest)
		return
	}

	if svc.Status == 0 {
		svc.Status = registry.StatusUp
	}
	svc.RegisteredAt = time.Now()

	if err := s.registry.Register(r.Context(), &svc, registry.DefaultTTL); err != nil {
		http.Error(w, fmt.Sprintf("register failed: %v", err), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]string{
		"status":  "registered",
		"service": svc.ID,
	})
}

// handleDeregister handles DELETE /deregister?id={serviceID} requests.
func (s *Server) handleDeregister(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodDelete {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}

	id := r.URL.Query().Get("id")
	if id == "" {
		http.Error(w, "missing id parameter", http.StatusBadRequest)
		return
	}

	if err := s.registry.Deregister(r.Context(), id); err != nil {
		http.Error(w, fmt.Sprintf("deregister failed: %v", err), http.StatusInternalServerError)
		return
	}

	json.NewEncoder(w).Encode(map[string]string{"status": "deregistered"})
}

// handleListServices handles GET /services requests.
func (s *Server) handleListServices(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}

	all := s.discoverer.GetAllServices()
	json.NewEncoder(w).Encode(all)
}

// handleGetService handles GET /services/{name} requests.
func (s *Server) handleGetService(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}

	name := r.URL.Path[len("/services/"):]
	if name == "" {
		http.Error(w, "missing service name", http.StatusBadRequest)
		return
	}

	services := s.discoverer.GetServices(name)
	if len(services) == 0 {
		http.Error(w, "service not found", http.StatusNotFound)
		return
	}

	json.NewEncoder(w).Encode(services)
}

// handleDiscover handles GET /discover?name={name} requests.
func (s *Server) handleDiscover(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}

	name := r.URL.Query().Get("name")
	if name == "" {
		http.Error(w, "missing name parameter", http.StatusBadRequest)
		return
	}

	services := s.discoverer.GetServices(name)
	json.NewEncoder(w).Encode(services)
}

// handleChoose handles GET /choose?name={name} requests.
// It uses the load balancer to select a single service instance.
func (s *Server) handleChoose(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}

	name := r.URL.Query().Get("name")
	if name == "" {
		http.Error(w, "missing name parameter", http.StatusBadRequest)
		return
	}

	services := s.discoverer.GetServices(name)
	svc, err := s.balancer.Select(services)
	if err != nil {
		http.Error(w, fmt.Sprintf("no services available: %v", err), http.StatusServiceUnavailable)
		return
	}

	json.NewEncoder(w).Encode(svc)
}

// handleHealth handles GET /health requests.
func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}

// handleDiscoverByTags handles GET /discover/tags?name=X&tag1=val1&tag2=val2 requests.
// It discovers services by name and filters by metadata tags.
func (s *Server) handleDiscoverByTags(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}

	name := r.URL.Query().Get("name")
	if name == "" {
		http.Error(w, "missing name parameter", http.StatusBadRequest)
		return
	}

	// Extract tag filters from query parameters (exclude "name")
	tags := make(map[string]string)
	for key, values := range r.URL.Query() {
		if key != "name" && len(values) > 0 {
			tags[key] = values[0]
		}
	}

	services := s.discoverer.GetServicesByTags(name, tags)
	json.NewEncoder(w).Encode(services)
}

// handleChooseByTags handles GET /choose/tags?name=X&tag1=val1 requests.
// It chooses a service by name, filtered by tags, using the load balancer.
func (s *Server) handleChooseByTags(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}

	name := r.URL.Query().Get("name")
	if name == "" {
		http.Error(w, "missing name parameter", http.StatusBadRequest)
		return
	}

	// Extract tag filters from query parameters (exclude "name")
	tags := make(map[string]string)
	for key, values := range r.URL.Query() {
		if key != "name" && len(values) > 0 {
			tags[key] = values[0]
		}
	}

	services := s.discoverer.GetServicesByTags(name, tags)
	svc, err := s.balancer.Select(services)
	if err != nil {
		http.Error(w, fmt.Sprintf("no services available: %v", err), http.StatusServiceUnavailable)
		return
	}

	json.NewEncoder(w).Encode(svc)
}

// Package tests provides integration tests for the service discovery system.
// These tests exercise multiple components working together: store, registry,
// discovery, load balancer, and the HTTP API server.
package tests

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"sync"
	"testing"
	"time"

	"github.com/anthropic/service-discovery/internal/discovery"
	"github.com/anthropic/service-discovery/internal/loadbalancer"
	"github.com/anthropic/service-discovery/internal/registry"
	"github.com/anthropic/service-discovery/internal/server"
	"github.com/anthropic/service-discovery/internal/store"
)

// --- Helper ---

func newService(id, name string, port int) *registry.Service {
	return &registry.Service{
		ID:      id,
		Name:    name,
		Address: "127.0.0.1",
		Port:    port,
		Status:  registry.StatusUp,
		Metadata: map[string]string{
			"env": "test",
		},
	}
}

func putServiceDirect(t *testing.T, s store.Store, ctx context.Context, svc *registry.Service) {
	t.Helper()
	data, err := svc.Marshal()
	if err != nil {
		t.Fatalf("Marshal failed: %v", err)
	}
	if err := s.Put(ctx, svc.Key(), data, 0); err != nil {
		t.Fatalf("Put failed: %v", err)
	}
}

// --- Integration: Registry + Discovery ---

func TestIntegrationRegisterAndDiscover(t *testing.T) {
	s := store.NewMemStore()
	defer s.Close()
	ctx := context.Background()

	// Create registry and register services
	reg := registry.New(s)
	defer reg.Stop()

	svc1 := newService("web-1", "web", 8001)
	svc2 := newService("web-2", "web", 8002)
	svc3 := newService("api-1", "api", 9001)

	if err := reg.Register(ctx, svc1, 10*time.Second); err != nil {
		t.Fatalf("Register svc1 failed: %v", err)
	}
	if err := reg.Register(ctx, svc2, 10*time.Second); err != nil {
		t.Fatalf("Register svc2 failed: %v", err)
	}
	if err := reg.Register(ctx, svc3, 10*time.Second); err != nil {
		t.Fatalf("Register svc3 failed: %v", err)
	}

	// Create discoverer and verify it finds registered services
	disc := discovery.New(s)
	defer disc.Stop()
	if err := disc.Start(ctx); err != nil {
		t.Fatalf("Start discoverer failed: %v", err)
	}
	time.Sleep(100 * time.Millisecond)

	webServices := disc.GetServices("web")
	if len(webServices) != 2 {
		t.Errorf("expected 2 web services, got %d", len(webServices))
	}

	apiServices := disc.GetServices("api")
	if len(apiServices) != 1 {
		t.Errorf("expected 1 api service, got %d", len(apiServices))
	}

	if disc.Count("web") != 2 {
		t.Errorf("expected Count=2 for web, got %d", disc.Count("web"))
	}
}

func TestIntegrationDeregisterRemovesFromDiscovery(t *testing.T) {
	s := store.NewMemStore()
	defer s.Close()
	ctx := context.Background()

	reg := registry.New(s)
	defer reg.Stop()

	svc := newService("web-1", "web", 8001)
	reg.Register(ctx, svc, 10*time.Second)

	disc := discovery.New(s)
	defer disc.Stop()
	disc.Start(ctx)
	time.Sleep(100 * time.Millisecond)

	if disc.Count("web") != 1 {
		t.Fatalf("expected 1 web service initially")
	}

	// Deregister and verify discovery updates
	if err := reg.Deregister(ctx, "web-1"); err != nil {
		t.Fatalf("Deregister failed: %v", err)
	}
	time.Sleep(100 * time.Millisecond)

	if disc.Count("web") != 0 {
		t.Errorf("expected 0 web services after deregister, got %d", disc.Count("web"))
	}
}

func TestIntegrationMultipleNames(t *testing.T) {
	s := store.NewMemStore()
	defer s.Close()
	ctx := context.Background()

	reg := registry.New(s)
	defer reg.Stop()

	services := []struct {
		id   string
		name string
		port int
	}{
		{"web-1", "web", 8001},
		{"web-2", "web", 8002},
		{"api-1", "api", 9001},
		{"api-2", "api", 9002},
		{"api-3", "api", 9003},
		{"db-1", "db", 5432},
	}

	for _, s := range services {
		svc := newService(s.id, s.name, s.port)
		if err := reg.Register(ctx, svc, 10*time.Second); err != nil {
			t.Fatalf("Register %s failed: %v", s.id, err)
		}
	}

	disc := discovery.New(s)
	defer disc.Stop()
	disc.Start(ctx)
	time.Sleep(100 * time.Millisecond)

	names := disc.GetServiceNames()
	if len(names) != 3 {
		t.Errorf("expected 3 service names, got %d", len(names))
	}

	if disc.Count("web") != 2 {
		t.Errorf("expected 2 web services, got %d", disc.Count("web"))
	}
	if disc.Count("api") != 3 {
		t.Errorf("expected 3 api services, got %d", disc.Count("api"))
	}
	if disc.Count("db") != 1 {
		t.Errorf("expected 1 db service, got %d", disc.Count("db"))
	}
}

// --- Integration: Discovery + Load Balancer ---

func TestIntegrationDiscoveryWithLoadBalancer(t *testing.T) {
	s := store.NewMemStore()
	defer s.Close()
	ctx := context.Background()

	// Register services
	for i := 1; i <= 3; i++ {
		svc := newService(fmt.Sprintf("web-%d", i), "web", 8000+i)
		putServiceDirect(t, s, ctx, svc)
	}

	disc := discovery.New(s)
	defer disc.Stop()
	disc.Start(ctx)
	time.Sleep(100 * time.Millisecond)

	balancer := loadbalancer.New(loadbalancer.RoundRobin)

	services := disc.GetServices("web")
	if len(services) != 3 {
		t.Fatalf("expected 3 web services, got %d", len(services))
	}

	// Load balancer should distribute across all instances
	selected := make(map[string]int)
	for i := 0; i < 9; i++ {
		svc, err := balancer.Select(services)
		if err != nil {
			t.Fatalf("Select failed: %v", err)
		}
		selected[svc.ID]++
	}

	for id, count := range selected {
		if count != 3 {
			t.Errorf("service %s selected %d times, expected 3", id, count)
		}
	}
}

func TestIntegrationRandomBalancerWithDiscovery(t *testing.T) {
	s := store.NewMemStore()
	defer s.Close()
	ctx := context.Background()

	for i := 1; i <= 3; i++ {
		svc := newService(fmt.Sprintf("web-%d", i), "web", 8000+i)
		putServiceDirect(t, s, ctx, svc)
	}

	disc := discovery.New(s)
	defer disc.Stop()
	disc.Start(ctx)
	time.Sleep(100 * time.Millisecond)

	balancer := loadbalancer.New(loadbalancer.Random)
	services := disc.GetServices("web")

	selected := make(map[string]int)
	for i := 0; i < 300; i++ {
		svc, err := balancer.Select(services)
		if err != nil {
			t.Fatalf("Select failed: %v", err)
		}
		selected[svc.ID]++
	}

	// Each service should be selected at least once
	for i := 1; i <= 3; i++ {
		id := fmt.Sprintf("web-%d", i)
		if selected[id] == 0 {
			t.Errorf("service %s was never selected", id)
		}
	}
}

// --- Integration: Store Lease + Registry Heartbeat ---

func TestIntegrationLeaseExpiration(t *testing.T) {
	s := store.NewMemStore()
	defer s.Close()
	ctx := context.Background()

	// Register with short TTL, stop heartbeat by stopping registry quickly
	reg := registry.New(s)
	svc := newService("web-1", "web", 8001)

	if err := reg.Register(ctx, svc, 200*time.Millisecond); err != nil {
		t.Fatalf("Register failed: %v", err)
	}

	// Verify service exists in store
	_, err := s.Get(ctx, svc.Key())
	if err != nil {
		t.Fatalf("service should exist in store: %v", err)
	}

	// Stop registry to kill heartbeat, then wait for lease expiration
	reg.Stop()
	time.Sleep(300 * time.Millisecond)

	_, err = s.Get(ctx, svc.Key())
	if err == nil {
		t.Error("expected service to be expired from store after lease TTL")
	}
}

// --- Integration: HTTP API End-to-End ---

func setupAPIServer(t *testing.T) (*server.Server, *store.MemStore) {
	t.Helper()
	s := store.NewMemStore()
	srv := server.New(s, server.Config{ListenAddr: ":0"})
	return srv, s
}

func TestIntegrationAPIRegisterAndDiscover(t *testing.T) {
	srv, s := setupAPIServer(t)
	defer s.Close()

	ctx := context.Background()
	srv.Discoverer().Start(ctx)
	defer srv.Discoverer().Stop()

	// Register a service via API
	body := `{"id":"svc-1","name":"web","address":"10.0.0.1","port":8080}`
	req := httptest.NewRequest("POST", "/register", bytes.NewBufferString(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	srv.handleRegister(w, req)

	if w.Code != http.StatusCreated {
		t.Fatalf("register: expected 201, got %d", w.Code)
	}

	// Discover the service
	req = httptest.NewRequest("GET", "/discover?name=web", nil)
	w = httptest.NewRecorder()
	srv.handleDiscover(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("discover: expected 200, got %d", w.Code)
	}

	var services []*registry.Service
	json.NewDecoder(w.Body).Decode(&services)
	if len(services) != 1 {
		t.Errorf("expected 1 service, got %d", len(services))
	}
	if len(services) > 0 && services[0].ID != "svc-1" {
		t.Errorf("expected svc-1, got %s", services[0].ID)
	}
}

func TestIntegrationAPIRegisterDeregisterFlow(t *testing.T) {
	srv, s := setupAPIServer(t)
	defer s.Close()

	ctx := context.Background()
	srv.Discoverer().Start(ctx)
	defer srv.Discoverer().Stop()

	// Register
	body := `{"id":"svc-1","name":"web","address":"10.0.0.1","port":8080}`
	req := httptest.NewRequest("POST", "/register", bytes.NewBufferString(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	srv.handleRegister(w, req)

	if w.Code != http.StatusCreated {
		t.Fatalf("register: expected 201, got %d", w.Code)
	}

	// List services
	req = httptest.NewRequest("GET", "/services", nil)
	w = httptest.NewRecorder()
	srv.handleListServices(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("list: expected 200, got %d", w.Code)
	}

	// Deregister
	req = httptest.NewRequest("DELETE", "/deregister?id=svc-1", nil)
	w = httptest.NewRecorder()
	srv.handleDeregister(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("deregister: expected 200, got %d", w.Code)
	}

	// Verify service is gone
	time.Sleep(100 * time.Millisecond)
	req = httptest.NewRequest("GET", "/discover?name=web", nil)
	w = httptest.NewRecorder()
	srv.handleDiscover(w, req)

	var services []*registry.Service
	json.NewDecoder(w.Body).Decode(&services)
	if len(services) != 0 {
		t.Errorf("expected 0 services after deregister, got %d", len(services))
	}
}

func TestIntegrationAPIChoose(t *testing.T) {
	srv, s := setupAPIServer(t)
	defer s.Close()

	ctx := context.Background()
	srv.Discoverer().Start(ctx)
	defer srv.Discoverer().Stop()

	// Register multiple services
	for i := 1; i <= 3; i++ {
		body := fmt.Sprintf(`{"id":"svc-%d","name":"web","address":"10.0.0.%d","port":800%d}`, i, i, i)
		req := httptest.NewRequest("POST", "/register", bytes.NewBufferString(body))
		req.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()
		srv.handleRegister(w, req)

		if w.Code != http.StatusCreated {
			t.Fatalf("register svc-%d: expected 201, got %d", i, w.Code)
		}
	}

	time.Sleep(100 * time.Millisecond)

	// Choose multiple times - should round-robin
	selected := make(map[string]bool)
	for i := 0; i < 10; i++ {
		req := httptest.NewRequest("GET", "/choose?name=web", nil)
		w := httptest.NewRecorder()
		srv.handleChoose(w, req)

		if w.Code != http.StatusOK {
			t.Fatalf("choose: expected 200, got %d", w.Code)
		}

		var svc registry.Service
		json.NewDecoder(w.Body).Decode(&svc)
		selected[svc.ID] = true
	}

	if len(selected) < 2 {
		t.Errorf("expected multiple services to be selected, got %v", selected)
	}
}

func TestIntegrationAPIMethodNotAllowed(t *testing.T) {
	srv, s := setupAPIServer(t)
	defer s.Close()

	tests := []struct {
		method string
		path   string
	}{
		{"GET", "/register"},
		{"POST", "/deregister"},
		{"POST", "/services"},
		{"POST", "/discover"},
		{"POST", "/choose"},
	}

	for _, tt := range tests {
		t.Run(tt.method+" "+tt.path, func(t *testing.T) {
			req := httptest.NewRequest(tt.method, tt.path, nil)
			w := httptest.NewRecorder()

			// Route to the correct handler
			switch tt.path {
			case "/register":
				srv.handleRegister(w, req)
			case "/deregister":
				srv.handleDeregister(w, req)
			case "/services":
				srv.handleListServices(w, req)
			case "/discover":
				srv.handleDiscover(w, req)
			case "/choose":
				srv.handleChoose(w, req)
			}

			if w.Code != http.StatusMethodNotAllowed {
				t.Errorf("expected 405, got %d", w.Code)
			}
		})
	}
}

// --- Integration: Concurrent Registration ---

func TestIntegrationConcurrentRegistration(t *testing.T) {
	s := store.NewMemStore()
	defer s.Close()
	ctx := context.Background()

	reg := registry.New(s)
	defer reg.Stop()

	var wg sync.WaitGroup
	errors := make(chan error, 20)

	for i := 0; i < 20; i++ {
		wg.Add(1)
		go func(n int) {
			defer wg.Done()
			svc := newService(fmt.Sprintf("svc-%d", n), "web", 8000+n)
			if err := reg.Register(ctx, svc, 10*time.Second); err != nil {
				errors <- fmt.Errorf("register svc-%d: %w", n, err)
			}
		}(i)
	}

	wg.Wait()
	close(errors)

	for err := range errors {
		t.Errorf("concurrent register error: %v", err)
	}

	services := reg.ListRegistered()
	if len(services) != 20 {
		t.Errorf("expected 20 registered services, got %d", len(services))
	}

	// Verify all are discoverable
	disc := discovery.New(s)
	defer disc.Stop()
	disc.Start(ctx)
	time.Sleep(200 * time.Millisecond)

	if disc.Count("web") != 20 {
		t.Errorf("expected 20 discoverable services, got %d", disc.Count("web"))
	}
}

// --- Integration: Watch Events ---

func TestIntegrationWatchEvents(t *testing.T) {
	s := store.NewMemStore()
	defer s.Close()
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	watchCh, err := s.Watch(ctx, "/services/")
	if err != nil {
		t.Fatalf("Watch failed: %v", err)
	}

	reg := registry.New(s)
	defer reg.Stop()

	// Register should trigger a watch event
	svc := newService("web-1", "web", 8001)
	reg.Register(ctx, svc, 10*time.Second)

	select {
	case event := <-watchCh:
		if event.Type != store.EventPut {
			t.Errorf("expected EventPut, got %v", event.Type)
		}
	case <-time.After(time.Second):
		t.Fatal("timeout waiting for register watch event")
	}

	// Deregister should trigger a watch event
	reg.Deregister(ctx, "web-1")

	select {
	case event := <-watchCh:
		if event.Type != store.EventDelete {
			t.Errorf("expected EventDelete, got %v", event.Type)
		}
	case <-time.After(time.Second):
		t.Fatal("timeout waiting for deregister watch event")
	}
}

// --- Integration: Discovery OnChange Callback ---

func TestIntegrationDiscoveryOnChange(t *testing.T) {
	s := store.NewMemStore()
	defer s.Close()
	ctx := context.Background()

	onChangeCh := make(chan []*registry.Service, 10)
	onChange := func(services []*registry.Service) {
		onChangeCh <- services
	}

	disc := discovery.New(s, discovery.WithOnChange(onChange))
	defer disc.Stop()
	disc.Start(ctx)
	time.Sleep(50 * time.Millisecond)

	// Add a service - should trigger onChange
	svc := newService("web-1", "web", 8001)
	putServiceDirect(t, s, ctx, svc)

	select {
	case services := <-onChangeCh:
		if len(services) != 1 {
			t.Errorf("expected 1 service in callback, got %d", len(services))
		}
	case <-time.After(time.Second):
		t.Fatal("timeout waiting for onChange callback")
	}

	// Add another service
	svc2 := newService("web-2", "web", 8002)
	putServiceDirect(t, s, ctx, svc2)

	select {
	case services := <-onChangeCh:
		if len(services) != 2 {
			t.Errorf("expected 2 services in callback, got %d", len(services))
		}
	case <-time.After(time.Second):
		t.Fatal("timeout waiting for onChange callback")
	}

	// Remove a service
	s.Delete(ctx, svc.Key())

	select {
	case services := <-onChangeCh:
		if len(services) != 1 {
			t.Errorf("expected 1 service in callback after delete, got %d", len(services))
		}
	case <-time.After(time.Second):
		t.Fatal("timeout waiting for onChange callback after delete")
	}
}

// --- Integration: Service Validation via API ---

func TestIntegrationAPIInvalidServiceRegistration(t *testing.T) {
	srv, s := setupAPIServer(t)
	defer s.Close()

	ctx := context.Background()
	srv.Discoverer().Start(ctx)
	defer srv.Discoverer().Stop()

	// Missing required fields
	tests := []struct {
		name string
		body string
	}{
		{"missing id", `{"name":"web","address":"10.0.0.1","port":8080}`},
		{"missing name", `{"id":"svc-1","address":"10.0.0.1","port":8080}`},
		{"missing address", `{"id":"svc-1","name":"web","port":8080}`},
		{"invalid port", `{"id":"svc-1","name":"web","address":"10.0.0.1","port":0}`},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			req := httptest.NewRequest("POST", "/register", bytes.NewBufferString(tt.body))
			req.Header.Set("Content-Type", "application/json")
			w := httptest.NewRecorder()

			srv.handleRegister(w, req)

			if w.Code != http.StatusInternalServerError {
				t.Errorf("expected 500 for %s, got %d", tt.name, w.Code)
			}
		})
	}
}

// --- Integration: GetService by name endpoint ---

func TestIntegrationAPIGetServiceByName(t *testing.T) {
	srv, s := setupAPIServer(t)
	defer s.Close()

	ctx := context.Background()
	srv.Discoverer().Start(ctx)
	defer srv.Discoverer().Stop()

	// Pre-populate services
	svc1 := newService("web-1", "web", 8001)
	svc2 := newService("web-2", "web", 8002)
	putServiceDirect(t, s, ctx, svc1)
	putServiceDirect(t, s, ctx, svc2)
	time.Sleep(100 * time.Millisecond)

	// GET /services/web
	req := httptest.NewRequest("GET", "/services/web", nil)
	w := httptest.NewRecorder()
	srv.handleGetService(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", w.Code)
	}

	var services []*registry.Service
	json.NewDecoder(w.Body).Decode(&services)
	if len(services) != 2 {
		t.Errorf("expected 2 services, got %d", len(services))
	}
}

// --- Integration: Health endpoint is always available ---

func TestIntegrationHealthEndpoint(t *testing.T) {
	srv, s := setupAPIServer(t)
	defer s.Close()

	req := httptest.NewRequest("GET", "/health", nil)
	w := httptest.NewRecorder()
	srv.handleHealth(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", w.Code)
	}

	var resp map[string]string
	json.NewDecoder(w.Body).Decode(&resp)
	if resp["status"] != "ok" {
		t.Errorf("expected status=ok, got %s", resp["status"])
	}
}

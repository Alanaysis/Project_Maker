package server

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/anthropic/service-discovery/internal/registry"
	"github.com/anthropic/service-discovery/internal/store"
)

func setupTestServer(t *testing.T) (*Server, *store.MemStore) {
	t.Helper()
	s := store.NewMemStore()
	srv := New(s, Config{ListenAddr: ":0"})
	return srv, s
}

func TestHandleHealth(t *testing.T) {
	srv, s := setupTestServer(t)
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

func TestHandleRegister(t *testing.T) {
	srv, s := setupTestServer(t)
	defer s.Close()

	ctx := context.Background()
	srv.discoverer.Start(ctx)
	defer srv.discoverer.Stop()

	body := `{"id":"svc-1","name":"web","address":"10.0.0.1","port":8080}`
	req := httptest.NewRequest("POST", "/register", bytes.NewBufferString(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	srv.handleRegister(w, req)

	if w.Code != http.StatusCreated {
		t.Errorf("expected 201, got %d", w.Code)
	}

	var resp map[string]string
	json.NewDecoder(w.Body).Decode(&resp)
	if resp["status"] != "registered" {
		t.Errorf("expected status=registered, got %s", resp["status"])
	}
}

func TestHandleRegisterInvalidBody(t *testing.T) {
	srv, s := setupTestServer(t)
	defer s.Close()

	req := httptest.NewRequest("POST", "/register", bytes.NewBufferString("invalid"))
	w := httptest.NewRecorder()

	srv.handleRegister(w, req)

	if w.Code != http.StatusBadRequest {
		t.Errorf("expected 400, got %d", w.Code)
	}
}

func TestHandleRegisterMethodNotAllowed(t *testing.T) {
	srv, s := setupTestServer(t)
	defer s.Close()

	req := httptest.NewRequest("GET", "/register", nil)
	w := httptest.NewRecorder()

	srv.handleRegister(w, req)

	if w.Code != http.StatusMethodNotAllowed {
		t.Errorf("expected 405, got %d", w.Code)
	}
}

func TestHandleDeregister(t *testing.T) {
	srv, s := setupTestServer(t)
	defer s.Close()

	ctx := context.Background()
	srv.discoverer.Start(ctx)
	defer srv.discoverer.Stop()

	// Register first
	svc := &registry.Service{ID: "svc-1", Name: "web", Address: "10.0.0.1", Port: 8080}
	svc.RegisteredAt = time.Now()
	srv.registry.Register(ctx, svc, 10*time.Second)

	req := httptest.NewRequest("DELETE", "/deregister?id=svc-1", nil)
	w := httptest.NewRecorder()

	srv.handleDeregister(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", w.Code)
	}
}

func TestHandleDeregisterMissingID(t *testing.T) {
	srv, s := setupTestServer(t)
	defer s.Close()

	req := httptest.NewRequest("DELETE", "/deregister", nil)
	w := httptest.NewRecorder()

	srv.handleDeregister(w, req)

	if w.Code != http.StatusBadRequest {
		t.Errorf("expected 400, got %d", w.Code)
	}
}

func TestHandleListServices(t *testing.T) {
	srv, s := setupTestServer(t)
	defer s.Close()

	ctx := context.Background()
	srv.discoverer.Start(ctx)
	defer srv.discoverer.Stop()

	// Add services to store
	svc1 := &registry.Service{ID: "svc-1", Name: "web", Address: "10.0.0.1", Port: 8001, Status: registry.StatusUp}
	svc2 := &registry.Service{ID: "svc-2", Name: "api", Address: "10.0.0.2", Port: 9001, Status: registry.StatusUp}
	data1, _ := svc1.Marshal()
	data2, _ := svc2.Marshal()
	s.Put(ctx, svc1.Key(), data1, 0)
	s.Put(ctx, svc2.Key(), data2, 0)

	time.Sleep(100 * time.Millisecond)

	req := httptest.NewRequest("GET", "/services", nil)
	w := httptest.NewRecorder()

	srv.handleListServices(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", w.Code)
	}
}

func TestHandleDiscover(t *testing.T) {
	srv, s := setupTestServer(t)
	defer s.Close()

	ctx := context.Background()
	srv.discoverer.Start(ctx)
	defer srv.discoverer.Stop()

	// Add services
	svc := &registry.Service{ID: "svc-1", Name: "web", Address: "10.0.0.1", Port: 8001, Status: registry.StatusUp}
	data, _ := svc.Marshal()
	s.Put(ctx, svc.Key(), data, 0)

	time.Sleep(100 * time.Millisecond)

	req := httptest.NewRequest("GET", "/discover?name=web", nil)
	w := httptest.NewRecorder()

	srv.handleDiscover(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", w.Code)
	}

	var services []*registry.Service
	json.NewDecoder(w.Body).Decode(&services)
	if len(services) != 1 {
		t.Errorf("expected 1 service, got %d", len(services))
	}
}

func TestHandleDiscoverMissingName(t *testing.T) {
	srv, s := setupTestServer(t)
	defer s.Close()

	req := httptest.NewRequest("GET", "/discover", nil)
	w := httptest.NewRecorder()

	srv.handleDiscover(w, req)

	if w.Code != http.StatusBadRequest {
		t.Errorf("expected 400, got %d", w.Code)
	}
}

func TestHandleChoose(t *testing.T) {
	srv, s := setupTestServer(t)
	defer s.Close()

	ctx := context.Background()
	srv.discoverer.Start(ctx)
	defer srv.discoverer.Stop()

	// Add services
	svc1 := &registry.Service{ID: "svc-1", Name: "web", Address: "10.0.0.1", Port: 8001, Status: registry.StatusUp}
	svc2 := &registry.Service{ID: "svc-2", Name: "web", Address: "10.0.0.2", Port: 8002, Status: registry.StatusUp}
	data1, _ := svc1.Marshal()
	data2, _ := svc2.Marshal()
	s.Put(ctx, svc1.Key(), data1, 0)
	s.Put(ctx, svc2.Key(), data2, 0)

	time.Sleep(100 * time.Millisecond)

	// Choose multiple times - should get different services
	selected := make(map[string]bool)
	for i := 0; i < 10; i++ {
		req := httptest.NewRequest("GET", "/choose?name=web", nil)
		w := httptest.NewRecorder()
		srv.handleChoose(w, req)

		if w.Code != http.StatusOK {
			t.Fatalf("expected 200, got %d", w.Code)
		}

		var svc registry.Service
		json.NewDecoder(w.Body).Decode(&svc)
		selected[svc.ID] = true
	}

	// Both services should be selected at least once
	if len(selected) < 2 {
		t.Errorf("expected both services to be selected, got %v", selected)
	}
}

func TestHandleChooseNoServices(t *testing.T) {
	srv, s := setupTestServer(t)
	defer s.Close()

	ctx := context.Background()
	srv.discoverer.Start(ctx)
	defer srv.discoverer.Stop()

	req := httptest.NewRequest("GET", "/choose?name=nonexistent", nil)
	w := httptest.NewRecorder()

	srv.handleChoose(w, req)

	if w.Code != http.StatusServiceUnavailable {
		t.Errorf("expected 503, got %d", w.Code)
	}
}

func TestHandleGetService(t *testing.T) {
	srv, s := setupTestServer(t)
	defer s.Close()

	ctx := context.Background()
	srv.discoverer.Start(ctx)
	defer srv.discoverer.Stop()

	svc := &registry.Service{ID: "svc-1", Name: "web", Address: "10.0.0.1", Port: 8001, Status: registry.StatusUp}
	data, _ := svc.Marshal()
	s.Put(ctx, svc.Key(), data, 0)

	time.Sleep(100 * time.Millisecond)

	req := httptest.NewRequest("GET", "/services/web", nil)
	w := httptest.NewRecorder()

	srv.handleGetService(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", w.Code)
	}
}

func TestHandleGetServiceNotFound(t *testing.T) {
	srv, s := setupTestServer(t)
	defer s.Close()

	ctx := context.Background()
	srv.discoverer.Start(ctx)
	defer srv.discoverer.Stop()

	req := httptest.NewRequest("GET", "/services/nonexistent", nil)
	w := httptest.NewRecorder()

	srv.handleGetService(w, req)

	if w.Code != http.StatusNotFound {
		t.Errorf("expected 404, got %d", w.Code)
	}
}

func TestHandleDiscoverByTags(t *testing.T) {
	srv, s := setupTestServer(t)
	defer s.Close()

	ctx := context.Background()
	srv.discoverer.Start(ctx)
	defer srv.discoverer.Stop()

	// Add services with metadata
	svc1 := &registry.Service{
		ID: "svc-1", Name: "web", Address: "10.0.0.1", Port: 8001,
		Status:   registry.StatusUp,
		Metadata: map[string]string{"env": "prod", "version": "1.0"},
	}
	svc2 := &registry.Service{
		ID: "svc-2", Name: "web", Address: "10.0.0.2", Port: 8002,
		Status:   registry.StatusUp,
		Metadata: map[string]string{"env": "staging", "version": "1.0"},
	}
	data1, _ := svc1.Marshal()
	data2, _ := svc2.Marshal()
	s.Put(ctx, svc1.Key(), data1, 0)
	s.Put(ctx, svc2.Key(), data2, 0)

	time.Sleep(100 * time.Millisecond)

	// Filter by env=prod
	req := httptest.NewRequest("GET", "/discover/tags?name=web&env=prod", nil)
	w := httptest.NewRecorder()
	srv.handleDiscoverByTags(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", w.Code)
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

func TestHandleDiscoverByTagsMissingName(t *testing.T) {
	srv, s := setupTestServer(t)
	defer s.Close()

	req := httptest.NewRequest("GET", "/discover/tags?env=prod", nil)
	w := httptest.NewRecorder()
	srv.handleDiscoverByTags(w, req)

	if w.Code != http.StatusBadRequest {
		t.Errorf("expected 400, got %d", w.Code)
	}
}

func TestHandleDiscoverByTagsMethodNotAllowed(t *testing.T) {
	srv, s := setupTestServer(t)
	defer s.Close()

	req := httptest.NewRequest("POST", "/discover/tags?name=web&env=prod", nil)
	w := httptest.NewRecorder()
	srv.handleDiscoverByTags(w, req)

	if w.Code != http.StatusMethodNotAllowed {
		t.Errorf("expected 405, got %d", w.Code)
	}
}

func TestHandleChooseByTags(t *testing.T) {
	srv, s := setupTestServer(t)
	defer s.Close()

	ctx := context.Background()
	srv.discoverer.Start(ctx)
	defer srv.discoverer.Stop()

	// Add services with metadata
	svc1 := &registry.Service{
		ID: "svc-1", Name: "web", Address: "10.0.0.1", Port: 8001,
		Status:   registry.StatusUp,
		Metadata: map[string]string{"env": "prod"},
	}
	svc2 := &registry.Service{
		ID: "svc-2", Name: "web", Address: "10.0.0.2", Port: 8002,
		Status:   registry.StatusUp,
		Metadata: map[string]string{"env": "prod"},
	}
	data1, _ := svc1.Marshal()
	data2, _ := svc2.Marshal()
	s.Put(ctx, svc1.Key(), data1, 0)
	s.Put(ctx, svc2.Key(), data2, 0)

	time.Sleep(100 * time.Millisecond)

	// Choose with tag filter
	selected := make(map[string]bool)
	for i := 0; i < 10; i++ {
		req := httptest.NewRequest("GET", "/choose/tags?name=web&env=prod", nil)
		w := httptest.NewRecorder()
		srv.handleChooseByTags(w, req)

		if w.Code != http.StatusOK {
			t.Fatalf("expected 200, got %d", w.Code)
		}

		var svc registry.Service
		json.NewDecoder(w.Body).Decode(&svc)
		selected[svc.ID] = true
	}

	if len(selected) < 2 {
		t.Errorf("expected both services to be selected, got %v", selected)
	}
}

func TestHandleChooseByTagsNoMatch(t *testing.T) {
	srv, s := setupTestServer(t)
	defer s.Close()

	ctx := context.Background()
	srv.discoverer.Start(ctx)
	defer srv.discoverer.Stop()

	req := httptest.NewRequest("GET", "/choose/tags?name=web&env=prod", nil)
	w := httptest.NewRecorder()
	srv.handleChooseByTags(w, req)

	if w.Code != http.StatusServiceUnavailable {
		t.Errorf("expected 503, got %d", w.Code)
	}
}

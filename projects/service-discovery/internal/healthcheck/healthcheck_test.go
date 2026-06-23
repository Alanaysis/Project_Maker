package healthcheck

import (
	"context"
	"net"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/anthropic/service-discovery/internal/registry"
	"github.com/anthropic/service-discovery/internal/store"
)

func putService(t *testing.T, s store.Store, ctx context.Context, svc *registry.Service) {
	t.Helper()
	data, _ := svc.Marshal()
	s.Put(ctx, svc.Key(), data, 0)
}

func TestCheckerTCPHealthy(t *testing.T) {
	// Start a TCP listener
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("listen failed: %v", err)
	}
	defer listener.Close()

	go func() {
		for {
			conn, err := listener.Accept()
			if err != nil {
				return
			}
			conn.Close()
		}
	}()

	addr := listener.Addr().(*net.TCPAddr)

	s := store.NewMemStore()
	defer s.Close()
	ctx := context.Background()

	svc := &registry.Service{
		ID:      "svc-1",
		Name:    "web",
		Address: addr.IP.String(),
		Port:    addr.Port,
		Status:  registry.StatusUp,
	}
	putService(t, s, ctx, svc)

	config := DefaultConfig()
	config.Interval = 100 * time.Millisecond
	config.Timeout = 500 * time.Millisecond

	checker := New(s, config)

	// Perform a single check
	result := checker.check(ctx, svc)
	if !result.Healthy {
		t.Errorf("expected healthy, got error: %v", result.Error)
	}
	if result.Latency <= 0 {
		t.Error("expected positive latency")
	}
}

func TestCheckerTCPUnhealthy(t *testing.T) {
	s := store.NewMemStore()
	defer s.Close()
	ctx := context.Background()

	svc := &registry.Service{
		ID:      "svc-1",
		Name:    "web",
		Address: "127.0.0.1",
		Port:    1, // unlikely to be open
		Status:  registry.StatusUp,
	}

	config := DefaultConfig()
	config.Timeout = 100 * time.Millisecond

	checker := New(s, config)
	result := checker.check(ctx, svc)
	if result.Healthy {
		t.Error("expected unhealthy for closed port")
	}
}

func TestCheckerHTTPHealthy(t *testing.T) {
	// Start HTTP test server
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/health" {
			w.WriteHeader(http.StatusOK)
			w.Write([]byte(`{"status":"ok"}`))
		}
	}))
	defer ts.Close()

	s := store.NewMemStore()
	defer s.Close()
	ctx := context.Background()

	// Parse the test server address
	// ts.URL is like "http://127.0.0.1:PORT"
	addr := ts.Listener.Addr().(*net.TCPAddr)

	svc := &registry.Service{
		ID:      "svc-1",
		Name:    "web",
		Address: addr.IP.String(),
		Port:    addr.Port,
		Status:  registry.StatusUp,
	}

	config := DefaultConfig()
	config.Type = CheckHTTP
	config.HTTPPath = "/health"

	checker := New(s, config)
	result := checker.check(ctx, svc)
	if !result.Healthy {
		t.Errorf("expected healthy, got error: %v", result.Error)
	}
}

func TestCheckerHTTPUnhealthy(t *testing.T) {
	// Start HTTP test server that returns 500
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer ts.Close()

	s := store.NewMemStore()
	defer s.Close()
	ctx := context.Background()

	addr := ts.Listener.Addr().(*net.TCPAddr)

	svc := &registry.Service{
		ID:      "svc-1",
		Name:    "web",
		Address: addr.IP.String(),
		Port:    addr.Port,
		Status:  registry.StatusUp,
	}

	config := DefaultConfig()
	config.Type = CheckHTTP

	checker := New(s, config)
	result := checker.check(ctx, svc)
	if result.Healthy {
		t.Error("expected unhealthy for 500 status")
	}
}

func TestCheckerGetResult(t *testing.T) {
	s := store.NewMemStore()
	defer s.Close()

	checker := New(s, DefaultConfig())

	// No result initially
	_, ok := checker.GetResult("svc-1")
	if ok {
		t.Error("expected no result initially")
	}

	// Manually set a result
	checker.mu.Lock()
	checker.results["svc-1"] = &CheckResult{
		ServiceID: "svc-1",
		Healthy:   true,
		Latency:   10 * time.Millisecond,
	}
	checker.mu.Unlock()

	result, ok := checker.GetResult("svc-1")
	if !ok {
		t.Fatal("expected result to exist")
	}
	if !result.Healthy {
		t.Error("expected healthy")
	}
}

func TestCheckerGetAllResults(t *testing.T) {
	s := store.NewMemStore()
	defer s.Close()

	checker := New(s, DefaultConfig())

	checker.mu.Lock()
	checker.results["svc-1"] = &CheckResult{ServiceID: "svc-1", Healthy: true}
	checker.results["svc-2"] = &CheckResult{ServiceID: "svc-2", Healthy: false}
	checker.mu.Unlock()

	results := checker.GetAllResults()
	if len(results) != 2 {
		t.Errorf("expected 2 results, got %d", len(results))
	}
}

func TestExtractIDFromKey(t *testing.T) {
	tests := []struct {
		key  string
		want string
	}{
		{"/services/web/svc-1", "svc-1"},
		{"/services/api/instance-42", "instance-42"},
	}

	for _, tt := range tests {
		got := extractIDFromKey(tt.key)
		if got != tt.want {
			t.Errorf("extractIDFromKey(%s) = %s, want %s", tt.key, got, tt.want)
		}
	}
}

func TestDefaultConfig(t *testing.T) {
	config := DefaultConfig()

	if config.Interval != 5*time.Second {
		t.Errorf("Interval = %v, want 5s", config.Interval)
	}
	if config.Timeout != 2*time.Second {
		t.Errorf("Timeout = %v, want 2s", config.Timeout)
	}
	if config.Type != CheckTCP {
		t.Errorf("Type = %v, want CheckTCP", config.Type)
	}
	if config.HTTPPath != "/health" {
		t.Errorf("HTTPPath = %s, want /health", config.HTTPPath)
	}
}

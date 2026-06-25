package discovery

import (
	"context"
	"testing"
	"time"

	"github.com/anthropic/service-discovery/internal/registry"
	"github.com/anthropic/service-discovery/internal/store"
)

func putService(t *testing.T, s store.Store, ctx context.Context, svc *registry.Service) {
	t.Helper()
	data, err := svc.Marshal()
	if err != nil {
		t.Fatalf("Marshal failed: %v", err)
	}
	if err := s.Put(ctx, svc.Key(), data, 0); err != nil {
		t.Fatalf("Put failed: %v", err)
	}
}

func TestDiscovererStart(t *testing.T) {
	s := store.NewMemStore()
	defer s.Close()
	ctx := context.Background()

	// Pre-register some services
	putService(t, s, ctx, &registry.Service{ID: "svc-1", Name: "web", Address: "10.0.0.1", Port: 8001, Status: registry.StatusUp})
	putService(t, s, ctx, &registry.Service{ID: "svc-2", Name: "web", Address: "10.0.0.2", Port: 8002, Status: registry.StatusUp})
	putService(t, s, ctx, &registry.Service{ID: "svc-3", Name: "api", Address: "10.0.0.3", Port: 9001, Status: registry.StatusUp})

	d := New(s)
	defer d.Stop()

	if err := d.Start(ctx); err != nil {
		t.Fatalf("Start failed: %v", err)
	}

	// Give it a moment to load
	time.Sleep(50 * time.Millisecond)

	// Check discovered services
	webServices := d.GetServices("web")
	if len(webServices) != 2 {
		t.Errorf("expected 2 web services, got %d", len(webServices))
	}

	apiServices := d.GetServices("api")
	if len(apiServices) != 1 {
		t.Errorf("expected 1 api service, got %d", len(apiServices))
	}
}

func TestDiscovererWatchNewService(t *testing.T) {
	s := store.NewMemStore()
	defer s.Close()
	ctx := context.Background()

	d := New(s)
	defer d.Stop()

	if err := d.Start(ctx); err != nil {
		t.Fatalf("Start failed: %v", err)
	}

	// Add a new service
	time.Sleep(50 * time.Millisecond)
	putService(t, s, ctx, &registry.Service{ID: "svc-1", Name: "web", Address: "10.0.0.1", Port: 8001, Status: registry.StatusUp})

	// Give it a moment to process the event
	time.Sleep(100 * time.Millisecond)

	services := d.GetServices("web")
	if len(services) != 1 {
		t.Errorf("expected 1 web service, got %d", len(services))
	}
}

func TestDiscovererWatchRemoveService(t *testing.T) {
	s := store.NewMemStore()
	defer s.Close()
	ctx := context.Background()

	svc := &registry.Service{ID: "svc-1", Name: "web", Address: "10.0.0.1", Port: 8001, Status: registry.StatusUp}
	putService(t, s, ctx, svc)

	d := New(s)
	defer d.Stop()
	d.Start(ctx)
	time.Sleep(50 * time.Millisecond)

	// Verify service exists
	if d.Count("web") != 1 {
		t.Fatalf("expected 1 web service initially")
	}

	// Remove the service
	s.Delete(ctx, svc.Key())
	time.Sleep(100 * time.Millisecond)

	if d.Count("web") != 0 {
		t.Errorf("expected 0 web services after delete, got %d", d.Count("web"))
	}
}

func TestDiscovererGetAllServices(t *testing.T) {
	s := store.NewMemStore()
	defer s.Close()
	ctx := context.Background()

	putService(t, s, ctx, &registry.Service{ID: "svc-1", Name: "web", Address: "10.0.0.1", Port: 8001, Status: registry.StatusUp})
	putService(t, s, ctx, &registry.Service{ID: "svc-2", Name: "api", Address: "10.0.0.2", Port: 9001, Status: registry.StatusUp})

	d := New(s)
	defer d.Stop()
	d.Start(ctx)
	time.Sleep(50 * time.Millisecond)

	all := d.GetAllServices()
	if len(all) != 2 {
		t.Errorf("expected 2 service names, got %d", len(all))
	}
	if len(all["web"]) != 1 {
		t.Errorf("expected 1 web service, got %d", len(all["web"]))
	}
	if len(all["api"]) != 1 {
		t.Errorf("expected 1 api service, got %d", len(all["api"]))
	}
}

func TestDiscovererGetServiceNames(t *testing.T) {
	s := store.NewMemStore()
	defer s.Close()
	ctx := context.Background()

	putService(t, s, ctx, &registry.Service{ID: "svc-1", Name: "web", Address: "10.0.0.1", Port: 8001, Status: registry.StatusUp})
	putService(t, s, ctx, &registry.Service{ID: "svc-2", Name: "api", Address: "10.0.0.2", Port: 9001, Status: registry.StatusUp})

	d := New(s)
	defer d.Stop()
	d.Start(ctx)
	time.Sleep(50 * time.Millisecond)

	names := d.GetServiceNames()
	if len(names) != 2 {
		t.Errorf("expected 2 names, got %d", len(names))
	}
}

func TestDiscovererOnChange(t *testing.T) {
	s := store.NewMemStore()
	defer s.Close()
	ctx := context.Background()

	onChangeCalled := make(chan []*registry.Service, 10)
	onChange := func(services []*registry.Service) {
		onChangeCalled <- services
	}

	d := New(s, WithOnChange(onChange))
	defer d.Stop()
	d.Start(ctx)
	time.Sleep(50 * time.Millisecond)

	// Add a service - should trigger onChange
	putService(t, s, ctx, &registry.Service{ID: "svc-1", Name: "web", Address: "10.0.0.1", Port: 8001, Status: registry.StatusUp})

	select {
	case services := <-onChangeCalled:
		if len(services) != 1 {
			t.Errorf("expected 1 service in callback, got %d", len(services))
		}
	case <-time.After(time.Second):
		t.Fatal("timeout waiting for onChange callback")
	}
}

func TestDiscovererCount(t *testing.T) {
	s := store.NewMemStore()
	defer s.Close()
	ctx := context.Background()

	putService(t, s, ctx, &registry.Service{ID: "svc-1", Name: "web", Address: "10.0.0.1", Port: 8001, Status: registry.StatusUp})
	putService(t, s, ctx, &registry.Service{ID: "svc-2", Name: "web", Address: "10.0.0.2", Port: 8002, Status: registry.StatusUp})

	d := New(s)
	defer d.Stop()
	d.Start(ctx)
	time.Sleep(50 * time.Millisecond)

	if d.Count("web") != 2 {
		t.Errorf("expected 2 web services, got %d", d.Count("web"))
	}
	if d.Count("api") != 0 {
		t.Errorf("expected 0 api services, got %d", d.Count("api"))
	}
}

func TestDiscovererGetServicesFiltersDown(t *testing.T) {
	s := store.NewMemStore()
	defer s.Close()
	ctx := context.Background()

	putService(t, s, ctx, &registry.Service{ID: "svc-1", Name: "web", Address: "10.0.0.1", Port: 8001, Status: registry.StatusUp})
	putService(t, s, ctx, &registry.Service{ID: "svc-2", Name: "web", Address: "10.0.0.2", Port: 8002, Status: registry.StatusDown})

	d := New(s)
	defer d.Stop()
	d.Start(ctx)
	time.Sleep(50 * time.Millisecond)

	// Only StatusUp services should be returned
	services := d.GetServices("web")
	if len(services) != 1 {
		t.Errorf("expected 1 healthy web service, got %d", len(services))
	}
	if len(services) > 0 && services[0].ID != "svc-1" {
		t.Errorf("expected svc-1, got %s", services[0].ID)
	}
}

func TestDiscovererNoServices(t *testing.T) {
	s := store.NewMemStore()
	defer s.Close()
	ctx := context.Background()

	d := New(s)
	defer d.Stop()
	d.Start(ctx)
	time.Sleep(50 * time.Millisecond)

	services := d.GetServices("nonexistent")
	if len(services) != 0 {
		t.Errorf("expected 0 services, got %d", len(services))
	}

	all := d.GetAllServices()
	if len(all) != 0 {
		t.Errorf("expected 0 service groups, got %d", len(all))
	}
}

func TestExtractIDFromKey(t *testing.T) {
	tests := []struct {
		key  string
		want string
	}{
		{"/services/web/svc-1", "svc-1"},
		{"/services/api/instance-42", "instance-42"},
		{"/services/x", "x"},
	}

	for _, tt := range tests {
		got := extractIDFromKey(tt.key)
		if got != tt.want {
			t.Errorf("extractIDFromKey(%s) = %s, want %s", tt.key, got, tt.want)
		}
	}
}

func TestDiscovererGetServicesByTags(t *testing.T) {
	s := store.NewMemStore()
	defer s.Close()
	ctx := context.Background()

	putService(t, s, ctx, &registry.Service{
		ID: "svc-1", Name: "web", Address: "10.0.0.1", Port: 8001,
		Status:   registry.StatusUp,
		Metadata: map[string]string{"env": "prod", "version": "1.0"},
	})
	putService(t, s, ctx, &registry.Service{
		ID: "svc-2", Name: "web", Address: "10.0.0.2", Port: 8002,
		Status:   registry.StatusUp,
		Metadata: map[string]string{"env": "staging", "version": "1.0"},
	})
	putService(t, s, ctx, &registry.Service{
		ID: "svc-3", Name: "web", Address: "10.0.0.3", Port: 8003,
		Status:   registry.StatusUp,
		Metadata: map[string]string{"env": "prod", "version": "2.0"},
	})

	d := New(s)
	defer d.Stop()
	d.Start(ctx)
	time.Sleep(50 * time.Millisecond)

	// Filter by env=prod
	services := d.GetServicesByTags("web", map[string]string{"env": "prod"})
	if len(services) != 2 {
		t.Errorf("expected 2 prod services, got %d", len(services))
	}

	// Filter by env=prod AND version=1.0
	services = d.GetServicesByTags("web", map[string]string{"env": "prod", "version": "1.0"})
	if len(services) != 1 {
		t.Errorf("expected 1 prod v1.0 service, got %d", len(services))
	}

	// Filter by nonexistent tag
	services = d.GetServicesByTags("web", map[string]string{"region": "us-east"})
	if len(services) != 0 {
		t.Errorf("expected 0 services, got %d", len(services))
	}

	// Empty tags should return all
	services = d.GetServicesByTags("web", map[string]string{})
	if len(services) != 3 {
		t.Errorf("expected 3 services with empty tags, got %d", len(services))
	}
}

func TestDiscovererGetAllServicesByTags(t *testing.T) {
	s := store.NewMemStore()
	defer s.Close()
	ctx := context.Background()

	putService(t, s, ctx, &registry.Service{
		ID: "svc-1", Name: "web", Address: "10.0.0.1", Port: 8001,
		Status:   registry.StatusUp,
		Metadata: map[string]string{"env": "prod"},
	})
	putService(t, s, ctx, &registry.Service{
		ID: "svc-2", Name: "api", Address: "10.0.0.2", Port: 9001,
		Status:   registry.StatusUp,
		Metadata: map[string]string{"env": "prod"},
	})
	putService(t, s, ctx, &registry.Service{
		ID: "svc-3", Name: "api", Address: "10.0.0.3", Port: 9002,
		Status:   registry.StatusUp,
		Metadata: map[string]string{"env": "staging"},
	})

	d := New(s)
	defer d.Stop()
	d.Start(ctx)
	time.Sleep(50 * time.Millisecond)

	// Filter by env=prod
	all := d.GetAllServicesByTags(map[string]string{"env": "prod"})
	if len(all) != 2 {
		t.Errorf("expected 2 service names, got %d", len(all))
	}
	if len(all["web"]) != 1 {
		t.Errorf("expected 1 web service, got %d", len(all["web"]))
	}
	if len(all["api"]) != 1 {
		t.Errorf("expected 1 api service, got %d", len(all["api"]))
	}
}

func TestMatchTags(t *testing.T) {
	tests := []struct {
		name   string
		svc    *registry.Service
		tags   map[string]string
		expect bool
	}{
		{
			name:   "nil tags matches all",
			svc:    &registry.Service{Metadata: map[string]string{"env": "prod"}},
			tags:   nil,
			expect: true,
		},
		{
			name:   "empty tags matches all",
			svc:    &registry.Service{Metadata: map[string]string{"env": "prod"}},
			tags:   map[string]string{},
			expect: true,
		},
		{
			name:   "nil metadata with tags",
			svc:    &registry.Service{},
			tags:   map[string]string{"env": "prod"},
			expect: false,
		},
		{
			name:   "matching tag",
			svc:    &registry.Service{Metadata: map[string]string{"env": "prod"}},
			tags:   map[string]string{"env": "prod"},
			expect: true,
		},
		{
			name:   "non-matching tag value",
			svc:    &registry.Service{Metadata: map[string]string{"env": "prod"}},
			tags:   map[string]string{"env": "staging"},
			expect: false,
		},
		{
			name:   "missing tag key",
			svc:    &registry.Service{Metadata: map[string]string{"env": "prod"}},
			tags:   map[string]string{"region": "us-east"},
			expect: false,
		},
		{
			name:   "multiple tags all match",
			svc:    &registry.Service{Metadata: map[string]string{"env": "prod", "version": "1.0"}},
			tags:   map[string]string{"env": "prod", "version": "1.0"},
			expect: true,
		},
		{
			name:   "multiple tags partial match",
			svc:    &registry.Service{Metadata: map[string]string{"env": "prod", "version": "1.0"}},
			tags:   map[string]string{"env": "prod", "version": "2.0"},
			expect: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := matchTags(tt.svc, tt.tags)
			if got != tt.expect {
				t.Errorf("matchTags() = %v, want %v", got, tt.expect)
			}
		})
	}
}

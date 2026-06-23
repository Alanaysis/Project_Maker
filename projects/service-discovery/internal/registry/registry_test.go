package registry

import (
	"context"
	"testing"
	"time"

	"github.com/anthropic/service-discovery/internal/store"
)

func newTestService(id, name string) *Service {
	return &Service{
		ID:      id,
		Name:    name,
		Address: "127.0.0.1",
		Port:    8080,
	}
}

func TestServiceValidate(t *testing.T) {
	tests := []struct {
		name    string
		svc     *Service
		wantErr bool
	}{
		{"valid", &Service{ID: "1", Name: "web", Address: "127.0.0.1", Port: 8080}, false},
		{"missing ID", &Service{Name: "web", Address: "127.0.0.1", Port: 8080}, true},
		{"missing Name", &Service{ID: "1", Address: "127.0.0.1", Port: 8080}, true},
		{"missing Address", &Service{ID: "1", Name: "web", Port: 8080}, true},
		{"invalid port 0", &Service{ID: "1", Name: "web", Address: "127.0.0.1", Port: 0}, true},
		{"invalid port negative", &Service{ID: "1", Name: "web", Address: "127.0.0.1", Port: -1}, true},
		{"invalid port too high", &Service{ID: "1", Name: "web", Address: "127.0.0.1", Port: 70000}, true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := tt.svc.Validate()
			if (err != nil) != tt.wantErr {
				t.Errorf("Validate() error = %v, wantErr %v", err, tt.wantErr)
			}
		})
	}
}

func TestServiceKey(t *testing.T) {
	svc := &Service{ID: "instance-1", Name: "web-api"}
	expected := "/services/web-api/instance-1"
	if got := svc.Key(); got != expected {
		t.Errorf("Key() = %s, want %s", got, expected)
	}
}

func TestServiceEndpoint(t *testing.T) {
	svc := &Service{Address: "10.0.0.1", Port: 8080}
	expected := "10.0.0.1:8080"
	if got := svc.Endpoint(); got != expected {
		t.Errorf("Endpoint() = %s, want %s", got, expected)
	}
}

func TestServiceMarshalUnmarshal(t *testing.T) {
	original := &Service{
		ID:       "svc-1",
		Name:     "web",
		Address:  "10.0.0.1",
		Port:     8080,
		Metadata: map[string]string{"version": "1.0"},
		Status:   StatusUp,
	}

	data, err := original.Marshal()
	if err != nil {
		t.Fatalf("Marshal failed: %v", err)
	}

	restored, err := UnmarshalService(data)
	if err != nil {
		t.Fatalf("Unmarshal failed: %v", err)
	}

	if restored.ID != original.ID {
		t.Errorf("ID = %s, want %s", restored.ID, original.ID)
	}
	if restored.Name != original.Name {
		t.Errorf("Name = %s, want %s", restored.Name, original.Name)
	}
	if restored.Endpoint() != original.Endpoint() {
		t.Errorf("Endpoint = %s, want %s", restored.Endpoint(), original.Endpoint())
	}
	if restored.Metadata["version"] != "1.0" {
		t.Errorf("Metadata[version] = %s, want 1.0", restored.Metadata["version"])
	}
}

func TestServiceStatusString(t *testing.T) {
	tests := []struct {
		status ServiceStatus
		want   string
	}{
		{StatusUp, "up"},
		{StatusDown, "down"},
		{StatusStarting, "starting"},
		{ServiceStatus(99), "unknown"},
	}

	for _, tt := range tests {
		if got := tt.status.String(); got != tt.want {
			t.Errorf("Status(%d).String() = %s, want %s", tt.status, got, tt.want)
		}
	}
}

func TestRegistryRegister(t *testing.T) {
	s := store.NewMemStore()
	defer s.Close()
	r := New(s)
	defer r.Stop()

	ctx := context.Background()
	svc := newTestService("svc-1", "web")

	err := r.Register(ctx, svc, 10*time.Second)
	if err != nil {
		t.Fatalf("Register failed: %v", err)
	}

	// Verify service is in the store
	key := svc.Key()
	data, err := s.Get(ctx, key)
	if err != nil {
		t.Fatalf("Service not in store: %v", err)
	}

	stored, err := UnmarshalService(data)
	if err != nil {
		t.Fatalf("Failed to unmarshal: %v", err)
	}

	if stored.ID != svc.ID {
		t.Errorf("stored ID = %s, want %s", stored.ID, svc.ID)
	}
}

func TestRegistryDeregister(t *testing.T) {
	s := store.NewMemStore()
	defer s.Close()
	r := New(s)
	defer r.Stop()

	ctx := context.Background()
	svc := newTestService("svc-1", "web")

	r.Register(ctx, svc, 10*time.Second)

	err := r.Deregister(ctx, "svc-1")
	if err != nil {
		t.Fatalf("Deregister failed: %v", err)
	}

	// Verify service is removed from store
	_, err = s.Get(ctx, svc.Key())
	if err == nil {
		t.Error("expected service to be removed from store")
	}
}

func TestRegistryDeregisterNotFound(t *testing.T) {
	s := store.NewMemStore()
	defer s.Close()
	r := New(s)
	defer r.Stop()

	err := r.Deregister(context.Background(), "nonexistent")
	if err != ErrServiceNotFound {
		t.Errorf("expected ErrServiceNotFound, got %v", err)
	}
}

func TestRegistryGetService(t *testing.T) {
	s := store.NewMemStore()
	defer s.Close()
	r := New(s)
	defer r.Stop()

	ctx := context.Background()
	svc := newTestService("svc-1", "web")

	r.Register(ctx, svc, 10*time.Second)

	got, err := r.GetService("svc-1")
	if err != nil {
		t.Fatalf("GetService failed: %v", err)
	}

	if got.ID != svc.ID {
		t.Errorf("ID = %s, want %s", got.ID, svc.ID)
	}
}

func TestRegistryListRegistered(t *testing.T) {
	s := store.NewMemStore()
	defer s.Close()
	r := New(s)
	defer r.Stop()

	ctx := context.Background()
	r.Register(ctx, newTestService("svc-1", "web"), 10*time.Second)
	r.Register(ctx, newTestService("svc-2", "web"), 10*time.Second)
	r.Register(ctx, newTestService("svc-3", "api"), 10*time.Second)

	services := r.ListRegistered()
	if len(services) != 3 {
		t.Errorf("expected 3 services, got %d", len(services))
	}
}

func TestRegistryInvalidService(t *testing.T) {
	s := store.NewMemStore()
	defer s.Close()
	r := New(s)
	defer r.Stop()

	// Missing required fields
	svc := &Service{ID: "svc-1"}
	err := r.Register(context.Background(), svc, 10*time.Second)
	if err == nil {
		t.Error("expected error for invalid service")
	}
}

func TestRegistryHeartbeat(t *testing.T) {
	s := store.NewMemStore()
	defer s.Close()
	r := New(s)
	defer r.Stop()

	ctx := context.Background()
	svc := newTestService("svc-1", "web")

	// Register with a TTL that gives the heartbeat time to renew.
	// Heartbeat interval = TTL/3. We wait ~1x TTL, so at least 2 heartbeats fire.
	err := r.Register(ctx, svc, 300*time.Millisecond)
	if err != nil {
		t.Fatalf("Register failed: %v", err)
	}

	// Wait ~1 TTL - heartbeat should have renewed the lease by now
	time.Sleep(200 * time.Millisecond)

	// Service should still be in store
	_, err = s.Get(ctx, svc.Key())
	if err != nil {
		t.Errorf("service should still be alive after heartbeat: %v", err)
	}
}

func TestRegistryStop(t *testing.T) {
	s := store.NewMemStore()
	defer s.Close()
	r := New(s)

	ctx := context.Background()
	r.Register(ctx, newTestService("svc-1", "web"), 10*time.Second)
	r.Register(ctx, newTestService("svc-2", "api"), 10*time.Second)

	r.Stop()

	// All services should be removed
	services := r.ListRegistered()
	if len(services) != 0 {
		t.Errorf("expected 0 services after stop, got %d", len(services))
	}
}

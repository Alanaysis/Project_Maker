package loadbalancer

import (
	"sync"
	"testing"

	"github.com/anthropic/service-discovery/internal/registry"
)

func newService(id, name string, port int) *registry.Service {
	return &registry.Service{
		ID:      id,
		Name:    name,
		Address: "127.0.0.1",
		Port:    port,
		Status:  registry.StatusUp,
	}
}

func newServiceWithWeight(id, name string, port int, weight string) *registry.Service {
	return &registry.Service{
		ID:      id,
		Name:    name,
		Address: "127.0.0.1",
		Port:    port,
		Status:  registry.StatusUp,
		Metadata: map[string]string{
			"weight": weight,
		},
	}
}

func TestRoundRobinBalancer(t *testing.T) {
	b := NewRoundRobinBalancer()

	services := []*registry.Service{
		newService("svc-1", "web", 8001),
		newService("svc-2", "web", 8002),
		newService("svc-3", "web", 8003),
	}

	// Should cycle through services
	selected := make(map[string]int)
	for i := 0; i < 9; i++ {
		svc, err := b.Select(services)
		if err != nil {
			t.Fatalf("Select failed: %v", err)
		}
		selected[svc.ID]++
	}

	// Each service should be selected 3 times
	for id, count := range selected {
		if count != 3 {
			t.Errorf("service %s selected %d times, expected 3", id, count)
		}
	}
}

func TestRoundRobinEmpty(t *testing.T) {
	b := NewRoundRobinBalancer()

	_, err := b.Select(nil)
	if err != ErrNoServices {
		t.Errorf("expected ErrNoServices, got %v", err)
	}

	_, err = b.Select([]*registry.Service{})
	if err != ErrNoServices {
		t.Errorf("expected ErrNoServices, got %v", err)
	}
}

func TestRoundRobinSingle(t *testing.T) {
	b := NewRoundRobinBalancer()

	services := []*registry.Service{
		newService("svc-1", "web", 8001),
	}

	for i := 0; i < 5; i++ {
		svc, err := b.Select(services)
		if err != nil {
			t.Fatalf("Select failed: %v", err)
		}
		if svc.ID != "svc-1" {
			t.Errorf("expected svc-1, got %s", svc.ID)
		}
	}
}

func TestRandomBalancer(t *testing.T) {
	b := NewRandomBalancer()

	services := []*registry.Service{
		newService("svc-1", "web", 8001),
		newService("svc-2", "web", 8002),
		newService("svc-3", "web", 8003),
	}

	selected := make(map[string]int)
	for i := 0; i < 300; i++ {
		svc, err := b.Select(services)
		if err != nil {
			t.Fatalf("Select failed: %v", err)
		}
		selected[svc.ID]++
	}

	// Each service should be selected at least once (statistically)
	for _, svc := range services {
		if selected[svc.ID] == 0 {
			t.Errorf("service %s was never selected", svc.ID)
		}
	}
}

func TestRandomEmpty(t *testing.T) {
	b := NewRandomBalancer()

	_, err := b.Select(nil)
	if err != ErrNoServices {
		t.Errorf("expected ErrNoServices, got %v", err)
	}
}

func TestWeightedRoundRobinBalancer(t *testing.T) {
	b := NewWeightedRoundRobinBalancer()

	services := []*registry.Service{
		newServiceWithWeight("svc-1", "web", 8001, "3"),
		newServiceWithWeight("svc-2", "web", 8002, "1"),
	}

	// With weights 3 and 1, svc-1 should be selected 3x more often
	selected := make(map[string]int)
	for i := 0; i < 8; i++ {
		svc, err := b.Select(services)
		if err != nil {
			t.Fatalf("Select failed: %v", err)
		}
		selected[svc.ID]++
	}

	// svc-1 should be selected 6 times (3/4 of 8), svc-2 should be 2 times
	if selected["svc-1"] != 6 {
		t.Errorf("svc-1 selected %d times, expected 6", selected["svc-1"])
	}
	if selected["svc-2"] != 2 {
		t.Errorf("svc-2 selected %d times, expected 2", selected["svc-2"])
	}
}

func TestWeightedRoundRobinDefaultWeight(t *testing.T) {
	b := NewWeightedRoundRobinBalancer()

	// Services without weight metadata should default to weight 1
	services := []*registry.Service{
		newService("svc-1", "web", 8001),
		newService("svc-2", "web", 8002),
	}

	selected := make(map[string]int)
	for i := 0; i < 6; i++ {
		svc, err := b.Select(services)
		if err != nil {
			t.Fatalf("Select failed: %v", err)
		}
		selected[svc.ID]++
	}

	// Should be evenly distributed (3 each)
	if selected["svc-1"] != 3 {
		t.Errorf("svc-1 selected %d times, expected 3", selected["svc-1"])
	}
	if selected["svc-2"] != 3 {
		t.Errorf("svc-2 selected %d times, expected 3", selected["svc-2"])
	}
}

func TestWeightedRoundRobinEmpty(t *testing.T) {
	b := NewWeightedRoundRobinBalancer()

	_, err := b.Select(nil)
	if err != ErrNoServices {
		t.Errorf("expected ErrNoServices, got %v", err)
	}
}

func TestNewBalancerFactory(t *testing.T) {
	tests := []struct {
		strategy Strategy
		wantType string
	}{
		{RoundRobin, "*loadbalancer.RoundRobinBalancer"},
		{Random, "*loadbalancer.RandomBalancer"},
		{WeightedRoundRobin, "*loadbalancer.WeightedRoundRobinBalancer"},
		{Strategy(99), "*loadbalancer.RoundRobinBalancer"}, // default
	}

	for _, tt := range tests {
		b := New(tt.strategy)
		if b == nil {
			t.Errorf("New(%v) returned nil", tt.strategy)
		}
	}
}

func TestRoundRobinConcurrent(t *testing.T) {
	b := NewRoundRobinBalancer()

	services := []*registry.Service{
		newService("svc-1", "web", 8001),
		newService("svc-2", "web", 8002),
		newService("svc-3", "web", 8003),
	}

	var wg sync.WaitGroup
	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			_, err := b.Select(services)
			if err != nil {
				t.Errorf("Select failed: %v", err)
			}
		}()
	}
	wg.Wait()
}

func TestRandomConcurrent(t *testing.T) {
	b := NewRandomBalancer()

	services := []*registry.Service{
		newService("svc-1", "web", 8001),
		newService("svc-2", "web", 8002),
	}

	var wg sync.WaitGroup
	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			_, err := b.Select(services)
			if err != nil {
				t.Errorf("Select failed: %v", err)
			}
		}()
	}
	wg.Wait()
}

func TestGetWeight(t *testing.T) {
	tests := []struct {
		name   string
		svc    *registry.Service
		expect int
	}{
		{"nil metadata", &registry.Service{}, 1},
		{"empty metadata", &registry.Service{Metadata: map[string]string{}}, 1},
		{"no weight key", &registry.Service{Metadata: map[string]string{"foo": "bar"}}, 1},
		{"weight 1", &registry.Service{Metadata: map[string]string{"weight": "1"}}, 1},
		{"weight 5", &registry.Service{Metadata: map[string]string{"weight": "5"}}, 5},
		{"weight 0", &registry.Service{Metadata: map[string]string{"weight": "0"}}, 1},
		{"weight invalid", &registry.Service{Metadata: map[string]string{"weight": "abc"}}, 1},
		{"weight empty", &registry.Service{Metadata: map[string]string{"weight": ""}}, 1},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := getWeight(tt.svc)
			if got != tt.expect {
				t.Errorf("getWeight() = %d, want %d", got, tt.expect)
			}
		})
	}
}

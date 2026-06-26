package service_discovery

import (
	"testing"
	"time"
)

// TestLoadBalancerRoundRobin tests round-robin load balancing.
func TestLoadBalancerRoundRobin(t *testing.T) {
	instances := []*ServiceInstance{
		{ID: "inst-1", Service: "test", Address: "127.0.0.1", Port: 8080, Metadata: map[string]string{}, TTL: 30 * time.Second},
		{ID: "inst-2", Service: "test", Address: "127.0.0.1", Port: 8081, Metadata: map[string]string{}, TTL: 30 * time.Second},
		{ID: "inst-3", Service: "test", Address: "127.0.0.1", Port: 8082, Metadata: map[string]string{}, TTL: 30 * time.Second},
	}

	lb := NewLoadBalancer(LoadBalancerRoundRobin)
	lb.SetInstances(instances)

	// Should cycle through instances in order
	expected := []string{"inst-1", "inst-2", "inst-3", "inst-1", "inst-2"}
	for i, id := range expected {
		inst := lb.Next()
		if inst == nil || inst.ID != id {
			t.Errorf("RoundRobin request %d: expected ID %s, got %v", i+1, id, inst)
		}
	}
}

// TestLoadBalancerLeastConnections tests least-connections load balancing.
func TestLoadBalancerLeastConnections(t *testing.T) {
	instances := []*ServiceInstance{
		{ID: "inst-1", Service: "test", Address: "127.0.0.1", Port: 8080, Metadata: map[string]string{"active_connections": "10"}, TTL: 30 * time.Second},
		{ID: "inst-2", Service: "test", Address: "127.0.0.1", Port: 8081, Metadata: map[string]string{"active_connections": "3"}, TTL: 30 * time.Second},
		{ID: "inst-3", Service: "test", Address: "127.0.0.1", Port: 8082, Metadata: map[string]string{"active_connections": "7"}, TTL: 30 * time.Second},
	}

	lb := NewLoadBalancer(LoadBalancerLeastConn)
	lb.SetInstances(instances)

	// Should select inst-2 (fewest connections)
	inst := lb.Next()
	if inst == nil || inst.ID != "inst-2" {
		t.Errorf("LeastConn: expected inst-2, got %v", inst)
	}

	// After adding a connection to inst-2, next should be inst-3
	inst.AddActiveConnection()
	inst = lb.Next()
	if inst == nil || inst.ID != "inst-3" {
		t.Errorf("LeastConn: expected inst-3, got %v", inst)
	}
}

// TestLoadBalancerWeighted tests weighted load balancing.
func TestLoadBalancerWeighted(t *testing.T) {
	instances := []*ServiceInstance{
		{ID: "inst-1", Service: "test", Address: "127.0.0.1", Port: 8080, Metadata: map[string]string{"weight": "3"}, TTL: 30 * time.Second},
		{ID: "inst-2", Service: "test", Address: "127.0.0.1", Port: 8081, Metadata: map[string]string{"weight": "1"}, TTL: 30 * time.Second},
	}

	lb := NewLoadBalancer(LoadBalancerWeighted)
	lb.SetInstances(instances)

	// inst-1 has weight 3, inst-2 has weight 1
	// Total weight = 4
	// Over 4 requests, inst-1 should be selected 3 times, inst-2 once
	counts := map[string]int{}
	for i := 0; i < 20; i++ {
		inst := lb.Next()
		if inst != nil {
			counts[inst.ID]++
		}
	}

	// inst-1 should get roughly 3x more traffic than inst-2
	if counts["inst-1"] < counts["inst-2"]*2 {
		t.Errorf("Weighted: expected inst-1 to get more traffic, got inst-1=%d, inst-2=%d",
			counts["inst-1"], counts["inst-2"])
	}
}

// TestLoadBalancerRandom tests random load balancing.
func TestLoadBalancerRandom(t *testing.T) {
	instances := []*ServiceInstance{
		{ID: "inst-1", Service: "test", Address: "127.0.0.1", Port: 8080, Metadata: map[string]string{}, TTL: 30 * time.Second},
		{ID: "inst-2", Service: "test", Address: "127.0.0.1", Port: 8081, Metadata: map[string]string{}, TTL: 30 * time.Second},
	}

	lb := NewLoadBalancer(LoadBalancerRandom)
	lb.SetInstances(instances)

	// Over many requests, both instances should be selected
	counts := map[string]int{}
	for i := 0; i < 100; i++ {
		inst := lb.Next()
		if inst != nil {
			counts[inst.ID]++
		}
	}

	if counts["inst-1"] == 0 || counts["inst-2"] == 0 {
		t.Errorf("Random: both instances should be selected, got %v", counts)
	}
}

// TestLoadBalancerEmpty tests behavior with no instances.
func TestLoadBalancerEmpty(t *testing.T) {
	lb := NewLoadBalancer(LoadBalancerRoundRobin)
	lb.SetInstances(nil)

	if lb.Next() != nil {
		t.Error("Next: should return nil for empty instance list")
	}

	if lb.InstanceCount() != 0 {
		t.Errorf("InstanceCount: expected 0, got %d", lb.InstanceCount())
	}
}

// TestLoadBalancerStrategyChange tests changing the load balancing strategy.
func TestLoadBalancerStrategyChange(t *testing.T) {
	instances := []*ServiceInstance{
		{ID: "inst-1", Service: "test", Address: "127.0.0.1", Port: 8080, Metadata: map[string]string{}, TTL: 30 * time.Second},
	}

	lb := NewLoadBalancer(LoadBalancerRoundRobin)
	lb.SetInstances(instances)

	if lb.GetStrategy() != LoadBalancerRoundRobin {
		t.Error("GetStrategy: should return initial strategy")
	}

	lb.SetStrategy(LoadBalancerRandom)
	if lb.GetStrategy() != LoadBalancerRandom {
		t.Error("GetStrategy: should return updated strategy")
	}
}

// TestLoadBalancerActiveConnections tests connection tracking.
func TestLoadBalancerActiveConnections(t *testing.T) {
	instance := &ServiceInstance{
		ID:       "conn-test",
		Service:  "test",
		Address:  "127.0.0.1",
		Port:     8080,
		Metadata: map[string]string{},
		TTL:      30 * time.Second,
	}

	if instance.ActiveConnections() != 0 {
		t.Errorf("ActiveConnections: expected 0, got %d", instance.ActiveConnections())
	}

	instance.AddActiveConnection()
	instance.AddActiveConnection()
	if instance.ActiveConnections() != 2 {
		t.Errorf("ActiveConnections: expected 2, got %d", instance.ActiveConnections())
	}

	instance.RemoveActiveConnection()
	if instance.ActiveConnections() != 1 {
		t.Errorf("ActiveConnections: expected 1, got %d", instance.ActiveConnections())
	}

	instance.RemoveActiveConnection()
	if instance.ActiveConnections() != 0 {
		t.Errorf("ActiveConnections: expected 0, got %d", instance.ActiveConnections())
	}
}

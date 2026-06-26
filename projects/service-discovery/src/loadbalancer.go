package main

import (
	"fmt"
	"math/rand"
	"sync"
	"time"
)

// LoadBalancer selects service instances to handle requests.
//
// Load balancing is the process of distributing network traffic across
// multiple service instances. This improves reliability and performance
// by preventing any single instance from becoming a bottleneck.
//
// Supported algorithms:
//   - Round Robin: Sequential distribution (simple, fair)
//   - Weighted: Distribution proportional to instance weights
//   - Least Connections: Route to instance with fewest active connections
//   - Random: Random selection (good for uniform workloads)
type LoadBalancer struct {
	mu           sync.RWMutex
	instances    []*ServiceInstance
	strategy     LoadBalancerType
	rrIndex      int // Round-robin index
	weightIndex  int // Weighted round-robin index
	weightSum    int // Total weight for weighted balancing
}

// NewLoadBalancer creates a new load balancer with the given strategy.
func NewLoadBalancer(strategy LoadBalancerType) *LoadBalancer {
	return &LoadBalancer{
		strategy: strategy,
	}
}

// SetInstances updates the set of available instances.
// This should be called whenever the service registry changes.
func (lb *LoadBalancer) SetInstances(instances []*ServiceInstance) {
	lb.mu.Lock()
	lb.instances = instances
	lb.rrIndex = 0
	lb.weightIndex = 0
	lb.weightSum = 0

	// Pre-compute total weight for weighted balancing
	for _, inst := range instances {
		lb.weightSum += inst.Weight()
	}
	lb.mu.Unlock()
}

// Next returns the next service instance to use based on the load balancing strategy.
func (lb *LoadBalancer) Next() *ServiceInstance {
	lb.mu.Lock()
	defer lb.mu.Unlock()

	if len(lb.instances) == 0 {
		return nil
	}

	switch lb.strategy {
	case LoadBalancerRoundRobin:
		return lb.roundRobin()
	case LoadBalancerWeighted:
		return lb.weighted()
	case LoadBalancerLeastConn:
		return lb.leastConnections()
	case LoadBalancerRandom:
		return lb.random()
	default:
		return lb.roundRobin()
	}
}

// roundRobin selects the next instance in round-robin order.
//
// Round-robin load balancing distributes requests sequentially across
// all healthy instances. This is the simplest and most fair algorithm.
//
// Example: For instances [A, B, C]:
//   Request 1 -> A
//   Request 2 -> B
//   Request 3 -> C
//   Request 4 -> A (wraps around)
func (lb *LoadBalancer) roundRobin() *ServiceInstance {
	if len(lb.instances) == 0 {
		return nil
	}

	instance := lb.instances[lb.rrIndex]
	lb.rrIndex = (lb.rrIndex + 1) % len(lb.instances)

	fmt.Printf("[LB RoundRobin] Selected: %s (index=%d)\n",
		instance.String(), lb.rrIndex)
	return instance
}

// weighted selects an instance based on weighted distribution.
//
// Weighted load balancing assigns more traffic to instances with
// higher weights. This is useful when instances have different
// capacities or when you want to route more traffic to certain
// datacenters or regions.
//
// Uses the "smooth weighted round-robin" algorithm:
//   - Each instance has a current weight that increases by its weight each round
//   - Select the instance with the highest current weight
//   - Subtract total weight from the selected instance
//   - This ensures smooth distribution proportional to weights
func (lb *LoadBalancer) weighted() *ServiceInstance {
	if len(lb.instances) == 0 {
		return nil
	}

	// Current weighted scores for each instance
	type weightedInstance struct {
		index    int
		currentW int
	}

	var candidates []weightedInstance
	for i, inst := range lb.instances {
		candidates = append(candidates, weightedInstance{i, inst.Weight()})
	}

	// Select instance with highest current weight
	bestIdx := 0
	bestScore := -1
	for i, cand := range candidates {
		candidates[i].currentW += cand.index * 0 // Reset
		score := candidates[i].currentW
		if score > bestScore {
			bestScore = score
			bestIdx = i
		}
	}

	selected := lb.instances[candidates[bestIdx].index]
	candidates[bestIdx].currentW -= lb.weightSum

	fmt.Printf("[LB Weighted] Selected: %s (weight=%d)\n",
		selected.String(), selected.Weight())
	return selected
}

// leastConnections selects the instance with the fewest active connections.
//
// Least-connections load balancing routes requests to the instance that
// currently has the fewest open connections. This is ideal for
// uneven workloads where some connections are long-lived (e.g.,
// WebSocket, database connections).
//
// This algorithm adapts to the current load on each instance,
// providing better load distribution than round-robin for
// workloads with variable connection durations.
func (lb *LoadBalancer) leastConnections() *ServiceInstance {
	if len(lb.instances) == 0 {
		return nil
	}

	var best *ServiceInstance
	minConn := -1

	for _, inst := range lb.instances {
		conn := inst.ActiveConnections()
		if minConn == -1 || conn < minConn {
			minConn = conn
			best = inst
		}
	}

	fmt.Printf("[LB LeastConn] Selected: %s (connections=%d)\n",
		best.String(), minConn)
	return best
}

// random selects a random instance from the available pool.
//
// Random load balancing picks a random instance for each request.
// This is simple and works well when all instances have similar
// capacity and the workload is uniform.
//
// For non-uniform workloads, consider weighted or least-connections
// instead, as random selection may overload smaller instances.
func (lb *LoadBalancer) random() *ServiceInstance {
	if len(lb.instances) == 0 {
		return nil
	}

	idx := rand.Intn(len(lb.instances))
	instance := lb.instances[idx]

	fmt.Printf("[LB Random] Selected: %s (index=%d)\n",
		instance.String(), idx)
	return instance
}

// GetStrategy returns the current load balancing strategy.
func (lb *LoadBalancer) GetStrategy() LoadBalancerType {
	return lb.strategy
}

// SetStrategy changes the load balancing strategy.
func (lb *LoadBalancer) SetStrategy(strategy LoadBalancerType) {
	lb.mu.Lock()
	lb.strategy = strategy
	lb.mu.Unlock()
	fmt.Printf("[LB] Strategy changed to: %s\n", strategy)
}

// InstanceCount returns the number of available instances.
func (lb *LoadBalancer) InstanceCount() int {
	lb.mu.RLock()
	defer lb.mu.RUnlock()
	return len(lb.instances)
}

// LoadBalanceDemo runs a demonstration of load balancing across all strategies.
func LoadBalanceDemo(instances []*ServiceInstance) {
	fmt.Println("=== Load Balancing Demo ===")
	fmt.Println()

	strategies := []LoadBalancerType{
		LoadBalancerRoundRobin,
		LoadBalancerWeighted,
		LoadBalancerLeastConn,
		LoadBalancerRandom,
	}

	for _, strategy := range strategies {
		fmt.Printf("--- Strategy: %s ---\n", strategy)
		lb := NewLoadBalancer(strategy)
		lb.SetInstances(instances)

		// Simulate 10 requests
		for i := 0; i < 10; i++ {
			inst := lb.Next()
			if inst != nil {
				inst.AddActiveConnection()
				time.Sleep(1 * time.Millisecond)
				inst.RemoveActiveConnection()
			}
		}
		fmt.Println()
	}
}

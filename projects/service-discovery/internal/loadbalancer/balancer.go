// Package loadbalancer implements load balancing strategies for distributing
// requests across multiple service instances.
package loadbalancer

import (
	"errors"
	"math/rand"
	"sync"
	"sync/atomic"

	"github.com/anthropic/service-discovery/internal/registry"
)

var (
	ErrNoServices = errors.New("no services available")
)

// Strategy defines the load balancing strategy type.
type Strategy int

const (
	// RoundRobin distributes requests sequentially across all instances.
	RoundRobin Strategy = iota

	// Random selects a random instance for each request.
	Random

	// WeightedRoundRobin distributes requests based on weights from metadata.
	WeightedRoundRobin
)

// Balancer selects a service instance from a list of available instances.
type Balancer interface {
	// Select returns a service instance. Returns ErrNoServices if none available.
	Select(services []*registry.Service) (*registry.Service, error)
}

// New creates a new Balancer with the given strategy.
func New(strategy Strategy) Balancer {
	switch strategy {
	case RoundRobin:
		return NewRoundRobinBalancer()
	case Random:
		return NewRandomBalancer()
	case WeightedRoundRobin:
		return NewWeightedRoundRobinBalancer()
	default:
		return NewRoundRobinBalancer()
	}
}

// --- Round Robin ---

// RoundRobinBalancer distributes requests sequentially.
type RoundRobinBalancer struct {
	counter uint64
}

// NewRoundRobinBalancer creates a new round-robin balancer.
func NewRoundRobinBalancer() *RoundRobinBalancer {
	return &RoundRobinBalancer{}
}

// Select returns the next service in round-robin order.
func (b *RoundRobinBalancer) Select(services []*registry.Service) (*registry.Service, error) {
	if len(services) == 0 {
		return nil, ErrNoServices
	}

	idx := atomic.AddUint64(&b.counter, 1)
	return services[idx%uint64(len(services))], nil
}

// --- Random ---

// RandomBalancer selects a random service instance.
type RandomBalancer struct {
	mu     sync.Mutex
	random *rand.Rand
}

// NewRandomBalancer creates a new random balancer.
func NewRandomBalancer() *RandomBalancer {
	return &RandomBalancer{
		random: rand.New(rand.NewSource(rand.Int63())),
	}
}

// Select returns a random service instance.
func (b *RandomBalancer) Select(services []*registry.Service) (*registry.Service, error) {
	if len(services) == 0 {
		return nil, ErrNoServices
	}

	b.mu.Lock()
	idx := b.random.Intn(len(services))
	b.mu.Unlock()

	return services[idx], nil
}

// --- Weighted Round Robin ---

// WeightedRoundRobinBalancer distributes requests based on weights.
// Weights are read from the service's Metadata["weight"] field.
// Default weight is 1. Higher weight means more requests.
type WeightedRoundRobinBalancer struct {
	mu       sync.Mutex
	counter  int
	weighted []*registry.Service
	current  int
}

// NewWeightedRoundRobinBalancer creates a new weighted round-robin balancer.
func NewWeightedRoundRobinBalancer() *WeightedRoundRobinBalancer {
	return &WeightedRoundRobinBalancer{}
}

// Select returns a service based on weighted round-robin.
func (b *WeightedRoundRobinBalancer) Select(services []*registry.Service) (*registry.Service, error) {
	if len(services) == 0 {
		return nil, ErrNoServices
	}

	b.mu.Lock()
	defer b.mu.Unlock()

	// Rebuild weighted list if services changed
	if b.shouldRebuild(services) {
		b.buildWeightedList(services)
	}

	if len(b.weighted) == 0 {
		return services[0], nil
	}

	svc := b.weighted[b.current]
	b.current = (b.current + 1) % len(b.weighted)
	return svc, nil
}

// shouldRebuild checks if the weighted list needs rebuilding.
func (b *WeightedRoundRobinBalancer) shouldRebuild(services []*registry.Service) bool {
	if len(b.weighted) != b.expectedWeightedListSize(services) {
		return true
	}
	// Check if any service IDs changed
	idSet := make(map[string]bool)
	for _, svc := range services {
		idSet[svc.ID] = true
	}
	for _, svc := range b.weighted {
		if !idSet[svc.ID] {
			return true
		}
	}
	return false
}

// expectedWeightedListSize calculates the expected size of the weighted list.
func (b *WeightedRoundRobinBalancer) expectedWeightedListSize(services []*registry.Service) int {
	total := 0
	for _, svc := range services {
		total += getWeight(svc)
	}
	return total
}

// buildWeightedList creates the weighted list from services.
func (b *WeightedRoundRobinBalancer) buildWeightedList(services []*registry.Service) {
	b.weighted = nil
	b.current = 0

	for _, svc := range services {
		weight := getWeight(svc)
		for i := 0; i < weight; i++ {
			b.weighted = append(b.weighted, svc)
		}
	}
}

// getWeight returns the weight for a service from its metadata.
func getWeight(svc *registry.Service) int {
	if svc.Metadata == nil {
		return 1
	}
	weight, ok := svc.Metadata["weight"]
	if !ok || weight == "" {
		return 1
	}
	// Parse weight, default to 1 on error
	w := 0
	for _, c := range weight {
		if c >= '0' && c <= '9' {
			w = w*10 + int(c-'0')
		} else {
			return 1
		}
	}
	if w <= 0 {
		return 1
	}
	return w
}

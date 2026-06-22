package dispatcher

import (
	"errors"
	"net/http"
	"sync"
	"sync/atomic"
	"time"
)

var (
	// ErrNoNodes is returned when there are no available nodes.
	ErrNoNodes = errors.New("no available nodes")
)

// NodeStatus represents the health status of a node.
type NodeStatus int

const (
	// NodeStatusHealthy means the node is healthy and available.
	NodeStatusHealthy NodeStatus = iota
	// NodeStatusUnhealthy means the node is unhealthy and should not be used.
	NodeStatusUnhealthy
	// NodeStatusUnknown means the node status is unknown.
	NodeStatusUnknown
)

// Node represents a backend node that can serve requests.
type Node struct {
	ID          string
	Address     string
	Weight      int
	Status      NodeStatus
	Connections int64
	LastCheck   time.Time
}

// Strategy is the interface for load balancing strategies.
// Different strategies implement different algorithms for selecting nodes.
//
// ⭐ Available Strategies:
// - RoundRobin: distributes requests evenly
// - WeightedRoundRobin: distributes based on weights
// - LeastConnections: selects node with fewest connections
type Strategy interface {
	Select(nodes []*Node, r *http.Request) (*Node, error)
}

// RoundRobinStrategy implements round-robin load balancing.
// It distributes requests evenly across all available nodes.
//
// 💡 Round Robin Algorithm:
// - Simple and fair distribution
// - Each node gets an equal number of requests
// - Good for homogeneous node clusters
type RoundRobinStrategy struct {
	current uint64
}

// NewRoundRobinStrategy creates a new round-robin strategy.
func NewRoundRobinStrategy() *RoundRobinStrategy {
	return &RoundRobinStrategy{}
}

// Select selects the next node in round-robin order.
func (s *RoundRobinStrategy) Select(nodes []*Node, r *http.Request) (*Node, error) {
	if len(nodes) == 0 {
		return nil, ErrNoNodes
	}

	// Filter healthy nodes
	healthy := filterHealthy(nodes)
	if len(healthy) == 0 {
		return nil, ErrNoNodes
	}

	// Select next node
	idx := atomic.AddUint64(&s.current, 1)
	return healthy[idx%uint64(len(healthy))], nil
}

// WeightedRoundRobinStrategy implements weighted round-robin load balancing.
// Nodes with higher weights receive more requests.
//
// 💡 Weighted Round Robin Algorithm:
// - Nodes are selected proportionally to their weights
// - A node with weight 2 gets twice as many requests as weight 1
// - Good for heterogeneous node clusters
type WeightedRoundRobinStrategy struct {
	currentWeight int
	current       int
}

// NewWeightedRoundRobinStrategy creates a new weighted round-robin strategy.
func NewWeightedRoundRobinStrategy() *WeightedRoundRobinStrategy {
	return &WeightedRoundRobinStrategy{}
}

// Select selects a node based on weighted round-robin.
func (s *WeightedRoundRobinStrategy) Select(nodes []*Node, r *http.Request) (*Node, error) {
	if len(nodes) == 0 {
		return nil, ErrNoNodes
	}

	healthy := filterHealthy(nodes)
	if len(healthy) == 0 {
		return nil, ErrNoNodes
	}

	// Calculate total weight
	totalWeight := 0
	for _, node := range healthy {
		totalWeight += node.Weight
	}

	// Select based on weight
	s.currentWeight++
	if s.currentWeight >= totalWeight {
		s.currentWeight = 0
		s.current = 0
	}

	weight := 0
	for i, node := range healthy {
		weight += node.Weight
		if s.currentWeight < weight {
			s.current = i
			return node, nil
		}
	}

	return healthy[0], nil
}

// LeastConnectionsStrategy implements least-connections load balancing.
// It selects the node with the fewest active connections.
//
// 💡 Least Connections Algorithm:
// - Selects the node with the fewest active connections
// - Good for long-lived connections
// - Automatically balances load based on actual usage
type LeastConnectionsStrategy struct{}

// NewLeastConnectionsStrategy creates a new least-connections strategy.
func NewLeastConnectionsStrategy() *LeastConnectionsStrategy {
	return &LeastConnectionsStrategy{}
}

// Select selects the node with the fewest connections.
func (s *LeastConnectionsStrategy) Select(nodes []*Node, r *http.Request) (*Node, error) {
	if len(nodes) == 0 {
		return nil, ErrNoNodes
	}

	healthy := filterHealthy(nodes)
	if len(healthy) == 0 {
		return nil, ErrNoNodes
	}

	// Find node with least connections
	minConns := int64(^uint64(0) >> 1) // Max int64
	var selected *Node

	for _, node := range healthy {
		conns := atomic.LoadInt64(&node.Connections)
		if conns < minConns {
			minConns = conns
			selected = node
		}
	}

	return selected, nil
}

// filterHealthy returns only healthy nodes.
func filterHealthy(nodes []*Node) []*Node {
	healthy := make([]*Node, 0, len(nodes))
	for _, node := range nodes {
		if node.Status == NodeStatusHealthy {
			healthy = append(healthy, node)
		}
	}
	return healthy
}

// Dispatcher manages a pool of backend nodes and selects
// the appropriate node for each request using a configured strategy.
//
// ⭐ Key Responsibilities:
// 1. Maintain a list of backend nodes
// 2. Select nodes based on the configured strategy
// 3. Track node connections
// 4. Perform health checks
type Dispatcher struct {
	nodes        []*Node
	strategy     Strategy
	healthTicker *time.Ticker
	stopHealth   chan struct{}
	mutex        sync.RWMutex
}

// NewDispatcher creates a new dispatcher with the specified strategy.
//
// Parameters:
//   - strategy: the load balancing strategy to use
//
// Returns:
//   - *Dispatcher: a new dispatcher instance
func NewDispatcher(strategy Strategy) *Dispatcher {
	d := &Dispatcher{
		strategy:   strategy,
		stopHealth: make(chan struct{}),
	}

	// Start health check goroutine
	d.healthTicker = time.NewTicker(30 * time.Second)
	go d.healthCheckLoop()

	return d
}

// AddNode adds a node to the dispatcher.
func (d *Dispatcher) AddNode(node *Node) {
	d.mutex.Lock()
	defer d.mutex.Unlock()

	d.nodes = append(d.nodes, node)
}

// RemoveNode removes a node from the dispatcher.
func (d *Dispatcher) RemoveNode(id string) {
	d.mutex.Lock()
	defer d.mutex.Unlock()

	for i, node := range d.nodes {
		if node.ID == id {
			d.nodes = append(d.nodes[:i], d.nodes[i+1:]...)
			return
		}
	}
}

// Select selects a node for the given request.
// It uses the configured strategy to select the best node.
//
// Parameters:
//   - r: the HTTP request
//
// Returns:
//   - *Node: the selected node
//   - error: any error that occurred
func (d *Dispatcher) Select(r *http.Request) (*Node, error) {
	d.mutex.RLock()
	defer d.mutex.RUnlock()

	node, err := d.strategy.Select(d.nodes, r)
	if err != nil {
		return nil, err
	}

	// Increment connection count
	atomic.AddInt64(&node.Connections, 1)

	return node, nil
}

// Release decrements the connection count for a node.
func (d *Dispatcher) Release(node *Node) {
	atomic.AddInt64(&node.Connections, -1)
}

// Nodes returns a copy of the current nodes list.
func (d *Dispatcher) Nodes() []*Node {
	d.mutex.RLock()
	defer d.mutex.RUnlock()

	nodes := make([]*Node, len(d.nodes))
	copy(nodes, d.nodes)
	return nodes
}

// Stop stops the dispatcher and its health check goroutine.
func (d *Dispatcher) Stop() {
	close(d.stopHealth)
	d.healthTicker.Stop()
}

// healthCheckLoop runs in a background goroutine to periodically
// check the health of all nodes.
//
// 💡 Health Check:
// - Periodically checks node health
// - Marks unhealthy nodes
// - Can be extended to perform actual health checks
func (d *Dispatcher) healthCheckLoop() {
	for {
		select {
		case <-d.healthTicker.C:
			d.checkHealth()
		case <-d.stopHealth:
			return
		}
	}
}

// checkHealth checks the health of all nodes.
// This is a placeholder implementation that can be extended
// to perform actual health checks (HTTP, TCP, etc.).
func (d *Dispatcher) checkHealth() {
	d.mutex.Lock()
	defer d.mutex.Unlock()

	// Placeholder: mark all nodes as healthy
	// In a real implementation, you would:
	// 1. Make HTTP requests to each node's health endpoint
	// 2. Check response status code
	// 3. Update node status based on response
	for _, node := range d.nodes {
		node.Status = NodeStatusHealthy
		node.LastCheck = time.Now()
	}
}
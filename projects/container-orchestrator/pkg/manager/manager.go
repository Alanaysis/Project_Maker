package manager

import (
	"context"
	"errors"
	"sync"
	"time"

	"github.com/container-orchestrator/pkg/container"
	"github.com/container-orchestrator/pkg/discovery"
	"github.com/container-orchestrator/pkg/health"
	"github.com/container-orchestrator/pkg/scaler"
	"github.com/container-orchestrator/pkg/scheduler"
)

var (
	ErrServiceNotFound = errors.New("service not found")
	ErrNodeNotFound    = errors.New("node not found")
)

// Manager orchestrates containers
type Manager struct {
	mu        sync.RWMutex
	scheduler *scheduler.Scheduler
	discovery *discovery.Discovery
	monitor   *health.HealthMonitor
	scaler    *scaler.Scaler
	services  map[string]*ServiceManager
	nodes     map[string]*NodeManager
	ctx       context.Context
	cancel    context.CancelFunc
}

// ServiceManager manages a service
type ServiceManager struct {
	Service    *container.Service
	Containers []*container.Container
}

// NodeManager manages a node
type NodeManager struct {
	Node       *container.Node
	Containers []*container.Container
}

// NewManager creates a new container orchestrator manager
func NewManager() *Manager {
	ctx, cancel := context.WithCancel(context.Background())

	m := &Manager{
		scheduler: scheduler.NewScheduler(scheduler.StrategyBinPacking),
		discovery: discovery.NewDiscovery(),
		services:  make(map[string]*ServiceManager),
		nodes:     make(map[string]*NodeManager),
		ctx:       ctx,
		cancel:    cancel,
	}

	// Create health monitor with a simple checker
	checker := health.NewHTTPHealthChecker(&simpleHTTPClient{})
	m.monitor = health.NewHealthMonitor(checker)

	// Create scaler
	m.scaler = scaler.NewScaler(m.scaleService)

	return m
}

// Start starts the manager
func (m *Manager) Start() {
	// Start health monitoring
	m.monitor.Start(m.ctx, 10*time.Second)

	// Start auto-scaling
	go m.scaler.AutoScale(m.ctx, 30*time.Second)

	// Start cleanup routine
	go m.cleanup(m.ctx)
}

// Stop stops the manager
func (m *Manager) Stop() {
	m.cancel()
	m.monitor.Stop()
}

// AddNode adds a node to the cluster
func (m *Manager) AddNode(name, address string, resources container.Resources) *container.Node {
	node := container.NewNode(name, address, resources)

	m.mu.Lock()
	m.nodes[node.ID] = &NodeManager{
		Node: node,
		Containers: make([]*container.Container, 0),
	}
	m.mu.Unlock()

	m.scheduler.AddNode(node)

	return node
}

// RemoveNode removes a node from the cluster
func (m *Manager) RemoveNode(nodeID string) error {
	m.mu.Lock()
	nm, exists := m.nodes[nodeID]
	if !exists {
		m.mu.Unlock()
		return ErrNodeNotFound
	}

	// Stop all containers on the node
	for _, c := range nm.Containers {
		c.SetState(container.StateStopped)
		m.monitor.RemoveContainer(c.ID)
	}

	delete(m.nodes, nodeID)
	m.mu.Unlock()

	m.scheduler.RemoveNode(nodeID)

	return nil
}

// GetNode returns a node by ID
func (m *Manager) GetNode(nodeID string) (*container.Node, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	nm, exists := m.nodes[nodeID]
	if !exists {
		return nil, ErrNodeNotFound
	}

	return nm.Node, nil
}

// GetNodes returns all nodes
func (m *Manager) GetNodes() []*container.Node {
	return m.scheduler.GetNodes()
}

// CreateService creates a new service
func (m *Manager) CreateService(name string, replicas int, template container.ContainerTemplate) (*container.Service, error) {
	service := container.NewService(name, replicas, template)

	// Register with discovery
	if err := m.discovery.RegisterService(service); err != nil {
		return nil, err
	}

	// Register with scaler
	m.scaler.RegisterService(service.ID, replicas, &scaler.ScalingPolicy{
		MinReplicas:     1,
		MaxReplicas:     10,
		ScaleUpCPU:      0.8,
		ScaleDownCPU:    0.2,
		ScaleUpMemory:   0.8,
		ScaleDownMemory: 0.2,
		Cooldown:        5 * time.Minute,
	})

	// Create service manager
	sm := &ServiceManager{
		Service:    service,
		Containers: make([]*container.Container, 0),
	}

	m.mu.Lock()
	m.services[service.ID] = sm
	m.mu.Unlock()

	// Create initial containers
	for i := 0; i < replicas; i++ {
		if err := m.createContainer(service, template); err != nil {
			// Log error but continue
			continue
		}
	}

	return service, nil
}

// DeleteService deletes a service
func (m *Manager) DeleteService(serviceID string) error {
	m.mu.Lock()
	sm, exists := m.services[serviceID]
	if !exists {
		m.mu.Unlock()
		return ErrServiceNotFound
	}

	// Stop all containers
	for _, c := range sm.Containers {
		m.scheduler.Unschedule(c.ID)
		m.monitor.RemoveContainer(c.ID)
		m.discovery.UnregisterEndpoint(serviceID, c.ID)
	}

	delete(m.services, serviceID)
	m.mu.Unlock()

	m.discovery.UnregisterService(serviceID)
	m.scaler.UnregisterService(serviceID)

	return nil
}

// GetService returns a service by ID
func (m *Manager) GetService(serviceID string) (*container.Service, error) {
	return m.discovery.GetService(serviceID)
}

// GetServices returns all services
func (m *Manager) GetServices() []*container.Service {
	m.mu.RLock()
	defer m.mu.RUnlock()

	services := make([]*container.Service, 0, len(m.services))
	for _, sm := range m.services {
		services = append(services, sm.Service)
	}

	return services
}

// ScaleService scales a service to the desired number of replicas
func (m *Manager) ScaleService(serviceID string, replicas int) error {
	return m.scaler.ManualScale(serviceID, replicas)
}

// createContainer creates and schedules a container
func (m *Manager) createContainer(service *container.Service, template container.ContainerTemplate) error {
	c := container.NewContainer(
		service.Name+"-container",
		template.Image,
		template.Resources,
	)

	c.Labels = template.Labels
	c.Ports = template.Ports
	c.HealthCheck = template.HealthCheck

	// Schedule the container
	node, err := m.scheduler.Schedule(c)
	if err != nil {
		return err
	}

	// Set container as running
	c.SetState(container.StateRunning)

	// Add to health monitoring
	m.monitor.AddContainer(c)

	// Register with discovery
	endpoint := &discovery.Endpoint{
		ID:          c.ID,
		ServiceID:   service.ID,
		ContainerID: c.ID,
		NodeID:      node.ID,
		Address:     node.Address,
		Port:        8080, // Default port
		Labels:      c.Labels,
		Health:      discovery.HealthHealthy,
		Weight:      1,
		LastSeen:    time.Now(),
	}

	if err := m.discovery.RegisterEndpoint(endpoint); err != nil {
		return err
	}

	// Update service manager
	m.mu.Lock()
	sm, exists := m.services[service.ID]
	if exists {
		sm.Containers = append(sm.Containers, c)
	}

	// Update node manager
	nm, exists := m.nodes[node.ID]
	if exists {
		nm.Containers = append(nm.Containers, c)
	}
	m.mu.Unlock()

	return nil
}

// scaleService is the scale function for the scaler
func (m *Manager) scaleService(serviceID string, desiredReplicas int) error {
	m.mu.RLock()
	sm, exists := m.services[serviceID]
	if !exists {
		m.mu.RUnlock()
		return ErrServiceNotFound
	}
	service := sm.Service
	template := service.Template
	currentReplicas := len(sm.Containers)
	m.mu.RUnlock()

	if desiredReplicas > currentReplicas {
		// Scale up
		for i := 0; i < desiredReplicas-currentReplicas; i++ {
			if err := m.createContainer(service, template); err != nil {
				return err
			}
		}
	} else if desiredReplicas < currentReplicas {
		// Scale down
		m.mu.Lock()
		containers := sm.Containers[desiredReplicas:]
		sm.Containers = sm.Containers[:desiredReplicas]
		m.mu.Unlock()

		for _, c := range containers {
			m.scheduler.Unschedule(c.ID)
			m.monitor.RemoveContainer(c.ID)
			m.discovery.UnregisterEndpoint(serviceID, c.ID)
		}
	}

	return nil
}

// ResolveService resolves a service name to an endpoint
func (m *Manager) ResolveService(serviceName string) (*discovery.Endpoint, error) {
	return m.discovery.Resolve(serviceName)
}

// GetClusterStats returns cluster statistics
func (m *Manager) GetClusterStats() scheduler.ClusterStats {
	return m.scheduler.GetClusterStats()
}

// GetHealthSummary returns health summary
func (m *Manager) GetHealthSummary() health.HealthSummary {
	return m.monitor.GetSummary()
}

// cleanup runs periodic cleanup tasks
func (m *Manager) cleanup(ctx context.Context) {
	ticker := time.NewTicker(5 * time.Minute)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			// Cleanup unhealthy endpoints
			m.discovery.Cleanup(10 * time.Minute)
		}
	}
}

// simpleHTTPClient implements HTTPClient interface
type simpleHTTPClient struct{}

func (c *simpleHTTPClient) Get(url string) (int, error) {
	// Simulate HTTP health check
	return 200, nil
}

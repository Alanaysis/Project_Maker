package container

import (
	"fmt"
	"sync"
	"time"

	"github.com/google/uuid"
)

// ContainerState represents the state of a container
type ContainerState string

const (
	StatePending   ContainerState = "pending"
	StateRunning   ContainerState = "running"
	StateStopped   ContainerState = "stopped"
	StateFailed    ContainerState = "failed"
	StateCompleted ContainerState = "completed"
)

// Container represents a container instance
type Container struct {
	ID          string            `json:"id"`
	Name        string            `json:"name"`
	Image       string            `json:"image"`
	State       ContainerState    `json:"state"`
	NodeID      string            `json:"node_id"`
	Labels      map[string]string `json:"labels"`
	Ports       []Port            `json:"ports"`
	Resources   Resources         `json:"resources"`
	HealthCheck *HealthCheck      `json:"health_check,omitempty"`
	CreatedAt   time.Time         `json:"created_at"`
	StartedAt   *time.Time        `json:"started_at,omitempty"`
	StoppedAt   *time.Time        `json:"stopped_at,omitempty"`
	RestartCount int              `json:"restart_count"`
	mu          sync.RWMutex
}

// Port represents a container port mapping
type Port struct {
	HostPort      int    `json:"host_port"`
	ContainerPort int    `json:"container_port"`
	Protocol      string `json:"protocol"`
}

// Resources represents container resource requirements
type Resources struct {
	CPU    float64 `json:"cpu"`    // CPU cores
	Memory int64   `json:"memory"` // Memory in bytes
	Disk   int64   `json:"disk"`   // Disk in bytes
}

// HealthCheck represents container health check configuration
type HealthCheck struct {
	Interval     time.Duration `json:"interval"`
	Timeout      time.Duration `json:"timeout"`
	Retries      int           `json:"retries"`
	StartPeriod  time.Duration `json:"start_period"`
	TestCommand  []string      `json:"test_command"`
}

// ContainerStatus represents the health status of a container
type ContainerStatus struct {
	Healthy   bool      `json:"healthy"`
	LastCheck time.Time `json:"last_check"`
	Message   string    `json:"message,omitempty"`
}

// Node represents a cluster node
type Node struct {
	ID        string            `json:"id"`
	Name      string            `json:"name"`
	Address   string            `json:"address"`
	Labels    map[string]string `json:"labels"`
	Resources Resources         `json:"resources"`
	Used      Resources         `json:"used"`
	State     NodeState         `json:"state"`
	Containers []string         `json:"containers"`
	mu        sync.RWMutex
}

// NodeState represents the state of a node
type NodeState string

const (
	NodeReady    NodeState = "ready"
	NodeNotReady NodeState = "not_ready"
	NodeDrained  NodeState = "drained"
)

// Service represents a service that runs containers
type Service struct {
	ID            string            `json:"id"`
	Name          string            `json:"name"`
	Labels        map[string]string `json:"labels"`
	Replicas      int               `json:"replicas"`
	Template      ContainerTemplate `json:"template"`
	Selector      map[string]string `json:"selector"`
	Ports         []ServicePort     `json:"ports"`
	Strategy      Strategy          `json:"strategy"`
	CreatedAt     time.Time         `json:"created_at"`
	UpdatedAt     time.Time         `json:"updated_at"`
}

// ContainerTemplate represents the template for creating containers
type ContainerTemplate struct {
	Image       string            `json:"image"`
	Labels      map[string]string `json:"labels"`
	Ports       []Port            `json:"ports"`
	Resources   Resources         `json:"resources"`
	HealthCheck *HealthCheck      `json:"health_check,omitempty"`
	Env         map[string]string `json:"env,omitempty"`
	Command     []string          `json:"command,omitempty"`
}

// ServicePort represents a service port
type ServicePort struct {
	Name       string `json:"name"`
	Port       int    `json:"port"`
	TargetPort int    `json:"target_port"`
	Protocol   string `json:"protocol"`
}

// Strategy represents deployment strategy
type Strategy struct {
	Type          StrategyType `json:"type"`
	MaxSurge      int          `json:"max_surge"`
	MaxUnavailable int         `json:"max_unavailable"`
}

// StrategyType represents the type of deployment strategy
type StrategyType string

const (
	StrategyRollingUpdate StrategyType = "rolling_update"
	StrategyRecreate      StrategyType = "recreate"
)

// ScalingPolicy represents scaling policy
type ScalingPolicy struct {
	MinReplicas int    `json:"min_replicas"`
	MaxReplicas int    `json:"max_replicas"`
	ScaleUp     ScaleRule `json:"scale_up"`
	ScaleDown   ScaleRule `json:"scale_down"`
}

// ScaleRule represents scaling rules
type ScaleRule struct {
	CPUThreshold    float64       `json:"cpu_threshold"`
	MemoryThreshold float64       `json:"memory_threshold"`
	Cooldown        time.Duration `json:"cooldown"`
}

// NewContainer creates a new container
func NewContainer(name, image string, resources Resources) *Container {
	return &Container{
		ID:        uuid.New().String(),
		Name:      name,
		Image:     image,
		State:     StatePending,
		Labels:    make(map[string]string),
		Resources: resources,
		CreatedAt: time.Now(),
	}
}

// SetState safely sets the container state
func (c *Container) SetState(state ContainerState) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.State = state
	if state == StateRunning && c.StartedAt == nil {
		now := time.Now()
		c.StartedAt = &now
	}
	if state == StateStopped || state == StateFailed {
		now := time.Now()
		c.StoppedAt = &now
	}
}

// Start starts the container (transitions from pending/stopped to running)
func (c *Container) Start() error {
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.State != StatePending && c.State != StateStopped {
		return fmt.Errorf("cannot start container in state %s", c.State)
	}
	c.State = StateRunning
	now := time.Now()
	c.StartedAt = &now
	c.StoppedAt = nil
	return nil
}

// Stop stops the container (transitions from running to stopped)
func (c *Container) Stop() error {
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.State != StateRunning {
		return fmt.Errorf("cannot stop container in state %s", c.State)
	}
	c.State = StateStopped
	now := time.Now()
	c.StoppedAt = &now
	return nil
}

// Restart restarts the container
func (c *Container) Restart() error {
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.State != StateRunning && c.State != StateStopped && c.State != StateFailed {
		return fmt.Errorf("cannot restart container in state %s", c.State)
	}
	c.State = StateRunning
	now := time.Now()
	c.StartedAt = &now
	c.StoppedAt = nil
	c.RestartCount++
	return nil
}

// IsRunning returns true if the container is running
func (c *Container) IsRunning() bool {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.State == StateRunning
}

// GetState safely gets the container state
func (c *Container) GetState() ContainerState {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.State
}

// NewNode creates a new node
func NewNode(name, address string, resources Resources) *Node {
	return &Node{
		ID:        uuid.New().String(),
		Name:      name,
		Address:   address,
		Labels:    make(map[string]string),
		Resources: resources,
		State:     NodeReady,
		Containers: make([]string, 0),
	}
}

// AvailableResources returns available resources on the node
func (n *Node) AvailableResources() Resources {
	n.mu.RLock()
	defer n.mu.RUnlock()
	return Resources{
		CPU:    n.Resources.CPU - n.Used.CPU,
		Memory: n.Resources.Memory - n.Used.Memory,
		Disk:   n.Resources.Disk - n.Used.Disk,
	}
}

// CanSchedule checks if a container can be scheduled on this node
func (n *Node) CanSchedule(container *Container) bool {
	n.mu.RLock()
	defer n.mu.RUnlock()

	if n.State != NodeReady {
		return false
	}

	available := n.AvailableResources()
	return container.Resources.CPU <= available.CPU &&
		container.Resources.Memory <= available.Memory &&
		container.Resources.Disk <= available.Disk
}

// AddContainer adds a container to the node
func (n *Node) AddContainer(containerID string, resources Resources) {
	n.mu.Lock()
	defer n.mu.Unlock()
	n.Containers = append(n.Containers, containerID)
	n.Used.CPU += resources.CPU
	n.Used.Memory += resources.Memory
	n.Used.Disk += resources.Disk
}

// RemoveContainer removes a container from the node
func (n *Node) RemoveContainer(containerID string, resources Resources) {
	n.mu.Lock()
	defer n.mu.Unlock()
	for i, id := range n.Containers {
		if id == containerID {
			n.Containers = append(n.Containers[:i], n.Containers[i+1:]...)
			break
		}
	}
	n.Used.CPU -= resources.CPU
	n.Used.Memory -= resources.Memory
	n.Used.Disk -= resources.Disk
}

// NewService creates a new service
func NewService(name string, replicas int, template ContainerTemplate) *Service {
	return &Service{
		ID:        uuid.New().String(),
		Name:      name,
		Labels:    make(map[string]string),
		Replicas:  replicas,
		Template:  template,
		Selector:  make(map[string]string),
		Strategy: Strategy{
			Type:          StrategyRollingUpdate,
			MaxSurge:      1,
			MaxUnavailable: 0,
		},
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
}

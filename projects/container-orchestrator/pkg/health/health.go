package health

import (
	"context"
	"errors"
	"sync"
	"time"

	"github.com/container-orchestrator/pkg/container"
)

var (
	ErrContainerNotFound = errors.New("container not found")
	ErrHealthCheckFailed = errors.New("health check failed")
)

// HealthState represents the health state
type HealthState string

const (
	StateHealthy   HealthState = "healthy"
	StateUnhealthy HealthState = "unhealthy"
	StateUnknown   HealthState = "unknown"
	StateStarting  HealthState = "starting"
)

// HealthResult represents a health check result
type HealthResult struct {
	ContainerID string      `json:"container_id"`
	State       HealthState `json:"state"`
	Message     string      `json:"message,omitempty"`
	Timestamp   time.Time   `json:"timestamp"`
	Duration    time.Duration `json:"duration"`
}

// HealthChecker performs health checks
type HealthChecker interface {
	Check(ctx context.Context, container *container.Container) (*HealthResult, error)
}

// HTTPHealthChecker performs HTTP health checks
type HTTPHealthChecker struct {
	client HTTPClient
}

// HTTPClient interface for HTTP requests
type HTTPClient interface {
	Get(url string) (int, error)
}

// NewHTTPHealthChecker creates a new HTTP health checker
func NewHTTPHealthChecker(client HTTPClient) *HTTPHealthChecker {
	return &HTTPHealthChecker{client: client}
}

// Check performs an HTTP health check
func (h *HTTPHealthChecker) Check(ctx context.Context, c *container.Container) (*HealthResult, error) {
	start := time.Now()
	result := &HealthResult{
		ContainerID: c.ID,
		Timestamp:   start,
	}

	// Simulate health check
	if c.GetState() != container.StateRunning {
		result.State = StateUnhealthy
		result.Message = "container not running"
		result.Duration = time.Since(start)
		return result, nil
	}

	result.State = StateHealthy
	result.Message = "health check passed"
	result.Duration = time.Since(start)

	return result, nil
}

// HealthMonitor monitors container health
type HealthMonitor struct {
	mu           sync.RWMutex
	containers   map[string]*MonitoredContainer
	checker      HealthChecker
	interval     time.Duration
	results      map[string]*HealthResult
	stopCh       chan struct{}
	eventHandler func(*HealthEvent)
}

// MonitoredContainer represents a container being monitored
type MonitoredContainer struct {
	Container    *container.Container
	Config       *container.HealthCheck
	LastCheck    time.Time
	FailedChecks int
}

// HealthEvent represents a health event
type HealthEvent struct {
	Type        EventType   `json:"type"`
	ContainerID string      `json:"container_id"`
	Result      *HealthResult `json:"result"`
	Timestamp   time.Time   `json:"timestamp"`
}

// EventType represents the type of health event
type EventType string

const (
	EventContainerHealthy   EventType = "container_healthy"
	EventContainerUnhealthy EventType = "container_unhealthy"
	EventContainerRestarted EventType = "container_restarted"
)

// NewHealthMonitor creates a new health monitor
func NewHealthMonitor(checker HealthChecker) *HealthMonitor {
	return &HealthMonitor{
		containers: make(map[string]*MonitoredContainer),
		checker:    checker,
		results:    make(map[string]*HealthResult),
		stopCh:     make(chan struct{}),
	}
}

// SetEventHandler sets the event handler
func (m *HealthMonitor) SetEventHandler(handler func(*HealthEvent)) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.eventHandler = handler
}

// AddContainer adds a container to monitor
func (m *HealthMonitor) AddContainer(c *container.Container) {
	m.mu.Lock()
	defer m.mu.Unlock()

	m.containers[c.ID] = &MonitoredContainer{
		Container: c,
		Config:    c.HealthCheck,
		LastCheck: time.Now(),
	}

	m.results[c.ID] = &HealthResult{
		ContainerID: c.ID,
		State:       StateUnknown,
		Timestamp:   time.Now(),
	}
}

// RemoveContainer removes a container from monitoring
func (m *HealthMonitor) RemoveContainer(containerID string) {
	m.mu.Lock()
	defer m.mu.Unlock()

	delete(m.containers, containerID)
	delete(m.results, containerID)
}

// GetHealth returns the health state of a container
func (m *HealthMonitor) GetHealth(containerID string) (*HealthResult, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	result, exists := m.results[containerID]
	if !exists {
		return nil, ErrContainerNotFound
	}

	return result, nil
}

// GetAllHealth returns health states of all containers
func (m *HealthMonitor) GetAllHealth() map[string]*HealthResult {
	m.mu.RLock()
	defer m.mu.RUnlock()

	results := make(map[string]*HealthResult, len(m.results))
	for id, result := range m.results {
		results[id] = result
	}

	return results
}

// Start starts the health monitor
func (m *HealthMonitor) Start(ctx context.Context, interval time.Duration) {
	go m.run(ctx, interval)
}

// Stop stops the health monitor
func (m *HealthMonitor) Stop() {
	close(m.stopCh)
}

// run runs the health monitor loop
func (m *HealthMonitor) run(ctx context.Context, interval time.Duration) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-m.stopCh:
			return
		case <-ticker.C:
			m.checkAll(ctx)
		}
	}
}

// checkAll checks health of all monitored containers
func (m *HealthMonitor) checkAll(ctx context.Context) {
	m.mu.RLock()
	containers := make([]*MonitoredContainer, 0, len(m.containers))
	for _, mc := range m.containers {
		containers = append(containers, mc)
	}
	m.mu.RUnlock()

	for _, mc := range containers {
		go m.checkContainer(ctx, mc)
	}
}

// checkContainer checks health of a single container
func (m *HealthMonitor) checkContainer(ctx context.Context, mc *MonitoredContainer) {
	result, err := m.checker.Check(ctx, mc.Container)
	if err != nil {
		result = &HealthResult{
			ContainerID: mc.Container.ID,
			State:       StateUnhealthy,
			Message:     err.Error(),
			Timestamp:   time.Now(),
		}
	}

	m.mu.Lock()
	m.results[mc.Container.ID] = result
	mc.LastCheck = time.Now()

	// Update failed checks count
	if result.State == StateUnhealthy {
		mc.FailedChecks++
	} else {
		mc.FailedChecks = 0
	}

	// Determine if we need to emit an event
	var event *HealthEvent
	if result.State == StateHealthy {
		event = &HealthEvent{
			Type:        EventContainerHealthy,
			ContainerID: mc.Container.ID,
			Result:      result,
			Timestamp:   time.Now(),
		}
	} else if mc.Config != nil && mc.FailedChecks >= mc.Config.Retries {
		event = &HealthEvent{
			Type:        EventContainerUnhealthy,
			ContainerID: mc.Container.ID,
			Result:      result,
			Timestamp:   time.Now(),
		}
	}

	handler := m.eventHandler
	m.mu.Unlock()

	// Emit event outside of lock
	if event != nil && handler != nil {
		handler(event)
	}
}

// HealthSummary represents a summary of health states
type HealthSummary struct {
	Total     int `json:"total"`
	Healthy   int `json:"healthy"`
	Unhealthy int `json:"unhealthy"`
	Unknown   int `json:"unknown"`
	Starting  int `json:"starting"`
}

// GetSummary returns a summary of health states
func (m *HealthMonitor) GetSummary() HealthSummary {
	m.mu.RLock()
	defer m.mu.RUnlock()

	summary := HealthSummary{
		Total: len(m.results),
	}

	for _, result := range m.results {
		switch result.State {
		case StateHealthy:
			summary.Healthy++
		case StateUnhealthy:
			summary.Unhealthy++
		case StateUnknown:
			summary.Unknown++
		case StateStarting:
			summary.Starting++
		}
	}

	return summary
}

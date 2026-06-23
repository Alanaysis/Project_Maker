package scaler

import (
	"context"
	"errors"
	"sync"
	"time"

	"github.com/container-orchestrator/pkg/container"
)

var (
	ErrServiceNotFound = errors.New("service not found")
	ErrScalingInProgress = errors.New("scaling already in progress")
)

// Scaler handles auto-scaling of services
type Scaler struct {
	mu           sync.RWMutex
	services     map[string]*ServiceState
	policies     map[string]*ScalingPolicy
	metrics      *MetricsCollector
	scaleFunc    ScaleFunc
	cooldowns    map[string]time.Time
}

// ServiceState represents the current state of a service
type ServiceState struct {
	ServiceID    string
	CurrentReplicas int
	DesiredReplicas int
	LastScaleTime   time.Time
	Scaling         bool
}

// ScalingPolicy defines scaling rules
type ScalingPolicy struct {
	MinReplicas     int           `json:"min_replicas"`
	MaxReplicas     int           `json:"max_replicas"`
	ScaleUpCPU      float64       `json:"scale_up_cpu"`
	ScaleDownCPU    float64       `json:"scale_down_cpu"`
	ScaleUpMemory   float64       `json:"scale_up_memory"`
	ScaleDownMemory float64       `json:"scale_down_memory"`
	Cooldown        time.Duration `json:"cooldown"`
}

// ScaleFunc is a function that performs scaling
type ScaleFunc func(serviceID string, desiredReplicas int) error

// MetricsCollector collects metrics for scaling decisions
type MetricsCollector struct {
	mu      sync.RWMutex
	metrics map[string]*ServiceMetrics
}

// ServiceMetrics represents metrics for a service
type ServiceMetrics struct {
	CPUUsage    float64   `json:"cpu_usage"`
	MemoryUsage float64   `json:"memory_usage"`
	Requests    int64     `json:"requests"`
	Timestamp   time.Time `json:"timestamp"`
}

// NewMetricsCollector creates a new metrics collector
func NewMetricsCollector() *MetricsCollector {
	return &MetricsCollector{
		metrics: make(map[string]*ServiceMetrics),
	}
}

// UpdateMetrics updates metrics for a service
func (mc *MetricsCollector) UpdateMetrics(serviceID string, metrics *ServiceMetrics) {
	mc.mu.Lock()
	defer mc.mu.Unlock()
	mc.metrics[serviceID] = metrics
}

// GetMetrics returns metrics for a service
func (mc *MetricsCollector) GetMetrics(serviceID string) (*ServiceMetrics, bool) {
	mc.mu.RLock()
	defer mc.mu.RUnlock()
	m, ok := mc.metrics[serviceID]
	return m, ok
}

// NewScaler creates a new scaler
func NewScaler(scaleFunc ScaleFunc) *Scaler {
	return &Scaler{
		services:  make(map[string]*ServiceState),
		policies:  make(map[string]*ScalingPolicy),
		metrics:   NewMetricsCollector(),
		scaleFunc: scaleFunc,
		cooldowns: make(map[string]time.Time),
	}
}

// RegisterService registers a service for scaling
func (s *Scaler) RegisterService(serviceID string, replicas int, policy *ScalingPolicy) {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.services[serviceID] = &ServiceState{
		ServiceID:       serviceID,
		CurrentReplicas: replicas,
		DesiredReplicas: replicas,
	}

	if policy != nil {
		s.policies[serviceID] = policy
	}
}

// UnregisterService unregisters a service
func (s *Scaler) UnregisterService(serviceID string) {
	s.mu.Lock()
	defer s.mu.Unlock()

	delete(s.services, serviceID)
	delete(s.policies, serviceID)
	delete(s.cooldowns, serviceID)
}

// UpdateMetrics updates metrics for a service
func (s *Scaler) UpdateMetrics(serviceID string, metrics *ServiceMetrics) {
	s.metrics.UpdateMetrics(serviceID, metrics)
}

// Evaluate evaluates scaling for all services
func (s *Scaler) Evaluate() []ScaleDecision {
	s.mu.RLock()
	var decisions []ScaleDecision
	for serviceID := range s.services {
		if decision := s.evaluateService(serviceID); decision != nil {
			decisions = append(decisions, *decision)
		}
	}
	s.mu.RUnlock()

	return decisions
}

// evaluateService evaluates scaling for a single service
func (s *Scaler) evaluateService(serviceID string) *ScaleDecision {
	state, exists := s.services[serviceID]
	if !exists || state.Scaling {
		return nil
	}

	policy, exists := s.policies[serviceID]
	if !exists {
		return nil
	}

	// Check cooldown
	if lastScale, ok := s.cooldowns[serviceID]; ok {
		if time.Since(lastScale) < policy.Cooldown {
			return nil
		}
	}

	metrics, exists := s.metrics.GetMetrics(serviceID)
	if !exists {
		return nil
	}

	// Evaluate scale up
	if metrics.CPUUsage > policy.ScaleUpCPU || metrics.MemoryUsage > policy.ScaleUpMemory {
		if state.CurrentReplicas < policy.MaxReplicas {
			newReplicas := state.CurrentReplicas + 1
			if newReplicas > policy.MaxReplicas {
				newReplicas = policy.MaxReplicas
			}
			return &ScaleDecision{
				ServiceID:       serviceID,
				Direction:       ScaleUp,
				CurrentReplicas: state.CurrentReplicas,
				DesiredReplicas: newReplicas,
				Reason:          "high resource usage",
				Timestamp:       time.Now(),
			}
		}
	}

	// Evaluate scale down
	if metrics.CPUUsage < policy.ScaleDownCPU && metrics.MemoryUsage < policy.ScaleDownMemory {
		if state.CurrentReplicas > policy.MinReplicas {
			newReplicas := state.CurrentReplicas - 1
			if newReplicas < policy.MinReplicas {
				newReplicas = policy.MinReplicas
			}
			return &ScaleDecision{
				ServiceID:       serviceID,
				Direction:       ScaleDown,
				CurrentReplicas: state.CurrentReplicas,
				DesiredReplicas: newReplicas,
				Reason:          "low resource usage",
				Timestamp:       time.Now(),
			}
		}
	}

	return nil
}

// Scale performs scaling for a service
func (s *Scaler) Scale(serviceID string, desiredReplicas int) error {
	s.mu.Lock()
	state, exists := s.services[serviceID]
	if !exists {
		s.mu.Unlock()
		return ErrServiceNotFound
	}

	if state.Scaling {
		s.mu.Unlock()
		return ErrScalingInProgress
	}

	state.Scaling = true
	state.DesiredReplicas = desiredReplicas
	s.mu.Unlock()

	// Perform scaling
	err := s.scaleFunc(serviceID, desiredReplicas)

	s.mu.Lock()
	state.Scaling = false
	if err == nil {
		state.CurrentReplicas = desiredReplicas
		state.LastScaleTime = time.Now()
		s.cooldowns[serviceID] = time.Now()
	}
	s.mu.Unlock()

	return err
}

// ScaleDecision represents a scaling decision
type ScaleDecision struct {
	ServiceID       string      `json:"service_id"`
	Direction       ScaleDirection `json:"direction"`
	CurrentReplicas int         `json:"current_replicas"`
	DesiredReplicas int         `json:"desired_replicas"`
	Reason          string      `json:"reason"`
	Timestamp       time.Time   `json:"timestamp"`
}

// ScaleDirection represents the direction of scaling
type ScaleDirection string

const (
	ScaleUp   ScaleDirection = "scale_up"
	ScaleDown ScaleDirection = "scale_down"
)

// AutoScale runs the auto-scaling loop
func (s *Scaler) AutoScale(ctx context.Context, interval time.Duration) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			decisions := s.Evaluate()
			for _, decision := range decisions {
				_ = s.Scale(decision.ServiceID, decision.DesiredReplicas)
			}
		}
	}
}

// GetServiceState returns the current state of a service
func (s *Scaler) GetServiceState(serviceID string) (*ServiceState, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	state, exists := s.services[serviceID]
	if !exists {
		return nil, ErrServiceNotFound
	}

	return state, nil
}

// GetAllServiceStates returns states of all services
func (s *Scaler) GetAllServiceStates() map[string]*ServiceState {
	s.mu.RLock()
	defer s.mu.RUnlock()

	states := make(map[string]*ServiceState, len(s.services))
	for id, state := range s.services {
		states[id] = state
	}

	return states
}

// ManualScale manually scales a service
func (s *Scaler) ManualScale(serviceID string, desiredReplicas int) error {
	s.mu.Lock()
	policy, exists := s.policies[serviceID]
	if !exists {
		// Create a default policy
		policy = &ScalingPolicy{
			MinReplicas: 1,
			MaxReplicas: 10,
		}
		s.policies[serviceID] = policy
	}
	s.mu.Unlock()

	if desiredReplicas < policy.MinReplicas {
		desiredReplicas = policy.MinReplicas
	}
	if desiredReplicas > policy.MaxReplicas {
		desiredReplicas = policy.MaxReplicas
	}

	return s.Scale(serviceID, desiredReplicas)
}

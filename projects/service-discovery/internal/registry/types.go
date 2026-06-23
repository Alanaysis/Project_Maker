// Package registry handles service registration and deregistration.
// Services register themselves in the key-value store with a lease,
// and must periodically refresh the lease to signal liveness.
package registry

import (
	"encoding/json"
	"errors"
	"fmt"
	"time"
)

var (
	ErrServiceNotFound = errors.New("service not found")
	ErrInvalidService  = errors.New("invalid service")
)

// ServiceStatus represents the health status of a service instance.
type ServiceStatus int

const (
	StatusUp      ServiceStatus = iota // Service is healthy
	StatusDown                         // Service is unhealthy
	StatusStarting                     // Service is starting up
)

func (s ServiceStatus) String() string {
	switch s {
	case StatusUp:
		return "up"
	case StatusDown:
		return "down"
	case StatusStarting:
		return "starting"
	default:
		return "unknown"
	}
}

// Service represents a single service instance in the registry.
type Service struct {
	ID        string            `json:"id"`
	Name      string            `json:"name"`
	Address   string            `json:"address"`
	Port      int               `json:"port"`
	Metadata  map[string]string `json:"metadata,omitempty"`
	Status    ServiceStatus     `json:"status"`
	RegisteredAt time.Time      `json:"registered_at"`
}

// Key returns the etcd key for this service.
// Format: /services/{name}/{id}
func (s *Service) Key() string {
	return fmt.Sprintf("/services/%s/%s", s.Name, s.ID)
}

// Endpoint returns the service endpoint as host:port.
func (s *Service) Endpoint() string {
	return fmt.Sprintf("%s:%d", s.Address, s.Port)
}

// Validate checks that the service has all required fields.
func (s *Service) Validate() error {
	if s.ID == "" {
		return fmt.Errorf("%w: missing ID", ErrInvalidService)
	}
	if s.Name == "" {
		return fmt.Errorf("%w: missing Name", ErrInvalidService)
	}
	if s.Address == "" {
		return fmt.Errorf("%w: missing Address", ErrInvalidService)
	}
	if s.Port <= 0 || s.Port > 65535 {
		return fmt.Errorf("%w: invalid Port %d", ErrInvalidService, s.Port)
	}
	return nil
}

// Marshal serializes the service to JSON bytes.
func (s *Service) Marshal() ([]byte, error) {
	return json.Marshal(s)
}

// UnmarshalService deserializes a service from JSON bytes.
func UnmarshalService(data []byte) (*Service, error) {
	var svc Service
	if err := json.Unmarshal(data, &svc); err != nil {
		return nil, fmt.Errorf("unmarshal service: %w", err)
	}
	return &svc, nil
}

// DefaultTTL is the default time-to-live for a service lease.
const DefaultTTL = 10 * time.Second

// DefaultHeartbeatInterval is how often the service refreshes its lease.
const DefaultHeartbeatInterval = 3 * time.Second

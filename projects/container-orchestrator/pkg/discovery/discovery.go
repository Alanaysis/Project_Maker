package discovery

import (
	"errors"
	"fmt"
	"sync"
	"time"

	"github.com/container-orchestrator/pkg/container"
)

var (
	ErrServiceNotFound = errors.New("service not found")
	ErrEndpointNotFound = errors.New("endpoint not found")
)

// Endpoint represents a service endpoint
type Endpoint struct {
	ID        string            `json:"id"`
	ServiceID string            `json:"service_id"`
	ContainerID string          `json:"container_id"`
	NodeID    string            `json:"node_id"`
	Address   string            `json:"address"`
	Port      int               `json:"port"`
	Labels    map[string]string `json:"labels"`
	Health    HealthStatus      `json:"health"`
	Weight    int               `json:"weight"`
	LastSeen  time.Time         `json:"last_seen"`
}

// HealthStatus represents endpoint health
type HealthStatus string

const (
	HealthHealthy   HealthStatus = "healthy"
	HealthUnhealthy HealthStatus = "unhealthy"
	HealthUnknown   HealthStatus = "unknown"
)

// ServiceEntry represents a service with its endpoints
type ServiceEntry struct {
	Service   *container.Service `json:"service"`
	Endpoints map[string]*Endpoint `json:"endpoints"`
	mu        sync.RWMutex
}

// Discovery handles service discovery
type Discovery struct {
	mu       sync.RWMutex
	services map[string]*ServiceEntry
	watches  map[string][]chan *ServiceEvent
}

// ServiceEvent represents a service event
type ServiceEvent struct {
	Type      EventType  `json:"type"`
	ServiceID string     `json:"service_id"`
	Endpoint  *Endpoint  `json:"endpoint,omitempty"`
	Timestamp time.Time  `json:"timestamp"`
}

// EventType represents the type of service event
type EventType string

const (
	EventEndpointAdded   EventType = "endpoint_added"
	EventEndpointRemoved EventType = "endpoint_removed"
	EventEndpointUpdated EventType = "endpoint_updated"
	EventServiceAdded    EventType = "service_added"
	EventServiceRemoved  EventType = "service_removed"
)

// NewDiscovery creates a new service discovery
func NewDiscovery() *Discovery {
	return &Discovery{
		services: make(map[string]*ServiceEntry),
		watches:  make(map[string][]chan *ServiceEvent),
	}
}

// RegisterService registers a service
func (d *Discovery) RegisterService(service *container.Service) error {
	d.mu.Lock()
	defer d.mu.Unlock()

	if _, exists := d.services[service.ID]; exists {
		return errors.New("service already registered")
	}

	d.services[service.ID] = &ServiceEntry{
		Service:   service,
		Endpoints: make(map[string]*Endpoint),
	}

	d.notifyWatchers(&ServiceEvent{
		Type:      EventServiceAdded,
		ServiceID: service.ID,
		Timestamp: time.Now(),
	})

	return nil
}

// UnregisterService unregisters a service
func (d *Discovery) UnregisterService(serviceID string) error {
	d.mu.Lock()
	defer d.mu.Unlock()

	if _, exists := d.services[serviceID]; !exists {
		return ErrServiceNotFound
	}

	delete(d.services, serviceID)

	d.notifyWatchers(&ServiceEvent{
		Type:      EventServiceRemoved,
		ServiceID: serviceID,
		Timestamp: time.Now(),
	})

	return nil
}

// GetService returns a service by ID
func (d *Discovery) GetService(serviceID string) (*container.Service, error) {
	d.mu.RLock()
	defer d.mu.RUnlock()

	entry, exists := d.services[serviceID]
	if !exists {
		return nil, ErrServiceNotFound
	}

	return entry.Service, nil
}

// GetServiceByName returns a service by name
func (d *Discovery) GetServiceByName(name string) (*container.Service, error) {
	d.mu.RLock()
	defer d.mu.RUnlock()

	for _, entry := range d.services {
		if entry.Service.Name == name {
			return entry.Service, nil
		}
	}

	return nil, ErrServiceNotFound
}

// RegisterEndpoint registers an endpoint for a service
func (d *Discovery) RegisterEndpoint(endpoint *Endpoint) error {
	d.mu.Lock()
	defer d.mu.Unlock()

	entry, exists := d.services[endpoint.ServiceID]
	if !exists {
		return ErrServiceNotFound
	}

	entry.mu.Lock()
	defer entry.mu.Unlock()

	// Only update LastSeen if not already set (to allow tests to set custom times)
	if endpoint.LastSeen.IsZero() {
		endpoint.LastSeen = time.Now()
	}
	entry.Endpoints[endpoint.ID] = endpoint

	d.notifyWatchers(&ServiceEvent{
		Type:      EventEndpointAdded,
		ServiceID: endpoint.ServiceID,
		Endpoint:  endpoint,
		Timestamp: time.Now(),
	})

	return nil
}

// UnregisterEndpoint unregisters an endpoint
func (d *Discovery) UnregisterEndpoint(serviceID, endpointID string) error {
	d.mu.Lock()
	defer d.mu.Unlock()

	entry, exists := d.services[serviceID]
	if !exists {
		return ErrServiceNotFound
	}

	entry.mu.Lock()
	defer entry.mu.Unlock()

	endpoint, exists := entry.Endpoints[endpointID]
	if !exists {
		return ErrEndpointNotFound
	}

	delete(entry.Endpoints, endpointID)

	d.notifyWatchers(&ServiceEvent{
		Type:      EventEndpointRemoved,
		ServiceID: serviceID,
		Endpoint:  endpoint,
		Timestamp: time.Now(),
	})

	return nil
}

// GetEndpoints returns all endpoints for a service
func (d *Discovery) GetEndpoints(serviceID string) ([]*Endpoint, error) {
	d.mu.RLock()
	defer d.mu.RUnlock()

	entry, exists := d.services[serviceID]
	if !exists {
		return nil, ErrServiceNotFound
	}

	entry.mu.RLock()
	defer entry.mu.RUnlock()

	endpoints := make([]*Endpoint, 0, len(entry.Endpoints))
	for _, ep := range entry.Endpoints {
		endpoints = append(endpoints, ep)
	}

	return endpoints, nil
}

// GetHealthyEndpoints returns healthy endpoints for a service
func (d *Discovery) GetHealthyEndpoints(serviceID string) ([]*Endpoint, error) {
	endpoints, err := d.GetEndpoints(serviceID)
	if err != nil {
		return nil, err
	}

	var healthy []*Endpoint
	for _, ep := range endpoints {
		if ep.Health == HealthHealthy {
			healthy = append(healthy, ep)
		}
	}

	return healthy, nil
}

// Resolve resolves a service name to an endpoint using load balancing
func (d *Discovery) Resolve(serviceName string) (*Endpoint, error) {
	service, err := d.GetServiceByName(serviceName)
	if err != nil {
		return nil, err
	}

	endpoints, err := d.GetHealthyEndpoints(service.ID)
	if err != nil {
		return nil, err
	}

	if len(endpoints) == 0 {
		return nil, fmt.Errorf("no healthy endpoints for service %s", serviceName)
	}

	// Simple weighted round-robin
	var selected *Endpoint
	maxWeight := 0
	for _, ep := range endpoints {
		if ep.Weight > maxWeight {
			maxWeight = ep.Weight
			selected = ep
		}
	}

	// If all weights are equal, use round-robin based on last seen
	if selected == nil {
		selected = endpoints[0]
		for _, ep := range endpoints[1:] {
			if ep.LastSeen.Before(selected.LastSeen) {
				selected = ep
			}
		}
	}

	return selected, nil
}

// Watch watches for service events
func (d *Discovery) Watch(serviceID string) <-chan *ServiceEvent {
	d.mu.Lock()
	defer d.mu.Unlock()

	ch := make(chan *ServiceEvent, 100)
	d.watches[serviceID] = append(d.watches[serviceID], ch)

	return ch
}

// notifyWatchers notifies all watchers of an event
func (d *Discovery) notifyWatchers(event *ServiceEvent) {
	// Notify service-specific watchers
	if watchers, ok := d.watches[event.ServiceID]; ok {
		for _, ch := range watchers {
			select {
			case ch <- event:
			default:
				// Skip if channel is full
			}
		}
	}

	// Notify global watchers
	if watchers, ok := d.watches["*"]; ok {
		for _, ch := range watchers {
			select {
			case ch <- event:
			default:
				// Skip if channel is full
			}
		}
	}
}

// GetServiceCount returns the number of registered services
func (d *Discovery) GetServiceCount() int {
	d.mu.RLock()
	defer d.mu.RUnlock()
	return len(d.services)
}

// GetEndpointCount returns the total number of endpoints
func (d *Discovery) GetEndpointCount() int {
	d.mu.RLock()
	defer d.mu.RUnlock()

	count := 0
	for _, entry := range d.services {
		entry.mu.RLock()
		count += len(entry.Endpoints)
		entry.mu.RUnlock()
	}

	return count
}

// Cleanup removes unhealthy endpoints that haven't been seen recently
func (d *Discovery) Cleanup(maxAge time.Duration) int {
	d.mu.Lock()
	defer d.mu.Unlock()

	removed := 0
	cutoff := time.Now().Add(-maxAge)

	for _, entry := range d.services {
		entry.mu.Lock()
		for id, ep := range entry.Endpoints {
			if ep.Health == HealthUnhealthy && ep.LastSeen.Before(cutoff) {
				delete(entry.Endpoints, id)
				removed++
			}
		}
		entry.mu.Unlock()
	}

	return removed
}

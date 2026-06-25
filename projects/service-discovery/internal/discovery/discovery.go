// Package discovery implements service discovery by watching the key-value
// store for changes and maintaining a local cache of available services.
package discovery

import (
	"context"
	"fmt"
	"log"
	"sync"

	"github.com/anthropic/service-discovery/internal/registry"
	"github.com/anthropic/service-discovery/internal/store"
)

// ServiceListChangedFunc is called when the service list changes.
type ServiceListChangedFunc func(services []*registry.Service)

// Discoverer watches the store for service changes and maintains a local cache.
type Discoverer struct {
	store    store.Store
	mu       sync.RWMutex
	services map[string]map[string]*registry.Service // name -> id -> service
	onChange ServiceListChangedFunc
	stopCh   chan struct{}
}

// Option is a function that configures a Discoverer.
type Option func(*Discoverer)

// WithOnChange sets a callback for when the service list changes.
func WithOnChange(fn ServiceListChangedFunc) Option {
	return func(d *Discoverer) {
		d.onChange = fn
	}
}

// New creates a new Discoverer.
func New(s store.Store, opts ...Option) *Discoverer {
	d := &Discoverer{
		store:    s,
		services: make(map[string]map[string]*registry.Service),
		stopCh:   make(chan struct{}),
	}
	for _, opt := range opts {
		opt(d)
	}
	return d
}

// Start begins watching the store for service changes. It performs an initial
// list of all services before starting the watch.
func (d *Discoverer) Start(ctx context.Context) error {
	// Initial load of all services
	if err := d.loadAll(ctx); err != nil {
		return fmt.Errorf("initial load: %w", err)
	}

	// Start watching for changes
	watchCh, err := d.store.Watch(ctx, "/services/")
	if err != nil {
		return fmt.Errorf("start watch: %w", err)
	}

	go d.watchLoop(ctx, watchCh)

	log.Printf("[discovery] started, watching for service changes")
	return nil
}

// Stop stops the discoverer.
func (d *Discoverer) Stop() {
	close(d.stopCh)
}

// GetServices returns all healthy instances of a service by name.
func (d *Discoverer) GetServices(name string) []*registry.Service {
	d.mu.RLock()
	defer d.mu.RUnlock()

	instances, ok := d.services[name]
	if !ok {
		return nil
	}

	result := make([]*registry.Service, 0, len(instances))
	for _, svc := range instances {
		if svc.Status == registry.StatusUp {
			result = append(result, svc)
		}
	}
	return result
}

// GetServicesByTags returns all healthy instances of a service that match the given tags.
// All provided tags must match (AND logic).
func (d *Discoverer) GetServicesByTags(name string, tags map[string]string) []*registry.Service {
	d.mu.RLock()
	defer d.mu.RUnlock()

	instances, ok := d.services[name]
	if !ok {
		return nil
	}

	result := make([]*registry.Service, 0, len(instances))
	for _, svc := range instances {
		if svc.Status != registry.StatusUp {
			continue
		}
		if matchTags(svc, tags) {
			result = append(result, svc)
		}
	}
	return result
}

// GetAllServicesByTags returns all healthy services that match the given tags.
func (d *Discoverer) GetAllServicesByTags(tags map[string]string) map[string][]*registry.Service {
	d.mu.RLock()
	defer d.mu.RUnlock()

	result := make(map[string][]*registry.Service)
	for name, instances := range d.services {
		for _, svc := range instances {
			if svc.Status != registry.StatusUp {
				continue
			}
			if matchTags(svc, tags) {
				result[name] = append(result[name], svc)
			}
		}
	}
	return result
}

// matchTags checks if a service has all the specified tags in its metadata.
func matchTags(svc *registry.Service, tags map[string]string) bool {
	if len(tags) == 0 {
		return true
	}
	if svc.Metadata == nil {
		return false
	}
	for k, v := range tags {
		sv, ok := svc.Metadata[k]
		if !ok || sv != v {
			return false
		}
	}
	return true
}

// GetAllServices returns all registered services grouped by name.
func (d *Discoverer) GetAllServices() map[string][]*registry.Service {
	d.mu.RLock()
	defer d.mu.RUnlock()

	result := make(map[string][]*registry.Service, len(d.services))
	for name, instances := range d.services {
		services := make([]*registry.Service, 0, len(instances))
		for _, svc := range instances {
			services = append(services, svc)
		}
		result[name] = services
	}
	return result
}

// GetServiceNames returns all known service names.
func (d *Discoverer) GetServiceNames() []string {
	d.mu.RLock()
	defer d.mu.RUnlock()

	names := make([]string, 0, len(d.services))
	for name := range d.services {
		names = append(names, name)
	}
	return names
}

// Count returns the number of healthy instances for a service.
func (d *Discoverer) Count(name string) int {
	return len(d.GetServices(name))
}

// loadAll performs an initial load of all services from the store.
func (d *Discoverer) loadAll(ctx context.Context) error {
	data, err := d.store.List(ctx, "/services/")
	if err != nil {
		return err
	}

	d.mu.Lock()
	defer d.mu.Unlock()

	for _, v := range data {
		svc, err := registry.UnmarshalService(v)
		if err != nil {
			log.Printf("[discovery] failed to unmarshal service: %v", err)
			continue
		}
		d.addServiceLocked(svc)
	}

	log.Printf("[discovery] loaded %d services", len(data))
	return nil
}

// watchLoop processes watch events from the store.
func (d *Discoverer) watchLoop(ctx context.Context, ch <-chan store.Event) {
	for {
		select {
		case <-ctx.Done():
			return
		case <-d.stopCh:
			return
		case event, ok := <-ch:
			if !ok {
				return
			}
			d.handleEvent(event)
		}
	}
}

// handleEvent processes a single store event.
func (d *Discoverer) handleEvent(event store.Event) {
	switch event.Type {
	case store.EventPut:
		svc, err := registry.UnmarshalService(event.Value)
		if err != nil {
			log.Printf("[discovery] failed to unmarshal service: %v", err)
			return
		}
		d.mu.Lock()
		d.addServiceLocked(svc)
		d.mu.Unlock()

		log.Printf("[discovery] service %s/%s updated", svc.Name, svc.ID)
		d.notifyChange()

	case store.EventDelete:
		id := extractIDFromKey(event.Key)
		name := extractNameFromKey(event.Key)

		d.mu.Lock()
		if instances, ok := d.services[name]; ok {
			delete(instances, id)
			if len(instances) == 0 {
				delete(d.services, name)
			}
		}
		d.mu.Unlock()

		log.Printf("[discovery] service %s/%s removed", name, id)
		d.notifyChange()
	}
}

// addServiceLocked adds a service to the cache. Must be called with mu held.
func (d *Discoverer) addServiceLocked(svc *registry.Service) {
	if _, ok := d.services[svc.Name]; !ok {
		d.services[svc.Name] = make(map[string]*registry.Service)
	}
	d.services[svc.Name][svc.ID] = svc
}

// notifyChange calls the onChange callback with the current service list.
func (d *Discoverer) notifyChange() {
	if d.onChange == nil {
		return
	}

	d.mu.RLock()
	var all []*registry.Service
	for _, instances := range d.services {
		for _, svc := range instances {
			all = append(all, svc)
		}
	}
	d.mu.RUnlock()

	d.onChange(all)
}

// extractIDFromKey extracts the service ID from a key like /services/{name}/{id}.
func extractIDFromKey(key string) string {
	for i := len(key) - 1; i >= 0; i-- {
		if key[i] == '/' {
			return key[i+1:]
		}
	}
	return ""
}

// extractNameFromKey extracts the service name from a key like /services/{name}/{id}.
func extractNameFromKey(key string) string {
	// Find the second-to-last /
	count := 0
	for i := len(key) - 1; i >= 0; i-- {
		if key[i] == '/' {
			count++
			if count == 2 {
				return key[i+1 : len(key)-len(extractIDFromKey(key))-1]
			}
		}
	}
	return ""
}

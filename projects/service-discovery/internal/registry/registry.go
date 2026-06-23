package registry

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/anthropic/service-discovery/internal/store"
)

// Registry manages service registration with a key-value store.
// It handles lease creation, heartbeat, and deregistration.
type Registry struct {
	store   store.Store
	mu      sync.RWMutex
	entries map[string]*registryEntry // key: service ID
	stopCh  chan struct{}
}

type registryEntry struct {
	Service *Service
	LeaseID int64
	cancel  context.CancelFunc
}

// Option is a function that configures a Registry.
type Option func(*Registry)

// New creates a new Registry with the given store and options.
func New(s store.Store, opts ...Option) *Registry {
	r := &Registry{
		store:   s,
		entries: make(map[string]*registryEntry),
		stopCh:  make(chan struct{}),
	}
	for _, opt := range opts {
		opt(r)
	}
	return r
}

// Register registers a service with the store. It creates a lease and
// starts a background goroutine to keep the lease alive.
func (r *Registry) Register(ctx context.Context, svc *Service, ttl time.Duration) error {
	if err := svc.Validate(); err != nil {
		return err
	}

	// Marshal service data
	data, err := svc.Marshal()
	if err != nil {
		return fmt.Errorf("marshal service: %w", err)
	}

	// Create lease
	leaseID, err := r.store.GrantLease(ctx, ttl)
	if err != nil {
		return fmt.Errorf("grant lease: %w", err)
	}

	// Put service in store with lease
	key := svc.Key()
	if err := r.store.Put(ctx, key, data, leaseID); err != nil {
		// Try to revoke lease on failure
		_ = r.store.RevokeLease(ctx, leaseID)
		return fmt.Errorf("put service: %w", err)
	}

	// Start heartbeat goroutine
	heartbeatCtx, cancel := context.WithCancel(context.Background())
	entry := &registryEntry{
		Service: svc,
		LeaseID: leaseID,
		cancel:  cancel,
	}

	r.mu.Lock()
	r.entries[svc.ID] = entry
	r.mu.Unlock()

	go r.heartbeat(heartbeatCtx, svc, leaseID, ttl)

	log.Printf("[registry] registered service %s (%s) with lease %d", svc.Name, svc.Endpoint(), leaseID)
	return nil
}

// Deregister removes a service from the store and stops its heartbeat.
func (r *Registry) Deregister(ctx context.Context, serviceID string) error {
	r.mu.Lock()
	entry, ok := r.entries[serviceID]
	if !ok {
		r.mu.Unlock()
		return ErrServiceNotFound
	}
	delete(r.entries, serviceID)
	r.mu.Unlock()

	// Stop heartbeat
	entry.cancel()

	// Revoke lease (this also deletes associated keys)
	if err := r.store.RevokeLease(ctx, entry.LeaseID); err != nil {
		log.Printf("[registry] failed to revoke lease %d: %v", entry.LeaseID, err)
	}

	log.Printf("[registry] deregistered service %s (%s)", entry.Service.Name, entry.Service.Endpoint())
	return nil
}

// GetService returns a registered service by ID.
func (r *Registry) GetService(serviceID string) (*Service, error) {
	r.mu.RLock()
	entry, ok := r.entries[serviceID]
	r.mu.RUnlock()

	if !ok {
		return nil, ErrServiceNotFound
	}
	return entry.Service, nil
}

// ListRegistered returns all services registered by this registry instance.
func (r *Registry) ListRegistered() []*Service {
	r.mu.RLock()
	defer r.mu.RUnlock()

	services := make([]*Service, 0, len(r.entries))
	for _, entry := range r.entries {
		services = append(services, entry.Service)
	}
	return services
}

// Stop deregisters all services and stops all heartbeats.
func (r *Registry) Stop() {
	close(r.stopCh)

	r.mu.Lock()
	entries := make([]*registryEntry, 0, len(r.entries))
	for _, entry := range r.entries {
		entries = append(entries, entry)
	}
	r.entries = make(map[string]*registryEntry)
	r.mu.Unlock()

	for _, entry := range entries {
		entry.cancel()
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		_ = r.store.RevokeLease(ctx, entry.LeaseID)
		cancel()
	}

	log.Printf("[registry] stopped, deregistered %d services", len(entries))
}

// heartbeat periodically refreshes the lease for a service.
func (r *Registry) heartbeat(ctx context.Context, svc *Service, leaseID int64, ttl time.Duration) {
	interval := ttl / 3
	if interval < time.Second {
		interval = time.Second
	}

	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-r.stopCh:
			return
		case <-ticker.C:
			if err := r.store.KeepAlive(ctx, leaseID); err != nil {
				log.Printf("[registry] heartbeat failed for %s: %v", svc.Name, err)
				return
			}
		}
	}
}

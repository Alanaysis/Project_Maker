// Package store defines the interface for a key-value store used by the
// service discovery system. The primary implementation is etcd, but an
// in-memory implementation is provided for testing.
package store

import (
	"context"
	"errors"
	"sync"
	"time"
)

var (
	// ErrKeyNotFound is returned when a key does not exist.
	ErrKeyNotFound = errors.New("key not found")
	// ErrKeyExpired is returned when a key's lease has expired.
	ErrKeyExpired = errors.New("key expired")
	// ErrLeaseNotFound is returned when a lease does not exist.
	ErrLeaseNotFound = errors.New("lease not found")
)

// EventType describes the kind of watch event.
type EventType int

const (
	EventPut EventType = iota
	EventDelete
)

// Event represents a change to a key in the store.
type Event struct {
	Type  EventType
	Key   string
	Value []byte
}

// Lease represents a time-based lease on one or more keys.
type Lease struct {
	ID       int64
	TTL      time.Duration
	ExpireAt time.Time
}

// Store is the interface for a key-value store with lease support and watching.
type Store interface {
	// Put stores a key-value pair with an optional lease.
	Put(ctx context.Context, key string, value []byte, leaseID int64) error

	// Get retrieves the value for a key.
	Get(ctx context.Context, key string) ([]byte, error)

	// Delete removes a key.
	Delete(ctx context.Context, key string) error

	// List retrieves all key-value pairs with the given prefix.
	List(ctx context.Context, prefix string) (map[string][]byte, error)

	// GrantLease creates a new lease with the given TTL.
	GrantLease(ctx context.Context, ttl time.Duration) (int64, error)

	// KeepAlive refreshes a lease to prevent expiration.
	KeepAlive(ctx context.Context, leaseID int64) error

	// RevokeLease deletes a lease and all associated keys.
	RevokeLease(ctx context.Context, leaseID int64) error

	// Watch returns a channel that receives events for the given prefix.
	Watch(ctx context.Context, prefix string) (<-chan Event, error)

	// Close closes the store connection.
	Close() error
}

// MemStore is an in-memory implementation of Store for testing.
type MemStore struct {
	mu      sync.RWMutex
	data    map[string]*memEntry
	leases  map[int64]*Lease
	watchers []watcher
	nextID  int64
}

type memEntry struct {
	Value   []byte
	LeaseID int64
}

type watcher struct {
	prefix string
	ch     chan Event
}

// NewMemStore creates a new in-memory store.
func NewMemStore() *MemStore {
	return &MemStore{
		data:   make(map[string]*memEntry),
		leases: make(map[int64]*Lease),
		nextID: 1,
	}
}

func (m *MemStore) Put(ctx context.Context, key string, value []byte, leaseID int64) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	m.data[key] = &memEntry{Value: value, LeaseID: leaseID}

	// Notify watchers
	for _, w := range m.watchers {
		if len(key) >= len(w.prefix) && key[:len(w.prefix)] == w.prefix {
			select {
			case w.ch <- Event{Type: EventPut, Key: key, Value: value}:
			default:
			}
		}
	}

	return nil
}

func (m *MemStore) Get(ctx context.Context, key string) ([]byte, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	entry, ok := m.data[key]
	if !ok {
		return nil, ErrKeyNotFound
	}

	// Check lease expiration
	if entry.LeaseID != 0 {
		lease, exists := m.leases[entry.LeaseID]
		if !exists || time.Now().After(lease.ExpireAt) {
			return nil, ErrKeyExpired
		}
	}

	result := make([]byte, len(entry.Value))
	copy(result, entry.Value)
	return result, nil
}

func (m *MemStore) Delete(ctx context.Context, key string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if _, ok := m.data[key]; !ok {
		return ErrKeyNotFound
	}

	delete(m.data, key)

	// Notify watchers
	for _, w := range m.watchers {
		if len(key) >= len(w.prefix) && key[:len(w.prefix)] == w.prefix {
			select {
			case w.ch <- Event{Type: EventDelete, Key: key}:
			default:
			}
		}
	}

	return nil
}

func (m *MemStore) List(ctx context.Context, prefix string) (map[string][]byte, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	result := make(map[string][]byte)
	for key, entry := range m.data {
		if len(key) >= len(prefix) && key[:len(prefix)] == prefix {
			// Check lease
			if entry.LeaseID != 0 {
				lease, exists := m.leases[entry.LeaseID]
				if !exists || time.Now().After(lease.ExpireAt) {
					continue
				}
			}
			val := make([]byte, len(entry.Value))
			copy(val, entry.Value)
			result[key] = val
		}
	}

	return result, nil
}

func (m *MemStore) GrantLease(ctx context.Context, ttl time.Duration) (int64, error) {
	m.mu.Lock()
	defer m.mu.Unlock()

	id := m.nextID
	m.nextID++

	m.leases[id] = &Lease{
		ID:       id,
		TTL:      ttl,
		ExpireAt: time.Now().Add(ttl),
	}

	return id, nil
}

func (m *MemStore) KeepAlive(ctx context.Context, leaseID int64) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	lease, ok := m.leases[leaseID]
	if !ok {
		return ErrLeaseNotFound
	}

	lease.ExpireAt = time.Now().Add(lease.TTL)
	return nil
}

func (m *MemStore) RevokeLease(ctx context.Context, leaseID int64) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	lease, ok := m.leases[leaseID]
	if !ok {
		return ErrLeaseNotFound
	}

	// Delete all keys with this lease
	for key, entry := range m.data {
		if entry.LeaseID == leaseID {
			delete(m.data, key)
			// Notify watchers
			for _, w := range m.watchers {
				if len(key) >= len(w.prefix) && key[:len(w.prefix)] == w.prefix {
					select {
					case w.ch <- Event{Type: EventDelete, Key: key}:
					default:
					}
				}
			}
		}
	}

	delete(m.leases, lease.ID)
	return nil
}

func (m *MemStore) Watch(ctx context.Context, prefix string) (<-chan Event, error) {
	m.mu.Lock()
	defer m.mu.Unlock()

	ch := make(chan Event, 100)
	m.watchers = append(m.watchers, watcher{prefix: prefix, ch: ch})

	// Handle context cancellation
	go func() {
		<-ctx.Done()
		m.mu.Lock()
		defer m.mu.Unlock()
		for i, w := range m.watchers {
			if w.ch == ch {
				m.watchers = append(m.watchers[:i], m.watchers[i+1:]...)
				close(ch)
				break
			}
		}
	}()

	return ch, nil
}

func (m *MemStore) Close() error {
	m.mu.Lock()
	defer m.mu.Unlock()

	for _, w := range m.watchers {
		close(w.ch)
	}
	m.watchers = nil
	return nil
}

// ExpireLeases removes expired leases and their associated keys.
// This is useful for testing to simulate lease expiration.
func (m *MemStore) ExpireLeases() {
	m.mu.Lock()
	defer m.mu.Unlock()

	now := time.Now()
	for id, lease := range m.leases {
		if now.After(lease.ExpireAt) {
			// Delete keys with expired lease
			for key, entry := range m.data {
				if entry.LeaseID == id {
					delete(m.data, key)
					for _, w := range m.watchers {
						if len(key) >= len(w.prefix) && key[:len(w.prefix)] == w.prefix {
							select {
							case w.ch <- Event{Type: EventDelete, Key: key}:
							default:
							}
						}
					}
				}
			}
			delete(m.leases, id)
		}
	}
}

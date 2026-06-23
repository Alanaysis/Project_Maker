package state

import (
	"sync"
)

// StateStore provides a key-value state backend for operators.
// It supports basic CRUD operations and is safe for concurrent use.
type StateStore struct {
	mu    sync.RWMutex
	store map[string]interface{}
}

// NewStateStore creates a new empty state store.
func NewStateStore() *StateStore {
	return &StateStore{
		store: make(map[string]interface{}),
	}
}

// Get retrieves a value by key. Returns nil if not found.
func (s *StateStore) Get(key string) (interface{}, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	val, ok := s.store[key]
	return val, ok
}

// Put stores a value under the given key.
func (s *StateStore) Put(key string, value interface{}) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.store[key] = value
}

// Delete removes a key from the store.
func (s *StateStore) Delete(key string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	delete(s.store, key)
}

// Keys returns all keys in the store.
func (s *StateStore) Keys() []string {
	s.mu.RLock()
	defer s.mu.RUnlock()
	keys := make([]string, 0, len(s.store))
	for k := range s.store {
		keys = append(keys, k)
	}
	return keys
}

// Size returns the number of entries in the store.
func (s *StateStore) Size() int {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return len(s.store)
}

// Clear removes all entries.
func (s *StateStore) Clear() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.store = make(map[string]interface{})
}

// GetOrDefault retrieves a value by key, returning the default if not found.
func (s *StateStore) GetOrDefault(key string, defaultVal interface{}) interface{} {
	if val, ok := s.Get(key); ok {
		return val
	}
	return defaultVal
}

// Update atomically reads, transforms, and writes a value.
// The update function receives the current value (nil if not present)
// and returns the new value.
func (s *StateStore) Update(key string, updateFn func(current interface{}) interface{}) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.store[key] = updateFn(s.store[key])
}

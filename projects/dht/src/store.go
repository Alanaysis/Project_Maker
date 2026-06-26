package chord

import (
	"sync"
)

// KeyValueStore is a thread-safe in-memory key-value store.
// Each Chord node uses this to store key-value pairs for keys it is responsible for.
type KeyValueStore struct {
	data map[string]string
	mu   sync.RWMutex
}

// NewKeyValueStore creates a new empty key-value store.
func NewKeyValueStore() *KeyValueStore {
	return &KeyValueStore{
		data: make(map[string]string),
	}
}

// Put stores a key-value pair in the store.
func (ks *KeyValueStore) Put(key, value string) {
	ks.mu.Lock()
	defer ks.mu.Unlock()
	ks.data[key] = value
}

// Get retrieves a value by key. Returns the value and true if found, or "" and false if not.
func (ks *KeyValueStore) Get(key string) (string, bool) {
	ks.mu.RLock()
	defer ks.mu.RUnlock()
	val, ok := ks.data[key]
	return val, ok
}

// Delete removes a key from the store. Returns true if the key was found and deleted.
func (ks *KeyValueStore) Delete(key string) bool {
	ks.mu.Lock()
	defer ks.mu.Unlock()
	if _, ok := ks.data[key]; ok {
		delete(ks.data, key)
		return true
	}
	return false
}

// Keys returns all keys in the store.
func (ks *KeyValueStore) Keys() []string {
	ks.mu.RLock()
	defer ks.mu.RUnlock()
	keys := make([]string, 0, len(ks.data))
	for k := range ks.data {
		keys = append(keys, k)
	}
	return keys
}

// Size returns the number of key-value pairs in the store.
func (ks *KeyValueStore) Size() int {
	ks.mu.RLock()
	defer ks.mu.RUnlock()
	return len(ks.data)
}

// Clear removes all key-value pairs from the store.
func (ks *KeyValueStore) Clear() {
	ks.mu.Lock()
	defer ks.mu.Unlock()
	ks.data = make(map[string]string)
}

// Has checks if a key exists in the store.
func (ks *KeyValueStore) Has(key string) bool {
	ks.mu.RLock()
	defer ks.mu.RUnlock()
	_, ok := ks.data[key]
	return ok
}

// Values returns all values in the store.
func (ks *KeyValueStore) Values() []string {
	ks.mu.RLock()
	defer ks.mu.RUnlock()
	values := make([]string, 0, len(ks.data))
	for _, v := range ks.data {
		values = append(values, v)
	}
	return values
}

// ForEach iterates over all key-value pairs in the store.
func (ks *KeyValueStore) ForEach(fn func(key, value string)) {
	ks.mu.RLock()
	defer ks.mu.RUnlock()
	for k, v := range ks.data {
		fn(k, v)
	}
}

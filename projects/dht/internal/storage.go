package internal

import (
	"fmt"
	"log"
	"sync"
	"time"
)

// StorageItem represents an item in distributed storage
type StorageItem struct {
	Key       string    `json:"key"`
	Value     string    `json:"value"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
	TTL       int64     `json:"ttl"` // Time to live in seconds, 0 = no expiry
	Replicas  int       `json:"replicas"`
}

// DistributedStorage implements a distributed key-value store over DHT
type DistributedStorage struct {
	mu       sync.RWMutex
	node     *NetworkNode
	items    map[string]*StorageItem
	replicas int // Number of replicas for each item
}

// NewDistributedStorage creates a new distributed storage
func NewDistributedStorage(node *NetworkNode, replicas int) *DistributedStorage {
	if replicas < 1 {
		replicas = 3 // Default 3 replicas
	}
	return &DistributedStorage{
		node:     node,
		items:    make(map[string]*StorageItem),
		replicas: replicas,
	}
}

// Put stores a key-value pair with optional TTL
func (ds *DistributedStorage) Put(key, value string, ttl int64) error {
	ds.mu.Lock()
	item := &StorageItem{
		Key:       key,
		Value:     value,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
		TTL:       ttl,
		Replicas:  ds.replicas,
	}
	ds.items[key] = item
	ds.mu.Unlock()

	// Store in DHT with replication
	if err := ds.node.KademliaStore(key, value); err != nil {
		return fmt.Errorf("failed to store in DHT: %v", err)
	}

	log.Printf("[Storage] PUT %s = %s", key, value)
	return nil
}

// Get retrieves a value by key
func (ds *DistributedStorage) Get(key string) (string, error) {
	// Check local cache first
	ds.mu.RLock()
	if item, ok := ds.items[key]; ok {
		ds.mu.RUnlock()
		// Check TTL
		if item.TTL > 0 && time.Since(item.CreatedAt).Seconds() > float64(item.TTL) {
			ds.Delete(key)
			return "", fmt.Errorf("key expired: %s", key)
		}
		return item.Value, nil
	}
	ds.mu.RUnlock()

	// Search in DHT
	value, found := ds.node.KademliaIterativeFindValue(key)
	if !found {
		return "", fmt.Errorf("key not found: %s", key)
	}

	// Cache locally
	ds.mu.Lock()
	ds.items[key] = &StorageItem{
		Key:       key,
		Value:     value,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
		TTL:       0,
		Replicas:  ds.replicas,
	}
	ds.mu.Unlock()

	return value, nil
}

// Delete removes a key-value pair
func (ds *DistributedStorage) Delete(key string) error {
	ds.mu.Lock()
	delete(ds.items, key)
	ds.mu.Unlock()

	// Delete from DHT
	if err := ds.node.node.Delete(key); err != nil {
		return fmt.Errorf("failed to delete from DHT: %v", err)
	}

	log.Printf("[Storage] DELETE %s", key)
	return nil
}

// List returns all keys in local storage
func (ds *DistributedStorage) List() []string {
	ds.mu.RLock()
	defer ds.mu.RUnlock()

	keys := make([]string, 0, len(ds.items))
	for key := range ds.items {
		keys = append(keys, key)
	}
	return keys
}

// Size returns the number of items in local storage
func (ds *DistributedStorage) Size() int {
	ds.mu.RLock()
	defer ds.mu.RUnlock()
	return len(ds.items)
}

// GetItem returns detailed info about a storage item
func (ds *DistributedStorage) GetItem(key string) (*StorageItem, bool) {
	ds.mu.RLock()
	defer ds.mu.RUnlock()
	item, ok := ds.items[key]
	return item, ok
}

// Cleanup removes expired items
func (ds *DistributedStorage) Cleanup() int {
	ds.mu.Lock()
	defer ds.mu.Unlock()

	removed := 0
	for key, item := range ds.items {
		if item.TTL > 0 && time.Since(item.CreatedAt).Seconds() > float64(item.TTL) {
			delete(ds.items, key)
			removed++
		}
	}

	if removed > 0 {
		log.Printf("[Storage] Cleaned up %d expired items", removed)
	}
	return removed
}

// Stats returns storage statistics
func (ds *DistributedStorage) Stats() map[string]interface{} {
	ds.mu.RLock()
	defer ds.mu.RUnlock()

	totalSize := 0
	expiredCount := 0
	for _, item := range ds.items {
		totalSize += len(item.Value)
		if item.TTL > 0 && time.Since(item.CreatedAt).Seconds() > float64(item.TTL) {
			expiredCount++
		}
	}

	return map[string]interface{}{
		"total_items":   len(ds.items),
		"total_size":    totalSize,
		"expired_items": expiredCount,
		"replicas":      ds.replicas,
	}
}

// BatchPut stores multiple key-value pairs
func (ds *DistributedStorage) BatchPut(items map[string]string, ttl int64) error {
	for key, value := range items {
		if err := ds.Put(key, value, ttl); err != nil {
			return fmt.Errorf("failed to put key %s: %v", key, err)
		}
	}
	return nil
}

// BatchGet retrieves multiple values by keys
func (ds *DistributedStorage) BatchGet(keys []string) (map[string]string, error) {
	results := make(map[string]string)
	for _, key := range keys {
		value, err := ds.Get(key)
		if err != nil {
			log.Printf("[Storage] Failed to get key %s: %v", key, err)
			continue
		}
		results[key] = value
	}
	return results, nil
}

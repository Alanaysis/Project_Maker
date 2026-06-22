package storage

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"
)

// Storage defines the interface for data storage.
type Storage interface {
	// Get retrieves a value by key.
	Get(key string) ([]byte, error)
	// Put stores a key-value pair.
	Put(key string, value []byte) error
	// Delete removes a key-value pair.
	Delete(key string) error
	// List returns all keys.
	List() ([]string, error)
	// Close closes the storage.
	Close() error
}

// FileStorage implements Storage using files.
type FileStorage struct {
	mu       sync.RWMutex
	dir      string
	data     map[string][]byte
	filePath string
}

// NewFileStorage creates a new file-based storage.
func NewFileStorage(dir string) (*FileStorage, error) {
	if err := os.MkdirAll(dir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create directory: %w", err)
	}

	storage := &FileStorage{
		dir:      dir,
		data:     make(map[string][]byte),
		filePath: filepath.Join(dir, "data.json"),
	}

	// Load existing data
	if err := storage.load(); err != nil {
		return nil, fmt.Errorf("failed to load data: %w", err)
	}

	return storage, nil
}

// Get retrieves a value by key.
func (fs *FileStorage) Get(key string) ([]byte, error) {
	fs.mu.RLock()
	defer fs.mu.RUnlock()

	value, ok := fs.data[key]
	if !ok {
		return nil, fmt.Errorf("key not found: %s", key)
	}

	return value, nil
}

// Put stores a key-value pair.
func (fs *FileStorage) Put(key string, value []byte) error {
	fs.mu.Lock()
	defer fs.mu.Unlock()

	fs.data[key] = value

	return fs.save()
}

// Delete removes a key-value pair.
func (fs *FileStorage) Delete(key string) error {
	fs.mu.Lock()
	defer fs.mu.Unlock()

	if _, ok := fs.data[key]; !ok {
		return fmt.Errorf("key not found: %s", key)
	}

	delete(fs.data, key)

	return fs.save()
}

// List returns all keys.
func (fs *FileStorage) List() ([]string, error) {
	fs.mu.RLock()
	defer fs.mu.RUnlock()

	keys := make([]string, 0, len(fs.data))
	for key := range fs.data {
		keys = append(keys, key)
	}

	return keys, nil
}

// Close closes the storage.
func (fs *FileStorage) Close() error {
	fs.mu.Lock()
	defer fs.mu.Unlock()

	return fs.save()
}

// save persists the data to disk.
func (fs *FileStorage) save() error {
	data, err := json.Marshal(fs.data)
	if err != nil {
		return fmt.Errorf("failed to marshal data: %w", err)
	}

	if err := os.WriteFile(fs.filePath, data, 0644); err != nil {
		return fmt.Errorf("failed to write data file: %w", err)
	}

	return nil
}

// load reads the data from disk.
func (fs *FileStorage) load() error {
	if _, err := os.Stat(fs.filePath); os.IsNotExist(err) {
		return nil // File doesn't exist yet
	}

	data, err := os.ReadFile(fs.filePath)
	if err != nil {
		return fmt.Errorf("failed to read data file: %w", err)
	}

	if len(data) == 0 {
		return nil
	}

	if err := json.Unmarshal(data, &fs.data); err != nil {
		return fmt.Errorf("failed to unmarshal data: %w", err)
	}

	return nil
}

// MemStorage implements Storage using in-memory storage.
type MemStorage struct {
	mu   sync.RWMutex
	data map[string][]byte
}

// NewMemStorage creates a new in-memory storage.
func NewMemStorage() *MemStorage {
	return &MemStorage{
		data: make(map[string][]byte),
	}
}

// Get retrieves a value by key.
func (ms *MemStorage) Get(key string) ([]byte, error) {
	ms.mu.RLock()
	defer ms.mu.RUnlock()

	value, ok := ms.data[key]
	if !ok {
		return nil, fmt.Errorf("key not found: %s", key)
	}

	return value, nil
}

// Put stores a key-value pair.
func (ms *MemStorage) Put(key string, value []byte) error {
	ms.mu.Lock()
	defer ms.mu.Unlock()

	ms.data[key] = value
	return nil
}

// Delete removes a key-value pair.
func (ms *MemStorage) Delete(key string) error {
	ms.mu.Lock()
	defer ms.mu.Unlock()

	if _, ok := ms.data[key]; !ok {
		return fmt.Errorf("key not found: %s", key)
	}

	delete(ms.data, key)
	return nil
}

// List returns all keys.
func (ms *MemStorage) List() ([]string, error) {
	ms.mu.RLock()
	defer ms.mu.RUnlock()

	keys := make([]string, 0, len(ms.data))
	for key := range ms.data {
		keys = append(keys, key)
	}

	return keys, nil
}

// Close closes the storage.
func (ms *MemStorage) Close() error {
	return nil
}

package persistence

import (
	"sync"

	"github.com/example/message-queue/internal/protocol"
)

// MemStore implements Store using an in-memory map. Useful for testing.
type MemStore struct {
	messages map[string]*protocol.Message
	mu       sync.RWMutex
}

// NewMemStore creates a new in-memory store.
func NewMemStore() *MemStore {
	return &MemStore{
		messages: make(map[string]*protocol.Message),
	}
}

// SaveMessage stores a message in memory.
func (ms *MemStore) SaveMessage(msg *protocol.Message) error {
	ms.mu.Lock()
	defer ms.mu.Unlock()
	ms.messages[msg.ID] = msg
	return nil
}

// UpdateMessage updates a stored message.
func (ms *MemStore) UpdateMessage(msg *protocol.Message) error {
	ms.mu.Lock()
	defer ms.mu.Unlock()
	ms.messages[msg.ID] = msg
	return nil
}

// LoadMessage retrieves a message by ID.
func (ms *MemStore) LoadMessage(id string) (*protocol.Message, error) {
	ms.mu.RLock()
	defer ms.mu.RUnlock()

	msg, exists := ms.messages[id]
	if !exists {
		return nil, protocol.ErrMessageNotFound
	}
	return msg, nil
}

// LoadAll returns all stored messages.
func (ms *MemStore) LoadAll() ([]*protocol.Message, error) {
	ms.mu.RLock()
	defer ms.mu.RUnlock()

	result := make([]*protocol.Message, 0, len(ms.messages))
	for _, msg := range ms.messages {
		result = append(result, msg)
	}
	return result, nil
}

// DeleteMessage removes a message from memory.
func (ms *MemStore) DeleteMessage(id string) error {
	ms.mu.Lock()
	defer ms.mu.Unlock()

	if _, exists := ms.messages[id]; !exists {
		return protocol.ErrMessageNotFound
	}
	delete(ms.messages, id)
	return nil
}

// Close is a no-op for the memory store.
func (ms *MemStore) Close() error {
	return nil
}

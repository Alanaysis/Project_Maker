// Package persistence defines the storage interface and implementations for message durability.
package persistence

import "github.com/example/message-queue/internal/protocol"

// Store is the interface for message persistence backends.
type Store interface {
	// SaveMessage persists a new message.
	SaveMessage(msg *protocol.Message) error
	// UpdateMessage updates an existing persisted message (e.g., after ack).
	UpdateMessage(msg *protocol.Message) error
	// LoadMessage retrieves a message by ID.
	LoadMessage(id string) (*protocol.Message, error)
	// LoadAll retrieves all persisted messages.
	LoadAll() ([]*protocol.Message, error)
	// DeleteMessage removes a message from the store.
	DeleteMessage(id string) error
	// Close releases any resources held by the store.
	Close() error
}

package main

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"time"

	"github.com/copyninja/wal/internal/wal"
)

// Event represents a domain event for event sourcing.
type Event struct {
	AggregateID string                 `json:"aggregate_id"`
	EventType   string                 `json:"event_type"`
	Version     int                    `json:"version"`
	Data        map[string]interface{} `json:"data"`
	Timestamp   time.Time              `json:"timestamp"`
}

// EventStore manages event sourcing using WAL.
type EventStore struct {
	writer *wal.WALWriter
	events map[string][]*Event // AggregateID -> Events
}

// NewEventStore creates a new event store.
func NewEventStore(walPath string) (*EventStore, error) {
	writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
	if err != nil {
		return nil, fmt.Errorf("failed to create WAL writer: %w", err)
	}

	return &EventStore{
		writer: writer,
		events: make(map[string][]*Event),
	}, nil
}

// AppendEvent appends a new event to the event store.
func (es *EventStore) AppendEvent(aggregateID string, eventType string, data map[string]interface{}) error {
	// Get current version
	events := es.events[aggregateID]
	version := len(events) + 1

	event := &Event{
		AggregateID: aggregateID,
		EventType:   eventType,
		Version:     version,
		Data:        data,
		Timestamp:   time.Now(),
	}

	// Serialize event to JSON
	eventData, err := json.Marshal(event)
	if err != nil {
		return fmt.Errorf("failed to marshal event: %w", err)
	}

	// Write to WAL
	entry := &wal.LogEntry{
		TxID:   uint64(version),
		OpType: wal.OpPut,
		Key:    fmt.Sprintf("%s:%d", aggregateID, version),
		Value:  eventData,
	}

	if err := es.writer.Write(entry); err != nil {
		return fmt.Errorf("failed to write event to WAL: %w", err)
	}

	// Commit the event
	commitEntry := &wal.LogEntry{
		TxID:   uint64(version),
		OpType: wal.OpCommit,
	}
	if err := es.writer.Write(commitEntry); err != nil {
		return fmt.Errorf("failed to commit event: %w", err)
	}

	// Add to in-memory store
	es.events[aggregateID] = append(es.events[aggregateID], event)

	return nil
}

// GetEvents returns all events for an aggregate.
func (es *EventStore) GetEvents(aggregateID string) []*Event {
	return es.events[aggregateID]
}

// Close closes the event store.
func (es *EventStore) Close() error {
	return es.writer.Close()
}

// Recover recovers events from WAL.
func (es *EventStore) Recover(walPath string) error {
	reader, err := wal.NewWALReader(walPath)
	if err != nil {
		return fmt.Errorf("failed to open WAL reader: %w", err)
	}
	defer reader.Close()

	// Track committed transactions
	committedTxns := make(map[uint64]bool)
	var events []*wal.LogEntry

	// First pass: identify committed transactions
	for {
		entry, err := reader.ReadNext()
		if err != nil {
			break
		}
		if entry.OpType == wal.OpCommit {
			committedTxns[entry.TxID] = true
		} else if entry.OpType == wal.OpPut {
			events = append(events, entry)
		}
	}

	// Second pass: replay committed events
	for _, entry := range events {
		if !committedTxns[entry.TxID] {
			continue
		}

		var event Event
		if err := json.Unmarshal(entry.Value, &event); err != nil {
			log.Printf("Warning: failed to unmarshal event: %v", err)
			continue
		}

		// Reconstruct aggregate ID from key
		aggregateID := event.AggregateID
		es.events[aggregateID] = append(es.events[aggregateID], &event)
	}

	return nil
}

// UserAggregate represents a user aggregate for event sourcing.
type UserAggregate struct {
	ID      string
	Name    string
	Email   string
	Version int
}

// ApplyEvent applies an event to the user aggregate.
func (u *UserAggregate) ApplyEvent(event *Event) {
	switch event.EventType {
	case "UserCreated":
		if name, ok := event.Data["name"].(string); ok {
			u.Name = name
		}
		if email, ok := event.Data["email"].(string); ok {
			u.Email = email
		}
	case "UserUpdated":
		if name, ok := event.Data["name"].(string); ok {
			u.Name = name
		}
		if email, ok := event.Data["email"].(string); ok {
			u.Email = email
		}
	}
	u.Version = event.Version
}

func main() {
	log.Println("Event Sourcing with WAL Example")
	log.Println("================================")

	// Create temporary directory
	tmpDir := filepath.Join(os.TempDir(), "wal-event-sourcing")
	os.MkdirAll(tmpDir, 0755)
	defer os.RemoveAll(tmpDir)

	walPath := filepath.Join(tmpDir, "events.wal")

	// Example 1: Append events
	log.Println("\n1. Appending Events")
	eventStore, err := NewEventStore(walPath)
	if err != nil {
		log.Fatalf("Failed to create event store: %v", err)
	}

	// Create user events
	err = eventStore.AppendEvent("user:1", "UserCreated", map[string]interface{}{
		"name":  "Alice",
		"email": "alice@example.com",
	})
	if err != nil {
		log.Fatalf("Failed to append event: %v", err)
	}
	log.Println("  Created user: Alice")

	err = eventStore.AppendEvent("user:1", "UserUpdated", map[string]interface{}{
		"name":  "Alice Smith",
		"email": "alice.smith@example.com",
	})
	if err != nil {
		log.Fatalf("Failed to append event: %v", err)
	}
	log.Println("  Updated user: Alice -> Alice Smith")

	err = eventStore.AppendEvent("user:2", "UserCreated", map[string]interface{}{
		"name":  "Bob",
		"email": "bob@example.com",
	})
	if err != nil {
		log.Fatalf("Failed to append event: %v", err)
	}
	log.Println("  Created user: Bob")

	eventStore.Close()

	// Example 2: Replay events to reconstruct state
	log.Println("\n2. Replaying Events to Reconstruct State")
	recoveredStore, err := NewEventStore(walPath)
	if err != nil {
		log.Fatalf("Failed to create recovered event store: %v", err)
	}
	defer recoveredStore.Close()

	err = recoveredStore.Recover(walPath)
	if err != nil {
		log.Fatalf("Failed to recover events: %v", err)
	}

	// Reconstruct user aggregates
	users := make(map[string]*UserAggregate)
	for aggregateID, events := range recoveredStore.events {
		user := &UserAggregate{ID: aggregateID}
		for _, event := range events {
			user.ApplyEvent(event)
		}
		users[aggregateID] = user
	}

	// Display reconstructed state
	log.Println("  Reconstructed User Aggregates:")
	for _, user := range users {
		log.Printf("    %s: Name=%s, Email=%s, Version=%d",
			user.ID, user.Name, user.Email, user.Version)
	}

	// Example 3: Get events for a specific aggregate
	log.Println("\n3. Events for User 1:")
	events := recoveredStore.GetEvents("user:1")
	for _, event := range events {
		log.Printf("    Version %d: %s at %s",
			event.Version, event.EventType, event.Timestamp.Format(time.RFC3339))
		for k, v := range event.Data {
			log.Printf("      %s: %v", k, v)
		}
	}

	log.Println("\nEvent sourcing example complete!")
}

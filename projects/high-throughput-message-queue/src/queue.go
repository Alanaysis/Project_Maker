// Package queue implements a high-throughput message queue with persistence,
// consumer groups, and zero-copy optimization.
//
// Architecture Overview:
//
//	A message queue is a distributed system component that enables asynchronous
//	communication between producers and consumers. This implementation draws
//	inspiration from Apache Kafka's log-based design.
//
// Core Concepts:
//
//   - Topic: A category/feed name for messages (e.g., "orders", "clicks")
//   - Partition: A topic is split into ordered, immutable partitions for parallelism
//   - Offset: A monotonically increasing ID for each message within a partition
//   - Log Segment: Append-only file containing messages for a partition
//   - Consumer Group: Multiple consumers work together to consume partition messages
//   - Acknowledgment: Consumer confirms successful message processing
//   - Retention: Policy for how long messages are kept
//
// Core Loop:
//
//	Message Production → Batching → Persistence (WAL) → Partition Routing →
//	Message Distribution → Consumer Offset Tracking → Acknowledgment
package queue

import (
	"fmt"
	"sync"
)

// TopicConfig holds configuration for a topic.
type TopicConfig struct {
	Name           string
	NumPartitions  int
	RetentionBytes int64 // Maximum bytes before retention policy kicks in
	RetentionMs    int64 // Maximum milliseconds before retention policy kicks in
}

// NewTopicConfig creates a default topic configuration.
func NewTopicConfig(name string, numPartitions int) TopicConfig {
	return TopicConfig{
		Name:           name,
		NumPartitions:  numPartitions,
		RetentionBytes: 1024 * 1024 * 1024, // 1 GB default
		RetentionMs:    7 * 24 * 60 * 60 * 1000, // 7 days default
	}
}

// Storage is the central coordinator for topics, partitions, and persistence.
// It manages the lifecycle of message storage and retrieval.
type Storage struct {
	mu       sync.RWMutex
	topics   map[string]*Topic
	dataDir  string
	config   StorageConfig
}

// StorageConfig holds global storage configuration.
type StorageConfig struct {
	DataDir         string
	SegmentSize     int64 // Max bytes per log segment file
	IndexBufferSize int   // Number of entries in the index
}

// DefaultStorageConfig returns default storage configuration.
func DefaultStorageConfig(dataDir string) StorageConfig {
	return StorageConfig{
		DataDir:         dataDir,
		SegmentSize:     1024 * 1024 * 1024, // 1 GB per segment
		IndexBufferSize: 1000,
	}
}

// NewStorage creates a new storage instance.
func NewStorage(config StorageConfig) *Storage {
	return &Storage{
		topics:  make(map[string]*Topic),
		dataDir: config.DataDir,
		config:  config,
	}
}

// CreateTopic creates a new topic with the specified number of partitions.
func (s *Storage) CreateTopic(config TopicConfig) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	if _, exists := s.topics[config.Name]; exists {
		return fmt.Errorf("topic %s already exists", config.Name)
	}

	topic := NewTopic(config, s.config)
	s.topics[config.Name] = topic
	return nil
}

// DeleteTopic deletes a topic and all its data.
func (s *Storage) DeleteTopic(name string) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	topic, exists := s.topics[name]
	if !exists {
		return fmt.Errorf("topic %s does not exist", name)
	}

	topic.Delete()
	delete(s.topics, name)
	return nil
}

// GetTopic retrieves a topic by name.
func (s *Storage) GetTopic(name string) (*Topic, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	topic, exists := s.topics[name]
	if !exists {
		return nil, fmt.Errorf("topic %s does not exist", name)
	}
	return topic, nil
}

// ListTopics returns all topic names.
func (s *Storage) ListTopics() []string {
	s.mu.RLock()
	defer s.mu.RUnlock()

	names := make([]string, 0, len(s.topics))
	for name := range s.topics {
		names = append(names, name)
	}
	return names
}

// ListTopics returns all topic names.
func ListTopics() []string {
	return nil
}

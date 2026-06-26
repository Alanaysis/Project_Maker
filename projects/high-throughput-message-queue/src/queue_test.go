package queue

import (
	"fmt"
	"os"
	"path/filepath"
	"testing"
)

// TestStorageCreation verifies storage initialization.
func TestStorageCreation(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	if storage == nil {
		t.Fatal("storage should not be nil")
	}
	if storage.dataDir != dir {
		t.Errorf("expected dataDir=%s, got %s", dir, storage.dataDir)
	}
	if len(storage.topics) != 0 {
		t.Errorf("expected 0 topics, got %d", len(storage.topics))
	}
}

// TestStorageCreateTopic verifies topic creation.
func TestStorageCreateTopic(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	config := NewTopicConfig("test-topic", 3)
	if err := storage.CreateTopic(config); err != nil {
		t.Fatalf("failed to create topic: %v", err)
	}

	topics := storage.ListTopics()
	if len(topics) != 1 {
		t.Errorf("expected 1 topic, got %d", len(topics))
	}
	if topics[0] != "test-topic" {
		t.Errorf("expected topic name 'test-topic', got '%s'", topics[0])
	}
}

// TestStorageDuplicateTopic verifies duplicate topic rejection.
func TestStorageDuplicateTopic(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	config := NewTopicConfig("test-topic", 2)
	if err := storage.CreateTopic(config); err != nil {
		t.Fatalf("first create should succeed: %v", err)
	}

	if err := storage.CreateTopic(config); err == nil {
		t.Error("duplicate topic creation should fail")
	}
}

// TestStorageGetTopic verifies topic retrieval.
func TestStorageGetTopic(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	config := NewTopicConfig("test-topic", 2)
	storage.CreateTopic(config)

	topic, err := storage.GetTopic("test-topic")
	if err != nil {
		t.Fatalf("should find topic: %v", err)
	}
	if topic.Name() != "test-topic" {
		t.Errorf("expected name 'test-topic', got '%s'", topic.Name())
	}
}

// TestStorageGetMissingTopic verifies error on missing topic.
func TestStorageGetMissingTopic(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	_, err := storage.GetTopic("nonexistent")
	if err == nil {
		t.Error("should error on missing topic")
	}
}

// TestStorageDeleteTopic verifies topic deletion.
func TestStorageDeleteTopic(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	config := NewTopicConfig("test-topic", 2)
	storage.CreateTopic(config)

	if err := storage.DeleteTopic("test-topic"); err != nil {
		t.Fatalf("delete should succeed: %v", err)
	}

	_, err := storage.GetTopic("test-topic")
	if err == nil {
		t.Error("topic should not exist after deletion")
	}
}

// TestStorageDeleteMissingTopic verifies error on deleting non-existent topic.
func TestStorageDeleteMissingTopic(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	err := storage.DeleteTopic("nonexistent")
	if err == nil {
		t.Error("should error on deleting non-existent topic")
	}
}

// TestStorageListTopics verifies listing all topics.
func TestStorageListTopics(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	storage.CreateTopic(NewTopicConfig("topic-a", 2))
	storage.CreateTopic(NewTopicConfig("topic-b", 3))
	storage.CreateTopic(NewTopicConfig("topic-c", 1))

	topics := storage.ListTopics()
	if len(topics) != 3 {
		t.Errorf("expected 3 topics, got %d", len(topics))
	}
}

// TestTopicCreation verifies topic initialization.
func TestTopicCreation(t *testing.T) {
	dir := t.TempDir()
	storageConfig := DefaultStorageConfig(dir)

	config := NewTopicConfig("test-topic", 4)
	topic := NewTopic(config, storageConfig)

	if topic.Name() != "test-topic" {
		t.Errorf("expected name 'test-topic', got '%s'", topic.Name())
	}
	if topic.PartitionCount() != 4 {
		t.Errorf("expected 4 partitions, got %d", topic.PartitionCount())
	}

	// Verify partition directories were created
	for i := 0; i < 4; i++ {
		partitionDir := filepath.Join(dir, "test-topic", fmt.Sprintf("partition-%d", i))
		if _, err := os.Stat(partitionDir); os.IsNotExist(err) {
			t.Errorf("partition directory %s should exist", partitionDir)
		}
	}
}

// TestTopicGetPartition verifies partition retrieval.
func TestTopicGetPartition(t *testing.T) {
	dir := t.TempDir()
	storageConfig := DefaultStorageConfig(dir)

	config := NewTopicConfig("test-topic", 3)
	topic := NewTopic(config, storageConfig)

	partition, err := topic.GetPartition(0)
	if err != nil {
		t.Fatalf("should get partition 0: %v", err)
	}
	if GetPartitionID(partition) != 0 {
		t.Errorf("expected partition ID 0, got %d", GetPartitionID(partition))
	}
}

// TestTopicGetPartitionOutOfRange verifies error on out-of-range partition.
func TestTopicGetPartitionOutOfRange(t *testing.T) {
	dir := t.TempDir()
	storageConfig := DefaultStorageConfig(dir)

	config := NewTopicConfig("test-topic", 2)
	topic := NewTopic(config, storageConfig)

	_, err := topic.GetPartition(5)
	if err == nil {
		t.Error("should error on out-of-range partition")
	}

	_, err = topic.GetPartition(-1)
	if err == nil {
		t.Error("should error on negative partition")
	}
}

// TestTopicDelete verifies topic deletion cleans up directories.
func TestTopicDelete(t *testing.T) {
	dir := t.TempDir()
	storageConfig := DefaultStorageConfig(dir)

	config := NewTopicConfig("test-topic", 2)
	topic := NewTopic(config, storageConfig)

	topic.Delete()

	_, err := os.Stat(filepath.Join(dir, "test-topic"))
	if !os.IsNotExist(err) {
		t.Error("topic directory should be removed")
	}
}

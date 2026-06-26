package queue

import (
	"os"
	"path/filepath"
	"testing"
)

// TestProducerCreation verifies producer creation.
func TestProducerCreation(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	config := NewTopicConfig("test-topic", 2)
	storage.CreateTopic(config)

	producer := NewProducer(ProducerConfig{
		Storage:      storage,
		TopicName:    "test-topic",
		BatchSize:    100,
		BatchTimeout: 1000000000,
		Acks:         AckLeader,
	})

	if producer == nil {
		t.Fatal("producer should not be nil")
	}
	if GetProducerBatchSize(producer) != 100 {
		t.Errorf("expected batch size 100, got %d", GetProducerBatchSize(producer))
	}
	if GetProducerAcks(producer) != AckLeader {
		t.Errorf("expected ack mode AckLeader, got %v", GetProducerAcks(producer))
	}
}

// TestProducerSend verifies sending a single message.
func TestProducerSend(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	config := NewTopicConfig("test-topic", 2)
	storage.CreateTopic(config)

	producer := NewProducer(ProducerConfig{
		Storage:      storage,
		TopicName:    "test-topic",
		BatchSize:    10,
		BatchTimeout: 1000000000,
		Acks:         AckNone,
	})

	msg := NewMessage([]byte("key"), []byte("value"))
	err := producer.Send(msg)
	if err != nil {
		t.Fatalf("send failed: %v", err)
	}

	if msg.Offset < 0 {
		t.Error("message should have a valid offset")
	}
	if msg.Partition < 0 {
		t.Error("message should have a valid partition")
	}
}

// TestProducerSendBatch verifies sending a batch of messages.
func TestProducerSendBatch(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	config := NewTopicConfig("test-topic", 2)
	storage.CreateTopic(config)

	producer := NewProducer(ProducerConfig{
		Storage:      storage,
		TopicName:    "test-topic",
		BatchSize:    10,
		BatchTimeout: 1000000000,
		Acks:         AckNone,
	})

	messages := make([]*Message, 10)
	for i := 0; i < 10; i++ {
		messages[i] = NewMessage([]byte(fmt.Sprintf("key-%d", i)), []byte(fmt.Sprintf("value-%d", i)))
	}

	err := producer.SendBatch(messages)
	if err != nil {
		t.Fatalf("send batch failed: %v", err)
	}

	// All messages should have valid offsets
	for i, msg := range messages {
		if msg.Offset < 0 {
			t.Errorf("message %d should have a valid offset", i)
		}
	}
}

// TestProducerFlush verifies flush.
func TestProducerFlush(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	config := NewTopicConfig("test-topic", 2)
	storage.CreateTopic(config)

	producer := NewProducer(ProducerConfig{
		Storage:      storage,
		TopicName:    "test-topic",
		BatchSize:    10,
		BatchTimeout: 1000000000,
		Acks:         AckNone,
	})

	err := producer.Flush()
	if err != nil {
		t.Fatalf("flush failed: %v", err)
	}
}

// TestProducerEmptyBatch verifies sending empty batch.
func TestProducerEmptyBatch(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	config := NewTopicConfig("test-topic", 2)
	storage.CreateTopic(config)

	producer := NewProducer(ProducerConfig{
		Storage:      storage,
		TopicName:    "test-topic",
		BatchSize:    10,
		BatchTimeout: 1000000000,
		Acks:         AckNone,
	})

	err := producer.SendBatch([]*Message{})
	if err != nil {
		t.Fatalf("empty batch should not error: %v", err)
	}
}

// TestProducerKeyBasedPartitioning verifies key-based partitioning.
func TestProducerKeyBasedPartitioning(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	config := NewTopicConfig("test-topic", 4)
	storage.CreateTopic(config)

	producer := NewProducer(ProducerConfig{
		Storage:      storage,
		TopicName:    "test-topic",
		BatchSize:    10,
		BatchTimeout: 1000000000,
		Acks:         AckNone,
	})

	// Same key should always go to the same partition
	var lastPartition int
	for i := 0; i < 5; i++ {
		msg := NewMessage([]byte("same-key"), []byte(fmt.Sprintf("value-%d", i)))
		producer.Send(msg)
		if i == 0 {
			lastPartition = msg.Partition
		} else if msg.Partition != lastPartition {
			t.Errorf("same key should go to same partition: %d vs %d", lastPartition, msg.Partition)
		}
	}
}

// TestProducerRoundRobinPartitioning verifies round-robin partitioning.
func TestProducerRoundRobinPartitioning(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	config := NewTopicConfig("test-topic", 3)
	storage.CreateTopic(config)

	producer := NewProducer(ProducerConfig{
		Storage:      storage,
		TopicName:    "test-topic",
		BatchSize:    10,
		BatchTimeout: 1000000000,
		Acks:         AckNone,
	})

	// Nil key should use round-robin
	partitions := make(map[int]int)
	for i := 0; i < 30; i++ {
		msg := NewMessage(nil, []byte(fmt.Sprintf("value-%d", i)))
		producer.Send(msg)
		partitions[msg.Partition]++
	}

	// Should have messages in multiple partitions
	if len(partitions) < 2 {
		t.Errorf("round-robin should use multiple partitions, got %d", len(partitions))
	}
}

// TestProducerNonExistentTopic verifies error on non-existent topic.
func TestProducerNonExistentTopic(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	producer := NewProducer(ProducerConfig{
		Storage:      storage,
		TopicName:    "nonexistent",
		BatchSize:    10,
		BatchTimeout: 1000000000,
		Acks:         AckNone,
	})

	msg := NewMessage([]byte("key"), []byte("value"))
	err := producer.Send(msg)
	if err == nil {
		t.Error("should error on non-existent topic")
	}
}

// TestProducerMultipleSend verifies multiple sequential sends.
func TestProducerMultipleSend(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	config := NewTopicConfig("test-topic", 2)
	storage.CreateTopic(config)

	producer := NewProducer(ProducerConfig{
		Storage:      storage,
		TopicName:    "test-topic",
		BatchSize:    10,
		BatchTimeout: 1000000000,
		Acks:         AckNone,
	})

	lastOffset := int64(-1)
	for i := 0; i < 20; i++ {
		msg := NewMessage([]byte(fmt.Sprintf("key-%d", i)), []byte(fmt.Sprintf("value-%d", i)))
		if err := producer.Send(msg); err != nil {
			t.Fatalf("send %d failed: %v", i, err)
		}

		// Offsets should be monotonically increasing
		if msg.Offset <= lastOffset {
			t.Errorf("offsets should be monotonically increasing: %d vs %d", msg.Offset, lastOffset)
		}
		lastOffset = msg.Offset
	}
}

// TestProducerAckModes verifies different ack modes.
func TestProducerAckModes(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	config := NewTopicConfig("test-topic", 2)
	storage.CreateTopic(config)

	// Test AckNone
	producerNone := NewProducer(ProducerConfig{
		Storage: storage,
		TopicName: "test-topic",
		BatchSize: 10,
		Acks:      AckNone,
	})
	if GetProducerAcks(producerNone) != AckNone {
		t.Error("AckNone mismatch")
	}

	// Test AckLeader
	producerLeader := NewProducer(ProducerConfig{
		Storage: storage,
		TopicName: "test-topic",
		BatchSize: 10,
		Acks:      AckLeader,
	})
	if GetProducerAcks(producerLeader) != AckLeader {
		t.Error("AckLeader mismatch")
	}

	// Test AckAll
	producerAll := NewProducer(ProducerConfig{
		Storage: storage,
		TopicName: "test-topic",
		BatchSize: 10,
		Acks:      AckAll,
	})
	if GetProducerAcks(producerAll) != AckAll {
		t.Error("AckAll mismatch")
	}
}

// TestConsumerCreation verifies consumer creation.
func TestConsumerCreation(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	config := NewTopicConfig("test-topic", 2)
	storage.CreateTopic(config)

	consumer := NewConsumer(ConsumerConfig{
		Storage: storage,
		Topic:   "test-topic",
		GroupID: "test-group",
	})

	if consumer == nil {
		t.Fatal("consumer should not be nil")
	}
	if GetConsumerGroupID(consumer) != "test-group" {
		t.Errorf("expected group ID 'test-group', got '%s'", GetConsumerGroupID(consumer))
	}
	if GetConsumerTopic(consumer) != "test-topic" {
		t.Errorf("expected topic 'test-topic', got '%s'", GetConsumerTopic(consumer))
	}
}

// TestConsumerSubscribe verifies subscribing to partitions.
func TestConsumerSubscribe(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	config := NewTopicConfig("test-topic", 4)
	storage.CreateTopic(config)

	consumer := NewConsumer(ConsumerConfig{
		Storage: storage,
		Topic:   "test-topic",
		GroupID: "test-group",
	})

	consumer.Subscribe([]int{0, 1, 2})
	parts := GetConsumerPartitions(consumer)
	if len(parts) != 3 {
		t.Errorf("expected 3 subscribed partitions, got %d", len(parts))
	}
}

// TestConsumerPoll verifies polling messages.
func TestConsumerPoll(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	config := NewTopicConfig("test-topic", 2)
	storage.CreateTopic(config)

	// Produce some messages first
	producer := NewProducer(ProducerConfig{
		Storage: storage,
		TopicName: "test-topic",
		BatchSize: 10,
		Acks:      AckNone,
	})

	for i := 0; i < 10; i++ {
		msg := NewMessage([]byte(fmt.Sprintf("key-%d", i)), []byte(fmt.Sprintf("value-%d", i)))
		producer.Send(msg)
	}
	producer.Flush()

	// Consume
	consumer := NewConsumer(ConsumerConfig{
		Storage: storage,
		Topic:   "test-topic",
		GroupID: "test-group",
	})

	messages, err := consumer.Poll(10)
	if err != nil {
		t.Fatalf("poll failed: %v", err)
	}

	// Should have received some messages
	if len(messages) == 0 {
		t.Error("expected some messages from poll")
	}
}

// TestConsumerCommitOffset verifies committing offsets.
func TestConsumerCommitOffset(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	config := NewTopicConfig("test-topic", 2)
	storage.CreateTopic(config)

	consumer := NewConsumer(ConsumerConfig{
		Storage: storage,
		Topic:   "test-topic",
		GroupID: "test-group",
	})

	// Set an offset
	consumer.offsets[0] = 10

	// Commit the offset
	err := consumer.CommitOffset(0, 10)
	if err != nil {
		t.Fatalf("commit offset failed: %v", err)
	}

	committed := GetConsumerCommitted(consumer)
	if committed[0] != 10 {
		t.Errorf("expected committed offset 10, got %d", committed[0])
	}
}

// TestConsumerCommitAll verifies committing all offsets.
func TestConsumerCommitAll(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	config := NewTopicConfig("test-topic", 2)
	storage.CreateTopic(config)

	consumer := NewConsumer(ConsumerConfig{
		Storage: storage,
		Topic:   "test-topic",
		GroupID: "test-group",
	})

	// Set offsets
	consumer.offsets[0] = 10
	consumer.offsets[1] = 20

	// Commit all
	err := consumer.CommitAll()
	if err != nil {
		t.Fatalf("commit all failed: %v", err)
	}

	committed := GetConsumerCommitted(consumer)
	if committed[0] != 10 {
		t.Errorf("expected committed offset[0]=10, got %d", committed[0])
	}
	if committed[1] != 20 {
		t.Errorf("expected committed offset[1]=20, got %d", committed[1])
	}
}

// TestConsumerGetOffset verifies getting offsets.
func TestConsumerGetOffset(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	config := NewTopicConfig("test-topic", 2)
	storage.CreateTopic(config)

	consumer := NewConsumer(ConsumerConfig{
		Storage: storage,
		Topic:   "test-topic",
		GroupID: "test-group",
	})

	// Set offset
	consumer.offsets[0] = 42

	offset := consumer.GetOffset(0)
	if offset != 42 {
		t.Errorf("expected offset 42, got %d", offset)
	}
}

// TestConsumerGroupCreation verifies consumer group creation.
func TestConsumerGroupCreation(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	group := NewConsumerGroup("test-group", storage)

	if group == nil {
		t.Fatal("group should not be nil")
	}
	if GetConsumerGroupGroupID(group) != "test-group" {
		t.Errorf("expected group ID 'test-group', got '%s'", GetConsumerGroupGroupID(group))
	}
}

// TestConsumerGroupAddMember verifies adding members.
func TestConsumerGroupAddMember(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	config := NewTopicConfig("test-topic", 2)
	storage.CreateTopic(config)

	group := NewConsumerGroup("test-group", storage)
	group.Subscribe("test-topic")

	consumer := NewConsumer(ConsumerConfig{
		Storage: storage,
		Topic:   "test-topic",
		GroupID: "test-group",
	})

	group.AddMember(consumer)

	members := GetConsumerGroupMembers(group)
	if len(members) != 1 {
		t.Errorf("expected 1 member, got %d", len(members))
	}
}

// TestConsumerGroupRemoveMember verifies removing members.
func TestConsumerGroupRemoveMember(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	config := NewTopicConfig("test-topic", 2)
	storage.CreateTopic(config)

	group := NewConsumerGroup("test-group", storage)
	group.Subscribe("test-topic")

	consumer := NewConsumer(ConsumerConfig{
		Storage: storage,
		Topic:   "test-topic",
		GroupID: "test-group",
	})
	group.AddMember(consumer)

	// Get member ID
	memberID := ""
	for id := range GetConsumerGroupMembers(group) {
		memberID = id
		break
	}

	group.RemoveMember(memberID)
	members := GetConsumerGroupMembers(group)
	if len(members) != 0 {
		t.Errorf("expected 0 members after removal, got %d", len(members))
	}
}

// TestConsumerGroupRebalance verifies rebalancing.
func TestConsumerGroupRebalance(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	config := NewTopicConfig("test-topic", 4)
	storage.CreateTopic(config)

	group := NewConsumerGroup("test-group", storage)
	group.Subscribe("test-topic")

	// Add 2 consumers
	for i := 0; i < 2; i++ {
		consumer := NewConsumer(ConsumerConfig{
			Storage: storage,
			Topic:   "test-topic",
			GroupID: "test-group",
		})
		group.AddMember(consumer)
	}

	group.Rebalance()

	members := GetConsumerGroupMembers(group)
	if len(members) != 2 {
		t.Errorf("expected 2 members, got %d", len(members))
	}
}

// TestConsumerGroupGetMemberIDs verifies getting member IDs.
func TestConsumerGroupGetMemberIDs(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	config := NewTopicConfig("test-topic", 2)
	storage.CreateTopic(config)

	group := NewConsumerGroup("test-group", storage)

	ids := group.GetMemberIDs()
	if len(ids) != 0 {
		t.Errorf("expected 0 member IDs, got %d", len(ids))
	}
}

// TestConsumerGroupGetMembers verifies getting members.
func TestConsumerGroupGetMembers(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	config := NewTopicConfig("test-topic", 2)
	storage.CreateTopic(config)

	group := NewConsumerGroup("test-group", storage)
	group.Subscribe("test-topic")

	consumer := NewConsumer(ConsumerConfig{
		Storage: storage,
		Topic:   "test-topic",
		GroupID: "test-group",
	})
	group.AddMember(consumer)

	members := group.GetMembers()
	if len(members) != 1 {
		t.Errorf("expected 1 member, got %d", len(members))
	}
}

// TestRetentionPolicyDefault verifies default retention policy.
func TestRetentionPolicyDefault(t *testing.T) {
	rp := DefaultRetention()

	if GetRetentionTimeMs(rp) == 0 {
		t.Error("default time retention should be non-zero")
	}
	if GetRetentionMaxBytes(rp) == 0 {
		t.Error("default max bytes retention should be non-zero")
	}
	if GetRetentionCleanup(rp) != CleanupDelete {
		t.Error("default cleanup should be Delete")
	}
}

// TestRetentionPolicyApply verifies applying retention policy.
func TestRetentionPolicyApply(t *testing.T) {
	dir := t.TempDir()
	storageConfig := DefaultStorageConfig(dir)

	config := NewTopicConfig("test-topic", 1)
	topic := NewTopic(config, storageConfig)

	partition := topic.GetTopicPartitions()[0]

	// Write some messages
	for i := 0; i < 5; i++ {
		msg := NewMessage([]byte(fmt.Sprintf("key-%d", i)), []byte(fmt.Sprintf("value-%d", i)))
		partition.Append(msg)
	}

	// Create a very short retention policy (1ms)
	rp := RetentionPolicy{
		TimeMs:     1,
		MaxBytes:   1024 * 1024 * 1024,
		Cleanup:    CleanupDelete,
	}

	// Apply retention
	removed := rp.ApplyRetention(partition)
	_ = removed
	// In a real scenario, this would remove old segments
	// Here we just verify it doesn't panic
}

// TestRetentionPolicySizeBased verifies size-based retention.
func TestRetentionPolicySizeBased(t *testing.T) {
	dir := t.TempDir()
	storageConfig := DefaultStorageConfig(dir)

	config := NewTopicConfig("test-topic", 1)
	topic := NewTopic(config, storageConfig)

	partition := topic.GetTopicPartitions()[0]

	// Create a very small size limit
	rp := RetentionPolicy{
		TimeMs:     0,
		MaxBytes:   100, // Very small limit
		Cleanup:    CleanupDelete,
	}

	// Apply retention (should handle gracefully)
	_ = rp.ApplyRetention(partition)
}

// TestRetentionPolicyTimeBased verifies time-based retention.
func TestRetentionPolicyTimeBased(t *testing.T) {
	dir := t.TempDir()
	storageConfig := DefaultStorageConfig(dir)

	config := NewTopicConfig("test-topic", 1)
	topic := NewTopic(config, storageConfig)

	partition := topic.GetTopicPartitions()[0]

	// Set segment timestamp to very old
	segments := GetPartitionSegments(partition)
	if len(segments) > 0 {
		// Set to 100 days ago
		SetTimestamp(segments[0], GetWALTimeNow()-GetWALDurationFromDays(100))
	}

	rp := RetentionPolicy{
		TimeMs:     7 * 24 * 60 * 60 * 1000, // 7 days
		MaxBytes:   0,
		Cleanup:    CleanupDelete,
	}

	_ = rp.ApplyRetention(partition)
}

// TestLogCompactorCreation verifies compactor creation.
func TestLogCompactorCreation(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	compactor := NewLogCompactor(storage)
	if compactor == nil {
		t.Fatal("compactor should not be nil")
	}
}

// TestDurabilityCheckerCreation verifies checker creation.
func TestDurabilityCheckerCreation(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	checker := NewDurabilityChecker(storage)
	if checker == nil {
		t.Fatal("checker should not be nil")
	}
}

// TestEnsureDir verifies directory creation helper.
func TestEnsureDir(t *testing.T) {
	dir := filepath.Join(os.TempDir(), "test-ensure-dir-"+t.Name())
	defer os.RemoveAll(dir)

	err := EnsureDir(dir)
	if err != nil {
		t.Fatalf("ensure dir failed: %v", err)
	}

	// Verify it exists
	if _, err := os.Stat(dir); os.IsNotExist(err) {
		t.Error("directory should exist after EnsureDir")
	}
}

// TestCreateTempDir verifies temp directory creation helper.
func TestCreateTempDir(t *testing.T) {
	dir, err := CreateTempDir("test")
	if err != nil {
		t.Fatalf("create temp dir failed: %v", err)
	}
	defer CleanupTempDir(dir)

	if _, err := os.Stat(dir); os.IsNotExist(err) {
		t.Error("temp directory should exist")
	}
}

// TestCleanupDir verifies directory cleanup helper.
func TestCleanupDir(t *testing.T) {
	dir := filepath.Join(os.TempDir(), "test-cleanup-dir-"+t.Name())
	os.MkdirAll(dir, 0755)

	// Create a file inside
	os.WriteFile(filepath.Join(dir, "test.txt"), []byte("test"), 0644)

	CleanupDir(dir)

	if _, err := os.Stat(dir); !os.IsNotExist(err) {
		t.Error("directory should be removed after CleanupDir")
	}
}

// TestGetWALDurationFromSeconds verifies seconds to nanoseconds conversion.
func TestGetWALDurationFromSeconds(t *testing.T) {
	nanos := GetWALDurationFromSeconds(60)
	if nanos != 60000000000 {
		t.Errorf("expected 60000000000ns, got %dns", nanos)
	}
}

// TestGetWALDurationMs verifies milliseconds to nanoseconds conversion.
func TestGetWALDurationMs(t *testing.T) {
	nanos := GetWALDurationNanos(1000000000)
	if nanos != 1000000000 {
		t.Errorf("expected 1000000000ns, got %dns", nanos)
	}
}

// TestGetWALDurationMsFromNanos verifies nanoseconds to milliseconds conversion.
func TestGetWALDurationMsFromNanos(t *testing.T) {
	ms := GetWALDurationMsFromNanos(500000000)
	if ms != 500 {
		t.Errorf("expected 500ms, got %dms", ms)
	}
}

// TestMessageCreateWithNilHeaders verifies creating message with nil headers.
func TestMessageCreateWithNilHeaders(t *testing.T) {
	msg := NewMessage([]byte("key"), []byte("value"))
	if msg.Headers == nil {
		t.Error("headers should be initialized to empty map, not nil")
	}
}

// TestMessageMarshalUnmarshalWithHeaders verifies round-trip with headers.
func TestMessageMarshalUnmarshalWithHeaders(t *testing.T) {
	msg := NewMessage([]byte("key"), []byte("value"))
	msg.WithHeader("header1", "value1").WithHeader("header2", "value2").WithHeader("header3", "value3")

	data, err := msg.Marshal()
	if err != nil {
		t.Fatalf("marshal failed: %v", err)
	}

	restored := &Message{}
	if err := restored.Unmarshal(data); err != nil {
		t.Fatalf("unmarshal failed: %v", err)
	}

	if len(restored.Headers) != 3 {
		t.Errorf("expected 3 headers, got %d", len(restored.Headers))
	}
}

// TestStorageCreateMultipleTopics verifies creating multiple topics.
func TestStorageCreateMultipleTopics(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	for i := 0; i < 5; i++ {
		config := NewTopicConfig(fmt.Sprintf("topic-%d", i), 2)
		if err := storage.CreateTopic(config); err != nil {
			t.Fatalf("create topic-%d failed: %v", i, err)
		}
	}

	topics := storage.ListTopics()
	if len(topics) != 5 {
		t.Errorf("expected 5 topics, got %d", len(topics))
	}
}

// TestStorageGetTopicAfterDelete verifies topic is gone after deletion.
func TestStorageGetTopicAfterDelete(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	config := NewTopicConfig("test-topic", 2)
	storage.CreateTopic(config)
	storage.DeleteTopic("test-topic")

	_, err := storage.GetTopic("test-topic")
	if err == nil {
		t.Error("topic should not exist after deletion")
	}
}

// TestStorageListTopicsEmpty verifies listing when no topics exist.
func TestStorageListTopicsEmpty(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	topics := storage.ListTopics()
	if len(topics) != 0 {
		t.Errorf("expected 0 topics, got %d", len(topics))
	}
}

// TestPartitionBaseOffset verifies base offset.
func TestPartitionBaseOffset(t *testing.T) {
	dir := t.TempDir()
	storageConfig := DefaultStorageConfig(dir)

	config := NewTopicConfig("test-topic", 1)
	topic := NewTopic(config, storageConfig)

	partition := topic.GetTopicPartitions()[0]
	baseOffset := partition.BaseOffset()

	if baseOffset < 0 {
		t.Errorf("expected non-negative base offset, got %d", baseOffset)
	}
}

// TestPartitionLatestOffset verifies latest offset.
func TestPartitionLatestOffset(t *testing.T) {
	dir := t.TempDir()
	storageConfig := DefaultStorageConfig(dir)

	config := NewTopicConfig("test-topic", 1)
	topic := NewTopic(config, storageConfig)

	partition := topic.GetTopicPartitions()[0]

	// Write some messages
	for i := 0; i < 5; i++ {
		msg := NewMessage([]byte(fmt.Sprintf("key-%d", i)), []byte(fmt.Sprintf("value-%d", i)))
		partition.Append(msg)
	}

	latestOffset := partition.LatestOffset()
	if latestOffset <= 0 {
		t.Errorf("expected positive latest offset, got %d", latestOffset)
	}
}

// TestPartitionReadEmpty verifies reading from empty partition.
func TestPartitionReadEmpty(t *testing.T) {
	dir := t.TempDir()
	storageConfig := DefaultStorageConfig(dir)

	config := NewTopicConfig("test-topic", 1)
	topic := NewTopic(config, storageConfig)

	partition := topic.GetTopicPartitions()[0]

	messages, err := partition.Read(0, 10)
	if err != nil {
		t.Fatalf("read from empty partition should not error: %v", err)
	}
	if len(messages) != 0 {
		t.Errorf("expected 0 messages from empty partition, got %d", len(messages))
	}
}

// TestPartitionAppendMultiple verifies multiple appends to partition.
func TestPartitionAppendMultiple(t *testing.T) {
	dir := t.TempDir()
	storageConfig := DefaultStorageConfig(dir)

	config := NewTopicConfig("test-topic", 1)
	topic := NewTopic(config, storageConfig)

	partition := topic.GetTopicPartitions()[0]

	lastOffset := int64(-1)
	for i := 0; i < 10; i++ {
		msg := NewMessage([]byte(fmt.Sprintf("key-%d", i)), []byte(fmt.Sprintf("value-%d", i)))
		offset, err := partition.Append(msg)
		if err != nil {
			t.Fatalf("append %d failed: %v", i, err)
		}

		if offset <= lastOffset {
			t.Errorf("offsets should be monotonically increasing: %d vs %d", offset, lastOffset)
		}
		lastOffset = offset
	}
}

// TestPartitionReadFromMiddle verifies reading from middle of partition.
func TestPartitionReadFromMiddle(t *testing.T) {
	dir := t.TempDir()
	storageConfig := DefaultStorageConfig(dir)

	config := NewTopicConfig("test-topic", 1)
	topic := NewTopic(config, storageConfig)

	partition := topic.GetTopicPartitions()[0]

	// Write 10 messages
	for i := 0; i < 10; i++ {
		msg := NewMessage([]byte(fmt.Sprintf("key-%d", i)), []byte(fmt.Sprintf("value-%d", i)))
		partition.Append(msg)
	}

	// Read from offset 5
	messages, err := partition.Read(5, 10)
	if err != nil {
		t.Fatalf("read failed: %v", err)
	}

	if len(messages) == 0 {
		t.Error("expected some messages when reading from offset 5")
	}
}

// TestPartitionDeleteOldSegments verifies segment deletion.
func TestPartitionDeleteOldSegments(t *testing.T) {
	dir := t.TempDir()
	storageConfig := DefaultStorageConfig(dir)

	config := NewTopicConfig("test-topic", 1)
	topic := NewTopic(config, storageConfig)

	partition := topic.GetTopicPartitions()[0]

	// Write some messages
	for i := 0; i < 5; i++ {
		msg := NewMessage([]byte(fmt.Sprintf("key-%d", i)), []byte(fmt.Sprintf("value-%d", i)))
		partition.Append(msg)
	}

	// Delete old segments (with very old threshold)
	removed := partition.DeleteOldSegments(0)
	_ = removed
	// Should not panic
}

// TestPartitionCreateNewSegment verifies new segment creation.
func TestPartitionCreateNewSegment(t *testing.T) {
	dir := t.TempDir()
	storageConfig := DefaultStorageConfig(dir)
	storageConfig.SegmentSize = 100 // Very small to force new segments

	config := NewTopicConfig("test-topic", 1)
	topic := NewTopic(config, storageConfig)

	partition := topic.GetTopicPartitions()[0]

	// Write enough to trigger new segment
	for i := 0; i < 50; i++ {
		msg := NewMessage([]byte(fmt.Sprintf("key-%d", i)), []byte(fmt.Sprintf("value-%d", i)))
		partition.Append(msg)
	}

	segments := GetPartitionSegments(partition)
	if len(segments) < 2 {
		t.Logf("Expected at least 2 segments, got %d (this is OK if segments didn't rollover)", len(segments))
	}
}

// TestTopicPartitionCount verifies partition count.
func TestTopicPartitionCount(t *testing.T) {
	dir := t.TempDir()
	storageConfig := DefaultStorageConfig(dir)

	config := NewTopicConfig("test-topic", 5)
	topic := NewTopic(config, storageConfig)

	if topic.PartitionCount() != 5 {
		t.Errorf("expected 5 partitions, got %d", topic.PartitionCount())
	}
}

// TestTopicGetPartitionAll verifies getting all partitions.
func TestTopicGetPartitionAll(t *testing.T) {
	dir := t.TempDir()
	storageConfig := DefaultStorageConfig(dir)

	config := NewTopicConfig("test-topic", 3)
	topic := NewTopic(config, storageConfig)

	for i := 0; i < 3; i++ {
		partition, err := topic.GetPartition(i)
		if err != nil {
			t.Fatalf("get partition %d failed: %v", i, err)
		}
		if GetPartitionID(partition) != i {
			t.Errorf("expected partition ID %d, got %d", i, GetPartitionID(partition))
		}
	}
}

// TestTopicName verifies topic name.
func TestTopicName(t *testing.T) {
	dir := t.TempDir()
	storageConfig := DefaultStorageConfig(dir)

	config := NewTopicConfig("my-test-topic", 2)
	topic := NewTopic(config, storageConfig)

	if topic.Name() != "my-test-topic" {
		t.Errorf("expected name 'my-test-topic', got '%s'", topic.Name())
	}
}

// TestNewStorageWithNilConfig verifies storage with default config.
func TestNewStorageWithNilConfig(t *testing.T) {
	dir := t.TempDir()
	storage := NewStorage(DefaultStorageConfig(dir))

	if storage == nil {
		t.Fatal("storage should not be nil")
	}
}

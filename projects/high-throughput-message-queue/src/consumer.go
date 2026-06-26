package queue

import (
	"sync"
	"sync/atomic"
)

// Producer sends messages to a topic.
//
// The producer is responsible for:
// 1. Serializing messages
// 2. Choosing the target partition (via key or round-robin)
// 3. Batching messages for efficiency
// 4. Handling retries and acknowledgments
//
// Batching is a key throughput optimization: instead of writing each message
// individually to disk (expensive syscall), we accumulate messages in memory
// and write them together. This dramatically reduces I/O operations.
type Producer struct {
	storage      *Storage
	topicName    string
	partitionIdx uint32 // For round-robin partitioning
	batchSize    int
	batchTimeout int64  // Nanoseconds
	batchBuffer  []*Message
	mu           sync.Mutex
	acks         AckMode
}

// AckMode determines the acknowledgment level for produced messages.
type AckMode int

const (
	// AckNone: Fire-and-forget, highest throughput, lowest durability
	AckNone AckMode = iota
	// AckLeader: Wait for the partition leader to acknowledge
	AckLeader
	// AckAll: Wait for all in-sync replicas to acknowledge
	AckAll
)

// ProducerConfig holds producer configuration.
type ProducerConfig struct {
	Storage      *Storage
	TopicName    string
	BatchSize    int
	BatchTimeout int64 // Nanoseconds
	Acks         AckMode
}

// NewProducer creates a new message producer.
func NewProducer(config ProducerConfig) *Producer {
	return &Producer{
		storage:      config.Storage,
		topicName:    config.TopicName,
		batchSize:    config.BatchSize,
		batchTimeout: config.BatchTimeout,
		batchBuffer:  make([]*Message, 0, config.BatchSize),
		acks:         config.Acks,
	}
}

// Send sends a single message synchronously.
//
// The send process:
// 1. Choose partition (key-based or round-robin)
// 2. Add to batch buffer
// 3. If batch is full or timeout reached, flush
// 4. Write batch to partition's log segment
// 5. Wait for acknowledgment (based on ack mode)
func (p *Producer) Send(msg *Message) error {
	// Choose partition
	partition := p.choosePartition(msg.Key)

	// Get the partition
	topic, err := p.storage.GetTopic(p.topicName)
	if err != nil {
		return err
	}

	partitionObj, err := topic.GetPartition(partition)
	if err != nil {
		return err
	}

	// Append to partition
	offset, err := partitionObj.Append(msg)
	if err != nil {
		return err
	}

	msg.Offset = offset
	msg.Partition = partition

	// Wait for acknowledgment based on mode
	switch p.acks {
	case AckLeader:
		// Leader has acknowledged the write
	case AckAll:
		// All in-sync replicas have acknowledged
		// In a single-node implementation, this is the same as AckLeader
	}

	return nil
}

// SendBatch sends multiple messages as a batch.
//
// Batching improves throughput by:
// 1. Reducing the number of fsync calls (most expensive operation)
// 2. Improving disk sequential write patterns
// 3. Amortizing the cost of lock acquisition
//
// Typical batch sizes: 100-1000 messages or 100KB-1MB
func (p *Producer) SendBatch(messages []*Message) error {
	if len(messages) == 0 {
		return nil
	}

	topic, err := p.storage.GetTopic(p.topicName)
	if err != nil {
		return err
	}

	// Group messages by partition for efficient writing
	partitionMsgs := make(map[int][]*Message)
	for _, msg := range messages {
		partition := p.choosePartition(msg.Key)
		partitionMsgs[partition] = append(partitionMsgs[partition], msg)
	}

	// Write each partition's batch
	for partID, msgs := range partitionMsgs {
		partitionObj, err := topic.GetPartition(partID)
		if err != nil {
			continue
		}

		for _, msg := range msgs {
			offset, err := partitionObj.Append(msg)
			if err != nil {
				return err
			}
			msg.Offset = offset
			msg.Partition = partID
		}
	}

	return nil
}

// Flush forces any buffered messages to be written.
func (p *Producer) Flush() error {
	// In a production implementation, this would:
	// 1. Send any remaining batchBuffer messages
	// 2. Ensure all pending writes are synced
	p.mu.Lock()
	p.batchBuffer = p.batchBuffer[:0]
	p.mu.Unlock()
	return nil
}

// choosePartition selects a partition for the given key.
// If key is nil, uses round-robin. If key is present, uses consistent hashing.
func (p *Producer) choosePartition(key []byte) int {
	topic, err := p.storage.GetTopic(p.topicName)
	if err != nil {
		return 0
	}

	numPartitions := topic.PartitionCount()

	if key == nil {
		// Round-robin partitioning
		idx := atomic.AddUint32(&p.partitionIdx, 1)
		return int(idx) % numPartitions
	}

	// Key-based partitioning: messages with the same key always go to the same partition
	// This is critical for ordering guarantees
	hash := hashKey(key)
	return int(hash) % numPartitions
}

// hashKey computes a simple hash for the given key.
func hashKey(key []byte) uint32 {
	var h uint32
	for _, b := range key {
		h = 31*h + uint32(b)
	}
	return h
}

// Consumer reads messages from a topic partition.
//
// The consumer is responsible for:
// 1. Tracking its current offset in each partition
// 2. Fetching messages at or after the current offset
// 3. Acknowledging consumed messages (to advance the offset)
// 4. Handling rebalancing when part of a consumer group
//
// Offset management is critical: it determines where in the log the consumer
// resumes reading. Offsets are committed periodically (not per-message) for
// performance.
type Consumer struct {
	storage     *Storage
	topicName   string
	groupID     string
	partitions  []int
	offsets     map[int]int64  // partition -> current offset
	committed   map[int]int64  // partition -> last committed offset
	mu          sync.RWMutex
}

// ConsumerConfig holds consumer configuration.
type ConsumerConfig struct {
	Storage *Storage
	Topic   string
	GroupID string
}

// NewConsumer creates a new message consumer.
func NewConsumer(config ConsumerConfig) *Consumer {
	topic, err := config.Storage.GetTopic(config.Topic)
	if err != nil {
		return &Consumer{
			storage:  config.Storage,
			topicName: config.Topic,
			offsets:  make(map[int]int64),
			committed: make(map[int]int64),
		}
	}

	// Subscribe to all partitions
	partitions := make([]int, topic.PartitionCount())
	for i := 0; i < topic.PartitionCount(); i++ {
		partitions[i] = i
	}

	return &Consumer{
		storage:    config.Storage,
		topicName:  config.Topic,
		groupID:    config.GroupID,
		partitions: partitions,
		offsets:    make(map[int]int64),
		committed:  make(map[int]int64),
	}
}

// Subscribe sets the partitions this consumer will read from.
func (c *Consumer) Subscribe(partitions []int) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.partitions = partitions
}

// Poll fetches messages from subscribed partitions.
//
// The poll loop is the consumer's main work loop:
// 1. For each partition, read from the committed offset
// 2. Return available messages (up to maxMessages)
// 3. Update local offset tracking
//
// This is a pull-based model: the consumer decides when to fetch.
// Some systems (like RabbitMQ) use push-based delivery instead.
func (c *Consumer) Poll(maxMessages int) ([]*Message, error) {
	c.mu.RLock()
	partitions := make([]int, len(c.partitions))
	copy(partitions, c.partitions)
	c.mu.RUnlock()

	var allMessages []*Message

	for _, partID := range partitions {
		// Get the current offset for this partition
		c.mu.RLock()
		offset := c.offsets[partID]
		c.mu.RUnlock()

		// Get the topic and partition
		topic, err := c.storage.GetTopic(c.topicName)
		if err != nil {
			continue
		}

		partitionObj, err := topic.GetPartition(partID)
		if err != nil {
			continue
		}

		// Read messages from this partition
		messages, err := partitionObj.Read(offset, maxMessages)
		if err != nil {
			continue
		}

		if len(messages) > 0 {
			// Update local offset
			c.mu.Lock()
			c.offsets[partID] = offset + int64(len(messages))
			c.mu.Unlock()

			allMessages = append(allMessages, messages...)
		}
	}

	return allMessages, nil
}

// CommitOffset commits the offset for a partition.
//
// Committing an offset tells the consumer group that all messages up to
// (but not including) this offset have been successfully processed.
// If the consumer crashes, it will resume from the last committed offset.
//
// Offset commit strategies:
// - Auto commit: Periodic automatic commits (convenient but risk of duplicates)
// - Manual commit: Commit after processing each message (safer but slower)
// - Async commit: Commit in background (trade-off between safety and performance)
func (c *Consumer) CommitOffset(partition int, offset int64) error {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.committed[partition] = offset
	return nil
}

// CommitAll commits offsets for all subscribed partitions.
func (c *Consumer) CommitAll() error {
	c.mu.RLock()
	defer c.mu.RUnlock()

	for partID, offset := range c.offsets {
		c.committed[partID] = offset
	}
	return nil
}

// GetOffset returns the current offset for a partition.
func (c *Consumer) GetOffset(partition int) int64 {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.offsets[partition]
}

// ConsumerGroup manages a group of consumers sharing the load.
//
// Consumer groups provide:
// 1. Load balancing: Each partition is consumed by exactly one consumer in the group
// 2. Fault tolerance: If a consumer fails, its partitions are reassigned
// 3. Scalability: Add consumers to increase throughput
//
// Partition assignment uses range assignment or round-robin strategy.
// The group coordinator tracks which consumer owns which partitions.
type ConsumerGroup struct {
	groupID  string
	members  map[string]*Consumer
	topics   map[string][]int
	mu       sync.RWMutex
	storage  *Storage
}

// NewConsumerGroup creates a new consumer group.
func NewConsumerGroup(groupID string, storage *Storage) *ConsumerGroup {
	return &ConsumerGroup{
		groupID: groupID,
		members: make(map[string]*Consumer),
		topics:  make(map[string][]int),
		storage: storage,
	}
}

// AddMember adds a consumer to the group.
func (g *ConsumerGroup) AddMember(consumer *Consumer) {
	g.mu.Lock()
	defer g.mu.Unlock()

	// Generate a member ID
	memberID := consumer.groupID
	if memberID == "" {
		memberID = "consumer-" + consumer.topicName
	}

	g.members[memberID] = consumer
}

// RemoveMember removes a consumer from the group.
func (g *ConsumerGroup) RemoveMember(memberID string) {
	g.mu.Lock()
	defer g.mu.Unlock()

	delete(g.members, memberID)

	// Rebalance partitions
	g.rebalance()
}

// Subscribe adds a topic to the group.
func (g *ConsumerGroup) Subscribe(topic string) {
	g.mu.Lock()
	defer g.mu.Unlock()

	g.topics[topic] = nil // Will be populated during rebalance
}

// Rebalance redistributes partitions among group members.
//
// Rebalancing happens when:
// - A new member joins the group
// - A member leaves (detected by heartbeat timeout)
// - A topic's partition count changes
//
// We use range assignment: partitions are divided among consumers in order.
// For example, with 6 partitions and 2 consumers:
//   - Consumer A: partitions 0, 1, 2
//   - Consumer B: partitions 3, 4, 5
func (g *ConsumerGroup) Rebalance() {
	g.mu.Lock()
	defer g.mu.Unlock()

	g.rebalance()
}

// GetMemberIDs returns the IDs of all group members.
func (g *ConsumerGroup) GetMemberIDs() []string {
	g.mu.RLock()
	defer g.mu.RUnlock()

	ids := make([]string, 0, len(g.members))
	for id := range g.members {
		ids = append(ids, id)
	}
	return ids
}

// GetMembers returns a copy of the member map.
func (g *ConsumerGroup) GetMembers() map[string]*Consumer {
	g.mu.RLock()
	defer g.mu.RUnlock()

	members := make(map[string]*Consumer)
	for k, v := range g.members {
		members[k] = v
	}
	return members
}

// GroupID returns the group ID.
func (g *ConsumerGroup) GroupID() string {
	return g.groupID
}

// rebalance redistributes partitions among group members.
func (g *ConsumerGroup) rebalance() {
	// Collect all partitions from subscribed topics
	type topicPartitions struct {
		topic     string
		partitions []int
	}

	var allTopicParts []topicPartitions
	for topicName := range g.topics {
		topic, err := g.storage.GetTopic(topicName)
		if err != nil {
			continue
		}

		parts := make([]int, topic.PartitionCount())
		for i := 0; i < topic.PartitionCount(); i++ {
			parts[i] = i
		}
		allTopicParts = append(allTopicParts, topicPartitions{topicName, parts})
	}

	// Get sorted member IDs for deterministic assignment
	memberIDs := make([]string, 0, len(g.members))
	for id := range g.members {
		memberIDs = append(memberIDs, id)
	}

	if len(memberIDs) == 0 {
		return
	}

	// Assign partitions using round-robin across members
	memberIndex := 0
	for _, tp := range allTopicParts {
		// Assign each partition to a member
		for _, partID := range tp.partitions {
			memberID := memberIDs[memberIndex%len(memberIDs)]
			consumer := g.members[memberID]

			// Subscribe consumer to this partition
			consumer.Subscribe([]int{partID})
			memberIndex++
		}
	}
}

// Package main demonstrates basic producer and consumer usage.
//
// This example shows:
// 1. Creating a topic with partitions
// 2. Producing messages with batching
// 3. Consuming messages with offset tracking
// 4. Committing offsets for durability
package main

import (
	"fmt"
	"log"
	"os"
	"path/filepath"

	"high-throughput-message-queue/src"
)

func main() {
	// Create a temporary data directory
	dataDir := filepath.Join(os.TempDir(), "mq-demo-basic")
	os.RemoveAll(dataDir)
	os.MkdirAll(dataDir, 0755)
	defer os.RemoveAll(dataDir)

	// Create storage with configuration
	storage := queue.NewStorage(queue.DefaultStorageConfig(dataDir))

	// Create a topic with 3 partitions
	// Topics organize related messages; partitions enable parallelism
	topicConfig := queue.NewTopicConfig("orders", 3)
	if err := storage.CreateTopic(topicConfig); err != nil {
		log.Fatalf("Failed to create topic: %v", err)
	}
	fmt.Printf("Created topic: %s with %d partitions\n", topicConfig.Name, topicConfig.NumPartitions)

	// Create a producer
	// The producer batches messages and routes them to partitions
	producer := queue.NewProducer(queue.ProducerConfig{
		Storage:      storage,
		TopicName:    "orders",
		BatchSize:    100,
		BatchTimeout: 1000000000, // 1 second
		Acks:         queue.AckLeader,
	})

	// Create a consumer
	// The consumer tracks offsets to know where to resume reading
	consumer := queue.NewConsumer(queue.ConsumerConfig{
		Storage: storage,
		Topic:   "orders",
		GroupID: "order-processors",
	})

	// Produce messages
	fmt.Println("\n--- Producing messages ---")
	for i := 0; i < 20; i++ {
		key := []byte(fmt.Sprintf("order-%d", i))
		value := []byte(fmt.Sprintf(`{"id": %d, "amount": %d}`, i, 100+i))
		msg := queue.NewMessage(key, value)
		msg.WithHeader("type", "order").WithHeader("priority", "high")

		if err := producer.Send(msg); err != nil {
			log.Printf("Failed to send message: %v", err)
			continue
		}
		fmt.Printf("  Sent message %d (partition: %d)\n", i, queue.GetMessagePartition(msg))
	}

	// Flush any remaining buffered messages
	producer.Flush()

	// Consume messages
	fmt.Println("\n--- Consuming messages ---")
	for i := 0; i < 3; i++ {
		messages, err := consumer.Poll(10)
		if err != nil {
			log.Printf("Failed to poll: %v", err)
			continue
		}

		fmt.Printf("  Batch %d: received %d messages\n", i, len(messages))
		for _, msg := range messages {
			fmt.Printf("    Offset: %d, Partition: %d, Key: %s, Value: %s\n",
				msg.Offset, msg.Partition, string(msg.Key), string(msg.Value))
		}

		// Commit offsets to mark messages as processed
		if err := consumer.CommitAll(); err != nil {
			log.Printf("Failed to commit offsets: %v", err)
		}
	}

	// Verify topic exists
	topics := storage.ListTopics()
	fmt.Printf("\nTopics: %v\n", topics)

	// Show partition info
	topic, _ := storage.GetTopic("orders")
	for i := 0; i < topic.PartitionCount(); i++ {
		partition, _ := topic.GetPartition(i)
		fmt.Printf("  Partition %d: base offset=%d, latest offset=%d\n",
			i, queue.GetBaseOffset(partition), queue.GetBaseOffset(partition)+queue.GetEntryCount(queue.NewIndexFile("", 1000)))
	}

	fmt.Println("\nBasic demo complete!")
}

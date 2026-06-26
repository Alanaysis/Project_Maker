// Package main demonstrates consumer groups and partition rebalancing.
//
// Consumer groups enable:
// 1. Load balancing: Multiple consumers share the work
// 2. Fault tolerance: If a consumer fails, others take over
// 3. Horizontal scaling: Add consumers to increase throughput
//
// Partition assignment strategy:
// - Range assignment: partitions divided among consumers
// - Round-robin: partitions distributed evenly
// - Sticky assignment: minimizes reassignment during rebalancing
package main

import (
	"fmt"
	"log"
	"os"
	"path/filepath"
	"sync"
	"time"

	"high-throughput-message-queue/src"
)

func main() {
	// Create a temporary data directory
	dataDir := filepath.Join(os.TempDir(), "mq-demo-groups")
	os.RemoveAll(dataDir)
	os.MkdirAll(dataDir, 0755)
	defer os.RemoveAll(dataDir)

	// Create storage
	storage := queue.NewStorage(queue.DefaultStorageConfig(dataDir))

	// Create a topic with 6 partitions
	topicConfig := queue.NewTopicConfig("events", 6)
	if err := storage.CreateTopic(topicConfig); err != nil {
		log.Fatalf("Failed to create topic: %v", err)
	}
	fmt.Printf("Created topic: %s with %d partitions\n", topicConfig.Name, topicConfig.NumPartitions)

	// Create a consumer group
	group := queue.NewConsumerGroup("analytics-group", storage)
	group.Subscribe("events")

	// Create 3 consumers in the group
	// Each consumer will be assigned a subset of partitions
	var consumers []*queue.Consumer
	for i := 0; i < 3; i++ {
		consumer := queue.NewConsumer(queue.ConsumerConfig{
			Storage: storage,
			Topic:   "events",
			GroupID: "analytics-group",
		})
		consumer.Subscribe([]int{i}) // Initially subscribe to one partition
		consumers = append(consumers, consumer)

		// Add to group (triggers rebalance)
		group.AddMember(consumer)
	}

	// Trigger initial rebalance
	// This distributes partitions among consumers
	group.Rebalance()

	// Print partition assignment
	fmt.Println("\n--- Partition Assignment ---")
	members := group.GetMembers()
	for memberID, consumer := range members {
		parts := consumer.GetConsumerPartitions()
		fmt.Printf("  %s: partitions %v\n", memberID, parts)
	}

	// Produce messages to all partitions
	fmt.Println("\n--- Producing messages ---")
	producer := queue.NewProducer(queue.ProducerConfig{
		Storage:      storage,
		TopicName:    "events",
		BatchSize:    50,
		BatchTimeout: 1000000000,
		Acks:         queue.AckLeader,
	})

	for i := 0; i < 30; i++ {
		key := []byte(fmt.Sprintf("event-%d", i))
		value := []byte(fmt.Sprintf(`{"event": "click", "user": %d}`, i))
		msg := queue.NewMessage(key, value)
		msg.WithHeader("type", "click").WithHeader("ts", fmt.Sprintf("%d", time.Now().Unix()))

		if err := producer.Send(msg); err != nil {
			log.Printf("Failed to send: %v", err)
			continue
		}
		fmt.Printf("  Event %d -> partition %d\n", i, queue.GetMessagePartition(msg))
	}
	producer.Flush()

	// Each consumer reads from its assigned partitions
	fmt.Println("\n--- Consuming messages (per consumer) ---")
	var wg sync.WaitGroup
	for i, consumer := range consumers {
		wg.Add(1)
		go func(idx int, c *queue.Consumer) {
			defer wg.Done()

			messages, err := c.Poll(10)
			if err != nil {
				log.Printf("Consumer %d poll error: %v", idx, err)
				return
			}

			fmt.Printf("  Consumer %d: received %d messages\n", idx, len(messages))
			for _, msg := range messages {
				fmt.Printf("    [offset=%d] %s\n", msg.Offset, string(msg.Value))
			}

			// Commit offsets
			c.CommitAll()
		}(i, consumer)
	}

	wg.Wait()

	// Simulate a consumer leaving the group
	fmt.Println("\n--- Consumer leaving the group ---")
	if len(consumers) > 0 {
		// Remove the last consumer
		lastID := ""
		for id := range members {
			lastID = id
		}
		group.RemoveMember(lastID)
		fmt.Printf("  Removed consumer: %s\n", lastID)
	}

	// Rebalance and show new assignment
	group.Rebalance()
	fmt.Println("\n--- New Partition Assignment ---")
	members = group.GetMembers()
	for memberID, consumer := range members {
		parts := consumer.GetConsumerPartitions()
		fmt.Printf("  %s: partitions %v\n", memberID, parts)
	}

	// Demonstrate offset recovery
	fmt.Println("\n--- Offset Tracking ---")
	for i, consumer := range consumers {
		// Get committed offsets
		committed := consumer.GetConsumerCommitted()
		fmt.Printf("  Consumer %d committed offsets: %v\n", i, committed)
	}

	fmt.Println("\nConsumer group demo complete!")
}

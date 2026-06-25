// Command consumer demonstrates subscribing to and processing messages.
package main

import (
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/example/message-queue/internal/protocol"
	"github.com/example/message-queue/pkg/api"
)

func main() {
	cfg := api.DefaultConfig()
	cfg.DataDir = "./data"

	mq, err := api.New(cfg)
	if err != nil {
		log.Fatalf("Failed to create message queue: %v", err)
	}
	defer mq.Close()

	// Create topics.
	mq.CreateTopic("orders")
	mq.CreateTopic("notifications")
	mq.CreateQueueTopic("tasks")

	// 1. Pub/Sub consumer with filter.
	fmt.Println("=== Pub/Sub Consumer (orders) ===")
	orderHandler := func(msg *protocol.Message) error {
		fmt.Printf("[Orders] Received [%s]: %s\n", msg.ID[:16], string(msg.Payload))
		return nil
	}

	c1 := mq.NewConsumer("order-processor-1", orderHandler)
	defer c1.Close()

	if err := c1.Subscribe("orders"); err != nil {
		log.Fatalf("Subscribe error: %v", err)
	}
	fmt.Println("Consumer 'order-processor-1' subscribed to 'orders'")

	// 2. Filtered consumer (only SMS notifications).
	fmt.Println("\n=== Filtered Consumer (notifications - SMS only) ===")
	smsHandler := func(msg *protocol.Message) error {
		fmt.Printf("[SMS] Received [%s]: %s\n", msg.ID[:16], string(msg.Payload))
		return nil
	}

	c2 := mq.NewConsumer("sms-processor", smsHandler)
	defer c2.Close()

	// Subscribe with filter: only messages with channel=sms.
	filter := map[string]string{"channel": "sms"}
	if err := c2.SubscribeWithFilter("notifications", filter); err != nil {
		log.Fatalf("Subscribe with filter error: %v", err)
	}
	fmt.Println("Consumer 'sms-processor' subscribed to 'notifications' (filter: channel=sms)")

	// 3. Pull mode consumer.
	fmt.Println("\n=== Pull Mode Consumer (tasks) ===")
	go func() {
		pullConsumer := mq.NewConsumer("task-puller", func(msg *protocol.Message) error {
			fmt.Printf("[Pull] Processing task: %s\n", string(msg.Payload))
			return nil
		})
		defer pullConsumer.Close()

		for {
			err := pullConsumer.PullAndProcess("tasks", 1*time.Second)
			if err != nil {
				// No message available or timeout, continue.
				time.Sleep(100 * time.Millisecond)
				continue
			}
		}
	}()

	// 4. Consumer group example.
	fmt.Println("\n=== Consumer Group (tasks) ===")
	cg, err := mq.CreateConsumerGroup("task-group", "tasks")
	if err != nil {
		log.Printf("Consumer group error: %v", err)
	} else {
		// Add consumers to the group.
		for i := 0; i < 3; i++ {
			consumerID := fmt.Sprintf("worker-%d", i)
			cg.AddConsumer(consumerID)
			fmt.Printf("Added consumer '%s' to group 'task-group'\n", consumerID)
		}
	}

	fmt.Println("\nWaiting for messages... Press Ctrl+C to exit.")

	// Wait for interrupt signal.
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	<-sigCh

	fmt.Println("\nShutting down consumer...")
}

// Command consumer demonstrates subscribing to and processing messages.
package main

import (
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"

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

	// Create topic explicitly.
	if err := mq.CreateTopic("orders"); err != nil {
		log.Printf("Topic creation: %v (may already exist)", err)
	}

	// Define message handler.
	handler := func(msg *protocol.Message) error {
		fmt.Printf("[Consumer] Received [%s] on topic '%s': %s\n",
			msg.ID[:16], msg.Topic, string(msg.Payload))
		return nil
	}

	// Create and subscribe consumer.
	c := mq.NewConsumer("order-processor-1", handler)
	defer c.Close()

	if err := c.Subscribe("orders"); err != nil {
		log.Fatalf("Subscribe error: %v", err)
	}

	fmt.Println("Consumer 'order-processor-1' subscribed to 'orders'. Waiting for messages...")
	fmt.Println("Press Ctrl+C to exit.")

	// Wait for interrupt signal.
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	<-sigCh

	fmt.Println("\nShutting down consumer...")
}

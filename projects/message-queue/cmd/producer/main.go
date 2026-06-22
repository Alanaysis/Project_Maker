// Command producer demonstrates publishing messages to the queue.
package main

import (
	"fmt"
	"log"
	"time"

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

	p := mq.NewProducer()

	// Publish some messages.
	messages := []string{
		`{"order_id": 1, "item": "laptop", "qty": 1}`,
		`{"order_id": 2, "item": "mouse", "qty": 2}`,
		`{"order_id": 3, "item": "keyboard", "qty": 1}`,
		`{"order_id": 4, "item": "monitor", "qty": 1}`,
		`{"order_id": 5, "item": "headset", "qty": 3}`,
	}

	for _, payload := range messages {
		msg, err := p.PublishString("orders", payload)
		if err != nil {
			log.Printf("Publish error: %v", err)
			continue
		}
		fmt.Printf("Published [%s] to topic 'orders': %s\n", msg.ID[:16], payload)
		time.Sleep(100 * time.Millisecond)
	}

	fmt.Println("\nAll messages published successfully.")

	// Show topic info.
	count, subs, err := mq.TopicInfo("orders")
	if err != nil {
		log.Printf("Topic info error: %v", err)
	} else {
		fmt.Printf("Topic 'orders': %d messages, %d subscribers\n", count, subs)
	}
}

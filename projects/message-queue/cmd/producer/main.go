// Command producer demonstrates publishing messages to the queue.
package main

import (
	"fmt"
	"log"
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
	mq.CreateQueueTopic("tasks") // point-to-point topic

	p := mq.NewProducer()

	// 1. Basic publish.
	fmt.Println("=== Basic Publish ===")
	messages := []string{
		`{"order_id": 1, "item": "laptop", "qty": 1}`,
		`{"order_id": 2, "item": "mouse", "qty": 2}`,
		`{"order_id": 3, "item": "keyboard", "qty": 1}`,
	}

	for _, payload := range messages {
		msg, err := p.PublishString("orders", payload)
		if err != nil {
			log.Printf("Publish error: %v", err)
			continue
		}
		fmt.Printf("Published [%s] to topic 'orders': %s\n", msg.ID[:16], payload)
	}

	// 2. Priority messages.
	fmt.Println("\n=== Priority Messages ===")
	p.PublishWithPriority("orders", []byte(`{"order_id": 100, "urgent": true}`), protocol.PriorityHigh)
	p.PublishWithPriority("orders", []byte(`{"order_id": 101, "normal": true}`), protocol.PriorityNormal)
	p.PublishWithPriority("orders", []byte(`{"order_id": 102, "low": true}`), protocol.PriorityLow)
	fmt.Println("Published 3 messages with different priorities")

	// 3. Delayed message.
	fmt.Println("\n=== Delayed Message ===")
	delay := 5 * time.Second
	msg, _ := p.PublishWithOptions("notifications",
		[]byte(`{"type": "reminder", "msg": "Check your email"}`),
		protocol.PriorityNormal,
		map[string]string{"channel": "email"},
		&delay,
	)
	fmt.Printf("Published delayed message [%s] (deliver in %v)\n", msg.ID[:16], delay)

	// 4. Messages with headers for filtering.
	fmt.Println("\n=== Filtered Messages ===")
	p.PublishWithHeaders("notifications",
		[]byte(`{"type": "alert", "severity": "high"}`),
		map[string]string{"channel": "sms", "severity": "high"},
	)
	p.PublishWithHeaders("notifications",
		[]byte(`{"type": "info", "severity": "low"}`),
		map[string]string{"channel": "email", "severity": "low"},
	)
	fmt.Println("Published 2 messages with different headers")

	// 5. Queue topic (point-to-point).
	fmt.Println("\n=== Queue Topic (Point-to-Point) ===")
	for i := 0; i < 5; i++ {
		p.PublishString("tasks", fmt.Sprintf(`{"task_id": %d, "action": "process"}`, i))
	}
	fmt.Println("Published 5 tasks to queue topic")

	fmt.Println("\nAll messages published successfully.")

	// Show topic info.
	for _, topic := range []string{"orders", "notifications", "tasks"} {
		count, subs, err := mq.TopicInfo(topic)
		if err != nil {
			log.Printf("Topic info error: %v", err)
		} else {
			fmt.Printf("Topic '%s': %d messages, %d subscribers\n", topic, count, subs)
		}
	}
}

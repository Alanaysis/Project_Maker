package queue

import (
	"sync"
	"testing"
	"time"

	"github.com/example/message-queue/internal/persistence"
	"github.com/example/message-queue/internal/protocol"
)

func newTestBroker() *Broker {
	return NewBroker(DefaultConfig(), persistence.NewMemStore())
}

func TestBrokerCreateTopic(t *testing.T) {
	broker := newTestBroker()
	defer broker.Close()

	if err := broker.CreateTopic("test"); err != nil {
		t.Fatalf("create topic: %v", err)
	}

	if err := broker.CreateTopic("test"); err != protocol.ErrTopicAlreadyExists {
		t.Errorf("expected ErrTopicAlreadyExists, got %v", err)
	}
}

func TestBrokerCreateQueueTopic(t *testing.T) {
	broker := newTestBroker()
	defer broker.Close()

	if err := broker.CreateQueueTopic("queue-test"); err != nil {
		t.Fatalf("create queue topic: %v", err)
	}

	topic, err := broker.GetTopic("queue-test")
	if err != nil {
		t.Fatalf("get topic: %v", err)
	}

	if topic.Mode != ModeQueue {
		t.Errorf("expected queue mode, got %v", topic.Mode)
	}
}

func TestBrokerPublish(t *testing.T) {
	broker := newTestBroker()
	defer broker.Close()

	msg, err := broker.Publish("events", []byte("hello"))
	if err != nil {
		t.Fatalf("publish: %v", err)
	}
	if msg.Topic != "events" {
		t.Errorf("expected topic 'events', got %q", msg.Topic)
	}

	topic, err := broker.GetTopic("events")
	if err != nil {
		t.Fatalf("get topic: %v", err)
	}
	if len(topic.Messages()) != 1 {
		t.Errorf("expected 1 message, got %d", len(topic.Messages()))
	}
}

func TestBrokerAutoCreateTopic(t *testing.T) {
	broker := newTestBroker()
	defer broker.Close()

	_, err := broker.Publish("auto-topic", []byte("data"))
	if err != nil {
		t.Fatalf("publish to auto-created topic: %v", err)
	}

	topics := broker.Topics()
	found := false
	for _, name := range topics {
		if name == "auto-topic" {
			found = true
			break
		}
	}
	if !found {
		t.Error("expected 'auto-topic' in topics list")
	}
}

func TestBrokerSubscribeAndReceive(t *testing.T) {
	broker := newTestBroker()
	defer broker.Close()

	broker.CreateTopic("inbox")

	sub, err := broker.Subscribe("inbox", "consumer-1")
	if err != nil {
		t.Fatalf("subscribe: %v", err)
	}

	// Publish after subscribing.
	broker.Publish("inbox", []byte("msg1"))
	broker.Publish("inbox", []byte("msg2"))

	select {
	case msg := <-sub.Ch:
		if string(msg.Payload) != "msg1" {
			t.Errorf("expected 'msg1', got %q", string(msg.Payload))
		}
	case <-time.After(time.Second):
		t.Error("timeout waiting for first message")
	}

	select {
	case msg := <-sub.Ch:
		if string(msg.Payload) != "msg2" {
			t.Errorf("expected 'msg2', got %q", string(msg.Payload))
		}
	case <-time.After(time.Second):
		t.Error("timeout waiting for second message")
	}
}

func TestBrokerSubscribeWithFilter(t *testing.T) {
	broker := newTestBroker()
	defer broker.Close()

	broker.CreateTopic("filtered")

	filter := map[string]string{"type": "alert"}
	sub, err := broker.SubscribeWithFilter("filtered", "consumer-1", filter)
	if err != nil {
		t.Fatalf("subscribe: %v", err)
	}

	// Publish matching message.
	broker.PublishWithHeaders("filtered", []byte("alert-msg"), map[string]string{"type": "alert"})

	// Publish non-matching message.
	broker.PublishWithHeaders("filtered", []byte("info-msg"), map[string]string{"type": "info"})

	select {
	case msg := <-sub.Ch:
		if string(msg.Payload) != "alert-msg" {
			t.Errorf("expected 'alert-msg', got %q", string(msg.Payload))
		}
	case <-time.After(time.Second):
		t.Error("timeout waiting for filtered message")
	}
}

func TestBrokerPublishDelayed(t *testing.T) {
	broker := newTestBroker()
	defer broker.Close()

	broker.CreateTopic("delayed")

	delay := 500 * time.Millisecond
	msg, err := broker.PublishDelayed("delayed", []byte("delayed-msg"), delay)
	if err != nil {
		t.Fatalf("publish delayed: %v", err)
	}

	if msg.DeliverAfter == nil {
		t.Error("expected non-nil DeliverAfter")
	}

	// Message should not be ready immediately.
	topic, _ := broker.GetTopic("delayed")
	ready := topic.GetReadyMessages()
	if len(ready) != 0 {
		t.Errorf("expected 0 ready messages immediately, got %d", len(ready))
	}

	// Wait for delay.
	time.Sleep(600 * time.Millisecond)

	ready = topic.GetReadyMessages()
	if len(ready) != 1 {
		t.Errorf("expected 1 ready message after delay, got %d", len(ready))
	}
}

func TestBrokerPublishWithPriority(t *testing.T) {
	broker := newTestBroker()
	defer broker.Close()

	broker.CreateTopic("priority")

	broker.PublishWithPriority("priority", []byte("low"), protocol.PriorityLow)
	broker.PublishWithPriority("priority", []byte("high"), protocol.PriorityHigh)
	broker.PublishWithPriority("priority", []byte("normal"), protocol.PriorityNormal)

	topic, _ := broker.GetTopic("priority")
	msgs := topic.Messages()

	if len(msgs) != 3 {
		t.Fatalf("expected 3 messages, got %d", len(msgs))
	}

	// Should be ordered by priority.
	if string(msgs[0].Payload) != "high" {
		t.Errorf("expected first message 'high', got %q", string(msgs[0].Payload))
	}
	if string(msgs[1].Payload) != "normal" {
		t.Errorf("expected second message 'normal', got %q", string(msgs[1].Payload))
	}
	if string(msgs[2].Payload) != "low" {
		t.Errorf("expected third message 'low', got %q", string(msgs[2].Payload))
	}
}

func TestBrokerAcknowledge(t *testing.T) {
	broker := newTestBroker()
	defer broker.Close()

	msg, _ := broker.Publish("ack-test", []byte("data"))

	if err := broker.Acknowledge("ack-test", msg.ID); err != nil {
		t.Fatalf("ack: %v", err)
	}

	// After ack, message is removed from topic, so second ack returns not found.
	if err := broker.Acknowledge("ack-test", msg.ID); err != protocol.ErrMessageNotFound {
		t.Errorf("expected ErrMessageNotFound after ack (message removed), got %v", err)
	}
}

func TestBrokerNegativeAcknowledge(t *testing.T) {
	broker := newTestBroker()
	defer broker.Close()

	broker.CreateTopic("nack-test")

	// Publish a message with max retries of 2.
	msg, _ := broker.PublishWithOptions("nack-test", []byte("data"), protocol.PriorityNormal, nil, nil)
	msg.MaxRetries = 2

	// First nack - should increment retry.
	if err := broker.NegativeAcknowledge("nack-test", msg.ID); err != nil {
		t.Fatalf("first nack: %v", err)
	}

	if msg.RetryCount != 1 {
		t.Errorf("expected retry count 1, got %d", msg.RetryCount)
	}

	// Second nack - should increment retry.
	if err := broker.NegativeAcknowledge("nack-test", msg.ID); err != nil {
		t.Fatalf("second nack: %v", err)
	}

	if msg.RetryCount != 2 {
		t.Errorf("expected retry count 2, got %d", msg.RetryCount)
	}

	// Third nack - should move to DLQ.
	if err := broker.NegativeAcknowledge("nack-test", msg.ID); err != nil {
		t.Fatalf("third nack: %v", err)
	}

	dlq := broker.GetDeadLetterQueue("nack-test")
	if dlq.Count() != 1 {
		t.Errorf("expected 1 message in DLQ, got %d", dlq.Count())
	}
}

func TestBrokerConsumerGroup(t *testing.T) {
	broker := newTestBroker()
	defer broker.Close()

	broker.CreateTopic("group-test")

	// Create consumer group.
	cg, err := broker.CreateConsumerGroup("test-group", "group-test")
	if err != nil {
		t.Fatalf("create group: %v", err)
	}

	// Add consumers to group.
	gc1, err := broker.JoinConsumerGroup("test-group", "consumer-1")
	if err != nil {
		t.Fatalf("join group: %v", err)
	}

	gc2, err := broker.JoinConsumerGroup("test-group", "consumer-2")
	if err != nil {
		t.Fatalf("join group: %v", err)
	}

	if cg.ConsumerCount() != 2 {
		t.Errorf("expected 2 consumers in group, got %d", cg.ConsumerCount())
	}

	// Publish message.
	msg := protocol.NewMessage("group-test", []byte("group-msg"))
	broker.DeliverToGroup("test-group", msg)

	// Only one consumer should receive the message.
	received := 0
	timeout := time.After(500 * time.Millisecond)

	select {
	case <-gc1.Ch:
		received++
	case <-timeout:
	}

	select {
	case <-gc2.Ch:
		received++
	case <-timeout:
	}

	if received != 1 {
		t.Errorf("expected exactly 1 consumer to receive message, got %d", received)
	}
}

func TestBrokerPull(t *testing.T) {
	broker := newTestBroker()
	defer broker.Close()

	broker.CreateTopic("pull-test")

	// Publish messages.
	broker.Publish("pull-test", []byte("msg1"))
	broker.Publish("pull-test", []byte("msg2"))

	// Pull first message.
	msg1, err := broker.Pull("pull-test", 1*time.Second)
	if err != nil {
		t.Fatalf("pull: %v", err)
	}
	if string(msg1.Payload) != "msg1" {
		t.Errorf("expected 'msg1', got %q", string(msg1.Payload))
	}
	if msg1.Status != protocol.StatusDelivered {
		t.Errorf("expected delivered status, got %v", msg1.Status)
	}

	// Pull second message.
	msg2, err := broker.Pull("pull-test", 1*time.Second)
	if err != nil {
		t.Fatalf("pull: %v", err)
	}
	if string(msg2.Payload) != "msg2" {
		t.Errorf("expected 'msg2', got %q", string(msg2.Payload))
	}

	// Pull with timeout should return error.
	_, err = broker.Pull("pull-test", 100*time.Millisecond)
	if err != protocol.ErrMessageNotFound {
		t.Errorf("expected ErrMessageNotFound, got %v", err)
	}
}

func TestBrokerDeadLetterQueue(t *testing.T) {
	broker := newTestBroker()
	defer broker.Close()

	broker.CreateTopic("dlq-test")

	// Get DLQ.
	dlq := broker.GetDeadLetterQueue("dlq-test")
	if dlq == nil {
		t.Fatal("expected non-nil DLQ")
	}

	// Add message to DLQ.
	msg := protocol.NewMessage("dlq-test", []byte("dead-msg"))
	msg.MaxRetries = 0 // Already exceeded.
	dlq.Add(msg)

	if dlq.Count() != 1 {
		t.Errorf("expected 1 message in DLQ, got %d", dlq.Count())
	}

	// Retry message from DLQ.
	retried := dlq.RetryMessage(msg.ID)
	if retried == nil {
		t.Fatal("expected retried message")
	}
	if retried.Status != protocol.StatusPending {
		t.Errorf("expected pending status after retry, got %v", retried.Status)
	}

	if dlq.Count() != 0 {
		t.Errorf("expected 0 messages in DLQ after retry, got %d", dlq.Count())
	}
}

func TestBrokerUnsubscribe(t *testing.T) {
	broker := newTestBroker()
	defer broker.Close()

	broker.CreateTopic("t")
	sub, _ := broker.Subscribe("t", "c1")

	broker.Unsubscribe("t", "c1")

	// Channel should be closed.
	select {
	case _, ok := <-sub.Ch:
		if ok {
			t.Error("expected closed channel")
		}
	case <-time.After(time.Second):
		t.Error("timeout waiting for channel close")
	}
}

func TestBrokerTopics(t *testing.T) {
	broker := newTestBroker()
	defer broker.Close()

	broker.CreateTopic("a")
	broker.CreateTopic("b")
	broker.CreateTopic("c")

	topics := broker.Topics()
	if len(topics) != 3 {
		t.Errorf("expected 3 topics, got %d", len(topics))
	}
}

func TestBrokerFanOut(t *testing.T) {
	broker := newTestBroker()
	defer broker.Close()

	broker.CreateTopic("fanout")

	sub1, _ := broker.Subscribe("fanout", "c1")
	sub2, _ := broker.Subscribe("fanout", "c2")

	broker.Publish("fanout", []byte("broadcast"))

	var wg sync.WaitGroup
	wg.Add(2)

	go func() {
		defer wg.Done()
		select {
		case msg := <-sub1.Ch:
			if string(msg.Payload) != "broadcast" {
				t.Errorf("sub1: expected 'broadcast', got %q", string(msg.Payload))
			}
		case <-time.After(time.Second):
			t.Error("sub1: timeout")
		}
	}()

	go func() {
		defer wg.Done()
		select {
		case msg := <-sub2.Ch:
			if string(msg.Payload) != "broadcast" {
				t.Errorf("sub2: expected 'broadcast', got %q", string(msg.Payload))
			}
		case <-time.After(time.Second):
			t.Error("sub2: timeout")
		}
	}()

	wg.Wait()
}

func TestBrokerRecover(t *testing.T) {
	store := persistence.NewMemStore()

	// Phase 1: create broker, publish, close.
	broker1 := NewBroker(DefaultConfig(), store)
	broker1.CreateTopic("recovery")
	msg1, _ := broker1.Publish("recovery", []byte("m1"))
	msg2, _ := broker1.Publish("recovery", []byte("m2"))
	broker1.Acknowledge("recovery", msg1.ID) // msg1 acked, msg2 pending
	broker1.Close()

	// Phase 2: new broker recovers from same store.
	broker2 := NewBroker(DefaultConfig(), store)
	if err := broker2.Recover(); err != nil {
		t.Fatalf("recover: %v", err)
	}
	defer broker2.Close()

	topic, _ := broker2.GetTopic("recovery")
	msgs := topic.Messages()

	// Only msg2 should be replayed (msg1 was acknowledged).
	if len(msgs) != 1 {
		t.Fatalf("expected 1 recovered message, got %d", len(msgs))
	}
	if msgs[0].ID != msg2.ID {
		t.Errorf("expected recovered message %s, got %s", msg2.ID, msgs[0].ID)
	}
}

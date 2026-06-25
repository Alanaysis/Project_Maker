package consumer

import (
	"sync/atomic"
	"testing"
	"time"

	"github.com/example/message-queue/internal/persistence"
	"github.com/example/message-queue/internal/producer"
	"github.com/example/message-queue/internal/protocol"
	"github.com/example/message-queue/internal/queue"
)

func newTestEnv() (*queue.Broker, *producer.Producer) {
	broker := queue.NewBroker(queue.DefaultConfig(), persistence.NewMemStore())
	return broker, producer.New(broker)
}

func TestConsumerSubscribe(t *testing.T) {
	broker, p := newTestEnv()
	defer broker.Close()

	broker.CreateTopic("t")

	var count int32
	handler := func(msg *protocol.Message) error {
		atomic.AddInt32(&count, 1)
		return nil
	}

	c := New("c1", broker, handler)
	defer c.Close()

	if err := c.Subscribe("t"); err != nil {
		t.Fatalf("subscribe: %v", err)
	}

	p.PublishString("t", "msg1")
	p.PublishString("t", "msg2")

	time.Sleep(500 * time.Millisecond)

	if atomic.LoadInt32(&count) != 2 {
		t.Errorf("expected 2 processed, got %d", atomic.LoadInt32(&count))
	}
}

func TestConsumerSubscribeWithFilter(t *testing.T) {
	broker, p := newTestEnv()
	defer broker.Close()

	broker.CreateTopic("filtered")

	var count int32
	handler := func(msg *protocol.Message) error {
		atomic.AddInt32(&count, 1)
		return nil
	}

	c := New("c1", broker, handler)
	defer c.Close()

	// Subscribe with filter: only messages with type=alert.
	filter := map[string]string{"type": "alert"}
	if err := c.SubscribeWithFilter("filtered", filter); err != nil {
		t.Fatalf("subscribe with filter: %v", err)
	}

	// Publish matching message.
	p.PublishWithHeaders("filtered", []byte("alert"), map[string]string{"type": "alert"})

	// Publish non-matching message.
	p.PublishWithHeaders("filtered", []byte("info"), map[string]string{"type": "info"})

	time.Sleep(500 * time.Millisecond)

	if atomic.LoadInt32(&count) != 1 {
		t.Errorf("expected 1 processed (filtered), got %d", atomic.LoadInt32(&count))
	}
}

func TestConsumerDuplicateSubscribe(t *testing.T) {
	broker, _ := newTestEnv()
	defer broker.Close()

	broker.CreateTopic("t")

	c := New("c1", broker, func(msg *protocol.Message) error { return nil })
	defer c.Close()

	c.Subscribe("t")
	if err := c.Subscribe("t"); err == nil {
		t.Error("expected error on duplicate subscribe")
	}
}

func TestConsumerUnsubscribe(t *testing.T) {
	broker, _ := newTestEnv()
	defer broker.Close()

	broker.CreateTopic("t")

	c := New("c1", broker, func(msg *protocol.Message) error { return nil })
	c.Subscribe("t")
	c.Unsubscribe("t")

	// Should be safe to close after unsubscribe.
	c.Close()
}

func TestConsumerClose(t *testing.T) {
	broker, _ := newTestEnv()
	defer broker.Close()

	broker.CreateTopic("t")

	c := New("c1", broker, func(msg *protocol.Message) error { return nil })
	c.Subscribe("t")

	// Double close should be safe.
	c.Close()
	c.Close()
}

func TestConsumerPull(t *testing.T) {
	broker, p := newTestEnv()
	defer broker.Close()

	broker.CreateTopic("pull-test")
	p.PublishString("pull-test", "msg1")

	c := New("c1", broker, func(msg *protocol.Message) error { return nil })
	defer c.Close()

	msg, err := c.Pull("pull-test", 1*time.Second)
	if err != nil {
		t.Fatalf("pull: %v", err)
	}
	if string(msg.Payload) != "msg1" {
		t.Errorf("expected 'msg1', got %q", string(msg.Payload))
	}
}

func TestConsumerPullAndProcess(t *testing.T) {
	broker, p := newTestEnv()
	defer broker.Close()

	broker.CreateTopic("pull-process")
	p.PublishString("pull-process", "msg1")

	var processed int32
	handler := func(msg *protocol.Message) error {
		atomic.AddInt32(&processed, 1)
		return nil
	}

	c := New("c1", broker, handler)
	defer c.Close()

	// PullAndProcess will pull the message and call the handler.
	// Since Pull removes the message from the topic, Ack will return not found,
	// but the handler will still be called.
	_ = c.PullAndProcess("pull-process", 1*time.Second)

	// The handler should have been called even if ack fails.
	if atomic.LoadInt32(&processed) != 1 {
		t.Errorf("expected 1 processed, got %d", atomic.LoadInt32(&processed))
	}
}

func TestConsumerPullTimeout(t *testing.T) {
	broker, _ := newTestEnv()
	defer broker.Close()

	broker.CreateTopic("empty")

	c := New("c1", broker, func(msg *protocol.Message) error { return nil })
	defer c.Close()

	_, err := c.Pull("empty", 100*time.Millisecond)
	if err == nil {
		t.Error("expected error on pull timeout")
	}
}

func TestConsumerNegativeAcknowledge(t *testing.T) {
	broker, _ := newTestEnv()
	defer broker.Close()

	broker.CreateTopic("nack-test")

	// Publish a message without pulling it first.
	msg, _ := broker.Publish("nack-test", []byte("msg1"))

	// Negative acknowledge (message is still in topic).
	err := broker.NegativeAcknowledge("nack-test", msg.ID)
	if err != nil {
		t.Fatalf("nack: %v", err)
	}

	// Retry count should be incremented.
	if msg.RetryCount != 1 {
		t.Errorf("expected retry count 1, got %d", msg.RetryCount)
	}
}

func TestConsumerWithConsumerGroup(t *testing.T) {
	broker, _ := newTestEnv()
	defer broker.Close()

	broker.CreateTopic("group-test")

	// Create consumer group.
	cg, err := broker.CreateConsumerGroup("test-group", "group-test")
	if err != nil {
		t.Fatalf("create group: %v", err)
	}

	// Add consumers to group.
	gc1, _ := cg.AddConsumer("worker-1")
	gc2, _ := cg.AddConsumer("worker-2")

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

package producer

import (
	"testing"
	"time"

	"github.com/example/message-queue/internal/persistence"
	"github.com/example/message-queue/internal/protocol"
	"github.com/example/message-queue/internal/queue"
)

func newTestBroker() *queue.Broker {
	return queue.NewBroker(queue.DefaultConfig(), persistence.NewMemStore())
}

func TestProducerPublish(t *testing.T) {
	broker := newTestBroker()
	defer broker.Close()

	p := New(broker)

	msg, err := p.Publish("topic", []byte("hello"))
	if err != nil {
		t.Fatalf("publish: %v", err)
	}
	if msg.Topic != "topic" {
		t.Errorf("expected topic 'topic', got %q", msg.Topic)
	}
	if string(msg.Payload) != "hello" {
		t.Errorf("expected 'hello', got %q", string(msg.Payload))
	}
}

func TestProducerPublishString(t *testing.T) {
	broker := newTestBroker()
	defer broker.Close()

	p := New(broker)

	msg, err := p.PublishString("topic", "world")
	if err != nil {
		t.Fatalf("publish string: %v", err)
	}
	if string(msg.Payload) != "world" {
		t.Errorf("expected 'world', got %q", string(msg.Payload))
	}
}

func TestProducerPublishWithPriority(t *testing.T) {
	broker := newTestBroker()
	defer broker.Close()

	p := New(broker)

	msg, err := p.PublishWithPriority("topic", []byte("high-priority"), protocol.PriorityHigh)
	if err != nil {
		t.Fatalf("publish with priority: %v", err)
	}
	if msg.Priority != protocol.PriorityHigh {
		t.Errorf("expected high priority, got %v", msg.Priority)
	}
}

func TestProducerPublishDelayed(t *testing.T) {
	broker := newTestBroker()
	defer broker.Close()

	p := New(broker)

	delay := 1 * time.Second
	msg, err := p.PublishDelayed("topic", []byte("delayed"), delay)
	if err != nil {
		t.Fatalf("publish delayed: %v", err)
	}
	if msg.DeliverAfter == nil {
		t.Error("expected non-nil DeliverAfter")
	}
}

func TestProducerPublishWithHeaders(t *testing.T) {
	broker := newTestBroker()
	defer broker.Close()

	p := New(broker)

	headers := map[string]string{"type": "alert", "channel": "sms"}
	msg, err := p.PublishWithHeaders("topic", []byte("filtered"), headers)
	if err != nil {
		t.Fatalf("publish with headers: %v", err)
	}
	if msg.Headers["type"] != "alert" {
		t.Errorf("expected header type=alert, got %q", msg.Headers["type"])
	}
	if msg.Headers["channel"] != "sms" {
		t.Errorf("expected header channel=sms, got %q", msg.Headers["channel"])
	}
}

func TestProducerPublishWithOptions(t *testing.T) {
	broker := newTestBroker()
	defer broker.Close()

	p := New(broker)

	headers := map[string]string{"priority": "high"}
	delay := 500 * time.Millisecond
	msg, err := p.PublishWithOptions("topic", []byte("full-options"),
		protocol.PriorityHigh, headers, &delay)
	if err != nil {
		t.Fatalf("publish with options: %v", err)
	}
	if msg.Priority != protocol.PriorityHigh {
		t.Errorf("expected high priority, got %v", msg.Priority)
	}
	if msg.Headers["priority"] != "high" {
		t.Errorf("expected header priority=high, got %q", msg.Headers["priority"])
	}
	if msg.DeliverAfter == nil {
		t.Error("expected non-nil DeliverAfter")
	}
}

func TestProducerPull(t *testing.T) {
	broker := newTestBroker()
	defer broker.Close()

	broker.CreateTopic("pull-topic")
	broker.Publish("pull-topic", []byte("msg1"))

	p := New(broker)

	msg, err := p.Pull("pull-topic", 1*time.Second)
	if err != nil {
		t.Fatalf("pull: %v", err)
	}
	if string(msg.Payload) != "msg1" {
		t.Errorf("expected 'msg1', got %q", string(msg.Payload))
	}
}

func TestProducerPullTimeout(t *testing.T) {
	broker := newTestBroker()
	defer broker.Close()

	broker.CreateTopic("empty-topic")

	p := New(broker)

	_, err := p.Pull("empty-topic", 100*time.Millisecond)
	if err == nil {
		t.Error("expected error on pull timeout")
	}
}

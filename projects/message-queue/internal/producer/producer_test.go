package producer

import (
	"testing"

	"github.com/example/message-queue/internal/persistence"
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

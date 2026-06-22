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

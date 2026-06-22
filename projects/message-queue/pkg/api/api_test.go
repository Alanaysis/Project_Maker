package api

import (
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/example/message-queue/internal/consumer"
	"github.com/example/message-queue/internal/protocol"
)

func TestMessageQueueEndToEnd(t *testing.T) {
	cfg := DefaultConfig()
	mq, err := New(cfg)
	if err != nil {
		t.Fatalf("create mq: %v", err)
	}
	defer mq.Close()

	mq.CreateTopic("events")

	var received int32
	handler := func(msg *protocol.Message) error {
		atomic.AddInt32(&received, 1)
		return nil
	}

	consumer := mq.NewConsumer("c1", handler)
	defer consumer.Close()

	if err := consumer.Subscribe("events"); err != nil {
		t.Fatalf("subscribe: %v", err)
	}

	producer := mq.NewProducer()

	for i := 0; i < 5; i++ {
		_, err := producer.PublishString("events", "msg")
		if err != nil {
			t.Fatalf("publish %d: %v", i, err)
		}
	}

	// Wait for messages to be processed.
	time.Sleep(500 * time.Millisecond)

	if atomic.LoadInt32(&received) != 5 {
		t.Errorf("expected 5 received, got %d", atomic.LoadInt32(&received))
	}
}

func TestMessageQueueMultipleConsumers(t *testing.T) {
	cfg := DefaultConfig()
	mq, _ := New(cfg)
	defer mq.Close()

	mq.CreateTopic("shared")

	var mu sync.Mutex
	received := make(map[string]bool)

	handler := func(id string) consumer.Handler {
		return func(msg *protocol.Message) error {
			mu.Lock()
			received[id+"-"+msg.ID] = true
			mu.Unlock()
			return nil
		}
	}

	c1 := mq.NewConsumer("c1", handler("c1"))
	c2 := mq.NewConsumer("c2", handler("c2"))
	defer c1.Close()
	defer c2.Close()

	c1.Subscribe("shared")
	c2.Subscribe("shared")

	p := mq.NewProducer()
	p.PublishString("shared", "hello")

	time.Sleep(500 * time.Millisecond)

	// Fan-out: both consumers should receive the message.
	mu.Lock()
	count := len(received)
	mu.Unlock()

	if count != 2 {
		t.Errorf("expected 2 deliveries (fan-out), got %d", count)
	}
}

func TestMessageQueueTopics(t *testing.T) {
	cfg := DefaultConfig()
	mq, _ := New(cfg)
	defer mq.Close()

	mq.CreateTopic("a")
	mq.CreateTopic("b")

	topics := mq.Topics()
	if len(topics) != 2 {
		t.Errorf("expected 2 topics, got %d", len(topics))
	}
}

func TestMessageQueueTopicInfo(t *testing.T) {
	cfg := DefaultConfig()
	mq, _ := New(cfg)
	defer mq.Close()

	mq.CreateTopic("info")
	p := mq.NewProducer()
	p.PublishString("info", "m1")
	p.PublishString("info", "m2")

	msgs, subs, err := mq.TopicInfo("info")
	if err != nil {
		t.Fatalf("topic info: %v", err)
	}
	if msgs != 2 {
		t.Errorf("expected 2 messages, got %d", msgs)
	}
	if subs != 0 {
		t.Errorf("expected 0 subscribers, got %d", subs)
	}
}

func TestMessageQueueWithFileStore(t *testing.T) {
	dir := t.TempDir()

	cfg := Config{
		TopicCapacity:     100,
		SubscriberBufSize: 16,
		DataDir:           dir,
	}

	mq1, _ := New(cfg)
	p := mq1.NewProducer()
	p.PublishString("persist", "durable")
	mq1.Close()

	// Reopen and verify recovery.
	mq2, _ := New(cfg)
	defer mq2.Close()

	topic, err := mq2.GetTopic("persist")
	if err != nil {
		t.Fatalf("get topic after recover: %v", err)
	}
	msgs := topic.Messages()
	if len(msgs) != 1 {
		t.Errorf("expected 1 recovered message, got %d", len(msgs))
	}
	if string(msgs[0].Payload) != "durable" {
		t.Errorf("expected 'durable', got %q", string(msgs[0].Payload))
	}
}

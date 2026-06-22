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

func TestBrokerAcknowledge(t *testing.T) {
	broker := newTestBroker()
	defer broker.Close()

	msg, _ := broker.Publish("ack-test", []byte("data"))

	if err := broker.Acknowledge("ack-test", msg.ID); err != nil {
		t.Fatalf("ack: %v", err)
	}

	// Double ack should fail.
	if err := broker.Acknowledge("ack-test", msg.ID); err != protocol.ErrAlreadyAcknowledged {
		t.Errorf("expected ErrAlreadyAcknowledged, got %v", err)
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

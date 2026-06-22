package queue

import (
	"testing"
	"time"

	"github.com/example/message-queue/internal/protocol"
)

func TestTopicPublishAndMessages(t *testing.T) {
	topic := NewTopic("test", 100)

	msg := protocol.NewMessage("test", []byte("hello"))
	if err := topic.Publish(msg); err != nil {
		t.Fatalf("publish: %v", err)
	}

	msgs := topic.Messages()
	if len(msgs) != 1 {
		t.Fatalf("expected 1 message, got %d", len(msgs))
	}
	if string(msgs[0].Payload) != "hello" {
		t.Errorf("expected 'hello', got %q", string(msgs[0].Payload))
	}
}

func TestTopicCapacity(t *testing.T) {
	topic := NewTopic("cap", 2)

	topic.Publish(protocol.NewMessage("cap", []byte("a")))
	topic.Publish(protocol.NewMessage("cap", []byte("b")))

	err := topic.Publish(protocol.NewMessage("cap", []byte("c")))
	if err != protocol.ErrQueueFull {
		t.Errorf("expected ErrQueueFull, got %v", err)
	}
}

func TestTopicSubscriber(t *testing.T) {
	topic := NewTopic("sub", 100)

	sub := &Subscriber{
		ID: "c1",
		Ch: make(chan *protocol.Message, 10),
	}

	if err := topic.AddSubscriber(sub); err != nil {
		t.Fatalf("add subscriber: %v", err)
	}
	if topic.SubscriberCount() != 1 {
		t.Errorf("expected 1 subscriber, got %d", topic.SubscriberCount())
	}

	// Duplicate should fail.
	if err := topic.AddSubscriber(sub); err != protocol.ErrSubscriptionExists {
		t.Errorf("expected ErrSubscriptionExists, got %v", err)
	}

	topic.RemoveSubscriber("c1")
	if topic.SubscriberCount() != 0 {
		t.Errorf("expected 0 subscribers after remove, got %d", topic.SubscriberCount())
	}
}

func TestTopicFanOut(t *testing.T) {
	topic := NewTopic("fan", 100)

	sub1 := &Subscriber{ID: "s1", Ch: make(chan *protocol.Message, 10)}
	sub2 := &Subscriber{ID: "s2", Ch: make(chan *protocol.Message, 10)}

	topic.AddSubscriber(sub1)
	topic.AddSubscriber(sub2)

	msg := protocol.NewMessage("fan", []byte("broadcast"))
	topic.Publish(msg)

	// Both subscribers should receive the message.
	select {
	case m := <-sub1.Ch:
		if string(m.Payload) != "broadcast" {
			t.Errorf("sub1 got %q", string(m.Payload))
		}
	case <-time.After(time.Second):
		t.Error("sub1 timeout")
	}

	select {
	case m := <-sub2.Ch:
		if string(m.Payload) != "broadcast" {
			t.Errorf("sub2 got %q", string(m.Payload))
		}
	case <-time.After(time.Second):
		t.Error("sub2 timeout")
	}
}

func TestTopicPendingCount(t *testing.T) {
	topic := NewTopic("pending", 100)

	msg1 := protocol.NewMessage("pending", []byte("a"))
	msg2 := protocol.NewMessage("pending", []byte("b"))
	topic.Publish(msg1)
	topic.Publish(msg2)

	if topic.PendingCount() != 2 {
		t.Errorf("expected 2 pending, got %d", topic.PendingCount())
	}

	msg1.MarkAcknowledged()
	// PendingCount reads under RLock so we need to account for the pointer.
	if topic.PendingCount() != 1 {
		t.Errorf("expected 1 pending after ack, got %d", topic.PendingCount())
	}
}

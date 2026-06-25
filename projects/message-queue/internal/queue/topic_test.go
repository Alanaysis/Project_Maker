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

func TestTopicPriorityOrdering(t *testing.T) {
	topic := NewTopic("priority", 100)

	// Publish messages with different priorities.
	low := protocol.NewMessage("priority", []byte("low")).WithPriority(protocol.PriorityLow)
	normal := protocol.NewMessage("priority", []byte("normal")).WithPriority(protocol.PriorityNormal)
	high := protocol.NewMessage("priority", []byte("high")).WithPriority(protocol.PriorityHigh)

	topic.Publish(low)
	topic.Publish(normal)
	topic.Publish(high)

	msgs := topic.Messages()
	if len(msgs) != 3 {
		t.Fatalf("expected 3 messages, got %d", len(msgs))
	}

	// Should be ordered by priority (high first).
	if string(msgs[0].Payload) != "high" {
		t.Errorf("expected first message to be 'high', got %q", string(msgs[0].Payload))
	}
	if string(msgs[1].Payload) != "normal" {
		t.Errorf("expected second message to be 'normal', got %q", string(msgs[1].Payload))
	}
	if string(msgs[2].Payload) != "low" {
		t.Errorf("expected third message to be 'low', got %q", string(msgs[2].Payload))
	}
}

func TestTopicDelayedMessages(t *testing.T) {
	topic := NewTopic("delayed", 100)

	// Immediate message.
	immediate := protocol.NewMessage("delayed", []byte("now"))

	// Delayed message.
	delayed := protocol.NewMessage("delayed", []byte("later")).WithDelay(1 * time.Second)

	topic.Publish(immediate)
	topic.Publish(delayed)

	// Only immediate message should be ready.
	ready := topic.GetReadyMessages()
	if len(ready) != 1 {
		t.Errorf("expected 1 ready message, got %d", len(ready))
	}

	// Wait for delayed message to become ready.
	time.Sleep(1100 * time.Millisecond)

	ready = topic.GetReadyMessages()
	if len(ready) != 2 {
		t.Errorf("expected 2 ready messages after delay, got %d", len(ready))
	}
}

func TestTopicRemoveMessage(t *testing.T) {
	topic := NewTopic("remove", 100)

	msg := protocol.NewMessage("remove", []byte("test"))
	topic.Publish(msg)

	if !topic.RemoveMessage(msg.ID) {
		t.Error("expected message to be removed")
	}

	if topic.RemoveMessage("nonexistent") {
		t.Error("expected false for nonexistent message")
	}

	msgs := topic.Messages()
	if len(msgs) != 0 {
		t.Errorf("expected 0 messages after remove, got %d", len(msgs))
	}
}

func TestTopicFilter(t *testing.T) {
	topic := NewTopic("filtered", 100)
	topic.SetFilter(map[string]string{"channel": "sms"})

	sub := &Subscriber{ID: "s1", Ch: make(chan *protocol.Message, 10)}
	topic.AddSubscriber(sub)

	// Message matching filter should be delivered.
	matching := protocol.NewMessage("filtered", []byte("sms-msg")).
		WithHeader("channel", "sms")
	topic.Publish(matching)

	// Message not matching filter should be dropped.
	notMatching := protocol.NewMessage("filtered", []byte("email-msg")).
		WithHeader("channel", "email")
	topic.Publish(notMatching)

	select {
	case m := <-sub.Ch:
		if string(m.Payload) != "sms-msg" {
			t.Errorf("expected 'sms-msg', got %q", string(m.Payload))
		}
	case <-time.After(time.Second):
		t.Error("timeout waiting for filtered message")
	}

	// Should have only 1 message in topic (the matching one).
	msgs := topic.Messages()
	if len(msgs) != 1 {
		t.Errorf("expected 1 message after filtering, got %d", len(msgs))
	}
}

func TestTopicSubscriberFilter(t *testing.T) {
	topic := NewTopic("sub-filter", 100)

	// Subscriber with filter.
	sub := &Subscriber{
		ID:     "s1",
		Ch:     make(chan *protocol.Message, 10),
		filter: map[string]string{"type": "alert"},
	}
	topic.AddSubscriber(sub)

	// Matching message.
	alert := protocol.NewMessage("sub-filter", []byte("alert")).
		WithHeader("type", "alert")
	topic.Publish(alert)

	// Non-matching message.
	info := protocol.NewMessage("sub-filter", []byte("info")).
		WithHeader("type", "info")
	topic.Publish(info)

	select {
	case m := <-sub.Ch:
		if string(m.Payload) != "alert" {
			t.Errorf("expected 'alert', got %q", string(m.Payload))
		}
	case <-time.After(time.Second):
		t.Error("timeout waiting for filtered message")
	}
}

func TestQueueTopicMode(t *testing.T) {
	topic := NewQueueTopic("queue", 100)

	if topic.Mode != ModeQueue {
		t.Errorf("expected queue mode, got %v", topic.Mode)
	}

	sub1 := &Subscriber{ID: "s1", Ch: make(chan *protocol.Message, 10)}
	sub2 := &Subscriber{ID: "s2", Ch: make(chan *protocol.Message, 10)}

	topic.AddSubscriber(sub1)
	topic.AddSubscriber(sub2)

	msg := protocol.NewMessage("queue", []byte("point-to-point"))
	topic.Publish(msg)

	// Only one subscriber should receive the message.
	received := 0
	timeout := time.After(500 * time.Millisecond)

	select {
	case <-sub1.Ch:
		received++
	case <-timeout:
	}

	select {
	case <-sub2.Ch:
		received++
	case <-timeout:
	}

	if received != 1 {
		t.Errorf("expected exactly 1 subscriber to receive message, got %d", received)
	}
}

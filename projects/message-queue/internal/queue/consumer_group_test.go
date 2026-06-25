package queue

import (
	"sync"
	"testing"
	"time"

	"github.com/example/message-queue/internal/protocol"
)

func TestConsumerGroupAddConsumer(t *testing.T) {
	cg := NewConsumerGroup("test-group", "test-topic")

	gc, err := cg.AddConsumer("consumer-1")
	if err != nil {
		t.Fatalf("add consumer: %v", err)
	}

	if gc.ID != "consumer-1" {
		t.Errorf("expected consumer ID 'consumer-1', got %q", gc.ID)
	}
	if !gc.active {
		t.Error("expected consumer to be active")
	}

	if cg.ConsumerCount() != 1 {
		t.Errorf("expected 1 consumer, got %d", cg.ConsumerCount())
	}
}

func TestConsumerGroupDuplicateConsumer(t *testing.T) {
	cg := NewConsumerGroup("test-group", "test-topic")

	cg.AddConsumer("consumer-1")
	_, err := cg.AddConsumer("consumer-1")

	if err != protocol.ErrSubscriptionExists {
		t.Errorf("expected ErrSubscriptionExists, got %v", err)
	}
}

func TestConsumerGroupRemoveConsumer(t *testing.T) {
	cg := NewConsumerGroup("test-group", "test-topic")

	cg.AddConsumer("consumer-1")
	cg.RemoveConsumer("consumer-1")

	if cg.ConsumerCount() != 0 {
		t.Errorf("expected 0 consumers after remove, got %d", cg.ConsumerCount())
	}
}

func TestConsumerGroupDeliver(t *testing.T) {
	cg := NewConsumerGroup("test-group", "test-topic")

	gc1, _ := cg.AddConsumer("consumer-1")
	gc2, _ := cg.AddConsumer("consumer-2")

	msg := protocol.NewMessage("test-topic", []byte("test-msg"))

	// Deliver message to group.
	err := cg.Deliver(msg)
	if err != nil {
		t.Fatalf("deliver: %v", err)
	}

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

func TestConsumerGroupRoundRobin(t *testing.T) {
	cg := NewConsumerGroup("test-group", "test-topic")

	gc1, _ := cg.AddConsumer("consumer-1")
	gc2, _ := cg.AddConsumer("consumer-2")

	// Deliver multiple messages.
	for i := 0; i < 4; i++ {
		msg := protocol.NewMessage("test-topic", []byte("msg"))
		cg.Deliver(msg)
	}

	// Count messages per consumer.
	count1 := 0
	count2 := 0

	for i := 0; i < 4; i++ {
		select {
		case <-gc1.Ch:
			count1++
		case <-gc2.Ch:
			count2++
		case <-time.After(100 * time.Millisecond):
		}
	}

	// With round-robin, each consumer should get 2 messages.
	if count1 != 2 {
		t.Errorf("expected consumer-1 to get 2 messages, got %d", count1)
	}
	if count2 != 2 {
		t.Errorf("expected consumer-2 to get 2 messages, got %d", count2)
	}
}

func TestConsumerGroupEmptyGroup(t *testing.T) {
	cg := NewConsumerGroup("test-group", "test-topic")

	msg := protocol.NewMessage("test-topic", []byte("test-msg"))
	err := cg.Deliver(msg)

	if err != protocol.ErrNoAvailableConsumer {
		t.Errorf("expected ErrNoAvailableConsumer, got %v", err)
	}
}

func TestConsumerGroupInactiveConsumer(t *testing.T) {
	cg := NewConsumerGroup("test-group", "test-topic")

	gc1, _ := cg.AddConsumer("consumer-1")
	cg.AddConsumer("consumer-2")

	// Deactivate consumer-1.
	gc1.mu.Lock()
	gc1.active = false
	gc1.mu.Unlock()

	msg := protocol.NewMessage("test-topic", []byte("test-msg"))
	err := cg.Deliver(msg)

	if err != nil {
		t.Fatalf("deliver: %v", err)
	}

	// Consumer-2 should receive the message.
	select {
	case <-gc1.Ch:
		t.Error("inactive consumer should not receive message")
	case <-time.After(100 * time.Millisecond):
		// Expected: no message for inactive consumer.
	}
}

func TestConsumerGroupGetConsumer(t *testing.T) {
	cg := NewConsumerGroup("test-group", "test-topic")

	cg.AddConsumer("consumer-1")

	gc, ok := cg.GetConsumer("consumer-1")
	if !ok {
		t.Fatal("expected to find consumer-1")
	}
	if gc.ID != "consumer-1" {
		t.Errorf("expected consumer ID 'consumer-1', got %q", gc.ID)
	}

	_, ok = cg.GetConsumer("nonexistent")
	if ok {
		t.Error("expected false for nonexistent consumer")
	}
}

func TestConsumerGroupActiveConsumerCount(t *testing.T) {
	cg := NewConsumerGroup("test-group", "test-topic")

	gc1, _ := cg.AddConsumer("consumer-1")
	cg.AddConsumer("consumer-2")

	if cg.ActiveConsumerCount() != 2 {
		t.Errorf("expected 2 active consumers, got %d", cg.ActiveConsumerCount())
	}

	// Deactivate one consumer.
	gc1.mu.Lock()
	gc1.active = false
	gc1.mu.Unlock()

	if cg.ActiveConsumerCount() != 1 {
		t.Errorf("expected 1 active consumer, got %d", cg.ActiveConsumerCount())
	}
}

func TestConsumerGroupClose(t *testing.T) {
	cg := NewConsumerGroup("test-group", "test-topic")

	gc1, _ := cg.AddConsumer("consumer-1")
	gc2, _ := cg.AddConsumer("consumer-2")

	cg.Close()

	if cg.ConsumerCount() != 0 {
		t.Errorf("expected 0 consumers after close, got %d", cg.ConsumerCount())
	}

	// Channels should be closed.
	select {
	case _, ok := <-gc1.Ch:
		if ok {
			t.Error("expected closed channel for consumer-1")
		}
	case <-time.After(time.Second):
		t.Error("timeout waiting for channel close")
	}

	select {
	case _, ok := <-gc2.Ch:
		if ok {
			t.Error("expected closed channel for consumer-2")
		}
	case <-time.After(time.Second):
		t.Error("timeout waiting for channel close")
	}
}

func TestConsumerGroupConcurrentDeliver(t *testing.T) {
	cg := NewConsumerGroup("test-group", "test-topic")

	gc1, _ := cg.AddConsumer("consumer-1")
	gc2, _ := cg.AddConsumer("consumer-2")

	var wg sync.WaitGroup
	numMessages := 100

	wg.Add(numMessages)
	for i := 0; i < numMessages; i++ {
		go func() {
			defer wg.Done()
			msg := protocol.NewMessage("test-topic", []byte("msg"))
			cg.Deliver(msg)
		}()
	}
	wg.Wait()

	// Count total received messages.
	total := 0
	done := false
	for !done {
		select {
		case <-gc1.Ch:
			total++
		case <-gc2.Ch:
			total++
		default:
			done = true
		}
	}

	if total != numMessages {
		t.Errorf("expected %d messages, got %d", numMessages, total)
	}
}

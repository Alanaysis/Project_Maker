package queue

import (
	"testing"

	"github.com/example/message-queue/internal/protocol"
)

func TestDeadLetterQueueAdd(t *testing.T) {
	dlq := NewDeadLetterQueue("test-dlq", 100)

	msg := protocol.NewMessage("test", []byte("dead-msg"))
	err := dlq.Add(msg)

	if err != nil {
		t.Fatalf("add: %v", err)
	}

	if dlq.Count() != 1 {
		t.Errorf("expected 1 message in DLQ, got %d", dlq.Count())
	}

	if msg.Status != protocol.StatusDeadLetter {
		t.Errorf("expected dead_letter status, got %v", msg.Status)
	}
}

func TestDeadLetterQueueCapacity(t *testing.T) {
	dlq := NewDeadLetterQueue("test-dlq", 2)

	dlq.Add(protocol.NewMessage("test", []byte("msg1")))
	dlq.Add(protocol.NewMessage("test", []byte("msg2")))

	err := dlq.Add(protocol.NewMessage("test", []byte("msg3")))
	if err != protocol.ErrQueueFull {
		t.Errorf("expected ErrQueueFull, got %v", err)
	}
}

func TestDeadLetterQueueMessages(t *testing.T) {
	dlq := NewDeadLetterQueue("test-dlq", 100)

	msg1 := protocol.NewMessage("test", []byte("msg1"))
	msg2 := protocol.NewMessage("test", []byte("msg2"))

	dlq.Add(msg1)
	dlq.Add(msg2)

	msgs := dlq.Messages()
	if len(msgs) != 2 {
		t.Errorf("expected 2 messages, got %d", len(msgs))
	}
}

func TestDeadLetterQueuePeek(t *testing.T) {
	dlq := NewDeadLetterQueue("test-dlq", 100)

	// Empty queue.
	if dlq.Peek() != nil {
		t.Error("expected nil for empty DLQ peek")
	}

	msg := protocol.NewMessage("test", []byte("test-msg"))
	dlq.Add(msg)

	peeked := dlq.Peek()
	if peeked == nil {
		t.Fatal("expected non-nil peek")
	}
	if peeked.ID != msg.ID {
		t.Errorf("expected message ID %s, got %s", msg.ID, peeked.ID)
	}

	// Peek should not remove message.
	if dlq.Count() != 1 {
		t.Errorf("expected 1 message after peek, got %d", dlq.Count())
	}
}

func TestDeadLetterQueuePop(t *testing.T) {
	dlq := NewDeadLetterQueue("test-dlq", 100)

	// Empty queue.
	if dlq.Pop() != nil {
		t.Error("expected nil for empty DLQ pop")
	}

	msg := protocol.NewMessage("test", []byte("test-msg"))
	dlq.Add(msg)

	popped := dlq.Pop()
	if popped == nil {
		t.Fatal("expected non-nil pop")
	}
	if popped.ID != msg.ID {
		t.Errorf("expected message ID %s, got %s", msg.ID, popped.ID)
	}

	// Pop should remove message.
	if dlq.Count() != 0 {
		t.Errorf("expected 0 messages after pop, got %d", dlq.Count())
	}
}

func TestDeadLetterQueueRetryMessage(t *testing.T) {
	dlq := NewDeadLetterQueue("test-dlq", 100)

	msg := protocol.NewMessage("test", []byte("test-msg"))
	msg.MaxRetries = 3
	msg.RetryCount = 3
	dlq.Add(msg)

	retried := dlq.RetryMessage(msg.ID)
	if retried == nil {
		t.Fatal("expected non-nil retried message")
	}

	if retried.Status != protocol.StatusPending {
		t.Errorf("expected pending status after retry, got %v", retried.Status)
	}
	if retried.RetryCount != 4 {
		t.Errorf("expected retry count 4, got %d", retried.RetryCount)
	}

	// Message should be removed from DLQ.
	if dlq.Count() != 0 {
		t.Errorf("expected 0 messages after retry, got %d", dlq.Count())
	}
}

func TestDeadLetterQueueRetryNonexistent(t *testing.T) {
	dlq := NewDeadLetterQueue("test-dlq", 100)

	retried := dlq.RetryMessage("nonexistent")
	if retried != nil {
		t.Error("expected nil for nonexistent message retry")
	}
}

func TestDeadLetterQueueClear(t *testing.T) {
	dlq := NewDeadLetterQueue("test-dlq", 100)

	dlq.Add(protocol.NewMessage("test", []byte("msg1")))
	dlq.Add(protocol.NewMessage("test", []byte("msg2")))

	dlq.Clear()

	if dlq.Count() != 0 {
		t.Errorf("expected 0 messages after clear, got %d", dlq.Count())
	}
}

func TestDeadLetterQueueName(t *testing.T) {
	dlq := NewDeadLetterQueue("test-dlq", 100)

	if dlq.Name() != "test-dlq" {
		t.Errorf("expected name 'test-dlq', got %q", dlq.Name())
	}
}

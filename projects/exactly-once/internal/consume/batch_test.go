package consume

import (
	"errors"
	"fmt"
	"sync/atomic"
	"testing"

	"github.com/anthropic/exactly-once/internal/message"
)

func TestBatchConsumerBasic(t *testing.T) {
	bc := NewBatchConsumer(func(msg *ConsumedMessage) error {
		return nil
	}, WithBatchSize(3))

	for i := 0; i < 3; i++ {
		msg := message.New(fmt.Sprintf("msg-%d", i), []byte("data"))
		full := bc.Receive(msg)
		if i < 2 && full {
			t.Error("batch should not be full until 3 messages")
		}
		if i == 2 && !full {
			t.Error("batch should be full after 3 messages")
		}
	}

	err := bc.ProcessBatch()
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	stats := bc.StatsSnapshot()
	if stats.Received != 3 {
		t.Errorf("expected 3 received, got %d", stats.Received)
	}
	if stats.Acked != 3 {
		t.Errorf("expected 3 acked, got %d", stats.Acked)
	}
	if stats.Batches != 1 {
		t.Errorf("expected 1 batch, got %d", stats.Batches)
	}
}

func TestBatchConsumerPartialFailure(t *testing.T) {
	var callCount int32
	bc := NewBatchConsumer(func(msg *ConsumedMessage) error {
		count := atomic.AddInt32(&callCount, 1)
		if count == 2 {
			return errors.New("second message fails")
		}
		return nil
	}, WithBatchSize(3))

	for i := 0; i < 3; i++ {
		msg := message.New(fmt.Sprintf("msg-%d", i), []byte("data"))
		bc.Receive(msg)
	}

	err := bc.ProcessBatch()
	if err == nil {
		t.Fatal("expected error for partial batch failure")
	}

	stats := bc.StatsSnapshot()
	if stats.Acked != 2 {
		t.Errorf("expected 2 acked, got %d", stats.Acked)
	}
	if stats.Failed != 1 {
		t.Errorf("expected 1 failed, got %d", stats.Failed)
	}
}

func TestBatchConsumerEmpty(t *testing.T) {
	bc := NewBatchConsumer(func(msg *ConsumedMessage) error {
		return nil
	})

	err := bc.ProcessBatch()
	if err != nil {
		t.Fatalf("unexpected error on empty batch: %v", err)
	}

	stats := bc.StatsSnapshot()
	if stats.Batches != 0 {
		t.Errorf("expected 0 batches, got %d", stats.Batches)
	}
}

func TestBatchConsumerPendingSize(t *testing.T) {
	bc := NewBatchConsumer(func(msg *ConsumedMessage) error {
		return nil
	}, WithBatchSize(10))

	for i := 0; i < 5; i++ {
		msg := message.New(fmt.Sprintf("msg-%d", i), []byte("data"))
		bc.Receive(msg)
	}

	if bc.PendingSize() != 5 {
		t.Errorf("expected 5 pending, got %d", bc.PendingSize())
	}
}

func TestBatchConsumerFlush(t *testing.T) {
	bc := NewBatchConsumer(func(msg *ConsumedMessage) error {
		return nil
	}, WithBatchSize(10))

	for i := 0; i < 5; i++ {
		msg := message.New(fmt.Sprintf("msg-%d", i), []byte("data"))
		bc.Receive(msg)
	}

	batch := bc.Flush()
	if len(batch) != 5 {
		t.Errorf("expected 5 flushed, got %d", len(batch))
	}
	if bc.PendingSize() != 0 {
		t.Errorf("expected 0 pending after flush, got %d", bc.PendingSize())
	}
}

func TestBatchConsumerCallbacks(t *testing.T) {
	var ackCalled, nackCalled bool

	bc := NewBatchConsumer(func(msg *ConsumedMessage) error {
		return errors.New("fail")
	},
		WithBatchSize(2),
		WithOnBatchAck(func(msgs []*ConsumedMessage) { ackCalled = true }),
		WithOnBatchNack(func(msgs []*ConsumedMessage, err error) { nackCalled = true }),
	)

	msg1 := message.New("msg-001", []byte("data"))
	bc.Receive(msg1)
	msg2 := message.New("msg-002", []byte("data"))
	bc.Receive(msg2)

	bc.ProcessBatch()

	if ackCalled {
		t.Error("ack callback should not be called for failed batch")
	}
	if !nackCalled {
		t.Error("nack callback should be called for failed batch")
	}
}

func TestBatchConsumerManualAckNack(t *testing.T) {
	bc := NewBatchConsumer(func(msg *ConsumedMessage) error {
		return nil
	})

	var msgs []*ConsumedMessage
	for i := 0; i < 3; i++ {
		msg := message.New(fmt.Sprintf("msg-%d", i), []byte("data"))
		cm := &ConsumedMessage{
			Message:   msg,
			AckStatus: AckStatusPending,
		}
		msgs = append(msgs, cm)
	}

	bc.AckBatch(msgs)
	for _, cm := range msgs {
		if cm.AckStatus != AckStatusAcked {
			t.Errorf("expected ACKED, got %s", cm.AckStatus)
		}
	}

	// Nack a different batch
	var nackedMsgs []*ConsumedMessage
	for i := 10; i < 13; i++ {
		msg := message.New(fmt.Sprintf("nack-%d", i), []byte("data"))
		cm := &ConsumedMessage{
			Message:   msg,
			AckStatus: AckStatusPending,
		}
		nackedMsgs = append(nackedMsgs, cm)
	}

	bc.NackBatch(nackedMsgs, errors.New("batch error"))
	for _, cm := range nackedMsgs {
		if cm.AckStatus != AckStatusNacked {
			t.Errorf("expected NACKED, got %s", cm.AckStatus)
		}
	}
}

func TestBatchConsumerAverageBatchTime(t *testing.T) {
	bc := NewBatchConsumer(func(msg *ConsumedMessage) error {
		return nil
	}, WithBatchSize(2))

	for i := 0; i < 2; i++ {
		msg := message.New(fmt.Sprintf("msg-%d", i), []byte("data"))
		bc.Receive(msg)
	}
	bc.ProcessBatch()

	avg := bc.AverageBatchTime()
	if avg <= 0 {
		t.Error("expected positive average batch time")
	}
}

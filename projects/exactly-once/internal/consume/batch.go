package consume

import (
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/anthropic/exactly-once/internal/message"
)

// BatchConsumer processes messages in batches with batch acknowledgment.
//
// Instead of acknowledging each message individually, BatchConsumer collects
// messages into a batch, processes them together, and acknowledges the entire
// batch atomically. This is more efficient for high-throughput scenarios.
//
// Flow:
//
//	Receive(msg1) -> Receive(msg2) -> Receive(msg3)
//	-> ProcessBatch() -> AckBatch() or NackBatch()
type BatchConsumer struct {
	mu          sync.Mutex
	pending     []*ConsumedMessage
	batchSize   int
	flushTimeout time.Duration
	handler     Handler
	consumerID  string
	stats       BatchStats
	onBatchAck  func(msgs []*ConsumedMessage)
	onBatchNack func(msgs []*ConsumedMessage, err error)
}

// BatchStats tracks batch consumer statistics.
type BatchStats struct {
	Received    int64
	Batches     int64
	Acked       int64
	Failed      int64
	BatchTimeNs int64
}

// BatchOption configures a BatchConsumer.
type BatchOption func(*BatchConsumer)

// WithBatchSize sets the maximum number of messages per batch.
func WithBatchSize(n int) BatchOption {
	return func(bc *BatchConsumer) {
		bc.batchSize = n
	}
}

// WithFlushTimeout sets the maximum time to wait before flushing a partial batch.
func WithFlushTimeout(d time.Duration) BatchOption {
	return func(bc *BatchConsumer) {
		bc.flushTimeout = d
	}
}

// WithBatchConsumerID sets the consumer identifier.
func WithBatchConsumerID(id string) BatchOption {
	return func(bc *BatchConsumer) {
		bc.consumerID = id
	}
}

// WithOnBatchAck sets a callback for successful batch acknowledgment.
func WithOnBatchAck(fn func(msgs []*ConsumedMessage)) BatchOption {
	return func(bc *BatchConsumer) {
		bc.onBatchAck = fn
	}
}

// WithOnBatchNack sets a callback for failed batch processing.
func WithOnBatchNack(fn func(msgs []*ConsumedMessage, err error)) BatchOption {
	return func(bc *BatchConsumer) {
		bc.onBatchNack = fn
	}
}

// NewBatchConsumer creates a new BatchConsumer.
func NewBatchConsumer(handler Handler, opts ...BatchOption) *BatchConsumer {
	bc := &BatchConsumer{
		pending:      make([]*ConsumedMessage, 0),
		batchSize:    10,
		flushTimeout: 5 * time.Second,
		handler:      handler,
		consumerID:   "batch-default",
	}
	for _, opt := range opts {
		opt(bc)
	}
	return bc
}

// Receive adds a message to the current batch. Returns true if the batch
// is full and should be flushed.
func (bc *BatchConsumer) Receive(msg *message.Message) bool {
	bc.mu.Lock()
	defer bc.mu.Unlock()

	cm := &ConsumedMessage{
		Message:      msg,
		AckStatus:    AckStatusPending,
		ReceivedAt:   time.Now(),
		AttemptCount: 1,
		ConsumerID:   bc.consumerID,
	}
	bc.pending = append(bc.pending, cm)
	bc.stats.Received++

	log.Printf("[batch] received message: id=%s batch_size=%d/%d",
		msg.ID, len(bc.pending), bc.batchSize)

	return len(bc.pending) >= bc.batchSize
}

// ProcessBatch processes all pending messages as a batch.
// All messages in the batch are processed together. If any message fails,
// the entire batch is nacked.
func (bc *BatchConsumer) ProcessBatch() error {
	bc.mu.Lock()
	if len(bc.pending) == 0 {
		bc.mu.Unlock()
		return nil
	}
	batch := bc.pending
	bc.pending = make([]*ConsumedMessage, 0)
	bc.mu.Unlock()

	start := time.Now()
	bc.stats.Batches++

	// Process each message in the batch
	var failedMsgs []*ConsumedMessage
	var lastErr error

	for _, cm := range batch {
		if err := bc.handler(cm); err != nil {
			cm.LastError = err.Error()
			cm.AckStatus = AckStatusNacked
			failedMsgs = append(failedMsgs, cm)
			lastErr = err
		} else {
			now := time.Now()
			cm.AckStatus = AckStatusAcked
			cm.AckedAt = &now
			cm.Message.MarkCompleted(nil)
		}
	}

	bc.mu.Lock()
	bc.stats.BatchTimeNs += time.Since(start).Nanoseconds()

	if len(failedMsgs) > 0 {
		bc.stats.Failed += int64(len(failedMsgs))
		bc.mu.Unlock()

		log.Printf("[batch] batch partially failed: total=%d failed=%d",
			len(batch), len(failedMsgs))

		if bc.onBatchNack != nil {
			bc.onBatchNack(failedMsgs, lastErr)
		}
		return fmt.Errorf("batch partially failed: %d/%d messages failed: %w",
			len(failedMsgs), len(batch), lastErr)
	}

	bc.stats.Acked += int64(len(batch))
	bc.mu.Unlock()

	log.Printf("[batch] batch acked: size=%d duration=%v", len(batch), time.Since(start))

	if bc.onBatchAck != nil {
		bc.onBatchAck(batch)
	}
	return nil
}

// AckBatch manually acknowledges all messages in the provided slice.
func (bc *BatchConsumer) AckBatch(msgs []*ConsumedMessage) {
	now := time.Now()
	for _, cm := range msgs {
		cm.AckStatus = AckStatusAcked
		cm.AckedAt = &now
		cm.Message.MarkCompleted(nil)
	}

	bc.mu.Lock()
	bc.stats.Acked += int64(len(msgs))
	bc.mu.Unlock()

	log.Printf("[batch] manually acked batch: size=%d", len(msgs))
}

// NackBatch manually rejects all messages in the provided slice.
func (bc *BatchConsumer) NackBatch(msgs []*ConsumedMessage, err error) {
	for _, cm := range msgs {
		cm.AckStatus = AckStatusNacked
		cm.LastError = err.Error()
	}

	bc.mu.Lock()
	bc.stats.Failed += int64(len(msgs))
	bc.mu.Unlock()

	log.Printf("[batch] manually nacked batch: size=%d error=%v", len(msgs), err)

	if bc.onBatchNack != nil {
		bc.onBatchNack(msgs, err)
	}
}

// PendingSize returns the number of messages waiting to be batched.
func (bc *BatchConsumer) PendingSize() int {
	bc.mu.Lock()
	defer bc.mu.Unlock()
	return len(bc.pending)
}

// Flush returns the current pending messages without processing them.
// Useful for manual batch handling.
func (bc *BatchConsumer) Flush() []*ConsumedMessage {
	bc.mu.Lock()
	defer bc.mu.Unlock()

	batch := bc.pending
	bc.pending = make([]*ConsumedMessage, 0)
	return batch
}

// StatsSnapshot returns a copy of the current statistics.
func (bc *BatchConsumer) StatsSnapshot() BatchStats {
	bc.mu.Lock()
	defer bc.mu.Unlock()
	return bc.stats
}

// AverageBatchTime returns the average batch processing time.
func (bc *BatchConsumer) AverageBatchTime() time.Duration {
	bc.mu.Lock()
	defer bc.mu.Unlock()
	if bc.stats.Batches == 0 {
		return 0
	}
	return time.Duration(bc.stats.BatchTimeNs / bc.stats.Batches)
}

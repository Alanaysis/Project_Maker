// Package consume implements consumption acknowledgment for exactly-once processing.
//
// The Consumer provides manual acknowledgment, batch acknowledgment, and
// automatic retry mechanisms. This is essential for at-least-once delivery
// combined with idempotent processing to achieve exactly-once semantics.
//
// Consumption flow:
//
//	Message received -> Process -> Acknowledge (or Retry)
//
// Three acknowledgment modes:
//   - Manual: Caller explicitly calls Ack/Nack after processing
//   - Batch: Multiple messages are acknowledged together
//   - Auto-retry: Failed messages are automatically retried with backoff
package consume

import (
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/anthropic/exactly-once/internal/message"
)

// AckStatus represents the acknowledgment status of a consumed message.
type AckStatus int

const (
	// AckStatusPending means the message has been received but not yet acknowledged.
	AckStatusPending AckStatus = iota
	// AckStatusAcked means the message has been successfully processed and acknowledged.
	AckStatusAcked
	// AckStatusNacked means the message processing failed and it should be retried.
	AckStatusNacked
	// AckStatusRejected means the message has been permanently rejected (dead letter).
	AckStatusRejected
)

// String returns a human-readable representation of the ack status.
func (s AckStatus) String() string {
	switch s {
	case AckStatusPending:
		return "PENDING"
	case AckStatusAcked:
		return "ACKED"
	case AckStatusNacked:
		return "NACKED"
	case AckStatusRejected:
		return "REJECTED"
	default:
		return fmt.Sprintf("UNKNOWN(%d)", int(s))
	}
}

// ConsumedMessage wraps a message with consumption tracking metadata.
type ConsumedMessage struct {
	// Message is the underlying message.
	Message *message.Message
	// AckStatus is the current acknowledgment status.
	AckStatus AckStatus
	// ReceivedAt is when the message was received by the consumer.
	ReceivedAt time.Time
	// AckedAt is when the message was acknowledged (nil if not yet).
	AckedAt *time.Time
	// AttemptCount tracks how many times this message has been consumed.
	AttemptCount int
	// LastError stores the last processing error.
	LastError string
	// ConsumerID identifies which consumer processed this message.
	ConsumerID string
}

// Handler processes a consumed message and returns an error if processing fails.
type Handler func(msg *ConsumedMessage) error

// RetryPolicy defines how failed messages are retried.
type RetryPolicy struct {
	// MaxRetries is the maximum number of retry attempts.
	MaxRetries int
	// InitialBackoff is the initial delay before the first retry.
	InitialBackoff time.Duration
	// MaxBackoff is the maximum delay between retries.
	MaxBackoff time.Duration
	// BackoffMultiplier is the factor by which the backoff increases.
	BackoffMultiplier float64
}

// DefaultRetryPolicy returns a sensible default retry policy.
func DefaultRetryPolicy() RetryPolicy {
	return RetryPolicy{
		MaxRetries:        3,
		InitialBackoff:    100 * time.Millisecond,
		MaxBackoff:        10 * time.Second,
		BackoffMultiplier: 2.0,
	}
}

// Backoff calculates the backoff duration for the given attempt (0-indexed).
func (rp RetryPolicy) Backoff(attempt int) time.Duration {
	backoff := rp.InitialBackoff
	for i := 0; i < attempt; i++ {
		backoff = time.Duration(float64(backoff) * rp.BackoffMultiplier)
		if backoff > rp.MaxBackoff {
			return rp.MaxBackoff
		}
	}
	return backoff
}

// Consumer manages message consumption with acknowledgment.
type Consumer struct {
	mu          sync.RWMutex
	messages    map[string]*ConsumedMessage
	handler     Handler
	retryPolicy RetryPolicy
	consumerID  string
	stats       Stats
	onAck       func(msg *ConsumedMessage)
	onNack      func(msg *ConsumedMessage, err error)
	onReject    func(msg *ConsumedMessage)
}

// Stats tracks consumer statistics.
type Stats struct {
	Received    int64
	Acked       int64
	Nacked      int64
	Rejected    int64
	Retried     int64
	ProcessTime int64 // total processing time in nanoseconds
}

// Option configures a Consumer.
type Option func(*Consumer)

// WithRetryPolicy sets the retry policy.
func WithRetryPolicy(policy RetryPolicy) Option {
	return func(c *Consumer) {
		c.retryPolicy = policy
	}
}

// WithConsumerID sets the consumer identifier.
func WithConsumerID(id string) Option {
	return func(c *Consumer) {
		c.consumerID = id
	}
}

// WithOnAck sets a callback for successful acknowledgment.
func WithOnAck(fn func(msg *ConsumedMessage)) Option {
	return func(c *Consumer) {
		c.onAck = fn
	}
}

// WithOnNack sets a callback for negative acknowledgment.
func WithOnNack(fn func(msg *ConsumedMessage, err error)) Option {
	return func(c *Consumer) {
		c.onNack = fn
	}
}

// WithOnReject sets a callback for message rejection (dead letter).
func WithOnReject(fn func(msg *ConsumedMessage)) Option {
	return func(c *Consumer) {
		c.onReject = fn
	}
}

// New creates a new Consumer with the given handler and options.
func New(handler Handler, opts ...Option) *Consumer {
	c := &Consumer{
		messages:    make(map[string]*ConsumedMessage),
		handler:     handler,
		retryPolicy: DefaultRetryPolicy(),
		consumerID:  "default",
	}
	for _, opt := range opts {
		opt(c)
	}
	return c
}

// Receive registers a message for consumption. Returns the consumed message wrapper.
func (c *Consumer) Receive(msg *message.Message) *ConsumedMessage {
	c.mu.Lock()
	defer c.mu.Unlock()

	cm := &ConsumedMessage{
		Message:      msg,
		AckStatus:    AckStatusPending,
		ReceivedAt:   time.Now(),
		AttemptCount: 1,
		ConsumerID:   c.consumerID,
	}
	c.messages[msg.ID] = cm
	c.stats.Received++

	log.Printf("[consume] received message: id=%s consumer=%s", msg.ID, c.consumerID)
	return cm
}

// Process processes a message and automatically handles acknowledgment.
// If processing succeeds, the message is acked. If it fails, it is nacked
// and may be retried according to the retry policy.
func (c *Consumer) Process(msg *message.Message) error {
	cm := c.Receive(msg)
	return c.processConsumed(cm)
}

// processConsumed processes an already-received consumed message.
func (c *Consumer) processConsumed(cm *ConsumedMessage) error {
	start := time.Now()

	err := c.handler(cm)

	c.mu.Lock()
	c.stats.ProcessTime += time.Since(start).Nanoseconds()
	c.mu.Unlock()

	if err != nil {
		cm.LastError = err.Error()
		return c.handleFailure(cm, err)
	}

	c.Ack(cm)
	return nil
}

// Ack manually acknowledges a message as successfully processed.
func (c *Consumer) Ack(cm *ConsumedMessage) {
	c.mu.Lock()
	defer c.mu.Unlock()

	now := time.Now()
	cm.AckStatus = AckStatusAcked
	cm.AckedAt = &now
	cm.Message.MarkCompleted(nil)

	c.stats.Acked++

	log.Printf("[consume] acked message: id=%s consumer=%s", cm.Message.ID, c.consumerID)

	if c.onAck != nil {
		c.onAck(cm)
	}
}

// Nack manually rejects a message, triggering a retry if policy allows.
func (c *Consumer) Nack(cm *ConsumedMessage, err error) {
	c.mu.Lock()
	defer c.mu.Unlock()

	cm.AckStatus = AckStatusNacked
	cm.LastError = err.Error()
	c.stats.Nacked++

	log.Printf("[consume] nacked message: id=%s error=%v", cm.Message.ID, err)

	if c.onNack != nil {
		c.onNack(cm, err)
	}
}

// handleFailure handles a failed message processing attempt.
func (c *Consumer) handleFailure(cm *ConsumedMessage, err error) error {
	c.Nack(cm, err)

	if cm.AttemptCount <= c.retryPolicy.MaxRetries {
		cm.AttemptCount++
		c.mu.Lock()
		c.stats.Retried++
		c.mu.Unlock()

		backoff := c.retryPolicy.Backoff(cm.AttemptCount - 2)
		log.Printf("[consume] retrying message: id=%s attempt=%d backoff=%v",
			cm.Message.ID, cm.AttemptCount, backoff)

		time.Sleep(backoff)
		return c.processConsumed(cm)
	}

	// Exhausted retries - reject (dead letter)
	c.Reject(cm)
	return fmt.Errorf("message %s failed after %d attempts: %w",
		cm.Message.ID, cm.AttemptCount, err)
}

// Reject permanently rejects a message (sends to dead letter).
func (c *Consumer) Reject(cm *ConsumedMessage) {
	c.mu.Lock()
	defer c.mu.Unlock()

	cm.AckStatus = AckStatusRejected
	cm.Message.MarkFailed(cm.LastError)
	c.stats.Rejected++

	log.Printf("[consume] rejected message: id=%s attempts=%d",
		cm.Message.ID, cm.AttemptCount)

	if c.onReject != nil {
		c.onReject(cm)
	}
}

// GetConsumed returns the consumed message by ID, or nil if not found.
func (c *Consumer) GetConsumed(messageID string) *ConsumedMessage {
	c.mu.RLock()
	defer c.mu.RUnlock()
	cm, exists := c.messages[messageID]
	if !exists {
		return nil
	}
	return cm
}

// GetPending returns all messages that are pending acknowledgment.
func (c *Consumer) GetPending() []*ConsumedMessage {
	return c.getByStatus(AckStatusPending)
}

// GetAcked returns all acknowledged messages.
func (c *Consumer) GetAcked() []*ConsumedMessage {
	return c.getByStatus(AckStatusAcked)
}

// GetNacked returns all negatively acknowledged messages.
func (c *Consumer) GetNacked() []*ConsumedMessage {
	return c.getByStatus(AckStatusNacked)
}

// GetRejected returns all rejected (dead letter) messages.
func (c *Consumer) GetRejected() []*ConsumedMessage {
	return c.getByStatus(AckStatusRejected)
}

func (c *Consumer) getByStatus(status AckStatus) []*ConsumedMessage {
	c.mu.RLock()
	defer c.mu.RUnlock()

	var result []*ConsumedMessage
	for _, cm := range c.messages {
		if cm.AckStatus == status {
			result = append(result, cm)
		}
	}
	return result
}

// StatsSnapshot returns a copy of the current statistics.
func (c *Consumer) StatsSnapshot() Stats {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.stats
}

// AverageProcessTime returns the average processing time per message.
func (c *Consumer) AverageProcessTime() time.Duration {
	c.mu.RLock()
	defer c.mu.RUnlock()
	total := c.stats.Acked + c.stats.Nacked + c.stats.Rejected
	if total == 0 {
		return 0
	}
	return time.Duration(c.stats.ProcessTime / total)
}

// Size returns the total number of tracked consumed messages.
func (c *Consumer) Size() int {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return len(c.messages)
}

// Clear removes all consumed messages and resets statistics.
func (c *Consumer) Clear() {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.messages = make(map[string]*ConsumedMessage)
	c.stats = Stats{}
}

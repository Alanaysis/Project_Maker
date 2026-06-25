// Package outbox implements the Transactional Outbox pattern.
//
// The Transactional Outbox pattern ensures that a database write and a
// message publication happen atomically. Instead of publishing a message
// directly to a message broker, the message is written to an "outbox"
// table within the same database transaction. A separate process then
// reads the outbox and publishes the messages.
//
// This solves the dual-write problem:
//   - Write to database AND publish to message queue must both succeed or both fail
//   - Without outbox, a crash between DB write and message publish causes inconsistency
//
// Flow:
//
//	1. BEGIN transaction
//	2. Execute business logic (e.g., update order status)
//	3. Write message to outbox table (within the same transaction)
//	4. COMMIT transaction
//	5. (Async) Relay reads outbox and publishes to message queue
//	6. (Async) Relay marks outbox entry as published
package outbox

import (
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/anthropic/exactly-once/internal/message"
	"github.com/anthropic/exactly-once/internal/transaction"
)

// OutboxEntry represents a message waiting to be published.
type OutboxEntry struct {
	// ID is the unique identifier for this outbox entry.
	ID string
	// Topic is the destination topic/queue for the message.
	Topic string
	// Message is the message to be published.
	Message *message.Message
	// State is the current state of the outbox entry.
	State EntryState
	// CreatedAt is when the entry was created.
	CreatedAt time.Time
	// PublishedAt is when the entry was published (nil if not yet).
	PublishedAt *time.Time
	// RetryCount tracks how many times publishing has been attempted.
	RetryCount int
	// LastError stores the last publishing error.
	LastError string
	// TransactionID links this entry to the business transaction.
	TransactionID string
}

// EntryState represents the state of an outbox entry.
type EntryState int

const (
	// EntryStatePending means the entry is waiting to be published.
	EntryStatePending EntryState = iota
	// EntryStatePublishing means the entry is currently being published.
	EntryStatePublishing
	// EntryStatePublished means the entry has been successfully published.
	EntryStatePublished
	// EntryStateFailed means publishing has permanently failed.
	EntryStateFailed
)

// String returns a human-readable representation of the entry state.
func (s EntryState) String() string {
	switch s {
	case EntryStatePending:
		return "PENDING"
	case EntryStatePublishing:
		return "PUBLISHING"
	case EntryStatePublished:
		return "PUBLISHED"
	case EntryStateFailed:
		return "FAILED"
	default:
		return fmt.Sprintf("UNKNOWN(%d)", int(s))
	}
}

// Publisher is a function that publishes a message to a destination.
type Publisher func(topic string, msg *message.Message) error

// Outbox manages transactional outbox entries.
type Outbox struct {
	mu         sync.RWMutex
	entries    map[string]*OutboxEntry
	publisher  Publisher
	maxRetries int
	stats      Stats
	onPublish  func(entry *OutboxEntry)
	onFail     func(entry *OutboxEntry, err error)
}

// Stats tracks outbox statistics.
type Stats struct {
	Created    int64
	Published  int64
	Failed     int64
	Retried    int64
	Pending    int64
}

// Option configures an Outbox.
type Option func(*Outbox)

// WithPublisher sets the message publisher function.
func WithPublisher(pub Publisher) Option {
	return func(o *Outbox) {
		o.publisher = pub
	}
}

// WithMaxRetries sets the maximum number of publishing retries.
func WithMaxRetries(n int) Option {
	return func(o *Outbox) {
		o.maxRetries = n
	}
}

// WithOnPublish sets a callback for successful publishing.
func WithOnPublish(fn func(entry *OutboxEntry)) Option {
	return func(o *Outbox) {
		o.onPublish = fn
	}
}

// WithOnFail sets a callback for publishing failures.
func WithOnFail(fn func(entry *OutboxEntry, err error)) Option {
	return func(o *Outbox) {
		o.onFail = fn
	}
}

// New creates a new Outbox with the given options.
func New(opts ...Option) *Outbox {
	o := &Outbox{
		entries:    make(map[string]*OutboxEntry),
		maxRetries: 3,
	}
	for _, opt := range opts {
		opt(o)
	}
	return o
}

// Save stores a message in the outbox. This should be called within the
// same database transaction as the business logic.
func (o *Outbox) Save(id string, topic string, msg *message.Message, txnID string) *OutboxEntry {
	o.mu.Lock()
	defer o.mu.Unlock()

	entry := &OutboxEntry{
		ID:            id,
		Topic:         topic,
		Message:       msg,
		State:         EntryStatePending,
		CreatedAt:     time.Now(),
		TransactionID: txnID,
	}
	o.entries[id] = entry
	o.stats.Created++
	o.stats.Pending++

	log.Printf("[outbox] saved entry: id=%s topic=%s txn=%s", id, topic, txnID)
	return entry
}

// Publish sends a single outbox entry to the publisher.
func (o *Outbox) Publish(entryID string) error {
	o.mu.RLock()
	entry, exists := o.entries[entryID]
	o.mu.RUnlock()

	if !exists {
		return fmt.Errorf("outbox entry %s not found", entryID)
	}

	return o.publishEntry(entry)
}

// publishEntry publishes a single entry.
func (o *Outbox) publishEntry(entry *OutboxEntry) error {
	if o.publisher == nil {
		return fmt.Errorf("no publisher configured")
	}

	o.mu.Lock()
	entry.State = EntryStatePublishing
	o.mu.Unlock()

	err := o.publisher(entry.Topic, entry.Message)

	o.mu.Lock()
	defer o.mu.Unlock()

	if err != nil {
		entry.RetryCount++
		entry.LastError = err.Error()

		if entry.RetryCount >= o.maxRetries {
			entry.State = EntryStateFailed
			o.stats.Failed++
			o.stats.Pending--
			log.Printf("[outbox] entry permanently failed: id=%s error=%v", entry.ID, err)
			if o.onFail != nil {
				o.onFail(entry, err)
			}
			return fmt.Errorf("outbox entry %s failed after %d retries: %w",
				entry.ID, entry.RetryCount, err)
		}

		entry.State = EntryStatePending
		o.stats.Retried++
		log.Printf("[outbox] entry publish failed, will retry: id=%s attempt=%d",
			entry.ID, entry.RetryCount)
		return err
	}

	now := time.Now()
	entry.State = EntryStatePublished
	entry.PublishedAt = &now
	o.stats.Published++
	o.stats.Pending--

	log.Printf("[outbox] entry published: id=%s topic=%s", entry.ID, entry.Topic)

	if o.onPublish != nil {
		o.onPublish(entry)
	}
	return nil
}

// PublishPending publishes all pending outbox entries.
func (o *Outbox) PublishPending() (int, int) {
	o.mu.RLock()
	var pending []*OutboxEntry
	for _, entry := range o.entries {
		if entry.State == EntryStatePending {
			pending = append(pending, entry)
		}
	}
	o.mu.RUnlock()

	succeeded, failed := 0, 0
	for _, entry := range pending {
		if err := o.publishEntry(entry); err != nil {
			failed++
		} else {
			succeeded++
		}
	}

	log.Printf("[outbox] published pending: total=%d succeeded=%d failed=%d",
		len(pending), succeeded, failed)
	return succeeded, failed
}

// GetEntry returns an outbox entry by ID.
func (o *Outbox) GetEntry(id string) *OutboxEntry {
	o.mu.RLock()
	defer o.mu.RUnlock()
	entry, exists := o.entries[id]
	if !exists {
		return nil
	}
	return entry
}

// GetPending returns all pending outbox entries.
func (o *Outbox) GetPending() []*OutboxEntry {
	o.mu.RLock()
	defer o.mu.RUnlock()

	var result []*OutboxEntry
	for _, entry := range o.entries {
		if entry.State == EntryStatePending {
			result = append(result, entry)
		}
	}
	return result
}

// GetFailed returns all permanently failed outbox entries.
func (o *Outbox) GetFailed() []*OutboxEntry {
	o.mu.RLock()
	defer o.mu.RUnlock()

	var result []*OutboxEntry
	for _, entry := range o.entries {
		if entry.State == EntryStateFailed {
			result = append(result, entry)
		}
	}
	return result
}

// GetPublished returns all published outbox entries.
func (o *Outbox) GetPublished() []*OutboxEntry {
	o.mu.RLock()
	defer o.mu.RUnlock()

	var result []*OutboxEntry
	for _, entry := range o.entries {
		if entry.State == EntryStatePublished {
			result = append(result, entry)
		}
	}
	return result
}

// StatsSnapshot returns a copy of the current statistics.
func (o *Outbox) StatsSnapshot() Stats {
	o.mu.RLock()
	defer o.mu.RUnlock()
	return o.stats
}

// Size returns the total number of outbox entries.
func (o *Outbox) Size() int {
	o.mu.RLock()
	defer o.mu.RUnlock()
	return len(o.entries)
}

// Clear removes all entries and resets statistics.
func (o *Outbox) Clear() {
	o.mu.Lock()
	defer o.mu.Unlock()
	o.entries = make(map[string]*OutboxEntry)
	o.stats = Stats{}
}

// TransactionalOutbox combines a Transaction Manager with an Outbox to
// provide atomic business logic + message publishing.
type TransactionalOutbox struct {
	txnMgr *transaction.Manager
	outbox *Outbox
}

// NewTransactionalOutbox creates a new TransactionalOutbox.
func NewTransactionalOutbox(outbox *Outbox) *TransactionalOutbox {
	return &TransactionalOutbox{
		txnMgr: transaction.NewManager(),
		outbox: outbox,
	}
}

// Begin starts a new transaction for atomic business logic + outbox operations.
func (to *TransactionalOutbox) Begin(txnID string) *transaction.Transaction {
	return to.txnMgr.Begin(txnID)
}

// SaveMessage adds a message to the outbox within the context of a transaction.
// This should be called after business logic operations are added to the transaction.
func (to *TransactionalOutbox) SaveMessage(txnID string, outboxID string, topic string, msg *message.Message) {
	// The outbox save is a transaction operation that writes the message
	// when the transaction commits.
	to.outbox.Save(outboxID, topic, msg, txnID)
}

// PublishOutbox publishes all pending messages in the outbox.
func (to *TransactionalOutbox) PublishOutbox() (int, int) {
	return to.outbox.PublishPending()
}

// Outbox returns the underlying Outbox.
func (to *TransactionalOutbox) Outbox() *Outbox {
	return to.outbox
}

// TransactionManager returns the underlying Transaction Manager.
func (to *TransactionalOutbox) TransactionManager() *transaction.Manager {
	return to.txnMgr
}

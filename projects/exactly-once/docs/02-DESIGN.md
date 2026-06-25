# Exactly-Once Semantics Design

## Goals

1. Understand message delivery semantics (at-most-once, at-least-once, exactly-once)
2. Implement message deduplication using idempotency keys
3. Build idempotent message processing pipeline
4. Implement transactional operations with rollback support
5. Provide complete message state tracking and audit trail
6. Implement consumption acknowledgment (manual, batch, auto-retry)
7. Implement transactional outbox pattern for atomic DB + message publishing

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        Exactly-Once Pipeline                              │
│                                                                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────────┐               │
│  │  Message  │───▶│  Dedup   │───▶│     Processor        │               │
│  │  Input    │    │  Layer   │    │  ┌────────────────┐  │               │
│  └──────────┘    └──────────┘    │  │   Handler(s)   │  │               │
│                                  │  └────────────────┘  │               │
│  ┌──────────┐    ┌──────────┐    │  ┌────────────────┐  │               │
│  │  Tracker  │◀──│ Consume  │◀───│  │  Transaction   │  │               │
│  │  (Audit)  │   │  (Ack)   │    │  │  (Atomic Ops)  │  │               │
│  └──────────┘    └──────────┘    │  └────────────────┘  │               │
│                                  │  ┌────────────────┐  │               │
│  ┌──────────┐                    │  │    Outbox      │  │               │
│  │  Outbox  │◀───────────────────│  │ (Transactional)│  │               │
│  │ (Relay)  │                    │  └────────────────┘  │               │
│  └──────────┘                    └──────────────────────┘               │
└──────────────────────────────────────────────────────────────────────────┘
```

### Core Flow

```
Message --> Dedup Check --> [NEW]       --> Process --> Track --> Ack --> Complete
                       --> [DUP]       --> Skip (return cached result)
                       --> [IN_PROGRESS] --> Wait or Error

Failure --> Retry (with backoff) --> [Success] --> Ack
                               --> [Exhausted] --> Reject (Dead Letter)
```

## Package Structure

```
internal/
├── message/        # Core message types and lifecycle
├── dedup/          # Deduplication with idempotency keys
├── processor/      # Idempotent processing pipeline
├── transaction/    # Two-phase commit transactions
├── consume/        # Consumption acknowledgment (manual, batch, retry)
├── outbox/         # Transactional outbox pattern
└── tracker/        # Message state tracking and audit
```

## Message Package

### Design

```go
type Message struct {
    ID             string
    IdempotencyKey string
    Payload        []byte
    State          State      // PENDING -> PROCESSING -> COMPLETED/FAILED
    CreatedAt      time.Time
    ProcessedAt    *time.Time
    RetryCount     int
    MaxRetries     int
    Result         []byte
    Error          string
    Metadata       map[string]string
}
```

### Design Decisions

1. **Separate ID and IdempotencyKey**: The ID is unique per delivery; the IdempotencyKey identifies the logical operation. This allows the same operation to be delivered multiple times with different IDs but the same IdempotencyKey.

2. **Immutable IdempotencyKey**: Generated deterministically from ID and payload using SHA-256. Can be overridden for custom deduplication logic.

3. **State Machine**: Clear state transitions (PENDING -> PROCESSING -> COMPLETED/FAILED) prevent invalid state changes.

## Dedup Package

### Design

```go
type Deduplicator struct {
    entries    map[string]*Entry
    maxEntries int
    ttl        time.Duration
}

type Entry struct {
    Key       string
    State     string    // "processing", "completed", "failed"
    FirstSeen time.Time
    SeenCount int
    Result    []byte    // Cached result for duplicates
}
```

### Design Decisions

1. **TTL-based expiration**: Entries expire after a configurable TTL. This prevents unbounded memory growth and allows reprocessing of very old messages.

2. **Three-state tracking**: Entries track whether processing is in progress, completed, or failed. This allows different handling for each case.

3. **Thread-safe**: Uses sync.RWMutex for concurrent access.

## Processor Package

### Design

```go
type Processor struct {
    dedup    *Deduplicator
    tracker  *Tracker
    handlers map[string]Handler
}

type Handler func(msg *Message) ([]byte, error)
```

### Processing Flow

1. Check deduplication
2. If duplicate: return cached result or error
3. If in progress: return error (or wait)
4. If new: execute handler
5. On success: mark completed, cache result
6. On failure: retry (up to MaxRetries)
7. After all retries exhausted: mark failed

### Design Decisions

1. **Named handlers**: Handlers are registered by name, allowing different processing logic for different message types.

2. **Automatic retry**: Failed messages are retried up to MaxRetries times. The handler must be idempotent since it may be called multiple times.

3. **Callbacks**: Optional success/duplicate/failure callbacks for monitoring and alerting.

## Consume Package

### Design

```go
type Consumer struct {
    messages    map[string]*ConsumedMessage
    handler     Handler
    retryPolicy RetryPolicy
}

type ConsumedMessage struct {
    Message      *Message
    AckStatus    AckStatus  // PENDING, ACKED, NACKED, REJECTED
    ReceivedAt   time.Time
    AckedAt      *time.Time
    AttemptCount int
    LastError    string
}

type RetryPolicy struct {
    MaxRetries        int
    InitialBackoff    time.Duration
    MaxBackoff        time.Duration
    BackoffMultiplier float64
}
```

### Acknowledgment Flow

1. **Receive**: Register message for consumption
2. **Process**: Execute handler
3. **Ack**: On success, mark as acknowledged
4. **Nack**: On failure, mark for retry
5. **Retry**: Wait for backoff, then re-process
6. **Reject**: After max retries, send to dead letter

### Batch Consumer

```go
type BatchConsumer struct {
    pending     []*ConsumedMessage
    batchSize   int
    flushTimeout time.Duration
    handler     Handler
}
```

Batch processing collects messages and processes them together:
1. **Receive**: Add message to pending batch
2. **ProcessBatch**: Process all pending messages
3. **AckBatch/NackBatch**: Acknowledge or reject the batch

### Design Decisions

1. **Exponential backoff**: Retry delays increase exponentially to avoid overwhelming downstream systems.

2. **Dead letter**: Messages that fail all retries are marked as rejected and can be sent to a dead letter queue.

3. **Batch acknowledgment**: More efficient for high-throughput scenarios than individual ack/nack.

## Outbox Package

### Design

```go
type Outbox struct {
    entries    map[string]*OutboxEntry
    publisher  Publisher
    maxRetries int
}

type OutboxEntry struct {
    ID            string
    Topic         string
    Message       *Message
    State         EntryState  // PENDING, PUBLISHING, PUBLISHED, FAILED
    CreatedAt     time.Time
    PublishedAt   *time.Time
    RetryCount    int
    TransactionID string
}

type TransactionalOutbox struct {
    txnMgr *Manager
    outbox *Outbox
}
```

### Transactional Outbox Flow

1. BEGIN transaction
2. Execute business logic (e.g., update order status)
3. Write message to outbox (within same transaction)
4. COMMIT transaction
5. (Async) Relay reads outbox and publishes to message broker
6. (Async) Relay marks outbox entry as published

### Design Decisions

1. **Atomic writes**: Business logic and outbox writes happen in the same transaction, ensuring consistency.

2. **Relay pattern**: A separate process reads unpublished entries and publishes them. This handles broker failures gracefully.

3. **Retry on publish**: Failed publishes are retried with configurable max retries.

## Transaction Package

### Design

```go
type Transaction struct {
    ID         string
    State      State       // ACTIVE -> PREPARED -> COMMITTED/ABORTED
    Operations []*Operation
}

type Operation struct {
    Name     string
    Execute  func() (interface{}, error)
    Undo     func() error
}
```

### Two-Phase Commit

1. **Prepare Phase**: Execute all operations in order. If any fails, roll back all previously executed operations.

2. **Commit Phase**: If all operations succeeded, mark transaction as committed.

3. **Abort**: Roll back all executed operations in reverse order.

### Design Decisions

1. **Ordered operations**: Operations execute in the order they are added. This allows dependencies between operations.

2. **Reverse rollback**: Operations are rolled back in reverse order. This is important when operations have dependencies.

3. **Best-effort rollback**: If an undo operation fails, we log the error but continue with other undos. This is a pragmatic choice -- in production, failed rollbacks would need manual intervention.

## Tracker Package

### Design

```go
type Tracker struct {
    records map[string]*Record
}

type Record struct {
    MessageID      string
    CurrentState   State
    Events         []Event    // Complete audit trail
    FirstSeen      time.Time
    LastUpdated    time.Time
}

type Event struct {
    Timestamp time.Time
    FromState State
    ToState   State
    Message   string
}
```

### Design Decisions

1. **Immutable event log**: Events are append-only. This provides a complete audit trail of all state transitions.

2. **State-based queries**: Can query messages by current state (e.g., "get all failed messages" for dead-letter queue).

3. **Copy semantics**: GetRecord returns a copy to prevent data races.

## Error Handling

### Duplicate Messages
- Return cached result if available
- Return error if currently being processed
- Log duplicate detection

### Processing Failures
- Retry up to MaxRetries times with exponential backoff
- Track retry count per message
- After exhaustion: mark as rejected, trigger failure callback

### Consumption Failures
- Auto-retry with configurable backoff policy
- Dead letter queue for permanently failed messages
- Batch-level failure handling

### Transaction Failures
- Roll back all executed operations
- Record failure reason
- Leave transaction in ABORTED state

### Outbox Failures
- Retry publishing up to max retries
- Failed entries remain in outbox for manual inspection
- Relay process handles retry logic

## Testing Strategy

### Unit Tests
- Message lifecycle and state transitions
- Deduplication with various scenarios
- Processor with idempotent handlers
- Transaction commit and rollback
- Tracker event recording
- Consumer acknowledgment (manual, batch, retry)
- Outbox save, publish, and retry

### Integration Tests
- Full pipeline: message -> dedup -> process -> track -> ack
- Concurrent message processing
- Retry scenarios
- Batch processing
- Transactional outbox with business logic

### What We Don't Test
- External storage (in-memory only for this learning project)
- Network failures (simulated via error returns)
- Real distributed scenarios

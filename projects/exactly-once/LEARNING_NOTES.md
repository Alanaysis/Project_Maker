# Learning Notes - Exactly-Once Semantics

## What I Learned

### 1. Message Delivery Semantics

There are three levels of message delivery guarantees:

- **At-most-once**: Fire and forget. Messages may be lost but never duplicated. Simplest to implement.
- **At-least-once**: Retry until acknowledged. Messages may be delivered multiple times but never lost. Most common in practice.
- **Exactly-once**: Each message processed exactly once. Combines at-least-once delivery with idempotent processing. Most complex but strongest guarantee.

**Key Takeaway**: True exactly-once delivery is impossible due to the Two Generals Problem. What we actually implement is "effectively exactly-once" by combining at-least-once delivery with idempotent processing and deduplication.

### 2. Idempotency

An operation is idempotent if applying it multiple times has the same effect as applying it once.

**Idempotent examples**:
- `SET x = 5` (always sets x to 5)
- `DELETE user WHERE id = 123` (deleting twice is same as once)
- HTTP PUT (replace entire resource)

**Non-idempotent examples**:
- `x = x + 1` (each application increments)
- `INSERT INTO orders ...` (creates new row each time)
- `send_email(...)` (sends multiple emails)

**Key Takeaway**: The key insight is that idempotency is not about the operation itself, but about its side effects. `INSERT` can be made idempotent by using `INSERT ... ON CONFLICT DO NOTHING`.

### 3. Idempotency Keys

An idempotency key is a unique identifier for a logical operation. Messages with the same key are considered duplicates.

```go
// Generate deterministic key from message content
key := sha256(messageID + payload)
```

**Key Takeaway**: The idempotency key must be:
- Deterministic: Same operation always produces same key
- Unique: Different operations produce different keys
- Client-generated: The client decides what constitutes "the same operation"

### 4. Deduplication

Before processing any message, check if an equivalent operation has already been processed:

1. Check if the idempotency key has been seen
2. If seen and completed: return cached result
3. If seen and in progress: wait or error
4. If not seen: process the message

**Key Takeaway**: Deduplication is the first line of defense. Without it, every retry would be processed as a new message.

### 5. Two-Phase Commit (2PC)

A protocol for atomic transactions across multiple operations:

**Phase 1 (Prepare)**: Execute all operations, collect results
**Phase 2 (Commit/Rollback)**: If all succeed, commit. If any fail, rollback all.

```
Begin Transaction
  ├─ Operation 1: Execute → Success
  ├─ Operation 2: Execute → Success
  └─ Operation 3: Execute → Failure
     └─ Rollback Operation 2 (undo)
     └─ Rollback Operation 1 (undo)
     └─ Transaction Aborted
```

**Key Takeaway**: The rollback must happen in reverse order because later operations may depend on earlier ones.

### 6. Message State Machine

A message goes through clear state transitions:

```
PENDING ──▶ PROCESSING ──▶ COMPLETED
                │
                ▼
             FAILED ──▶ PENDING (retry)
                │
                └──▶ FAILED (exhausted)
```

**Key Takeaway**: The state machine prevents invalid transitions (e.g., going from COMPLETED back to PROCESSING) and provides a clear audit trail.

### 7. Consumption Acknowledgment

Three modes for acknowledging consumed messages:

**Manual Ack**: Explicit `Ack()`/`Nack()` calls after processing
```go
consumer.Process(msg) // auto-acks on success
```

**Batch Ack**: Acknowledge multiple messages together
```go
batch.Receive(msg1)
batch.Receive(msg2)
batch.ProcessBatch() // atomic ack
```

**Auto-retry**: Failed messages retried with exponential backoff
```go
consume.New(handler, consume.WithRetryPolicy(RetryPolicy{
    MaxRetries:        3,
    InitialBackoff:    100 * time.Millisecond,
    MaxBackoff:        10 * time.Second,
    BackoffMultiplier: 2.0,
}))
```

**Key Takeaway**: Acknowledgment is the consumer's responsibility. Without ack, the broker cannot know if a message was successfully processed.

### 8. Transactional Outbox Pattern

The outbox pattern solves the dual-write problem (DB write + message publish):

1. BEGIN transaction
2. Execute business logic
3. Write message to outbox table (same transaction!)
4. COMMIT transaction
5. Relay reads outbox and publishes to broker

**Key Takeaway**: By writing the message to the same database as the business data, we get atomicity for free. The relay handles the eventual consistency with the message broker.

### 9. Exponential Backoff

Retry delays increase exponentially to avoid overwhelming downstream systems:

```
Attempt 0: 100ms
Attempt 1: 200ms
Attempt 2: 400ms
Attempt 3: 800ms
...
Max: 10s (capped)
```

**Key Takeaway**: Exponential backoff with jitter is essential for retry logic. Without it, thundering herds can overwhelm recovering systems.

### 10. Concurrency with sync.RWMutex

All components use `sync.RWMutex` for thread safety:

```go
type Deduplicator struct {
    mu      sync.RWMutex
    entries map[string]*Entry
}

func (d *Deduplicator) Get(key string) *Entry {
    d.mu.RLock()         // Read lock - allows concurrent reads
    defer d.mu.RUnlock()
    return d.entries[key]
}

func (d *Deduplicator) Set(key string, entry *Entry) {
    d.mu.Lock()          // Write lock - exclusive access
    defer d.mu.Unlock()
    d.entries[key] = entry
}
```

**Key Takeaway**: RWMutex is ideal for read-heavy workloads. Multiple goroutines can read simultaneously, but writes require exclusive access.

### 11. Transaction Rollback

When a transaction fails, all executed operations must be undone:

```go
func (t *Transaction) rollbackExecuted(lastIndex int) {
    for i := lastIndex - 1; i >= 0; i-- {
        op := t.Operations[i]
        if op.Undo != nil {
            op.Undo()
        }
    }
}
```

**Key Takeaway**: Rollback in reverse order is critical. If operation B depends on operation A, we must undo B before A.

## Challenges Faced

### 1. Defining "Same Operation"

The hardest design decision was defining what constitutes "the same operation" for deduplication.

**Options considered**:
- Same message ID (too strict - retries have different IDs)
- Same payload (too loose - different operations could have same payload)
- Client-provided idempotency key (flexible but requires client cooperation)

**Solution**: Use a combination - generate a default idempotency key from ID + payload (SHA-256), but allow clients to override it for custom deduplication logic.

### 2. Handling In-Progress Messages

When a message is received while an identical one is being processed, what should we do?

**Options considered**:
- Wait for the first to complete (complex, potential deadlock)
- Return error immediately (simple but may lose the message)
- Queue for later processing (adds complexity)

**Solution**: Return an error immediately. The at-least-once delivery guarantee means the message will be retried later.

### 3. Transaction Rollback Failures

What happens if an undo operation itself fails?

**Options considered**:
- Retry the undo (could infinite loop)
- Panic (too aggressive)
- Log and continue (best effort)

**Solution**: Log the error and continue with other undos. In production, this would trigger an alert for manual intervention.

### 4. TTL for Dedup Entries

How long should we remember processed messages?

**Too short**: Might process duplicates that arrive after TTL expires
**Too long**: Unbounded memory growth

**Solution**: Configurable TTL with default of 24 hours. This is a trade-off between memory usage and duplicate detection window.

### 5. Batch Acknowledgment Failure

What happens when a batch partially fails?

**Options considered**:
- Fail the entire batch (wastes successful processing)
- Ack successful, nack failed (complex state management)
- Retry the entire batch (re-processes already-processed messages)

**Solution**: Ack successful messages, nack failed ones. The batch consumer tracks per-message status.

### 6. Outbox Relay Reliability

How to ensure the outbox relay doesn't lose messages?

**Options considered**:
- Poll-based relay (simple but adds latency)
- Change data capture (complex but real-time)
- Event-driven relay (requires DB triggers)

**Solution**: Poll-based relay with retry. Failed publishes remain in the outbox for retry.

## Design Decisions

### 1. Separate ID and IdempotencyKey

The message ID is unique per delivery, while the IdempotencyKey identifies the logical operation. This allows:
- Same operation delivered multiple times with different IDs
- Custom deduplication logic via IdempotencyKey
- Clear separation between transport and business logic

### 2. In-Memory Implementation

This project uses in-memory storage for simplicity. In production:
- Dedup: Redis with TTL
- Tracker: PostgreSQL or Elasticsearch
- Transactions: Database transactions
- Outbox: Database table with relay

### 3. Handler-Based Processing

Handlers are registered by name and must be idempotent:
```go
p.Register("transfer", func(msg *Message) ([]byte, error) {
    return performTransfer(msg.Payload)
})
```

This design:
- Separates routing from processing
- Allows different handlers for different message types
- Makes testing easier (mock handlers)

### 4. Callbacks for Monitoring

Optional callbacks for success, duplicate, and failure events:
```go
p := processor.New(
    processor.WithOnSuccess(func(msg *Message) { metrics.Increment("success") }),
    processor.WithOnDuplicate(func(msg *Message) { metrics.Increment("duplicate") }),
    processor.WithOnFailure(func(msg *Message, err error) { alert(err) }),
)
```

### 5. Configurable Retry Policy

Retry behavior is configurable per consumer:
```go
consume.New(handler, consume.WithRetryPolicy(RetryPolicy{
    MaxRetries:        3,
    InitialBackoff:    100 * time.Millisecond,
    MaxBackoff:        10 * time.Second,
    BackoffMultiplier: 2.0,
}))
```

### 6. Publisher Abstraction for Outbox

The outbox uses a Publisher function type, making it easy to swap message brokers:
```go
type Publisher func(topic string, msg *Message) error

// Kafka
outbox.New(outbox.WithPublisher(kafkaPublisher))

// RabbitMQ
outbox.New(outbox.WithPublisher(rabbitPublisher))

// In-memory (for testing)
outbox.New(outbox.WithPublisher(memoryPublisher))
```

## What I Would Do Differently

1. **Use interfaces for storage**: Would define Storage interfaces to make it easy to swap in Redis/PostgreSQL.

2. **Add bloom filters**: For high-throughput systems, bloom filters would reduce memory usage for dedup.

3. **Implement saga pattern**: For distributed transactions, the saga pattern is more practical than 2PC.

4. **Add message ordering**: Currently no ordering guarantee. Would add sequence numbers or timestamps.

5. **Add dead-letter queue**: Messages that fail after all retries should go to a DLQ for manual inspection.

6. **Add metrics**: Processing latency, dedup hit rate, retry rate, etc.

7. **Add configuration file**: Instead of hardcoding defaults, load from YAML/TOML.

8. **Persistent outbox**: Use a real database for the outbox table in production.

9. **Async relay**: The outbox relay should run as a separate goroutine with its own lifecycle.

10. **Circuit breaker**: Add circuit breaker for downstream service failures.

## Key Insights

### Exactly-Once is Really "Effectively Exactly-Once"

True exactly-once delivery is impossible in distributed systems (Two Generals Problem). What we implement is:
- At-least-once delivery (retry until acknowledged)
- Idempotent processing (same input produces same output)
- Deduplication (detect and skip duplicates)

The combination gives us "effectively exactly-once" semantics.

### Idempotency is the Key

The entire system hinges on idempotency. If handlers are not idempotent, no amount of deduplication can guarantee exactly-once semantics.

**Rule**: Every handler MUST be designed to be idempotent. If it's not naturally idempotent, make it so using:
- Idempotency keys in the database
- Conditional updates (WHERE version = N)
- Natural idempotency (SET instead of ADD)

### Deduplication Window Matters

The TTL for dedup entries determines the "exactly-once window":
- TTL = 1 hour: Messages duplicated within 1 hour are caught
- TTL = 24 hours: Messages duplicated within 24 hours are caught
- TTL = 0: No deduplication (at-least-once only)

Choose TTL based on your retry policy and message delivery guarantees.

### Acknowledgment is the Consumer's Responsibility

The message broker cannot know if a message was successfully processed unless the consumer explicitly acknowledges it. Without acknowledgment:
- The broker will redeliver the message
- The consumer may process it again
- Exactly-once is violated

### The Outbox Pattern is Essential

Without the outbox pattern, there's no way to atomically:
1. Write to a database
2. Publish to a message broker

The outbox pattern makes this atomic by writing the message to the same database as the business data.

## Next Steps

To extend this project:
1. Add Redis-backed deduplication
2. Implement saga pattern for distributed transactions
3. Add message ordering with sequence numbers
4. Implement dead-letter queue
5. Add Prometheus metrics
6. Add configuration file support
7. Create a REST API for message submission
8. Add support for message batches
9. Implement circuit breaker for handler failures
10. Add distributed tracing (OpenTelemetry)
11. Add persistent outbox with database backend
12. Implement async outbox relay with lifecycle management

## Resources That Helped

1. **Kafka Documentation**: Excellent explanation of exactly-once semantics in distributed systems.
2. **Two Generals Problem**: Understanding why true exactly-once is impossible.
3. **Stripe's Idempotency Key Blog Post**: Real-world implementation of idempotency keys.
4. **Jepsen Reports**: Understanding consistency models in distributed systems.
5. **Go sync package**: RWMutex documentation and examples.
6. **Microservices.io**: Transactional outbox pattern documentation.
7. **CloudEvents**: Standardized event format for outbox messages.

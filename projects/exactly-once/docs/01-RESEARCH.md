# Exactly-Once Semantics Research

## What is Exactly-Once Semantics?

Exactly-once semantics (EOS) guarantees that a message is processed exactly one time, producing the same result as if it were processed a single time -- even in the presence of network failures, retries, and crashes.

## Message Delivery Semantics

There are three levels of message delivery guarantees:

### At-Most-Once

- Fire and forget
- Messages may be lost
- No retries
- Simplest to implement
- Use case: Metrics, logging where occasional loss is acceptable

### At-Least-Once

- Retry until acknowledged
- Messages may be delivered multiple times
- Requires deduplication at the consumer
- Most common in practice
- Use case: Event sourcing, audit logs

### Exactly-Once

- Each message processed exactly once
- Combines at-least-once delivery with idempotent processing
- Most complex to implement
- Use case: Financial transactions, inventory management

## Why is Exactly-Once Hard?

The fundamental challenge is the **Two Generals Problem**: two parties cannot reliably agree on a message delivery without an unbounded number of messages.

In practice, exactly-once is achieved through a combination of:

1. **At-least-once delivery** (retry until acknowledged)
2. **Idempotent processing** (same input always produces same output)
3. **Deduplication** (detect and skip duplicates)

## Idempotency

An operation is **idempotent** if applying it multiple times has the same effect as applying it once.

### Examples of Idempotent Operations

- `SET x = 5` (always sets x to 5)
- `DELETE user WHERE id = 123` (deleting twice is same as once)
- HTTP PUT (replace entire resource)
- `mkdir /tmp/mydir` (fails gracefully if exists)

### Examples of Non-Idempotent Operations

- `x = x + 1` (each application increments)
- `INSERT INTO orders ...` (creates new row each time)
- HTTP POST (may create duplicate resources)
- `send_email(to, subject, body)` (sends multiple emails)

### Making Operations Idempotent

1. **Idempotency keys**: Client generates unique key per logical operation
2. **Deduplication tables**: Store processed keys, check before processing
3. **Conditional updates**: Use version numbers or timestamps
4. **Natural idempotency**: Design operations to be inherently idempotent

## Deduplication Strategies

### In-Memory Deduplication

- Fast, simple
- Lost on restart
- Good for single-instance systems
- Uses hash maps or bloom filters

### Persistent Deduplication

- Survives restarts
- Requires external storage (database, Redis)
- Good for distributed systems
- Uses deduplication tables with TTL

### Bloom Filters

- Probabilistic data structure
- Very memory efficient
- False positives possible (conservative: may skip valid messages)
- No false negatives (never processes a duplicate)
- Good for high-throughput systems

## Transactional Message Processing

### Two-Phase Commit (2PC)

1. **Prepare Phase**: Execute all operations, collect results
2. **Commit Phase**: If all succeed, commit. If any fail, rollback.

### Local Transactions

For single-database systems:
- BEGIN TRANSACTION
- Execute operations
- COMMIT or ROLLBACK

### Distributed Transactions

For multi-system operations:
- Saga pattern: Each step has a compensating action
- Event sourcing: Store events, replay to reconstruct state
- Outbox pattern: Write to local DB, then publish

## Key Technologies

### Apache Kafka

- Producer: `enable.idempotence=true` for exactly-once producer
- Consumer: `isolation.level=read_committed` for transactional reads
- Transactions: `initTransactions()`, `beginTransaction()`, `commitTransaction()`

### RabbitMQ

- Publisher confirms for at-least-once
- Consumer acknowledgments for at-least-once
- No built-in exactly-once (must implement at application level)

### Amazon SQS

- FIFO queues with message deduplication
- Exactly-once processing within visibility timeout
- Message group IDs for ordering

## References

- [Kafka Exactly-Once Semantics](https://kafka.apache.org/documentation/#semantics)
- [Two Generals Problem](https://en.wikipedia.org/wiki/Two_Generals%27_Problem)
- [Idempotency in Distributed Systems](https://blog.danslimmon.com/2019/07/15/do-nothing-scaffolding-the-key-to-idempotency/)
- [Jepsen: Consistency Models](https://jepsen.io/consistency)

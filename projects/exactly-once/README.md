# Exactly-Once Semantics

A Go implementation of exactly-once message processing semantics, built for understanding message delivery guarantees, idempotency, transactional processing, and consumption acknowledgment.

## Overview

This project implements the core building blocks for exactly-once message processing:

- **Message Deduplication**: Detect and skip duplicate messages using idempotency keys
- **Idempotent Processing**: Ensure the same message produces the same result regardless of delivery count
- **Transactional Operations**: Group multiple operations into atomic units with rollback support
- **State Tracking**: Complete audit trail of message lifecycle events
- **Consumption Acknowledgment**: Manual ack, batch ack, and automatic retry with backoff
- **Transactional Outbox**: Atomic business logic + message publishing via the outbox pattern
- **Practical Examples**: Payment system, order system, and message queue demos

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

## Core Flow

```
Message --> Dedup Check --> [NEW]       --> Process --> Track --> Ack --> Complete
                       --> [DUP]       --> Skip (return cached result)
                       --> [IN_PROGRESS] --> Wait or Error

Failure --> Retry (with backoff) --> [Success] --> Ack
                               --> [Exhausted] --> Reject (Dead Letter)
```

## Project Structure

```
exactly-once/
├── cmd/
│   └── demo/
│       └── main.go              # Demo program
├── examples/
│   ├── payment/
│   │   └── main.go              # Payment system example
│   ├── order/
│   │   └── main.go              # Order system example
│   └── mq/
│       └── main.go              # Message queue example
├── internal/
│   ├── message/
│   │   ├── message.go           # Core message types
│   │   └── message_test.go
│   ├── dedup/
│   │   ├── dedup.go             # Deduplication
│   │   └── dedup_test.go
│   ├── processor/
│   │   ├── processor.go         # Idempotent processing
│   │   └── processor_test.go
│   ├── transaction/
│   │   ├── transaction.go       # Two-phase commit
│   │   └── transaction_test.go
│   ├── consume/
│   │   ├── consume.go           # Consumption acknowledgment
│   │   ├── batch.go             # Batch acknowledgment
│   │   ├── consume_test.go
│   │   └── batch_test.go
│   ├── outbox/
│   │   ├── outbox.go            # Transactional outbox pattern
│   │   └── outbox_test.go
│   └── tracker/
│       ├── tracker.go           # State tracking
│       └── tracker_test.go
├── tests/
│   ├── semantics_test.go        # Exactly-once semantics tests
│   └── pipeline_test.go         # Full pipeline integration tests
├── docs/                        # Documentation
├── go.mod                       # Go module file
├── README.md                    # This file
└── LEARNING_NOTES.md            # Learning notes
```

## Quick Start

### Prerequisites

- Go 1.21 or later

### Build and Run

```bash
# Build and run demo
go run ./cmd/demo

# Run payment example
go run ./examples/payment

# Run order example
go run ./examples/order

# Run message queue example
go run ./examples/mq
```

### Run Tests

```bash
# Run all tests
go test ./...

# Run tests with verbose output
go test ./... -v

# Run tests for a specific package
go test ./internal/dedup -v
go test ./internal/consume -v
go test ./internal/outbox -v

# Run with race detection
go test ./... -race

# Run with coverage
go test ./... -cover
```

## Message Delivery Semantics

### At-Most-Once
- Fire and forget
- Messages may be lost
- Simplest to implement

### At-Least-Once
- Retry until acknowledged
- Messages may be delivered multiple times
- Most common in practice

### Exactly-Once (this project)
- Each message processed exactly once
- Combines at-least-once delivery with idempotent processing
- Most complex but strongest guarantee

## Key Concepts

### Idempotency

An operation is idempotent if applying it multiple times has the same effect as applying it once.

**Idempotent**: `SET x = 5`, `DELETE user WHERE id = 123`, HTTP PUT
**Not idempotent**: `x = x + 1`, `INSERT INTO orders ...`, HTTP POST

### Idempotency Keys

Each logical operation has a unique idempotency key. Messages with the same key are considered duplicates, regardless of how many times they are delivered.

```go
// Generate deterministic key from message content
key := sha256(messageID + payload)
```

### Consumption Acknowledgment

Three acknowledgment modes for message consumers:

1. **Manual Ack**: Caller explicitly calls `Ack`/`Nack` after processing
2. **Batch Ack**: Multiple messages are acknowledged together atomically
3. **Auto-retry**: Failed messages are automatically retried with exponential backoff

```go
// Manual acknowledgment
consumer := consume.New(handler)
msg := message.New("msg-001", []byte("data"))
consumer.Process(msg) // auto-acks on success, retries on failure

// Batch acknowledgment
batch := consume.NewBatchConsumer(handler, consume.WithBatchSize(10))
batch.Receive(msg1)
batch.Receive(msg2)
batch.ProcessBatch() // acks entire batch
```

### Transactional Outbox

The outbox pattern ensures atomic business logic + message publishing:

1. BEGIN transaction
2. Execute business logic (e.g., update order)
3. Write message to outbox (same transaction)
4. COMMIT transaction
5. Relay publishes outbox entries to message broker

```go
outbox := outbox.New(outbox.WithPublisher(publishFunc))
outbox.Save("entry-001", "orders", msg, "txn-001")
outbox.Publish("entry-001") // or outbox.PublishPending()
```

### Two-Phase Commit

Transactions use two phases:
1. **Prepare**: Execute all operations, collect results
2. **Commit/Rollback**: If all succeed, commit. If any fail, rollback all.

### Deduplication

Before processing any message:
1. Check if the idempotency key has been seen
2. If seen and completed: return cached result
3. If seen and in progress: wait or error
4. If not seen: process the message

## Practical Examples

### Payment System (`examples/payment`)

Demonstrates:
- Idempotent payment processing (same order charged only once)
- Transactional balance updates with rollback
- Outbox pattern for payment events

### Order System (`examples/order`)

Demonstrates:
- Idempotent order creation
- Atomic inventory reservation + order creation
- Batch message processing
- Dead letter queue for failed messages

### Message Queue (`examples/mq`)

Demonstrates:
- Producer with idempotency keys
- Consumer with manual acknowledgment
- Batch message processing
- Transactional outbox for reliable publishing

## Key Concepts Summary

| Concept | Purpose | Implementation |
|---------|---------|----------------|
| Idempotency Key | Identify "same operation" | SHA-256 of ID + payload |
| Deduplication | Skip already-processed messages | In-memory map with TTL |
| Transaction | Atomic multi-step operations | Two-phase commit |
| Outbox | Atomic DB + message publish | Outbox table + relay |
| Ack/Nack | Consumer confirmation | Manual + batch + auto-retry |
| Tracker | Audit trail | Event log per message |

## Learning Resources

- [Kafka Exactly-Once Semantics](https://kafka.apache.org/documentation/#semantics)
- [Two Generals Problem](https://en.wikipedia.org/wiki/Two_Generals%27_Problem)
- [Idempotency in Distributed Systems](https://blog.danslimmon.com/2019/07/15/do-nothing-scaffolding-the-key-to-idempotency/)
- [Jepsen: Consistency Models](https://jepsen.io/consistency)
- [Transactional Outbox Pattern](https://microservices.io/patterns/data/transactional-outbox.html)

## License

This project is for educational purposes.

---

[返回分布式系统模块](../DISTRIBUTED_README.md) | [返回主目录](../../README.md)

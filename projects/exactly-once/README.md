# Exactly-Once Semantics

A Go implementation of exactly-once message processing semantics, built for understanding message delivery guarantees, idempotency, and transactional processing.

## Overview

This project implements the core building blocks for exactly-once message processing:

- **Message Deduplication**: Detect and skip duplicate messages using idempotency keys
- **Idempotent Processing**: Ensure the same message produces the same result regardless of delivery count
- **Transactional Operations**: Group multiple operations into atomic units with rollback support
- **State Tracking**: Complete audit trail of message lifecycle events

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Exactly-Once Pipeline                      │
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────────┐  │
│  │  Message  │───▶│  Dedup   │───▶│     Processor        │  │
│  │  Input    │    │  Layer   │    │  ┌────────────────┐  │  │
│  └──────────┘    └──────────┘    │  │   Handler(s)   │  │  │
│                                  │  └────────────────┘  │  │
│  ┌──────────┐                    │  ┌────────────────┐  │  │
│  │  Tracker  │◀──────────────────│  │  Transaction   │  │  │
│  │  (Audit)  │                   │  │  (Atomic Ops)  │  │  │
│  └──────────┘                    │  └────────────────┘  │  │
│                                  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Core Flow

```
Message → Dedup Check → [NEW] → Process → Track → Complete
                     → [DUP] → Skip (return cached result)
                     → [IN_PROGRESS] → Wait or Error
```

## Project Structure

```
exactly-once/
├── cmd/
│   └── demo/
│       └── main.go              # Demo program
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
│   └── tracker/
│       ├── tracker.go           # State tracking
│       └── tracker_test.go
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
# Build
go build -o demo ./cmd/demo

# Run demo
./demo
```

### Run Tests

```bash
# Run all tests
go test ./...

# Run tests with verbose output
go test ./... -v

# Run tests for a specific package
go test ./internal/dedup -v

# Run with race detection
go test ./... -race
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

## Example Usage

```go
// Create processor
p := processor.New()

// Register idempotent handler
p.Register("transfer", func(msg *message.Message) ([]byte, error) {
    // This handler MUST be idempotent
    return performTransfer(msg.Payload)
})

// Process message (guaranteed exactly-once)
msg := message.New("msg-001", []byte(`{"from":"A","to":"B","amount":100}`))
err := p.Process(msg, "transfer")

// Even if the same message is delivered again, it won't be processed twice
msg2 := message.New("msg-002", []byte(`{"from":"A","to":"B","amount":100}`))
msg2.IdempotencyKey = msg.IdempotencyKey // Same logical operation
p.Process(msg2, "transfer") // Detected as duplicate, skipped
```

## Key Concepts

### Exactly-Once Semantics

Exactly-once semantics means that a message is processed exactly one time, producing the same result as if it were processed a single time -- even in the presence of network failures, retries, and crashes.

### Idempotency

An operation is idempotent if applying it multiple times has the same effect as applying it once. Examples:
- `SET x = 5` (idempotent)
- `x = x + 1` (not idempotent)

### Deduplication

Before processing a message, check if an equivalent operation has already been processed. If so, return the cached result instead of re-processing.

### Two-Phase Commit

A protocol for atomic transactions:
1. **Prepare**: Execute all operations
2. **Commit/Rollback**: If all succeed, commit. If any fail, rollback.

## Learning Resources

- [Kafka Exactly-Once Semantics](https://kafka.apache.org/documentation/#semantics)
- [Two Generals Problem](https://en.wikipedia.org/wiki/Two_Generals%27_Problem)
- [Idempotency in Distributed Systems](https://blog.danslimmon.com/2019/07/15/do-nothing-scaffolding-the-key-to-idempotency/)
- [Jepsen: Consistency Models](https://jepsen.io/consistency)

## License

This project is for educational purposes.

---

[返回分布式系统模块](../DISTRIBUTED_README.md) | [返回主目录](../../README.md)

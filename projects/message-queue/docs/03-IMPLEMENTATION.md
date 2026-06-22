# 03 - Implementation Guide

## Project Structure

```
message-queue/
├── cmd/
│   ├── producer/main.go       # CLI producer demo
│   └── consumer/main.go       # CLI consumer demo
├── internal/
│   ├── protocol/
│   │   ├── message.go          # Message struct, status, JSON
│   │   ├── errors.go           # Sentinel errors
│   │   └── message_test.go
│   ├── queue/
│   │   ├── topic.go            # Topic with subscriber management
│   │   ├── broker.go           # Central message router
│   │   ├── topic_test.go
│   │   └── broker_test.go
│   ├── persistence/
│   │   ├── store.go            # Store interface
│   │   ├── filestore.go        # Filesystem-based persistence
│   │   ├── memstore.go         # In-memory store for tests
│   │   ├── filestore_test.go
│   │   └── memstore_test.go
│   ├── producer/
│   │   ├── producer.go         # Message publisher
│   │   └── producer_test.go
│   └── consumer/
│       ├── consumer.go         # Message subscriber with handler
│       └── consumer_test.go
├── pkg/
│   └── api/
│       ├── api.go              # High-level facade
│       └── api_test.go
├── docs/
├── go.mod
└── README.md
```

## Key Implementation Details

### Message ID Generation
Uses nanosecond timestamp + random hex suffix to ensure uniqueness within a
single node. Not suitable for distributed deployment without additional
coordination.

### Fan-Out Delivery
When a message is published, the broker iterates over all subscribers of that
topic and sends on each subscriber's buffered channel. The send is non-blocking:
if a subscriber's buffer is full, the message is skipped for that subscriber.

### Persistence Strategy
- **Write-ahead**: Messages are persisted before being published to subscribers.
  This ensures at-least-once delivery even on crash.
- **File organization**: `data/topic-name/message-id.json`
- **Recovery**: On startup, all unacknowledged messages are reloaded into
  their topics.

### Acknowledgement Flow
```
Consumer handler returns nil  →  Broker marks message as Acknowledged
Consumer handler returns err  →  Message stays Delivered (retry possible)
```

### Auto-Topic Creation
Publishing to a non-existent topic automatically creates it. Explicit
`CreateTopic` is also supported.

## Running the Demo

Terminal 1 (Consumer):
```bash
go run ./cmd/consumer
```

Terminal 2 (Producer):
```bash
go run ./cmd/producer
```

The consumer will receive and print all messages published by the producer.
Messages are persisted to `./data/` and survive restarts.

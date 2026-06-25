# 03 - Implementation Guide

## Project Structure

```
message-queue/
├── cmd/
│   ├── producer/main.go       # CLI producer demo (priority, delayed, filtered)
│   └── consumer/main.go       # CLI consumer demo (push, pull, groups, filters)
├── internal/
│   ├── protocol/
│   │   ├── message.go          # Message struct, status, priority, headers, JSON
│   │   ├── errors.go           # Sentinel errors
│   │   └── message_test.go
│   ├── queue/
│   │   ├── topic.go            # Topic with priority queue, modes, filters
│   │   ├── broker.go           # Central message router
│   │   ├── consumer_group.go   # Consumer group with round-robin
│   │   ├── dead_letter.go      # Dead letter queue
│   │   ├── topic_test.go
│   │   ├── broker_test.go
│   │   ├── consumer_group_test.go
│   │   └── dead_letter_test.go
│   ├── persistence/
│   │   ├── store.go            # Store interface
│   │   ├── filestore.go        # Filesystem-based persistence
│   │   ├── memstore.go         # In-memory store for tests
│   │   ├── filestore_test.go
│   │   └── memstore_test.go
│   ├── producer/
│   │   ├── producer.go         # Message publisher with options
│   │   └── producer_test.go
│   └── consumer/
│       ├── consumer.go         # Message subscriber with handler, pull, groups
│       └── consumer_test.go
├── pkg/
│   └── api/
│       ├── api.go              # High-level facade
│       └── api_test.go
├── tests/
│   └── integration_test.go     # End-to-end integration tests
├── docs/
├── go.mod
└── README.md
```

## Key Implementation Details

### Priority Queue
Uses Go's `container/heap` package for O(log n) insertion and O(1) peek.
Messages are ordered by:
1. Priority (high > normal > low)
2. Creation time (FIFO within same priority)

```go
type priorityQueue []*protocol.Message

func (pq priorityQueue) Less(i, j int) bool {
    if pq[i].Priority != pq[j].Priority {
        return pq[i].Priority > pq[j].Priority
    }
    return pq[i].CreatedAt.Before(pq[j].CreatedAt)
}
```

### Delayed Messages
Messages with `DeliverAfter` set are not available for delivery until the
specified time. The `IsReady()` method checks if the delay has expired.

### Consumer Groups
Implements round-robin distribution using an atomic counter:
```go
idx := atomic.AddUint64(&cg.roundRobin, 1) - 1
selected := active[idx%uint64(len(active))]
```

### Dead Letter Queue
Messages that exceed `MaxRetries` are moved to a per-topic DLQ:
```go
if msg.CanRetry() {
    msg.IncrementRetry()
} else {
    topic.RemoveMessage(msg.ID)
    dlq.Add(msg)
}
```

### Message Filtering
Filters are checked at two levels:
1. Topic-level filter (set via `SetFilter`)
2. Subscriber-level filter (set via `SubscribeWithFilter`)

```go
func (m *Message) MatchesFilter(filter map[string]string) bool {
    for k, v := range filter {
        if msgVal, ok := m.Headers[k]; !ok || msgVal != v {
            return false
        }
    }
    return true
}
```

### Fan-Out Delivery
When a message is published in PubSub mode, the broker iterates over all
subscribers and sends on each subscriber's buffered channel. The send is
non-blocking to prevent slow subscribers from blocking others.

### Point-to-Point Delivery
In Queue mode, messages are delivered to exactly one subscriber using
round-robin selection.

### Persistence Strategy
- **Write-ahead**: Messages are persisted before being published to subscribers.
- **File organization**: `data/topic-name/message-id.json`
- **Recovery**: On startup, all unacknowledged messages are reloaded into
  their topics. Dead letter messages are restored to DLQ.

### Acknowledgement Flow
```
Consumer handler returns nil  →  Broker marks message as Acknowledged and removes
Consumer handler returns err  →  Message stays for retry or moves to DLQ
```

### Auto-Topic Creation
Publishing to a non-existent topic automatically creates it in PubSub mode.
Explicit `CreateTopic` or `CreateQueueTopic` is also supported.

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

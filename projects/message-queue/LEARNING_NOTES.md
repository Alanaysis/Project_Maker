# Learning Notes: Distributed Message Queue

## What I Learned

### 1. Message Queue Fundamentals
- A message queue decouples producers from consumers in time and space.
- The queue acts as a buffer, allowing producers and consumers to operate
  at different rates.
- Pub/Sub (publish/subscribe) is one pattern; point-to-point is another.
- Consumer groups enable horizontal scaling of message processing.

### 2. Publish/Subscribe Pattern
- In pub/sub, every subscriber receives every message (fan-out).
- This is different from competing consumers where only one gets each message.
- Go channels are a natural fit for implementing subscriber delivery:
  each subscriber gets a buffered channel, and the broker writes to all of them.

### 3. Point-to-Point Pattern
- Each message is consumed by exactly one consumer.
- Consumer groups with round-robin distribution provide load balancing.
- Messages stay in queue until successfully processed.

### 4. Priority Queue
- Go's `container/heap` package provides efficient priority queue operations.
- O(log n) insertion and O(1) peek operations.
- Messages ordered by priority then creation time (FIFO within same priority).

### 5. Delayed Messages
- Messages can be published with a future delivery time.
- `DeliverAfter` field stores the earliest delivery timestamp.
- `IsReady()` method checks if delay has expired.
- Useful for scheduled tasks and retry backoff.

### 6. Message Filtering
- Consumers can subscribe with header-based filters.
- Only messages matching all filter criteria are delivered.
- Enables content-based routing and selective processing.

### 7. Consumer Groups
- Groups of consumers that compete for messages.
- Round-robin distribution ensures fair load balancing.
- Atomic counter for thread-safe distribution.

### 8. Dead Letter Queue
- Messages that exceed max retries are moved to DLQ.
- Prevents poison messages from blocking the queue.
- DLQ messages can be inspected, retried, or discarded.

### 9. Message Persistence
- Persistence means writing messages to durable storage (disk) so they survive
  broker restarts.
- The write-ahead approach (persist before delivering) ensures at-least-once
  semantics.
- Recovery on startup involves reading all unacknowledged messages back into
  memory.
- File-per-message is simple but slow; an append-only log would be better
  for production.

### 10. Acknowledgement Mechanism
- Ack tells the broker "I have processed this message successfully."
- Without ack, the broker doesn't know if a message was consumed or lost.
- Negative ack triggers retry or DLQ on max retries.
- The message lifecycle tracks state transitions.

### 11. Go Concurrency Patterns
- `sync.RWMutex` for protecting shared state (topics, subscribers).
- Buffered channels for non-blocking message delivery.
- Goroutines for concurrent message processing per subscriber.
- `sync.WaitGroup` and `atomic` for coordinating in tests.
- Graceful shutdown via `close(channel)` and `done` channels.
- `container/heap` for priority queue implementation.

### 12. Interface-Based Design
- The `Store` interface abstracts persistence, allowing FileStore and MemStore
  to be swapped without changing the broker.
- This makes testing easy: use MemStore in tests, FileStore in production.

### 13. Fan-Out Implementation
- When a message is published, the broker iterates all subscribers.
- Each subscriber's channel receives a pointer to the same message.
- Non-blocking send (`select` with `default`) prevents a slow subscriber
  from blocking others.

## Key Takeaways

1. **Decoupling is the core value** of message queues. Producers don't need
   to know about consumers, and vice versa.

2. **Persistence is essential** for reliability. In-memory-only queues lose
   everything on crash.

3. **Acknowledgements** are what distinguish a message queue from a simple
   channel or pipe. They enable reliable delivery.

4. **Priority queues** enable important messages to be processed first.

5. **Delayed messages** enable scheduled processing and retry backoff.

6. **Consumer groups** enable horizontal scaling of message processing.

7. **Dead letter queues** prevent poison messages from blocking the system.

8. **Message filtering** enables selective processing and content-based routing.

9. **Go's concurrency primitives** (goroutines, channels, mutexes, atomic)
   map well to message queue internals.

10. **Start simple, iterate**. This implementation is single-node and
    file-based, but the abstractions (Store interface, Broker) allow
    extending to distributed operation later.

# Learning Notes: Distributed Message Queue

## What I Learned

### 1. Message Queue Fundamentals
- A message queue decouples producers from consumers in time and space.
- The queue acts as a buffer, allowing producers and consumers to operate
  at different rates.
- Pub/Sub (publish/subscribe) is one pattern; point-to-point is another.

### 2. Publish/Subscribe Pattern
- In pub/sub, every subscriber receives every message (fan-out).
- This is different from competing consumers where only one gets each message.
- Go channels are a natural fit for implementing subscriber delivery:
  each subscriber gets a buffered channel, and the broker writes to all of them.

### 3. Message Persistence
- Persistence means writing messages to durable storage (disk) so they survive
  broker restarts.
- The write-ahead approach (persist before delivering) ensures at-least-once
  semantics.
- Recovery on startup involves reading all unacknowledged messages back into
  memory.
- File-per-message is simple but slow; an append-only log would be better
  for production.

### 4. Acknowledgement Mechanism
- Ack tells the broker "I have processed this message successfully."
- Without ack, the broker doesn't know if a message was consumed or lost.
- Double-ack detection prevents bugs where a message is processed twice.
- The message lifecycle (Pending -> Delivered -> Acknowledged) tracks state.

### 5. Go Concurrency Patterns
- `sync.RWMutex` for protecting shared state (topics, subscribers).
- Buffered channels for non-blocking message delivery.
- Goroutines for concurrent message processing per subscriber.
- `sync.WaitGroup` and `atomic` for coordinating in tests.
- Graceful shutdown via `close(channel)` and `done` channels.

### 6. Interface-Based Design
- The `Store` interface abstracts persistence, allowing FileStore and MemStore
  to be swapped without changing the broker.
- This makes testing easy: use MemStore in tests, FileStore in production.

### 7. Fan-Out Implementation
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

4. **Go's concurrency primitives** (goroutines, channels, mutexes) map well
   to message queue internals.

5. **Start simple, iterate**. This implementation is single-node and
   file-based, but the abstractions (Store interface, Broker) allow
   extending to distributed operation later.

# 02 - Design: System Architecture

## High-Level Architecture

```
┌──────────┐     publish      ┌───────────────────────────────┐     deliver      ┌──────────┐
│ Producer │ ───────────────▶ │          Broker                │ ───────────────▶ │ Consumer │
└──────────┘                  │  ┌───────────┐ ┌────────────┐ │                  └──────────┘
                              │  │  Topic A   │ │ConsumerGrp │ │       ┌──────────┐
                              │  │  (PubSub)  │ │(RoundRobin)│ │──────▶│ Consumer │
                              │  │  Topic B   │ └────────────┘ │       └──────────┘
                              │  │  (Queue)   │                │
                              │  └───────────┘ ┌────────────┐ │
                              │       │        │DeadLetterQ │ │
                              │  ┌────▼──────┐ └────────────┘ │
                              │  │ FileStore  │                │
                              │  │ MemStore   │                │
                              │  └───────────┘                │
                              └───────────────────────────────┘
```

## Component Breakdown

### 1. Protocol Layer (`internal/protocol`)
Defines the `Message` struct and shared error types. This is the contract
between all other components.

**Message Lifecycle:**
```
Pending ──▶ Delivered ──▶ Acknowledged
    │
    └──▶ DeadLetter (after max retries)
```

**Message Properties:**
- ID: Unique identifier
- Topic: Destination topic
- Payload: Message content
- Priority: Low, Normal, High
- Headers: Key-value pairs for filtering
- DeliverAfter: Delayed delivery timestamp
- RetryCount / MaxRetries: Retry tracking

### 2. Queue Layer (`internal/queue`)
- **Topic**: Holds messages in a priority queue and manages subscribers.
  - ModePubSub: Fan-out to all subscribers
  - ModeQueue: Deliver to one consumer
- **Subscriber**: Represents a consumer's subscription with a Go channel and
  optional filter.
- **ConsumerGroup**: Manages a group of consumers with round-robin distribution.
- **DeadLetterQueue**: Holds messages that exceeded max retries.
- **Broker**: Central router that coordinates topics, publishing, subscribing,
  acknowledgement, and consumer groups.

### 3. Persistence Layer (`internal/persistence`)
- **Store interface**: Abstraction for saving/loading messages.
- **FileStore**: JSON files organized by topic on disk.
- **MemStore**: In-memory map for testing.

### 4. Producer (`internal/producer`)
Thin wrapper that publishes messages through the broker with support for:
- Basic publish
- Priority publish
- Delayed publish
- Filtered publish (with headers)

### 5. Consumer (`internal/consumer`)
Subscribes to topics and processes messages via a handler. Supports:
- Push mode (channel-based)
- Pull mode (explicit fetch)
- Filtered subscriptions
- Consumer group membership

### 6. API Layer (`pkg/api`)
High-level facade (`MessageQueue`) that wires everything together.

## Data Flow

### Pub/Sub Mode
```
1. Producer.Publish(topic, payload)
2. Broker creates Message with unique ID
3. Broker persists message via Store
4. Broker fans out to all topic subscribers (non-blocking channel send)
5. Each Consumer receives message on its channel
6. Consumer invokes Handler function
7. On success, Broker.Acknowledge is called
8. Message removed from topic, ack persisted via Store
```

### Point-to-Point Mode
```
1. Producer.Publish(queue_topic, payload)
2. Broker creates Message with unique ID
3. Broker persists message via Store
4. Broker delivers to one subscriber (round-robin)
5. Consumer processes message
6. On success, Broker.Acknowledge removes message
7. On failure, Broker.NegativeAcknowledge increments retry count
8. After max retries, message moves to Dead Letter Queue
```

### Pull Mode
```
1. Producer.Publish(topic, payload)
2. Broker persists message
3. Consumer calls Pull(topic, timeout)
4. Broker returns next ready message (priority-ordered)
5. Consumer processes and acknowledges
```

## Concurrency Model

- **Broker.mu**: RWMutex protecting the topics, subscribers, and consumer groups maps.
- **Topic.mu**: RWMutex protecting messages and subscribers within a topic.
- **Store.mu**: RWMutex for persistence operations.
- **Subscriber.Ch**: Buffered Go channel (default 256) for async delivery.
- **ConsumerGroup.mu**: RWMutex for consumer management.

## Error Handling

| Error                    | When                                     |
|--------------------------|------------------------------------------|
| ErrTopicNotFound         | Referencing a non-existent topic         |
| ErrTopicAlreadyExists    | Creating a duplicate topic               |
| ErrQueueFull             | Topic at capacity                        |
| ErrAlreadyAcknowledged   | Double ack on same message               |
| ErrSubscriptionExists    | Duplicate subscriber ID on a topic       |
| ErrConsumerGroupNotFound | Referencing non-existent consumer group  |
| ErrConsumerGroupExists   | Creating duplicate consumer group        |
| ErrNoAvailableConsumer   | No active consumer in group              |
| ErrMessageNotReady       | Delayed message not yet ready            |
| ErrMaxRetriesExceeded    | Message exceeded max retry count         |

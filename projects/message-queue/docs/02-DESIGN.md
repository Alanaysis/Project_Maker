# 02 - Design: System Architecture

## High-Level Architecture

```
┌──────────┐     publish      ┌───────────────┐     deliver      ┌──────────┐
│ Producer │ ───────────────▶ │    Broker      │ ───────────────▶ │ Consumer │
└──────────┘                  │  ┌───────────┐ │                  └──────────┘
                              │  │  Topic A   │ │       ┌──────────┐
                              │  │  Topic B   │ │──────▶│ Consumer │
                              │  │  Topic C   │ │       └──────────┘
                              │  └───────────┘ │
                              │       │        │
                              │  ┌────▼──────┐ │
                              │  │ FileStore  │ │
                              │  └───────────┘ │
                              └───────────────┘
```

## Component Breakdown

### 1. Protocol Layer (`internal/protocol`)
Defines the `Message` struct and shared error types. This is the contract
between all other components.

**Message Lifecycle:**
```
Pending ──▶ Delivered ──▶ Acknowledged
```

### 2. Queue Layer (`internal/queue`)
- **Topic**: Holds messages and manages subscriber channels.
- **Subscriber**: Represents a consumer's subscription with a Go channel.
- **Broker**: Central router that coordinates topics, publishing, subscribing,
  and acknowledgement.

### 3. Persistence Layer (`internal/persistence`)
- **Store interface**: Abstraction for saving/loading messages.
- **FileStore**: JSON files organized by topic on disk.
- **MemStore**: In-memory map for testing.

### 4. Producer (`internal/producer`)
Thin wrapper that publishes messages through the broker.

### 5. Consumer (`internal/consumer`)
Subscribes to topics, receives messages on a channel, invokes a handler,
and auto-acknowledges on success.

### 6. API Layer (`pkg/api`)
High-level facade (`MessageQueue`) that wires everything together.

## Data Flow

```
1. Producer.Publish(topic, payload)
2. Broker creates Message with unique ID
3. Broker persists message via Store
4. Broker fans out to all topic subscribers (non-blocking channel send)
5. Consumer receives message on its channel
6. Consumer invokes Handler function
7. On success, Broker.Acknowledge is called
8. Ack is persisted via Store
```

## Concurrency Model

- **Broker.mu**: RWMutex protecting the topics and subscribers maps.
- **Topic.mu**: RWMutex protecting messages and subscribers within a topic.
- **Store.mu**: RWMutex for persistence operations.
- **Subscriber.Ch**: Buffered Go channel (default 256) for async delivery.

## Error Handling

| Error                    | When                                     |
|--------------------------|------------------------------------------|
| ErrTopicNotFound         | Referencing a non-existent topic         |
| ErrTopicAlreadyExists    | Creating a duplicate topic               |
| ErrQueueFull             | Topic at capacity                        |
| ErrAlreadyAcknowledged   | Double ack on same message               |
| ErrSubscriptionExists    | Duplicate subscriber ID on a topic       |

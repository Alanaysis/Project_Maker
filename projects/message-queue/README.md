# Distributed Message Queue

A feature-rich distributed message queue implementation in Go, demonstrating core
messaging concepts: publish/subscribe pattern, point-to-point queues, message
persistence, acknowledgement mechanisms, priority queues, delayed messages,
consumer groups, and dead letter queues.

## Features

### Message Models
- **Publish/Subscribe**: Producers publish to topics; all subscribers receive
  every message (fan-out).
- **Point-to-Point**: Queue mode where each message is consumed by exactly one consumer.
- **Message Acknowledgement**: Consumers confirm message processing; unacknowledged
  messages survive restarts.

### Storage
- **In-Memory Store**: Fast, volatile storage for testing.
- **File Store**: Persistent JSON-based storage for durability.
- **Message Index**: Messages organized by topic on disk.

### Consumption Modes
- **Push Mode**: Messages are pushed to consumers via channels.
- **Pull Mode**: Consumers explicitly pull messages when ready.
- **Consumer Groups**: Groups of consumers that compete for messages (round-robin).

### Reliability
- **Message Persistence**: Messages stored on disk and recovered on restart.
- **Message Retry**: Configurable retry count with exponential backoff.
- **Dead Letter Queue**: Messages that exceed max retries are moved to DLQ.

### Advanced Features
- **Delayed Messages**: Messages delivered after a specified delay.
- **Priority Queue**: Messages processed by priority (high > normal > low).
- **Message Filtering**: Subscribe with header-based filters.

### Practical Applications
- **Asynchronous Processing**: Decouple producers from consumers.
- **System Decoupling**: Independent scaling of producers and consumers.
- **Traffic Shaping**: Buffer bursts of messages for gradual processing.

## Architecture

```
                    ┌─────────────────────────────────────────┐
                    │              Message Queue               │
┌──────────┐       │  ┌──────────────────────────────────┐    │       ┌──────────┐
│ Producer │──publish──▶│           Broker                │──deliver──▶│ Consumer │
└──────────┘       │  │  ┌─────────┐  ┌─────────────┐   │    │       └──────────┘
                   │  │  │  Topic  │  │ ConsumerGrp │   │    │
                   │  │  │ (Queue) │  │ (RoundRobin)│   │    │       ┌──────────┐
                   │  │  └─────────┘  └─────────────┘   │──deliver──▶│ Consumer │
                   │  │       │                          │    │       └──────────┘
                   │  │  ┌────▼──────┐  ┌─────────────┐  │    │
                   │  │  │ FileStore │  │  DeadLetter  │  │    │
                   │  │  │ MemStore  │  │    Queue     │  │    │
                   │  │  └───────────┘  └─────────────┘  │    │
                   │  └──────────────────────────────────┘    │
                   └─────────────────────────────────────────┘
```

## Project Structure

```
message-queue/
├── cmd/
│   ├── producer/          CLI demo: publish messages
│   └── consumer/          CLI demo: subscribe and process
├── internal/
│   ├── protocol/          Message struct, priorities, error types
│   ├── queue/             Topic, Broker, ConsumerGroup, DeadLetterQueue
│   ├── persistence/       FileStore and MemStore implementations
│   ├── producer/          Producer abstraction
│   └── consumer/          Consumer with handler pattern
├── pkg/
│   └── api/               High-level MessageQueue facade
├── tests/                 Integration tests
└── docs/                  Design and implementation docs
```

## Quick Start

### Run the Consumer (Terminal 1)
```bash
go run ./cmd/consumer
```

### Run the Producer (Terminal 2)
```bash
go run ./cmd/producer
```

### Run Tests
```bash
go test ./...
```

## Usage as a Library

```go
package main

import (
    "fmt"
    "time"
    "github.com/example/message-queue/pkg/api"
    "github.com/example/message-queue/internal/protocol"
)

func main() {
    mq, _ := api.New(api.DefaultConfig())
    defer mq.Close()

    // Create a pub/sub topic.
    mq.CreateTopic("events")

    // Create a point-to-point queue topic.
    mq.CreateQueueTopic("tasks")

    // Create a consumer group.
    cg, _ := mq.CreateConsumerGroup("workers", "tasks")
    cg.AddConsumer("worker-1")
    cg.AddConsumer("worker-2")

    // Producer with priority.
    p := mq.NewProducer()
    p.PublishWithPriority("events", []byte("urgent alert"), protocol.PriorityHigh)
    p.PublishDelayed("events", []byte("delayed msg"), 5*time.Second)
    p.PublishWithHeaders("events", []byte("filtered"),
        map[string]string{"channel": "sms"})

    // Consumer with filter.
    handler := func(msg *protocol.Message) error {
        fmt.Printf("Received: %s\n", msg.Payload)
        return nil
    }
    c := mq.NewConsumer("my-consumer", handler)
    c.SubscribeWithFilter("events", map[string]string{"channel": "sms"})
    defer c.Close()

    // Pull mode.
    msg, _ := mq.Pull("tasks", 5*time.Second)
    fmt.Printf("Pulled: %s\n", msg.Payload)

    // Dead letter queue.
    dlq := mq.GetDeadLetterQueue("events")
    deadMsgs := dlq.Messages()
    fmt.Printf("Dead letters: %d\n", len(deadMsgs))
}
```

## Learning Goals

- Understand message queue fundamentals (topics, producers, consumers)
- Implement publish/subscribe and point-to-point patterns
- Learn message persistence for durability across restarts
- Practice Go concurrency (goroutines, channels, mutexes)
- Implement priority queues with heap data structure
- Design consumer groups with round-robin distribution
- Handle message retry and dead letter queues

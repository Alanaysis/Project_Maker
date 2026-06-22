# Distributed Message Queue

A simple distributed message queue implementation in Go, demonstrating core
messaging concepts: publish/subscribe pattern, message persistence, and
acknowledgement mechanisms.

## Features

- **Publish/Subscribe**: Producers publish to topics; all subscribers receive
  every message (fan-out).
- **Message Persistence**: Messages are stored on disk (JSON files) and
  recovered on restart.
- **Acknowledgement**: Consumers confirm message processing; unacknowledged
  messages survive restarts.
- **Auto-Topic Creation**: Publishing to a non-existent topic creates it
  automatically.
- **Pluggable Storage**: File-based or in-memory persistence via the Store
  interface.

## Architecture

```
Producer ──publish──▶ Broker ──deliver──▶ Consumer
                        │
                        ▼
                    FileStore (disk)
```

## Project Structure

```
cmd/producer/          CLI demo: publish messages
cmd/consumer/          CLI demo: subscribe and process
internal/protocol/     Message struct and error types
internal/queue/        Topic and Broker implementation
internal/persistence/  FileStore and MemStore
internal/producer/     Producer abstraction
internal/consumer/     Consumer with handler pattern
pkg/api/               High-level MessageQueue facade
docs/                  Design and implementation docs
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
    "github.com/example/message-queue/pkg/api"
    "github.com/example/message-queue/internal/protocol"
)

func main() {
    mq, _ := api.New(api.DefaultConfig())
    defer mq.Close()

    // Producer
    p := mq.NewProducer()
    p.PublishString("events", `{"type": "user_created"}`)

    // Consumer
    handler := func(msg *protocol.Message) error {
        fmt.Printf("Received: %s\n", msg.Payload)
        return nil
    }
    c := mq.NewConsumer("my-consumer", handler)
    c.Subscribe("events")
    defer c.Close()
}
```

## Learning Goals

- Understand message queue fundamentals (topics, producers, consumers)
- Implement the publish/subscribe pattern with fan-out delivery
- Learn message persistence for durability across restarts
- Practice Go concurrency (goroutines, channels, mutexes)

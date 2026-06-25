# 01 - Research: Distributed Message Queue

## What is a Message Queue?

A message queue is an asynchronous communication protocol where producers send
messages to a queue and consumers read them independently. This decouples the
sender from the receiver in both time and space.

## Core Concepts

### Topic
A named channel that categorizes messages. Producers publish to topics;
consumers subscribe to them.

### Producer
A component that creates and publishes messages to one or more topics.

### Consumer
A component that subscribes to a topic and processes incoming messages.

### Acknowledgement (Ack)
A confirmation from the consumer that a message has been successfully processed.
This enables at-least-once delivery semantics.

### Persistence
Storing messages on disk so they survive broker restarts. Without persistence,
messages exist only in memory and are lost on failure.

## Delivery Semantics

| Semantic         | Guarantee                                          |
|------------------|----------------------------------------------------|
| At-most-once     | Message delivered 0 or 1 times; may be lost        |
| At-least-once    | Message delivered 1 or more times; may be duplicated|
| Exactly-once     | Message delivered exactly 1 time (hardest to achieve)|

This implementation targets **at-least-once** delivery.

## Message Patterns

### Pub/Sub (Fan-Out)
Each message is delivered to all subscribers of a topic. Use cases:
- Event broadcasting
- Notifications to multiple services
- Real-time updates

### Point-to-Point (Queue)
Each message is consumed by exactly one consumer. Use cases:
- Task distribution
- Work queue processing
- Load balancing

### Consumer Groups
A group of consumers that compete for messages. Only one consumer in the group
receives each message. This enables horizontal scaling of message processing.

## Consumption Modes

### Push Mode
The broker pushes messages to consumers as they arrive. Consumers receive
messages on a channel. This is simpler but gives less control to consumers.

### Pull Mode
Consumers explicitly request messages when ready. This provides:
- Better backpressure control
- Consumer-driven rate limiting
- Batch processing capabilities

## Advanced Features

### Priority Queues
Messages are processed based on priority level. Higher priority messages are
delivered before lower priority ones. Implementation uses a heap data structure
for O(log n) insertion and O(1) peek.

### Delayed Messages
Messages are published with a delay. They become available for delivery only
after the delay expires. Use cases:
- Scheduled tasks
- Retry backoff
- Time-delayed notifications

### Dead Letter Queue (DLQ)
Messages that fail processing after exceeding maximum retries are moved to a
DLQ. This prevents poison messages from blocking the queue and allows for
manual inspection and reprocessing.

### Message Filtering
Consumers can subscribe with filters based on message headers. Only messages
matching the filter are delivered. This enables:
- Selective message processing
- Routing messages to specific consumers
- Content-based routing

## Existing Systems for Reference

- **Apache Kafka**: Distributed log, partitioned topics, consumer groups.
- **RabbitMQ**: AMQP broker, exchanges, routing keys, dead letter exchanges.
- **Redis Pub/Sub**: Lightweight in-memory pub/sub.
- **NATS**: Simple, high-performance messaging.
- **Amazon SQS**: Managed queue service with DLQ support.

## Design Decisions for This Project

1. Single-node broker (not distributed across network).
2. File-based persistence using JSON files.
3. Both Pub/Sub and Point-to-Point modes.
4. Channel-based message delivery (Go channels).
5. Auto-ack on successful handler execution.
6. Priority queue using container/heap.
7. Consumer groups with round-robin distribution.
8. Dead letter queue for failed messages.

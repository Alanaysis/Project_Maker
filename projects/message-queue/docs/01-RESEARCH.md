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

## Pub/Sub vs Point-to-Point

- **Point-to-Point**: Each message is consumed by exactly one consumer.
- **Pub/Sub (Fan-Out)**: Each message is delivered to all subscribers.

This project implements **Pub/Sub** with fan-out delivery.

## Existing Systems for Reference

- **Apache Kafka**: Distributed log, partitioned topics, consumer groups.
- **RabbitMQ**: AMQP broker, exchanges, routing keys.
- **Redis Pub/Sub**: Lightweight in-memory pub/sub.
- **NATS**: Simple, high-performance messaging.

## Design Decisions for This Project

1. Single-node broker (not distributed across network).
2. File-based persistence using JSON files.
3. Fan-out to all subscribers of a topic.
4. Channel-based message delivery (Go channels).
5. Auto-ack on successful handler execution.

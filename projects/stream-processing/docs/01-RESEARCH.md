# Stream Processing Research

## What is Stream Processing?

Stream processing is a programming paradigm that treats data as a continuous, unbounded flow of events rather than static datasets. Unlike batch processing (which processes all data at once), stream processing handles data incrementally as it arrives.

### Key Characteristics

1. **Unbounded data**: The input never "ends" -- events keep arriving
2. **Low latency**: Results are produced as data arrives, not after a batch completes
3. **Stateful**: Operators may maintain state across events
4. **Windowed**: Aggregations are scoped to time windows

## Stream Processing Models

### 1. Dataflow Model (Google Dataflow / Apache Beam)

The Dataflow model unifies batch and stream processing:

- **PCollection**: An immutable collection of data elements
- **PTransform**: An operation that transforms PCollections
- **Pipeline**: A graph of PTransforms connected by PCollections
- **Window**: Divides unbounded data into finite chunks
- **Trigger**: Determines when to emit results for a window
- **Watermark**: Tracks progress through event time

### 2. Actor Model (Akka Streams)

Data flows through a graph of actors:

- Each actor processes one element at a time
- Backpressure is built into the protocol
- Naturally concurrent and distributed

### 3. Reactive Streams

An API standard for asynchronous stream processing:

- **Publisher**: Emits elements
- **Subscriber**: Consumes elements
- **Processor**: Transforms elements (both publisher and subscriber)
- **Backpressure**: Subscriber controls the rate

## Core Concepts

### Events

An event is the fundamental data unit:

```
Event {
    key:       string      // Partitioning key
    value:     interface{} // The actual data
    timestamp: time.Time   // When the event occurred (event time)
}
```

### Operators

Operators transform the stream:

| Operator    | Input   | Output  | Description                    |
|-------------|---------|---------|--------------------------------|
| Map         | 1 event | 1 event | Transforms each event          |
| Filter      | 1 event | 0-1     | Keeps events matching predicate|
| FlatMap     | 1 event | 0-N     | Splits one event into many     |
| Reduce      | N events| 1 event | Aggregates by key              |
| Window      | N events| N events| Groups by time window          |
| Join        | 2 streams| 1 stream| Combines two streams          |

### Windows

Windows group events by time for aggregation:

```
Tumbling Window (non-overlapping):
Time: 0  1  2  3  4  5  6  7  8  9  10
Win1: [--------)
Win2:             [--------)
Win3:                          [--------)

Sliding Window (overlapping):
Time: 0  1  2  3  4  5  6  7  8  9  10
Win1: [------------------)
Win2:        [------------------)
Win3:               [------------------)

Session Window (gap-based):
Time: 0  1  2  3  ... 10 11 12 13
Win1: [--------)
Win2:                        [-----)
     (gap > threshold separates sessions)
```

### Watermarks

A watermark tracks the progress of event time:

- **Event time**: When the event actually occurred
- **Processing time**: When the event is processed
- **Watermark**: The minimum event time we expect to see for unprocessed events

Watermarks determine when a window is "complete":

```
If watermark >= window.End, the window can be closed and results emitted.
```

### State Management

Stateful operators need to:

1. **Store state**: Accumulators, counters, buffers
2. **Persist state**: Survive failures (checkpointing)
3. **Query state**: Expose current state for debugging
4. **Clean up state**: Evict expired window state

## Real-World Systems

| System            | Company  | Language   | Key Feature                  |
|-------------------|----------|------------|------------------------------|
| Apache Flink      | Alibaba  | Java       | True streaming, event time   |
| Apache Kafka Streams| LinkedIn| Java     | Exactly-once semantics       |
| Google Dataflow   | Google   | Java/Python| Unified batch+stream         |
| Apache Spark Streaming| Databricks| Scala | Micro-batch approach         |
| Apache Storm      | Twitter  | Java       | Low-latency, at-least-once   |

## Key Algorithms

### 1. Consistent Hashing

For distributing events across partitions:

```
hash(key) % num_partitions -> partition_id
```

### 2. Chandy-Lamport Algorithm

For taking consistent snapshots in distributed systems (used in checkpointing).

### 3. Sliding Window Aggregation

Efficiently maintaining a running aggregate over a sliding window:

```
Maintain: running_sum, window_events[]
On new event:
    Add event to window_events
    running_sum += event.value
    Remove expired events
    running_sum -= expired.value
```

## References

- [Apache Beam Programming Model](https://beam.apache.org/documentation/programming-guide/)
- [Google Dataflow Paper](https://research.google/pubs/pub43864/)
- [The Dataflow Model (VLDB 2015)](https://research.google.com/pubs/archive/43856.pdf)
- [Apache Flink Documentation](https://flink.apache.org/docs/)
- [Streaming Systems Book](https://www.oreilly.com/library/view/streaming-systems/9781491983867/)

# Learning Notes - Stream Processing Framework

## What I Learned

### 1. Stream Processing Fundamentals

Stream processing treats data as a continuous, unbounded flow of events. Unlike batch processing (which processes all data at once), stream processing handles data incrementally as it arrives.

**Key Takeaway**: The mental model shift from "all data is available" to "data arrives over time" changes everything -- from how you design operators to how you think about correctness.

### 2. The Dataflow Model

The modern stream processing model (pioneered by Google Dataflow) separates concerns:

- **What**: Operators (map, filter, reduce)
- **Where**: Windowing (which window does this event belong to?)
- **When**: Triggers and watermarks (when do we emit results?)
- **How**: State management (how do we accumulate data?)

**Key Takeaway**: Separating "where" (windowing) from "when" (triggers) gives much more flexibility than coupling them together.

### 3. Window Types

Different windowing strategies serve different use cases:

| Window Type | Use Case | Example |
|-------------|----------|---------|
| Tumbling | Fixed-period aggregation | "5-minute averages" |
| Sliding | Moving averages | "10-minute window, sliding every 1 minute" |
| Session | User activity tracking | "Group events until 30s of inactivity" |

**Key Takeaway**: Tumbling windows are the simplest (each event belongs to exactly one window), but sliding windows are more useful for smooth aggregations.

### 4. Watermarks

A watermark tracks the progress of event time. It answers: "Have we seen all events up to time T?"

```
watermark = min(event timestamps we've seen)
```

When `watermark >= window.End`, the window is considered complete and results can be emitted.

**Key Takeaway**: Watermarks are the mechanism that allows us to reason about completeness in an unbounded stream. Without them, we'd never know when a window is "done."

### 5. Channel-Based Streams in Go

Go's channels are a natural fit for stream processing:

```go
// Producer
go func() {
    for _, item := range data {
        stream.Emit(item)
    }
    stream.Close()
}()

// Consumer
for event := range stream.Events() {
    process(event)
}
```

**Key Takeaway**: Channels provide natural backpressure (blocking when the buffer is full) and clean shutdown (closing the channel signals the end of data).

### 6. Operator Composition

The pipeline pattern chains operators through intermediate streams:

```
input -> [Op1] -> stream1 -> [Op2] -> stream2 -> [Op3] -> output
```

Each intermediate stream runs in its own goroutine, enabling pipelining: Op1 can process event N+1 while Op2 processes event N.

**Key Takeaway**: Pipelining increases throughput without requiring explicit parallelism. Each operator stage can work independently.

### 7. State Management

Stateful operators (like ReduceByKey) need:

1. **Storage**: Where to keep accumulated values
2. **Thread safety**: Multiple goroutines may access state
3. **Expiration**: Clean up old window states

Go's `sync.RWMutex` is perfect for read-heavy workloads (many reads, few writes).

**Key Takeaway**: State management is the hardest part of stream processing. In production systems, state must be persisted (checkpointed) for fault tolerance.

### 8. Concurrency Patterns in Go

This project uses several Go concurrency patterns:

- **Goroutine-per-operator**: Each pipeline stage runs concurrently
- **Channel-based communication**: Streams use buffered channels
- **WaitGroup for coordination**: Parallel workers signal completion
- **Mutex for shared state**: Protects mutable operator state

**Key Takeaway**: Go's goroutines and channels make concurrent stream processing straightforward. The `select` statement enables non-blocking operations.

## Challenges Faced

### 1. Sliding Window Assignment

The most complex part was implementing sliding window assignment. Each event may belong to multiple windows:

```
Window size = 10s, Slide = 5s
Event at t=7s belongs to windows [0,10) and [5,15)
```

**Solution**: Walk backwards from the aligned boundary, checking each possible window.

### 2. Pipeline Shutdown

Ensuring clean shutdown of the pipeline required careful channel management:

1. Producer closes the input stream
2. Each operator finishes processing remaining events
3. Operators call Flush to emit final results
4. Output stream is closed

**Solution**: Use `defer output.Close()` in goroutines and chain the close signals.

### 3. Race Conditions

With multiple goroutines accessing shared state, race conditions were a constant concern.

**Solution**: Use `-race` flag in tests. Use `sync.RWMutex` for read-heavy state, `sync.Mutex` for write-heavy state.

### 4. Window Boundary Alignment

Ensuring deterministic window boundaries required aligning to the epoch:

```go
func alignTimestamp(ts time.Time) time.Time {
    epoch := time.Unix(0, 0)
    offset := ts.Sub(epoch)
    aligned := (offset / windowSize) * windowSize
    return epoch.Add(aligned)
}
```

**Solution**: Epoch alignment ensures all instances compute the same window boundaries.

## Design Decisions

### 1. Interface{} for Values

Using `interface{}` instead of generics (or type parameters) was a deliberate choice:

- **Pros**: Simple, flexible, works with any data type
- **Cons**: No compile-time type safety, requires type assertions

In a production system, I would use Go 1.18+ generics for type safety.

### 2. Channel-Based Streams

Chose channels over callbacks or iterators:

- **Pros**: Natural Go pattern, built-in backpressure, composable
- **Cons**: Channel overhead, goroutine management

### 3. Separate Process and Flush

The `Operator` interface has two methods:

```go
Process(event Event, out *Stream)  // Handle one event
Flush(out *Stream)                 // Emit final results
```

This cleanly handles both stateless operators (Flush is a no-op) and stateful operators (Flush emits accumulated results).

### 4. Watermark-Based Window Completion

Instead of using timers, windows are completed based on the watermark (maximum event timestamp seen). This is simpler and works well for event-time processing.

## What I Would Do Differently

1. **Use generics from the start**: Type-safe operators would catch more errors at compile time
2. **Support operator chaining syntax**: A fluent API like `stream.Filter(...).Map(...).Reduce(...)`
3. **Add operator metrics**: Latency, throughput, and state size per operator

## What Has Been Implemented

The following features have been added since the initial implementation:

### Session Windows (Gap-Based)

Session windows group events by activity gaps. Unlike tumbling/sliding windows, session windows have dynamic boundaries that depend on the data:

```go
sw := window.NewSessionWindow(30 * time.Second)
closed := sw.ProcessEvent(event) // Returns closed windows
```

**Key Insight**: Session windows require per-key state tracking since each key has independent session boundaries.

### Watermark with Bounded Out-of-Orderness

Proper watermark implementation that handles late-arriving events:

```go
wm := watermark.NewWatermark(5 * time.Second)
wm.Update(event.Timestamp)
wm.IsLate(event.Timestamp) // Check if event arrived late
```

**Key Insight**: The `maxOutOfOrderness` parameter controls the trade-off between latency and completeness. A larger value means we wait longer but handle more late events.

### Data Sources

Multiple data source implementations:

- **FileSource**: Reads from files with configurable parsing (key, value, timestamp extraction)
- **SocketSource**: TCP/UDP socket streaming
- **KafkaSource**: Kafka consumer interface with mock implementation for testing

**Key Insight**: Abstracting sources behind an interface enables testing without real I/O dependencies.

### Keyed State with Checkpoints

Per-key state management with snapshot/restore for fault tolerance:

```go
ks := state.NewKeyedState()
ks.Put("user1", "count", 42)

// Checkpoint
snapshot, _ := ks.Snapshot()

// Restore
ks.Restore(snapshot)
```

**Key Insight**: Checkpointing is essential for production systems. The checkpoint manager provides periodic snapshots with configurable retention.

### Late Event Handling

Configurable policies for handling late-arriving events:

- `DropLateEvents`: Discard events arriving after watermark
- `AllowLateEvents`: Process within allowed lateness window
- `SideOutputLateEvents`: Send to side output for separate processing

## Next Steps

To further extend this project:

1. Implement stream joins (combining two streams)
2. Add custom triggers (early firing, late data handling)
3. Add metrics and monitoring
4. Create a DSL for pipeline definition
5. Implement exactly-once semantics
6. Support distributed execution across multiple nodes

## Resources That Helped

1. **"Streaming Systems" by Akidau, Slava & Huesuke**: The definitive guide to stream processing theory
2. **Apache Beam Documentation**: Excellent API design reference
3. **Apache Flink Internals**: State management and checkpointing patterns
4. **Go Concurrency Patterns**: The Go blog's concurrency articles
5. **Google Dataflow Paper**: The theoretical foundation for modern stream processing

# Stream Processing Framework - Design Document

## Architecture Overview

```
                    +-----------------+
                    |   Data Source   |
                    +--------+--------+
                             |
                    +--------v--------+
                    |   Input Stream   |
                    +--------+--------+
                             |
                    +--------v--------+
                    |   Pipeline      |
                    |  +-----------+  |
                    |  | Operator 1|  |
                    |  +-----------+  |
                    |  | Operator 2|  |
                    |  +-----------+  |
                    |  | Operator N|  |
                    |  +-----------+  |
                    +--------+--------+
                             |
                    +--------v--------+
                    |  Output Stream  |
                    +--------+--------+
                             |
                    +--------v--------+
                    |     Sink        |
                    +-----------------+
```

## Core Abstractions

### 1. Event (core/event.go)

The fundamental data unit in the stream.

```go
type Event struct {
    Key       string
    Value     interface{}
    Timestamp time.Time
}
```

**Design decisions:**
- `interface{}` for Value allows any data type (Go generics would be ideal but adds complexity)
- Timestamp enables event-time processing and windowing
- Key enables per-key aggregation

### 2. Stream (core/stream.go)

A channel-based data stream with lifecycle management.

```go
type Stream struct {
    events chan Event
    done   chan struct{}
}
```

**Design decisions:**
- Channel-based for Go-idiomatic concurrency
- Buffered channels for backpressure
- `done` channel for clean shutdown signaling
- `Emit` returns false if stream is closed (non-blocking check)

### 3. Window (core/event.go)

Represents a time interval `[Start, End)`.

```go
type Window struct {
    Start time.Time
    End   time.Time
}
```

**Design decisions:**
- Start-inclusive, End-exclusive (standard convention)
- Used as map key for windowed state
- Duration computed on demand

## Operator Design

### Interface

```go
type Operator interface {
    Process(event Event, out *Stream)
    Flush(out *Stream)
}
```

**Design decisions:**
- Each operator reads from input and writes to output stream
- `Flush` handles stateful operators' final emission
- Operators are composable through the Pipeline

### Stateless Operators

- **MapOperator**: Applies `MapFunc` to transform values
- **FilterOperator**: Applies `FilterFunc` to predicate events
- **FlatMapOperator**: Applies `FlatMapFunc` to split events

These operators have no internal state and process each event independently.

### Stateful Operators

- **ReduceByKeyOperator**: Accumulates values per key
  - Internal `map[string]interface{}` state
  - Emits results on `Flush`

- **WindowedReduceOperator**: Per-window aggregation
  - `map[Window][]Event` buffer
  - Watermark-based window completion
  - Supports both tumbling and sliding windows

## Windowing Strategy

### Window Assignment

Each event is assigned to one or more windows based on its timestamp:

```
TumblingWindow.Assign(ts) -> Window
SlidingWindow.Assign(ts)  -> []Window
```

### Window Alignment

Windows are aligned to the epoch (Unix timestamp 0):

```
For window_size = 10s:
  ts=0-9  -> Window[0, 10)
  ts=10-19 -> Window[10, 20)
```

### Watermark Progress

The watermark advances as new events arrive:

```
watermark = max(watermark, event.Timestamp)
```

When `watermark >= window.End`, the window is considered complete.

## Pipeline Execution

### Sequential Execution

```
for each event in input:
    for each operator in pipeline:
        event = operator.Process(event)
    emit event to output
```

### Parallel Execution

```
spawn N workers
for each event in input:
    worker = next_worker (round-robin)
    worker.process(event)
```

Each worker independently runs the full operator chain. This works for stateless operators. Stateful operators would need partitioning.

## State Management

### StateStore

A thread-safe key-value store:

```go
type StateStore struct {
    mu    sync.RWMutex
    store map[string]interface{}
}
```

**Features:**
- Concurrent read/write safety
- Atomic update via `Update(key, fn)`
- Bulk operations (Keys, Clear, Size)

### WindowState

Scoped state management for windowed operations:

```go
type WindowState struct {
    windows map[Window]*StateStore
    maxAge  time.Duration
}
```

**Features:**
- Per-window state isolation
- Automatic expiration of old window states
- Lazy creation on first access

## Concurrency Model

### Goroutine-per-Operator

Each intermediate operator in the pipeline runs in its own goroutine:

```
Goroutine 1: Read from input -> Process through Op1 -> Write to channel1
Goroutine 2: Read from channel1 -> Process through Op2 -> Write to channel2
Main:        Read from channel2 -> Process through Op3 -> Write to output
```

This enables pipelining: Op1 can process event N+1 while Op2 processes event N.

### Thread Safety

- Streams use buffered channels (inherently thread-safe)
- StateStore uses RWMutex for concurrent access
- WindowedReduceOperator uses Mutex for buffer access

## Trade-offs

| Decision | Pros | Cons |
|----------|------|------|
| `interface{}` for values | Flexible, simple | No compile-time type safety |
| Channel-based streams | Go-idiomatic, natural backpressure | Channel overhead |
| Sequential pipeline | Simple, correct | No operator-level parallelism |
| Map-keyed state | Simple | No automatic cleanup |
| Epoch-aligned windows | Deterministic | May not match business logic |

## Future Extensions

1. **Generics**: Replace `interface{}` with type parameters
2. **Checkpointing**: Periodic state snapshots for fault tolerance
3. **Session Windows**: Gap-based dynamic windows
4. **Joins**: Combine multiple input streams
5. **Triggers**: Custom window firing policies
6. **Metrics**: Operator-level latency and throughput tracking

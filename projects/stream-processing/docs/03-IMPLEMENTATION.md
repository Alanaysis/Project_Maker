# Stream Processing Framework - Implementation Guide

## Project Structure

```
stream-processing/
├── cmd/
│   └── pipeline/
│       └── main.go          # Demo application
├── internal/
│   ├── core/
│   │   ├── event.go         # Event and Window types
│   │   ├── stream.go        # Channel-based stream
│   │   ├── event_test.go
│   │   └── stream_test.go
│   ├── window/
│   │   ├── assigner.go      # Window assignment logic
│   │   ├── tumbling.go      # Tumbling window
│   │   ├── sliding.go       # Sliding window
│   │   └── window_test.go
│   ├── operator/
│   │   ├── operator.go      # Operator interface + FuncOperator
│   │   ├── map.go           # Map operator
│   │   ├── filter.go        # Filter operator
│   │   ├── flatmap.go       # FlatMap operator
│   │   ├── reduce.go        # ReduceByKey operator
│   │   ├── windowed_reduce.go # Windowed aggregation
│   │   └── operator_test.go
│   ├── state/
│   │   ├── state.go         # Key-value state store
│   │   ├── window_state.go  # Window-scoped state
│   │   └── state_test.go
│   └── pipeline/
│       ├── pipeline.go      # Pipeline orchestrator
│       └── pipeline_test.go
├── docs/
│   ├── 01-RESEARCH.md
│   ├── 02-DESIGN.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── go.mod
├── README.md
└── LEARNING_NOTES.md
```

## Implementation Details

### Core Types

#### Event

Events are the data units flowing through the system:

```go
type Event struct {
    Key       string
    Value     interface{}
    Timestamp time.Time
}
```

Key design choices:
- `interface{}` for Value allows maximum flexibility
- Timestamp is set at creation time (event time, not processing time)
- Two constructors: `NewEvent` (current time) and `NewEventWithTime` (explicit)

#### Stream

Streams are channel-based with lifecycle management:

```go
type Stream struct {
    events chan Event
    done   chan struct{}
}
```

- `Emit` sends an event, returns false if stream is closed
- `Close` signals both the event channel and done channel
- `Events` returns a read-only channel for consumers

### Operator Implementation

#### Map Operator

The simplest stateless operator:

```go
func (m *MapOperator) Process(event Event, out *Stream) {
    result := Event{
        Key:       event.Key,
        Value:     m.fn(event.Value),
        Timestamp: event.Timestamp,
    }
    out.Emit(result)
}
```

#### Filter Operator

Predicate-based filtering:

```go
func (f *FilterOperator) Process(event Event, out *Stream) {
    if f.fn(event) {
        out.Emit(event)
    }
}
```

#### ReduceByKey Operator

Accumulates values per key:

```go
func (r *ReduceByKeyOperator) Process(event Event, out *Stream) {
    if existing, ok := r.state[event.Key]; ok {
        r.state[event.Key] = r.fn(existing, event.Value)
    } else {
        r.state[event.Key] = event.Value
    }
}
```

Flush emits all accumulated results.

#### WindowedReduce Operator

The most complex operator:

1. Assigns each event to window(s) based on timestamp
2. Buffers events per window
3. On flush, reduces buffered events and emits results
4. Thread-safe via mutex

### Window Assignment

#### Tumbling Window

Each timestamp maps to exactly one window:

```go
func (tw *TumblingWindow) Assign(ts time.Time) Window {
    start := alignTimestamp(ts)
    return Window{Start: start, End: start.Add(tw.size)}
}
```

#### Sliding Window

Each timestamp may map to multiple windows:

```go
func (sw *SlidingWindow) Assign(ts time.Time) []Window {
    // Walk backwards by slide intervals
    // Return all windows that contain ts
}
```

### Pipeline Execution

#### Sequential Mode

Chains operators through intermediate streams:

```
input -> [Op1] -> chan1 -> [Op2] -> chan2 -> [Op3] -> output
```

Each intermediate operator runs in its own goroutine for pipelining.

#### Parallel Mode

Distributes events across N workers:

```
input -> [Worker1: Op1 -> Op2 -> Op3] -> output
       -> [Worker2: Op1 -> Op2 -> Op3] -> output
       -> [Worker3: Op1 -> Op2 -> Op3] -> output
```

Each worker independently processes its assigned events.

### State Management

#### StateStore

Thread-safe key-value store with:
- Basic CRUD (Get, Put, Delete)
- Atomic update (`Update(key, fn)`)
- Bulk operations (Keys, Clear, Size)

#### WindowState

Manages per-window state with automatic expiration:

```go
ws := NewWindowState(1 * time.Hour)
store := ws.GetState(window)
store.Put("count", 42)
ws.Expire(time.Now())  // Cleans up old windows
```

## Go-Specific Patterns Used

1. **Channel-based streams**: Go's native concurrency primitive
2. **Goroutine pipelines**: Each operator stage runs concurrently
3. **sync.RWMutex**: Read-heavy state access optimization
4. **sync.WaitGroup**: Parallel worker coordination
5. **Functional options**: Could be used for configuration (not implemented)
6. **Package-level organization**: `internal/` prevents external imports

## Performance Considerations

1. **Buffer sizes**: Streams use configurable buffer sizes
2. **Lock granularity**: Per-operator mutexes, not global locks
3. **Channel selection**: `select` with `done` channel for non-blocking close
4. **Map pre-allocation**: State stores use `make(map, 0)` for initial allocation

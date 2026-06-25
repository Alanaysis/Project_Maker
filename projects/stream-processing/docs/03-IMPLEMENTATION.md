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
│   │   ├── time_semantics.go # Time characteristics, late events
│   │   ├── event_test.go
│   │   └── stream_test.go
│   ├── window/
│   │   ├── assigner.go      # Window assignment logic
│   │   ├── tumbling.go      # Tumbling window
│   │   ├── sliding.go       # Sliding window
│   │   ├── session.go       # Session window
│   │   ├── window_test.go
│   │   └── session_test.go
│   ├── operator/
│   │   ├── operator.go      # Operator interface + FuncOperator
│   │   ├── map.go           # Map operator
│   │   ├── filter.go        # Filter operator
│   │   ├── flatmap.go       # FlatMap operator
│   │   ├── keyby.go         # KeyBy operator
│   │   ├── reduce.go        # ReduceByKey operator
│   │   ├── windowed_reduce.go # Windowed aggregation
│   │   └── operator_test.go
│   ├── source/
│   │   ├── source.go        # Source interface
│   │   ├── file_source.go   # File-based source
│   │   ├── socket_source.go # TCP/UDP socket source
│   │   ├── kafka_source.go  # Kafka source (with mock)
│   │   └── source_test.go
│   ├── state/
│   │   ├── state.go         # Key-value state store
│   │   ├── window_state.go  # Window-scoped state
│   │   ├── keyed_state.go   # Keyed state + checkpointing
│   │   ├── state_test.go
│   │   └── keyed_state_test.go
│   ├── watermark/
│   │   ├── watermark.go     # Watermark tracking
│   │   └── watermark_test.go
│   └── pipeline/
│       ├── pipeline.go      # Pipeline orchestrator
│       └── pipeline_test.go
├── examples/
│   ├── realtime_stats.go    # Real-time statistics
│   ├── anomaly_detection.go # Anomaly detection
│   └── etl_pipeline.go      # ETL pipeline
├── docs/
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

#### Time Semantics

Three time characteristics supported:

```go
type TimeCharacteristic int
const (
    ProcessingTime TimeCharacteristic = iota  // System clock
    EventTime                                  // Event timestamp
    IngestionTime                              // Ingestion time
)
```

Late event handling policies:
- `DropLateEvents`: Discard events arriving after watermark
- `AllowLateEvents`: Process within allowed lateness window
- `SideOutputLateEvents`: Send to side output

### Data Sources

#### Source Interface

```go
type Source interface {
    Name() string
    Open() (*Stream, error)
    Stop() error
}
```

#### FileSource

Reads lines from a file:

```go
src := NewFileSource("data.log",
    WithKeyFunc(func(line string, num int) string { return "log" }),
    WithValueFunc(func(line string) interface{} { return parse(line) }),
    WithTimestampFunc(func(line string) time.Time { return extractTime(line) }),
)
```

#### SocketSource

Reads from TCP/UDP connections:

```go
src := NewSocketSource("tcp", "localhost:9999")
stream, _ := src.Open()
```

#### KafkaSource

Reads from Kafka topics (uses interface for mock/real implementations):

```go
consumer := NewMockKafkaConsumer(messages)
src := NewKafkaSource(consumer, []string{"topic1", "topic2"})
```

### Operator Implementation

#### KeyBy Operator

Re-keys events based on value:

```go
func (k *KeyByOperator) Process(event Event, out *Stream) {
    result := Event{
        Key:       k.fn(event.Value),
        Value:     event.Value,
        Timestamp: event.Timestamp,
    }
    out.Emit(result)
}
```

#### WindowedReduce Operator

The most complex operator:

1. Assigns each event to window(s) based on timestamp
2. Buffers events per window
3. On flush, reduces buffered events and emits results
4. Thread-safe via mutex

### Window Types

#### Tumbling Window

Each timestamp maps to exactly one window:

```go
tw := NewTumblingWindow(5 * time.Second)
win := tw.Assign(event.Timestamp)
```

#### Sliding Window

Each timestamp may map to multiple windows:

```go
sw := NewSlidingWindow(10*time.Second, 5*time.Second)
windows := sw.Assign(event.Timestamp)
```

#### Session Window

Gap-based dynamic windows:

```go
sw := NewSessionWindow(30 * time.Second)
closedWindows := sw.ProcessEvent(event) // Returns closed windows
```

Session windows close when the gap between events exceeds the threshold.

### Watermark

Tracks event-time progress:

```go
wm := NewWatermark(5 * time.Second)
wm.Update(event.Timestamp)        // Advances watermark
wm.IsLate(event.Timestamp)        // Checks if event is late
wm.Current()                      // Returns current watermark
```

Policies:
- `BoundedOutOfOrdernessPolicy`: watermark = max(ts) - outOfOrderness
- `PeriodicWatermarkGenerator`: Emits watermarks at fixed intervals

### State Management

#### KeyedState

Per-key state with checkpointing:

```go
ks := NewKeyedState()
ks.Put("user1", "name", "Alice")
ks.Put("user1", "count", 42)

// Snapshot for checkpointing
snapshot, _ := ks.Snapshot()

// Restore from snapshot
ks2 := NewKeyedState()
ks2.Restore(snapshot)

// Expire old keys
ks.Expire(1 * time.Hour)
```

#### CheckpointManager

Periodic state checkpointing:

```go
cm := NewCheckpointManager(10*time.Second, 5) // 10s interval, keep 5
cm.Register(keyedState)
ch := cm.Start() // Channel receives checkpoint IDs
```

### Pipeline Execution

#### Sequential Mode

Chains operators through intermediate streams:

```
input -> [Op1] -> chan1 -> [Op2] -> chan2 -> [Op3] -> output
```

#### Parallel Mode

Distributes events across N workers:

```
input -> [Worker1: Op1 -> Op2 -> Op3] -> output
       -> [Worker2: Op1 -> Op2 -> Op3] -> output
       -> [Worker3: Op1 -> Op2 -> Op3] -> output
```

## Go-Specific Patterns Used

1. **Channel-based streams**: Go's native concurrency primitive
2. **Goroutine pipelines**: Each operator stage runs concurrently
3. **sync.RWMutex**: Read-heavy state access optimization
4. **sync.WaitGroup**: Parallel worker coordination
5. **Functional options**: Configuration via `WithXxx` functions
6. **Package-level organization**: `internal/` prevents external imports

## Performance Considerations

1. **Buffer sizes**: Streams use configurable buffer sizes
2. **Lock granularity**: Per-operator mutexes, not global locks
3. **Channel selection**: `select` with `done` channel for non-blocking close
4. **Map pre-allocation**: State stores use `make(map, 0)` for initial allocation

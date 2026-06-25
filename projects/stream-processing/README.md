# Stream Processing Framework

A complete stream processing framework implemented in Go. This project demonstrates core concepts of stream processing including event-driven data flow, time-windowed aggregation, operator chaining, state management, data sources, watermarks, and session windows.

## Features

### Data Sources
- **File Source**: Read from files with configurable parsing
- **Socket Source**: TCP/UDP socket streaming
- **Kafka Source**: Kafka consumer interface with mock implementation

### Operators
- **Map**: Transform each event's value
- **Filter**: Keep events matching a predicate
- **FlatMap**: Split one event into zero or more
- **KeyBy**: Re-key events for partitioning
- **ReduceByKey**: Per-key aggregation
- **WindowedReduce**: Aggregate within time windows

### Windows
- **Tumbling**: Fixed-size, non-overlapping
- **Sliding**: Fixed-size, overlapping
- **Session**: Gap-based, dynamic boundaries

### State Management
- **KeyedState**: Per-key state with snapshots
- **WindowState**: Window-scoped state with expiration
- **CheckpointManager**: Periodic state checkpointing

### Time Semantics
- **Processing Time**: System clock
- **Event Time**: Event timestamp
- **Watermark**: Event-time progress tracking
- **Late Events**: Configurable handling policies

## Architecture

```
Data Source -> Stream -> [Pipeline: KeyBy -> Filter -> Map -> WindowedReduce] -> Output
```

### Core Loop

```
Data Flow -> Window Assignment -> Watermark Update -> Aggregation -> Output
```

## Project Structure

```
stream-processing/
├── cmd/pipeline/main.go           # Demo application
├── internal/
│   ├── core/                      # Event, Stream, TimeSemantics
│   ├── window/                    # Tumbling, Sliding, Session windows
│   ├── operator/                  # Map, Filter, FlatMap, KeyBy, Reduce
│   ├── source/                    # File, Socket, Kafka sources
│   ├── state/                     # KeyedState, WindowState, Checkpoint
│   ├── watermark/                 # Watermark tracking
│   └── pipeline/                  # Pipeline orchestrator
├── examples/                      # Real-world examples
│   ├── realtime_stats.go          # Real-time statistics
│   ├── anomaly_detection.go       # Anomaly detection
│   └── etl_pipeline.go            # ETL pipeline
├── docs/                          # Design docs (01-05)
└── README.md
```

## Quick Start

```bash
# Run the demo
cd projects/stream-processing
go run cmd/pipeline/main.go

# Run examples
go run examples/realtime_stats.go
go run examples/anomaly_detection.go
go run examples/etl_pipeline.go

# Run all tests
go test ./...

# Run tests with race detector
go test -race ./...
```

## Demo Scenarios

The demo includes 6 scenarios:

1. **Basic Map Pipeline**: Double numbers
2. **Filter + Map**: Keep positives, then square
3. **Reduce By Key**: Per-sensor aggregation
4. **Windowed Aggregation**: 5-second tumbling window sums
5. **FlatMap**: Sentence to word splitting
6. **Parallel Pipeline**: Multi-worker execution

## Core Concepts

### Events

```go
type Event struct {
    Key       string
    Value     interface{}
    Timestamp time.Time
}
```

### Data Sources

```go
// File source
src := source.NewFileSource("data.log",
    source.WithKeyFunc(func(line string, num int) string { return "log" }),
    source.WithValueFunc(func(line string) interface{} { return parse(line) }),
)
stream, err := src.Open()

// Socket source
src := source.NewSocketSource("tcp", "localhost:9999")

// Kafka source
consumer := source.NewMockKafkaConsumer(messages)
src := source.NewKafkaSource(consumer, []string{"topic1"})
```

### Operators

| Operator       | Description                          |
|----------------|--------------------------------------|
| Map            | Transform each event's value         |
| Filter         | Keep events matching a predicate     |
| FlatMap        | Split one event into zero or more    |
| KeyBy          | Re-key events for partitioning       |
| ReduceByKey    | Accumulate values per key            |
| WindowedReduce | Aggregate within time windows        |

### Windows

```go
// Tumbling: fixed-size, non-overlapping
tw := window.NewTumblingWindow(5 * time.Second)

// Sliding: fixed-size, overlapping
sw := window.NewSlidingWindow(10*time.Second, 5*time.Second)

// Session: gap-based, dynamic
sess := window.NewSessionWindow(30 * time.Second)
closed := sess.ProcessEvent(event)
```

### Watermark

```go
wm := watermark.NewWatermark(5 * time.Second)
wm.Update(event.Timestamp)
if wm.IsLate(event.Timestamp) {
    // Handle late event
}
```

### State Management

```go
// Keyed state
ks := state.NewKeyedState()
ks.Put("user1", "name", "Alice")

// Checkpoint
cm := state.NewCheckpointManager(10*time.Second, 5)
cm.Register(ks)
cm.Start()
```

### Pipeline

```go
p := pipeline.NewPipeline()
p.AddOperator(operator.NewFilterOperator(...))
p.AddOperator(operator.NewMapOperator(...))
output := p.Execute(input)

// Or parallel
output := p.ExecuteParallel(input, 4)
```

## Examples

### Real-time Statistics
Demonstrates sensor aggregation, sliding window averages, and keyed state tracking.

### Anomaly Detection
Shows threshold-based, moving average, and Z-score detection methods.

### ETL Pipeline
Log parsing, data enrichment with lookup tables, and category aggregation.

## Documentation

- [Research](docs/01-RESEARCH.md) - Stream processing theory and models
- [Design](docs/02-DESIGN.md) - Architecture and design decisions
- [Implementation](docs/03-IMPLEMENTATION.md) - Code structure and details
- [Testing](docs/04-TESTING.md) - Test strategy and coverage
- [Development](docs/05-DEVELOPMENT.md) - Development log and lessons
- [Learning Notes](LEARNING_NOTES.md) - Personal learning reflections

## Dependencies

None. Uses only the Go standard library.

## License

MIT

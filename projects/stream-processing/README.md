# Stream Processing Framework

A minimal stream processing framework implemented in Go. This project demonstrates core concepts of stream processing including event-driven data flow, time-windowed aggregation, operator chaining, and state management.

## Learning Objectives

- Understand stream processing models (dataflow, event-driven)
- Master windowing strategies (tumbling, sliding)
- Learn stateful operator design and state management
- Practice Go concurrency patterns (goroutines, channels, mutexes)

## Architecture

```
Data Source -> Stream -> [Pipeline: Filter -> Map -> WindowedReduce] -> Output
```

### Core Loop

```
Data Flow -> Window Assignment -> Aggregation -> Output
```

## Project Structure

```
stream-processing/
├── cmd/pipeline/main.go        # Demo application
├── internal/
│   ├── core/                   # Event, Stream, Window types
│   ├── window/                 # Tumbling & Sliding window assignment
│   ├── operator/               # Map, Filter, FlatMap, Reduce, WindowedReduce
│   ├── state/                  # Key-value state store, Window-scoped state
│   └── pipeline/               # Pipeline orchestrator
├── docs/                       # Design docs (01-05)
├── go.mod
├── README.md
└── LEARNING_NOTES.md
```

## Quick Start

```bash
# Run the demo
cd projects/stream-processing
go run cmd/pipeline/main.go

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

### Operators

| Operator    | Description                          |
|-------------|--------------------------------------|
| Map         | Transform each event's value         |
| Filter      | Keep events matching a predicate     |
| FlatMap     | Split one event into zero or more    |
| ReduceByKey | Accumulate values per key            |
| WindowedReduce | Aggregate within time windows     |

### Windows

- **Tumbling**: Fixed-size, non-overlapping (each event in exactly one window)
- **Sliding**: Fixed-size, overlapping (event may be in multiple windows)

### Pipeline

```go
p := pipeline.NewPipeline()
p.AddOperator(operator.NewFilterOperator(...))
p.AddOperator(operator.NewMapOperator(...))
output := p.Execute(input)
```

### State Management

```go
store := state.NewStateStore()
store.Put("counter", 0)
store.Update("counter", func(current interface{}) interface{} {
    return current.(int) + 1
})
```

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

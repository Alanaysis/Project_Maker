# Stream Processing Framework - Testing Guide

## Test Strategy

### Unit Tests

Each package has dedicated unit tests:

| Package    | Test File                | Focus                         |
|------------|--------------------------|-------------------------------|
| core       | event_test.go, stream_test.go | Event creation, stream lifecycle |
| window     | window_test.go           | Window assignment, boundaries    |
| operator   | operator_test.go         | All operator types               |
| state      | state_test.go            | StateStore, WindowState          |
| pipeline   | pipeline_test.go         | Pipeline chaining, parallelism   |

### Test Categories

1. **Correctness**: Operators produce expected output for given input
2. **Edge cases**: Empty streams, single events, boundary timestamps
3. **Concurrency**: Thread safety under parallel access
4. **Lifecycle**: Stream open/close, operator flush behavior

## Running Tests

```bash
# Run all tests
go test ./...

# Run with verbose output
go test -v ./...

# Run specific package tests
go test ./internal/operator/
go test ./internal/state/

# Run with race detector
go test -race ./...

# Run benchmarks
go test -bench=. ./...
```

## Test Helpers

### Stream Helpers

```go
// Drain all events from a stream into a slice
func drainStream(s *core.Stream) []core.Event

// Create a pre-filled stream that closes after emitting
func streamFrom(events ...core.Event) *core.Stream
```

## Key Test Cases

### Event Tests

- `TestNewEvent`: Verify key, value, and auto-timestamp
- `TestNewEventWithTime`: Verify explicit timestamp
- `TestWindowContains`: Boundary conditions (start-inclusive, end-exclusive)
- `TestWindowDuration`: Duration calculation

### Window Tests

- `TestTumblingWindowAssign`: Events map to correct windows
- `TestSlidingWindowAssign`: Events map to multiple windows
- `TestSlidingWindowSizeAndSlide`: Accessor methods

### Operator Tests

- `TestMapOperator`: Value transformation
- `TestFilterOperator`: Predicate filtering
- `TestReduceByKeyOperator`: Per-key accumulation
- `TestFlatMapOperator`: One-to-many transformation
- `TestFuncOperator`: Generic function operator
- `TestWindowedReduceOperatorTumbling`: Window-scoped aggregation

### State Tests

- `TestStateStoreBasicOperations`: CRUD operations
- `TestStateStoreGetOrDefault`: Default value handling
- `TestStateStoreUpdate`: Atomic read-modify-write
- `TestStateStoreConcurrency`: Thread safety with 100 concurrent goroutines
- `TestWindowState`: Window-scoped state creation and access
- `TestWindowStateExpire`: Automatic cleanup of old windows

### Pipeline Tests

- `TestPipelineEmpty`: Passthrough with no operators
- `TestPipelineSingleOperator`: Single map operator
- `TestPipelineFilterThenMap`: Chained filter + map
- `TestPipelineThreeOperators`: Multi-stage pipeline
- `TestPipelineParallel`: Parallel execution with multiple workers

## Race Condition Testing

The `-race` flag is critical for this project due to heavy concurrency:

```bash
go test -race ./...
```

Key areas tested:
- Stream emit/read from multiple goroutines
- StateStore concurrent read/write
- WindowedReduceOperator buffer access
- Pipeline parallel worker execution

## Coverage

Target: 80%+ line coverage across all packages.

```bash
go test -cover ./...
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

## Manual Testing

Run the demo application to verify end-to-end behavior:

```bash
go run cmd/pipeline/main.go
```

Expected output:
1. Basic Map pipeline doubling numbers
2. Filter + Map pipeline (keep positives, square)
3. ReduceByKey aggregation per sensor
4. Windowed aggregation (5-second tumbling windows)
5. FlatMap word splitting
6. Parallel pipeline execution

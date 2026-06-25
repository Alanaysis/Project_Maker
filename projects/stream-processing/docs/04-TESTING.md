# Stream Processing Framework - Testing Guide

## Test Strategy

### Unit Tests

Each package has dedicated unit tests:

| Package    | Test Files                   | Focus                              |
|------------|------------------------------|------------------------------------|
| core       | event_test.go, stream_test.go| Event creation, stream lifecycle   |
| window     | window_test.go, session_test.go | Window assignment, session windows |
| operator   | operator_test.go             | All operator types                 |
| source     | source_test.go               | File, socket, Kafka sources        |
| state      | state_test.go, keyed_state_test.go | StateStore, KeyedState, checkpoints |
| watermark  | watermark_test.go            | Watermark tracking, policies       |
| pipeline   | pipeline_test.go             | Pipeline chaining, parallelism     |

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
go test ./internal/window/
go test ./internal/source/
go test ./internal/watermark/

# Run with race detector
go test -race ./...

# Run benchmarks
go test -bench=. ./...
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
- `TestSessionWindow`: Gap-based window creation and closing
- `TestSessionWindowMultipleKeys`: Per-key session isolation
- `TestSessionWindowOperator`: Session-based aggregation

### Operator Tests

- `TestMapOperator`: Value transformation
- `TestFilterOperator`: Predicate filtering
- `TestReduceByKeyOperator`: Per-key accumulation
- `TestFlatMapOperator`: One-to-many transformation
- `TestFuncOperator`: Generic function operator
- `TestWindowedReduceOperatorTumbling`: Window-scoped aggregation

### Source Tests

- `TestFileSourceBasicRead`: Read all lines from file
- `TestFileSourceWithKeyFunc`: Custom key extraction
- `TestFileSourceWithValueFunc`: Custom value transformation
- `TestFileSourceStop`: Graceful stop behavior
- `TestFileSourceFileNotFound`: Error handling
- `TestSocketSource`: Naming and configuration
- `TestKafkaSourceMockConsumer`: Mock consumer integration
- `TestParseCSVLine`: CSV parsing
- `TestParseKeyValueLine`: Key-value parsing

### State Tests

- `TestStateStoreBasicOperations`: CRUD operations
- `TestStateStoreUpdate`: Atomic read-modify-write
- `TestKeyedState`: Per-key state isolation
- `TestKeyedStateExpire`: Automatic key expiration
- `TestKeyedStateSnapshot`: Snapshot and restore
- `TestCheckpointManager`: Manual and auto checkpointing
- `TestCheckpointRetention`: Retention policy enforcement

### Watermark Tests

- `TestWatermarkBasicUpdate`: Watermark advancement
- `TestWatermarkForwardOnly`: Never moves backward
- `TestWatermarkIsLate`: Late event detection
- `TestBoundedOutOfOrdernessPolicy`: Policy computation
- `TestPeriodicWatermarkGenerator`: Periodic emission

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
- KeyedState concurrent access
- Watermark updates

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

Run examples for real-world scenarios:

```bash
go run examples/realtime_stats.go
go run examples/anomaly_detection.go
go run examples/etl_pipeline.go
```

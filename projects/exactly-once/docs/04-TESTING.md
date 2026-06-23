# Exactly-Once Semantics Testing

## Test Strategy

### Unit Tests

Each package has focused unit tests:

1. **Message Tests**: State transitions, idempotency key generation, retry logic
2. **Dedup Tests**: New/duplicate/in-progress detection, TTL, concurrency
3. **Processor Tests**: Idempotent processing, retry, callbacks, exactly-once guarantee
4. **Transaction Tests**: Commit, rollback, state management
5. **Tracker Tests**: Event recording, state queries, cleanup

### Integration Tests

The demo program (`cmd/demo/main.go`) serves as an integration test showing all components working together.

## Running Tests

### All Tests

```bash
go test ./...
```

### Verbose Output

```bash
go test ./... -v
```

### Specific Package

```bash
go test ./internal/message -v
go test ./internal/dedup -v
go test ./internal/processor -v
go test ./internal/transaction -v
go test ./internal/tracker -v
```

### With Coverage

```bash
go test ./... -cover
```

### Race Detection

```bash
go test ./... -race
```

## Test Cases

### Message Tests

#### State Transitions

```go
func TestMessageStateTransitions(t *testing.T) {
    msg := New("msg-001", []byte("test"))

    // PENDING -> PROCESSING -> COMPLETED
    msg.MarkProcessing()
    assert state == PROCESSING

    msg.MarkCompleted([]byte("result"))
    assert state == COMPLETED
    assert ProcessedAt != nil
}
```

#### Retry Logic

```go
func TestMessageCanRetry(t *testing.T) {
    msg := New("msg-001", []byte("test"))
    msg.MaxRetries = 2

    // Can retry when failed and count < max
    msg.MarkFailed("error")
    assert msg.CanRetry() == true

    // Cannot retry when count >= max
    msg.IncrementRetry()
    msg.MarkFailed("error")
    msg.IncrementRetry()
    msg.MarkFailed("error")
    assert msg.CanRetry() == false
}
```

#### Idempotency Key Determinism

```go
func TestGenerateIdempotencyKey(t *testing.T) {
    // Same input produces same key
    key1 := GenerateIdempotencyKey("msg-001", []byte("payload"))
    key2 := GenerateIdempotencyKey("msg-001", []byte("payload"))
    assert key1 == key2

    // Different input produces different key
    key3 := GenerateIdempotencyKey("msg-002", []byte("payload"))
    assert key1 != key3
}
```

### Dedup Tests

#### Basic Deduplication

```go
func TestDeduplicatorDuplicate(t *testing.T) {
    d := New()

    // First check - new
    d.Check("key-001")
    d.MarkCompleted("key-001", []byte("done"))

    // Second check - duplicate
    result := d.Check("key-001")
    assert result == ResultDuplicate
}
```

#### TTL Expiration

```go
func TestDeduplicatorTTL(t *testing.T) {
    d := New(WithTTL(50 * time.Millisecond))

    d.Check("key-001")
    d.MarkCompleted("key-001", []byte("done"))

    // Before TTL - duplicate
    assert d.Check("key-001") == ResultDuplicate

    // After TTL - treated as new
    time.Sleep(60 * time.Millisecond)
    assert d.Check("key-001") == ResultNew
}
```

#### Concurrent Access

```go
func TestDeduplicatorConcurrency(t *testing.T) {
    d := New()

    // 100 goroutines check the same key
    for i := 0; i < 100; i++ {
        go func() {
            result := d.Check("key-shared")
            if result == ResultNew {
                d.MarkCompleted("key-shared", []byte("done"))
            }
        }()
    }

    // Exactly one should have been new
    stats := d.StatsSnapshot()
    assert stats.NewMessages == 1
}
```

### Processor Tests

#### Exactly-Once Guarantee

```go
func TestProcessorIdempotency(t *testing.T) {
    p := New()
    var sideEffectCount int32

    p.Register("transfer", func(msg *Message) ([]byte, error) {
        atomic.AddInt32(&sideEffectCount, 1)
        return []byte("transferred"), nil
    })

    // Same message delivered 5 times
    for i := 0; i < 5; i++ {
        msg := New(fmt.Sprintf("delivery-%d", i), []byte("data"))
        msg.IdempotencyKey = "transfer-order-123" // Same logical operation
        p.Process(msg, "transfer")
    }

    // Side effect occurs exactly once
    assert atomic.LoadInt32(&sideEffectCount) == 1
}
```

#### Retry with Eventual Success

```go
func TestProcessorRetry(t *testing.T) {
    p := New()
    var attempts int32

    p.Register("flaky", func(msg *Message) ([]byte, error) {
        count := atomic.AddInt32(&attempts, 1)
        if count < 3 {
            return nil, errors.New("temporary failure")
        }
        return []byte("success"), nil
    })

    msg := New("msg-001", []byte("data"))
    msg.MaxRetries = 3

    err := p.Process(msg, "flaky")
    assert err == nil
    assert msg.State == StateCompleted
    assert msg.RetryCount == 2
}
```

### Transaction Tests

#### Successful Transaction

```go
func TestTransactionExecute(t *testing.T) {
    txn := New("txn-001")

    txn.Add(&Operation{
        Name: "step1",
        Execute: func() (interface{}, error) { return "ok", nil },
    })
    txn.Add(&Operation{
        Name: "step2",
        Execute: func() (interface{}, error) { return "ok", nil },
    })

    err := txn.Execute()
    assert err == nil
    assert txn.State == StateCommitted
}
```

#### Rollback on Failure

```go
func TestTransactionRollback(t *testing.T) {
    txn := New("txn-001")
    var step1Undone bool

    txn.Add(&Operation{
        Name: "step1",
        Execute: func() (interface{}, error) { return "ok", nil },
        Undo: func() error { step1Undone = true; return nil },
    })
    txn.Add(&Operation{
        Name: "step2",
        Execute: func() (interface{}, error) { return nil, errors.New("fail") },
    })

    err := txn.Execute()
    assert err != nil
    assert txn.State == StateAborted
    assert step1Undone == true
}
```

### Tracker Tests

#### Event Recording

```go
func TestTrackerEvents(t *testing.T) {
    tr := New()
    msg := New("msg-001", []byte("test"))

    tr.Track(msg)
    msg.MarkProcessing()
    tr.Update(msg)
    msg.MarkCompleted([]byte("done"))
    tr.Update(msg)

    events := tr.GetEvents("msg-001")
    assert len(events) == 3
    assert events[0].ToState == StatePending
    assert events[1].ToState == StateProcessing
    assert events[2].ToState == StateCompleted
}
```

## Manual Testing

### Run Demo

```bash
go run ./cmd/demo
```

Expected output shows:
1. Deduplication detecting duplicates
2. Idempotent processing with same result
3. Transactional processing with rollback
4. Retry handling with eventual success
5. State tracking with audit trail

## Test Coverage

Run with coverage report:

```bash
go test ./... -coverprofile=coverage.out
go tool cover -html=coverage.out
```

## Continuous Integration

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-go@v2
        with:
          go-version: 1.21
      - run: go test ./... -race -cover
```

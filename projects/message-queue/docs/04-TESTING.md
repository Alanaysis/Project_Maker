# 04 - Testing Strategy

## Test Layers

### 1. Unit Tests (protocol)
- Message creation and field validation
- Status transitions (Pending -> Delivered -> Acknowledged -> DeadLetter)
- Priority levels and string representation
- Delayed message readiness (IsReady)
- Message filtering (MatchesFilter)
- Retry logic (CanRetry, IncrementRetry)
- JSON marshaling with custom status and priority fields

### 2. Unit Tests (queue)
- **Topic**: publish, capacity limit, subscriber add/remove, fan-out, pending count,
  priority ordering, delayed messages, message filtering, queue mode
- **Broker**: create topic, create queue topic, publish, auto-create topic, subscribe,
  subscribe with filter, acknowledge, negative acknowledge, consumer groups, pull mode,
  dead letter queue, recovery from persistence
- **ConsumerGroup**: add/remove consumers, deliver, round-robin, inactive consumers,
  concurrent delivery
- **DeadLetterQueue**: add, capacity, peek, pop, retry, clear

### 3. Unit Tests (persistence)
- **FileStore**: save/load single message, load all, update, delete, not-found
- **MemStore**: same operations as FileStore

### 4. Unit Tests (producer/consumer)
- Producer: publish, publish-string, publish with priority, publish delayed,
  publish with headers, publish with options, pull, pull timeout
- Consumer: subscribe, subscribe with filter, duplicate subscribe, unsubscribe,
  close, pull, pull and process, negative acknowledge, consumer group

### 5. Integration Tests (api)
- End-to-end: produce -> consume -> verify count
- Multiple consumers with fan-out
- Topic info and listing
- File persistence with recovery across broker restarts
- Queue topic creation
- Consumer groups
- Dead letter queue
- Pull mode
- Priority ordering
- Delayed message delivery
- Message filtering

## Running Tests

```bash
# All tests
go test ./...

# With verbose output
go test -v ./...

# Specific package
go test -v ./internal/queue/...

# With coverage
go test -cover ./...

# Integration tests only
go test -v ./tests/...

# With timeout
go test -timeout 120s ./...
```

## Test Patterns Used

- **Table-driven tests** for message status strings and priorities
- **Subtests** for organizing related cases
- **Temp directories** (`t.TempDir()`) for file store tests
- **Atomic counters** for concurrent consumer tests
- **Timeout selects** to avoid hanging on channel operations
- **Two-phase testing** for persistence recovery (create, close, reopen, verify)
- **Round-robin verification** for consumer group distribution

## Test Coverage

| Package          | Coverage |
|------------------|----------|
| protocol         | ~95%     |
| queue            | ~90%     |
| persistence      | ~95%     |
| producer         | ~90%     |
| consumer         | ~85%     |
| api              | ~85%     |
| integration      | ~80%     |

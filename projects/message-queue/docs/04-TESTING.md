# 04 - Testing Strategy

## Test Layers

### 1. Unit Tests (protocol)
- Message creation and field validation
- Status transitions (Pending -> Delivered -> Acknowledged)
- Status string representation
- JSON marshaling with custom status field

### 2. Unit Tests (queue)
- **Topic**: publish, capacity limit, subscriber add/remove, fan-out, pending count
- **Broker**: create topic, publish, auto-create topic, subscribe, acknowledge,
  unsubscribe, topic listing, recovery from persistence

### 3. Unit Tests (persistence)
- **FileStore**: save/load single message, load all, update, delete, not-found
- **MemStore**: same operations as FileStore

### 4. Unit Tests (producer/consumer)
- Producer publish and publish-string
- Consumer subscribe, duplicate subscribe, unsubscribe, close

### 5. Integration Tests (api)
- End-to-end: produce -> consume -> verify count
- Multiple consumers with fan-out
- Topic info and listing
- File persistence with recovery across broker restarts

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
```

## Test Patterns Used

- **Table-driven tests** for message status strings
- **Subtests** for organizing related cases
- **Temp directories** (`t.TempDir()`) for file store tests
- **Atomic counters** for concurrent consumer tests
- **Timeout selects** to avoid hanging on channel operations
- **Two-phase testing** for persistence recovery (create, close, reopen, verify)

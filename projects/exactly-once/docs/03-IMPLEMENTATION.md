# Exactly-Once Semantics Implementation

## Overview

This document describes the implementation details of the exactly-once semantics system.

## Message Implementation

### State Machine

```
PENDING ──▶ PROCESSING ──▶ COMPLETED
                │
                ▼
             FAILED ──▶ PENDING (retry)
                │
                └──▶ FAILED (exhausted)
```

### Idempotency Key Generation

```go
func GenerateIdempotencyKey(id string, payload []byte) string {
    h := sha256.New()
    h.Write([]byte(id))
    h.Write(payload)
    return fmt.Sprintf("%x", h.Sum(nil))
}
```

SHA-256 is used because:
- Deterministic: same input always produces same output
- Low collision probability: 256-bit output
- Fast: suitable for high-throughput systems

## Deduplication Implementation

### Check Flow

```go
func (d *Deduplicator) Check(key string) Result {
    entry, exists := d.entries[key]

    if !exists {
        // New message - register as in-progress
        d.entries[key] = &Entry{State: "processing", ...}
        return ResultNew
    }

    // Check TTL expiration
    if time.Since(entry.FirstSeen) > d.ttl {
        // Expired - treat as new
        return ResultNew
    }

    // Duplicate check based on state
    switch entry.State {
    case "processing":
        return ResultInProgress
    case "completed", "failed":
        return ResultDuplicate
    }
}
```

### Thread Safety

The Deduplicator uses `sync.RWMutex`:
- Read lock for `IsSeen`, `GetEntry`, `Size`
- Write lock for `Check`, `MarkCompleted`, `MarkFailed`, `Reset`

This allows concurrent read operations while serializing writes.

## Processor Implementation

### Processing Pipeline

```go
func (p *Processor) Process(msg *Message, handlerName string) error {
    // 1. Deduplication check
    dedupResult := p.dedup.Check(msg.IdempotencyKey)
    if dedupResult == dedup.ResultDuplicate {
        msg.MarkDuplicate()
        return nil
    }

    // 2. Track message
    p.tracker.Track(msg)

    // 3. Process with retry
    for attempt := 0; attempt <= msg.MaxRetries; attempt++ {
        result, err := handler(msg)
        if err == nil {
            msg.MarkCompleted(result)
            p.dedup.MarkCompleted(msg.IdempotencyKey, result)
            return nil
        }
        msg.MarkFailed(err.Error())
        if !msg.CanRetry() {
            break
        }
        msg.IncrementRetry()
    }

    return fmt.Errorf("failed after %d retries", msg.MaxRetries)
}
```

### Idempotency Guarantee

The processor achieves exactly-once by:
1. Checking deduplication BEFORE processing
2. Recording the result AFTER successful processing
3. Using the same IdempotencyKey for all deliveries of the same operation

## Transaction Implementation

### Two-Phase Commit

```go
func (t *Transaction) Prepare() error {
    for i, op := range t.Operations {
        result, err := op.Execute()
        if err != nil {
            // Roll back all executed operations
            t.rollbackExecuted(i)
            t.State = StateAborted
            return err
        }
    }
    t.State = StatePrepared
    return nil
}

func (t *Transaction) Commit() error {
    if t.State != StatePrepared {
        return errors.New("not prepared")
    }
    t.State = StateCommitted
    return nil
}
```

### Rollback Strategy

Operations are rolled back in reverse order:

```go
func (t *Transaction) rollbackExecuted(lastIndex int) {
    for i := lastIndex - 1; i >= 0; i-- {
        op := t.Operations[i]
        if op.Undo != nil {
            op.Undo()
        }
    }
}
```

Reverse order is important because later operations may depend on earlier ones.

## Tracker Implementation

### Event Recording

Each state transition is recorded as an Event:

```go
func (t *Tracker) Update(msg *Message) {
    event := Event{
        Timestamp: time.Now(),
        FromState: record.CurrentState,
        ToState:   msg.State,
        Message:   fmt.Sprintf("%s -> %s", oldState, newState),
    }
    record.Events = append(record.Events, event)
}
```

### State-Based Queries

```go
func (t *Tracker) GetByState(state State) []string {
    var ids []string
    for id, record := range t.records {
        if record.CurrentState == state {
            ids = append(ids, id)
        }
    }
    return ids
}
```

## Performance Considerations

### Memory Usage

- Each dedup entry: ~200 bytes
- Each tracking record: ~500 bytes + events
- With 10K messages: ~7MB total

### Concurrency

- All packages use RWMutex for thread safety
- Read-heavy workloads benefit from RWMutex vs Mutex
- No lock contention between different packages

### Cleanup

- Dedup: TTL-based expiration, manual Cleanup()
- Tracker: Manual Cleanup(maxAge)
- Both support Clear() for full reset

## Known Limitations

1. **In-memory only**: State is lost on restart. Production systems would use Redis or a database.

2. **No distributed coordination**: This implementation works for single-process systems. Distributed systems need consensus protocols.

3. **No persistent dedup**: Dedup entries are lost on restart. Production systems would use persistent storage.

4. **Best-effort rollback**: Failed undo operations are logged but not retried. Production systems would need compensating transactions.

5. **No message ordering**: Messages are processed in arrival order but there's no global ordering guarantee.

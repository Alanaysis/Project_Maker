# 05 - Development Notes

## Development Timeline

1. **Protocol layer**: Defined Message struct, status enum, error sentinels.
2. **Queue layer**: Implemented Topic (publish, subscribe, fan-out) then Broker
   (routing, ack, recovery).
3. **Persistence layer**: Created Store interface, then FileStore and MemStore.
4. **Producer/Consumer**: Thin wrappers with handler pattern and auto-ack.
5. **API facade**: Wired everything together with Config struct.
6. **CLI demos**: Producer and consumer commands.
7. **Tests**: Unit tests for each layer, integration tests for end-to-end.
8. **Advanced features**: Priority queue, delayed messages, consumer groups,
   dead letter queue, message filtering, pull mode.

## Design Trade-offs

### Single Node vs Distributed
Chose single-node for simplicity. A distributed version would need:
- Network transport (gRPC or TCP)
- Partitioning / sharding across nodes
- Leader election for writes
- Replication for durability

### File Persistence vs Database
JSON files are simple and inspectable but slow for high throughput.
Alternatives: SQLite, append-only log (like Kafka), embedded key-value store.

### Push vs Pull Mode
Implemented both modes:
- Push: Simpler, messages delivered via channels
- Pull: Consumer controls rate, better for batch processing

### Priority Queue Implementation
Used Go's `container/heap` for O(log n) operations. Alternative would be
multiple queues per priority level, but heap is more memory efficient.

### Consumer Groups vs Competing Consumers
Consumer groups provide a named abstraction for managing competing consumers.
Round-robin distribution ensures fair load balancing.

### Auto-Ack vs Manual Ack
Auto-ack on successful handler return is simpler but means a crash during
handler execution after partial processing could lose the message. Manual ack
gives the consumer explicit control.

### Dead Letter Queue Design
Per-topic DLQ allows independent management of failed messages. Messages can
be retried from DLQ or inspected for debugging.

## Potential Improvements

- [ ] Network transport for true distributed operation
- [ ] WAL (Write-Ahead Log) for better write performance
- [ ] Message compression
- [ ] Schema registry for payload validation
- [ ] Batch publish and consume
- [ ] Metrics and monitoring endpoints
- [ ] Message TTL (time-to-live) independent of retries
- [ ] Message ordering guarantees within partitions
- [ ] Transaction support for atomic multi-message operations
- [ ] Replay capability for re-processing messages
- [ ] Admin API for queue management
- [ ] Web UI for monitoring and debugging

## Performance Considerations

### Memory Usage
- Priority queue uses heap for O(log n) operations
- Messages stored as pointers to avoid copying
- Buffered channels prevent blocking on slow consumers

### Disk I/O
- File-per-message is simple but creates many small files
- Production systems use append-only logs (WAL)
- Batch writes could improve throughput

### Concurrency
- RWMutex for read-heavy workloads (topic inspection)
- Atomic operations for consumer group round-robin
- Non-blocking channel sends prevent slow consumers from blocking producers

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

### Channel-Based Delivery vs Pull
Used push-based delivery via Go channels. A pull-based model (consumer polls)
would give consumers more control over throughput and backpressure.

### Auto-Ack vs Manual Ack
Auto-ack on successful handler return is simpler but means a crash during
handler execution after partial processing could lose the message. Manual ack
gives the consumer explicit control.

## Potential Improvements

- [ ] Consumer groups (competing consumers, only one gets each message)
- [ ] Message TTL (time-to-live) and dead letter queue
- [ ] Retry with exponential backoff
- [ ] Message ordering guarantees
- [ ] Batch publish and consume
- [ ] Metrics and monitoring endpoints
- [ ] Network transport for true distributed operation
- [ ] WAL (Write-Ahead Log) for better write performance
- [ ] Message compression
- [ ] Schema registry for payload validation

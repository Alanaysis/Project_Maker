# 01 - Research: Distributed Game Systems

## Overview

This document covers the research phase for building a distributed game server system capable of handling real-time multiplayer games.

## Key Technologies

### Networking

**WebSocket Protocol**
- Full-duplex communication over single TCP connection
- Lower overhead than HTTP polling (2-byte frame header vs full HTTP headers)
- Native support in browsers and most programming languages
- Ideal for real-time game communication

**Protocol Buffers vs JSON**
- JSON: Human-readable, easy debugging, wider support
- Protobuf: Smaller payload, faster serialization, schema enforcement
- Decision: JSON for simplicity and debuggability in initial version

### State Synchronization Approaches

**1. Snapshot Synchronization**
- Send complete game state at fixed intervals
- Simplest to implement and debug
- Higher bandwidth usage
- Best for: Small games, turn-based games, prototyping

**2. Delta Synchronization**
- Send only state changes since last sync
- Requires tracking previous state per client
- Lower bandwidth for sparse updates
- Best for: Games with infrequent state changes

**3. Frame Synchronization (Lockstep)**
- All clients advance frames together
- Only inputs are transmitted, not state
- Requires deterministic simulation
- Best for: Fighting games, RTS, competitive games

**4. Client-Side Prediction with Server Reconciliation**
- Client predicts movement locally
- Server sends authoritative state
- Client reconciles differences
- Best for: FPS, action games with responsive controls

### Matchmaking Systems

**Random Matching**
- Simple FIFO queue processing
- No skill consideration
- Fast queue times
- Use case: Casual play, testing

**ELO-Based Matching**
- Players assigned numerical skill rating
- Match players with similar ratings
- Rating updates after each game
- Dynamic tolerance based on queue time

**TrueSkill / Glicko-2**
- More advanced rating systems
- Account for rating uncertainty
- Better for team games
- More complex to implement

### Concurrency Models

**Go Goroutines + Channels**
- Lightweight green threads (~2KB stack each)
- Built-in channel-based communication
- Excellent for handling many concurrent connections
- Race detector built into toolchain

**Event Loop (Node.js)**
- Single-threaded with async I/O
- Good for I/O-bound workloads
- Limited CPU parallelism
- Large ecosystem

**Decision: Go** for superior concurrency model and performance for game servers.

## Research Findings

### Performance Benchmarks (Industry Data)

| Metric | Typical Value |
|--------|--------------|
| WebSocket connections per server | 10,000 - 100,000 |
| Message latency (same region) | 1 - 10 ms |
| Tick rate (competitive FPS) | 64 - 128 Hz |
| Tick rate (casual games) | 10 - 30 Hz |
| State snapshot size (100 players) | 1 - 10 KB |

### Architecture Patterns

**1. Single Server**
- All game logic on one machine
- Simplest to develop and deploy
- Limited by single machine resources
- Suitable for: Small to medium games

**2. Distributed Game Servers**
- Multiple servers handle different rooms/regions
- Requires service discovery and load balancing
- State must be shared via Redis/DB
- Suitable for: Large scale games

**3. Microservices**
- Separate services for auth, matchmaking, game logic
- Each service scales independently
- More operational complexity
- Suitable for: Enterprise games

### Decision: Single Server Architecture

For initial implementation, a single server architecture is chosen:
- Easier to develop and test
- Sufficient for moderate player counts
- Can be extended to distributed later

## Technology Stack

| Component | Choice | Reason |
|-----------|--------|--------|
| Language | Go | Concurrency, performance |
| WebSocket | gorilla/websocket | Mature, well-tested |
| Serialization | encoding/json | Simple, debuggable |
| State Storage | In-memory | Fast, sufficient for MVP |
| Logging | log (stdlib) | Simple, adequate |

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| WebSocket connection limits | High | Connection pooling, load balancing |
| State sync bandwidth | Medium | Delta compression, interest management |
| Cheating | High | Server-authoritative state |
| Network latency | Medium | Client-side prediction, interpolation |
| Memory leaks | Medium | Proper connection cleanup, monitoring |

# 03 - Design: Distributed Game Systems

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Game Server                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │  Network  │  │  Server  │  │  Match   │             │
│  │   Hub     │──│  Logic   │──│  Maker   │             │
│  └──────────┘  └──────────┘  └──────────┘             │
│       │              │              │                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │   Room   │  │  Player  │  │  State   │             │
│  │  Manager │  │  Manager │  │   Sync   │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└─────────────────────────────────────────────────────────┘
         ▲              ▲              ▲
         │              │              │
    WebSocket      HTTP API      Internal
         │              │              │
    ┌─────────┐   ┌─────────┐   ┌─────────┐
    │  Game   │   │  REST   │   │  Game   │
    │  Client │   │  Client │   │  Logic  │
    └─────────┘   └─────────┘   └─────────┘
```

### Package Structure

```
distributed-game-system/
├── cmd/
│   └── server/
│       └── main.go           # Entry point, flag parsing
├── internal/
│   ├── protocol/
│   │   └── message.go        # Message types, encode/decode
│   ├── network/
│   │   └── websocket.go      # Connection, Hub, WebSocket handler
│   ├── player/
│   │   └── player.go         # Player struct, PlayerManager
│   ├── room/
│   │   ├── room.go           # Room struct, RoomManager
│   │   └── game_state.go     # GameState, PlayerState
│   ├── sync/
│   │   └── sync.go           # StateSynchronizer
│   ├── matchmaking/
│   │   └── matchmaking.go    # Matchmaker, ELO calculation
│   └── server/
│       └── server.go         # GameServer, message routing
├── examples/
│   └── client.html           # Browser-based test client
├── tests/
│   └── game_test.go          # Unit tests
└── docs/                     # Documentation
```

## Component Design

### 1. Protocol Layer (`internal/protocol`)

**Responsibility**: Define message types, serialization/deserialization

```
Message
├── Type: MessageType (string enum)
├── ID: string (unique)
├── Timestamp: time.Time
├── PlayerID: string
├── RoomID: string
└── Payload: json.RawMessage
```

**Design Decisions**:
- Using `json.RawMessage` for payload allows lazy parsing
- Message IDs use timestamp + random string for uniqueness
- All times in UTC for consistency

### 2. Network Layer (`internal/network`)

**Responsibility**: WebSocket management, connection tracking, message routing

```
Hub
├── connections: map[playerID]*Connection
├── rooms: map[roomID]map[playerID]*Connection
├── Register(conn)
├── Unregister(conn)
├── JoinRoom(roomID, playerID)
├── LeaveRoom(roomID, playerID)
├── BroadcastToRoom(roomID, message, exclude)
└── SendToPlayer(playerID, message)

Connection
├── conn: *websocket.Conn
├── send: chan []byte
├── playerID: string
├── ReadPump()    # Reads from WebSocket, handles heartbeat
├── WritePump()   # Writes to WebSocket, sends pings
└── Send(message)
```

**Concurrency Model**:
- Each connection has two goroutines: ReadPump and WritePump
- `send` channel buffers up to 256 messages
- Hub uses RWMutex for concurrent access
- Room broadcasts are non-blocking (drop if channel full)

**Heartbeat Mechanism**:
```
Server                    Client
  │──── ping (54s) ────────>│
  │<──── pong ──────────────│
  │                          │
  │ (60s timeout)            │
  │── disconnect if no pong──│
```

### 3. Player Layer (`internal/player`)

**Responsibility**: Player data management, statistics

```
PlayerManager
├── players: map[playerID]*Player
├── AddPlayer(player)
├── RemovePlayer(playerID)
├── GetPlayer(playerID) -> *Player
├── GetPlayerCount() -> int
├── GetOnlinePlayers() -> []*Player
└── UpdatePlayerRating(playerID, newRating)

Player
├── ID, Name, Rating
├── Status: online | in_room | in_game | in_queue | offline
├── RoomID (current room)
├── Stats: Wins, Losses, Draws, GamesPlayed
├── RecordWin() / RecordLoss() / RecordDraw()
└── GetWinRate() -> float64
```

### 4. Room Layer (`internal/room`)

**Responsibility**: Room lifecycle, game state management

```
RoomManager
├── rooms: map[roomID]*Room
├── CreateRoom(id, name, maxPlayers, minPlayers)
├── GetRoom(roomID) -> *Room
├── DeleteRoom(roomID)
├── GetRoomList() -> []*Room
├── GetAvailableRooms() -> []*Room
└── FindRoomForPlayer() -> *Room

Room
├── ID, Name, MaxPlayers, MinPlayers
├── Status: waiting | playing | finished
├── Players: map[playerID]*Player
├── GameState: *GameState
├── AddPlayer(player) -> error
├── RemovePlayer(playerID) -> error
├── CanStart() -> bool
├── Start() -> error
└── End()

GameState
├── Frame: uint64
├── Players: map[playerID]*PlayerState
├── State: map[string]interface{}
├── UpdatePlayer(playerID, x, y, z)
├── GetSnapshot() -> map
├── GetDelta(lastFrame) -> map
└── AdvanceFrame()

PlayerState
├── PlayerID, X, Y, Z
├── Score, Health, Active
└── Data: map[string]interface{}
```

### 5. Sync Layer (`internal/sync`)

**Responsibility**: State synchronization between server and clients

```
StateSynchronizer
├── roomID, gameState
├── mode: snapshot | delta | frame
├── syncInterval: 50ms (20 FPS)
├── Start(broadcastFunc)
├── Stop()
├── syncLoop(broadcastFunc)     # Goroutine
├── syncSnapshot(broadcastFunc)
├── syncDelta(broadcastFunc)
├── syncFrame(broadcastFunc)
└── ProcessInput(frameInput)
```

**Sync Modes**:

```
Snapshot Sync:
  Server ──── [Full State] ────> All Clients
  (every 50ms)

Delta Sync:
  Server ──── [Frame N Changes] ────> All Clients
  (only if frame changed)

Frame Sync:
  Client A ──── [Input Frame N] ────> Server
  Client B ──── [Input Frame N] ────> Server
  Server ──── [All Inputs Frame N] ────> All Clients
  (all inputs collected before broadcast)
```

### 6. Matchmaking Layer (`internal/matchmaking`)

**Responsibility**: Player pairing and queue management

```
Matchmaker
├── queue: []*MatchRequest
├── matchCh: chan *MatchResult
├── Enqueue(request) -> error
├── Dequeue(playerID) -> error
├── GetMatchResult() <-chan *MatchResult
├── matchLoop()              # Goroutine, 1s tick
├── processQueue()
├── matchRandom(requests)
├── matchELO(requests)
└── CalculateELO(winner, loser, kFactor)
```

**ELO Matching Algorithm**:
```
1. Sort queue by rating
2. For each unpaired player:
   a. Find closest-rated unpaired player
   b. Check if rating difference <= maxDiff
      maxDiff = 100 + (queueTimeSeconds * 10)
   c. If match found, pair them
3. Create room for matched pair
4. Send match results
```

### 7. Server Layer (`internal/server`)

**Responsibility**: Orchestrate all components, route messages

```
GameServer
├── hub: *network.Hub
├── roomMgr: *room.RoomManager
├── playerMgr: *player.PlayerManager
├── matchmaker: *matchmaking.Matchmaker
├── syncMgr: map[roomID]*sync.StateSynchronizer
├── Start(addr) -> error
└── handleMessage(msg)
    ├── handleConnect(msg)
    ├── handleDisconnect(msg)
    ├── handleCreateRoom(msg)
    ├── handleJoinRoom(msg)
    ├── handleLeaveRoom(msg)
    ├── handleRoomListRequest(msg)
    ├── handlePlayerReady(msg)
    ├── handlePlayerMove(msg)
    ├── handleMatchRequest(msg)
    ├── handleMatchCancel(msg)
    └── handleFrameInput(msg)
```

**Message Flow**:
```
Client ──WebSocket──> Hub ──> GameServer.handleMessage()
                                    │
                  ┌─────────────────┼─────────────────┐
                  ▼                 ▼                 ▼
            RoomManager      PlayerManager      Matchmaker
                  │                 │                 │
                  └─────────────────┼─────────────────┘
                                    ▼
                              Response Message
                                    │
                  ┌─────────────────┼─────────────────┐
                  ▼                 ▼                 ▼
           Hub.SendToPlayer  Hub.BroadcastToRoom  matchCh
```

## Concurrency Design

### Goroutine Model

```
Main Goroutine
└── HTTP Server (goroutine per request)
    └── WebSocket Upgrade
        ├── ReadPump (per connection)
        └── WritePump (per connection)

Matchmaker Goroutine
└── matchLoop (1s tick)

Sync Goroutines (per active room)
└── syncLoop (50ms tick)
```

### Lock Strategy

| Resource | Lock Type | Usage |
|----------|-----------|-------|
| Hub.connections | RWMutex | Reads for broadcast, writes for register/unregister |
| Hub.rooms | RWMutex | Reads for broadcast, writes for join/leave |
| PlayerManager.players | RWMutex | Frequent reads, infrequent writes |
| RoomManager.rooms | RWMutex | Frequent reads, infrequent writes |
| Room.Players | RWMutex | Reads for count/list, writes for add/remove |
| GameState | RWMutex | Reads for snapshot, writes for updates |
| Matchmaker.queue | RWMutex | Reads for status, writes for enqueue/dequeue |

### Channel Usage

| Channel | Buffer | Purpose |
|---------|--------|---------|
| Connection.send | 256 | Outbound message queue per client |
| Matchmaker.matchCh | 100 | Match result delivery |

## Error Handling

### Error Categories

1. **Protocol Errors**: Invalid message format -> send error response
2. **Room Errors**: Room full, not found -> send error response
3. **Player Errors**: Already in queue, not in room -> send error response
4. **System Errors**: Internal failures -> log and continue

### Error Response Format

```json
{
  "type": "error",
  "payload": {
    "code": 400,
    "message": "Room is full"
  }
}
```

## Performance Considerations

### Memory Management

- Connection `send` channel drops messages when full (prevents memory leak)
- Empty rooms are auto-deleted
- Player data is removed on disconnect
- Game state uses map for O(1) lookups

### Network Optimization

- Delta sync reduces bandwidth for sparse updates
- Frame sync batches all inputs per frame
- Heartbeat pings are minimal (2 bytes)
- Message compression not implemented (add if needed)

### Scalability Limits

| Component | Limit | Notes |
|-----------|-------|-------|
| Connections per server | ~10,000 | Goroutine overhead |
| Rooms per server | ~1,000 | Memory for game states |
| Players per room | 2-10 | Configurable |
| Sync rate | 20 FPS | Configurable per room |

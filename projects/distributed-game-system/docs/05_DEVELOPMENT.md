# 05 - Development: Distributed Game Systems

## Development Setup

### Prerequisites

- Go 1.21 or later
- Git

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd distributed-game-system

# Install dependencies
go mod tidy

# Verify installation
go build ./...
```

### Running the Server

```bash
# Development mode
go run cmd/server/main.go

# With custom address
go run cmd/server/main.go -addr :9090

# Build and run binary
go build -o game-server cmd/server/main.go
./game-server -addr :8080
```

### Running Tests

```bash
# Run all tests
go test ./tests/ -v

# Run with race detector
go test ./tests/ -v -race

# Run specific test
go test ./tests/ -v -run TestPlayerCreation
```

## Project Structure

```
distributed-game-system/
├── cmd/
│   └── server/
│       └── main.go              # Entry point (28 lines)
├── internal/
│   ├── protocol/
│   │   └── message.go           # Message protocol (160 lines)
│   ├── network/
│   │   └── websocket.go         # WebSocket hub (300 lines)
│   ├── player/
│   │   └── player.go            # Player management (180 lines)
│   ├── room/
│   │   ├── room.go              # Room management (220 lines)
│   │   └── game_state.go        # Game state (150 lines)
│   ├── sync/
│   │   └── sync.go              # State sync (160 lines)
│   ├── matchmaking/
│   │   └── matchmaking.go       # Matchmaking (230 lines)
│   └── server/
│       └── server.go            # Server orchestration (320 lines)
├── examples/
│   └── client.html              # Browser client (400 lines)
├── tests/
│   └── game_test.go             # Unit tests (300 lines)
├── docs/                        # Documentation
├── go.mod                       # Module definition
└── README.md                    # Project readme
```

## Implementation Details

### 1. Message Protocol (`internal/protocol/message.go`)

**Key Types**:
- `MessageType`: String enum for message types
- `Message`: Base message structure with type, ID, timestamp, payload
- Payload types: ConnectPayload, RoomPayload, PlayerMovePayload, etc.

**Design Decisions**:
- `json.RawMessage` for payload enables lazy parsing
- Message ID uses timestamp + random for uniqueness
- All timestamps in UTC

**Usage Example**:
```go
// Create message
payload := &protocol.PlayerMovePayload{X: 10, Y: 20, Z: 0}
msg, _ := protocol.NewMessage(protocol.MsgTypePlayerMove, "player1", "room1", payload)

// Encode
data, _ := msg.Encode()

// Decode
decoded, _ := protocol.DecodeMessage(data)
var movePayload protocol.PlayerMovePayload
decoded.DecodePayload(&movePayload)
```

### 2. Network Layer (`internal/network/websocket.go`)

**Components**:
- `Connection`: Single WebSocket connection with read/write pumps
- `Hub`: Connection manager with room-based routing

**Concurrency Model**:
```
Connection:
  - ReadPump goroutine: reads from WebSocket, dispatches to Hub
  - WritePump goroutine: writes from send channel to WebSocket
  - send channel: buffered (256), non-blocking writes

Hub:
  - RWMutex for connections map
  - RWMutex for rooms map
  - BroadcastToRoom iterates room connections
```

**Heartbeat**:
- Server sends Ping every 54s
- Client responds with Pong
- 60s timeout disconnects dead connections

**Usage Example**:
```go
hub := network.NewHub()
hub.SetMessageHandler(func(msg *protocol.Message) {
    // Handle message
})

// In HTTP handler
network.HandleWebSocket(hub, w, r, playerID)

// Send to player
hub.SendToPlayer(playerID, messageBytes)

// Broadcast to room
hub.BroadcastToRoom(roomID, messageBytes, excludePlayerID)
```

### 3. Player Management (`internal/player/player.go`)

**Player States**:
- `online`: Connected, not in room
- `in_room`: In a room, waiting
- `in_game`: Currently playing
- `in_queue`: In matchmaking queue
- `offline`: Disconnected

**Usage Example**:
```go
pm := player.NewPlayerManager()
p := player.NewPlayer("id1", "Player1")
pm.AddPlayer(p)

p.SetRoom("room1")  // Status -> in_room
p.RecordWin()        // Update stats
rating := p.Rating   // Get current rating
```

### 4. Room Management (`internal/room/room.go`)

**Room Lifecycle**:
```
Created (waiting) -> Players Join -> Game Start (playing) -> Game End (finished)
        |                                |
        └── Empty -> Auto Delete         └── All Leave -> Delete
```

**Usage Example**:
```go
rm := room.NewRoomManager()
room := rm.CreateRoom("room1", "Game Room", 4, 2)

room.AddPlayer(player1)
room.AddPlayer(player2)

if room.CanStart() {
    room.Start()  // Creates GameState
    // Game is now playing
}

room.RemovePlayer("player1")
```

### 5. Game State (`internal/room/game_state.go`)

**Player State**:
- Position: X, Y, Z (float64)
- Score: int
- Health: int (0-100)
- Active: bool

**Operations**:
- `UpdatePlayer(id, x, y, z)`: Update position, increment frame
- `GetSnapshot()`: Full state for snapshot sync
- `GetDelta(lastFrame)`: Changes since last frame
- `AdvanceFrame()`: Increment frame counter

### 6. State Synchronization (`internal/sync/sync.go`)

**Sync Modes**:

```go
// Snapshot sync - full state every 50ms
sync := sync.NewStateSynchronizer(roomID, gameState, sync.SyncModeSnapshot)

// Delta sync - only changes
sync := sync.NewStateSynchronizer(roomID, gameState, sync.SyncModeDelta)

// Frame sync - lockstep
sync := sync.NewStateSynchronizer(roomID, gameState, sync.SyncModeFrame)

// Start syncing
sync.Start(func(msg *protocol.Message) {
    hub.BroadcastToRoom(roomID, encodedMsg, "")
})

// Stop when game ends
sync.Stop()
```

### 7. Matchmaking (`internal/matchmaking/matchmaking.go`)

**ELO Calculation**:
```go
newWinner, newLoser := matchmaking.CalculateELO(1200, 1200, 32)
// Winner gains ~16 points, loser loses ~16 points
```

**Queue Management**:
```go
mm := matchmaking.NewMatchmaker(roomMgr, playerMgr)
mm.Start()

// Enqueue player
req := &matchmaking.MatchRequest{
    PlayerID: "player1",
    Mode:     matchmaking.ModeELO,
    Rating:   1200,
    GameType: "ranked",
}
mm.Enqueue(req)

// Get match results
for result := range mm.GetMatchResult() {
    // result.RoomID, result.Players
}

// Dequeue
mm.Dequeue("player1")
```

### 8. Server Orchestration (`internal/server/server.go`)

**Message Routing**:
```
handleMessage(msg)
├── connect -> handleConnect
├── disconnect -> handleDisconnect
├── create_room -> handleCreateRoom
├── join_room -> handleJoinRoom
├── leave_room -> handleLeaveRoom
├── room_list -> handleRoomListRequest
├── player_ready -> handlePlayerReady
├── player_move -> handlePlayerMove
├── match_request -> handleMatchRequest
├── match_cancel -> handleMatchCancel
└── frame_input -> handleFrameInput
```

## Testing

### Test Coverage

| Component | Test Cases |
|-----------|------------|
| Player | Creation, Manager CRUD, Status transitions, Stats |
| Room | Creation, Player management, Game start, Full error |
| GameState | Creation, Update, Snapshot, Frame advancement |
| Protocol | Message encoding/decoding, Payload parsing |
| Matchmaking | ELO calculation, Queue management, Duplicate prevention |
| Concurrency | Concurrent access safety |

### Running Tests

```bash
# All tests
go test ./tests/ -v

# With race detector
go test ./tests/ -v -race

# Specific test
go test ./tests/ -v -run TestMatchmakingELO
```

### Test Examples

```go
func TestPlayerCreation(t *testing.T) {
    p := player.NewPlayer("player1", "TestPlayer")
    if p.Rating != 1200 {
        t.Errorf("Expected default rating 1200, got %d", p.Rating)
    }
}

func TestMatchmakingELO(t *testing.T) {
    newWinner, newLoser := matchmaking.CalculateELO(1200, 1200, 32)
    if newWinner <= 1200 {
        t.Errorf("Winner rating should increase, got %d", newWinner)
    }
}
```

## Client Usage

### HTML5 Client

Open `examples/client.html` in a browser:

1. Enter player name
2. Set server address (default: ws://localhost:8080/ws)
3. Click Connect
4. Use matchmaking or create/join rooms
5. Use WASD/Arrow keys to move in game
6. Press R to signal ready

### WebSocket Client (JavaScript)

```javascript
const ws = new WebSocket('ws://localhost:8080/ws?player_id=my-id');

ws.onopen = () => {
    ws.send(JSON.stringify({
        type: 'connect',
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        player_id: 'my-id',
        payload: { player_name: 'MyName' }
    }));
};

ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    console.log('Received:', msg.type, msg.payload);
};
```

## Performance Tuning

### Configuration Points

| Parameter | Default | Description |
|-----------|---------|-------------|
| Sync interval | 50ms | State sync frequency |
| Max connections | unlimited | WebSocket connections |
| Send buffer | 256 | Messages per connection |
| Ping interval | 54s | Heartbeat frequency |
| Pong timeout | 60s | Connection timeout |
| Match interval | 1s | Queue processing frequency |

### Scaling Considerations

1. **Connection Limits**: ~10,000 per server (goroutine overhead)
2. **Room Limits**: ~1,000 per server (memory for states)
3. **Sync Rate**: Adjust based on game type (10-60 FPS)
4. **Match Queue**: Process more frequently for faster matching

## Troubleshooting

### Common Issues

**Connection refused**:
- Verify server is running on correct port
- Check firewall settings
- Ensure WebSocket URL format: `ws://host:port/ws?player_id=xxx`

**Messages not received**:
- Check message format matches protocol
- Verify player_id matches connection
- Check server logs for errors

**High latency**:
- Reduce sync interval
- Use delta sync instead of snapshot
- Check network conditions

**Memory usage**:
- Monitor room count (auto-cleanup)
- Check for connection leaks
- Profile with `go tool pprof`

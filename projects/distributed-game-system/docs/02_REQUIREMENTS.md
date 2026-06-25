# 02 - Requirements: Distributed Game Systems

## Functional Requirements

### FR1: Game Server

#### FR1.1 Room Management
- Create game rooms with configurable max player count (2-10)
- Join existing rooms
- Leave rooms
- List available rooms
- Auto-delete empty rooms
- Room status tracking (waiting, playing, finished)

#### FR1.2 Player Management
- Player registration with name
- Player status tracking (online, in_room, in_game, in_queue, offline)
- Player statistics (wins, losses, draws, games played)
- ELO rating system (default 1200)

#### FR1.3 Game State
- Game state initialization with all players
- Player position tracking (x, y, z coordinates)
- Player score and health tracking
- Frame counter for synchronization

### FR2: Network Communication

#### FR2.1 WebSocket Server
- Accept WebSocket connections on configurable port
- Player identification via query parameter
- Upgrade HTTP to WebSocket
- Support text message format (JSON)

#### FR2.2 Message Protocol
- Message type identification
- Message ID for tracking
- Timestamp for ordering
- Player ID and Room ID routing
- JSON payload for flexibility

#### FR2.3 Heartbeat Detection
- Server sends ping every 54 seconds (90% of pong timeout)
- Client responds with pong
- 60-second pong timeout
- Automatic disconnection on timeout

### FR3: State Synchronization

#### FR3.1 Snapshot Sync
- Full state broadcast at configurable interval (default 50ms)
- Includes all player positions and game data
- Frame number for ordering

#### FR3.2 Delta Sync
- Track changes per frame
- Send only modified state since last sync
- Frame-based change tracking

#### FR3.3 Frame Sync (Lockstep)
- Collect player inputs per frame
- Broadcast frame data to all players
- Advance frame only after all inputs received
- Support for frame input messages

### FR4: Matchmaking System

#### FR4.1 Random Matching
- FIFO queue processing
- Match any two players in queue
- Support different game types
- Queue status tracking

#### FR4.2 ELO Matching
- Rating-based player pairing
- Configurable rating tolerance (base 100 + 10 per second in queue)
- Sorted by rating for efficient matching
- ELO calculation after game (K-factor = 32)

#### FR4.3 Queue Management
- Enqueue/dequeue operations
- Duplicate prevention
- Queue size tracking
- Queue status by mode

### FR5: REST API

#### FR5.1 Room Endpoints
- GET /api/rooms - List all rooms

#### FR5.2 Player Endpoints
- GET /api/players - List online players

#### FR5.3 Status Endpoints
- GET /api/status - Server health and statistics

## Non-Functional Requirements

### NFR1: Performance
- Support 1000+ concurrent WebSocket connections
- Message processing latency < 5ms
- State sync at 20 FPS (50ms intervals)
- Room operations < 1ms

### NFR2: Reliability
- Graceful handling of client disconnections
- Automatic room cleanup on empty
- No data loss during normal operation
- Error messages for invalid operations

### NFR3: Scalability
- Modular architecture for component replacement
- Configurable sync intervals
- Support for different game types
- Extensible message protocol

### NFR4: Security
- Server-authoritative game state
- Input validation on all messages
- Rate limiting ready (extensible)
- No client-trusted data for game logic

### NFR5: Usability
- Clear error messages
- Comprehensive logging
- HTML5 client for testing
- Simple setup and deployment

## Data Models

### Player
```
ID: string (UUID)
Name: string
Rating: int (default 1200)
Status: enum (online, in_room, in_game, in_queue, offline)
RoomID: string (optional)
Wins: int
Losses: int
Draws: int
GamesPlayed: int
CreatedAt: timestamp
LastSeen: timestamp
```

### Room
```
ID: string
Name: string
MaxPlayers: int (2-10)
MinPlayers: int (2)
Status: enum (waiting, playing, finished)
Players: map[PlayerID]*Player
GameState: *GameState
CreatedAt: timestamp
StartedAt: timestamp (optional)
```

### GameState
```
Frame: uint64
State: map[string]interface{}
Players: map[PlayerID]*PlayerState
Timestamp: timestamp
```

### PlayerState
```
PlayerID: string
X, Y, Z: float64
Score: int
Health: int (0-100)
Active: bool
```

### Message
```
Type: MessageType
ID: string
Timestamp: time.Time
PlayerID: string
RoomID: string
Payload: json.RawMessage
```

## Constraints

1. Single server deployment initially
2. In-memory state storage (no persistence)
3. JSON message format for simplicity
4. No authentication system (player_id from client)
5. No database integration in MVP

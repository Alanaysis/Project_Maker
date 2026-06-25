# Distributed Game System

A distributed game server system supporting real-time multiplayer games with matchmaking, state synchronization, and WebSocket communication.

## Features

- **Game Server** - Room management, player management, game state synchronization
- **WebSocket Communication** - Real-time bidirectional communication with heartbeat detection
- **State Synchronization** - Snapshot sync, delta sync, and frame sync modes
- **Matchmaking System** - Random matching and ELO-based skill matching
- **Web Client** - HTML5 client demo with canvas rendering

## Architecture

```
distributed-game-system/
├── cmd/server/          # Server entry point
├── internal/
│   ├── protocol/        # Message protocol definitions
│   ├── network/         # WebSocket and Hub implementation
│   ├── player/          # Player management
│   ├── room/            # Room and game state management
│   ├── sync/            # State synchronization
│   ├── matchmaking/     # Matchmaking system
│   └── server/          # Game server orchestration
├── examples/            # Client examples
├── tests/               # Unit tests
└── docs/                # Documentation
```

## Quick Start

### Prerequisites

- Go 1.21+

### Build and Run

```bash
# Install dependencies
go mod tidy

# Run server
go run cmd/server/main.go

# Or build
go build -o game-server cmd/server/main.go
./game-server -addr :8080
```

### Run Tests

```bash
go test ./tests/ -v
```

### Open Client

Open `examples/client.html` in a browser and connect to `ws://localhost:8080/ws`.

## WebSocket Message Protocol

### Connection Messages
| Type | Direction | Description |
|------|-----------|-------------|
| `connect` | Client -> Server | Player connects with name |
| `disconnect` | Client -> Server | Player disconnects |
| `heartbeat` | Bidirectional | Keep-alive ping/pong (30s interval, 60s timeout) |

### Room Management
| Type | Direction | Description |
|------|-----------|-------------|
| `create_room` | Client -> Server | Create a new game room |
| `join_room` | Client -> Server | Join an existing room |
| `leave_room` | Client -> Server | Leave current room |
| `room_list` | Client -> Server | Request list of rooms |
| `room_info` | Server -> Client | Room information response |
| `player_join` | Server -> Client | Player joined notification |
| `player_leave` | Server -> Client | Player left notification |

### Gameplay
| Type | Direction | Description |
|------|-----------|-------------|
| `player_ready` | Client -> Server | Player ready status |
| `player_move` | Client -> Server | Player movement input (x, y, z) |
| `game_start` | Server -> Client | Game starts notification |
| `game_end` | Server -> Client | Game ends notification |

### State Synchronization
| Type | Direction | Description |
|------|-----------|-------------|
| `game_state` | Server -> Client | Full state snapshot |
| `state_delta` | Server -> Client | State changes since last sync |
| `frame_input` | Client -> Server | Player input for frame sync |
| `frame_sync` | Server -> Client | Frame synchronization data |

### Matchmaking
| Type | Direction | Description |
|------|-----------|-------------|
| `match_request` | Client -> Server | Request matchmaking (random/elo) |
| `match_result` | Server -> Client | Match found with room ID |
| `match_cancel` | Client -> Server | Cancel matchmaking |

### REST API
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/rooms` | GET | List all rooms |
| `/api/players` | GET | List online players |
| `/api/status` | GET | Server status |

## State Synchronization Modes

### Snapshot Sync
Sends the complete game state at regular intervals (default 50ms = 20 FPS). Simple but uses more bandwidth. Best for small game states or infrequent updates.

### Delta Sync
Sends only changes since the last synchronization frame. More bandwidth-efficient for games with sparse state changes. Tracks the last synced frame and sends only the diff.

### Frame Sync (Lockstep)
All player inputs are collected for each frame before advancing to the next. The server broadcasts frame data containing all player inputs. Best for deterministic simulations like fighting games or RTS games.

## Matchmaking System

### Random Match
Quickly pairs any two players waiting in the queue, regardless of skill level. Fast queue times but potentially unbalanced matches.

### ELO Match
Pairs players based on ELO rating proximity. Players who have been waiting longer are allowed larger rating differences to prevent indefinite queue times.

**ELO Calculation:**
- Default rating: 1200
- K-factor: 32
- Expected score: `1 / (1 + 10^((ratingB - ratingA) / 400))`
- New rating: `rating + K * (actual - expected)`

## Game State Structure

```json
{
  "frame": 42,
  "timestamp": "2024-01-01T00:00:00Z",
  "players": {
    "player-1": {
      "x": 100.0,
      "y": 200.0,
      "z": 0.0,
      "score": 10,
      "health": 100,
      "active": true
    }
  },
  "state": {}
}
```

## Message Format

All messages follow this structure:

```json
{
  "type": "message_type",
  "id": "unique-message-id",
  "timestamp": "2024-01-01T00:00:00Z",
  "player_id": "player-id",
  "room_id": "room-id",
  "payload": {}
}
```

## License

MIT

# Social Chat App

A real-time chat system supporting single chat, offline messages, and user management. Built from scratch in Go with WebSocket, designed as a learning project for understanding instant messaging architecture.

## Learning Objectives

- **Instant Messaging Architecture**: Understand long connections (WebSocket) and message queuing
- **Message Push & Offline Storage**: Master reliable message delivery and offline message storage strategies
- **End-to-End Encryption**: Learn to implement basic E2EE to protect user privacy
- **Concurrent Programming**: Master Go's concurrency model (goroutine, channel) in real-time systems

## Tech Stack

| Technology | Purpose | Learning Difficulty |
|------------|---------|---------------------|
| **Go** | Main language, server and core logic | Medium |
| **WebSocket** (gorilla/websocket) | Real-time bidirectional communication | Medium |
| **SQLite** | Persistent storage | Low |
| **JWT** (golang-jwt) | User authentication | Medium |
| **bcrypt** | Password hashing | Low |

## Key Features

### Implemented (MVP)
- User registration and login (JWT authentication)
- Single chat (real-time text messaging via WebSocket)
- Offline message storage and sync on reconnect
- User status management (online/offline)
- Message delivery confirmation (ACK)
- Typing indicator
- Read receipts
- Heartbeat detection (ping/pong)
- Web-based chat UI
- CLI chat client

### Planned (Future)
- Group chat
- File transfer
- End-to-end encryption
- Message search
- Multi-device sync

## Project Structure

```
social-chat-app/
├── cmd/
│   ├── server/
│   │   └── main.go           # Server entry point
│   └── client/
│       └── main.go           # CLI chat client
├── internal/
│   ├── auth/
│   │   ├── auth.go           # Authentication service
│   │   ├── jwt.go            # JWT token management
│   │   └── middleware.go     # Auth middleware
│   ├── message/
│   │   ├── message.go        # Message service
│   │   └── repository.go     # Message storage (SQLite)
│   ├── user/
│   │   ├── user.go           # User service
│   │   └── repository.go     # User storage (SQLite)
│   └── websocket/
│       ├── manager.go        # Connection manager
│       └── connection.go     # WebSocket connection wrapper
├── pkg/
│   └── models/
│       ├── user.go           # User model
│       ├── message.go        # Message model
│       ├── group.go          # Group model
│       └── websocket.go      # WebSocket message models
├── web/
│   └── index.html            # Web-based chat UI
├── tests/                    # Unit and integration tests
├── examples/                 # Usage examples
├── docs/                     # Detailed documentation
├── Makefile                  # Build automation
├── Dockerfile                # Docker build
├── docker-compose.yml        # Docker Compose config
├── go.mod                    # Go module definition
└── README.md                 # This file
```

## Quick Start

### Prerequisites

- Go 1.21+
- GCC (for SQLite CGO)

### Build & Run

```bash
cd projects/social-chat-app

# Install dependencies
go mod tidy

# Build server and client
make build

# Run server
make run

# Or run directly without building
make dev
```

The server starts on `http://localhost:8080`. Open this URL in your browser to use the Web UI.

### Using the CLI Client

```bash
# Terminal 1: Register a user
./bin/chat-client register alice password123

# Terminal 2: Register another user
./bin/chat-client register bob password456

# Terminal 1: Start chatting with Alice's token
./bin/chat-client chat <alice_token>

# Terminal 2: Start chatting with Bob's token
./bin/chat-client chat <bob_token>

# In Alice's terminal, send message to Bob
/to <bob_user_id> Hello Bob!

# In Bob's terminal, reply
/to <alice_user_id> Hi Alice!
```

### Using the Web UI

1. Open `http://localhost:8080` in your browser
2. Register two users (open in two different browser tabs)
3. Login with each user
4. Copy one user's ID and paste in the other's "Search user ID" field
5. Start chatting!

### Using Docker

```bash
docker-compose up -d
```

### API Testing with curl

```bash
# Register
curl -X POST http://localhost:8080/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'

# Login
curl -X POST http://localhost:8080/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'

# Get user info (use token from login response)
curl -X GET http://localhost:8080/api/user/<user_id> \
  -H "Authorization: Bearer <token>"

# Search users
curl -X GET "http://localhost:8080/api/users?q=test" \
  -H "Authorization: Bearer <token>"

# Get conversation history
curl -X GET http://localhost:8080/api/messages/<other_user_id> \
  -H "Authorization: Bearer <token>"

# Health check
curl http://localhost:8080/api/health
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CHAT_SERVER_PORT` | `8080` | Server port |
| `CHAT_DB_PATH` | `./data/chat.db` | SQLite database path |
| `CHAT_JWT_SECRET` | `default-secret-change-this` | JWT signing secret |
| `CHAT_JWT_EXPIRY` | `24h` | JWT token expiry duration |

## Architecture Highlights

### WebSocket Connection Management

The server uses a hub-and-spoke pattern for managing WebSocket connections:

```
Client A ──ws──> Connection ──> Manager ──> Connection ──ws──> Client B
                     │            │
                     └── ReadPump │ WritePump
                                  │
                              Message Router
                                  │
                          ┌───────┼───────┐
                          │       │       │
                        Online  Offline  Broadcast
                        (push)  (store)  (all)
```

### Message Flow

```
User sends message
    -> WebSocket receives
    -> Parse and validate
    -> Save to database
    -> Find recipient connection
        -> Online: push directly
        -> Offline: store as offline message
    -> Send ACK to sender
    -> On recipient reconnect: sync offline messages
```

### Key Design Decisions

1. **Channel-based connection management**: Using Go channels (register/unregister) to safely manage concurrent connection operations
2. **Repository pattern**: Clean separation between business logic and data access
3. **Interface-based design**: Services depend on interfaces, making testing easy with mocks
4. **SQLite for simplicity**: No external database dependency for development

## Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cover
```

## Documentation

- [docs/01-RESEARCH.md](docs/01-RESEARCH.md) - Market research and technology analysis
- [docs/02-REQUIREMENTS.md](docs/02-REQUIREMENTS.md) - Requirements analysis
- [docs/03-DESIGN.md](docs/03-DESIGN.md) - Technical design
- [docs/04-PRODUCT.md](docs/04-PRODUCT.md) - Product thinking and competitive analysis
- [docs/05-DEVELOPMENT.md](docs/05-DEVELOPMENT.md) - Development manual

## Reference Projects

- [Tinode](https://github.com/tinode/chat) - Go-based instant messaging server
- [Matrix/Synapse](https://github.com/matrix-org/synapse) - Decentralized communication protocol
- [Rocket.Chat](https://github.com/RocketChat/Rocket.Chat) - Team collaboration chat platform
- [Signal Server](https://github.com/signalapp/Signal-Server) - End-to-end encrypted communication

## Learning Path

1. **Phase 1**: Understand WebSocket basics, implement simple message send/receive
2. **Phase 2**: Add user authentication and message storage
3. **Phase 3**: Implement offline messages and message queuing
4. **Phase 4**: Add group chat and file transfer
5. **Phase 5**: Implement end-to-end encryption

## License

MIT License

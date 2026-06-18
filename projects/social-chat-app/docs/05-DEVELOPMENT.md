# 开发手册

## 1. 环境搭建

### 1.1 系统要求

| 工具 | 版本 | 用途 |
|------|------|------|
| Go | 1.21+ | 主语言 |
| Git | 2.0+ | 版本控制 |
| SQLite | 3.0+ | 开发数据库 |
| Redis | 6.0+ | 消息队列（可选） |

### 1.2 安装 Go

#### macOS
```bash
# 使用 Homebrew
brew install go

# 或下载安装包
# https://go.dev/dl/
```

#### Linux
```bash
# 下载并安装
wget https://go.dev/dl/go1.21.5.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz

# 添加到 PATH
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
source ~/.bashrc
```

#### Windows
下载安装包：https://go.dev/dl/

### 1.3 安装 Redis（可选）

#### macOS
```bash
brew install redis
brew services start redis
```

#### Linux
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

### 1.4 配置环境变量

```bash
# 服务器配置
export CHAT_SERVER_PORT=8080
export CHAT_SERVER_HOST=0.0.0.0

# 数据库配置
export CHAT_DB_TYPE=sqlite
export CHAT_DB_PATH=./data/chat.db

# Redis 配置（可选）
export CHAT_REDIS_URL=redis://localhost:6379

# JWT 配置
export CHAT_JWT_SECRET=your-secret-key-change-this
export CHAT_JWT_EXPIRY=24h

# 日志配置
export CHAT_LOG_LEVEL=info
export CHAT_LOG_FILE=./logs/chat.log
```

## 2. 项目结构详解

### 2.1 目录结构

```
social-chat-app/
├── cmd/
│   └── server/
│       └── main.go           # 程序入口
│
├── internal/
│   ├── auth/
│   │   ├── auth.go           # 认证服务
│   │   ├── jwt.go            # JWT 处理
│   │   └── middleware.go     # 认证中间件
│   │
│   ├── chat/
│   │   ├── chat.go           # 聊天服务
│   │   └── group.go          # 群聊服务
│   │
│   ├── message/
│   │   ├── message.go        # 消息服务
│   │   └── repository.go     # 消息存储
│   │
│   ├── user/
│   │   ├── user.go           # 用户服务
│   │   └── repository.go     # 用户存储
│   │
│   └── websocket/
│       ├── manager.go        # 连接管理
│       ├── connection.go     # 连接封装
│       └── handler.go        # 消息处理
│
├── pkg/
│   └── models/
│       ├── user.go           # 用户模型
│       ├── message.go        # 消息模型
│       ├── group.go          # 群组模型
│       └── websocket.go      # WebSocket 消息模型
│
├── docs/                     # 文档
├── examples/                 # 使用示例
├── tests/                    # 测试文件
├── data/                     # 数据目录（运行时创建）
├── go.mod                    # Go 模块文件
├── go.sum                    # 依赖校验
└── README.md                 # 项目说明
```

### 2.2 模块职责

#### cmd/server
程序入口，负责：
- 解析配置
- 初始化依赖
- 启动服务器
- 优雅关闭

#### internal/auth
认证模块，负责：
- 用户认证
- JWT Token 管理
- 请求认证中间件

#### internal/user
用户模块，负责：
- 用户注册
- 用户信息管理
- 用户状态维护

#### internal/chat
聊天模块，负责：
- 聊天会话管理
- 群组管理
- 消息路由

#### internal/message
消息模块，负责：
- 消息存储
- 消息查询
- 离线消息管理

#### internal/websocket
WebSocket 模块，负责：
- 连接管理
- 消息收发
- 心跳检测

#### pkg/models
数据模型，负责：
- 定义数据结构
- JSON 序列化
- 数据库映射

## 3. 核心模块解析

### 3.1 WebSocket 连接管理

#### 3.1.1 连接池设计

```go
// internal/websocket/manager.go

type Manager struct {
    mu          sync.RWMutex
    connections map[string]*Connection  // user_id -> Connection
    register    chan *Connection
    unregister  chan *Connection
    broadcast   chan []byte
}

func NewManager() *Manager {
    return &Manager{
        connections: make(map[string]*Connection),
        register:    make(chan *Connection),
        unregister:  make(chan *Connection),
        broadcast:   make(chan []byte),
    }
}

func (m *Manager) Start() {
    for {
        select {
        case conn := <-m.register:
            m.mu.Lock()
            m.connections[conn.UserID] = conn
            m.mu.Unlock()

        case conn := <-m.unregister:
            m.mu.Lock()
            if _, ok := m.connections[conn.UserID]; ok {
                delete(m.connections, conn.UserID)
                close(conn.Send)
            }
            m.mu.Unlock()

        case message := <-m.broadcast:
            m.mu.RLock()
            for _, conn := range m.connections {
                select {
                case conn.Send <- message:
                default:
                    close(conn.Send)
                    delete(m.connections, conn.UserID)
                }
            }
            m.mu.RUnlock()
        }
    }
}
```

#### 3.1.2 连接封装

```go
// internal/websocket/connection.go

type Connection struct {
    UserID    string
    Conn      *websocket.Conn
    Send      chan []byte
    Manager   *Manager
    CreatedAt time.Time
    LastPing  time.Time
}

func (c *Connection) ReadPump() {
    defer func() {
        c.Manager.unregister <- c
        c.Conn.Close()
    }

    c.Conn.SetReadLimit(512 * 1024) // 512KB
    c.Conn.SetReadDeadline(time.Now().Add(60 * time.Second))
    c.Conn.SetPongHandler(func(string) error {
        c.Conn.SetReadDeadline(time.Now().Add(60 * time.Second))
        c.LastPing = time.Now()
        return nil
    })

    for {
        _, message, err := c.Conn.ReadMessage()
        if err != nil {
            break
        }
        // 处理消息
        c.HandleMessage(message)
    }
}

func (c *Connection) WritePump() {
    ticker := time.NewTicker(30 * time.Second)
    defer func() {
        ticker.Stop()
        c.Conn.Close()
    }()

    for {
        select {
        case message, ok := <-c.Send:
            if !ok {
                c.Conn.WriteMessage(websocket.CloseMessage, []byte{})
                return
            }
            c.Conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
            err := c.Conn.WriteMessage(websocket.TextMessage, message)
            if err != nil {
                return
            }

        case <-ticker.C:
            c.Conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
            if err := c.Conn.WriteMessage(websocket.PingMessage, nil); err != nil {
                return
            }
        }
    }
}
```

#### 3.1.3 消息处理

```go
// internal/websocket/handler.go

func (c *Connection) HandleMessage(data []byte) {
    var req WSRequest
    if err := json.Unmarshal(data, &req); err != nil {
        c.SendError("invalid message format")
        return
    }

    switch req.Type {
    case "message":
        c.HandleChatMessage(req)
    case "typing":
        c.HandleTyping(req)
    case "read":
        c.HandleReadReceipt(req)
    case "ping":
        c.HandlePing(req)
    default:
        c.SendError("unknown message type")
    }
}

func (c *Connection) HandleChatMessage(req WSRequest) {
    var payload MessagePayload
    if err := json.Unmarshal(req.Payload, &payload); err != nil {
        c.SendError("invalid message payload")
        return
    }

    // 创建消息
    msg := &Message{
        ID:        generateID(),
        Type:      payload.MsgType,
        From:      c.UserID,
        To:        payload.To,
        Content:   payload.Content,
        Status:    "sent",
        CreatedAt: time.Now(),
    }

    // 存储消息
    c.Manager.messageService.Save(msg)

    // 路由消息
    c.Manager.RouteMessage(msg)

    // 发送确认
    c.SendAck(req.ID, msg.ID)
}
```

### 3.2 消息存储与查询

#### 3.2.1 消息仓库

```go
// internal/message/repository.go

type Repository interface {
    Save(msg *Message) error
    FindByID(id string) (*Message, error)
    FindByConversation(user1, user2 string, limit, offset int) ([]*Message, error)
    FindUnread(userID string) ([]*Message, error)
    MarkAsRead(messageIDs []string) error
    SaveOffline(msg *Message) error
    FindOffline(userID string) ([]*Message, error)
    DeleteOffline(messageIDs []string) error
}

type SQLiteRepository struct {
    db *sql.DB
}

func (r *SQLiteRepository) Save(msg *Message) error {
    query := `
        INSERT INTO messages (id, type, from_user, to_user, content, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `
    _, err := r.db.Exec(query,
        msg.ID, msg.Type, msg.From, msg.To,
        msg.Content, msg.Status, msg.CreatedAt, msg.UpdatedAt,
    )
    return err
}

func (r *SQLiteRepository) FindByConversation(user1, user2 string, limit, offset int) ([]*Message, error) {
    query := `
        SELECT id, type, from_user, to_user, content, status, created_at, updated_at
        FROM messages
        WHERE (from_user = ? AND to_user = ?) OR (from_user = ? AND to_user = ?)
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    `
    rows, err := r.db.Query(query, user1, user2, user2, user1, limit, offset)
    if err != nil {
        return nil, err
    }
    defer rows.Close()

    var messages []*Message
    for rows.Next() {
        msg := &Message{}
        err := rows.Scan(
            &msg.ID, &msg.Type, &msg.From, &msg.To,
            &msg.Content, &msg.Status, &msg.CreatedAt, &msg.UpdatedAt,
        )
        if err != nil {
            return nil, err
        }
        messages = append(messages, msg)
    }
    return messages, nil
}
```

### 3.3 用户认证

#### 3.3.1 JWT 处理

```go
// internal/auth/jwt.go

type Claims struct {
    UserID   string `json:"user_id"`
    Username string `json:"username"`
    Role     string `json:"role"`
    jwt.RegisteredClaims
}

type JWTManager struct {
    secret     []byte
    expiry     time.Duration
}

func NewJWTManager(secret string, expiry time.Duration) *JWTManager {
    return &JWTManager{
        secret: []byte(secret),
        expiry: expiry,
    }
}

func (m *JWTManager) Generate(userID, username, role string) (string, error) {
    claims := Claims{
        UserID:   userID,
        Username: username,
        Role:     role,
        RegisteredClaims: jwt.RegisteredClaims{
            ExpiresAt: jwt.NewNumericDate(time.Now().Add(m.expiry)),
            IssuedAt:  jwt.NewNumericDate(time.Now()),
            Issuer:    "social-chat-app",
        },
    }

    token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
    return token.SignedString(m.secret)
}

func (m *JWTManager) Verify(tokenString string) (*Claims, error) {
    token, err := jwt.ParseWithClaims(tokenString, &Claims{}, func(token *jwt.Token) (interface{}, error) {
        if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
            return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
        }
        return m.secret, nil
    })

    if err != nil {
        return nil, err
    }

    claims, ok := token.Claims.(*Claims)
    if !ok || !token.Valid {
        return nil, fmt.Errorf("invalid token")
    }

    return claims, nil
}
```

### 3.4 消息队列（Redis）

#### 3.4.1 Redis Pub/Sub

```go
// internal/message/redis_queue.go

type RedisQueue struct {
    client   *redis.Client
    handlers map[string]func(string)
    mu       sync.RWMutex
}

func NewRedisQueue(redisURL string) (*RedisQueue, error) {
    opt, err := redis.ParseURL(redisURL)
    if err != nil {
        return nil, err
    }

    client := redis.NewClient(opt)
    if err := client.Ping(context.Background()).Err(); err != nil {
        return nil, err
    }

    return &RedisQueue{
        client:   client,
        handlers: make(map[string]func(string)),
    }, nil
}

func (q *RedisQueue) Publish(channel, message string) error {
    return q.client.Publish(context.Background(), channel, message).Err()
}

func (q *RedisQueue) Subscribe(channel string, handler func(string)) {
    q.mu.Lock()
    q.handlers[channel] = handler
    q.mu.Unlock()

    go func() {
        pubsub := q.client.Subscribe(context.Background(), channel)
        defer pubsub.Close()

        for msg := range pubsub.Channel() {
            if h, ok := q.handlers[channel]; ok {
                h(msg.Payload)
            }
        }
    }()
}
```

## 4. 开发流程

### 4.1 Git 工作流

```
main (生产分支)
  │
  ├── develop (开发分支)
  │     │
  │     ├── feature/user-auth (功能分支)
  │     ├── feature/websocket (功能分支)
  │     └── feature/message (功能分支)
  │
  └── release/v1.0 (发布分支)
```

### 4.2 提交规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型**：
- `feat`: 新功能
- `fix`: 修复 Bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

**示例**：
```
feat(websocket): 添加心跳检测机制

- 客户端每 30 秒发送 ping
- 服务器回复 pong
- 60 秒无响应标记离线

Closes #123
```

### 4.3 代码审查清单

- [ ] 代码符合 Go 编码规范
- [ ] 添加了必要的注释
- [ ] 包含单元测试
- [ ] 错误处理完善
- [ ] 没有明显的性能问题
- [ ] 安全性考虑（输入验证、加密等）

## 5. 测试策略

### 5.1 测试类型

| 类型 | 覆盖率目标 | 工具 |
|------|------------|------|
| 单元测试 | > 70% | testing, testify |
| 集成测试 | > 50% | testing, httptest |
| 端到端测试 | > 30% | testing, websocket |

### 5.2 单元测试示例

```go
// internal/auth/jwt_test.go

func TestJWTManager_Generate(t *testing.T) {
    manager := NewJWTManager("test-secret", 24*time.Hour)

    token, err := manager.Generate("user123", "testuser", "user")
    assert.NoError(t, err)
    assert.NotEmpty(t, token)

    claims, err := manager.Verify(token)
    assert.NoError(t, err)
    assert.Equal(t, "user123", claims.UserID)
    assert.Equal(t, "testuser", claims.Username)
}

func TestJWTManager_ExpiredToken(t *testing.T) {
    manager := NewJWTManager("test-secret", -1*time.Hour) // 已过期

    token, err := manager.Generate("user123", "testuser", "user")
    assert.NoError(t, err)

    _, err = manager.Verify(token)
    assert.Error(t, err)
}
```

### 5.3 集成测试示例

```go
// internal/user/handler_test.go

func TestUserHandler_Register(t *testing.T) {
    // 创建测试服务器
    server := httptest.NewServer(setupRouter())
    defer server.Close()

    // 发送注册请求
    body := `{"username":"testuser","password":"password123"}`
    resp, err := http.Post(server.URL+"/api/register", "application/json", strings.NewReader(body))
    assert.NoError(t, err)
    assert.Equal(t, http.StatusCreated, resp.StatusCode)

    // 验证响应
    var result map[string]interface{}
    json.NewDecoder(resp.Body).Decode(&result)
    assert.NotEmpty(t, result["token"])
}
```

### 5.4 WebSocket 测试示例

```go
// internal/websocket/handler_test.go

func TestWebSocket_ChatMessage(t *testing.T) {
    // 创建测试服务器
    server := httptest.NewServer(http.HandlerFunc(HandleWebSocket))
    defer server.Close()

    // 创建两个 WebSocket 连接
    ws1 := connectWebSocket(t, server, "user1")
    ws2 := connectWebSocket(t, server, "user2")
    defer ws1.Close()
    defer ws2.Close()

    // user1 发送消息给 user2
    msg := WSRequest{
        Type: "message",
        ID:   "req_001",
        Payload: MessagePayload{
            To:      "user2",
            Content: "Hello!",
            MsgType: "text",
        },
    }
    err := ws1.WriteJSON(msg)
    assert.NoError(t, err)

    // user2 接收消息
    var received WSResponse
    err = ws2.ReadJSON(&received)
    assert.NoError(t, err)
    assert.Equal(t, "message", received.Type)
}
```

## 6. 部署指南

### 6.1 本地开发

```bash
# 克隆项目
git clone https://github.com/yourusername/social-chat-app.git
cd social-chat-app

# 安装依赖
go mod tidy

# 运行测试
go test ./...

# 启动服务器
go run ./cmd/server
```

### 6.2 Docker 部署

```dockerfile
# Dockerfile
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o chat-server ./cmd/server

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /app/chat-server .
COPY --from=builder /app/config ./config
EXPOSE 8080
CMD ["./chat-server"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  chat-server:
    build: .
    ports:
      - "8080:8080"
    environment:
      - CHAT_SERVER_PORT=8080
      - CHAT_DB_TYPE=sqlite
      - CHAT_DB_PATH=/data/chat.db
      - CHAT_JWT_SECRET=your-secret-key
    volumes:
      - chat-data:/data
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  chat-data:
```

### 6.3 生产环境配置

```bash
# 使用环境变量
export CHAT_SERVER_PORT=8080
export CHAT_DB_TYPE=postgres
export CHAT_DB_HOST=localhost
export CHAT_DB_PORT=5432
export CHAT_DB_NAME=chat
export CHAT_DB_USER=chatuser
export CHAT_DB_PASSWORD=securepassword
export CHAT_REDIS_URL=redis://localhost:6379
export CHAT_JWT_SECRET=very-long-and-secure-secret-key
export CHAT_LOG_LEVEL=warn
```

## 7. 性能优化

### 7.1 数据库优化

```sql
-- 创建索引
CREATE INDEX idx_messages_conversation ON messages(from_user, to_user, created_at);
CREATE INDEX idx_messages_status ON messages(to_user, status);
CREATE INDEX idx_users_status ON users(status);

-- 分页优化
SELECT * FROM messages
WHERE (from_user = ? AND to_user = ?) OR (from_user = ? AND to_user = ?)
AND created_at < ?
ORDER BY created_at DESC
LIMIT 50;
```

### 7.2 连接优化

```go
// 使用连接池
type ConnectionPool struct {
    pool chan *Connection
    size int
}

func NewConnectionPool(size int) *ConnectionPool {
    return &ConnectionPool{
        pool: make(chan *Connection, size),
        size: size,
    }
}
```

### 7.3 缓存策略

```go
// 用户信息缓存
type UserCache struct {
    mu    sync.RWMutex
    cache map[string]*User
    ttl   time.Duration
}

func (c *UserCache) Get(userID string) (*User, bool) {
    c.mu.RLock()
    defer c.mu.RUnlock()

    user, ok := c.cache[userID]
    if ok && time.Since(user.CachedAt) < c.ttl {
        return user, true
    }
    return nil, false
}
```

## 8. 故障排查

### 8.1 常见问题

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 连接失败 | JWT Token 无效 | 检查 Token 是否过期 |
| 消息丢失 | 网络不稳定 | 实现消息重试机制 |
| 内存泄漏 | 连接未正确关闭 | 检查连接池管理 |
| 性能下降 | 数据库查询慢 | 添加索引、优化查询 |

### 8.2 日志分析

```bash
# 查看错误日志
grep "ERROR" logs/chat.log

# 查看特定用户的日志
grep "user_id=user123" logs/chat.log

# 统计消息量
grep "message.send" logs/chat.log | wc -l
```

### 8.3 性能监控

```go
// 添加性能指标
var (
    messageCounter = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "chat_messages_total",
            Help: "Total number of messages",
        },
        []string{"type"},
    )
    
    activeConnections = prometheus.NewGauge(
        prometheus.GaugeOpts{
            Name: "chat_active_connections",
            Help: "Number of active WebSocket connections",
        },
    )
)
```
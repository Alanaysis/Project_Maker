# 技术设计文档

## 1. 架构概述

### 1.1 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        客户端层                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Web App  │  │ Desktop  │  │  iOS App │  │ Android  │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
└───────┼──────────────┼──────────────┼──────────────┼────────┘
        │              │              │              │
        └──────────────┴──────┬───────┴──────────────┘
                              │
                         WebSocket / HTTP
                              │
┌─────────────────────────────┼─────────────────────────────┐
│                        服务器层                              │
│  ┌──────────────────────────┴──────────────────────────┐   │
│  │                   API Gateway                        │   │
│  │            (负载均衡、认证、路由)                      │   │
│  └──────────────────────────┬──────────────────────────┘   │
│                              │                              │
│  ┌───────────────┬───────────┼───────────┬───────────────┐ │
│  │               │           │           │               │ │
│  ▼               ▼           ▼           ▼               │ │
│ ┌─────┐      ┌─────┐    ┌─────┐     ┌─────┐          │ │
│ │User │      │Chat │    │Msg  │     │File │          │ │
│ │Svc  │      │Svc  │    │Svc  │     │Svc  │          │ │
│ └──┬──┘      └──┬──┘    └──┬──┘     └──┬──┘          │ │
│    │            │          │           │               │ │
│    └────────────┴─────┬────┴───────────┘               │ │
│                       │                                 │ │
│  ┌────────────────────┴──────────────────────────────┐ │ │
│  │                 数据访问层                          │ │ │
│  │          (Repository Pattern)                      │ │ │
│  └────────────────────┬──────────────────────────────┘ │ │
└───────────────────────┼─────────────────────────────────┘
                        │
┌───────────────────────┼─────────────────────────────────┐
│                    数据存储层                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│
│  │  SQLite  │  │  Redis   │  │  Files   │  │  Cache   ││
│  │ (主存储)  │  │ (消息队列) │  │ (文件存储) │  │ (缓存)   ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘│
└─────────────────────────────────────────────────────────┘
```

### 1.2 核心循环

```
用户发送消息
    │
    ▼
客户端 → WebSocket → 服务器
    │
    ▼
服务器接收消息
    │
    ├──→ 消息存储（数据库）
    │
    ├──→ 查找接收方连接
    │        │
    │        ├──→ 在线：直接推送
    │        │
    │        └──→ 离线：存储为离线消息
    │
    └──→ 返回发送确认
```

## 2. 模块设计

### 2.1 模块依赖关系

```
cmd/server
    │
    ├── internal/auth      (认证模块)
    │       │
    │       └── pkg/models  (数据模型)
    │
    ├── internal/user      (用户模块)
    │       │
    │       └── pkg/models
    │
    ├── internal/chat      (聊天模块)
    │       │
    │       ├── internal/message
    │       ├── internal/websocket
    │       └── pkg/models
    │
    ├── internal/message   (消息模块)
    │       │
    │       └── pkg/models
    │
    └── internal/websocket (WebSocket 模块)
            │
            └── pkg/models
```

### 2.2 模块职责

| 模块 | 职责 | 主要接口 |
|------|------|----------|
| **auth** | 用户认证、JWT 管理 | `AuthService` |
| **user** | 用户管理、状态维护 | `UserService` |
| **chat** | 聊天会话管理 | `ChatService` |
| **message** | 消息存储、查询 | `MessageService` |
| **websocket** | 连接管理、消息路由 | `WSManager` |

## 3. 数据结构设计

### 3.1 用户模型

```go
type User struct {
    ID        string    `json:"id" db:"id"`
    Username  string    `json:"username" db:"username"`
    Password  string    `json:"-" db:"password"` // 不序列化密码
    Email     string    `json:"email,omitempty" db:"email"`
    Nickname  string    `json:"nickname" db:"nickname"`
    Avatar    string    `json:"avatar" db:"avatar"`
    Status    string    `json:"status" db:"status"` // online, offline, busy, away
    CreatedAt time.Time `json:"created_at" db:"created_at"`
    UpdatedAt time.Time `json:"updated_at" db:"updated_at"`
}
```

### 3.2 消息模型

```go
type Message struct {
    ID        string    `json:"id" db:"id"`
    Type      string    `json:"type" db:"type"` // text, image, file
    From      string    `json:"from" db:"from_user"`
    To        string    `json:"to" db:"to_user"`
    Content   string    `json:"content" db:"content"`
    Status    string    `json:"status" db:"status"` // sent, delivered, read
    CreatedAt time.Time `json:"created_at" db:"created_at"`
    UpdatedAt time.Time `json:"updated_at" db:"updated_at"`
}
```

### 3.3 群组模型

```go
type Group struct {
    ID          string    `json:"id" db:"id"`
    Name        string    `json:"name" db:"name"`
    Description string    `json:"description" db:"description"`
    OwnerID     string    `json:"owner_id" db:"owner_id"`
    Avatar      string    `json:"avatar" db:"avatar"`
    MemberCount int       `json:"member_count" db:"member_count"`
    CreatedAt   time.Time `json:"created_at" db:"created_at"`
    UpdatedAt   time.Time `json:"updated_at" db:"updated_at"`
}

type GroupMember struct {
    GroupID   string    `json:"group_id" db:"group_id"`
    UserID    string    `json:"user_id" db:"user_id"`
    Role      string    `json:"role" db:"role"` // owner, admin, member
    JoinedAt  time.Time `json:"joined_at" db:"joined_at"`
}
```

### 3.4 WebSocket 消息格式

```go
// 客户端 → 服务器
type WSRequest struct {
    Type      string      `json:"type"`      // message, typing, read, status
    ID        string      `json:"id"`        // 请求 ID，用于匹配响应
    Payload   interface{} `json:"payload"`   // 具体数据
}

// 服务器 → 客户端
type WSResponse struct {
    Type      string      `json:"type"`      // message, ack, error, status
    ID        string      `json:"id"`        // 对应请求的 ID
    Payload   interface{} `json:"payload"`   // 具体数据
    Timestamp int64       `json:"timestamp"` // 服务器时间戳
}

// 消息请求
type MessagePayload struct {
    To      string `json:"to"`      // 接收者 ID 或群组 ID
    Content string `json:"content"` // 消息内容
    MsgType string `json:"msg_type"` // text, image, file
}

// 消息响应
type MessageResponse struct {
    MessageID string `json:"message_id"` // 消息 ID
    Status    string `json:"status"`     // sent, delivered, read
}
```

## 4. 接口设计

### 4.1 REST API

#### 用户相关

```
POST   /api/register          # 用户注册
POST   /api/login             # 用户登录
GET    /api/user/:id          # 获取用户信息
PUT    /api/user/:id          # 更新用户信息
GET    /api/users             # 搜索用户
```

#### 消息相关

```
GET    /api/messages/:user_id  # 获取与某用户的历史消息
GET    /api/messages/unread    # 获取未读消息
POST   /api/messages/read      # 标记消息已读
```

#### 群组相关

```
POST   /api/groups             # 创建群组
GET    /api/groups             # 获取用户的群组列表
GET    /api/groups/:id         # 获取群组详情
PUT    /api/groups/:id         # 更新群组信息
POST   /api/groups/:id/members # 添加群成员
DELETE /api/groups/:id/members/:user_id # 移除群成员
```

#### 文件相关

```
POST   /api/files/upload       # 上传文件
GET    /api/files/:id          # 下载文件
```

### 4.2 WebSocket API

#### 连接

```
ws://localhost:8080/ws?token=<jwt_token>
```

#### 消息类型

**发送文本消息**：
```json
{
  "type": "message",
  "id": "req_001",
  "payload": {
    "to": "user_123",
    "content": "Hello!",
    "msg_type": "text"
  }
}
```

**接收文本消息**：
```json
{
  "type": "message",
  "id": "msg_789",
  "payload": {
    "from": "user_456",
    "content": "Hi there!",
    "msg_type": "text",
    "timestamp": 1234567890
  },
  "timestamp": 1234567890
}
```

**输入状态**：
```json
{
  "type": "typing",
  "payload": {
    "to": "user_123"
  }
}
```

**已读回执**：
```json
{
  "type": "read",
  "payload": {
    "message_id": "msg_789"
  }
}
```

**状态更新**：
```json
{
  "type": "status",
  "payload": {
    "status": "online"
  }
}
```

**心跳检测**：
```json
// 客户端发送
{
  "type": "ping",
  "id": "ping_001"
}

// 服务器响应
{
  "type": "pong",
  "id": "ping_001"
}
```

## 5. 数据库设计

### 5.1 表结构

#### users 表
```sql
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    nickname VARCHAR(50),
    avatar VARCHAR(255),
    status VARCHAR(20) DEFAULT 'offline',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
```

#### messages 表
```sql
CREATE TABLE messages (
    id VARCHAR(36) PRIMARY KEY,
    type VARCHAR(20) NOT NULL,
    from_user VARCHAR(36) NOT NULL,
    to_user VARCHAR(36) NOT NULL,
    content TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'sent',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_user) REFERENCES users(id),
    FOREIGN KEY (to_user) REFERENCES users(id)
);

CREATE INDEX idx_messages_from ON messages(from_user);
CREATE INDEX idx_messages_to ON messages(to_user);
CREATE INDEX idx_messages_created ON messages(created_at);
CREATE INDEX idx_messages_conversation ON messages(from_user, to_user, created_at);
```

#### groups 表
```sql
CREATE TABLE groups (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    owner_id VARCHAR(36) NOT NULL,
    avatar VARCHAR(255),
    member_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id)
);
```

#### group_members 表
```sql
CREATE TABLE group_members (
    group_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    role VARCHAR(20) DEFAULT 'member',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (group_id, user_id),
    FOREIGN KEY (group_id) REFERENCES groups(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_group_members_user ON group_members(user_id);
```

### 5.2 Redis 数据结构

#### 在线状态（Hash）
```
Key: user:status:{user_id}
Field: status, last_seen
Value: "online", timestamp
```

#### 未读消息计数（Hash）
```
Key: unread:{user_id}
Field: {from_user_id}
Value: count
```

#### 用户会话（String）
```
Key: session:{user_id}
Value: connection_id
TTL: 24h
```

#### 消息队列（List）
```
Key: queue:{user_id}
Value: message_json
```

## 6. 连接管理设计

### 6.1 连接生命周期

```
客户端发起 WebSocket 连接
    │
    ▼
验证 JWT Token
    │
    ├── 无效 → 返回 401，关闭连接
    │
    └── 有效 → 继续
        │
        ▼
    注册连接到连接池
    │
    ▼
    更新用户状态为在线
    │
    ▼
    同步离线消息
    │
    ▼
    等待消息...
    │
    ├── 收到消息 → 处理并路由
    │
    ├── 收到心跳 → 回复 pong
    │
    └── 连接断开 → 清理资源
        │
        ▼
    从连接池移除
    │
    ▼
    更新用户状态为离线
```

### 6.2 连接池设计

```go
type ConnectionPool struct {
    mu          sync.RWMutex
    connections map[string]*Connection  // user_id -> Connection
}

type Connection struct {
    UserID    string
    Conn      *websocket.Conn
    Send      chan []byte
    CreatedAt time.Time
    LastPing  time.Time
}
```

### 6.3 消息路由

```go
func (m *Manager) RouteMessage(msg *Message) {
    // 1. 存储消息到数据库
    m.messageService.Save(msg)

    // 2. 查找接收方连接
    conn, ok := m.GetConnection(msg.To)

    if ok {
        // 3a. 在线：直接推送
        conn.Send <- msg.ToJSON()
    } else {
        // 3b. 离线：存储为离线消息
        m.messageService.SaveOffline(msg)
    }
}
```

## 7. 安全设计

### 7.1 认证流程

```
客户端                     服务器
   │                         │
   │  POST /api/login        │
   │  {username, password}   │
   │ ────────────────────────>│
   │                         │
   │                         │ 验证用户名密码
   │                         │ 生成 JWT Token
   │                         │
   │  {token, user_info}     │
   │ <────────────────────────│
   │                         │
   │  WebSocket 连接          │
   │  ?token=xxx             │
   │ ────────────────────────>│
   │                         │
   │                         │ 验证 Token
   │                         │ 建立连接
   │                         │
   │  连接成功                │
   │ <────────────────────────│
```

### 7.2 JWT Token 设计

```go
type Claims struct {
    UserID   string `json:"user_id"`
    Username string `json:"username"`
    Role     string `json:"role"`
    jwt.RegisteredClaims
}
```

Token 有效期：24 小时
刷新机制：过期前 1 小时内可刷新

### 7.3 密码安全

- 使用 bcrypt 加密存储
- 盐值自动生成
- 工作因子：10

### 7.4 输入验证

- 所有用户输入必须验证
- 防止 SQL 注入：使用参数化查询
- 防止 XSS：输出时转义
- 消息长度限制：10000 字符

## 8. 性能优化设计

### 8.1 连接优化

- 使用 epoll/kqueue 提高并发连接数
- 连接复用，减少握手开销
- 心跳检测，及时清理死连接

### 8.2 数据库优化

- 合理使用索引
- 分页查询，避免全表扫描
- 定期清理过期数据

### 8.3 缓存策略

- 用户信息缓存（Redis）
- 在线状态缓存
- 最近消息缓存

### 8.4 消息压缩

- 大消息使用 gzip 压缩
- 二进制消息使用 Protocol Buffers

## 9. 扩展性设计

### 9.1 水平扩展

```
                    ┌─────────────┐
                    │   Nginx     │
                    │ (负载均衡)   │
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────┴─────┐   ┌─────┴─────┐   ┌─────┴─────┐
    │ Server 1  │   │ Server 2  │   │ Server 3  │
    └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
                    ┌──────┴──────┐
                    │    Redis    │
                    │  (Pub/Sub)  │
                    └─────────────┘
```

### 9.2 Redis Pub/Sub 消息路由

当用户 A 和用户 B 连接到不同的服务器实例时：

1. 用户 A 发送消息到 Server 1
2. Server 1 发布消息到 Redis
3. Server 2 订阅并收到消息
4. Server 2 推送消息给用户 B

```go
// 发布消息
redis.Publish("channel:"+msg.To, msg.ToJSON())

// 订阅消息
redis.Subscribe("channel:"+userID, func(msg string) {
    conn.Send <- []byte(msg)
})
```

## 10. 监控与日志

### 10.1 日志设计

```go
type LogEntry struct {
    Timestamp time.Time `json:"timestamp"`
    Level     string    `json:"level"`     // DEBUG, INFO, WARN, ERROR
    Module    string    `json:"module"`
    Message   string    `json:"message"`
    UserID    string    `json:"user_id,omitempty"`
    RequestID string    `json:"request_id,omitempty"`
}
```

### 10.2 监控指标

- 在线用户数
- 消息发送量（QPS）
- 消息延迟（P50, P95, P99）
- WebSocket 连接数
- 数据库查询延迟
- Redis 操作延迟
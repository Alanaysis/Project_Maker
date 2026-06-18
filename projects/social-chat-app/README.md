# 社交聊天软件 (Social Chat App)

## 项目简介

一个支持实时消息、群聊、文件传输的社交聊天系统。本项目从零实现，旨在深入理解即时通讯架构的核心原理。

## 学习目标

- **即时通讯架构**：理解长连接（WebSocket）、消息队列（Redis Pub/Sub）的工作原理
- **消息推送与离线存储**：掌握消息的可靠投递机制和离线消息的存储策略
- **端到端加密**：学会实现基本的端到端加密（E2EE）保护用户隐私
- **并发编程**：掌握 Go 语言的并发模型（goroutine、channel）在实时系统中的应用

## 技术栈

| 技术 | 用途 | 学习难度 |
|------|------|----------|
| **Go** | 主语言，实现服务器和核心逻辑 | ⭐⭐⭐ |
| **WebSocket** | 实时双向通信 | ⭐⭐⭐ |
| **Protocol Buffers** | 高效的消息序列化 | ⭐⭐ |
| **Redis** | 消息队列、会话存储、在线状态 | ⭐⭐⭐ |
| **SQLite/PostgreSQL** | 持久化存储 | ⭐⭐ |
| **JWT** | 用户认证 | ⭐⭐ |

## 重点难点

### ⭐ 重点
1. **WebSocket 连接管理**：如何维护大量并发连接，处理连接的生命周期
2. **消息可靠投递**：确保消息不丢失、不重复、按顺序到达
3. **离线消息存储**：用户离线时如何存储消息，上线后如何拉取
4. **用户状态同步**：实时更新用户的在线/离线状态

### ⭐ 难点
1. **消息队列设计**：使用 Redis Pub/Sub 实现消息的发布订阅
2. **并发安全**：多 goroutine 访问共享资源时的数据一致性
3. **端到端加密**：密钥交换、消息加解密的实现
4. **水平扩展**：如何支持多服务器实例的消息路由

## 💡 值得思考

1. **为什么选择 WebSocket 而不是 HTTP 长轮询？**
   - WebSocket 是全双工通信，服务器可以主动推送消息
   - HTTP 长轮询需要客户端不断请求，效率较低

2. **消息队列的作用是什么？**
   - 解耦生产者和消费者
   - 削峰填谷，处理突发消息量
   - 支持消息的异步处理

3. **如何保证消息的顺序性？**
   - 使用时间戳或序列号
   - 服务器端排序后再投递
   - 客户端展示时再次确认顺序

4. **离线消息应该推还是拉？**
   - 推送（Push）：服务器主动发送，适合实时性要求高的场景
   - 拉取（Pull）：客户端主动请求，适合离线消息同步
   - 本项目采用混合模式：在线推送 + 离线拉取

## 项目结构

```
social-chat-app/
├── cmd/
│   └── server/          # 服务器入口
│       └── main.go
├── internal/
│   ├── auth/            # 认证模块
│   ├── chat/            # 聊天核心逻辑
│   ├── message/         # 消息处理
│   ├── user/            # 用户管理
│   └── websocket/       # WebSocket 连接管理
├── pkg/
│   └── models/          # 数据模型
├── docs/                # 文档
├── examples/            # 使用示例
└── tests/               # 测试文件
```

## 快速开始

### 环境要求

- Go 1.21+
- Redis 6.0+（可选，用于消息队列）
- SQLite（默认）或 PostgreSQL

### 安装与运行

```bash
# 克隆项目
cd projects/social-chat-app

# 安装依赖
go mod tidy

# 编译服务器
go build -o chat-server ./cmd/server

# 运行服务器
./chat-server

# 或者直接运行
go run ./cmd/server
```

### 配置选项

服务器支持以下环境变量配置：

```bash
export CHAT_SERVER_PORT=8080          # 服务器端口
export CHAT_DB_TYPE=sqlite            # 数据库类型：sqlite 或 postgres
export CHAT_DB_PATH=./data/chat.db    # SQLite 数据库路径
export CHAT_REDIS_URL=redis://localhost:6379  # Redis 地址（可选）
export CHAT_JWT_SECRET=your-secret    # JWT 密钥
```

## API 文档

### WebSocket 连接

```
ws://localhost:8080/ws?token=<jwt_token>
```

### REST API

#### 用户注册
```http
POST /api/register
Content-Type: application/json

{
  "username": "user1",
  "password": "password123",
  "email": "user1@example.com"
}
```

#### 用户登录
```http
POST /api/login
Content-Type: application/json

{
  "username": "user1",
  "password": "password123"
}
```

#### 发送消息
```json
{
  "type": "message",
  "to": "user2",
  "content": "Hello!",
  "timestamp": 1234567890
}
```

#### 消息类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `message` | 文本消息 | `{"type":"message","to":"user2","content":"Hi"}` |
| `file` | 文件消息 | `{"type":"file","to":"user2","filename":"doc.pdf","data":"base64..."}` |
| `typing` | 输入状态 | `{"type":"typing","to":"user2"}` |
| `read` | 已读回执 | `{"type":"read","message_id":"123"}` |
| `status` | 状态更新 | `{"type":"status","status":"online"}` |

## 参考资源

### 开源项目
- [Tinode](https://github.com/tinode/chat) - Go 实现的即时通讯服务器
- [Matrix/Synapse](https://github.com/matrix-org/synapse) - 去中心化通信协议
- [Rocket.Chat](https://github.com/RocketChat/Rocket.Chat) - 团队协作聊天平台
- [Signal Server](https://github.com/signalapp/Signal-Server) - 端到端加密通讯

### 技术文档
- [Go WebSocket](https://pkg.go.dev/github.com/gorilla/websocket)
- [Redis Pub/Sub](https://redis.io/docs/manual/pub-sub/)
- [Protocol Buffers](https://protobuf.dev/)

## 学习路径

1. **第一阶段**：理解 WebSocket 基础，实现简单的消息收发
2. **第二阶段**：添加用户认证和消息存储
3. **第三阶段**：实现离线消息和消息队列
4. **第四阶段**：添加群聊和文件传输
5. **第五阶段**：实现端到端加密

## 许可证

MIT License
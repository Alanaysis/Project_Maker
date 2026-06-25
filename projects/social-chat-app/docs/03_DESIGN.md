# 系统设计文档

## 1. 架构设计

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      客户端层                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Web浏览器 │  │ CLI客户端│  │ 移动端   │  │ 桌面端   │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │              │              │              │         │
│       └──────────────┴──────────────┴──────────────┘         │
│                           │                                  │
└───────────────────────────┼──────────────────────────────────┘
                            │
┌───────────────────────────┼──────────────────────────────────┐
│                      服务层                                  │
│                           │                                  │
│  ┌────────────────────────┼────────────────────────┐        │
│  │              WebSocket服务器                      │        │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │        │
│  │  │ 连接管理器   │  │ 消息路由器   │  │ 认证服务 │ │        │
│  │  └─────────────┘  └─────────────┘  └──────────┘ │        │
│  └─────────────────────────────────────────────────┘        │
│                           │                                  │
│  ┌────────────────────────┼────────────────────────┐        │
│  │              HTTP API服务器                      │        │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │        │
│  │  │ 用户API     │  │ 消息API     │  │ 文件API  │ │        │
│  │  └─────────────┘  └─────────────┘  └──────────┘ │        │
│  └─────────────────────────────────────────────────┘        │
│                           │                                  │
└───────────────────────────┼──────────────────────────────────┘
                            │
┌───────────────────────────┼──────────────────────────────────┐
│                      数据层                                  │
│                           │                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   SQLite    │  │    Redis    │  │   文件存储   │         │
│  │  (主数据库)  │  │   (缓存)    │  │  (可选)     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 模块划分

```
src/
├── server/              # 服务器模块
│   ├── websocket_server.py  # WebSocket服务器
│   └── connection_manager.py # 连接管理器
├── client/              # 客户端模块
│   └── chat_client.py   # 聊天客户端
├── models/              # 数据模型
│   ├── database.py      # 数据库模型
│   └── db_manager.py    # 数据库管理器
└── utils/               # 工具模块
    ├── auth.py          # 认证服务
    └── validators.py    # 数据验证
```

### 1.3 技术架构

| 层次 | 技术选型 | 说明 |
|------|----------|------|
| 前端 | HTML/CSS/JS | 原生实现 |
| 通信 | WebSocket | 实时双向通信 |
| 后端 | Python/aiohttp | 异步Web框架 |
| 数据库 | SQLAlchemy/aiosqlite | 异步ORM |
| 认证 | JWT/bcrypt | 令牌认证 |

## 2. 数据库设计

### 2.1 ER图

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    User     │       │  Friendship │       │    User     │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id (PK)     │──┐    │ user_id(FK) │    ┌──│ id (PK)     │
│ username    │  │    │ friend_id(FK)│   │  │ username    │
│ email       │  │    │ status      │    │  │ email       │
│ password_hash│  │    │ created_at  │    │  │ ...         │
│ nickname    │  │    └─────────────┘    │  └─────────────┘
│ avatar_url  │  │                       │
│ bio         │  │    ┌─────────────┐    │
│ status      │  │    │   Message   │    │
│ last_seen   │  │    ├─────────────┤    │
│ created_at  │  ├───>│ sender_id(FK)│   │
│ updated_at  │  │    │ receiver_id │<───┘
└─────────────┘  │    │ (FK)        │
                 │    │ group_id(FK)│<───┐
                 │    │ message_type│    │
                 │    │ content     │    │
                 │    │ file_url    │    │
                 │    │ is_read     │    │
                 │    │ created_at  │    │
                 │    └─────────────┘    │
                 │                       │
                 │    ┌─────────────┐    │
                 │    │    Group    │    │
                 │    ├─────────────┤    │
                 └───>│ owner_id(FK)│    │
                      │ name        │    │
                      │ description │    │
                      │ avatar_url  │    │
                      │ max_members │    │
                      │ created_at  │    │
                      └─────────────┘    │
                                         │
                      ┌─────────────┐    │
                      │ GroupMember │    │
                      ├─────────────┤    │
                      │ user_id(FK) │────┘
                      │ group_id(FK)│
                      │ role        │
                      │ joined_at   │
                      └─────────────┘
```

### 2.2 表结构设计

#### users表

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nickname VARCHAR(50) DEFAULT '',
    avatar_url VARCHAR(500) DEFAULT '',
    bio VARCHAR(500) DEFAULT '',
    status VARCHAR(20) DEFAULT 'offline',
    last_seen DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
```

#### messages表

```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER NOT NULL,
    receiver_id INTEGER,
    group_id INTEGER,
    message_type VARCHAR(20) DEFAULT 'text',
    content TEXT NOT NULL,
    file_url VARCHAR(500),
    file_name VARCHAR(255),
    file_size INTEGER,
    is_read BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES users(id),
    FOREIGN KEY (receiver_id) REFERENCES users(id),
    FOREIGN KEY (group_id) REFERENCES groups(id)
);

CREATE INDEX idx_messages_sender ON messages(sender_id);
CREATE INDEX idx_messages_receiver ON messages(receiver_id);
CREATE INDEX idx_messages_group ON messages(group_id);
CREATE INDEX idx_messages_created ON messages(created_at);
```

#### groups表

```sql
CREATE TABLE groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500) DEFAULT '',
    avatar_url VARCHAR(500) DEFAULT '',
    owner_id INTEGER NOT NULL,
    max_members INTEGER DEFAULT 500,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id)
);
```

#### friendships表

```sql
CREATE TABLE friendships (
    user_id INTEGER NOT NULL,
    friend_id INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, friend_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (friend_id) REFERENCES users(id)
);
```

#### group_members表

```sql
CREATE TABLE group_members (
    user_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    role VARCHAR(20) DEFAULT 'member',
    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, group_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (group_id) REFERENCES groups(id)
);
```

#### friend_requests表

```sql
CREATE TABLE friend_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_user_id INTEGER NOT NULL,
    to_user_id INTEGER NOT NULL,
    message VARCHAR(200) DEFAULT '',
    status VARCHAR(20) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_user_id) REFERENCES users(id),
    FOREIGN KEY (to_user_id) REFERENCES users(id)
);
```

#### offline_messages表

```sql
CREATE TABLE offline_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (message_id) REFERENCES messages(id)
);
```

## 3. 接口设计

### 3.1 HTTP API接口

#### 用户注册

```
POST /api/register

请求体：
{
    "username": "string",
    "email": "string",
    "password": "string",
    "nickname": "string"  // 可选
}

响应：
{
    "message": "注册成功",
    "user": {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "nickname": "测试用户"
    },
    "token": "jwt_token_string"
}

错误响应：
{
    "error": "用户名已存在"
}
```

#### 用户登录

```
POST /api/login

请求体：
{
    "username": "string",
    "password": "string"
}

响应：
{
    "message": "登录成功",
    "user": {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com"
    },
    "token": "jwt_token_string"
}
```

#### 搜索用户

```
GET /api/users/search?q={query}

Headers:
Authorization: Bearer {token}

响应：
{
    "users": [
        {
            "id": 2,
            "username": "alice",
            "nickname": "Alice",
            "email": "alice@example.com"
        }
    ]
}
```

### 3.2 WebSocket消息协议

#### 连接建立

```
ws://localhost:8765/ws?token={jwt_token}
```

#### 消息格式

所有WebSocket消息使用JSON格式：

```json
{
    "type": "message_type",
    "data": { ... }
}
```

#### 客户端 -> 服务器消息

**发送消息**
```json
{
    "type": "send_message",
    "content": "Hello!",
    "receiver_id": 2,        // 单聊
    "group_id": null,        // 群聊
    "message_type": "text",  // text, image, file
    "file_url": null,
    "file_name": null,
    "file_size": null
}
```

**输入状态**
```json
{
    "type": "typing",
    "receiver_id": 2,
    "is_typing": true
}
```

**已读回执**
```json
{
    "type": "read_receipt",
    "sender_id": 2
}
```

**心跳**
```json
{
    "type": "heartbeat"
}
```

**获取好友列表**
```json
{
    "type": "get_friends"
}
```

**发送好友请求**
```json
{
    "type": "send_friend_request",
    "to_user_id": 3,
    "message": "请求添加好友"
}
```

**接受/拒绝好友请求**
```json
{
    "type": "accept_friend_request",
    "request_id": 1
}

{
    "type": "reject_friend_request",
    "request_id": 1
}
```

**创建群组**
```json
{
    "type": "create_group",
    "name": "我的群组",
    "description": "群组描述"
}
```

**加入/离开群组**
```json
{
    "type": "join_group",
    "group_id": 1
}

{
    "type": "leave_group",
    "group_id": 1
}
```

**获取消息历史**
```json
{
    "type": "get_messages",
    "receiver_id": 2,  // 或 group_id
    "limit": 50,
    "before_id": null
}
```

**搜索消息**
```json
{
    "type": "search_messages",
    "query": "关键词"
}
```

#### 服务器 -> 客户端消息

**新消息**
```json
{
    "type": "new_message",
    "message": {
        "id": 1,
        "sender_id": 1,
        "receiver_id": 2,
        "content": "Hello!",
        "message_type": "text",
        "created_at": "2024-01-01T00:00:00Z",
        "sender": {
            "id": 1,
            "username": "testuser",
            "nickname": "测试用户"
        }
    }
}
```

**用户上线/下线**
```json
{
    "type": "user_online",
    "user_id": 2,
    "username": "alice"
}

{
    "type": "user_offline",
    "user_id": 2,
    "username": "alice"
}
```

**输入状态**
```json
{
    "type": "typing",
    "user_id": 2,
    "is_typing": true
}
```

**已读回执**
```json
{
    "type": "read_receipt",
    "reader_id": 2,
    "count": 5
}
```

**好友列表**
```json
{
    "type": "friends_list",
    "friends": [
        {
            "id": 2,
            "username": "alice",
            "nickname": "Alice",
            "is_online": true
        }
    ]
}
```

**消息历史**
```json
{
    "type": "message_history",
    "messages": [...],
    "receiver_id": 2,
    "group_id": null
}
```

**搜索结果**
```json
{
    "type": "search_results",
    "query": "关键词",
    "messages": [...]
}
```

**错误**
```json
{
    "type": "error",
    "message": "错误描述"
}
```

## 4. 核心流程设计

### 4.1 用户注册流程

```
客户端                    服务器                    数据库
  │                         │                         │
  │--- POST /register ----->│                         │
  │                         │--- 验证输入 ----------->│
  │                         │<-- 验证结果 ------------│
  │                         │                         │
  │                         │--- 检查用户名 ---------->│
  │                         │<-- 查询结果 ------------│
  │                         │                         │
  │                         │--- 创建用户 ------------>│
  │                         │<-- 用户ID --------------│
  │                         │                         │
  │                         │--- 生成JWT令牌 --------->│
  │<-- 注册成功 + token ----│                         │
```

### 4.2 消息发送流程

```
客户端A                   服务器                    客户端B
  │                         │                         │
  │--- send_message ------->│                         │
  │                         │--- 验证消息 ----------->│
  │                         │                         │
  │                         │--- 存储消息 ------------>│
  │                         │                         │
  │                         │--- 查找接收者连接 ------>│
  │                         │                         │
  │                         │--- [在线] new_message ->│
  │                         │                         │
  │<-- message_sent --------│                         │
```

### 4.3 离线消息流程

```
客户端A                   服务器                    数据库         客户端B
  │                         │                         │            │
  │--- send_message ------->│                         │            │
  │                         │--- 存储消息 ------------>│            │
  │                         │                         │            │
  │                         │--- 查找接收者连接 ------>│            │
  │                         │                         │            │
  │                         │--- [离线] 存储离线消息 ->│            │
  │                         │                         │            │
  │<-- message_sent --------│                         │            │
  │                         │                         │            │
  │                         │                         │     (B上线) │
  │                         │<--- ws连接 -------------│------------│
  │                         │                         │            │
  │                         │--- 获取离线消息 -------->│            │
  │                         │<-- 离线消息列表 --------│            │
  │                         │                         │            │
  │                         │--- new_message -------->│------------│
  │                         │                         │            │
  │                         │--- 删除离线消息 -------->│            │
```

### 4.4 好友请求流程

```
用户A                     服务器                    用户B
  │                         │                         │
  │--- send_friend_request->│                         │
  │                         │--- 存储请求 ------------>│
  │                         │                         │
  │                         │--- friend_request ----->│
  │<-- friend_request_sent -│                         │
  │                         │                         │
  │                         │                    (用户B操作)
  │                         │<-- accept_friend_request│
  │                         │                         │
  │                         │--- 创建好友关系 -------->│
  │                         │                         │
  │                         │--- friend_accepted ---->│
```

## 5. 安全设计

### 5.1 认证机制

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   客户端    │────>│  HTTP API   │────>│   数据库    │
└─────────────┘     └─────────────┘     └─────────────┘
                          │
                          │ 验证密码
                          │ 生成JWT
                          │
                    ┌─────┴─────┐
                    │  JWT令牌  │
                    └───────────┘
                          │
┌─────────────┐     ┌─────┴─────┐     ┌─────────────┐
│   客户端    │────>│ WebSocket │────>│   连接管理  │
└─────────────┘     │   服务器  │     └─────────────┘
                    └───────────┘
                          │
                          │ 验证JWT
                          │ 提取用户信息
```

### 5.2 密码安全

- 使用bcrypt算法加密
- 自动生成salt
- 可调节计算成本
- 抗彩虹表攻击

### 5.3 输入验证

所有用户输入都需要验证：

1. **用户名**: 3-20位，字母数字下划线
2. **邮箱**: 有效邮箱格式
3. **密码**: 6-50位
4. **消息内容**: 最大5000字符
5. **群组名称**: 最大50字符

### 5.4 SQL注入防护

使用SQLAlchemy ORM，自动参数化查询：

```python
# 安全的查询方式
user = await session.execute(
    select(User).where(User.username == username)
)

# 危险的查询方式（禁止使用）
# query = f"SELECT * FROM users WHERE username = '{username}'"
```

## 6. 性能设计

### 6.1 连接管理

```python
class ConnectionManager:
    def __init__(self):
        self._connections: Dict[int, ConnectionInfo] = {}
        self._lock = asyncio.Lock()

    async def connect(self, user_id, websocket):
        async with self._lock:
            # 线程安全的连接管理
            self._connections[user_id] = ConnectionInfo(...)
```

### 6.2 数据库优化

1. **索引优化**: 为常用查询字段添加索引
2. **连接池**: 使用SQLAlchemy连接池
3. **批量操作**: 合并多条SQL语句
4. **分页查询**: 避免一次性加载过多数据

### 6.3 消息处理

1. **异步处理**: 使用asyncio处理并发
2. **批量发送**: 合并多条消息发送
3. **压缩传输**: 可选的消息压缩
4. **缓存策略**: 缓存热点数据

## 7. 可扩展性设计

### 7.1 水平扩展

```
                    ┌─────────────┐
                    │Load Balancer│
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────┴────┐        ┌────┴────┐        ┌────┴────┐
   │Server 1 │        │Server 2 │        │Server 3 │
   └────┬────┘        └────┬────┘        └────┬────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                    ┌──────┴──────┐
                    │    Redis    │
                    │  (Pub/Sub)  │
                    └─────────────┘
```

### 7.2 消息队列

使用Redis实现跨服务器消息传递：

```python
# 发布消息
await redis.publish(f'user:{user_id}', message)

# 订阅消息
async for message in redis.subscribe(f'user:{user_id}'):
    await websocket.send(message)
```

### 7.3 微服务拆分

1. **用户服务**: 用户注册、登录、资料管理
2. **消息服务**: 消息存储、查询、搜索
3. **连接服务**: WebSocket连接管理
4. **通知服务**: 推送通知、离线消息

## 8. 监控设计

### 8.1 关键指标

| 指标 | 说明 | 告警阈值 |
|------|------|----------|
| 在线用户数 | 当前连接数 | > 1000 |
| 消息延迟 | 消息送达时间 | > 200ms |
| 错误率 | 请求失败比例 | > 1% |
| 响应时间 | API响应时间 | > 100ms |

### 8.2 日志设计

```python
import logging

logger = logging.getLogger(__name__)

# 用户操作日志
logger.info(f"用户 {username} 登录成功")

# 错误日志
logger.error(f"消息发送失败: {error}")

# 性能日志
logger.debug(f"数据库查询耗时: {elapsed}ms")
```

### 8.3 健康检查

```python
@app.route('/api/health')
async def health_check():
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'connections': connection_manager.get_online_count()
    }
```

## 9. 部署架构

### 9.1 单机部署

```
┌─────────────────────────────────────┐
│           单台服务器                 │
│  ┌─────────────┐  ┌─────────────┐  │
│  │  Python App │  │   SQLite    │  │
│  │  (aiohttp)  │  │  (文件)     │  │
│  └─────────────┘  └─────────────┘  │
└─────────────────────────────────────┘
```

### 9.2 Docker部署

```yaml
version: '3.8'
services:
  chat-app:
    build: .
    ports:
      - "8765:8765"
    volumes:
      - ./data:/app/data
    environment:
      - JWT_SECRET_KEY=your-secret-key
```

### 9.3 生产环境部署

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Nginx     │────>│  Python App │────>│ PostgreSQL  │
│  (反向代理)  │     │  (多实例)   │     │  (数据库)   │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │    Redis    │
                    │  (缓存/队列) │
                    └─────────────┘
```

## 10. 总结

本设计文档详细描述了社交聊天应用的系统架构、数据库设计、接口设计、核心流程、安全设计、性能设计等方面。通过模块化设计和异步处理，系统具有良好的可扩展性和性能表现。

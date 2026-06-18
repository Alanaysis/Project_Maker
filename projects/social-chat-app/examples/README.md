# 使用示例

本目录包含社交聊天系统的使用示例。

## 示例列表

### 1. register_and_login.go

用户注册和登录示例。

**使用方法**：

```bash
# 注册新用户
go run register_and_login.go register <username> <password>

# 登录已有用户
go run register_and_login.go login <username> <password>
```

**示例**：

```bash
# 注册用户
go run register_and_login.go register alice password123

# 登录用户
go run register_and_login.go login alice password123
```

### 2. client.go

WebSocket 聊天客户端。

**使用方法**：

```bash
# 先获取 Token（通过注册或登录）
go run register_and_login.go register alice password123

# 使用 Token 连接 WebSocket
go run client.go ws://localhost:8080/ws <token>
```

**客户端命令**：

- `/to <user_id> <message>` - 发送消息给指定用户
- `/quit` - 退出客户端

**示例会话**：

```
# 终端 1：注册用户 Alice
go run register_and_login.go register alice password123
# 输出 Token: eyJhbGciOiJIUzI1NiIs...

# 终端 2：注册用户 Bob
go run register_and_login.go register bob password456
# 输出 Token: eyJhbGciOiJIUzI1NiIs...

# 终端 1：启动 Alice 的客户端
go run client.go ws://localhost:8080/ws <alice_token>

# 终端 2：启动 Bob 的客户端
go run client.go ws://localhost:8080/ws <bob_token>

# 在 Alice 的终端发送消息
/to <bob_user_id> Hello Bob!

# 在 Bob 的终端回复消息
/to <alice_user_id> Hi Alice!
```

## 完整测试流程

### 步骤 1：启动服务器

```bash
cd projects/social-chat-app
go run ./cmd/server
```

服务器将在 `http://localhost:8080` 启动。

### 步骤 2：注册用户

```bash
# 终端 1
cd examples
go run register_and_login.go register alice password123

# 终端 2
go run register_and_login.go register bob password456
```

### 步骤 3：启动聊天客户端

```bash
# 终端 1（使用 Alice 的 Token）
go run client.go ws://localhost:8080/ws <alice_token>

# 终端 2（使用 Bob 的 Token）
go run client.go ws://localhost:8080/ws <bob_token>
```

### 步骤 4：开始聊天

在任一终端输入消息：

```
# Alice 终端
/to <bob_id> Hello Bob! How are you?

# Bob 终端
/to <alice_id> Hi Alice! I'm doing great!
```

## API 测试

### 注册用户

```bash
curl -X POST http://localhost:8080/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'
```

### 登录用户

```bash
curl -X POST http://localhost:8080/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'
```

### 获取用户信息

```bash
curl -X GET http://localhost:8080/api/user/<user_id> \
  -H "Authorization: Bearer <token>"
```

### 搜索用户

```bash
curl -X GET "http://localhost:8080/api/users?q=test" \
  -H "Authorization: Bearer <token>"
```

### 获取对话历史

```bash
curl -X GET http://localhost:8080/api/messages/<other_user_id> \
  -H "Authorization: Bearer <token>"
```

## 注意事项

1. 确保服务器已启动后再运行示例
2. Token 是区分大小写的，请完整复制
3. 用户 ID 是 UUID 格式，如 `550e8400-e29b-41d4-a716-446655440000`
4. WebSocket 连接断开后需要重新获取 Token
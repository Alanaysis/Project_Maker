# 快速开始指南

本指南帮助您快速启动和测试社交聊天系统。

## 前置条件

1. **Go 1.21+**
   - 下载地址：https://go.dev/dl/
   - 验证安装：`go version`

2. **Git**（可选）
   - 用于克隆项目

## 步骤 1：安装依赖

```bash
cd projects/social-chat-app
go mod tidy
```

这将下载所有必要的依赖包：
- `github.com/gorilla/websocket` - WebSocket 库
- `github.com/mattn/go-sqlite3` - SQLite 驱动
- `golang.org/x/crypto` - 加密库
- `github.com/golang-jwt/jwt/v5` - JWT 库
- `github.com/google/uuid` - UUID 生成

## 步骤 2：运行测试

```bash
go test -v ./...
```

预期输出：
```
=== RUN   TestJWTManager_Generate
--- PASS: TestJWTManager_Generate (0.00s)
=== RUN   TestJWTManager_Verify
--- PASS: TestJWTManager_Verify (0.00s)
...
PASS
ok      social-chat-app/tests  0.123s
```

## 步骤 3：启动服务器

```bash
go run ./cmd/server
```

预期输出：
```
╔═══════════════════════════════════════════════════════════╗
║          Social Chat Server v1.0.0                       ║
║          Listening on http://localhost:8080              ║
║          WebSocket: ws://localhost:8080/ws              ║
╚═══════════════════════════════════════════════════════════╝
```

服务器将在 `http://localhost:8080` 启动。

### Web UI 使用

打开浏览器访问 `http://localhost:8080`，可以直接使用 Web 界面进行聊天：
1. 注册两个用户（在两个浏览器标签页中）
2. 登录后，复制一个用户的 ID
3. 在另一个用户的界面中，将 ID 粘贴到左侧的搜索框，按回车
4. 开始聊天！

## 步骤 4：注册用户

打开新的终端窗口：

```bash
cd projects/social-chat-app/examples

# 注册用户 Alice
go run register_and_login.go register alice password123

# 注册用户 Bob
go run register_and_login.go register bob password456
```

每个用户注册后会显示：
- User ID（用户 ID）
- Token（JWT Token）

**请记下每个用户的 Token，后续步骤需要使用。**

## 步骤 5：启动聊天客户端

### 方式一：使用 CLI 客户端（推荐）

```bash
# 编译客户端
go build -o bin/chat-client ./cmd/client

# 终端 1（Alice）- 使用 Alice 的 token 启动聊天
./bin/chat-client chat <alice_token>

# 终端 2（Bob）- 使用 Bob 的 token 启动聊天
./bin/chat-client chat <bob_token>
```

### 方式二：使用示例客户端

```bash
cd projects/social-chat-app/examples

# 终端 1（Alice）
go run client.go ws://localhost:8080/ws <alice_token>

# 终端 2（Bob）
go run client.go ws://localhost:8080/ws <bob_token>
```

## 步骤 6：开始聊天

### 在 Alice 的终端发送消息

```
/to <bob_user_id> Hello Bob! How are you?
```

### 在 Bob 的终端回复消息

```
/to <alice_user_id> Hi Alice! I'm doing great!
```

## 常见问题

### Q: 出现 "connection refused" 错误

**原因**：服务器未启动

**解决**：
```bash
# 确保服务器正在运行
go run ./cmd/server
```

### Q: 出现 "unauthorized" 错误

**原因**：Token 无效或过期

**解决**：
```bash
# 重新登录获取新 Token
go run register_and_login.go login alice password123
```

### Q: 出现 "user not found" 错误

**原因**：用户 ID 不正确

**解决**：
- 检查用户 ID 是否正确复制
- 用户 ID 是 UUID 格式，如 `550e8400-e29b-41d4-a716-446655440000`

### Q: 消息发送后没有收到

**原因**：接收方未在线

**解决**：
- 确保接收方的客户端正在运行
- 消息会存储为离线消息，接收方上线后会自动同步

## API 测试

### 使用 curl 测试

#### 注册用户
```bash
curl -X POST http://localhost:8080/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'
```

#### 登录用户
```bash
curl -X POST http://localhost:8080/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'
```

#### 获取用户信息
```bash
curl -X GET http://localhost:8080/api/user/<user_id> \
  -H "Authorization: Bearer <token>"
```

#### 搜索用户
```bash
curl -X GET "http://localhost:8080/api/users?q=test" \
  -H "Authorization: Bearer <token>"
```

#### 获取对话历史
```bash
curl -X GET http://localhost:8080/api/messages/<other_user_id> \
  -H "Authorization: Bearer <token>"
```

## 下一步

完成基本测试后，您可以：

1. **查看代码**：了解 WebSocket 连接管理和消息处理的实现
2. **阅读文档**：查看 `docs/` 目录下的技术文档
3. **修改代码**：尝试添加新功能或优化现有代码
4. **运行测试**：查看测试覆盖率和测试用例

## 使用 Docker

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 相关资源

- [WebSocket 协议](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
- [Go 并发编程](https://go.dev/doc/effective_go#concurrency)
- [JWT 认证](https://jwt.io/introduction)
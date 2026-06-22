# 项目索引

## 项目概述

**项目名称**：社交聊天软件 (Social Chat App)

**一句话描述**：实现一个支持实时消息、群聊、文件传输的社交聊天系统

**技术栈**：Go, WebSocket, SQLite, JWT

## 文档目录

### 核心文档

| 文档 | 说明 | 阅读顺序 |
|------|------|----------|
| [README.md](README.md) | 项目说明、快速开始 | 1 |
| [QUICKSTART.md](QUICKSTART.md) | 详细使用指南 | 2 |
| [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) | 实现总结 | 3 |
| [LEARNING_NOTES.md](LEARNING_NOTES.md) | 学习笔记模板 | 4 |

### 技术文档

| 文档 | 说明 | 位置 |
|------|------|------|
| 市场调研 | 同类型项目分析 | [docs/01-RESEARCH.md](docs/01-RESEARCH.md) |
| 需求分析 | 用户画像、功能需求 | [docs/02-REQUIREMENTS.md](docs/02-REQUIREMENTS.md) |
| 技术设计 | 架构、数据结构、接口 | [docs/03-DESIGN.md](docs/03-DESIGN.md) |
| 产品思维 | 竞品分析、用户吸引力 | [docs/04-PRODUCT.md](docs/04-PRODUCT.md) |
| 开发手册 | 环境搭建、模块解析 | [docs/05-DEVELOPMENT.md](docs/05-DEVELOPMENT.md) |

### 使用示例

| 文档 | 说明 | 位置 |
|------|------|------|
| 示例说明 | 使用示例说明 | [examples/README.md](examples/README.md) |
| 注册登录 | 用户注册和登录 | [examples/register_and_login.go](examples/register_and_login.go) |
| 聊天客户端 | WebSocket 聊天客户端 | [examples/client.go](examples/client.go) |

## 代码目录

### 入口文件

```
cmd/server/main.go    # 服务器入口，HTTP 路由，数据库初始化
```

### 核心模块

#### 认证模块 (internal/auth/)

| 文件 | 说明 |
|------|------|
| auth.go | 认证服务（注册、登录） |
| jwt.go | JWT Token 生成和验证 |
| middleware.go | 认证中间件 |

#### 用户模块 (internal/user/)

| 文件 | 说明 |
|------|------|
| user.go | 用户服务（查询、更新） |
| repository.go | 用户存储（SQLite） |

#### 消息模块 (internal/message/)

| 文件 | 说明 |
|------|------|
| message.go | 消息服务（创建、查询） |
| repository.go | 消息存储（SQLite） |

#### WebSocket 模块 (internal/websocket/)

| 文件 | 说明 |
|------|------|
| connection.go | 连接封装（读写、消息处理） |
| manager.go | 连接管理（注册、注销、路由） |

### 数据模型 (pkg/models/)

| 文件 | 说明 |
|------|------|
| user.go | 用户模型 |
| message.go | 消息模型 |
| group.go | 群组模型 |
| websocket.go | WebSocket 消息格式 |

### 测试文件 (tests/)

| 文件 | 说明 |
|------|------|
| auth_test.go | 认证模块测试 |
| message_test.go | 消息模块测试 |
| user_test.go | 用户模块测试 |
| integration_test.go | 集成测试 |

## 快速导航

### 我想...

**了解项目**：
1. 阅读 [README.md](README.md)
2. 查看 [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

**运行项目**：
1. 查看 [QUICKSTART.md](QUICKSTART.md)
2. 运行 `go run ./cmd/server`

**学习技术**：
1. 阅读 [docs/01-RESEARCH.md](docs/01-RESEARCH.md)（市场调研）
2. 阅读 [docs/03-DESIGN.md](docs/03-DESIGN.md)（技术设计）
3. 阅读 [docs/05-DEVELOPMENT.md](docs/05-DEVELOPMENT.md)（开发手册）

**修改代码**：
1. 查看 [internal/websocket/connection.go](internal/websocket/connection.go)（WebSocket 实现）
2. 查看 [internal/message/message.go](internal/message/message.go)（消息处理）
3. 查看 [cmd/server/main.go](cmd/server/main.go)（HTTP 路由）

**运行测试**：
```bash
go test -v ./...
```

## 关键概念

### WebSocket 连接管理

**位置**：`internal/websocket/`

**核心概念**：
- 连接池：管理所有活跃的 WebSocket 连接
- 心跳检测：定期发送 Ping/Pong 保持连接
- 消息路由：根据接收者 ID 转发消息

**关键代码**：
```go
// manager.go
type Manager struct {
    connections map[string]*Connection  // userID -> Connection
    register    chan *Connection
    unregister  chan *Connection
}
```

### 消息存储

**位置**：`internal/message/`

**核心概念**：
- 消息持久化：存储到 SQLite 数据库
- 离线消息：用户离线时存储消息
- 状态跟踪：已发送、已送达、已读

**关键代码**：
```go
// repository.go
type Repository interface {
    Save(msg *Message) error
    FindByConversation(user1, user2 string, limit, offset int) ([]*Message, error)
    FindUnread(userID string) ([]*Message, error)
    MarkAsRead(messageIDs []string) error
}
```

### 用户认证

**位置**：`internal/auth/`

**核心概念**：
- JWT Token：无状态认证
- 密码加密：bcrypt 哈希
- 中间件：统一认证逻辑

**关键代码**：
```go
// jwt.go
type JWTManager struct {
    secret []byte
    expiry time.Duration
}

func (m *JWTManager) Generate(userID, username, role string) (string, error)
func (m *JWTManager) Verify(tokenString string) (*Claims, error)
```

## 学习路径

### 初级（1-2 周）

- [ ] 理解 WebSocket 协议
- [ ] 实现简单的消息收发
- [ ] 学习 Go 并发编程

**相关文件**：
- `internal/websocket/connection.go`
- `internal/websocket/manager.go`

### 中级（2-4 周）

- [ ] 实现用户认证系统
- [ ] 设计消息存储方案
- [ ] 处理离线消息

**相关文件**：
- `internal/auth/`
- `internal/message/`
- `pkg/models/`

### 高级（4-8 周）

- [ ] 实现端到端加密
- [ ] 设计分布式架构
- [ ] 性能优化

**相关文件**：
- `docs/03-DESIGN.md`
- `docs/05-DEVELOPMENT.md`

## 常见问题

### Q: 如何添加新的消息类型？

**步骤**：
1. 在 `pkg/models/message.go` 添加新类型常量
2. 在 `internal/websocket/connection.go` 添加处理逻辑
3. 更新消息存储（如果需要）

### Q: 如何添加新的 API？

**步骤**：
1. 在 `cmd/server/main.go` 添加路由
2. 创建处理器函数
3. 添加认证中间件（如果需要）

### Q: 如何扩展数据库支持？

**步骤**：
1. 实现 `Repository` 接口
2. 在 `cmd/server/main.go` 初始化新存储
3. 更新配置

## 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支：`git checkout -b feature/new-feature`
3. 提交更改：`git commit -m 'Add new feature'`
4. 推送分支：`git push origin feature/new-feature`
5. 创建 Pull Request

## 许可证

MIT License
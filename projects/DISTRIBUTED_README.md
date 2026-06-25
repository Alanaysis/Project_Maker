# 🎮 分布式 & 通讯模块

> 4 个深度学习项目，涵盖分布式游戏、即时通讯、消息语义、服务发现

---

## 📋 项目列表

| 项目 | 描述 | 技术栈 | 难度 | 状态 |
|------|------|--------|------|------|
| [distributed-game-system](distributed-game-system/) | 分布式游戏系统 | Go | ⭐⭐⭐⭐ | ✅ |
| [social-chat-app](social-chat-app/) | 社交聊天应用 | Go | ⭐⭐⭐⭐ | ✅ |
| [exactly-once](exactly-once/) | Exactly-once 语义 | Go | ⭐⭐⭐ | ✅ |
| [service-discovery](service-discovery/) | 服务发现系统 | Go | ⭐⭐⭐⭐ | ✅ |

---

## 🎯 学习路径

```
分布式游戏系统 → 社交聊天应用 → Exactly-once 语义
       ↓              ↓              ↓
    状态同步        消息推送        消息去重
    延迟优化        离线存储        幂等处理
    一致性哈希      WebSocket       事务消息
```

### 推荐学习顺序

1. **distributed-game-system** (分布式游戏)
   - 学习分布式状态同步原理
   - 理解网络延迟优化技术
   - 掌握一致性哈希和负载均衡

2. **social-chat-app** (即时通讯)
   - 学习即时通讯架构
   - 理解消息推送和离线存储
   - 掌握 WebSocket 通信

3. **exactly-once** (消息语义)
   - 理解消息传递语义（at-most-once, at-least-once, exactly-once）
   - 掌握幂等性和去重机制
   - 学会事务消息和两阶段提交
   - 理解消费确认（手动、批量、自动重试）
   - 掌握事务发件箱模式

---

## 🔧 技术栈

| 技术 | 用途 | 学习资源 |
|------|------|----------|
| **Go** | 主语言 | [Go 官方文档](https://go.dev/doc/) |
| **WebSocket** | 实时通信 | [WebSocket 文档](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket) |
| **Protobuf** | 序列化 | [Protobuf 文档](https://protobuf.dev/) |
| **SQLite** | 数据存储 | [SQLite 文档](https://www.sqlite.org/docs.html) |
| **JWT** | 身份认证 | [JWT 文档](https://jwt.io/) |

---

## 📊 项目详情

### 1. distributed-game-system (分布式游戏)

**核心功能**：
- 客户端预测和服务器校正
- 状态同步（快照 + Delta 压缩）
- 实体插值
- 一致性哈希（虚拟节点）
- UDP 网络通信
- 游戏世界管理（玩家、战斗、边界）

**代码量**：约 41 个文件

**快速开始**：
```bash
cd distributed-game-system
go mod tidy
make build
./bin/server
```

---

### 2. social-chat-app (即时通讯)

**核心功能**：
- 用户管理（注册、登录、查询、搜索）
- 单聊消息（实时推送、存储、状态跟踪）
- 离线消息（存储、同步、删除）
- WebSocket 连接管理（连接池、心跳、路由）
- JWT 认证系统

**代码量**：约 42 个文件

**快速开始**：
```bash
cd social-chat-app
go mod tidy
make build
make run
```

---

### 3. exactly-once (Exactly-once 语义)

**核心功能**：
- 消息去重（基于幂等键的重复检测）
- 幂等处理（相同消息产生相同结果）
- 事务消息（两阶段提交，原子操作和回滚）
- 消费确认（手动确认、批量确认、指数退避重试）
- 事务发件箱（原子性数据库写入 + 消息发布）
- 状态追踪（完整的消息生命周期审计）
- 实际应用示例（支付系统、订单系统、消息队列）

**代码量**：约 30 个文件

**快速开始**：
```bash
cd exactly-once
go run ./cmd/demo
go run ./examples/payment
go run ./examples/order
go run ./examples/mq
```

---

### 4. service-discovery (服务发现)

**核心功能**：
- 服务注册（TTL 租约 + 心跳续期）
- 健康检查（TCP / HTTP 探活）
- 服务发现（Watch 机制 + 本地缓存）
- 负载均衡（轮询、随机、加权轮询）
- HTTP API（注册、发现、选择、注销）

**代码量**：约 21 个文件

**快速开始**：
```bash
cd service-discovery
go build -o service-discovery ./cmd/server
./service-discovery
# 另一个终端:
curl http://localhost:8500/health
curl -X POST http://localhost:8500/register -H "Content-Type: application/json" \
  -d '{"id":"svc-1","name":"web","address":"10.0.0.1","port":8080}'
curl http://localhost:8500/discover?name=web
```

---

## 📚 学习资源

### 书籍
- 《分布式系统概念》
- 《即时通讯技术》

### 课程
- [MIT 6.824](https://pdos.csail.mit.edu/6.824/)

### 开源项目
- [Skynet](https://github.com/cloudwu/skynet)
- [Matrix](https://github.com/matrix-org)
- [Rocket.Chat](https://github.com/RocketChat/Rocket.Chat)

---

## 🔗 相关链接

- [返回主 README](../README.md)
- [学习路径图](../LEARNING_PATHS.md)
- [项目索引](../PROJECT_INDEX.md)

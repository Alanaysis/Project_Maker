# 🎮 分布式 & 通讯模块

> 2 个深度学习项目，涵盖分布式游戏、即时通讯

---

## 📋 项目列表

| 项目 | 描述 | 技术栈 | 难度 | 状态 |
|------|------|--------|------|------|
| [distributed-game-system](distributed-game-system/) | 分布式游戏系统 | Go | ⭐⭐⭐⭐ | ✅ |
| [social-chat-app](social-chat-app/) | 社交聊天应用 | Go | ⭐⭐⭐⭐ | ✅ |

---

## 🎯 学习路径

```
分布式游戏系统 → 社交聊天应用
       ↓              ↓
    状态同步        消息推送
    延迟优化        离线存储
    一致性哈希      WebSocket
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

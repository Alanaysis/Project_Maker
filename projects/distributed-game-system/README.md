# 分布式游戏系统 (Distributed Game System)

## 项目简介

一个支持多玩家实时对战的分布式游戏服务器，从零实现客户端预测、服务器验证、状态同步等核心机制。

## 学习目标

- **分布式状态同步原理** - 理解如何在多个客户端之间同步游戏状态
- **网络延迟优化技术** - 掌握客户端预测和服务器校正算法
- **一致性哈希和负载均衡** - 学会分布式系统中的玩家分配策略

## 技术栈

| 技术 | 用途 | 学习难度 |
|------|------|----------|
| Go | 主语言，高并发网络服务 | ⭐⭐ |
| Protobuf | 高效序列化协议 | ⭐⭐ |
| UDP/TCP | 网络传输层 | ⭐⭐⭐ |
| 一致性哈希 | 分布式负载均衡 | ⭐⭐⭐ |

## 核心循环

```
玩家输入 → 客户端预测 → 服务器验证 → 状态同步 → 客户端校正
```

## 项目结构

```
distributed-game-system/
├── cmd/
│   ├── server/          # 游戏服务器入口
│   └── client/          # 游戏客户端入口
├── internal/
│   ├── game/            # 游戏核心逻辑
│   ├── network/         # 网络通信层
│   ├── sync/            # 状态同步引擎
│   ├── prediction/      # 客户端预测系统
│   └── hashing/         # 一致性哈希实现
├── pkg/
│   ├── protocol/        # 通信协议定义
│   ├── config/          # 配置管理
│   └── logger/          # 日志系统
├── api/                 # API 定义
├── proto/               # Protobuf 定义文件
├── docs/                # 项目文档
├── examples/            # 使用示例
├── tests/               # 集成测试
└── scripts/             # 构建脚本
```

## 快速开始

```bash
# 编译项目
go build -o bin/server ./cmd/server
go build -o bin/client ./cmd/client

# 启动服务器
./bin/server -port 8080

# 启动客户端
./bin/client -server localhost:8080 -name Player1
```

## 重点难点

### ⭐ 客户端预测 (Client Prediction)
客户端在发送输入后立即在本地模拟结果，无需等待服务器确认，大幅降低感知延迟。

### ⭐ 服务器校正 (Server Reconciliation)
当服务器状态与客户端预测不一致时，客户端需要从服务器状态重新应用未确认的输入。

### ⭐ 状态插值 (Entity Interpolation)
远程玩家的状态需要在两个服务器快照之间平滑插值，避免画面抖动。

### ⭐ 一致性哈希 (Consistent Hashing)
使用虚拟节点的一致性哈希环，实现玩家到服务器的均匀分配和最小化迁移。

## 值得思考

- 💡 为什么选择 UDP 而不是 TCP？在什么场景下 TCP 更合适？
- 💡 如何处理作弊问题？客户端预测是否会导致安全漏洞？
- 💡 状态同步的频率如何确定？过高和过低各有什么问题？
- 💡 一致性哈希的虚拟节点数量如何选择？

## 参考资源

- [Gabriel Gambetta - Fast-Paced Multiplayer](https://www.gabrielgambetta.com/client-server-game-architecture.html)
- [Valve Developer Wiki - Source Multiplayer Networking](https://developer.valvesoftware.com/wiki/Source_Multiplayer_Networking)
- [Glenn Fiedler - Game Networking](https://gafferongames.com/)
- [Agones - Game Server on Kubernetes](https://github.com/googleforgames/agones)
- [Nakama - Open-Source Game Server](https://github.com/heroiclabs/nakama)

## 许可证

MIT License

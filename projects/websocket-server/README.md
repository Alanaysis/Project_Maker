# WebSocket 服务器

一个使用纯 Go 实现的高性能 WebSocket 服务器，不依赖任何第三方框架。

## 学习目标

- 理解 WebSocket 协议的工作原理
- 掌握长连接管理技术
- 学会实现消息广播功能

## 功能特性

- **WebSocket 协议实现**: 完整的 RFC 6455 WebSocket 协议支持
- **HTTP 升级**: 从 HTTP 连接升级到 WebSocket 连接
- **连接管理**: 支持多客户端并发连接
- **消息广播**: 向所有连接的客户端广播消息
- **心跳检测**: 自动检测并清理断开的连接
- **房间系统**: 支持消息分组广播

## 项目结构

```
websocket-server/
├── cmd/
│   └── server/
│       └── main.go          # 服务器入口
├── internal/
│   ├── server/
│   │   └── server.go        # HTTP/WebSocket 服务器
│   ├── websocket/
│   │   ├── conn.go          # WebSocket 连接实现
│   │   ├── frame.go         # WebSocket 帧处理
│   │   └── handshake.go     # WebSocket 握手
│   ├── client/
│   │   └── client.go        # 客户端管理
│   └── room/
│       └── room.go          # 房间/频道管理
├── examples/
│   └── client.html          # 浏览器测试客户端
├── docs/                    # 学习文档
├── go.mod
├── go.sum
└── README.md
```

## 快速开始

### 安装依赖

```bash
go mod tidy
```

### 运行服务器

```bash
go run cmd/server/main.go
```

服务器将在 `localhost:8080` 启动。

### 测试连接

1. 在浏览器中打开 `examples/client.html`
2. 或使用 `websocat` 命令行工具:
   ```bash
   websocat ws://localhost:8080/ws
   ```

## WebSocket 协议概述

WebSocket 是一种在单个 TCP 连接上进行全双工通信的协议。它通过 HTTP 升级握手建立连接，之后双方可以随时发送数据。

### 连接流程

```
客户端                     服务器
  |                          |
  |--- HTTP Upgrade -------->|
  |<-- 101 Switching --------|
  |                          |
  |<====== WebSocket ========>|
  |      (全双工通信)        |
```

### 帧格式

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-------+-+-------------+-------------------------------+
|F|R|R|R| opcode|M| Payload len |    Extended payload length    |
|I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
|N|V|V|V|       |S|             |   (if payload len==126/127)   |
| |1|2|3|       |K|             |                               |
+-+-+-+-+-------+-+-------------+-------------------------------+
|     Extended payload length continued, if payload len == 127  |
+-------------------------------+-------------------------------+
|                               |Masking-key, if MASK set to 1  |
+-------------------------------+-------------------------------+
| Masking-key (continued)       |          Payload Data         |
+-------------------------------+-------------------------------+
```

## API 说明

### WebSocket 端点

- **URL**: `ws://localhost:8080/ws`
- **协议**: WebSocket (RFC 6455)

### 消息格式

支持以下消息类型:

1. **文本消息** (opcode 0x1): UTF-8 编码的文本
2. **二进制消息** (opcode 0x2): 原始二进制数据
3. **关闭连接** (opcode 0x8): 关闭帧
4. **Ping** (opcode 0x9): 心跳请求
5. **Pong** (opcode 0xA): 心跳响应

## 学习资源

- [RFC 6455 - The WebSocket Protocol](https://tools.ietf.org/html/rfc6455)
- [MDN WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [WebSocket 协议详解](https://www.ruanyifeng.com/blog/2017/05/websocket.html)

## 许可证

MIT License

# WebSocket 技术调研

## 1. WebSocket 概述

WebSocket 是一种在单个 TCP 连接上进行全双工通信的协议。它被设计用来在 Web 浏览器和服务器之间建立持久连接，允许双向实时数据传输。

### 1.1 历史背景

- **2008年**: WebSocket 协议首次被提出
- **2011年**: RFC 6455 发布，定义了 WebSocket 协议标准
- **2012年**: 所有主流浏览器支持 WebSocket
- **2021年**: RFC 8441 发布，定义了 HTTP/2 上的 WebSocket

### 1.2 协议特点

| 特性 | 描述 |
|------|------|
| 全双工通信 | 客户端和服务器可以同时发送数据 |
| 低延迟 | 建立连接后无需重复握手 |
| 低开销 | 数据帧头部仅 2-14 字节 |
| 持久连接 | 连接保持打开状态，直到主动关闭 |
| 跨域支持 | 可以跨域通信 |

## 2. 应用场景

### 2.1 实时通信

- **聊天应用**: 微信网页版、Slack、Discord
- **即时通讯**: 消息推送、在线客服
- **视频会议**: 信令服务器

### 2.2 实时数据

- **股票行情**: 实时股价更新
- **体育比分**: 实时比赛数据
- **监控系统**: 服务器状态监控
- **物联网**: 设备数据上报

### 2.3 在线游戏

- **多人游戏**: 实时玩家交互
- **棋牌游戏**: 实时对战
- **网页游戏**: 游戏状态同步

### 2.4 协同工作

- **协同编辑**: Google Docs、Notion
- **白板工具**: 实时绘图同步
- **项目管理**: 实时任务更新

## 3. WebSocket vs 其他技术

### 3.1 WebSocket vs HTTP

| 特性 | WebSocket | HTTP |
|------|-----------|------|
| 通信模式 | 全双工 | 请求-响应 |
| 连接方式 | 持久连接 | 短连接/长轮询 |
| 数据方向 | 双向 | 单向（请求后响应） |
| 头部开销 | 2-14 字节 | 每次请求数百字节 |
| 实时性 | 高 | 低（需要轮询） |

### 3.2 WebSocket vs SSE (Server-Sent Events)

| 特性 | WebSocket | SSE |
|------|-----------|-----|
| 通信模式 | 全双工 | 单向（服务器到客户端） |
| 协议 | ws:// / wss:// | HTTP/HTTPS |
| 浏览器支持 | 所有主流浏览器 | 所有主流浏览器（除 IE） |
| 自动重连 | 需手动实现 | 内置支持 |
| 二进制数据 | 支持 | 仅文本 |

### 3.3 WebSocket vs Long Polling

| 特性 | WebSocket | Long Polling |
|------|-----------|--------------|
| 连接开销 | 一次握手 | 每次请求都握手 |
| 服务器资源 | 低 | 高 |
| 实时性 | 高 | 中等 |
| 实现复杂度 | 中等 | 低 |

## 4. 技术优缺点

### 4.1 优点

1. **低延迟**: 建立连接后，数据传输无需额外握手
2. **低开销**: 数据帧头部小，减少网络流量
3. **双向通信**: 服务器可以主动推送数据
4. **持久连接**: 减少连接建立的开销
5. **跨域支持**: 可以跨域通信
6. **二进制支持**: 支持文本和二进制数据

### 4.2 缺点

1. **代理问题**: 某些代理服务器可能不支持 WebSocket
2. **负载均衡**: 需要支持会话保持的负载均衡器
3. **连接管理**: 需要处理连接断开和重连
4. **安全性**: 需要额外的安全措施（WSS、认证、限流）
5. **浏览器兼容性**: 旧版浏览器可能不支持

## 5. 协议详解

### 5.1 握手过程

WebSocket 握手基于 HTTP Upgrade 机制：

```
客户端请求：
GET /chat HTTP/1.1
Host: server.example.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13

服务器响应：
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

### 5.2 帧格式

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-------+-+-------------+-------------------------------+
|F|R|R|R| opcode|M| Payload len |    Extended payload length    |
|I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
|N|V|V|V|       |S|             |   (if payload len==126/127)   |
| |1|2|3|       |K|             |                               |
+-+-+-+-+-------+-+-------------+ - - - - - - - - - - - - - - - +
|     Extended payload length continued, if payload len == 127  |
+ - - - - - - - - - - - - - - - +-------------------------------+
|                               |Masking-key, if MASK set to 1  |
+-------------------------------+-------------------------------+
| Masking-key (continued)       |          Payload Data         |
+-------------------------------- - - - - - - - - - - - - - - - +
```

### 5.3 操作码

| 操作码 | 含义 |
|--------|------|
| 0x0 | 继续帧 |
| 0x1 | 文本帧 |
| 0x2 | 二进制帧 |
| 0x8 | 关闭帧 |
| 0x9 | Ping 帧 |
| 0xA | Pong 帧 |

### 5.4 关闭状态码

| 状态码 | 含义 |
|--------|------|
| 1000 | 正常关闭 |
| 1001 | 端点正在离开 |
| 1002 | 协议错误 |
| 1003 | 接收到不可接受的数据类型 |
| 1007 | 消息内容与类型不一致 |
| 1008 | 策略违规 |
| 1009 | 消息过大 |
| 1011 | 服务器遇到意外情况 |

## 6. 安全考虑

### 6.1 WSS (WebSocket Secure)

- 使用 TLS 加密传输
- 默认端口 443
- 防止中间人攻击

### 6.2 认证授权

- 握手阶段认证
- Token 认证
- Cookie 认证

### 6.3 输入验证

- 消息大小限制
- 消息格式验证
- UTF-8 编码验证

### 6.4 速率限制

- 连接频率限制
- 消息频率限制
- 防止 DoS 攻击

## 7. 性能优化

### 7.1 连接管理

- 连接池复用
- 心跳检测
- 自动重连

### 7.2 消息优化

- 消息压缩 (permessage-deflate)
- 二进制协议
- 消息批处理

### 7.3 服务器优化

- 异步 I/O (epoll/kqueue)
- 多线程处理
- 负载均衡

## 8. 学习资源

### 8.1 规范文档

- [RFC 6455 - The WebSocket Protocol](https://tools.ietf.org/html/rfc6455)
- [RFC 7692 - Compression Extensions for WebSocket](https://tools.ietf.org/html/rfc7692)
- [RFC 8441 - Bootstrapping WebSockets with HTTP/2](https://tools.ietf.org/html/rfc8441)

### 8.2 开源实现

- [libwebsockets](https://github.com/warmcat/libwebsockets) - C 语言实现
- [Boost.Beast](https://github.com/boostorg/beast) - C++ 实现
- [ws](https://github.com/websockets/ws) - Node.js 实现
- [gorilla/websocket](https://github.com/gorilla/websocket) - Go 实现

### 8.3 学习教程

- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [WebSocket Tutorial](https://websocket.org/)
- [HTML5 Rocks WebSocket Tutorial](https://www.html5rocks.com/en/tutorials/websockets/basics/)

# WebSocket 服务器

## 项目简介

一个完整的 C++17 WebSocket 服务器实现，涵盖 WebSocket 协议的核心技术，包括协议实现、连接管理、房间系统、消息路由、安全特性和性能优化。

### 核心功能

- **WebSocket 协议**: 完整的 RFC 6455 实现
- **连接管理**: 高效的连接生命周期管理
- **房间系统**: 灵活的房间管理
- **消息路由**: 可扩展的消息路由系统
- **安全特性**: 认证、限流、输入验证
- **性能优化**: epoll 异步 I/O

## 快速开始

### 编译

```bash
# 进入项目目录
cd projects/websocket-server

# 创建构建目录
mkdir build && cd build

# 配置和编译
cmake ..
make -j$(nproc)
```

### 运行

```bash
# 运行主程序
./websocket_server --port 8080

# 运行聊天服务器示例
./chat_server --port 8081
```

### 测试

```bash
# 运行单元测试
./test_frame
./test_connection
./test_room
./test_router
```

## 技术分类

### 1. WebSocket 协议

| 功能 | 文件 | 说明 |
|------|------|------|
| 握手处理 | connection.cpp | HTTP Upgrade 握手 |
| 帧格式 | frame.cpp | 帧编解码 |
| 掩码处理 | frame.cpp | 掩码应用/移除 |
| 关闭握手 | connection.cpp | 关闭帧处理 |
| Ping/Pong | frame.cpp | 心跳检测 |

### 2. 连接管理

| 功能 | 文件 | 说明 |
|------|------|------|
| 连接建立 | server.cpp | TCP 连接接受 |
| 连接维护 | connection.cpp | 状态管理 |
| 连接关闭 | connection.cpp | 资源清理 |
| 心跳检测 | server.cpp | Ping/Pong 超时 |

### 3. 房间系统

| 功能 | 文件 | 说明 |
|------|------|------|
| 房间创建 | room.cpp | 房间管理 |
| 房间加入 | room.cpp | 成员管理 |
| 房间离开 | room.cpp | 成员移除 |
| 房间广播 | room.cpp | 消息广播 |

### 4. 消息路由

| 功能 | 文件 | 说明 |
|------|------|------|
| 消息解析 | router.cpp | JSON 解析 |
| 消息路由 | router.cpp | 路径/动作路由 |
| 消息处理 | router.cpp | 处理器调用 |
| 中间件 | router.cpp | 处理链 |

### 5. 安全特性

| 功能 | 文件 | 说明 |
|------|------|------|
| 认证授权 | security.cpp | Token 认证 |
| 速率限制 | security.cpp | 请求限流 |
| 输入验证 | security.cpp | 消息验证 |

## 学习路径

### 初级：理解协议

1. 阅读 `docs/01_RESEARCH.md` 了解 WebSocket 协议
2. 阅读 `include/websocket/common.h` 了解数据结构
3. 阅读 `src/frame.cpp` 了解帧编解码

### 中级：掌握实现

1. 阅读 `src/connection.cpp` 了解连接管理
2. 阅读 `src/server.cpp` 了解服务器核心
3. 阅读 `src/room.cpp` 了解房间系统

### 高级：应用实践

1. 阅读 `examples/` 目录下的示例程序
2. 运行测试程序验证功能
3. 修改代码实验新功能

## 编译运行

### 环境要求

- C++17 编译器 (GCC 7+, Clang 5+)
- CMake 3.14+
- Linux/macOS

### 编译选项

```bash
# Debug 模式
cmake -DCMAKE_BUILD_TYPE=Debug ..

# Release 模式
cmake -DCMAKE_BUILD_TYPE=Release ..
```

### 运行示例

```bash
# 聊天服务器
./chat_server --port 8080

# 通知服务器
./notification_server --port 8081

# 游戏服务器
./game_server --port 8082

# 协同编辑器
./collaborative_editor --port 8083
```

### 客户端测试

使用浏览器控制台：

```javascript
const ws = new WebSocket('ws://localhost:8080');
ws.onopen = () => ws.send('{"action":"message","path":"chat","data":"Hello!"}');
ws.onmessage = (e) => console.log(e.data);
```

## 项目结构

```
websocket-server/
├── CMakeLists.txt              # 构建配置
├── README.md                   # 项目文档
├── include/                    # 头文件
│   └── websocket/
│       ├── common.h           # 公共类型
│       ├── frame.h            # 帧编解码
│       ├── connection.h       # 连接管理
│       ├── server.h           # 服务器核心
│       ├── room.h             # 房间系统
│       ├── router.h           # 消息路由
│       └── security.h         # 安全管理
├── src/                        # 源文件
│   ├── common.cpp
│   ├── frame.cpp
│   ├── connection.cpp
│   ├── server.cpp
│   ├── room.cpp
│   ├── router.cpp
│   ├── security.cpp
│   └── main.cpp
├── examples/                   # 示例程序
│   ├── chat_server.cpp
│   ├── notification_server.cpp
│   ├── game_server.cpp
│   └── collaborative_editor.cpp
├── tests/                      # 测试程序
│   ├── test_frame.cpp
│   ├── test_connection.cpp
│   ├── test_room.cpp
│   └── test_router.cpp
└── docs/                       # 文档
    ├── 01_RESEARCH.md
    ├── 02_REQUIREMENTS.md
    ├── 03_DESIGN.md
    ├── 04_PRODUCT.md
    └── 05_DEVELOPMENT.md
```

## API 参考

### Server

```cpp
class Server {
    bool start();
    void stop();
    void run();
    void poll(int timeout_ms);

    void set_on_open(callback);
    void set_on_message(callback);
    void set_on_close(callback);

    void broadcast_text(const std::string& text);
    RoomManager& room_manager();
    Router& router();
    SecurityManager& security();
};
```

### Connection

```cpp
class Connection {
    uint64_t id() const;
    ConnectionState state() const;

    void send_text(const std::string& text);
    void send_binary(const std::vector<uint8_t>& data);
    void close(CloseCode code, const std::string& reason);

    void join_room(const std::string& room_name);
    void leave_room(const std::string& room_name);
};
```

### RoomManager

```cpp
class RoomManager {
    std::shared_ptr<Room> create_room(const std::string& name);
    void join_room(ConnectionPtr conn, const std::string& room_name);
    void leave_room(ConnectionPtr conn, const std::string& room_name);
    void broadcast_to_room(const std::string& room_name, const std::string& text);
};
```

### Router

```cpp
class Router {
    void on(const std::string& path, MessageHandler handler);
    void on(const std::string& path, const std::string& action, MessageHandler handler);
    void use(Middleware middleware);
};
```

## 学习资源

### 规范文档

- [RFC 6455 - The WebSocket Protocol](https://tools.ietf.org/html/rfc6455)
- [RFC 7692 - Compression Extensions](https://tools.ietf.org/html/rfc7692)

### 开源实现

- [libwebsockets](https://github.com/warmcat/libwebsockets)
- [Boost.Beast](https://github.com/boostorg/beast)

### 学习教程

- [MDN WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [WebSocket.org](https://websocket.org/)

## 许可证

MIT License

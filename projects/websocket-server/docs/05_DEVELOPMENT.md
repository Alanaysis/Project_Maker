# WebSocket 服务器开发手册

## 1. 环境要求

### 1.1 编译器

- GCC 7+ (支持 C++17)
- Clang 5+ (支持 C++17)
- MSVC 2017+ (支持 C++17)

### 1.2 构建工具

- CMake 3.14+

### 1.3 操作系统

- Linux (推荐)
- macOS
- Windows (WSL)

## 2. 编译说明

### 2.1 快速编译

```bash
# 进入项目目录
cd projects/websocket-server

# 创建构建目录
mkdir build && cd build

# 配置
cmake ..

# 编译
make -j$(nproc)
```

### 2.2 编译选项

```bash
# Debug 模式
cmake -DCMAKE_BUILD_TYPE=Debug ..

# Release 模式
cmake -DCMAKE_BUILD_TYPE=Release ..

# 指定安装路径
cmake -DCMAKE_INSTALL_PREFIX=/usr/local ..
```

### 2.3 编译单个目标

```bash
# 编译主程序
make websocket_server

# 编译示例
make chat_server
make notification_server
make game_server
make collaborative_editor

# 编译测试
make test_frame
make test_connection
make test_room
make test_router
```

## 3. 运行方式

### 3.1 运行主程序

```bash
# 默认配置
./websocket_server

# 指定端口
./websocket_server --port 9090

# 指定地址
./websocket_server --host 127.0.0.1 --port 8080

# 查看帮助
./websocket_server --help
```

### 3.2 运行示例程序

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

### 3.3 运行测试

```bash
# 运行帧测试
./test_frame

# 运行连接测试
./test_connection

# 运行房间测试
./test_room

# 运行路由测试
./test_router
```

## 4. 测试验证

### 4.1 使用浏览器控制台

```javascript
// 连接服务器
const ws = new WebSocket('ws://localhost:8080');

// 连接成功
ws.onopen = () => {
    console.log('Connected');
    ws.send(JSON.stringify({
        action: 'message',
        path: 'chat',
        data: 'Hello!'
    }));
};

// 接收消息
ws.onmessage = (event) => {
    console.log('Received:', event.data);
};

// 连接关闭
ws.onclose = () => {
    console.log('Disconnected');
};
```

### 4.2 使用 websocat 工具

```bash
# 安装 websocat
cargo install websocat

# 连接服务器
websocat ws://localhost:8080

# 发送消息
{"action":"message","path":"chat","data":"Hello!"}
```

### 4.3 使用 Python 测试

```python
import asyncio
import websockets

async def test():
    async with websockets.connect('ws://localhost:8080') as ws:
        # 发送消息
        await ws.send('{"action":"message","path":"chat","data":"Hello!"}')

        # 接收消息
        response = await ws.recv()
        print(f"Received: {response}")

asyncio.run(test())
```

## 5. 调试技巧

### 5.1 启用详细日志

```cpp
// 在 main.cpp 中添加日志
#define DEBUG_LOG(msg) std::cout << "[DEBUG] " << msg << std::endl
```

### 5.2 使用 GDB 调试

```bash
# 编译 Debug 版本
cmake -DCMAKE_BUILD_TYPE=Debug ..
make

# 使用 GDB
gdb ./websocket_server
(gdb) break main
(gdb) run
(gdb) next
(gdb) print variable
```

### 5.3 使用 Valgrind 检测内存泄漏

```bash
valgrind --leak-check=full ./websocket_server
```

### 5.4 使用 strace 跟踪系统调用

```bash
strace -f -e trace=network ./websocket_server
```

## 6. 项目结构详解

### 6.1 头文件 (include/websocket/)

| 文件 | 说明 |
|------|------|
| common.h | 公共类型、枚举、工具函数 |
| frame.h | 帧编解码器接口 |
| connection.h | 连接管理接口 |
| server.h | 服务器核心接口 |
| room.h | 房间系统接口 |
| router.h | 消息路由接口 |
| security.h | 安全管理接口 |

### 6.2 源文件 (src/)

| 文件 | 说明 |
|------|------|
| common.cpp | Base64、SHA-1、URI 解析实现 |
| frame.cpp | 帧编解码实现 |
| connection.cpp | 连接生命周期管理实现 |
| server.cpp | 服务器核心逻辑实现 |
| room.cpp | 房间系统实现 |
| router.cpp | 消息路由实现 |
| security.cpp | 安全管理实现 |
| main.cpp | 主程序入口 |

### 6.3 示例文件 (examples/)

| 文件 | 说明 |
|------|------|
| chat_server.cpp | 聊天服务器示例 |
| notification_server.cpp | 通知服务器示例 |
| game_server.cpp | 游戏服务器示例 |
| collaborative_editor.cpp | 协同编辑器示例 |

### 6.4 测试文件 (tests/)

| 文件 | 说明 |
|------|------|
| test_frame.cpp | 帧编解码测试 |
| test_connection.cpp | 连接功能测试 |
| test_room.cpp | 房间系统测试 |
| test_router.cpp | 路由系统测试 |

## 7. 常见问题

### 7.1 编译错误

**问题**: 找不到头文件
```
fatal error: websocket/server.h: No such file or directory
```

**解决**: 确保 include 路径正确
```bash
cmake -I../include ..
```

### 7.2 运行错误

**问题**: 端口被占用
```
Failed to bind: Address already in use
```

**解决**: 使用其他端口或关闭占用端口的程序
```bash
# 查看端口占用
lsof -i :8080

# 使用其他端口
./websocket_server --port 9090
```

### 7.3 连接问题

**问题**: 无法连接服务器

**解决**:
1. 检查服务器是否启动
2. 检查防火墙设置
3. 检查地址和端口是否正确

## 8. 扩展开发

### 8.1 添加新的消息类型

```cpp
// 在 Router 中注册新的处理器
router.on("game", "shoot", [](const RouteContext& ctx) {
    auto x = SimpleJson::get(ctx.message.text(), "x");
    auto y = SimpleJson::get(ctx.message.text(), "y");
    // 处理射击逻辑
});
```

### 8.2 添加新的认证方式

```cpp
class JWTAuthenticator : public Authenticator {
public:
    AuthResult authenticate(ConnectionPtr conn, const std::string& token) override {
        // 验证 JWT Token
        // ...
    }
};
```

### 8.3 添加中间件

```cpp
// 日志中间件
router.use([](RouteContext& ctx) -> bool {
    std::cout << "Received: " << ctx.message.text() << std::endl;
    return true;
});

// 认证中间件
router.use([&security](RouteContext& ctx) -> bool {
    return security.validate_connection(ctx.connection);
});
```

## 9. 性能调优

### 9.1 调整 epoll 参数

```cpp
// 增加最大事件数
static constexpr int MAX_EVENTS = 4096;

// 调整超时时间
int timeout_ms = 50;  // 50ms
```

### 9.2 调整缓冲区大小

```cpp
// 增加读缓冲区
static constexpr size_t READ_BUFFER_SIZE = 131072;  // 128KB
```

### 9.3 调整心跳参数

```cpp
config.heartbeat_interval_ms = 15000;  // 15秒
config.heartbeat_timeout_ms = 45000;   // 45秒
```

## 10. 部署建议

### 10.1 使用 systemd 管理服务

```ini
[Unit]
Description=WebSocket Server
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/websocket_server --port 8080
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 10.2 使用 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name example.com;

    location /ws {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### 10.3 使用 Docker 部署

```dockerfile
FROM ubuntu:20.04

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake

COPY . /app
WORKDIR /app

RUN mkdir build && cd build && cmake .. && make

EXPOSE 8080

CMD ["./build/websocket_server", "--port", "8080"]
```

## 11. 学习资源

### 11.1 官方文档

- [RFC 6455 - The WebSocket Protocol](https://tools.ietf.org/html/rfc6455)
- [MDN WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)

### 11.2 开源项目

- [libwebsockets](https://github.com/warmcat/libwebsockets)
- [Boost.Beast](https://github.com/boostorg/beast)
- [Crow](https://github.com/CrowCpp/Crow)

### 11.3 学习教程

- [WebSocket Tutorial](https://websocket.org/)
- [Beej's Guide to Network Programming](https://beej.us/guide/bgnet/)

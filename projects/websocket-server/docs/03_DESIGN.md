# WebSocket 服务器技术设计

## 1. 架构概述

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      WebSocket Server                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │  Frame   │  │Connection│  │  Room   │  │ Router  │       │
│  │  Codec   │  │ Manager  │  │ Manager │  │         │       │
│  └────┬─────┘  └────┬─────┘  └────┬────┘  └────┬────┘       │
│       │             │             │             │            │
│  ┌────┴─────────────┴─────────────┴─────────────┴────┐      │
│  │                    Server Core                     │      │
│  └────┬─────────────┬─────────────┬─────────────┬────┘      │
│       │             │             │             │            │
│  ┌────┴────┐  ┌─────┴─────┐ ┌────┴────┐  ┌────┴────┐      │
│  │  epoll  │  │  Security │ │  Timer  │  │  Utils  │      │
│  │  I/O    │  │  Manager  │ │         │  │         │      │
│  └─────────┘  └───────────┘ └─────────┘  └─────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 组件职责

| 组件 | 职责 |
|------|------|
| Server | 服务器核心，管理生命周期和事件循环 |
| FrameCodec | WebSocket 帧的编解码 |
| Connection | 单个连接的管理 |
| RoomManager | 房间系统的管理 |
| Router | 消息路由和分发 |
| SecurityManager | 安全策略管理 |

## 2. 文件组织

### 2.1 目录结构

```
websocket-server/
├── CMakeLists.txt              # 构建配置
├── README.md                   # 项目文档
├── include/                    # 头文件
│   └── websocket/
│       ├── common.h           # 公共类型和工具
│       ├── frame.h            # 帧编解码器
│       ├── connection.h       # 连接管理
│       ├── server.h           # 服务器核心
│       ├── room.h             # 房间系统
│       ├── router.h           # 消息路由
│       └── security.h         # 安全管理
├── src/                        # 源文件
│   ├── common.cpp             # 公共工具实现
│   ├── frame.cpp              # 帧编解码实现
│   ├── connection.cpp         # 连接管理实现
│   ├── server.cpp             # 服务器实现
│   ├── room.cpp               # 房间系统实现
│   ├── router.cpp             # 路由系统实现
│   ├── security.cpp           # 安全管理实现
│   └── main.cpp               # 主程序入口
├── examples/                   # 示例程序
│   ├── chat_server.cpp        # 聊天服务器
│   ├── notification_server.cpp # 通知服务器
│   ├── game_server.cpp        # 游戏服务器
│   └── collaborative_editor.cpp # 协同编辑器
├── tests/                      # 测试程序
│   ├── test_frame.cpp         # 帧测试
│   ├── test_connection.cpp    # 连接测试
│   ├── test_room.cpp          # 房间测试
│   └── test_router.cpp        # 路由测试
└── docs/                       # 文档
    ├── 01_RESEARCH.md         # 技术调研
    ├── 02_REQUIREMENTS.md     # 需求分析
    ├── 03_DESIGN.md           # 技术设计
    ├── 04_PRODUCT.md          # 产品思考
    └── 05_DEVELOPMENT.md      # 开发手册
```

### 2.2 头文件依赖

```
common.h
    ├── frame.h
    │   └── connection.h
    │       └── server.h
    ├── room.h
    ├── router.h
    └── security.h
```

## 3. 核心设计

### 3.1 帧编解码器 (FrameCodec)

#### 设计原则

- **无状态**: 帧编解码器不保存状态，每次调用都是独立的
- **零拷贝**: 尽量减少数据拷贝
- **高效**: 使用位操作进行快速编解码

#### 接口设计

```cpp
class FrameCodec {
public:
    // 编码接口
    static std::vector<uint8_t> encode_text(const std::string& text, bool masked = false);
    static std::vector<uint8_t> encode_binary(const std::vector<uint8_t>& data, bool masked = false);
    static std::vector<uint8_t> create_ping(const std::vector<uint8_t>& payload = {});
    static std::vector<uint8_t> create_pong(const std::vector<uint8_t>& payload = {});
    static std::vector<uint8_t> create_close_frame(CloseCode code, const std::string& reason = "");

    // 解码接口
    static std::optional<Frame> decode_frame(const uint8_t* data, size_t length, size_t& bytes_consumed);
};
```

#### 帧头序列化

```cpp
std::vector<uint8_t> serialize_header(const FrameHeader& header, uint64_t payload_length) {
    std::vector<uint8_t> header_bytes;

    // 第一个字节: FIN + RSV + Opcode
    uint8_t byte1 = 0;
    if (header.fin)  byte1 |= 0x80;
    if (header.rsv1) byte1 |= 0x40;
    if (header.rsv2) byte1 |= 0x20;
    if (header.rsv3) byte1 |= 0x10;
    byte1 |= static_cast<uint8_t>(header.opcode) & 0x0F;
    header_bytes.push_back(byte1);

    // 第二个字节: MASK + Payload Length
    // ...
}
```

### 3.2 连接管理 (Connection)

#### 连接生命周期

```
Connecting ──→ Open ──→ Closing ──→ Closed
    │            │          │
    └────────────┴──────────┘
         (异常关闭)
```

#### 状态管理

```cpp
enum class ConnectionState {
    Connecting,    // 等待握手
    Open,          // 连接已建立
    Closing,       // 正在关闭
    Closed,        // 已关闭
};
```

#### 缓冲区设计

- **读缓冲区**: 接收网络数据，解析帧
- **写缓冲区**: 缓存待发送数据
- **线程安全**: 使用 mutex 保护写缓冲区

### 3.3 服务器核心 (Server)

#### 事件循环

```cpp
void Server::poll(int timeout_ms) {
    int nfds = epoll_wait(epoll_fd_, events_, MAX_EVENTS, timeout_ms);

    for (int i = 0; i < nfds; ++i) {
        if (events_[i].data.fd == listen_fd_) {
            accept_connection();
        } else {
            handle_connection_event(events_[i]);
        }
    }

    check_heartbeat();
}
```

#### 连接管理

- 使用 `unordered_map<uint64_t, ConnectionPtr>` 存储连接
- 使用 `unordered_map<int, uint64_t>` 映射 fd 到连接 ID
- 使用 mutex 保护连接表

### 3.4 房间系统 (Room)

#### 房间结构

```cpp
class Room {
    std::string name_;
    std::unordered_map<uint64_t, ConnectionPtr> members_;
    std::unordered_map<std::string, std::string> properties_;
};
```

#### 房间管理器

```cpp
class RoomManager {
    std::unordered_map<std::string, std::shared_ptr<Room>> rooms_;

    void join_room(ConnectionPtr conn, const std::string& room_name);
    void leave_room(ConnectionPtr conn, const std::string& room_name);
    void broadcast_to_room(const std::string& room_name, const std::string& text);
};
```

### 3.5 消息路由 (Router)

#### 路由表结构

```cpp
class Router {
    // 路径路由: path -> handler
    std::unordered_map<std::string, MessageHandler> routes_;

    // 动作路由: path/action -> handler
    std::unordered_map<std::string,
        std::unordered_map<std::string, MessageHandler>> action_routes_;

    // 中间件链
    std::vector<Middleware> middlewares_;
};
```

#### 消息解析

```cpp
// 默认消息格式: {"path": "xxx", "action": "xxx", ...}
auto [path, action] = parse_message(msg);

// 匹配路由
if (action_routes_[path].count(action)) {
    action_routes_[path][action](ctx);
} else if (routes_.count(path)) {
    routes_[path](ctx);
} else if (default_handler_) {
    default_handler_(ctx);
}
```

### 3.6 安全管理 (Security)

#### 认证流程

```
客户端 ──→ 连接建立 ──→ 发送 Token ──→ 验证 Token ──→ 允许/拒绝
                              │
                              ↓
                      SecurityManager::validate_connection()
```

#### 速率限制算法

```cpp
bool RateLimiter::allow(const std::string& client_id) {
    auto& info = clients_[client_id];

    if (now - info.window_start > window_ms_) {
        // 重置窗口
        info.request_count = 1;
        info.window_start = now;
        return true;
    }

    if (info.request_count >= max_requests_) {
        return false;
    }

    info.request_count++;
    return true;
}
```

## 4. 数据流

### 4.1 接收消息流程

```
网络数据 ──→ 读缓冲区 ──→ 帧解析 ──→ 帧处理 ──→ 消息组装 ──→ 路由分发
                              │
                              ↓
                         掩码解码
```

### 4.2 发送消息流程

```
消息 ──→ 帧编码 ──→ 写缓冲区 ──→ 网络发送
                │
                ↓
           序列化帧头 + 载荷
```

### 4.3 握手流程

```
客户端请求 ──→ 解析 HTTP ──→ 提取 Key ──→ 计算 Accept ──→ 发送响应
                                      │
                                      ↓
                              SHA-1(Key + Magic) → Base64
```

## 5. 线程模型

### 5.1 主线程

- 运行事件循环
- 处理网络 I/O
- 处理连接事件

### 5.2 工作线程（可选）

- 消息处理
- 业务逻辑
- 定时任务

### 5.3 线程安全

- 连接表: mutex 保护
- 写缓冲区: mutex 保护
- 房间系统: mutex 保护
- 路由表: 只读（初始化后）

## 6. 错误处理

### 6.1 网络错误

- 连接断开: 清理资源
- 读写错误: 关闭连接
- 超时: 心跳检测

### 6.2 协议错误

- 帧格式错误: 发送关闭帧
- 掩码错误: 关闭连接
- 消息过大: 拒绝消息

### 6.3 业务错误

- 认证失败: 拒绝连接
- 速率限制: 拒绝请求
- 输入验证: 拒绝消息

## 7. 性能优化

### 7.1 I/O 优化

- epoll 边缘触发
- 非阻塞 I/O
- 批量事件处理

### 7.2 内存优化

- 缓冲区复用
- 避免不必要的拷贝
- 使用移动语义

### 7.3 锁优化

- 细粒度锁
- 读写锁
- 无锁数据结构（原子操作）

## 8. 扩展性设计

### 8.1 插件式架构

- 认证器接口
- 中间件接口
- 消息解析器接口

### 8.2 配置化

- 服务器配置
- 安全策略配置
- 路由配置

### 8.3 监控接口

- 连接统计
- 消息统计
- 性能指标

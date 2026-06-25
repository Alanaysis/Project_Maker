# WebSocket 服务器需求分析

## 1. 项目概述

### 1.1 项目目标

构建一个完整的 WebSocket 服务器实现，涵盖 WebSocket 协议的核心技术，包括协议实现、连接管理、房间系统、消息路由、安全特性和性能优化。

### 1.2 技术栈

- **语言**: C++17/20
- **构建系统**: CMake 3.14+
- **网络**: POSIX Sockets + epoll
- **并发**: std::thread, std::mutex
- **测试**: 自定义测试框架

## 2. 功能需求

### 2.1 WebSocket 协议实现

#### 2.1.1 握手过程

- [x] HTTP Upgrade 请求解析
- [x] Sec-WebSocket-Key 验证
- [x] Sec-WebSocket-Accept 计算
- [x] 握手响应生成
- [x] 协议版本检查

#### 2.1.2 帧格式

- [x] 帧头解析（FIN, RSV, Opcode, MASK, Payload Length）
- [x] 扩展长度支持（16位、64位）
- [x] 掩码处理（应用/移除掩码）
- [x] 帧序列化
- [x] 帧反序列化

#### 2.1.3 消息类型

- [x] 文本消息（Opcode 0x1）
- [x] 二进制消息（Opcode 0x2）
- [x] 分片消息（Continuation Frame）
- [x] 关闭帧（Opcode 0x8）
- [x] Ping 帧（Opcode 0x9）
- [x] Pong 帧（Opcode 0xA）

#### 2.1.4 掩码处理

- [x] 客户端发送的帧必须掩码
- [x] 服务器发送的帧不能掩码
- [x] 掩码算法：payload[i] ^= mask[i % 4]

#### 2.1.5 关闭握手

- [x] 关闭帧发送
- [x] 关闭帧接收
- [x] 关闭状态码处理
- [x] 关闭原因处理

### 2.2 连接管理

#### 2.2.1 连接建立

- [x] TCP 监听
- [x] 连接接受
- [x] 非阻塞 I/O 设置
- [x] 连接 ID 分配

#### 2.2.2 连接维护

- [x] 连接状态管理
- [x] 活动时间记录
- [x] 连接属性存储

#### 2.2.3 连接关闭

- [x] 主动关闭
- [x] 被动关闭
- [x] 异常关闭处理
- [x] 资源清理

#### 2.2.4 心跳检测

- [x] 定时 Ping 发送
- [x] Pong 响应处理
- [x] 超时检测
- [x] 超时关闭

### 2.3 房间系统

#### 2.3.1 房间管理

- [x] 房间创建
- [x] 房间销毁
- [x] 房间查找
- [x] 房间列表

#### 2.3.2 成员管理

- [x] 成员加入
- [x] 成员离开
- [x] 成员列表
- [x] 成员数量

#### 2.3.3 房间广播

- [x] 文本消息广播
- [x] 二进制消息广播
- [x] 排除发送者广播
- [x] 房间属性管理

### 2.4 消息路由

#### 2.4.1 消息解析

- [x] JSON 消息解析
- [x] 路径提取
- [x] 动作提取
- [x] 参数提取

#### 2.4.2 路由注册

- [x] 基于路径的路由
- [x] 基于动作的路由
- [x] 默认路由
- [x] 路由优先级

#### 2.4.3 中间件

- [x] 中间件注册
- [x] 中间件执行链
- [x] 中间件中断
- [x] 上下文传递

### 2.5 安全特性

#### 2.5.1 认证授权

- [x] Token 认证器接口
- [x] 简单 Token 认证器实现
- [x] 用户数据存储
- [x] 认证状态管理

#### 2.5.2 速率限制

- [x] 令牌桶算法
- [x] 时间窗口限制
- [x] 客户端标识
- [x] 配额查询

#### 2.5.3 输入验证

- [x] 消息大小限制
- [x] 字符串长度限制
- [x] UTF-8 编码验证
- [x] 二进制数据验证

### 2.6 性能优化

#### 2.6.1 异步 I/O

- [x] epoll 事件驱动
- [x] 非阻塞套接字
- [x] 边缘触发模式
- [x] 事件批量处理

#### 2.6.2 多线程支持

- [x] 线程安全的数据结构
- [x] 锁粒度优化
- [x] 原子操作

#### 2.6.3 缓冲区管理

- [x] 读缓冲区
- [x] 写缓冲区
- [x] 缓冲区复用

## 3. 非功能需求

### 3.1 性能要求

- 支持 1000+ 并发连接
- 消息延迟 < 10ms
- 吞吐量 > 10000 msg/s

### 3.2 可靠性要求

- 连接断开自动清理
- 异常情况优雅处理
- 资源泄漏防护

### 3.3 可扩展性

- 模块化设计
- 接口抽象
- 插件式架构

### 3.4 可维护性

- 清晰的代码结构
- 详细的注释文档
- 完整的单元测试

## 4. 技术清单

### 4.1 核心组件

| 组件 | 功能 | 文件 |
|------|------|------|
| FrameCodec | 帧编解码 | frame.h/cpp |
| Connection | 连接管理 | connection.h/cpp |
| Server | 服务器核心 | server.h/cpp |
| Room | 房间管理 | room.h/cpp |
| Router | 消息路由 | router.h/cpp |
| Security | 安全管理 | security.h/cpp |

### 4.2 数据结构

| 结构 | 用途 | 文件 |
|------|------|------|
| FrameHeader | 帧头信息 | common.h |
| Frame | 完整帧 | common.h |
| Message | 消息对象 | common.h |
| WebSocketURI | URI 解析 | common.h |

### 4.3 工具函数

| 函数 | 功能 | 文件 |
|------|------|------|
| base64_encode | Base64 编码 | common.h/cpp |
| sha1 | SHA-1 哈希 | common.h/cpp |
| apply_mask | 掩码应用 | common.h |
| random_bytes | 随机字节 | common.h |

### 4.4 依赖项

| 依赖 | 版本 | 用途 |
|------|------|------|
| CMake | 3.14+ | 构建系统 |
| POSIX | - | 网络 API |
| C++ Standard Library | C++17 | 标准库 |

## 5. 接口设计

### 5.1 服务器接口

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

### 5.2 连接接口

```cpp
class Connection {
    uint64_t id() const;
    ConnectionState state() const;

    void send_text(const std::string& text);
    void send_binary(const std::vector<uint8_t>& data);
    void send_ping();
    void close(CloseCode code, const std::string& reason);

    void join_room(const std::string& room_name);
    void leave_room(const std::string& room_name);
};
```

### 5.3 房间接口

```cpp
class RoomManager {
    std::shared_ptr<Room> create_room(const std::string& name);
    bool destroy_room(const std::string& name);
    std::shared_ptr<Room> get_room(const std::string& name);

    void join_room(ConnectionPtr conn, const std::string& room_name);
    void leave_room(ConnectionPtr conn, const std::string& room_name);
    void broadcast_to_room(const std::string& room_name, const std::string& text);
};
```

### 5.4 路由接口

```cpp
class Router {
    void on(const std::string& path, MessageHandler handler);
    void on(const std::string& path, const std::string& action, MessageHandler handler);
    void use(Middleware middleware);
    void set_default_handler(MessageHandler handler);
};
```

## 6. 测试需求

### 6.1 单元测试

- [x] 帧编解码测试
- [x] 掩码处理测试
- [x] SHA-1 哈希测试
- [x] Base64 编码测试
- [x] JSON 解析测试

### 6.2 集成测试

- [x] 服务器启动/停止测试
- [x] 连接回调测试
- [x] 房间系统测试
- [x] 路由系统测试

### 6.3 示例程序

- [x] 聊天服务器
- [x] 通知服务器
- [x] 游戏服务器
- [x] 协同编辑器

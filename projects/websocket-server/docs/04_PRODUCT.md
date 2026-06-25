# WebSocket 服务器产品思考

## 1. 学习目标

### 1.1 核心知识

通过本项目，深入理解以下技术：

1. **WebSocket 协议**
   - 握手过程
   - 帧格式
   - 掩码处理
   - 关闭握手
   - Ping/Pong 心跳

2. **网络编程**
   - TCP 套接字编程
   - 非阻塞 I/O
   - epoll 事件驱动
   - 缓冲区管理

3. **并发编程**
   - 多线程同步
   - 线程安全数据结构
   - 锁的使用和优化

4. **协议设计**
   - 二进制协议设计
   - 消息格式设计
   - 错误处理

### 1.2 实践技能

1. **系统设计**
   - 模块化设计
   - 接口抽象
   - 可扩展架构

2. **代码质量**
   - 清晰的代码结构
   - 详细的注释
   - 完整的测试

3. **工程实践**
   - CMake 构建系统
   - 版本控制
   - 文档编写

## 2. 关键要点

### 2.1 WebSocket 协议要点

#### 握手过程

```
客户端：
GET /chat HTTP/1.1
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==

服务器：
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

**关键点**:
- Sec-WebSocket-Key 是随机的 16 字节 Base64 编码
- Sec-WebSocket-Accept = Base64(SHA1(Key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"))
- 必须验证 Upgrade 和 Connection 头

#### 帧格式

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-------+-+-------------+-------------------------------+
|F|R|R|R| opcode|M| Payload len |    Extended payload length    |
|I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
|N|V|V|V|       |S|             |   (if payload len==126/127)   |
+-+-+-+-+-------+-+-------------+-------------------------------+
```

**关键点**:
- FIN: 是否是最后一帧
- Opcode: 帧类型（文本、二进制、控制帧）
- MASK: 是否使用掩码（客户端必须掩码，服务器不能掩码）
- Payload Length: 7位、16位或64位

#### 掩码处理

```cpp
void apply_mask(uint8_t* data, size_t length, const uint8_t mask[4]) {
    for (size_t i = 0; i < length; ++i) {
        data[i] ^= mask[i % 4];
    }
}
```

**关键点**:
- 掩码密钥是随机的 4 字节
- 掩码是为了防止缓存污染攻击
- 客户端发送的帧必须掩码
- 服务器发送的帧不能掩码

### 2.2 网络编程要点

#### 非阻塞 I/O

```cpp
// 设置非阻塞
int flags = fcntl(fd, F_GETFL, 0);
fcntl(fd, F_SETFL, flags | O_NONBLOCK);
```

**关键点**:
- 非阻塞 I/O 避免线程阻塞
- 配合 epoll 使用效果最佳
- 需要处理 EAGAIN/EWOULDBLOCK

#### epoll 使用

```cpp
// 创建 epoll
int epfd = epoll_create1(0);

// 添加事件
struct epoll_event ev;
ev.events = EPOLLIN | EPOLLET;
ev.data.fd = fd;
epoll_ctl(epfd, EPOLL_CTL_ADD, fd, &ev);

// 等待事件
int nfds = epoll_wait(epfd, events, MAX_EVENTS, timeout);
```

**关键点**:
- 边缘触发 (EPOLLET) 比水平触发更高效
- 边缘触发需要一次性读取所有数据
- 注意事件处理的原子性

#### 缓冲区管理

```cpp
class Connection {
    std::vector<uint8_t> read_buffer_;
    std::vector<uint8_t> write_buffer_;
    std::mutex write_mutex_;
};
```

**关键点**:
- 读缓冲区用于接收数据
- 写缓冲区用于缓存发送数据
- 写缓冲区需要线程安全保护

### 2.3 并发编程要点

#### 线程安全

```cpp
class Room {
    mutable std::mutex mutex_;
    std::unordered_map<uint64_t, ConnectionPtr> members_;

    void broadcast(const std::string& text) {
        std::lock_guard<std::mutex> lock(mutex_);
        for (const auto& [id, conn] : members_) {
            conn->send_text(text);
        }
    }
};
```

**关键点**:
- 使用 mutex 保护共享数据
- 使用 lock_guard 自动管理锁
- 注意锁的粒度，避免死锁

#### 原子操作

```cpp
class Connection {
    static std::atomic<uint64_t> next_id_;
    std::atomic<bool> running_{false};
};
```

**关键点**:
- 原子操作避免锁的开销
- 适用于简单的计数器和标志位
- 注意内存顺序

### 2.4 协议设计要点

#### 消息格式设计

```json
{
    "path": "chat",
    "action": "message",
    "data": {
        "room": "general",
        "content": "Hello!"
    }
}
```

**关键点**:
- 清晰的消息结构
- 支持路由和动作
- 易于扩展

#### 错误处理

```cpp
enum class CloseCode : uint16_t {
    Normal            = 1000,
    GoingAway         = 1001,
    ProtocolError     = 1002,
    // ...
};
```

**关键点**:
- 定义清晰的错误码
- 提供有意义的错误消息
- 优雅地处理错误

## 3. 设计模式应用

### 3.1 观察者模式

用于事件回调：

```cpp
server.set_on_open([](ConnectionPtr conn) {
    // 处理连接打开
});

server.set_on_message([](ConnectionPtr conn, const Message& msg) {
    // 处理消息
});
```

### 3.2 策略模式

用于可替换的组件：

```cpp
// 认证策略
class Authenticator {
    virtual AuthResult authenticate(ConnectionPtr conn, const std::string& token) = 0;
};

class SimpleTokenAuthenticator : public Authenticator {
    // 简单 Token 认证
};
```

### 3.3 中间件模式

用于请求处理链：

```cpp
router.use([](RouteContext& ctx) -> bool {
    // 认证检查
    return true;  // 继续处理
});

router.use([](RouteContext& ctx) -> bool {
    // 日志记录
    return true;
});
```

### 3.4 工厂模式

用于对象创建：

```cpp
auto room = room_manager.create_room("chat");
auto conn = std::make_shared<Connection>(fd, server);
```

## 4. 性能考虑

### 4.1 内存优化

1. **缓冲区复用**: 避免频繁分配和释放
2. **移动语义**: 减少数据拷贝
3. **预留空间**: 预分配缓冲区

### 4.2 CPU 优化

1. **批量处理**: 一次处理多个事件
2. **减少锁竞争**: 细粒度锁
3. **避免不必要的拷贝**: 使用引用和指针

### 4.3 I/O 优化

1. **非阻塞 I/O**: 避免线程阻塞
2. **边缘触发**: 减少事件通知次数
3. **批量发送**: 合并小消息

## 5. 安全考虑

### 5.1 输入验证

- 消息大小限制
- UTF-8 编码验证
- 特殊字符处理

### 5.2 认证授权

- Token 认证
- 连接级别认证
- 消息级别授权

### 5.3 速率限制

- 连接频率限制
- 消息频率限制
- 防止 DoS 攻击

### 5.4 数据保护

- WSS 加密传输
- 敏感数据脱敏
- 日志安全

## 6. 扩展性思考

### 6.1 功能扩展

- WebSocket 压缩扩展
- 二进制协议支持
- 自定义帧类型

### 6.2 性能扩展

- 多线程事件循环
- 连接池
- 消息队列

### 6.3 架构扩展

- 分布式部署
- 负载均衡
- 消息广播

## 7. 学习路径建议

### 7.1 初级阶段

1. 理解 WebSocket 协议
2. 实现基础帧编解码
3. 实现简单服务器

### 7.2 中级阶段

1. 实现完整的连接管理
2. 实现房间系统
3. 实现消息路由

### 7.3 高级阶段

1. 性能优化
2. 安全加固
3. 生产级特性

## 8. 常见问题

### 8.1 为什么需要掩码？

掩码是为了防止缓存污染攻击。当代理服务器缓存 WebSocket 帧时，恶意客户端可能构造特定的帧内容，污染缓存。

### 8.2 为什么使用 epoll？

epoll 是 Linux 下高效的 I/O 多路复用机制，相比 select/poll：
- O(1) 事件通知
- 支持大量连接
- 边缘触发模式

### 8.3 如何处理粘包？

WebSocket 协议本身处理了消息边界：
- 每个帧有明确的长度
- 分片消息通过 FIN 位标识
- 不需要像 TCP 那样处理粘包

### 8.4 如何保证消息顺序？

WebSocket 基于 TCP，TCP 保证数据的顺序性。分片消息按顺序到达，不需要额外的排序。

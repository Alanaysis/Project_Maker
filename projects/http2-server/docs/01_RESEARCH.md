# HTTP/2 技术调研

## 1. HTTP/2 技术历史

### HTTP 协议演进

#### HTTP/0.9（1991年）
- 最早的 HTTP 版本
- 只支持 GET 请求
- 无头部信息
- 响应只能是 HTML

#### HTTP/1.0（1996年）
- 引入状态码
- 支持多种 HTTP 方法
- 引入头部字段
- 支持多种内容类型

#### HTTP/1.1（1997年）
- 持久连接（Keep-Alive）
- 管道化（Pipelining）
- 分块传输编码
- 缓存控制增强

#### HTTP/2（2015年）
- 二进制分帧
- 多路复用
- 头部压缩
- 服务器推送
- 流量控制

#### HTTP/3（2022年）
- 基于 QUIC 协议
- 0-RTT 连接建立
- 改进的拥塞控制
- 连接迁移

### HTTP/2 的起源

HTTP/2 起源于 Google 的 SPDY 协议：

1. **SPDY（2009年）**
   - Google 开发的实验性协议
   - 多路复用
   - 头部压缩
   - 优先级

2. **HTTP/2 标准化（2012-2015年）**
   - IETF 基于 SPDY 制定标准
   - 2015年5月发布 RFC 7540
   - 2015年5月发布 RFC 7541（HPACK）

## 2. HTTP/2 核心技术

### 2.1 二进制分帧

HTTP/2 使用二进制格式而非文本格式：

```
+-----------------------------------------------+
|                 Length (24)                    |
+---------------+---------------+---------------+
|   Type (8)    |   Flags (8)   |
+-+-------------+---------------+---------------+
|R|                 Stream Identifier (31)      |
+=+=============================================+
|                   Frame Payload (0...)        |
+-----------------------------------------------+
```

**帧类型：**
- DATA (0x00)：传输数据
- HEADERS (0x01)：传输头部
- PRIORITY (0x02)：设置优先级
- RST_STREAM (0x03)：终止流
- SETTINGS (0x04)：配置参数
- PUSH_PROMISE (0x05)：服务器推送
- PING (0x06)：心跳检测
- GOAWAY (0x07)：优雅关闭
- WINDOW_UPDATE (0x08)：流量控制
- CONTINUATION (0x09)：续传头部

### 2.2 多路复用

HTTP/2 允许在单个 TCP 连接上并行处理多个请求：

**HTTP/1.1 的问题：**
```
Client → Server: GET /index.html
Client ← Server: Response (blocked)
Client → Server: GET /style.css
Client ← Server: Response (blocked)
```

**HTTP/2 的优势：**
```
Client → Server: Stream 1: GET /index.html
Client → Server: Stream 3: GET /style.css
Client ← Server: Stream 1: Response (interleaved)
Client ← Server: Stream 3: Response (interleaved)
```

### 2.3 头部压缩（HPACK）

HPACK 使用三种编码方式：

1. **索引表示**
   - 使用预定义的静态表
   - 使用动态表（连接期间学习）

2. **字面量表示**
   - 不索引
   - 从不索引
   - 索引的新字段

3. **霍夫曼编码**
   - 变长编码
   - 高频字符用短编码

**静态表示示例：**
```
:method: GET → 索引 2
:path: / → 索引 4
:scheme: http → 索引 6
```

### 2.4 流量控制

HTTP/2 使用基于窗口的流量控制：

1. **连接级别**
   - 初始窗口大小：65,535 字节
   - 通过 SETTINGS 帧更新

2. **流级别**
   - 每个流独立的窗口
   - 通过 WINDOW_UPDATE 帧更新

3. **流量控制过程**
```
Client: WINDOW_UPDATE (stream 1, +1024)
Server: DATA (stream 1, 1024 bytes)
Client: WINDOW_UPDATE (stream 1, +1024)
Server: DATA (stream 1, 1024 bytes)
```

### 2.5 服务器推送

服务器可以主动推送资源：

```
Client: GET /index.html
Server: PUSH_PROMISE (/style.css)
Server: PUSH_PROMISE (/script.js)
Server: DATA (/index.html)
Server: DATA (/style.css)
Server: DATA (/script.js)
```

## 3. HTTP/2 应用场景

### 3.1 Web 应用

**静态资源加载：**
- CSS、JavaScript、图片
- 减少连接数
- 提高加载速度

**API 服务：**
- RESTful API
- GraphQL
- gRPC

### 3.2 微服务架构

**服务间通信：**
- 高性能 RPC
- 流式数据传输
- 双向通信

**API 网关：**
- 请求路由
- 负载均衡
- 认证授权

### 3.3 实时应用

**Server-Sent Events：**
- 实时通知
- 数据流
- 股票行情

**WebSocket：**
- 聊天应用
- 在线游戏
- 协同编辑

### 3.4 CDN 和边缘计算

**内容分发：**
- 静态资源缓存
- 动态内容加速
- 全球负载均衡

## 4. HTTP/2 优缺点

### 4.1 优点

#### 性能提升
- **多路复用**：消除队头阻塞
- **头部压缩**：减少带宽使用
- **二进制协议**：更快的解析

#### 功能增强
- **服务器推送**：预加载资源
- **流优先级**：优化资源加载顺序
- **流量控制**：防止资源耗尽

#### 兼容性
- **向后兼容**：支持 HTTP/1.1
- **透明升级**：客户端自动协商
- **广泛支持**：所有主流浏览器

### 4.2 缺点

#### 实现复杂性
- **协议复杂**：二进制格式难以调试
- **状态管理**：流状态机复杂
- **头部压缩**：需要维护动态表

#### TCP 层面问题
- **队头阻塞**：TCP 层面仍然存在
- **连接重置**：所有流都受影响
- **拥塞控制**：TCP 拥塞控制影响性能

#### 资源消耗
- **内存使用**：流状态和动态表
- **CPU 使用**：头部压缩和解压
- **连接管理**：需要维护长连接

### 4.3 与 HTTP/1.1 对比

| 特性 | HTTP/1.1 | HTTP/2 |
|------|----------|--------|
| 协议格式 | 文本 | 二进制 |
| 多路复用 | 不支持 | 支持 |
| 头部压缩 | 不支持 | 支持（HPACK） |
| 服务器推送 | 不支持 | 支持 |
| 流量控制 | 不支持 | 支持 |
| 连接复用 | 有限 | 完全支持 |

### 4.4 与 HTTP/3 对比

| 特性 | HTTP/2 | HTTP/3 |
|------|--------|--------|
| 传输层 | TCP | QUIC（UDP） |
| 队头阻塞 | TCP 层面存在 | 完全消除 |
| 连接建立 | 1-3 RTT | 0-1 RTT |
| 连接迁移 | 不支持 | 支持 |
| 加密 | 可选 | 强制 |

## 5. HTTP/2 生态系统

### 5.1 浏览器支持

- Chrome 40+（2015年）
- Firefox 36+（2015年）
- Safari 9+（2015年）
- Edge 12+（2015年）

### 5.2 服务器支持

- Nginx 1.9.5+
- Apache 2.4.17+
- IIS 10+
- Node.js 8+
- Go 标准库
- Java 9+

### 5.3 客户端库

- curl 7.43+
- wget 1.18+
- Python requests
- Java HttpClient
- Go net/http

### 5.4 工具

- Wireshark：协议分析
- nghttp2：参考实现
- h2spec：合规性测试
- h2load：性能测试

## 6. HTTP/2 最佳实践

### 6.1 服务器配置

```nginx
# Nginx 配置
server {
    listen 443 ssl http2;
    ssl_certificate server.crt;
    ssl_certificate_key server.key;

    # 启用 HTTP/2
    http2_max_concurrent_streams 100;
    http2_max_field_size 4k;
    http2_max_header_size 16k;
}
```

### 6.2 性能优化

1. **减少域名分片**
   - HTTP/2 多路复用不需要多个连接
   - 合并资源到单个域名

2. **优化头部**
   - 减少不必要的头部
   - 使用简短的头部名称

3. **合理使用服务器推送**
   - 只推送关键资源
   - 避免推送过多资源

4. **设置适当的优先级**
   - CSS 优先于 JavaScript
   - 关键资源优先加载

### 6.3 安全考虑

1. **强制 HTTPS**
   - 浏览器要求 HTTPS
   - 保护用户隐私

2. **配置 TLS**
   - 使用 TLS 1.2+
   - 配置强密码套件

3. **防止攻击**
   - 限制并发流数
   - 设置最大帧大小
   - 监控资源使用

## 7. HTTP/2 未来发展

### 7.1 HTTP/3

- 基于 QUIC 协议
- 完全消除队头阻塞
- 0-RTT 连接建立

### 7.2 扩展机制

- 帧类型扩展
- 设置参数扩展
- 优先级扩展

### 7.3 新特性

- WebSocket over HTTP/2
- 改进的服务器推送
- 更好的流量控制

## 8. 学习资源

### 8.1 规范文档

- [RFC 7540 - HTTP/2](https://tools.ietf.org/html/rfc7540)
- [RFC 7541 - HPACK](https://tools.ietf.org/html/rfc7541)
- [RFC 8441 - HTTP/2 Bootstrapping with WebSocket](https://tools.ietf.org/html/rfc8441)

### 8.2 在线资源

- [HTTP/2 官网](https://http2.github.io/)
- [HTTP/2 规范](https://httpwg.org/specs/rfc7540.html)
- [HPACK 规范](https://httpwg.org/specs/rfc7541.html)

### 8.3 书籍

- "HTTP/2 in Action" by Barry Pollard
- "High Performance Browser Networking" by Ilya Grigorik
- "Web Performance in Action" by Jeremy Wagner

### 8.4 工具

- [nghttp2](https://nghttp2.org/) - HTTP/2 C 库
- [h2spec](https://github.com/summerwind/h2spec) - 合规性测试
- [h2load](https://nghttp2.org/documentation/h2load-howto.html) - 性能测试

## 9. 总结

HTTP/2 是 HTTP 协议的重大升级，通过二进制分帧、多路复用、头部压缩等技术显著提升了 Web 性能。虽然存在一些缺点，但其优势远大于劣势，已成为现代 Web 的标准协议。

随着 HTTP/3 的发展，HTTP/2 的一些问题（如 TCP 队头阻塞）将得到解决。但 HTTP/2 仍将在很长时间内继续使用，理解其原理对于 Web 开发者至关重要。

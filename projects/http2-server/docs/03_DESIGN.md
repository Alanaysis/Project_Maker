# HTTP/2 服务器技术设计

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      HTTP/2 Server                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Router    │  │  Middleware │  │   Handler   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Request    │  │  Response   │  │   Stream    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Connection  │  │   HPACK    │  │    Frame    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    TCP/Socket                        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 模块划分

#### 核心层
- **Frame**：HTTP/2 帧格式处理
- **HPACK**：头部压缩/解压
- **Stream**：流状态管理
- **Connection**：连接管理

#### 协议层
- **Request**：HTTP 请求处理
- **Response**：HTTP 响应处理
- **Router**：路由匹配
- **Middleware**：中间件处理

#### 应用层
- **Server**：服务器主类
- **StaticFile**：静态文件服务
- **APIHandler**：API 处理器

## 2. 文件组织

### 2.1 目录结构

```
http2-server/
├── CMakeLists.txt
├── README.md
├── include/
│   ├── http2_frame.h
│   ├── http2_hpack.h
│   ├── http2_stream.h
│   ├── http2_request.h
│   ├── http2_response.h
│   ├── http2_connection.h
│   └── http2_server.h
├── src/
│   ├── http2_frame.cpp
│   ├── http2_hpack.cpp
│   ├── http2_stream.cpp
│   ├── http2_request.cpp
│   ├── http2_response.cpp
│   ├── http2_connection.cpp
│   └── http2_server.cpp
├── examples/
│   ├── http2_server_example.cpp
│   ├── static_file_server.cpp
│   ├── api_server.cpp
│   ├── sse_server.cpp
│   └── reverse_proxy.cpp
├── tests/
│   ├── test_frame.cpp
│   ├── test_hpack.cpp
│   ├── test_stream.cpp
│   └── test_request_response.cpp
└── docs/
    ├── 01_RESEARCH.md
    ├── 02_REQUIREMENTS.md
    ├── 03_DESIGN.md
    ├── 04_PRODUCT.md
    └── 05_DEVELOPMENT.md
```

### 2.2 文件职责

#### 头文件（include/）

| 文件 | 职责 |
|------|------|
| http2_frame.h | 帧格式定义、帧类型枚举、帧类 |
| http2_hpack.h | HPACK 编码器、霍夫曼编码表 |
| http2_stream.h | 流状态机、流管理器、流量控制 |
| http2_request.h | HTTP 请求类、方法枚举 |
| http2_response.h | HTTP 响应类、状态码枚举 |
| http2_connection.h | 连接管理、请求处理器 |
| http2_server.h | 服务器类、路由器、中间件 |

#### 源文件（src/）

| 文件 | 职责 |
|------|------|
| http2_frame.cpp | 帧序列化/反序列化 |
| http2_hpack.cpp | HPACK 编码/解码实现 |
| http2_stream.cpp | 流状态转换、流量控制 |
| http2_request.cpp | 请求解析、参数处理 |
| http2_response.cpp | 响应生成、头部设置 |
| http2_connection.cpp | 连接处理、帧路由 |
| http2_server.cpp | 服务器启动、请求路由 |

## 3. 类设计

### 3.1 核心类

#### Frame 类
```cpp
class Frame {
public:
    FrameHeader header;
    std::vector<uint8_t> payload;

    virtual std::vector<uint8_t> serialize();
    static std::unique_ptr<Frame> deserialize(const uint8_t* data, size_t length);
};

class DataFrame : public Frame { ... };
class HeadersFrame : public Frame { ... };
class SettingsFrame : public Frame { ... };
class WindowUpdateFrame : public Frame { ... };
class GoAwayFrame : public Frame { ... };
class PingFrame : public Frame { ... };
class RstStreamFrame : public Frame { ... };
```

#### HPACKEncoder 类
```cpp
class HPACKEncoder {
public:
    std::vector<uint8_t> encode(const std::vector<HeaderField>& headers);
    std::vector<HeaderField> decode(const uint8_t* data, size_t length);
    void set_max_dynamic_table_size(size_t max_size);

private:
    static const std::vector<HeaderField> static_table_;
    std::list<HeaderField> dynamic_table_;
    size_t dynamic_table_size_;
    size_t max_dynamic_table_size_;
};
```

#### Stream 类
```cpp
class Stream {
public:
    Stream(uint32_t stream_id, uint32_t initial_window_size = 65535);

    uint32_t get_id() const;
    StreamState get_state() const;
    void set_state(StreamState state);

    int32_t get_send_window() const;
    int32_t get_recv_window() const;
    void update_send_window(int32_t delta);
    void update_recv_window(int32_t delta);
    bool consume_send_window(int32_t bytes);
    bool consume_recv_window(int32_t bytes);

    void send_headers(bool end_stream = false);
    void recv_headers(bool end_stream = false);
    void send_data(bool end_stream = false);
    void recv_data(bool end_stream = false);
    void send_rst_stream();
    void recv_rst_stream();
};
```

#### StreamManager 类
```cpp
class StreamManager {
public:
    StreamManager(uint32_t initial_window_size = 65535);

    std::shared_ptr<Stream> create_stream(uint32_t stream_id);
    std::shared_ptr<Stream> get_stream(uint32_t stream_id);
    void close_stream(uint32_t stream_id);

    std::vector<std::shared_ptr<Stream>> get_active_streams() const;
    size_t get_active_stream_count() const;
    bool can_create_stream() const;

    void set_max_concurrent_streams(uint32_t max_streams);
    uint32_t get_next_client_stream_id();
    uint32_t get_next_server_stream_id();
    void update_all_windows(int32_t delta);
};
```

### 3.2 协议类

#### HttpRequest 类
```cpp
class HttpRequest {
public:
    void set_method(HttpMethod method);
    void set_method(const std::string& method);
    HttpMethod get_method() const;
    std::string get_method_string() const;

    void set_path(const std::string& path);
    const std::string& get_path() const;

    void set_query(const std::string& query);
    const std::string& get_query() const;
    std::string get_query_param(const std::string& name) const;

    void set_header(const std::string& name, const std::string& value);
    std::string get_header(const std::string& name) const;
    bool has_header(const std::string& name) const;

    void set_body(const std::vector<uint8_t>& body);
    void set_body(const std::string& body);
    const std::vector<uint8_t>& get_body() const;
    std::string get_body_string() const;
};
```

#### HttpResponse 类
```cpp
class HttpResponse {
public:
    void set_status(HttpStatusCode status);
    void set_status(int code);
    HttpStatusCode get_status() const;
    int get_status_code() const;
    std::string get_status_message() const;

    void set_header(const std::string& name, const std::string& value);
    std::string get_header(const std::string& name) const;
    bool has_header(const std::string& name) const;

    void set_body(const std::vector<uint8_t>& body);
    void set_body(const std::string& body);
    void append_body(const std::string& data);
    const std::vector<uint8_t>& get_body() const;
    std::string get_body_string() const;

    void set_content_type(const std::string& type);
    void set_content_length(size_t length);
    void set_cache_control(const std::string& directive);
    void set_cors_headers(const std::string& origin = "*");

    void send_chunk(const std::vector<uint8_t>& chunk);
    void end_stream();
    void send_sse_event(const std::string& event, const std::string& data);
};
```

### 3.3 服务器类

#### Router 类
```cpp
class Router {
public:
    void get(const std::string& path, RequestHandler handler);
    void post(const std::string& path, RequestHandler handler);
    void put(const std::string& path, RequestHandler handler);
    void del(const std::string& path, RequestHandler handler);
    void head(const std::string& path, RequestHandler handler);
    void options(const std::string& path, RequestHandler handler);
    void all(const std::string& path, RequestHandler handler);

    RequestHandler match(HttpMethod method, const std::string& path) const;

    void use(Middleware middleware);
    bool execute_middleware(std::shared_ptr<HttpRequest> request,
                          std::shared_ptr<HttpResponse> response,
                          std::function<void()> final_handler);
};
```

#### Http2Server 类
```cpp
class Http2Server {
public:
    Http2Server(const ServerConfig& config = ServerConfig());
    ~Http2Server();

    bool start();
    void stop();

    Router& get_router();
    void serve_static(const std::string& mount_point, const StaticFileConfig& config);
    void set_request_handler(RequestHandler handler);

    bool is_running() const;
    size_t get_connection_count() const;
};
```

## 4. 数据流设计

### 4.1 请求处理流程

```
Client Request
      ↓
┌─────────────────┐
│   TCP Socket    │
└─────────────────┘
      ↓
┌─────────────────┐
│  Frame Parser   │
└─────────────────┘
      ↓
┌─────────────────┐
│  HPACK Decoder  │
└─────────────────┘
      ↓
┌─────────────────┐
│ Stream Manager  │
└─────────────────┘
      ↓
┌─────────────────┐
│  Connection     │
└─────────────────┘
      ↓
┌─────────────────┐
│    Router       │
└─────────────────┘
      ↓
┌─────────────────┐
│  Middleware     │
└─────────────────┘
      ↓
┌─────────────────┐
│    Handler      │
└─────────────────┘
      ↓
┌─────────────────┐
│   Response      │
└─────────────────┘
      ↓
Client Response
```

### 4.2 帧处理流程

```
Raw Bytes
      ↓
┌─────────────────┐
│ Frame Header    │
│ (9 bytes)       │
└─────────────────┘
      ↓
┌─────────────────┐
│ Frame Payload   │
│ (length bytes)  │
└─────────────────┘
      ↓
┌─────────────────┐
│ Frame Type      │
│ Dispatch        │
└─────────────────┘
      ↓
┌─────────────────┐
│ Type-specific   │
│ Processing      │
└─────────────────┘
```

### 4.3 流状态转换

```
                    send_headers()
    ┌───────────────────────────────────────────┐
    │                                           ↓
┌───────┐                                  ┌───────┐
│ idle  │                                  │ open  │
└───────┘                                  └───────┘
    │                                           │
    │ recv_headers()                            │
    ↓                                           │
┌───────┐                                  ┌───────┐
│ open  │                                  │ half  │
│       │                                  │closed │
└───────┘                                  │(local)│
    │                                      └───────┘
    │ recv_data(end_stream=true)                │
    ↓                                           │
┌───────┐                                  ┌───────┐
│ half  │                                  │closed │
│closed │                                  └───────┘
│(remote)                                      ↑
└───────┘                                      │
    │                                          │
    │ send_data(end_stream=true)               │
    └──────────────────────────────────────────┘
```

## 5. 接口设计

### 5.1 服务器配置接口

```cpp
struct ServerConfig {
    std::string host = "0.0.0.0";
    uint16_t port = 8080;
    int backlog = 128;
    int max_connections = 1000;
    int num_threads = 4;
    bool enable_tls = false;
    std::string cert_file;
    std::string key_file;
    ConnectionSettings connection_settings;
};

struct ConnectionSettings {
    uint32_t header_table_size = 4096;
    uint32_t enable_push = 0;
    uint32_t max_concurrent_streams = 100;
    uint32_t initial_window_size = 65535;
    uint32_t max_frame_size = 16384;
    uint32_t max_header_list_size = 8192;
};

struct StaticFileConfig {
    std::string root_dir;
    std::string index_file = "index.html";
    bool enable_directory_listing = false;
    int cache_max_age = 3600;
    std::map<std::string, std::string> mime_types;
};
```

### 5.2 请求处理器接口

```cpp
using RequestHandler = std::function<void(
    std::shared_ptr<HttpRequest> request,
    std::shared_ptr<HttpResponse> response
)>;

using Middleware = std::function<bool(
    std::shared_ptr<HttpRequest> request,
    std::shared_ptr<HttpResponse> response,
    std::function<void()> next
)>;
```

### 5.3 服务器接口

```cpp
class Http2Server {
public:
    // 生命周期
    bool start();
    void stop();
    bool is_running() const;

    // 配置
    Router& get_router();
    void serve_static(const std::string& mount_point, const StaticFileConfig& config);
    void set_request_handler(RequestHandler handler);

    // 状态
    size_t get_connection_count() const;
};
```

## 6. 错误处理设计

### 6.1 错误类型

```cpp
enum class ErrorCode : uint32_t {
    NO_ERROR           = 0x00,
    PROTOCOL_ERROR     = 0x01,
    INTERNAL_ERROR     = 0x02,
    FLOW_CONTROL_ERROR = 0x03,
    SETTINGS_TIMEOUT   = 0x04,
    STREAM_CLOSED      = 0x05,
    FRAME_SIZE_ERROR   = 0x06,
    REFUSED_STREAM     = 0x07,
    CANCEL             = 0x08,
    COMPRESSION_ERROR  = 0x09,
    CONNECT_ERROR      = 0x0a,
    ENHANCE_YOUR_CALM = 0x0b,
    INADEQUATE_SECURITY = 0x0c,
    HTTP_1_1_REQUIRED  = 0x0d
};
```

### 6.2 错误处理策略

#### 连接级错误
- 发送 GOAWAY 帧
- 关闭连接
- 记录错误日志

#### 流级错误
- 发送 RST_STREAM 帧
- 关闭流
- 继续处理其他流

#### 应用级错误
- 生成错误响应
- 记录错误日志
- 通知监控系统

### 6.3 异常安全

- 使用 RAII 管理资源
- 捕获所有异常
- 保证异常安全

## 7. 并发设计

### 7.1 线程模型

```
Main Thread
      │
      ├── Accept Thread
      │   └── Accept new connections
      │
      ├── Worker Thread 1
      │   └── Handle connections
      │
      ├── Worker Thread 2
      │   └── Handle connections
      │
      └── Worker Thread N
          └── Handle connections
```

### 7.2 同步机制

- **互斥锁**：保护共享数据
- **原子变量**：无锁计数器
- **条件变量**：线程通知
- **读写锁**：读多写少场景

### 7.3 线程安全

- 连接列表使用互斥锁
- 流管理器使用互斥锁
- 配置数据使用读写锁
- 统计数据使用原子变量

## 8. 性能设计

### 8.1 内存管理

- 使用智能指针管理对象
- 对象池复用对象
- 避免不必要的拷贝
- 使用移动语义

### 8.2 I/O 优化

- 非阻塞 I/O
- 批量读写
- 缓冲区管理
- 零拷贝技术

### 8.3 协议优化

- 头部压缩
- 流量控制
- 连接复用
- 服务器推送

### 8.4 缓存策略

- 响应缓存
- 头部缓存
- 连接缓存
- 文件缓存

## 9. 安全设计

### 9.1 输入验证

- 验证帧格式
- 验证头部大小
- 验证路径安全
- 验证请求大小

### 9.2 访问控制

- CORS 配置
- IP 白名单/黑名单
- 用户认证
- 权限控制

### 9.3 防护措施

- 速率限制
- 连接限制
- 资源限制
- 日志审计

## 10. 测试设计

### 10.1 单元测试

- 帧序列化/反序列化
- HPACK 编码/解码
- 流状态转换
- 请求/响应处理

### 10.2 集成测试

- 连接建立
- 请求处理
- 响应生成
- 错误处理

### 10.3 性能测试

- 并发连接测试
- 吞吐量测试
- 延迟测试
- 资源使用测试

### 10.4 安全测试

- 输入验证测试
- 访问控制测试
- 防护措施测试
- 漏洞扫描

## 11. 部署设计

### 11.1 构建系统

```cmake
cmake_minimum_required(VERSION 3.16)
project(http2-server)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(http2_lib STATIC ${SOURCES})
add_executable(http2_server examples/http2_server_example.cpp)
target_link_libraries(http2_server http2_lib pthread)
```

### 11.2 安装部署

```bash
# 编译
mkdir build && cd build
cmake ..
make

# 安装
sudo make install

# 运行
http2_server -p 8080
```

### 11.3 配置管理

- 命令行参数
- 配置文件
- 环境变量
- 默认值

## 12. 监控设计

### 12.1 指标收集

- 连接数
- 请求速率
- 响应时间
- 错误率

### 12.2 日志记录

- 访问日志
- 错误日志
- 调试日志
- 审计日志

### 12.3 健康检查

- 连接状态
- 内存使用
- CPU 使用
- 磁盘空间

## 13. 扩展设计

### 13.1 插件机制

- 中间件插件
- 协议扩展
- 功能模块
- 第三方集成

### 13.2 模块化设计

- 核心模块
- 协议模块
- 应用模块
- 工具模块

### 13.3 配置灵活

- 运行时配置
- 动态加载
- 热更新
- 版本管理

## 14. 总结

本设计文档详细描述了 HTTP/2 服务器的技术架构、模块划分、接口设计、并发模型、性能优化、安全防护等方面。通过清晰的模块划分和接口设计，可以保证系统的可维护性和可扩展性。

关键设计决策：
1. 使用 C++17 特性提高开发效率
2. 采用多线程模型提高并发性能
3. 使用智能指针管理内存
4. 实现完整的 HTTP/2 协议支持
5. 提供灵活的路由和中间件系统
6. 支持静态文件服务和 API 服务

# DNS 服务器技术设计

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      DNS Server                             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ UDP Server  │  │ TCP Server  │  │   Event     │         │
│  │             │  │             │  │   Loop      │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          │                                  │
│  ┌───────────────────────┴───────────────────────┐         │
│  │              Request Handler                   │         │
│  └───────────────────────┬───────────────────────┘         │
│                          │                                  │
│  ┌───────────┬───────────┼───────────┬───────────┐         │
│  │           │           │           │           │         │
│  ▼           ▼           ▼           ▼           ▼         │
│ ACL      Cache      Zone        Resolver     Security      │
│ Check    Lookup     Query       (Recursive)  (DNSSEC)      │
│  │           │           │           │           │         │
│  └───────────┴───────────┴───────────┴───────────┘         │
│                          │                                  │
│  ┌───────────────────────┴───────────────────────┐         │
│  │              Response Builder                  │         │
│  └───────────────────────┬───────────────────────┘         │
│                          │                                  │
│  ┌───────────┬───────────┼───────────┬───────────┐         │
│  │           │           │           │           │         │
│  ▼           ▼           ▼           ▼           ▼         │
│ Monitor   Logger     Stats       Audit      Response       │
│                          │                                  │
└──────────────────────────┼──────────────────────────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Client    │
                    └─────────────┘
```

### 1.2 模块划分

| 模块 | 职责 | 主要类 |
|------|------|--------|
| protocol | DNS 协议实现 | DnsMessage, DnsServer |
| resolver | DNS 解析 | DnsResolver, DnsCache |
| zone | 区域管理 | Zone, ZoneManager |
| security | 安全特性 | DnssecValidator, AccessControlList |
| performance | 性能优化 | EventLoop, ThreadPool |
| monitoring | 监控日志 | Logger, QueryStatsCollector |
| application | 应用实现 | AuthoritativeServer, RecursiveServer |

## 2. 文件组织

### 2.1 目录结构

```
dns-server/
├── include/                    # 头文件
│   ├── protocol/               # DNS 协议
│   │   ├── dns_message.h       # 报文定义
│   │   └── dns_server.h        # 服务器定义
│   ├── resolver/               # 解析器
│   │   ├── dns_resolver.h      # 解析器定义
│   │   └── dns_cache.h         # 缓存定义
│   ├── zone/                   # 区域管理
│   │   └── zone_manager.h      # 区域管理器
│   ├── security/               # 安全特性
│   │   ├── dnssec.h            # DNSSEC
│   │   └── access_control.h    # 访问控制
│   ├── performance/            # 性能优化
│   │   └── async_io.h          # 异步 I/O
│   ├── monitoring/             # 监控日志
│   │   └── dns_monitor.h       # 监控系统
│   └── application/            # 应用实现
│       ├── authoritative_server.h
│       ├── recursive_server.h
│       └── dns_forwarder.h
├── src/                        # 源文件
│   ├── protocol/
│   │   ├── dns_message.cpp
│   │   └── dns_server.cpp
│   ├── resolver/
│   │   ├── dns_resolver.cpp
│   │   └── dns_cache.cpp
│   ├── zone/
│   │   └── zone_manager.cpp
│   ├── security/
│   │   ├── dnssec.cpp
│   │   └── access_control.cpp
│   ├── performance/
│   │   └── async_io.cpp
│   ├── monitoring/
│   │   └── dns_monitor.cpp
│   └── application/
│       ├── authoritative_server.cpp
│       ├── recursive_server.cpp
│       └── dns_forwarder.cpp
└── tests/                      # 测试文件
    ├── test_dns_message.cpp
    ├── test_cache.cpp
    └── test_zone.cpp
```

### 2.2 文件职责

| 文件 | 职责 | 行数估计 |
|------|------|----------|
| dns_message.h/cpp | DNS 报文解析/序列化 | ~800 |
| dns_server.h/cpp | 服务器网络层 | ~500 |
| dns_resolver.h/cpp | DNS 解析器 | ~600 |
| dns_cache.h/cpp | 缓存实现 | ~400 |
| zone_manager.h/cpp | 区域管理 | ~700 |
| dnssec.h/cpp | DNSSEC 实现 | ~600 |
| access_control.h/cpp | 访问控制 | ~500 |
| async_io.h/cpp | 异步 I/O | ~400 |
| dns_monitor.h/cpp | 监控日志 | ~500 |

## 3. 核心类设计

### 3.1 DnsMessage

```cpp
class DnsMessage {
public:
    // 访问器
    DnsHeader& header();
    std::vector<DnsQuestion>& questions();
    std::vector<ResourceRecord>& answers();
    std::vector<ResourceRecord>& authorities();
    std::vector<ResourceRecord>& additionals();

    // 序列化/反序列化
    std::vector<uint8_t> serialize() const;
    static std::optional<DnsMessage> deserialize(std::span<const uint8_t> data);

    // 工厂方法
    static DnsMessage create_query(const std::string& name, RecordType type);
    static DnsMessage create_response(const DnsMessage& query, ResponseCode rcode);

    // 操作方法
    void add_answer(ResourceRecord rr);
    void add_authority(ResourceRecord rr);
    void add_additional(ResourceRecord rr);
    void set_response(ResponseCode rcode);
};
```

### 3.2 DnsResolver

```cpp
class DnsResolver {
public:
    explicit DnsResolver(const ResolverConfig& config);

    // 解析方法
    ResolveResult resolve(const std::string& name, RecordType type);
    ResolveResult resolve_iterative(const std::string& name, RecordType type);
    ResolveResult reverse_resolve(const std::string& ip_addr);

    // 缓存管理
    void clear_cache();
    CacheStats get_cache_stats() const;

private:
    // 内部方法
    ResolveResult resolve_recursive(const std::string& name, RecordType type, size_t depth);
    ResolveResult query_authoritative(const std::string& zone,
                                       const std::vector<ResourceRecord>& ns_records,
                                       const std::string& name, RecordType type);
    ResolveResult follow_cname(const std::string& cname_target, RecordType type, size_t depth);

    ResolverConfig config_;
    DnsQuerier querier_;
    std::unique_ptr<DnsCache> cache_;
};
```

### 3.3 ZoneManager

```cpp
class ZoneManager {
public:
    // 区域管理
    bool load_zone(const ZoneConfig& config);
    bool add_zone(std::unique_ptr<Zone> zone);
    bool remove_zone(const std::string& zone_name);
    Zone* get_zone(const std::string& zone_name);
    Zone* find_zone(const std::string& name);

    // 查询
    std::vector<ResourceRecord> query(const std::string& name, RecordType type);

    // 区域传输
    std::vector<DnsMessage> handle_transfer(const std::string& zone_name,
                                             TransferType type, uint32_t client_serial);

    // 动态更新
    ResponseCode handle_update(const std::string& zone_name, const DnsMessage& request);

    // 持久化
    bool save_zone(const std::string& zone_name, const std::string& filename);
    bool reload_zone(const std::string& zone_name);
};
```

### 3.4 DnsServer

```cpp
class DnsServer {
public:
    explicit DnsServer(const DnsServerConfig& config);

    // 设置处理器
    void set_handler(DnsRequestHandler handler);

    // 控制方法
    bool start();
    void stop();
    bool is_running() const;

    // 统计信息
    Stats get_stats() const;

private:
    DnsServerConfig config_;
    DnsRequestHandler handler_;
    std::unique_ptr<UdpServer> udp_server_;
    std::unique_ptr<TcpServer> tcp_server_;
    Stats stats_;
};
```

## 4. 数据流设计

### 4.1 查询处理流程

```
Client Query
     │
     ▼
┌─────────────┐
│ UDP/TCP     │ 接收请求
│ Server      │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Parse       │ 解析报文
│ Message     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ ACL Check   │ 访问控制
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Rate Limit  │ 速率限制
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Query       │ 查询过滤
│ Filter      │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Cache       │ 缓存查询
│ Lookup      │
└──────┬──────┘
       │
       ├──── Cache Hit ────► Response
       │
       ▼
┌─────────────┐
│ Zone        │ 区域查询
│ Query       │
└──────┬──────┘
       │
       ├──── Found ────► Response
       │
       ▼
┌─────────────┐
│ Recursive   │ 递归解析
│ Resolve     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Cache       │ 缓存结果
│ Store       │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Build       │ 构建响应
│ Response    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Log &       │ 记录日志
│ Stats       │
└──────┬──────┘
       │
       ▼
Client Response
```

### 4.2 区域传输流程

```
Transfer Request
       │
       ▼
┌─────────────┐
│ ACL Check   │ 检查权限
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Get Zone    │ 获取区域
└──────┬──────┘
       │
       ├──── AXFR ────► Full Zone Dump
       │
       └──── IXFR ────► Incremental Changes
              │
              ▼
       ┌─────────────┐
       │ TCP Send    │ TCP 发送
       └─────────────┘
```

## 5. 接口设计

### 5.1 配置接口

```cpp
// 服务器配置
struct DnsServerConfig {
    std::string bind_address = "0.0.0.0";
    uint16_t port = 53;
    size_t thread_pool_size = 4;
    size_t max_connections = 1000;
    bool enable_udp = true;
    bool enable_tcp = true;
};

// 缓存配置
struct CacheConfig {
    size_t max_entries = 10000;
    uint32_t min_ttl = 60;
    uint32_t max_ttl = 86400;
    uint32_t negative_ttl = 300;
    bool enable_negative_cache = true;
};

// 区域配置
struct ZoneConfig {
    std::string zone_file;
    ZoneType type = ZoneType::PRIMARY;
    std::string zone_name;
    bool allow_transfer = false;
    std::vector<std::string> transfer_allowed;
};
```

### 5.2 回调接口

```cpp
// 请求处理器
using DnsRequestHandler = std::function<DnsMessage(
    const DnsMessage& request,
    const std::string& client_addr,
    uint16_t client_port
)>;

// 事件回调
using EventCallback = std::function<void(int fd, EventType type)>;

// 查询回调
using QueryCallback = std::function<void(std::optional<DnsMessage>)>;
```

### 5.3 日志接口

```cpp
class Logger {
public:
    static Logger& instance();

    void set_level(LogLevel level);
    void add_sink(std::unique_ptr<LogSink> sink);

    void trace(const std::string& source, const std::string& message);
    void debug(const std::string& source, const std::string& message);
    void info(const std::string& source, const std::string& message);
    void warn(const std::string& source, const std::string& message);
    void error(const std::string& source, const std::string& message);
    void fatal(const std::string& source, const std::string& message);
};

// 便捷宏
#define DNS_LOG_INFO(source, msg) dns::Logger::instance().info(source, msg)
```

## 6. 错误处理

### 6.1 错误类型

| 错误类型 | 处理方式 | 示例 |
|----------|----------|------|
| 网络错误 | 重试/回退 | 连接超时 |
| 协议错误 | 返回错误码 | 格式错误 |
| 配置错误 | 日志/拒绝启动 | 无效配置 |
| 内存错误 | 异常处理 | 分配失败 |

### 6.2 错误响应

```cpp
// 错误响应码
enum class ResponseCode : uint8_t {
    NO_ERROR        = 0,  // 无错误
    FORMAT_ERROR    = 1,  // 报文格式错误
    SERVER_FAILURE  = 2,  // 服务器失败
    NAME_ERROR      = 3,  // 域名不存在
    NOT_IMPLEMENTED = 4,  // 未实现
    REFUSED         = 5,  // 拒绝查询
};
```

## 7. 性能设计

### 7.1 并发模型

```
┌─────────────────────────────────────────────┐
│                Main Thread                   │
│  ┌─────────────────────────────────────┐    │
│  │         Event Loop (epoll)          │    │
│  └──────────────────┬──────────────────┘    │
│                     │                        │
│  ┌──────────────────┼──────────────────┐    │
│  │                  │                  │    │
│  ▼                  ▼                  ▼    │
│ Worker 1        Worker 2        Worker N    │
│ ┌────────┐      ┌────────┐      ┌────────┐ │
│ │ Queue  │      │ Queue  │      │ Queue  │ │
│ └───┬────┘      └───┬────┘      └───┬────┘ │
│     │               │               │       │
│     ▼               ▼               ▼       │
│  Process         Process         Process    │
│  Request         Request         Request    │
└─────────────────────────────────────────────┘
```

### 7.2 缓存策略

```
┌─────────────────────────────────────────────┐
│              LRU Cache                       │
│  ┌─────────────────────────────────────┐    │
│  │         Hash Map (O(1))             │    │
│  │  ┌─────┐ ┌─────┐ ┌─────┐           │    │
│  │  │Key1 │ │Key2 │ │Key3 │ ...       │    │
│  │  └──┬──┘ └──┬──┘ └──┬──┘           │    │
│  │     │       │       │               │    │
│  │     ▼       ▼       ▼               │    │
│  │  ┌─────┐ ┌─────┐ ┌─────┐           │    │
│  │  │Entry│ │Entry│ │Entry│           │    │
│  │  └─────┘ └─────┘ └─────┘           │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │      LRU List (Doubly Linked)       │    │
│  │  ◄──► [Recent] ◄──► [Old] ◄──►     │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

## 8. 安全设计

### 8.1 访问控制流程

```
Request
   │
   ▼
┌─────────────┐
│ IP Check    │ 检查客户端 IP
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ ACL Match   │ 匹配 ACL 规则
└──────┬──────┘
       │
       ├──── DENY ────► REFUSED
       │
       ├──── ALLOW ───► Continue
       │
       └──── Default ──► Check Default Action
```

### 8.2 DNSSEC 验证流程

```
Response
   │
   ▼
┌─────────────┐
│ Get RRSIG   │ 获取签名记录
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Get DNSKEY  │ 获取公钥
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Verify DS   │ 验证 DS 链
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Verify RRSIG│ 验证签名
└──────┬──────┘
       │
       ├──── Valid ────► Secure
       │
       └──── Invalid ──► Bogus
```

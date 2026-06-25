# DNS 服务器 (DNS Server)

一个完整的 DNS 服务器项目，涵盖 DNS 协议的核心技术。

## 项目概述

本项目实现了一个全面的 DNS 服务器，包含：
- DNS 协议实现（报文格式、查询类型、响应码）
- DNS 解析（递归解析、迭代解析、反向解析、缓存）
- 区域管理（区域文件解析、区域传输、动态更新）
- 安全特性（DNSSEC、TSIG 认证、访问控制、速率限制）
- 性能优化（异步 I/O、多线程、连接池）
- 监控和日志（查询统计、性能监控、审计日志）
- 实际应用（权威服务器、递归服务器、转发器、负载均衡）

## 核心流程

```
客户端查询 → 接收请求 → 解析报文 → 查询处理 → 构建响应 → 返回结果
                ↓
            访问控制 → 缓存查询 → 区域查询 → 递归解析
                ↓
            记录日志 → 更新统计 → 缓存结果
```

## 功能特性

### DNS 协议
- DNS 报文格式（Header/Question/Answer/Authority/Additional）
- 查询类型（A, AAAA, MX, CNAME, NS, TXT, SRV, PTR）
- 响应码（NOERROR, NXDOMAIN, SERVFAIL, REFUSED 等）
- 递归查询和迭代查询
- EDNS0 扩展

### DNS 解析
- 递归解析器
- 迭代解析器
- 反向解析（IP -> 域名）
- 缓存机制（LRU 淘汰、TTL 管理、负缓存）
- 转发机制

### 区域管理
- 区域文件解析（标准 BIND 格式）
- 区域传输（AXFR 全量、IXFR 增量）
- 动态更新（RFC 2136）
- SOA 记录管理

### 安全特性
- DNSSEC（DNSKEY, RRSIG, DS, NSEC 记录）
- TSIG 认证（HMAC-MD5, HMAC-SHA256）
- 访问控制列表（ACL）
- 速率限制
- 查询过滤（黑名单/白名单）

### 性能优化
- epoll 异步 I/O
- 线程池
- 连接池
- 异步 DNS 查询
- 消息压缩

### 监控和日志
- 查询统计（按类型、响应码、客户端）
- 性能监控（CPU、内存、网络）
- 错误日志（分级日志、文件轮转）
- 审计日志（操作记录、安全事件）
- ISC 格式查询日志

### 实际应用
- 权威 DNS 服务器
- 递归 DNS 服务器
- DNS 转发器
- DNS 负载均衡器（加权轮询、健康检查）

## 系统要求

- Linux/macOS
- GCC 9+ / Clang 10+
- CMake 3.16+
- OpenSSL 1.1+

## 快速开始

### 安装依赖

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install build-essential cmake libssl-dev
```

#### macOS
```bash
brew install cmake openssl
```

### 构建项目

```bash
cd projects/dns-server
mkdir build && cd build
cmake ..
make -j$(nproc)
```

### 运行示例

```bash
# 基本 DNS 服务器
./bin/basic_server

# 权威 DNS 服务器
./bin/authoritative_server_example

# 递归 DNS 服务器
./bin/recursive_server_example

# DNS 转发器
./bin/forwarder_example

# DNS 负载均衡器
./bin/load_balancer_example

# DNS 客户端
./bin/dns_client_example
```

### 运行测试

```bash
cd build
ctest --output-on-failure
```

## 项目结构

```
dns-server/
├── CMakeLists.txt              # CMake 构建配置
├── README.md                   # 项目说明
├── include/                    # 头文件
│   ├── protocol/               # DNS 协议
│   │   ├── dns_message.h       # DNS 报文
│   │   └── dns_server.h        # DNS 服务器
│   ├── resolver/               # DNS 解析
│   │   ├── dns_resolver.h      # DNS 解析器
│   │   └── dns_cache.h         # DNS 缓存
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
│       ├── authoritative_server.h  # 权威服务器
│       ├── recursive_server.h      # 递归服务器
│       └── dns_forwarder.h         # 转发器/负载均衡
├── src/                        # 源代码
│   ├── protocol/               # 协议实现
│   ├── resolver/               # 解析器实现
│   ├── zone/                   # 区域管理实现
│   ├── security/               # 安全特性实现
│   ├── performance/            # 性能优化实现
│   ├── monitoring/             # 监控日志实现
│   └── application/            # 应用实现
├── examples/                   # 示例程序
│   ├── basic_server.cpp        # 基本服务器
│   ├── authoritative_server_example.cpp  # 权威服务器
│   ├── recursive_server_example.cpp      # 递归服务器
│   ├── forwarder_example.cpp             # 转发器
│   ├── load_balancer_example.cpp         # 负载均衡
│   └── dns_client_example.cpp            # DNS 客户端
├── tests/                      # 测试代码
│   ├── test_dns_message.cpp    # 报文测试
│   ├── test_cache.cpp          # 缓存测试
│   └── test_zone.cpp           # 区域测试
└── docs/                       # 文档
    ├── 01_RESEARCH.md          # 市场调研
    ├── 02_REQUIREMENTS.md      # 需求分析
    ├── 03_DESIGN.md            # 技术设计
    ├── 04_PRODUCT.md           # 产品思考
    └── 05_DEVELOPMENT.md       # 开发手册
```

## 配置说明

### DNS 服务器配置

```cpp
DnsServerConfig config;
config.bind_address = "0.0.0.0";  // 绑定地址
config.port = 53;                  // 监听端口
config.thread_pool_size = 4;       // 线程池大小
config.max_connections = 1000;     // 最大连接数
config.enable_udp = true;          // 启用 UDP
config.enable_tcp = true;          // 启用 TCP
```

### 缓存配置

```cpp
CacheConfig config;
config.max_entries = 10000;        // 最大缓存条目
config.min_ttl = 60;               // 最小 TTL
config.max_ttl = 86400;            // 最大 TTL
config.negative_ttl = 300;         // 负缓存 TTL
config.enable_negative_cache = true; // 启用负缓存
```

### 区域文件格式

```bind
$ORIGIN example.com.
$TTL 3600

@       IN  SOA   ns1.example.com. admin.example.com. (
                  2024010101  ; Serial
                  3600        ; Refresh
                  900         ; Retry
                  604800      ; Expire
                  86400       ; Minimum TTL
                  )

@       IN  NS    ns1.example.com.
@       IN  NS    ns2.example.com.

ns1     IN  A     192.168.1.1
ns2     IN  A     192.168.1.2

www     IN  CNAME example.com.
mail    IN  A     192.168.1.10

@       IN  MX    10 mail.example.com.
@       IN  TXT   "v=spf1 mx ~all"

_http   IN  SRV   10 60 80 www.example.com.
```

## 学习资源

- [RFC 1035 - Domain Names](https://tools.ietf.org/html/rfc1035)
- [RFC 1034 - Domain Concepts](https://tools.ietf.org/html/rfc1034)
- [RFC 2136 - Dynamic Updates](https://tools.ietf.org/html/rfc2136)
- [RFC 4034 - DNSSEC](https://tools.ietf.org/html/rfc4034)
- [RFC 2845 - TSIG](https://tools.ietf.org/html/rfc2845)

## 常见问题

### Q: 如何修改监听端口？
A: 修改 `DnsServerConfig` 中的 `port` 参数，注意 53 以下端口需要 root 权限。

### Q: 如何添加自定义记录？
A: 通过 `Zone::add_record()` 方法添加记录，或修改区域文件后重新加载。

### Q: 如何启用 DNSSEC？
A: 使用 `DnssecSigner` 生成密钥对并签名区域，配置信任锚点。

### Q: 如何配置转发器？
A: 在 `RecursiveConfig` 中设置 `forwarders` 列表。

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

---

[返回主目录](../../README.md)

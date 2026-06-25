# DNS 服务器开发手册

## 1. 环境准备

### 1.1 系统要求

| 要求 | 最低 | 推荐 |
|------|------|------|
| 操作系统 | Linux/macOS | Ubuntu 20.04+ |
| 编译器 | GCC 9+ / Clang 10+ | GCC 11+ / Clang 14+ |
| CMake | 3.16+ | 3.20+ |
| 内存 | 1GB | 4GB+ |
| 磁盘 | 100MB | 500MB+ |

### 1.2 依赖安装

#### Ubuntu/Debian

```bash
sudo apt update
sudo apt install -y \
    build-essential \
    cmake \
    git \
    libssl-dev \
    pkg-config
```

#### CentOS/RHEL

```bash
sudo yum install -y \
    gcc-c++ \
    cmake3 \
    git \
    openssl-devel
```

#### macOS

```bash
brew install cmake openssl
```

### 1.3 开发工具

| 工具 | 用途 | 安装 |
|------|------|------|
| VS Code | IDE | [下载](https://code.visualstudio.com/) |
| CLion | IDE | [下载](https://www.jetbrains.com/clion/) |
| GDB | 调试器 | `apt install gdb` |
| Valgrind | 内存检测 | `apt install valgrind` |
| Wireshark | 抓包分析 | `apt install wireshark` |
| dig | DNS 工具 | `apt install dnsutils` |

## 2. 编译说明

### 2.1 基本编译

```bash
# 克隆项目
cd projects/dns-server

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

# 禁用示例
cmake -DBUILD_EXAMPLES=OFF ..

# 禁用测试
cmake -DBUILD_TESTS=OFF ..

# 指定安装路径
cmake -DCMAKE_INSTALL_PREFIX=/usr/local ..
```

### 2.3 编译输出

```
build/
├── bin/                    # 可执行文件
│   ├── basic_server
│   ├── authoritative_server_example
│   ├── recursive_server_example
│   ├── forwarder_example
│   ├── load_balancer_example
│   └── dns_client_example
├── lib/                    # 库文件
│   └── libdns-server-core.a
└── tests/                  # 测试
    ├── test_dns_message
    ├── test_cache
    └── test_zone
```

## 3. 运行方式

### 3.1 基本服务器

```bash
# 启动基本 DNS 服务器
./bin/basic_server

# 测试查询
dig @127.0.0.1 -p 5353 example.com A
```

### 3.2 权威服务器

```bash
# 启动权威 DNS 服务器
./bin/authoritative_server_example

# 测试查询
dig @127.0.0.1 -p 5354 example.com A
dig @127.0.0.1 -p 5354 example.com MX
dig @127.0.0.1 -p 5354 example.com NS
```

### 3.3 递归服务器

```bash
# 启动递归 DNS 服务器
./bin/recursive_server_example

# 测试查询
dig @127.0.0.1 -p 5355 www.google.com A
dig @127.0.0.1 -p 5355 github.com MX
```

### 3.4 转发器

```bash
# 启动 DNS 转发器
./bin/forwarder_example

# 测试查询
dig @127.0.0.1 -p 5356 example.com A
```

### 3.5 负载均衡器

```bash
# 启动 DNS 负载均衡器
./bin/load_balancer_example

# 测试查询
dig @127.0.0.1 -p 5357 example.com A
```

### 3.6 DNS 客户端

```bash
# 运行 DNS 客户端示例
./bin/dns_client_example
```

## 4. 测试

### 4.1 运行所有测试

```bash
cd build
ctest --output-on-failure
```

### 4.2 运行单个测试

```bash
# 报文测试
./tests/test_dns_message

# 缓存测试
./tests/test_cache

# 区域测试
./tests/test_zone
```

### 4.3 测试覆盖率

```bash
# 安装 gcovr
pip install gcovr

# 编译时启用覆盖率
cmake -DCMAKE_BUILD_TYPE=Coverage ..
make -j$(nproc)

# 运行测试
ctest

# 生成覆盖率报告
gcovr -r .. --html --html-details -o coverage.html
```

## 5. 调试

### 5.1 GDB 调试

```bash
# 编译 Debug 版本
cmake -DCMAKE_BUILD_TYPE=Debug ..
make -j$(nproc)

# 运行 GDB
gdb ./bin/basic_server

# 常用命令
(gdb) break main          # 设置断点
(gdb) run                 # 运行程序
(gdb) next                # 单步执行
(gdb) step                # 进入函数
(gdb) print variable      # 打印变量
(gdb) backtrace           # 查看调用栈
(gdb) quit                # 退出
```

### 5.2 Valgrind 内存检测

```bash
# 检测内存泄漏
valgrind --leak-check=full ./bin/basic_server

# 检测内存错误
valgrind --tool=memcheck ./bin/basic_server
```

### 5.3 Wireshark 抓包

```bash
# 启动抓包
sudo wireshark -i lo -f "udp port 5353"

# 或使用 tcpdump
sudo tcpdump -i lo -n -v udp port 5353
```

### 5.4 DNS 工具测试

```bash
# 使用 dig 测试
dig @127.0.0.1 -p 5353 example.com A
dig @127.0.0.1 -p 5353 example.com AAAA
dig @127.0.0.1 -p 5353 example.com MX
dig @127.0.0.1 -p 5353 example.com NS
dig @127.0.0.1 -p 5353 example.com TXT

# 使用 nslookup 测试
nslookup example.com 127.0.0.1 -port=5353
```

## 6. 代码规范

### 6.1 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 命名空间 | 小写 | `dns` |
| 类名 | PascalCase | `DnsMessage` |
| 函数名 | snake_case | `create_query` |
| 变量名 | snake_case | `thread_pool_size` |
| 常量 | UPPER_CASE | `DNS_PORT` |
| 枚举 | PascalCase | `RecordType` |

### 6.2 注释规范

```cpp
/**
 * @file dns_message.h
 * @brief DNS 报文格式定义
 *
 * 详细描述...
 */

/**
 * @brief 创建查询报文
 *
 * @param name 域名
 * @param type 记录类型
 * @param rd 是否期望递归
 * @return DnsMessage 查询报文
 */
static DnsMessage create_query(const std::string& name,
                                RecordType type,
                                bool rd = true);
```

### 6.3 文件组织

```cpp
// 1. 头文件包含
#include "dns_message.h"
#include <vector>

// 2. 命名空间
namespace dns {

// 3. 常量定义
constexpr uint16_t DNS_PORT = 53;

// 4. 类定义
class DnsMessage {
    // ...
};

} // namespace dns
```

## 7. 性能调优

### 7.1 编译优化

```bash
# Release 模式
cmake -DCMAKE_BUILD_TYPE=Release ..

# 链接时优化
cmake -DCMAKE_INTERPROCEDURAL_OPTIMIZATION=ON ..

# 指定 CPU 架构
cmake -DCMAKE_CXX_FLAGS="-march=native" ..
```

### 7.2 运行时调优

```cpp
// 调整线程池大小
config.thread_pool_size = std::thread::hardware_concurrency();

// 调整缓存大小
config.cache_config.max_entries = 100000;

// 调整连接数
config.max_connections = 10000;
```

### 7.3 系统调优

```bash
# 增加文件描述符限制
ulimit -n 65535

# 调整内核参数
sudo sysctl -w net.core.somaxconn=65535
sudo sysctl -w net.ipv4.tcp_max_syn_backlog=65535
```

## 8. 部署

### 8.1 安装

```bash
cd build
sudo make install
```

### 8.2 系统服务

```bash
# 创建服务文件
sudo tee /etc/systemd/system/dns-server.service << EOF
[Unit]
Description=DNS Server
After=network.target

[Service]
Type=simple
User=nobody
ExecStart=/usr/local/bin/basic_server
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 启用服务
sudo systemctl enable dns-server
sudo systemctl start dns-server

# 查看状态
sudo systemctl status dns-server
```

### 8.3 Docker 部署

```dockerfile
FROM ubuntu:20.04

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libssl-dev

COPY . /app
WORKDIR /app

RUN mkdir build && cd build && \
    cmake .. && \
    make -j$(nproc)

EXPOSE 53/udp
EXPOSE 53/tcp

CMD ["./build/bin/basic_server"]
```

## 9. 故障排除

### 9.1 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 编译失败 | 依赖缺失 | 安装依赖 |
| 端口占用 | 端口被占用 | 更换端口 |
| 权限不足 | 低端口需要 root | 使用高端口或 sudo |
| 连接超时 | 防火墙 | 开放端口 |
| 内存泄漏 | 代码问题 | 使用 Valgrind |

### 9.2 日志分析

```bash
# 查看错误日志
grep ERROR dns.log

# 查看警告日志
grep WARN dns.log

# 统计查询
grep "Query:" dns.log | wc -l
```

### 9.3 性能分析

```bash
# 使用 perf 分析
perf record -g ./bin/basic_server
perf report

# 使用 gprof 分析
cmake -DCMAKE_BUILD_TYPE=Profile ..
make -j$(nproc)
./bin/basic_server
gprof ./bin/basic_server gmon.out > analysis.txt
```

## 10. 参考资料

### 10.1 RFC 文档

- [RFC 1034](https://tools.ietf.org/html/rfc1034) - Domain Names - Concepts and Facilities
- [RFC 1035](https://tools.ietf.org/html/rfc1035) - Domain Names - Implementation and Specification
- [RFC 1995](https://tools.ietf.org/html/rfc1995) - Incremental Zone Transfer
- [RFC 1996](https://tools.ietf.org/html/rfc1996) - A Mechanism for Prompt Notification of Zone Changes
- [RFC 2136](https://tools.ietf.org/html/rfc2136) - Dynamic Updates in the Domain Name System
- [RFC 2845](https://tools.ietf.org/html/rfc2845) - Secret Key Transaction Authentication for DNS
- [RFC 4034](https://tools.ietf.org/html/rfc4034) - Resource Records for the DNS Security Extensions
- [RFC 5936](https://tools.ietf.org/html/rfc5936) - DNS Zone Transfer Protocol
- [RFC 6891](https://tools.ietf.org/html/rfc6891) - Extension Mechanisms for DNS

### 10.2 在线资源

- [DNS Wiki](https://en.wikipedia.org/wiki/Domain_Name_System)
- [BIND Documentation](https://bind9.readthedocs.io/)
- [IANA DNS Parameters](https://www.iana.org/assignments/dns-parameters/dns-parameters.xhtml)

### 10.3 开源项目

- [BIND 9](https://gitlab.isc.org/isc-projects/bind9)
- [Unbound](https://github.com/NLnetLabs/unbound)
- [CoreDNS](https://github.com/coredns/coredns)
- [PowerDNS](https://github.com/PowerDNS/pdns)

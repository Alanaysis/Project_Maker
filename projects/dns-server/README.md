# DNS Server / DNS 服务器

> A learning project implementing a DNS server from scratch in Go, covering DNS protocol, caching, zone files, and recursive resolution.

---

## English

### Description

A DNS (Domain Name System) server implemented from scratch in Go for educational purposes. This project demonstrates the complete DNS protocol stack including packet encoding/decoding, domain name compression, resource record types, caching with TTL, zone file parsing, and recursive query resolution.

### Learning Objectives / 学习目标

**DNS Protocol Understanding:**
- DNS packet format (header, questions, answers, authority, additional sections)
- Domain name wire format and label compression
- Resource record types (A, AAAA, CNAME, MX, TXT, NS, SOA, PTR)
- Query/response flags and opcodes
- EDNS0 and extension mechanisms

**Implementation Skills:**
- Binary protocol encoding and decoding in Go
- Domain name compression (RFC 1035 section 4.1.4)
- TTL-based cache with eviction
- Zone file parsing (BIND format)
- Recursive query resolution
- Upstream DNS forwarding

### DNS Protocol Overview

The DNS protocol works as follows:

```
Client                     Server
  |                          |
  |---- Query (UDP 53) ---->|
  |                          |
  |<--- Response (UDP 53) ---|
```

**Packet Structure:**
```
+---------------------+
|        ID           |  Transaction identifier
+---------------------+
|   QR  Opcode   |AA |  Flags (16 bits)
|   TC  |RD|RA|   Z  |
+---------------------+
|       QDCount       |  Questions count
+---------------------+
|       ANCount       |  Answers count
+---------------------+
|       NSCount       |  Authority count
+---------------------+
|       ARCount       |  Additional count
+---------------------+
|       Questions     |
+---------------------+
|       Answers       |
+---------------------+
|      Authority      |
+---------------------+
|      Additional     |
+---------------------+
```

**Domain Name Wire Format:**
```
"www.example.com" -> [03 w w w 07 e x a m p l e 03 c o m 00]
```
Each label is prefixed with its length. A zero byte terminates the name.

**Label Compression:**
```
Pointer: [C0 offset] -> references name at 'offset' position
```

### Core Resolution Loop

```
DNS Query -> Protocol Parse -> Domain Lookup -> Cache -> Response
                              -> Zone Files
                              -> Upstream Forward
```

### How to Run Examples / 如何运行示例

```bash
# Navigate to the project directory
cd projects/dns-server

# Run example 1: DNS query and response demo
go run examples/01_query_response.go

# Run example 2: Caching demo
go run examples/02_caching.go

# Run example 3: Zone file loading demo
go run examples/03_zone_file.go

# Run example 4: Recursive resolution demo
go run examples/04_recursive_resolution.go

# Run all tests
go test ./tests/...

# Run tests with verbose output
go test -v ./tests/...

# Run tests with coverage
go test -cover ./tests/...
```

### Project Structure / 项目结构

```
dns-server/
├── go.mod              # Go module definition
├── README.md           # This file
├── src/                # Core library
│   ├── packet.go       # DNS packet format, encoding/decoding
│   ├── zone.go         # Zone file parsing and lookup
│   ├── resolver.go     # Resolver, forwarder, query handling
│   └── server.go       # DNS server implementation
├── examples/           # Demo programs
│   ├── 01_query_response.go    # Wire format demo
│   ├── 02_caching.go           # Cache behavior demo
│   ├── 03_zone_file.go         # Zone file parsing demo
│   └── 04_recursive_resolution.go  # Resolution demo
└── tests/              # Unit tests
    ├── packet_test.go
    ├── zone_test.go
    └── resolver_test.go
```

### DNS Record Types Implemented

| Type | Name | Description |
|------|------|-------------|
| A    | Address | IPv4 address (4 bytes) |
| AAAA | IPv6 Address | IPv6 address (16 bytes) |
| CNAME | Canonical Name | Domain alias |
| MX   | Mail Exchange | Mail server with preference |
| TXT  | Text | Arbitrary text data |
| NS   | Nameserver | Authoritative nameserver |
| SOA  | Start of Authority | Zone metadata |
| PTR  | Pointer | Reverse DNS lookup |

### DNS Caching

The DNS cache implements:
- TTL-based expiration (respects authoritative server's TTL)
- LRU eviction when cache is full
- Cache key: `name:type:class` (e.g., `www.example.com:A:IN`)
- Minimum TTL from all answer records

---

## 中文

### 项目描述

用 Go 从零实现的 DNS（域名系统）服务器，用于教学目的。本项目展示了完整的 DNS 协议栈，包括数据包编解码、域名压缩、资源记录类型、TTL 缓存、区域文件解析和递归查询解析。

### 学习目标

**理解 DNS 协议：**
- DNS 数据包格式（头部、问题、答案、授权、附加部分）
- 域名线格式和标签压缩
- 资源记录类型（A、AAAA、CNAME、MX、TXT、NS、SOA、PTR）
- 查询/响应标志和操作码
- EDNS0 扩展机制

**掌握实现技能：**
- Go 中的二进制协议编解码
- 域名压缩（RFC 1035 第 4.1.4 节）
- 基于 TTL 的缓存和驱逐
- 区域文件解析（BIND 格式）
- 递归查询解析
- 上游 DNS 转发

### DNS 协议概述

DNS 协议工作流程：

```
客户端                     服务器
  |                        |
  |---- 查询 (UDP 53) ---->|
  |                        |
  |<--- 响应 (UDP 53) -----|
```

**数据包结构：**
```
+---------------------+
|        ID           |  事务标识符
+---------------------+
|   QR  Opcode   |AA |  标志（16 位）
|   TC  |RD|RA|   Z  |
+---------------------+
|       QDCount       |  问题计数
+---------------------+
|       ANCount       |  答案计数
+---------------------+
|       NSCount       |  授权计数
+---------------------+
|       ARCount       |  附加计数
+---------------------+
|       问题区        |
+---------------------+
|       答案区        |
+---------------------+
|       授权区        |
+---------------------+
|       附加区        |
+---------------------+
```

**域名线格式：**
```
"www.example.com" -> [03 w w w 07 e x a m p l e 03 c o m 00]
```
每个标签前缀为其长度。零字节终止域名。

**标签压缩：**
```
指针: [C0 offset] -> 引用 'offset' 位置的名称
```

### 核心解析循环

```
DNS 查询 → 协议解析 → 域名查找 → 缓存 → 响应
                          → 区域文件
                          → 上游转发
```

### 运行示例

```bash
# 进入项目目录
cd projects/dns-server

# 运行示例 1：DNS 查询和响应演示
go run examples/01_query_response.go

# 运行示例 2：缓存演示
go run examples/02_caching.go

# 运行示例 3：区域文件加载演示
go run examples/03_zone_file.go

# 运行示例 4：递归解析演示
go run examples/04_recursive_resolution.go

# 运行所有测试
go test ./tests/...

# 详细输出运行测试
go test -v ./tests/...

# 运行测试并生成覆盖率
go test -cover ./tests/...
```

### 项目结构

```
dns-server/
├── go.mod              # Go 模块定义
├── README.md           # 本文件
├── src/                # 核心库
│   ├── packet.go       # DNS 数据包格式、编解码
│   ├── zone.go         # 区域文件解析和查找
│   ├── resolver.go     # 解析器、转发器、查询处理
│   └── server.go       # DNS 服务器实现
├── examples/           # 演示程序
│   ├── 01_query_response.go    # 线格式演示
│   ├── 02_caching.go           # 缓存行为演示
│   ├── 03_zone_file.go         # 区域文件解析演示
│   └── 04_recursive_resolution.go  # 解析演示
└── tests/              # 单元测试
    ├── packet_test.go
    ├── zone_test.go
    └── resolver_test.go
```

### 已实现的 DNS 记录类型

| 类型 | 名称 | 描述 |
|------|------|------|
| A    | 地址 | IPv4 地址（4 字节） |
| AAAA | IPv6 地址 | IPv6 地址（16 字节） |
| CNAME | 规范名称 | 域名别名 |
| MX   | 邮件交换 | 带优先级的邮件服务器 |
| TXT  | 文本 | 任意文本数据 |
| NS   | 名称服务器 | 权威名称服务器 |
| SOA  | 起始授权 | 区域元数据 |
| PTR  | 指针 | 反向 DNS 查找 |

### DNS 缓存

DNS 缓存实现：
- 基于 TTL 的过期（遵循权威服务器的 TTL）
- 缓存满时的 LRU 驱逐
- 缓存键：`name:type:class`（例如 `www.example.com:A:IN`）
- 所有答案记录中的最小 TTL

---

## References / 参考资料

- [RFC 1035 - DNS](https://tools.ietf.org/html/rfc1035)
- [RFC 2181 - Clarifications to DNS](https://tools.ietf.org/html/rfc2181)
- [RFC 2671 - EDNS0](https://tools.ietf.org/html/rfc2671)
- [CoreDNS](https://coredns.io/)
- [miekg/dns](https://github.com/miekg/dns)

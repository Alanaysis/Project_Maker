# 🌐 网络服务模块

> 5 个深度学习项目，涵盖高可用、MCP、VPN、CDN、防火墙

---

## 📋 项目列表

| 项目 | 描述 | 技术栈 | 难度 | 状态 |
|------|------|--------|------|------|
| [ha-server](ha-server/) | 高可用服务器 | C++ | ⭐⭐⭐⭐⭐ | ✅ |
| [mcp-server](mcp-server/) | MCP 服务端 | Rust | ⭐⭐⭐⭐ | ✅ |
| [vpn-software](vpn-software/) | VPN 软件 | Rust | ⭐⭐⭐⭐⭐ | ✅ |
| [cdn-service](cdn-service/) | CDN 服务 | Go | ⭐⭐⭐ | ✅ |
| [firewall](firewall/) | 防火墙 | C | ⭐⭐⭐⭐⭐ | ✅ |

---

## 🎯 学习路径

```
高可用服务器 → MCP 协议 → VPN 加密 → CDN 缓存 → 防火墙
      ↓           ↓           ↓           ↓           ↓
   负载均衡     JSON-RPC    隧道加密     缓存策略     包过滤
   健康检查     工具注册     密钥交换     回源机制     状态检测
   连接池       请求路由     TUN设备      调度算法     入侵检测
```

### 推荐学习顺序

1. **ha-server** (高可用)
   - 学习负载均衡算法（轮询、加权、最少连接）
   - 理解健康检查和故障转移
   - 掌握连接池管理

2. **mcp-server** (MCP 协议)
   - 学习 MCP 协议规范
   - 理解 JSON-RPC 通信
   - 掌握工具注册和调用

3. **vpn-software** (VPN)
   - 学习 VPN 协议（WireGuard 风格）
   - 理解加密算法（ChaCha20-Poly1305、X25519）
   - 掌握 TUN 设备管理

4. **cdn-service** (CDN)
   - 学习 LRU 缓存算法
   - 理解回源机制
   - 掌握智能调度

5. **firewall** (防火墙)
   - 学习包过滤规则
   - 理解状态检测
   - 掌握入侵检测

---

## 🔧 技术栈

| 技术 | 用途 | 学习资源 |
|------|------|----------|
| **C++** | 高可用服务器 | [C++ 官方文档](https://en.cppreference.com/) |
| **Rust** | MCP、VPN | [Rust 官方文档](https://doc.rust-lang.org/) |
| **Go** | CDN 服务 | [Go 官方文档](https://go.dev/doc/) |
| **C** | 防火墙 | [C 官方文档](https://en.cppreference.com/w/c) |
| **OpenSSL** | 加密库 | [OpenSSL 文档](https://www.openssl.org/docs/) |

---

## 📊 项目详情

### 1. ha-server (高可用)

**核心功能**：
- 3 种负载均衡算法（轮询、加权轮询、最少连接）
- 健康检查（TCP 检查、故障检测、自动恢复）
- 连接池管理（连接复用、超时清理）
- HTTP 解析器（HTTP/1.1、分块解析）
- 事件驱动架构（epoll、非阻塞 I/O）

**代码量**：约 30 个文件

**快速开始**：
```bash
cd ha-server
mkdir build && cd build
cmake ..
make
./ha_server_example
```

---

### 2. mcp-server (MCP 协议)

**核心功能**：
- JSON-RPC 2.0 协议完整实现
- MCP 协议核心方法（initialize、tools/list、tools/call）
- 动态工具注册和发现机制
- 异步工具执行（async trait）

**代码量**：约 15 个文件

**快速开始**：
```bash
cd mcp-server
cargo build
cargo test
cargo run
```

---

### 3. vpn-software (VPN)

**核心功能**：
- 加密模块（X25519 密钥交换、ChaCha20-Poly1305 加密）
- 协议模块（WireGuard 风格协议）
- 隧道模块（VPN 隧道生命周期管理）
- TUN 设备管理（虚拟网络接口、路由管理）

**代码量**：约 20 个文件

**快速开始**：
```bash
cd vpn-software
cargo build
cargo test
cargo run --example simple_vpn
```

---

### 4. cdn-service (CDN)

**核心功能**：
- LRU 缓存算法（双向链表+哈希表）
- 缓存管理器（TTL、过期清理、统计）
- 回源机制（重试、超时、连接池）
- 智能调度（轮询、加权轮询、最少连接）

**代码量**：约 24 个文件

**快速开始**：
```bash
cd cdn-service
go mod tidy
go build -o bin/cdn-server cmd/cdn-server/main.go
./bin/cdn-server -addr :8080 -origin http://localhost:9090
```

---

### 5. firewall (防火墙)

**核心功能**：
- 包解析模块（以太网、IP、TCP、UDP、ICMP）
- 规则引擎（协议、IP CIDR、端口过滤）
- 状态管理（TCP 连接状态跟踪、超时管理）
- 入侵检测（SYN Flood、端口扫描、异常包检测）

**代码量**：约 37 个文件

**快速开始**：
```bash
cd firewall
chmod +x build.sh
./build.sh build
```

---

## 📚 学习资源

### 书籍
- 《UNIX 网络编程》
- 《TCP/IP 详解》
- 《高性能网络编程》

### 课程
- [Stanford CS144](https://cs144.github.io/)
- [MIT 6.829](https://css.csail.mit.edu/6.829/)

### 开源项目
- [Nginx](https://github.com/nginx/nginx)
- [HAProxy](https://github.com/haproxy/haproxy)
- [WireGuard](https://github.com/WireGuard)

---

## 🔗 相关链接

- [返回主 README](../README.md)
- [学习路径图](../LEARNING_PATHS.md)
- [项目索引](../PROJECT_INDEX.md)

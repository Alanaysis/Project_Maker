# 🌐 网络服务模块

> 11 个项目，涵盖高可用、MCP、VPN、CDN、防火墙、渗透测试、RPC、服务发现、熔断降级、MQTT、边缘计算

---

## 📋 项目列表

| 项目 | 描述 | 技术栈 | 难度 | 状态 |
|------|------|--------|------|------|
| [ha-server](ha-server/) | 高可用服务器 | C++ | ⭐⭐⭐⭐⭐ | ✅ |
| [mcp-server](mcp-server/) | MCP 服务端 | Rust | ⭐⭐⭐⭐ | ✅ |
| [vpn-software](vpn-software/) | VPN 软件 | Rust | ⭐⭐⭐⭐⭐ | ✅ |
| [cdn-service](cdn-service/) | CDN 服务 | Go | ⭐⭐⭐ | ✅ |
| [firewall](firewall/) | 防火墙 | C | ⭐⭐⭐⭐⭐ | ✅ |
| [pentest-tools](pentest-tools/) | 渗透测试工具集 | Python | ⭐⭐⭐⭐ | ✅ |
| [simple-rpc](simple-rpc/) | 简易 RPC 框架 | Go | ⭐⭐⭐⭐ | ✅ |
| [service-discovery](service-discovery/) | 服务发现系统 | Go | ⭐⭐⭐⭐ | ✅ |
| [circuit-breaker](circuit-breaker/) | 熔断降级 | Go | ⭐⭐⭐ | ✅ |
| [mqtt-broker](mqtt-broker/) | MQTT 消息代理 | Go | ⭐⭐⭐⭐ | ✅ |
| [device-management](device-management/) | 设备管理系统 | Go | ⭐⭐⭐⭐ | ✅ |
| [edge-computing](edge-computing/) | 边缘计算框架 | Python | ⭐⭐⭐⭐ | ✅ |

---

## 🎯 学习路径

```
高可用服务器 → MCP 协议 → VPN 加密 → CDN 缓存 → 防火墙 → 渗透测试
      ↓           ↓           ↓           ↓           ↓           ↓
   负载均衡     JSON-RPC    隧道加密     缓存策略     包过滤     端口扫描
   健康检查     工具注册     密钥交换     回源机制     状态检测   漏洞检测
   连接池       请求路由     TUN设备      调度算法     入侵检测   报告生成
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

6. **pentest-tools** (渗透测试)
   - 学习端口扫描和服务识别
   - 理解常见漏洞类型
   - 掌握漏洞检测和报告生成

7. **simple-rpc** (RPC 框架)
   - 学习 RPC 调用流程和序列化
   - 理解服务注册与发现
   - 掌握负载均衡和超时处理

8. **service-discovery** (服务发现)
   - 学习服务注册与 TTL 租约
   - 理解健康检查（TCP/HTTP）
   - 掌握服务发现与负载均衡

9. **circuit-breaker** (熔断降级)
   - 学习熔断器状态机（关闭→打开→半开）
   - 理解故障检测和优雅降级
   - 掌握指标统计和恢复机制

10. **mqtt-broker** (MQTT 消息代理)
    - 学习 MQTT 3.1.1 协议
    - 理解 QoS 0/1/2 服务质量
    - 掌握发布/订阅模式和遗嘱消息

11. **device-management** (设备管理)
    - 学习设备生命周期管理
    - 理解设备注册和状态上报
    - 掌握远程控制和设备分组

12. **edge-computing** (边缘计算)
    - 学习边缘计算核心概念
    - 理解任务卸载策略
    - 掌握资源调度和负载均衡

---

## 🔧 技术栈

| 技术 | 用途 | 学习资源 |
|------|------|----------|
| **C++** | 高可用服务器 | [C++ 官方文档](https://en.cppreference.com/) |
| **Rust** | MCP、VPN | [Rust 官方文档](https://doc.rust-lang.org/) |
| **Go** | CDN 服务 | [Go 官方文档](https://go.dev/doc/) |
| **C** | 防火墙 | [C 官方文档](https://en.cppreference.com/w/c) |
| **Python** | 渗透测试 | [Python 官方文档](https://docs.python.org/3/) |
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

**代码量**：约 37 个文件（C 实现）+ 约 20 个文件（Python 实现）

**快速开始**：

C 语言实现：
```bash
cd firewall
chmod +x build.sh
./build.sh build
```

Python 实现：
```bash
cd firewall/python
pip install -r requirements.txt
pytest tests/ -v
python examples/basic_firewall.py
```

---

---

### 6. pentest-tools (渗透测试)

**核心功能**：
- 端口扫描器（TCP连接扫描、多线程并发、速率限制）
- 服务识别器（Banner抓取、指纹匹配、版本提取）
- 漏洞扫描器（已知漏洞数据库、弱密码检测、配置检查）
- 报告生成器（JSON、HTML、TXT格式、修复建议）

**代码量**：约 20 个文件

**快速开始**：
```bash
cd pentest-tools
pip install -r requirements.txt
python3 -m pytest tests/ -v
python3 examples/scan_example.py --demo
```

---

### 7. simple-rpc (RPC 框架)

**核心功能**：
- RPC 调用流程（客户端→序列化→网络传输→反序列化→服务端处理）
- 多种序列化格式（JSON、Protocol Buffers）
- 服务注册与发现
- 多种负载均衡策略（随机、轮询、加权、最少连接）
- 超时处理和熔断器

**代码量**：约 15 个文件

**快速开始**：
```bash
cd simple-rpc
go mod tidy
go run cmd/server/main.go -addr localhost:8080 -service Calculator
go run cmd/client/main.go -service Calculator -balancer round_robin
```

---

### 8. service-discovery (服务发现)

**核心功能**：
- 服务注册（TTL 租约机制）
- 健康检查（TCP、HTTP 探测）
- 服务发现（Watch 机制、本地缓存）
- 负载均衡（Round Robin、Random、Weighted）

**代码量**：约 10 个文件

**快速开始**：
```bash
cd service-discovery
go build -o service-discovery ./cmd/server
./service-discovery
curl -X POST http://localhost:8500/register -H "Content-Type: application/json" -d '{"id":"svc-1","name":"user-service","address":"10.0.0.1","port":8080}'
```

---

### 9. circuit-breaker (熔断降级)

**核心功能**：
- 熔断器状态机（关闭→打开→半开）
- 失败率统计和阈值配置
- 优雅降级策略
- 自动恢复机制

**代码量**：约 6 个文件

**快速开始**：
```bash
cd circuit-breaker
go test ./tests/...
```

---

### 10. mqtt-broker (MQTT 消息代理)

**核心功能**：
- MQTT 3.1.1 协议完整实现
- QoS 0/1/2 三种服务质量
- 发布/订阅模式
- 遗嘱消息（Last Will and Testament）
- 主题通配符（+、#）

**代码量**：约 6 个文件

**快速开始**：
```bash
cd mqtt-broker
go build -o mqtt-broker ./cmd
./mqtt-broker
go test ./tests/ -v
```

---

### 11. device-management (设备管理)

**核心功能**：
- 设备注册与认证（生成唯一设备ID、身份验证）
- 设备状态管理（电量、信号、固件版本、IP地址）
- 远程控制（命令下发、命令执行跟踪）
- 设备分组管理（按类型、区域、功能分组）
- 事件通知（设备注册、状态更新、设备删除事件）

**代码量**：约 8 个文件

**快速开始**：
```bash
cd device-management
go mod tidy
go run cmd/server/main.go
go test ./... -v
```

---

### 12. edge-computing (边缘计算)

**核心功能**：
- 边缘节点管理
- 任务分发和调度
- 结果收集和聚合
- 多种负载均衡算法

**代码量**：约 10 个文件

**快速开始**：
```bash
cd edge-computing
python3 -m pytest tests/ -v
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

# 防火墙 (Firewall)

> 实现一个网络防火墙，支持包过滤、状态检测、入侵检测

## 项目概述

本项目是一个从零实现的网络防火墙系统，基于 Linux Netfilter 框架，使用 C 语言开发。通过本项目，你将深入理解网络协议、包过滤机制和状态检测技术。

## 学习目标

- ⭐ **理解网络协议和包结构**：深入学习 IP、TCP、UDP、ICMP 等协议的报文格式
- ⭐ **掌握 Netfilter 框架**：理解 Linux 内核的包过滤机制和钩子函数
- ⭐ **学会规则匹配和状态管理**：实现高效的规则匹配算法和连接状态跟踪
- 💡 **理解防火墙设计哲学**：从安全性和性能的角度思考防火墙架构

## 技术栈

| 技术 | 学习难度 | 说明 |
|------|----------|------|
| C 语言 | ⭐⭐⭐ | 系统编程语言，需要扎实的基础 |
| Linux Netfilter | ⭐⭐⭐⭐ | 内核级网络框架，理解有一定难度 |
| libnetfilter_queue | ⭐⭐⭐ | 用户态包队列库 |
| libpcap | ⭐⭐ | 数据包捕获库 |
| iptables/nftables | ⭐⭐⭐ | 命令行防火墙工具 |

## 核心功能

### 1. 包过滤 (Packet Filtering)
- 基于源/目的 IP 地址过滤
- 基于源/目的端口过滤
- 基于协议类型过滤 (TCP/UDP/ICMP)
- 支持通配符和 CIDR 表示法

### 2. 状态检测 (Stateful Inspection)
- TCP 连接状态跟踪 (SYN, SYN-ACK, ESTABLISHED, FIN)
- UDP "连接" 跟踪
- ICMP 请求/响应匹配
- 连接超时管理

### 3. 入侵检测 (Intrusion Detection)
- SYN Flood 检测
- 端口扫描检测
- 异常包大小检测
- 基于规则的告警

### 4. 日志记录 (Logging)
- 详细的包日志
- 规则匹配日志
- 告警日志
- 支持文件和 syslog 输出

## 核心循环

```
数据包捕获 → 规则匹配 → 状态检测 → 动作执行 → 日志记录
     ↑                                              |
     └──────────────────────────────────────────────┘
```

## 项目结构

```
firewall/
├── README.md                 # 项目说明
├── LEARNING_NOTES.md         # 学习笔记模板
├── Makefile                  # 构建脚本
├── docs/                     # 文档目录
│   ├── 01-RESEARCH.md       # 市场调研
│   ├── 02-REQUIREMENTS.md   # 需求分析
│   ├── 03-DESIGN.md         # 技术设计
│   ├── 04-PRODUCT.md        # 产品思维
│   └── 05-DEVELOPMENT.md    # 开发手册
├── include/                  # 头文件
│   ├── firewall.h           # 主头文件
│   ├── packet.h             # 包解析
│   ├── rules.h              # 规则引擎
│   ├── state.h              # 状态管理
│   ├── logger.h             # 日志模块
│   └── ids.h                # 入侵检测
├── src/                      # 源代码
│   ├── main.c               # 主程序
│   ├── packet.c             # 包解析实现
│   ├── rules.c              # 规则引擎实现
│   ├── state.c              # 状态管理实现
│   ├── logger.c             # 日志模块实现
│   └── ids.c                # 入侵检测实现
├── tests/                    # 测试代码
│   ├── test_packet.c        # 包解析测试
│   ├── test_rules.c         # 规则引擎测试
│   └── test_state.c         # 状态管理测试
├── examples/                 # 示例程序
│   ├── simple_filter.c      # 简单过滤示例
│   └── example.conf         # 示例配置
└── configs/                  # 配置文件
    └── default.conf         # 默认配置
```

## 快速开始

### 环境要求

- Linux 操作系统 (推荐 Ubuntu 20.04+)
- GCC 编译器
- libnetfilter-queue-dev
- libpcap-dev

### 安装依赖

```bash
# Ubuntu/Debian
sudo apt-get install libnetfilter-queue-dev libpcap-dev

# CentOS/RHEL
sudo yum install libnetfilter_queue-devel libpcap-devel
```

### 编译运行

```bash
# 编译
make

# 运行 (需要 root 权限)
sudo ./build/firewall -c configs/default.conf

# 运行测试
make test
```

## ⭐ 重点难点

### 1. Netfilter 钩子机制
理解 `NF_INET_PRE_ROUTING`, `NF_INET_LOCAL_IN`, `NF_INET_FORWARD`, `NF_INET_LOCAL_OUT`, `NF_INET_POST_ROUTING` 五个钩子点的作用。

### 2. 状态检测算法
实现高效的连接状态跟踪，处理 TCP 状态机的各种转换。

### 3. 规则匹配优化
如何高效地匹配大量规则，避免线性扫描的性能问题。

### 4. 并发处理
多线程环境下的数据同步和竞态条件处理。

## 💡 值得思考

1. **为什么选择 Netfilter 而不是 raw socket？**
   - Netfilter 提供了内核级的包拦截能力
   - 可以实现真正的防火墙功能（阻止/放行）
   - 性能更好，减少了用户态/内核态切换

2. **无状态 vs 有状态防火墙？**
   - 无状态：简单但安全性低
   - 有状态：复杂但更安全，能检测连接状态

3. **规则匹配的性能优化？**
   - 如何避免每包都遍历所有规则？
   - 是否可以使用数据结构（如 Trie、哈希表）加速？

4. **入侵检测的准确性？**
   - 如何降低误报率？
   - 如何处理加密流量？

## 参考项目

- [iptables](https://netfilter.org/iptables/) - 经典的 Linux 防火墙工具
- [nftables](https://netfilter.org/projects/nftables/) - iptables 的继任者
- [Suricata](https://suricata.io/) - 高性能入侵检测系统
- [libnetfilter_queue](https://netfilter.org/projects/libnetfilter_queue/) - 用户态包队列库
- [Snort](https://www.snort.org/) - 开源入侵检测系统

## 资源链接

### 文档
- [Netfilter 官方文档](https://www.netfilter.org/documentation.html)
- [Linux 内核网络文档](https://www.kernel.org/doc/html/latest/networking/)
- [libnetfilter_queue API](https://netfilter.org/projects/libnetfilter_queue/doxygen/)

### 教程
- [Linux Firewall Tutorial](https://www.booleanworld.com/depth-guide-iptables-linux-firewall/)
- [Netfilter Hooks](https://wiki.nftables.org/wiki-nftables/index.php/Netfilter_hooks)

### 书籍
- 《Linux 防火墙》(Linux Firewalls: Attack Detection and Response)
- 《网络安全监控》(Network Security Monitoring)

## 许可证

MIT License

## 作者

学习项目 - 用于理解防火墙原理和实现

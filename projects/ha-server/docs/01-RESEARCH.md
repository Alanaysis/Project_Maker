# 01 - 市场调研

## 调研目的

在实现高可用服务器框架之前，需要深入分析业界成熟的开源项目，理解它们的架构设计、技术选型和发力方向。

## 一、主流开源项目分析

### 1. Nginx

| 维度 | 描述 |
|------|------|
| GitHub | https://github.com/nginx/nginx |
| 语言 | C |
| Stars | 25k+ |
| 定位 | Web 服务器 + 反向代理 + 负载均衡器 |
| 架构 | 事件驱动、异步非阻塞 I/O |
| 进程模型 | Master-Worker 多进程 |

**核心特性：**
- ⭐ 事件驱动架构：单线程处理数千并发连接
- 模块化设计：丰富的第三方模块生态
- 热加载：支持不停机配置更新
- 高性能静态文件服务

**发力方向：**
- 传统 Web 服务器和反向代理
- CDN 边缘节点
- Kubernetes Ingress Controller

**值得学习：**
- 事件循环的实现方式
- 内存池管理策略
- 模块化架构设计

### 2. HAProxy

| 维度 | 描述 |
|------|------|
| GitHub | https://github.com/haproxy/haproxy |
| 语言 | C |
| Stars | 5k+ |
| 定位 | 专业负载均衡器和代理服务器 |
| 架构 | 事件驱动、单线程/多线程 |
| 协议 | TCP (L4) + HTTP (L7) |

**核心特性：**
- ⭐ 细粒度的 ACL 路由规则
- 丰富的健康检查机制（TCP/HTTP/自定义脚本）
- Stick Table 会话保持
- Runtime API 动态管理

**发力方向：**
- 企业级负载均衡
- 微服务网关
- 数据库代理

**值得学习：**
- 连接管理的精细控制
- 健康检查的多种模式
- ACL 规则引擎设计

### 3. Envoy

| 维度 | 描述 |
|------|------|
| GitHub | https://github.com/envoyproxy/envoy |
| 语言 | C++ |
| Stars | 25k+ |
| 定位 | 云原生 L4/L7 代理 |
| 架构 | 多线程事件驱动 |
| 特点 | xDS 动态配置 API |

**核心特性：**
- ⭐ xDS 动态配置：无需重启即可更新配置
- 丰富的可观测性：内置统计、追踪、日志
- 原生 gRPC 支持
- 多协议支持：HTTP/1.1, HTTP/2, HTTP/3, gRPC, TCP

**发力方向：**
- 服务网格数据面（Istio, Consul Connect）
- 云原生基础设施
- 边缘代理

**值得学习：**
- 多线程事件驱动模型
- xDS 配置管理架构
- 可观测性设计

## 二、技术变体和演进路径

### 演进时间线

```
传统负载均衡 (L4)        应用层代理 (L7)         服务网格 (Service Mesh)
    │                        │                         │
    ▼                        ▼                         ▼
  LVS (Linux)            Nginx/HAP                Envoy/Linkerd
  IPVS                   反向代理                  Sidecar 模式
  硬件 F5                URL 路由                  xDS API
                         会话保持                  mTLS
```

### 技术路线对比

| 路线 | 代表项目 | 优势 | 劣势 |
|------|----------|------|------|
| C 事件驱动 | Nginx, HAProxy | 极致性能、资源占用低 | 开发难度大、扩展性有限 |
| C++ 现代化 | Envoy | 动态配置、可观测性强 | 复杂度高、资源占用较大 |
| Go 云原生 | Traefik, Linkerd | 开发效率高、容器友好 | 性能略逊于 C/C++ |
| Rust 新锐 | Pingora (Cloudflare) | 内存安全、性能优异 | 生态较新 |

### 2024-2025 行业趋势

1. **服务网格普及**：Envoy 成为服务网格标准数据面
2. **eBPF 网络**：Cilium 使用 eBPF 实现内核级负载均衡
3. **HTTP/3 (QUIC)**：新一代传输协议逐步落地
4. **AI 驱动的负载均衡**：基于机器学习的智能路由决策
5. **边缘计算**：CDN 边缘节点集成更多代理功能

## 三、本项目定位

### 学习目标

本项目不是要替代 Nginx 或 Envoy，而是通过从零实现一个简化版本来：
- 深入理解高可用架构的核心原理
- 掌握负载均衡算法的实现细节
- 理解健康检查和故障转移的机制
- 学习高性能网络编程技术

### 技术选型理由

| 决策 | 选择 | 理由 |
|------|------|------|
| 语言 | C++ | 学习价值高、性能关键 |
| 网络模型 | epoll | Linux 标准、Nginx/HAProxy 使用 |
| 线程模型 | 线程池 | 简化并发管理 |
| 配置 | JSON | 易读易解析 |

### 差异化

与现有项目相比，本项目：
- 专注于教学和学习，代码注释详尽
- 从最基础的 socket 编程开始
- 逐步迭代，每个版本都可运行
- 包含完整的学习笔记和思考题

## 四、参考资源

### 官方文档
- [Nginx Development Guide](https://nginx.org/en/docs/dev/development_guide.html)
- [HAProxy Architecture](https://www.haproxy.com/documentation/haproxy-architecture/)
- [Envoy Architecture](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/)

### 技术博客
- [The Architecture of Open Source Applications](https://aosabook.org/en/)
- [High Scalability](http://highscalability.com/)
- [The Morning Paper](https://blog.acolyer.org/)

### 开源项目
- [Pingora - Cloudflare 的 Rust 代理](https://github.com/cloudflare/pingora)
- [Caddy - Go Web 服务器](https://github.com/caddyserver/caddy)
- [Traefik - 云原生反向代理](https://github.com/traefik/traefik)

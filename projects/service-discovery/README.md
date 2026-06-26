# Service Discovery / 服务发现

> 从零实现服务发现系统，包含服务注册、健康检查、服务发现和负载均衡。

A service discovery system implemented from scratch, covering service registration, health checking, service discovery, and load balancing.

---

## 目录 / Contents

- [概述 / Overview](#概述--overview)
- [学习目标 / Learning Objectives](#学习目标--learning-objectives)
- [架构 / Architecture](#架构--architecture)
- [核心概念 / Core Concepts](#核心概念--core-concepts)
- [项目结构 / Project Structure](#项目结构--project-structure)
- [快速开始 / Quick Start](#快速开始--quick-start)
- [运行示例 / Running Examples](#运行示例--running-examples)
- [运行测试 / Running Tests](#运行测试--running-tests)
- [服务发现原理 / How Service Discovery Works](#服务发现原理--how-service-discovery-works)
- [负载均衡算法 / Load Balancing Algorithms](#负载均衡算法--load-balancing-algorithms)

---

## 概述 / Overview

**一句话描述 / Description**: 实现一个服务发现系统，包含服务注册、健康检查、服务发现和负载均衡。

**一句话描述 / Description**: Implement a service discovery system with service registration, health checking, discovery, and load balancing.

**核心循环 / Core Loop**:

```
服务注册 → 健康检查 → 服务发现 → 负载均衡
Service Registration → Health Check → Service Discovery → Load Balancing
```

---

## 学习目标 / Learning Objectives

### 中文

- **理解服务发现**: 掌握服务注册、发现、健康检查的核心原理
- **掌握健康检查**: 实现 TCP、HTTP 和自定义健康检查机制
- **学会负载均衡**: 实现轮询、加权、最少连接和随机负载均衡算法
- **理解 TTL 过期机制**: 掌握基于 TTL 的服务实例过期管理
- **了解分布式协调**: 实现 Consul-like KV 存储用于分布式协调

### English

- **Understand Service Discovery**: Master the core principles of service registration, discovery, and health checking
- **Master Health Checking**: Implement TCP, HTTP, and custom health check mechanisms
- **Learn Load Balancing**: Implement round-robin, weighted, least-connections, and random algorithms
- **Understand TTL Expiration**: Manage service instance expiration based on TTL
- **Learn Distributed Coordination**: Implement Consul-like KV store for distributed coordination

---

## 架构 / Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       Service Broker                            │
│  (Main Orchestrator / 主要协调器)                               │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │  Service      │  │  Health      │  │  Discovery       │    │
│  │  Registry     │  │  Checker     │  │  Cache           │    │
│  │              │  │              │  │                  │    │
│  │  - Register   │  │  - TCP       │  │  - Cache         │    │
│  │  - Deregister │  │  - HTTP      │  │  - TTL           │    │
│  │  - Lookup     │  │  - Custom    │  │  - Refresh       │    │
│  └──────────────┘  └──────────────┘  └──────────────────┘    │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐                   │
│  │  Load Balancer   │  │  Consul-like     │                   │
│  │                  │  │  KV Store        │                   │
│  │  - Round Robin   │  │                  │                   │
│  │  - Weighted      │  │  - Put/Get       │                   │
│  │  - Least Conn    │  │  - CAS           │                   │
│  │  - Random        │  │  - List/Prefix   │                   │
│  └──────────────────┘  └──────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 核心概念 / Core Concepts

### 服务注册 / Service Registration

服务实例启动时向注册中心注册自己的信息（地址、端口、元数据、TTL）。

**Registration Flow / 注册流程**:

```
1. Service starts
2. Create ServiceInstance {ID, Service, Address, Port, Metadata, TTL}
3. Registry.Register(instance)
4. Registry stores instance in memory
5. Health check registered for instance
6. KV store synced (if enabled)
```

### 健康检查 / Health Checking

定期检查服务实例是否健康，只有健康的实例才会被分配到流量。

**Health Check Types / 健康检查类型**:

| 类型 | 说明 | 适用场景 |
|------|------|----------|
| TCP | 尝试建立 TCP 连接 | 任何 TCP 服务 |
| HTTP | 请求 HTTP 健康端点 | Web 服务 |
| Custom | 自定义检查函数 | 特殊需求 |

### 服务发现 / Service Discovery

客户端通过服务名称查询可用的健康实例列表。

**Discovery Flow / 发现流程**:

```
1. Client queries for "user-service"
2. Registry returns all healthy instances
3. Load balancer selects one instance
4. Client connects to the selected instance
```

### 负载均衡 / Load Balancing

将请求分发到多个服务实例，避免单点过载。

**Strategies / 策略**:

| 算法 | 说明 | 适用场景 |
|------|------|----------|
| 轮询 (Round Robin) | 按顺序轮流分配 | 实例能力相同 |
| 加权 (Weighted) | 按权重分配 | 实例能力不同 |
| 最少连接 (Least Connections) | 分配给连接数最少的实例 | 请求时长不均 |
| 随机 (Random) | 随机选择 | 简单场景 |

---

## 项目结构 / Project Structure

```
service-discovery/
├── go.mod                    # Go module definition
├── README.md                 # This file
├── src/                      # Core package
│   ├── main.go               # Entry point
│   ├── types.go              # Core types (ServiceInstance, HealthCheck, etc.)
│   ├── registry.go           # Service registry implementation
│   ├── healthcheck.go        # Health checker implementation
│   ├── loadbalancer.go       # Load balancer implementation
│   └── broker.go             # Service broker (orchestrator)
├── examples/                 # Demo programs
│   ├── register_discover.go  # Service registration and discovery
│   ├── health_check.go       # Health check demonstration
│   ├── load_balance.go       # Load balancing demonstration
│   └── failure_recovery.go   # Service failure and recovery
└── tests/                    # Unit tests
    ├── registry_test.go      # Registry and type tests
    ├── loadbalancer_test.go  # Load balancer tests
    └── kv_store_test.go      # KV store and cache tests
```

---

## 快速开始 / Quick Start

### 前置条件 / Prerequisites

- Go 1.21+
- No external dependencies required

### 编译 / Build

```bash
cd projects/service-discovery
go build ./src/
```

---

## 运行示例 / Running Examples

### 1. 服务注册与发现 / Service Registration & Discovery

```bash
cd projects/service-discovery
go run examples/register_discover.go
```

**演示 / Demonstrates**:
- 注册多个服务实例
- 查询可用实例
- 获取负载均衡的实例

### 2. 健康检查 / Health Check

```bash
go run examples/health_check.go
```

**演示 / Demonstrates**:
- TCP 健康检查
- HTTP 健康检查
- 自定义健康检查
- 服务故障检测和恢复

### 3. 负载均衡 / Load Balancing

```bash
go run examples/load_balance.go
```

**演示 / Demonstrates**:
- 轮询算法
- 加权算法
- 最少连接算法
- 随机算法

### 4. 服务故障与恢复 / Service Failure & Recovery

```bash
go run examples/failure_recovery.go
```

**演示 / Demonstrates**:
- 服务注册
- 正常操作
- 模拟服务故障
- 故障检测
- 服务恢复
- 服务注销

---

## 运行测试 / Running Tests

```bash
cd projects/service-discovery
go test ./tests/... -v
```

---

## 服务发现原理 / How Service Discovery Works

### 为什么需要服务发现 / Why Service Discovery

在微服务架构中，服务实例的数量和位置是动态变化的。服务发现解决了以下问题：

1. **服务定位**: 客户端如何找到服务的实例？
2. **故障转移**: 当实例故障时，如何自动切换？
3. **负载均衡**: 如何将请求分发到多个实例？
4. **弹性伸缩**: 如何自动处理实例的增加和减少？

### 注册中心模式 / Registry Pattern

```
┌──────────┐     ┌────────────┐     ┌──────────┐
│ Service A │────▶│ Registry   │────▶│ Service B │
│ (Client)  │◀────│ (Server)   │◀────│ (Server)  │
└──────────┘     └────────────┘     └──────────┘
                      │
                      ▼
              ┌────────────┐
              │ Health     │
              │ Checker    │
              └────────────┘
```

### TTL 机制 / TTL Mechanism

每个服务实例注册时都有一个 TTL（Time-To-Live）。如果实例在 TTL 时间内没有刷新（心跳），注册中心会认为实例已失效并自动移除。

```
Instance registered at T=0, TTL=30s

T=0   Instance registered, LastUpdate = T=0
T=10  Heartbeat, LastUpdate = T=10
T=20  Heartbeat, LastUpdate = T=20
T=30  No heartbeat → Instance expired!
```

---

## 负载均衡算法 / Load Balancing Algorithms

### 轮询 / Round Robin

按顺序轮流分配请求到每个实例。

```
实例: [A, B, C]
请求 1 -> A
请求 2 -> B
请求 3 -> C
请求 4 -> A (循环)
```

**优点**: 简单、公平
**缺点**: 不考虑实例容量和当前负载

### 加权 / Weighted

根据实例的权重分配请求，权重高的实例获得更多流量。

```
实例: A(weight=3), B(weight=2), C(weight=1)
平均 6 个请求的分配:
A: 3 个请求 (50%)
B: 2 个请求 (33%)
C: 1 个请求 (17%)
```

**优点**: 考虑实例容量差异
**缺点**: 需要手动配置权重

### 最少连接 / Least Connections

将请求分配给当前连接数最少的实例。

```
实例: A(10 connections), B(3 connections), C(7 connections)
下一个请求 -> B (最少连接)
```

**优点**: 自适应负载，适合不均匀请求
**缺点**: 需要跟踪连接数

### 随机 / Random

随机选择一个实例。

```
实例: [A, B, C]
请求 1 -> B
请求 2 -> A
请求 3 -> C
请求 4 -> A
```

**优点**: 最简单，无状态
**缺点**: 可能不均匀

---

## 扩展阅读 / Further Reading

- [Consul Service Discovery](https://www.consul.io/docs/service-discovery) - HashiCorp 的服务发现实现
- [Etcd](https://etcd.io/) - 分布式键值存储
- [Nginx Load Balancing](https://nginx.org/en/docs/http/load_balancing.html) - Nginx 负载均衡
- [Microservices Patterns](https://microservices.io/patterns/microservices.html) - 微服务架构模式

---

## 技术栈 / Tech Stack

- **语言 / Language**: Go
- **框架 / Framework**: None (纯 Go 标准库)
- **测试 / Testing**: Go testing 标准库

---

## 许可证 / License

MIT License

# 容器编排

一个简易的容器编排系统实现，用于学习容器编排的核心概念。

## 项目简介

本项目实现了一个简易的容器编排系统，包含以下核心功能：

- **容器调度**：支持多种调度策略（Bin Packing、Spread、Round Robin）
- **服务发现**：服务注册、端点管理、服务解析
- **健康检查**：HTTP 健康检查、健康状态管理
- **扩缩容**：自动扩缩容、手动扩缩容、冷却时间控制

## 核心循环

```
容器定义 → 调度 → 部署 → 监控 → 扩缩容
```

## 功能特性

### 1. 容器调度
- **Bin Packing**：紧凑调度，提高资源利用率
- **Spread**：分散调度，提高可用性
- **Round Robin**：轮询调度，简单公平

### 2. 服务发现
- 服务注册与注销
- 端点管理
- 服务解析与负载均衡

### 3. 健康检查
- HTTP 健康检查
- 健康状态管理
- 事件通知

### 4. 扩缩容
- 基于 CPU/内存指标的自动扩缩容
- 手动扩缩容
- 冷却时间控制

## 项目结构

```
container-orchestrator/
├── cmd/
│   └── main.go              # 主程序入口
├── docs/
│   ├── 01-RESEARCH.md       # 调研文档
│   ├── 02-DESIGN.md         # 设计文档
│   ├── 03-IMPLEMENTATION.md # 实现文档
│   ├── 04-TESTING.md        # 测试文档
│   └── 05-DEVELOPMENT.md    # 开发文档
├── pkg/
│   ├── api/
│   │   └── server.go        # API 服务器
│   ├── container/
│   │   └── types.go         # 容器类型定义
│   ├── discovery/
│   │   └── discovery.go     # 服务发现
│   ├── health/
│   │   └── health.go        # 健康检查
│   ├── manager/
│   │   └── manager.go       # 管理器
│   ├── scaler/
│   │   └── scaler.go        # 扩缩容
│   └── scheduler/
│       └── scheduler.go     # 调度器
├── tests/
│   ├── api_test.go          # API 测试
│   ├── container_test.go    # 容器测试
│   ├── discovery_test.go    # 服务发现测试
│   ├── health_test.go       # 健康检查测试
│   ├── manager_test.go      # 管理器测试
│   ├── scheduler_test.go    # 调度器测试
│   └── scaler_test.go       # 扩缩容测试
├── go.mod
├── go.sum
├── LEARNING_NOTES.md
└── README.md
```

## 快速开始

### 前置要求

- Go 1.21+
- Docker（可选）

### 安装

```bash
cd projects/container-orchestrator
go mod download
```

### 构建

```bash
go build -o bin/orchestrator ./cmd/main.go
```

### 运行

```bash
./bin/orchestrator
```

### 测试

```bash
# 运行所有测试
go test ./...

# 运行带覆盖率的测试
go test -cover ./...
```

## API 使用

### 创建节点

```bash
curl -X POST http://localhost:8080/api/nodes \
  -H "Content-Type: application/json" \
  -d '{
    "name": "node-1",
    "address": "192.168.1.1",
    "cpu": 4.0,
    "memory": 8589934592,
    "disk": 107374182400
  }'
```

### 创建服务

```bash
curl -X POST http://localhost:8080/api/services \
  -H "Content-Type: application/json" \
  -d '{
    "name": "web-service",
    "image": "nginx:latest",
    "replicas": 3,
    "cpu": 0.5,
    "memory": 536870912,
    "disk": 5368709120
  }'
```

### 扩缩容服务

```bash
curl -X PUT http://localhost:8080/api/services/{service_id} \
  -H "Content-Type: application/json" \
  -d '{
    "replicas": 5
  }'
```

### 解析服务

```bash
curl http://localhost:8080/api/resolve/web-service
```

### 获取集群统计

```bash
curl http://localhost:8080/api/stats
```

### 获取健康状态

```bash
curl http://localhost:8080/api/health
```

## 调度算法

### Bin Packing

**目标**：最大化资源利用率

**策略**：将容器调度到资源最少的可用节点

**适用场景**：成本敏感、资源有限、批处理任务

### Spread

**目标**：最大化可用性

**策略**：将容器分散到不同节点

**适用场景**：高可用要求、Web 服务、关键业务

### Round Robin

**目标**：简单公平

**策略**：轮询选择节点

**适用场景**：节点同构、简单场景、测试环境

## 服务发现

### 服务注册

```go
service := container.NewService("web-service", 3, template)
discovery.RegisterService(service)
```

### 端点注册

```go
endpoint := &discovery.Endpoint{
    ID:        "endpoint-1",
    ServiceID: service.ID,
    Address:   "192.168.1.1",
    Port:      8080,
    Health:    discovery.HealthHealthy,
}
discovery.RegisterEndpoint(endpoint)
```

### 服务解析

```go
endpoint, err := discovery.Resolve("web-service")
```

## 健康检查

### HTTP 健康检查

```go
checker := health.NewHTTPHealthChecker(httpClient)
monitor := health.NewHealthMonitor(checker)
monitor.AddContainer(container)
monitor.Start(ctx, 10*time.Second)
```

### 健康状态

```go
result, err := monitor.GetHealth(containerID)
if result.State == health.StateHealthy {
    // 容器健康
}
```

## 扩缩容

### 自动扩缩容

```go
policy := &scaler.ScalingPolicy{
    MinReplicas:     1,
    MaxReplicas:     10,
    ScaleUpCPU:      0.8,
    ScaleDownCPU:    0.2,
    Cooldown:        5 * time.Minute,
}
scaler.RegisterService(serviceID, replicas, policy)
```

### 手动扩缩容

```go
scaler.ManualScale(serviceID, 5)
```

## 学习资源

- [调研文档](docs/01-RESEARCH.md) - 容器编排调研
- [设计文档](docs/02-DESIGN.md) - 系统设计
- [实现文档](docs/03-IMPLEMENTATION.md) - 实现细节
- [测试文档](docs/04-TESTING.md) - 测试策略
- [开发文档](docs/05-DEVELOPMENT.md) - 开发指南
- [学习笔记](LEARNING_NOTES.md) - 学习笔记

## 技术栈

- **语言**：Go 1.21
- **框架**：无
- **其他**：Docker

## 许可证

MIT License

# 01 - 容器编排调研

## 什么是容器编排？

容器编排是自动化容器化应用程序的部署、管理、扩展和联网的过程。它解决了在生产环境中运行容器时面临的复杂性问题。

## 核心概念

### 1. 容器（Container）
- 轻量级、可移植的软件包
- 包含应用程序及其所有依赖项
- 在隔离的环境中运行

### 2. 编排（Orchestration）
- 自动化容器的生命周期管理
- 处理容器的调度、部署、扩展
- 提供服务发现和负载均衡

### 3. 集群（Cluster）
- 一组运行容器的节点
- 提供高可用性和容错能力
- 资源池化管理

## 主流容器编排工具

### 1. Kubernetes
- **特点**：行业标准，功能丰富
- **架构**：Master-Worker 模式
- **核心组件**：
  - API Server
  - Scheduler
  - Controller Manager
  - etcd
  - Kubelet
  - Kube-proxy

### 2. Docker Swarm
- **特点**：简单易用，与 Docker 深度集成
- **架构**：Manager-Worker 模式
- **适用场景**：小规模部署

### 3. Apache Mesos
- **特点**：大规模集群管理
- **架构**：Master-Agent 模式
- **适用场景**：超大规模部署

## 核心功能

### 1. 调度（Scheduling）
- **目标**：将容器分配到合适的节点
- **策略**：
  - Bin Packing：紧凑调度，提高资源利用率
  - Spread：分散调度，提高可用性
  - Round Robin：轮询调度，简单公平

### 2. 服务发现（Service Discovery）
- **功能**：自动发现和定位服务
- **机制**：
  - DNS 解析
  - 环境变量
  - 服务注册中心

### 3. 健康检查（Health Check）
- **类型**：
  - HTTP 检查
  - TCP 检查
  - 命令检查
- **策略**：
  - 启动探针
  - 存活探针
  - 就绪探针

### 4. 扩缩容（Scaling）
- **水平扩展**：增加/减少容器副本数
- **垂直扩展**：调整容器资源限制
- **自动扩缩容**：基于指标自动调整

### 5. 负载均衡（Load Balancing）
- **算法**：
  - 轮询
  - 加权轮询
  - 最少连接
  - IP Hash

## 调度算法

### 1. Bin Packing
```
目标：最大化资源利用率
策略：将容器调度到资源最少的可用节点
优点：资源利用高效
缺点：可能导致热点
```

### 2. Spread
```
目标：最大化可用性
策略：将容器分散到不同节点
优点：容错性好
缺点：资源利用率可能较低
```

### 3. Best Fit
```
目标：找到最匹配的节点
策略：选择资源最接近需求的节点
优点：资源分配合理
缺点：计算复杂度较高
```

## 健康检查机制

### 1. HTTP 检查
```yaml
httpGet:
  path: /health
  port: 8080
initialDelaySeconds: 30
periodSeconds: 10
```

### 2. TCP 检查
```yaml
tcpSocket:
  port: 8080
initialDelaySeconds: 30
periodSeconds: 10
```

### 3. 命令检查
```yaml
exec:
  command:
    - cat
    - /tmp/healthy
initialDelaySeconds: 30
periodSeconds: 10
```

## 服务发现机制

### 1. 客户端发现
- 客户端直接查询服务注册中心
- 客户端负责负载均衡
- 优点：简单直接
- 缺点：客户端复杂

### 2. 服务端发现
- 通过代理/负载均衡器查询
- 代理负责负载均衡
- 优点：客户端简单
- 缺点：增加一跳延迟

### 3. DNS 发现
- 使用 DNS 记录进行服务发现
- 优点：标准化，兼容性好
- 缺点：DNS 缓存可能导致延迟

## 参考资源

1. **Kubernetes 官方文档**
   - https://kubernetes.io/docs/

2. **Docker 官方文档**
   - https://docs.docker.com/

3. **《Kubernetes in Action》**
   - 全面介绍 Kubernetes 的书籍

4. **《Docker Deep Dive》**
   - 深入理解 Docker 和容器技术

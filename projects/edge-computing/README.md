# 边缘计算框架

实现边缘计算框架，支持边缘节点管理、任务分发、结果收集和负载均衡。

## 学习目标

- 理解边缘计算的核心概念和架构
- 掌握任务卸载的策略和实现
- 学会资源调度和负载均衡算法

## 核心循环

```
任务提交 → 边缘节点 → 计算 → 结果返回
```

## 项目结构

```
edge-computing/
├── src/
│   ├── __init__.py          # 包初始化
│   ├── edge_node.py         # 边缘节点定义
│   ├── task.py              # 任务定义
│   ├── scheduler.py         # 调度器实现
│   ├── edge_cluster.py      # 边缘集群管理
│   └── coordinator.py       # 协调器
├── tests/
│   ├── __init__.py
│   ├── test_edge_node.py    # 节点测试
│   ├── test_task.py         # 任务测试
│   ├── test_scheduler.py    # 调度器测试
│   ├── test_edge_cluster.py # 集群测试
│   └── test_coordinator.py  # 协调器测试
├── docs/
│   ├── 01-RESEARCH.md
│   ├── 02-DESIGN.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── README.md
└── LEARNING_NOTES.md
```

## 核心组件

### 1. 边缘节点 (EdgeNode)

边缘计算的基本计算单元，具有以下特性：
- 支持多种节点类型（EDGE/FOG/CLOUD）
- 任务队列管理
- 资源监控和指标收集
- 心跳检测

### 2. 任务 (Task)

表示需要在边缘节点上执行的计算任务：
- 优先级支持（LOW/NORMAL/HIGH/CRITICAL）
- 完整的生命周期管理
- 超时控制
- 回调机制

### 3. 调度器 (Scheduler)

实现多种任务调度策略：
- **RoundRobinScheduler**: 轮询调度，简单公平
- **LeastLoadScheduler**: 最小负载调度，动态均衡
- **WeightedScheduler**: 加权调度，考虑节点容量
- **PriorityScheduler**: 优先级调度，高优先级任务优先
- **LocationAwareScheduler**: 位置感知调度，减少延迟

### 4. 边缘集群 (EdgeCluster)

管理一组边缘节点：
- 节点的添加和移除
- 任务的统一分发
- 集群健康检查
- 统计信息收集

### 5. 协调器 (Coordinator)

系统的核心协调组件：
- 管理多个边缘集群
- 协调任务分发
- 收集和聚合结果
- 系统监控

## 快速开始

### 安装依赖

```bash
# 无需额外依赖，使用 Python 标准库
```

### 运行测试

```bash
cd projects/edge-computing
python3 -m pytest tests/ -v
```

### 使用示例

```python
from src import (
    EdgeNode, NodeType, Task, TaskPriority,
    EdgeCluster, Coordinator, LeastLoadScheduler
)

# 创建协调器
coordinator = Coordinator(coordinator_id="main")

# 创建集群
cluster = EdgeCluster(cluster_id="cluster-1", scheduler=LeastLoadScheduler())

# 添加节点
node1 = EdgeNode(name="edge-node-1", node_type=NodeType.EDGE, capacity=5)
node2 = EdgeNode(name="edge-node-2", node_type=NodeType.EDGE, capacity=10)
cluster.add_node(node1)
cluster.add_node(node2)

# 注册集群
coordinator.add_cluster(cluster)

# 提交任务
task = Task(name="image-processing", priority=TaskPriority.HIGH)
coordinator.submit_task(task)

# 完成任务
coordinator.complete_task(task.task_id, node1.node_id, "cluster-1", {"result": "processed"})

# 获取结果
result = coordinator.get_task_result(task.task_id)
print(f"Task result: {result.data}")

# 系统统计
stats = coordinator.get_system_stats()
print(f"Total nodes: {stats['total_nodes']}")
print(f"Current load: {stats['current_load']}")
```

## 调度策略详解

### 轮询调度 (Round Robin)

最简单的调度策略，按顺序将任务分配给各个节点。

**优点**: 实现简单，分配公平
**缺点**: 不考虑节点实际负载

### 最小负载调度 (Least Load)

选择当前负载最低的节点执行任务。

**优点**: 动态均衡，适应性强
**缺点**: 可能导致频繁切换

### 加权调度 (Weighted)

根据节点容量和当前负载进行加权随机选择。

**优点**: 考虑节点能力差异
**缺点**: 需要准确的容量配置

### 优先级调度 (Priority)

高优先级任务优先分配到性能更好的节点。

**优点**: 保证关键任务优先处理
**缺点**: 低优先级任务可能饥饿

### 位置感知调度 (Location-Aware)

根据任务来源位置选择最近的边缘节点。

**优点**: 减少网络延迟
**缺点**: 需要位置信息

## 技术栈

- **语言**: Python 3.12+
- **框架**: 无（纯 Python 实现）
- **测试**: pytest

## 扩展方向

1. **异步支持**: 使用 asyncio 实现异步任务处理
2. **分布式部署**: 支持跨网络的节点管理
3. **动态扩缩容**: 根据负载自动调整节点数量
4. **故障恢复**: 实现任务重试和故障转移
5. **监控告警**: 集成 Prometheus/Grafana 监控

## 参考资料

- [边缘计算概述](https://en.wikipedia.org/wiki/Edge_computing)
- [任务调度算法](https://en.wikipedia.org/wiki/Scheduling_(computing))
- [负载均衡](https://en.wikipedia.org/wiki/Load_balancing_(computing))

# 边缘计算框架

完整的边缘计算解决方案，支持边缘节点管理、任务调度、数据处理、云端同步和 IoT 网关。

## 学习目标

- 理解边缘计算的核心概念和架构
- 掌握任务卸载的策略和实现
- 学会资源调度和负载均衡算法
- 实现数据过滤、聚合和规则引擎
- 掌握边缘与云端的数据同步机制
- 构建 IoT 数据处理和实时分析系统

## 核心循环

```
IoT 设备 → 数据采集 → 边缘处理 → 云端同步
    ↑           ↓           ↓           ↓
    └─── 配置下发 ←── 告警触发 ←── 规则引擎
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
│   ├── coordinator.py       # 协调器
│   ├── data_processor.py    # 数据处理（过滤/聚合/规则引擎）
│   ├── cloud_sync.py        # 云端同步
│   └── iot_gateway.py       # IoT 网关
├── tests/
│   ├── __init__.py
│   ├── test_edge_node.py
│   ├── test_task.py
│   ├── test_scheduler.py
│   ├── test_edge_cluster.py
│   ├── test_coordinator.py
│   ├── test_data_processor.py
│   ├── test_cloud_sync.py
│   └── test_iot_gateway.py
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

### 6. 数据处理器 (DataProcessor)

边缘数据处理核心：
- **DataFilter**: 数据过滤，支持多种操作符和组合条件
- **DataAggregator**: 数据聚合，支持 COUNT/SUM/AVG/MIN/MAX 等
- **RuleEngine**: 规则引擎，支持转发、丢弃、转换、告警等动作

### 7. 云端同步 (CloudSync)

边缘与云端的数据同步：
- **DataUploader**: 批量数据上传，支持重试和进度跟踪
- **ConfigManager**: 配置管理，支持云端下发和本地覆盖
- **CloudSyncManager**: 统一同步管理

### 8. IoT 网关 (IoTGateway)

IoT 数据处理和实时分析：
- **DeviceRegistry**: 设备注册和管理
- **DataBuffer**: 传感器数据缓冲
- **AlertManager**: 告警规则和通知
- **RealtimeAnalyzer**: 实时统计和趋势分析

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

#### 基础边缘计算

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
```

#### 数据处理

```python
from src import (
    DataPoint, FilterRule, FilterOperator,
    DataFilter, DataAggregator, AggregationType,
    RuleEngine, Rule, RuleAction
)

# 创建数据过滤器
data_filter = DataFilter()
data_filter.add_rule(FilterRule(
    field="value",
    operator=FilterOperator.GT,
    value=30.0
))

# 过滤数据
data_points = [
    DataPoint(timestamp=0, source="sensor-1", metric="temperature", value=25.0),
    DataPoint(timestamp=0, source="sensor-1", metric="temperature", value=35.0),
]
filtered = data_filter.filter(data_points)  # 只保留 value > 30 的数据

# 数据聚合
aggregator = DataAggregator(window_size=300)
for dp in data_points:
    aggregator.add(dp)

avg_result = aggregator.aggregate(AggregationType.AVG)

# 规则引擎
engine = RuleEngine()
engine.add_rule(Rule(
    rule_id="high-temp-alert",
    name="High Temperature Alert",
    conditions=[FilterRule(field="value", operator=FilterOperator.GT, value=30.0)],
    action=RuleAction.ALERT,
    action_params={"severity": "warning"},
))

# 注册告警回调
engine.register_alert_callback(lambda alert: print(f"Alert: {alert}"))

# 处理数据
result = engine.process(data_points[1])  # 触发告警
```

#### IoT 网关

```python
from src import (
    IoTGateway, IoTDevice, DeviceStatus, DataType,
    SensorReading, AlertLevel
)

# 创建网关
gateway = IoTGateway(gateway_id="factory-gateway")

# 注册设备
device = IoTDevice(
    device_id="temp-sensor-1",
    name="Temperature Sensor",
    device_type="sensor",
    location={"lat": 39.9, "lon": 116.4}
)
gateway.register_device(device)

# 添加告警规则
gateway.add_alert_rule(
    rule_id="high-temp",
    data_type=DataType.TEMPERATURE,
    condition="gt",
    threshold=35.0,
    level=AlertLevel.WARNING,
    message="Temperature too high: {value}°C"
)

# 启动网关
gateway.start()

# 接收传感器数据
reading = SensorReading(
    reading_id="r-1",
    device_id="temp-sensor-1",
    data_type=DataType.TEMPERATURE,
    value=36.5,
    unit="°C"
)

result = gateway.receive_data(reading)
print(f"Alert triggered: {result['alert']}")

# 获取设备摘要
summary = gateway.get_device_summary("temp-sensor-1")
```

#### 云端同步

```python
from src import (
    MockCloudConnector, CloudSyncManager, SyncConfig
)

# 创建云端连接器
connector = MockCloudConnector(endpoint="https://cloud.example.com")

# 创建同步管理器
sync_manager = CloudSyncManager(
    node_id="edge-node-1",
    connector=connector,
    sync_config=SyncConfig(batch_size=50, max_retries=3)
)

# 启动同步
sync_manager.start()

# 同步数据
sync_manager.sync_data("sensor", "temp-1", {"value": 25.0, "unit": "°C"})
sync_manager.sync_data("sensor", "humidity-1", {"value": 60.0, "unit": "%"})

# 执行批量同步
result = sync_manager.sync_batch()
print(f"Uploaded: {result['upload']['uploaded']}")

# 获取配置
config_value = sync_manager.config_manager.get("log_level")
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

**优点**: 净少网络延迟
**缺点**: 需要位置信息

## 数据处理详解

### 数据过滤

支持多种过滤操作符：
- 比较操作: EQ, NEQ, GT, GTE, LT, LTE
- 集合操作: IN, NOT_IN
- 字符串操作: CONTAINS, REGEX

支持 AND/OR 组合模式。

### 数据聚合

支持时间窗口聚合：
- COUNT: 计数
- SUM: 求和
- AVG: 平均值
- MIN/MAX: 最小/最大值
- FIRST/LAST: 首/末值
- STDDEV: 标准差

### 规则引擎

支持多种动作：
- FORWARD: 转发数据
- DROP: 丢弃数据
- TRANSFORM: 转换数据（缩放、偏移、重命名）
- ALERT: 触发告警
- AGGREGATE: 聚合请求

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
6. **MQTT 集成**: 支持 MQTT 协议的设备通信
7. **数据持久化**: 集成时序数据库存储历史数据

## 参考资料

- [边缘计算概述](https://en.wikipedia.org/wiki/Edge_computing)
- [任务调度算法](https://en.wikipedia.org/wiki/Scheduling_(computing))
- [负载均衡](https://en.wikipedia.org/wiki/Load_balancing_(computing))
- [IoT 架构](https://en.wikipedia.org/wiki/Internet_of_things)

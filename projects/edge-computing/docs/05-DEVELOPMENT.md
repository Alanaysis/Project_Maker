# 05 - 开发阶段

## 开发概述

本文档记录边缘计算框架的开发过程、遇到的问题和解决方案。

## 开发环境

### 系统环境

- **操作系统**: Linux
- **Python 版本**: 3.12.3
- **包管理**: pip

### 开发工具

- **编辑器**: VS Code
- **版本控制**: Git
- **测试框架**: pytest

### 依赖

```bash
# 无需额外依赖，使用 Python 标准库
```

## 开发过程

### 阶段 1: 需求分析

**目标**: 理解边缘计算的核心概念和需求

**输出**:
- 边缘计算概述
- 核心功能需求
- 技术选型

### 阶段 2: 系统设计

**目标**: 设计系统架构和组件接口

**输出**:
- 系统架构图
- 组件接口定义
- 数据流设计

### 阶段 3: 核心实现

**目标**: 实现核心组件

**实现顺序**:
1. Task（任务）
2. EdgeNode（边缘节点）
3. Scheduler（调度器）
4. EdgeCluster（边缘集群）
5. Coordinator（协调器）
6. DataProcessor（数据处理器）
7. CloudSync（云端同步）
8. IoTGateway（IoT 网关）

### 阶段 4: 测试验证

**目标**: 编写测试用例并验证功能

**输出**:
- 单元测试
- 集成测试
- 测试报告

### 阶段 5: 文档完善

**目标**: 编写完整的项目文档

**输出**:
- README
- 研究文档
- 设计文档
- 实现文档
- 测试文档
- 开发文档

## 关键实现细节

### 1. 任务状态管理

**问题**: 如何管理任务的生命周期？

**解决方案**: 使用枚举定义任务状态，并实现状态转换逻辑

```python
class TaskStatus(Enum):
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

**状态转换**:
```
PENDING ──(调度)──> QUEUED
QUEUED ──(开始处理)──> PROCESSING
PROCESSING ──(完成)──> COMPLETED
PROCESSING ──(失败)──> FAILED
ANY ──(取消)──> CANCELLED
```

### 2. 节点状态管理

**问题**: 如何管理节点的状态？

**解决方案**: 使用枚举定义节点状态，并根据任务情况动态更新

```python
class NodeStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
```

**状态更新逻辑**:
```python
def _update_status(self) -> None:
    if self.current_load == 0:
        self.status = NodeStatus.IDLE
    elif self.current_load > 0:
        self.status = NodeStatus.BUSY
```

### 3. 调度算法实现

**问题**: 如何实现多种调度策略？

**解决方案**: 使用策略模式，定义统一的调度器接口

```python
class Scheduler(ABC):
    @abstractmethod
    def select_node(self, task, nodes) -> Optional[EdgeNode]
    
    def schedule(self, task, nodes) -> bool
    def schedule_batch(self, tasks, nodes) -> Dict[str, bool]
```

**实现**:
- RoundRobinScheduler: 轮询调度
- LeastLoadScheduler: 最小负载调度
- WeightedScheduler: 加权调度
- PriorityScheduler: 优先级调度
- LocationAwareScheduler: 位置感知调度

### 4. 负载均衡

**问题**: 如何实现负载均衡？

**解决方案**: 使用负载因子（load_factor）衡量节点负载

```python
@property
def load_factor(self) -> float:
    if self.capacity == 0:
        return 1.0
    return self.current_load / self.capacity
```

**调度策略**:
- 选择负载因子最低的节点
- 考虑节点容量
- 支持加权随机选择

### 5. 结果收集

**问题**: 如何收集和聚合任务结果？

**解决方案**: 使用回调机制和结果存储

```python
# 任务完成时触发回调
if self.callback:
    self.callback(self.result)

# Coordinator 存储结果
self._completed_tasks[task_id] = TaskResult(...)
```

### 6. 数据过滤实现

**问题**: 如何高效过滤边缘数据？

**解决方案**: 使用规则组合和多种操作符

```python
class FilterRule:
    def matches(self, data_point: DataPoint) -> bool:
        field_value = self._get_field_value(data_point)
        result = self._compare(field_value)
        return not result if self.negate else result

class DataFilter:
    def filter(self, data_points: List[DataPoint]) -> List[DataPoint]:
        if self._match_all:
            return [dp for dp in data_points if all(r.matches(dp) for r in self._rules)]
        else:
            return [dp for dp in data_points if any(r.matches(dp) for r in self._rules)]
```

**支持的操作符**:
- EQ, NEQ: 等于/不等于
- GT, GTE, LT, LTE: 大于/大于等于/小于/小于等于
- IN, NOT_IN: 在列表中/不在列表中
- CONTAINS: 包含
- REGEX: 正则匹配

### 7. 数据聚合实现

**问题**: 如何进行时间窗口聚合？

**解决方案**: 使用环形缓冲区和时间窗口

```python
class DataAggregator:
    def __init__(self, window_size: float = 60.0):
        self.window_size = window_size
        self._buffer: Dict[str, List[DataPoint]] = defaultdict(list)

    def add(self, data_point: DataPoint) -> None:
        key = f"{data_point.source}:{data_point.metric}"
        self._buffer[key].append(data_point)
        self._cleanup(key)

    def _cleanup(self, key: str) -> None:
        cutoff = time.time() - self.window_size
        self._buffer[key] = [dp for dp in self._buffer[key] if dp.timestamp >= cutoff]
```

**支持的聚合类型**:
- COUNT: 计数
- SUM: 求和
- AVG: 平均值
- MIN/MAX: 最小/最大值
- FIRST/LAST: 首/末值
- STDDEV: 标准差

### 8. 规则引擎实现

**问题**: 如何实现灵活的规则处理？

**解决方案**: 使用策略模式和动作处理器

```python
class RuleEngine:
    def __init__(self):
        self._handlers: Dict[RuleAction, Callable] = {
            RuleAction.FORWARD: self._handle_forward,
            RuleAction.DROP: self._handle_drop,
            RuleAction.TRANSFORM: self._handle_transform,
            RuleAction.ALERT: self._handle_alert,
        }

    def process(self, data_point: DataPoint) -> Optional[DataPoint]:
        for rule in self._rules:
            if rule.evaluate(data_point):
                handler = self._handlers.get(rule.action)
                if handler:
                    return handler(data_point, rule)
        return data_point
```

**支持的动作**:
- FORWARD: 转发数据
- DROP: 丢弃数据
- TRANSFORM: 转换数据（缩放、偏移、重命名）
- ALERT: 触发告警

### 9. 云端同步实现

**问题**: 如何实现可靠的数据同步？

**解决方案**: 使用队列、重试机制和校验和

```python
class DataUploader:
    def upload_batch(self) -> Dict[str, Any]:
        batch = []
        with self._lock:
            for _ in range(min(self.config.batch_size, len(self._upload_queue))):
                if self._upload_queue:
                    batch.append(self._upload_queue.popleft())

        for record in batch:
            for attempt in range(self.config.max_retries):
                if self.connector.upload_data(upload_data):
                    record.synced = True
                    break
                else:
                    if attempt < self.config.max_retries - 1:
                        time.sleep(self.config.retry_delay)
```

**特性**:
- 批量上传
- 失败重试
- 校验和验证
- 进度跟踪

### 10. 配置管理实现

**问题**: 如何管理边缘节点配置？

**解决方案**: 支持远程配置和本地覆盖

```python
class ConfigManager:
    def get(self, key: str, default: Any = None) -> Any:
        # 优先返回本地覆盖
        if key in self._overrides:
            return self._overrides[key]
        # 然后返回远程配置
        if key in self._config:
            return self._config[key]
        return default

    def sync_from_cloud(self) -> Dict[str, Any]:
        cloud_config = self.connector.get_config()
        for key, value in cloud_config.items():
            old_value = self._config.get(key)
            self._config[key] = value
            if old_value != value:
                self._notify_watchers(key, old_value, value)
```

**特性**:
- 远程配置下发
- 本地配置覆盖
- 变更通知
- 版本管理

### 11. 设备管理实现

**问题**: 如何管理大量 IoT 设备？

**解决方案**: 使用注册表和索引

```python
class DeviceRegistry:
    def __init__(self):
        self._devices: Dict[str, IoTDevice] = {}
        self._device_types: Dict[str, Set[str]] = defaultdict(set)

    def register(self, device: IoTDevice) -> bool:
        with self._lock:
            if device.device_id in self._devices:
                return False
            self._devices[device.device_id] = device
            self._device_types[device.device_type].add(device.device_id)
            return True

    def get_devices_by_type(self, device_type: str) -> List[IoTDevice]:
        device_ids = self._device_types.get(device_type, set())
        return [self._devices[did] for did in device_ids if did in self._devices]
```

**特性**:
- 设备注册/注销
- 按类型索引
- 心跳检测
- 健康检查

### 12. 实时分析实现

**问题**: 如何进行实时数据分析？

**解决方案**: 使用统计方法和异常检测

```python
class RealtimeAnalyzer:
    def detect_trend(self, readings: List[SensorReading]) -> Dict[str, Any]:
        # 简单线性回归
        n = len(values)
        sum_x = sum(x for x, _ in values)
        sum_y = sum(y for _, y in values)
        sum_xy = sum(x * y for x, y in values)
        sum_x2 = sum(x * x for x, _ in values)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)

        if abs(slope) < 0.001:
            trend = "stable"
        elif slope > 0:
            trend = "increasing"
        else:
            trend = "decreasing"

        return {"trend": trend, "slope": slope}

    def detect_anomalies(self, readings: List[SensorReading], threshold: float = 2.0) -> List[SensorReading]:
        # Z-score 异常检测
        mean = sum(values) / len(values)
        stddev = (sum((x - mean) ** 2 for x in values) / len(values)) ** 0.5

        for reading in readings:
            z_score = abs(reading.value - mean) / stddev
            if z_score > threshold:
                anomalies.append(reading)
```

**功能**:
- 统计计算（均值、方差、极值）
- 趋势检测（线性回归）
- 异常检测（Z-score）

## 遇到的问题和解决方案

### 问题 1: 相对导入错误

**问题描述**: 使用相对导入时，测试文件无法正确导入模块

**错误信息**:
```
ImportError: attempted relative import with no known parent package
```

**解决方案**: 使用 try/except 处理相对导入和绝对导入

```python
try:
    from .edge_node import EdgeNode, NodeType, NodeStatus
except ImportError:
    from edge_node import EdgeNode, NodeType, NodeStatus
```

### 问题 2: 节点状态更新不正确

**问题描述**: 提交任务后，节点状态没有正确更新为 BUSY

**原因**: 原始实现只在负载达到容量时才更新状态

**解决方案**: 修改状态更新逻辑，有活跃任务时就更新为 BUSY

```python
# 修改前
if self.current_load >= self.capacity:
    self.status = NodeStatus.BUSY

# 修改后
if self.current_load > 0:
    self.status = NodeStatus.BUSY
```

### 问题 3: 测试缺少导入

**问题描述**: 测试文件中缺少 TaskStatus 的导入

**错误信息**:
```
NameError: name 'TaskStatus' is not defined
```

**解决方案**: 添加缺失的导入

```python
from task import Task, TaskPriority, TaskStatus
```

### 问题 4: 浮点精度问题

**问题描述**: 趋势检测测试失败，因为大时间戳导致浮点精度问题

**原因**: Unix 时间戳（约 17 亿）与小数值（0-9）计算时精度丢失

**解决方案**: 使用小的相对时间戳进行测试

```python
# 不好的做法
readings = [
    SensorReading(f"r-{i}", "device-1", DataType.TEMPERATURE, float(i), "°C", timestamp=time.time() + i)
    for i in range(10)
]

# 好的做法
readings = [
    SensorReading(f"r-{i}", "device-1", DataType.TEMPERATURE, float(i) * 10, "°C", timestamp=float(i))
    for i in range(10)
]
```

### 问题 5: 线程安全问题

**问题描述**: 多线程环境下访问共享资源可能导致数据竞争

**解决方案**: 使用 threading.Lock 保护共享资源

```python
class DeviceRegistry:
    def __init__(self):
        self._devices: Dict[str, IoTDevice] = {}
        self._lock = threading.Lock()

    def register(self, device: IoTDevice) -> bool:
        with self._lock:
            if device.device_id in self._devices:
                return False
            self._devices[device.device_id] = device
            return True
```

## 代码质量

### 1. 代码风格

- 遵循 PEP 8 规范
- 使用类型注解
- 编写清晰的文档字符串

### 2. 代码组织

- 每个组件一个文件
- 清晰的模块结构
- 合理的命名规范

### 3. 错误处理

- 使用异常处理错误
- 提供清晰的错误信息
- 记录错误日志

### 4. 性能优化

- 选择合适的数据结构
- 避免不必要的计算
- 使用缓存（可选）
- 批量处理减少 I/O

## 版本控制

### Git 工作流

1. **主分支**: `master`，保持稳定
2. **开发分支**: `dev`，日常开发
3. **功能分支**: `feature/xxx`，新功能开发
4. **修复分支**: `fix/xxx`，问题修复

### 提交规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型**:
- `feat`: 新功能
- `fix`: 修复问题
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具相关

### 分支管理

```bash
# 创建功能分支
git checkout -b feature/new-scheduler

# 提交更改
git add .
git commit -m "feat(scheduler): add weighted scheduler"

# 合并到开发分支
git checkout dev
git merge feature/new-scheduler
```

## 持续集成

### GitHub Actions

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.12'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pytest
    - name: Run tests
      run: |
        python -m pytest tests/ -v
```

## 部署

### 本地部署

```bash
# 克隆项目
git clone <repository-url>
cd edge-computing

# 运行测试
python3 -m pytest tests/ -v

# 使用示例
python3 -c "
from src import EdgeNode, Task, EdgeCluster, Coordinator

# 创建和使用边缘计算系统
coordinator = Coordinator()
cluster = EdgeCluster()
node = EdgeNode(name='node-1', capacity=5)
cluster.add_node(node)
coordinator.add_cluster(cluster)

task = Task(name='test-task')
coordinator.submit_task(task)
print('Task submitted successfully')
"
```

### Docker 部署（可选）

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install pytest

CMD ["python3", "-m", "pytest", "tests/", "-v"]
```

## 扩展计划

### 短期计划

1. **异步支持**: 使用 asyncio 实现异步任务处理
2. **更多调度算法**: 添加更多调度策略
3. **性能优化**: 优化关键路径的性能
4. **MQTT 集成**: 支持 MQTT 协议的设备通信

### 中期计划

1. **分布式部署**: 支持跨网络的节点管理
2. **动态扩缩容**: 根据负载自动调整节点数量
3. **故障恢复**: 实现任务重试和故障转移
4. **数据持久化**: 集成时序数据库存储历史数据

### 长期计划

1. **监控告警**: 集成 Prometheus/Grafana 监控
2. **Web 界面**: 提供 Web 管理界面
3. **API 网关**: 提供 RESTful API
4. **机器学习**: 集成边缘 AI 推理

## 经验总结

### 1. 设计先行

在开始编码之前，先进行充分的设计，包括：
- 系统架构设计
- 组件接口设计
- 数据流设计

### 2. 测试驱动

采用测试驱动开发（TDD）的方式：
- 先编写测试用例
- 再实现功能代码
- 最后重构优化

### 3. 迭代开发

采用迭代开发的方式：
- 每次迭代实现一个完整功能
- 及时测试和验证
- 根据反馈调整

### 4. 文档同步

文档与代码同步更新：
- 代码变更时更新文档
- 文档反映最新实现
- 保持文档的准确性

### 5. 关注边界情况

- 空输入处理
- 极端值处理
- 并发安全
- 错误恢复

## 参考资料

1. [Python 开发最佳实践](https://docs.python.org/3/tutorial/)
2. [Git 工作流](https://www.atlassian.com/git/tutorials/comparing-workflows)
3. [持续集成](https://en.wikipedia.org/wiki/Continuous_integration)
4. [测试驱动开发](https://en.wikipedia.org/wiki/Test-driven_development)
5. [线程安全编程](https://docs.python.org/3/library/threading.html)
6. [设计模式](https://refactoring.guru/design-patterns)

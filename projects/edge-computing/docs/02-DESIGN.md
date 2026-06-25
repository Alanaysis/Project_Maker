# 02 - 设计阶段

## 系统架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Cloud Layer                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Cloud Storage / Config Server / Analytics                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Sync
                                    v
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Edge Computing Layer                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                          Coordinator                                │   │
│  │  ┌──────────┐  ┌──────────────┐  ┌────────────┐  ┌──────────────┐ │   │
│  │  │ Cluster  │  │ Data         │  │ Cloud Sync │  │ IoT Gateway  │ │   │
│  │  │ Manager  │  │ Processor    │  │ Manager    │  │              │ │   │
│  │  └──────────┘  └──────────────┘  └────────────┘  └──────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│          │                │                │                │               │
│          v                v                v                v               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  Cluster 1   │  │  Cluster 2   │  │  Cluster 3   │  │  Cluster N   │   │
│  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │   │
│  │ │ Node 1   │ │  │ │ Node 4   │ │  │ │ Node 7   │ │  │ │ Node N   │ │   │
│  │ │ Node 2   │ │  │ │ Node 5   │ │  │ │ Node 8   │ │  │ │          │ │   │
│  │ │ Node 3   │ │  │ │ Node 6   │ │  │ │ Node 9   │ │  │ │          │ │   │
│  │ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    v
┌─────────────────────────────────────────────────────────────────────────────┐
│                            IoT Device Layer                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Sensor 1 │  │ Sensor 2 │  │ Actuator │  │ Camera   │  │ Device N │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 核心组件设计

### 1. EdgeNode（边缘节点）

**职责**:
- 执行分配的任务
- 监控自身资源使用情况
- 报告状态和指标

**属性**:
- `node_id`: 节点唯一标识
- `name`: 节点名称
- `node_type`: 节点类型（EDGE/FOG/CLOUD）
- `capacity`: 最大并发任务数
- `status`: 节点状态（IDLE/BUSY/OFFLINE/MAINTENANCE）
- `location`: 节点位置坐标

**方法**:
- `submit_task(task)`: 提交任务
- `complete_task(task_id, result)`: 完成任务
- `fail_task(task_id, error)`: 标记任务失败
- `heartbeat()`: 更新心跳
- `get_stats()`: 获取统计信息

**状态转换**:
```
IDLE ──(提交任务)──> BUSY
BUSY ──(所有任务完成)──> IDLE
ANY ──(离线)──> OFFLINE
ANY ──(维护)──> MAINTENANCE
```

### 2. Task（任务）

**职责**:
- 封装计算任务
- 跟踪任务状态
- 管理任务生命周期

**属性**:
- `task_id`: 任务唯一标识
- `name`: 任务名称
- `payload`: 任务数据
- `priority`: 优先级（LOW/NORMAL/HIGH/CRITICAL）
- `timeout`: 超时时间
- `status`: 任务状态

**方法**:
- `start_processing(node_id)`: 开始处理
- `complete(data)`: 完成任务
- `fail(error)`: 标记失败
- `cancel()`: 取消任务
- `to_dict()`: 转换为字典

**状态转换**:
```
PENDING ──(调度)──> QUEUED
QUEUED ──(开始处理)──> PROCESSING
PROCESSING ──(完成)──> COMPLETED
PROCESSING ──(失败)──> FAILED
ANY ──(取消)──> CANCELLED
```

### 3. Scheduler（调度器）

**职责**:
- 选择执行任务的节点
- 实现负载均衡策略

**接口**:
```python
class Scheduler(ABC):
    def select_node(self, task, nodes) -> Optional[EdgeNode]
    def schedule(self, task, nodes) -> bool
    def schedule_batch(self, tasks, nodes) -> Dict[str, bool]
```

**实现**:
1. **RoundRobinScheduler**: 轮询调度
2. **LeastLoadScheduler**: 最小负载调度
3. **WeightedScheduler**: 加权调度
4. **PriorityScheduler**: 优先级调度
5. **LocationAwareScheduler**: 位置感知调度

### 4. EdgeCluster（边缘集群）

**职责**:
- 管理一组边缘节点
- 提供统一的任务分发接口
- 收集集群统计信息

**属性**:
- `cluster_id`: 集群标识
- `scheduler`: 调度器实例
- `_nodes`: 节点集合

**方法**:
- `add_node(node)`: 添加节点
- `remove_node(node_id)`: 移除节点
- `submit_task(task)`: 提交任务
- `complete_task(task_id, node_id, result)`: 完成任务
- `health_check()`: 健康检查
- `get_cluster_stats()`: 获取统计信息

### 5. Coordinator（协调器）

**职责**:
- 管理多个边缘集群
- 协调任务分发
- 收集和聚合结果
- 监控系统状态

**属性**:
- `coordinator_id`: 协调器标识
- `_clusters`: 集群集合
- `_pending_tasks`: 待处理任务队列
- `_completed_tasks`: 已完成任务

**方法**:
- `add_cluster(cluster)`: 添加集群
- `remove_cluster(cluster_id)`: 移除集群
- `submit_task(task)`: 提交任务
- `complete_task(...)`: 完成任务
- `get_system_stats()`: 获取系统统计
- `health_check()`: 系统健康检查

### 6. DataProcessor（数据处理器）

**职责**:
- 过滤边缘数据
- 聚合时间序列数据
- 执行规则引擎

#### DataFilter（数据过滤器）

**属性**:
- `name`: 过滤器名称
- `_rules`: 过滤规则列表
- `_match_all`: 匹配模式（AND/OR）

**方法**:
- `add_rule(rule)`: 添加过滤规则
- `filter(data_points)`: 过滤数据点
- `matches(data_point)`: 检查单个数据点

#### DataAggregator（数据聚合器）

**属性**:
- `window_size`: 时间窗口大小
- `_buffer`: 数据缓冲区

**方法**:
- `add(data_point)`: 添加数据点
- `aggregate(type, source, metric)`: 执行聚合
- `get_window_data(...)`: 获取窗口数据

**聚合类型**:
- COUNT: 计数
- SUM: 求和
- AVG: 平均值
- MIN/MAX: 最小/最大值
- FIRST/LAST: 首/末值
- STDDEV: 标准差

#### RuleEngine（规则引擎）

**属性**:
- `_rules`: 规则列表
- `_handlers`: 动作处理器
- `_alert_callbacks`: 告警回调

**方法**:
- `add_rule(rule)`: 添加规则
- `process(data_point)`: 处理单个数据点
- `process_batch(data_points)`: 批量处理
- `register_alert_callback(callback)`: 注册告警回调

**规则动作**:
- FORWARD: 转发数据
- DROP: 丢弃数据
- TRANSFORM: 转换数据
- ALERT: 触发告警
- AGGREGATE: 聚合请求

### 7. CloudSync（云端同步）

**职责**:
- 管理边缘与云端的数据同步
- 处理配置下发
- 支持批量上传和重试

#### DataUploader（数据上传器）

**属性**:
- `connector`: 云端连接器
- `config`: 同步配置
- `_upload_queue`: 上传队列

**方法**:
- `queue_data(...)`: 数据入队
- `upload_batch()`: 执行批量上传
- `register_callback(callback)`: 注册回调

#### ConfigManager（配置管理器）

**属性**:
- `connector`: 云端连接器
- `node_id`: 节点标识
- `_config`: 远程配置
- `_overrides`: 本地覆盖

**方法**:
- `get(key, default)`: 获取配置值
- `set_override(key, value)`: 设置本地覆盖
- `sync_from_cloud()`: 从云端同步配置
- `watch(key, callback)`: 监视配置变更

#### CloudSyncManager（同步管理器）

**属性**:
- `node_id`: 节点标识
- `connector`: 云端连接器
- `uploader`: 数据上传器
- `config_manager`: 配置管理器

**方法**:
- `start()`: 启动同步
- `stop()`: 停止同步
- `sync_data(...)`: 同步数据
- `sync_batch()`: 执行批量同步
- `report_status(status)`: 上报状态

### 8. IoTGateway（IoT 网关）

**职责**:
- 管理 IoT 设备
- 收集传感器数据
- 实时数据分析
- 告警管理

#### DeviceRegistry（设备注册表）

**属性**:
- `_devices`: 设备集合
- `_device_types`: 设备类型索引

**方法**:
- `register(device)`: 注册设备
- `unregister(device_id)`: 注销设备
- `get_device(device_id)`: 获取设备
- `heartbeat(device_id)`: 设备心跳
- `check_device_health()`: 健康检查

#### DataBuffer（数据缓冲区）

**属性**:
- `max_size`: 最大容量
- `ttl`: 数据存活时间
- `_buffer`: 数据缓冲

**方法**:
- `add(reading)`: 添加读数
- `get_recent(count, device_id, data_type)`: 获取最近数据
- `get_time_range(start, end, device_id)`: 获取时间范围数据
- `get_latest(device_id, data_type)`: 获取最新数据

#### AlertManager（告警管理器）

**属性**:
- `_alerts`: 告警列表
- `_rules`: 告警规则
- `_callbacks`: 告警回调

**方法**:
- `add_rule(...)`: 添加告警规则
- `check_reading(reading)`: 检查读数
- `acknowledge_alert(alert_id)`: 确认告警
- `get_alerts(...)`: 获取告警列表

#### RealtimeAnalyzer（实时分析器）

**方法**:
- `calculate_stats(readings)`: 计算统计信息
- `detect_trend(readings)`: 检测趋势
- `detect_anomalies(readings, threshold)`: 检测异常
- `get_summary(device_id, data_type, buffer)`: 获取摘要

## 数据流设计

### 任务提交流程

```
1. 用户提交任务
2. Coordinator 选择集群（负载最低）
3. Cluster 使用 Scheduler 选择节点
4. Node 执行任务
5. Node 返回结果
6. Coordinator 收集结果
7. 触发回调（如果有）
```

### 数据处理流程

```
1. IoT 设备产生数据
2. IoT Gateway 接收数据
3. DataFilter 过滤无效数据
4. RuleEngine 执行规则
5. DataAggregator 聚合数据
6. DataUploader 上传到云端
7. 触发告警（如果需要）
```

### 云端同步流程

```
1. 边缘节点产生数据
2. DataUploader 队列数据
3. 批量上传到云端
4. 云端处理并存储
5. ConfigManager 下发新配置
6. 边缘节点应用配置
```

## 接口设计

### EdgeNode 接口

```python
class EdgeNode:
    def submit_task(self, task: Task) -> bool
    def complete_task(self, task_id: str, result: Any) -> Optional[Any]
    def fail_task(self, task_id: str, error: str) -> bool
    def heartbeat(self) -> None
    def is_alive(self, timeout: float) -> bool
    def get_stats(self) -> Dict[str, Any]
```

### Task 接口

```python
class Task:
    def start_processing(self, node_id: str) -> None
    def complete(self, data: Any) -> None
    def fail(self, error: str) -> None
    def cancel(self) -> bool
    def to_dict(self) -> Dict[str, Any]
```

### Scheduler 接口

```python
class Scheduler(ABC):
    def select_node(self, task: Task, nodes: List[EdgeNode]) -> Optional[EdgeNode]
    def schedule(self, task: Task, nodes: List[EdgeNode]) -> bool
    def schedule_batch(self, tasks: List[Task], nodes: List[EdgeNode]) -> Dict[str, bool]
```

### EdgeCluster 接口

```python
class EdgeCluster:
    def add_node(self, node: EdgeNode) -> bool
    def remove_node(self, node_id: str) -> bool
    def submit_task(self, task: Task) -> bool
    def complete_task(self, task_id: str, node_id: str, result: Any) -> bool
    def health_check(self) -> Dict[str, Any]
    def get_cluster_stats(self) -> Dict[str, Any]
```

### Coordinator 接口

```python
class Coordinator:
    def add_cluster(self, cluster: EdgeCluster) -> bool
    def remove_cluster(self, cluster_id: str) -> bool
    def submit_task(self, task: Task, cluster_id: str, callback: Callable) -> bool
    def complete_task(self, task_id: str, node_id: str, cluster_id: str, result: Any) -> bool
    def get_system_stats(self) -> Dict[str, Any]
    def health_check(self) -> Dict[str, Any]
```

### DataProcessor 接口

```python
class DataFilter:
    def add_rule(self, rule: FilterRule) -> DataFilter
    def filter(self, data_points: List[DataPoint]) -> List[DataPoint]
    def matches(self, data_point: DataPoint) -> bool

class DataAggregator:
    def add(self, data_point: DataPoint) -> None
    def aggregate(self, type: AggregationType, ...) -> Dict[str, Any]

class RuleEngine:
    def add_rule(self, rule: Rule) -> None
    def process(self, data_point: DataPoint) -> Optional[DataPoint]
    def process_batch(self, data_points: List[DataPoint]) -> List[DataPoint]
```

### CloudSync 接口

```python
class CloudConnector(ABC):
    def connect(self) -> bool
    def disconnect(self) -> None
    def upload_data(self, data: Dict) -> bool
    def download_data(self, data_type: str, since: float) -> List[Dict]
    def get_config(self, key: str) -> Dict
    def report_status(self, status: Dict) -> bool

class CloudSyncManager:
    def start(self) -> bool
    def stop(self) -> None
    def sync_data(self, type: str, id: str, data: Any) -> str
    def sync_batch(self) -> Dict
    def report_status(self, status: Dict) -> bool
```

### IoTGateway 接口

```python
class IoTGateway:
    def register_device(self, device: IoTDevice) -> bool
    def unregister_device(self, device_id: str) -> bool
    def receive_data(self, reading: SensorReading) -> Dict
    def add_alert_rule(self, **kwargs) -> None
    def get_device_summary(self, device_id: str) -> Dict
    def get_gateway_stats(self) -> Dict
```

## 扩展性设计

### 1. 调度器扩展

通过继承 `Scheduler` 基类，可以轻松添加新的调度策略：

```python
class CustomScheduler(Scheduler):
    def select_node(self, task, nodes):
        # 自定义调度逻辑
        pass
```

### 2. 节点类型扩展

通过 `NodeType` 枚举，可以添加新的节点类型：

```python
class NodeType(Enum):
    EDGE = "edge"
    FOG = "fog"
    CLOUD = "cloud"
    GPU = "gpu"  # 新增
```

### 3. 任务类型扩展

通过 `metadata` 字段，可以支持不同类型的任务：

```python
task = Task(
    name="image-processing",
    metadata={
        "type": "image",
        "format": "jpeg",
        "resolution": "1920x1080",
    }
)
```

### 4. 云端连接器扩展

通过继承 `CloudConnector` 基类，可以支持不同的云服务：

```python
class AWSConnector(CloudConnector):
    def connect(self):
        # AWS 连接逻辑
        pass

class AzureConnector(CloudConnector):
    def connect(self):
        # Azure 连接逻辑
        pass
```

### 5. 数据类型扩展

通过 `DataType` 枚举，可以添加新的传感器类型：

```python
class DataType(Enum):
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    PRESSURE = "pressure"
    ACCELEROMETER = "accelerometer"  # 新增
    GYROSCOPE = "gyroscope"  # 新增
```

## 性能考虑

### 1. 任务队列管理

使用双端队列（deque）管理任务队列，支持高效的入队和出队操作。

### 2. 节点选择优化

对于大量节点的场景，可以使用优先队列优化节点选择：

```python
import heapq

# 按负载因子排序的优先队列
heapq.heappush(available_nodes, (node.load_factor, node))
```

### 3. 结果缓存

对于重复查询，可以缓存任务结果：

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_task_result(task_id):
    return self._completed_tasks.get(task_id)
```

### 4. 数据缓冲区优化

使用 deque 的 maxlen 参数自动淘汰旧数据：

```python
buffer = deque(maxlen=10000)  # 自动淘汰超过 10000 的旧数据
```

### 5. 批量处理

减少 I/O 操作次数，提高吞吐量：

```python
# 不好的做法
for item in items:
    upload(item)

# 好的做法
upload_batch(items)
```

## 安全考虑

### 1. 任务验证

验证任务的合法性和完整性。

### 2. 节点认证

确保只有授权的节点可以加入集群。

### 3. 数据加密

在传输和存储过程中加密敏感数据。

### 4. 访问控制

实现基于角色的访问控制（RBAC）。

### 5. 数据完整性

使用校验和验证数据完整性：

```python
import hashlib

def calculate_checksum(data):
    return hashlib.md5(json.dumps(data).encode()).hexdigest()
```

## 参考资料

1. [Designing Data-Intensive Applications](https://dataintensive.net/)
2. [System Design Interview](https://www.amazon.com/System-Design-Interview-insiders-Second/dp/B08CMF2CQF)
3. [Edge Computing Architecture](https://www.edgecomputing.com/)
4. [IoT Architecture](https://en.wikipedia.org/wiki/Internet_of_things)
5. [Stream Processing](https://en.wikipedia.org/wiki/Stream_processing)

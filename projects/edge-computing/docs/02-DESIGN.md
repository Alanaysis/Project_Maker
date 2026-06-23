# 02 - 设计阶段

## 系统架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Coordinator                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  - 管理多个集群                                       │   │
│  │  - 协调任务分发                                       │   │
│  │  - 收集结果                                           │   │
│  │  - 系统监控                                           │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          v                v                v
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Cluster 1   │  │  Cluster 2   │  │  Cluster 3   │
│ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │
│ │ Node 1   │ │  │ │ Node 4   │ │  │ │ Node 7   │ │
│ │ Node 2   │ │  │ │ Node 5   │ │  │ │ Node 8   │ │
│ │ Node 3   │ │  │ │ Node 6   │ │  │ │ Node 9   │ │
│ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │
└──────────────┘  └──────────────┘  └──────────────┘
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

### 结果收集流程

```
1. Node 完成任务
2. Node 通知 Cluster
3. Cluster 通知 Coordinator
4. Coordinator 存储结果
5. 触发用户回调
6. 更新统计信息
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

## 安全考虑

### 1. 任务验证

验证任务的合法性和完整性。

### 2. 节点认证

确保只有授权的节点可以加入集群。

### 3. 数据加密

在传输和存储过程中加密敏感数据。

### 4. 访问控制

实现基于角色的访问控制（RBAC）。

## 参考资料

1. [Designing Data-Intensive Applications](https://dataintensive.net/)
2. [System Design Interview](https://www.amazon.com/System-Design-Interview-insiders-Second/dp/B08CMF2CQF)
3. [Edge Computing Architecture](https://www.edgecomputing.com/)

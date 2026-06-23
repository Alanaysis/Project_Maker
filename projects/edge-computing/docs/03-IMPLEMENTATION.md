# 03 - 实现阶段

## 实现概述

本文档详细说明边缘计算框架的实现细节，包括各组件的代码实现和关键算法。

## 核心组件实现

### 1. EdgeNode 实现

**文件**: `src/edge_node.py`

#### 关键实现

**节点状态管理**:
```python
def submit_task(self, task: Any) -> bool:
    if not self.is_available:
        self._task_queue.append(task)
        return False

    self._active_tasks[task.task_id] = {
        "task": task,
        "start_time": time.time(),
    }
    task.start_processing(self.node_id)

    # 有活跃任务时状态为 BUSY
    if self.current_load > 0:
        self.status = NodeStatus.BUSY

    return True
```

**指标收集**:
```python
def complete_task(self, task_id: str, result: Any = None) -> Optional[Any]:
    if task_id not in self._active_tasks:
        return None

    task_info = self._active_tasks.pop(task_id)
    processing_time = time.time() - task_info["start_time"]

    task = task_info["task"]
    task.complete(result)

    # 更新指标
    self.metrics.tasks_completed += 1
    self.metrics.total_processing_time += processing_time
    self._update_status()

    return result
```

#### 设计决策

1. **使用 deque 作为任务队列**: 支持高效的 FIFO 操作
2. **使用字典存储活跃任务**: 支持 O(1) 的任务查找和删除
3. **心跳机制**: 用于检测节点是否存活

### 2. Task 实现

**文件**: `src/task.py`

#### 关键实现

**任务生命周期管理**:
```python
def start_processing(self, node_id: str) -> None:
    self.status = TaskStatus.PROCESSING
    self.assigned_node = node_id
    self._started_at = time.time()

def complete(self, data: Any = None) -> None:
    self._completed_at = time.time()
    self.status = TaskStatus.COMPLETED
    self.result = TaskResult(
        task_id=self.task_id,
        success=True,
        data=data,
        processing_time=self.processing_time,
        node_id=self.assigned_node,
    )
    if self.callback:
        self.callback(self.result)
```

**优先级排序**:
```python
def __lt__(self, other: "Task") -> bool:
    """用于优先级排序"""
    return self.priority.value > other.priority.value
```

#### 设计决策

1. **使用枚举定义状态和优先级**: 类型安全，易于扩展
2. **支持回调机制**: 任务完成时自动触发回调
3. **使用 dataclass 存储结果**: 简洁的数据结构

### 3. Scheduler 实现

**文件**: `src/scheduler.py`

#### 调度算法实现

**轮询调度**:
```python
class RoundRobinScheduler(Scheduler):
    def __init__(self):
        self._index = 0

    def select_node(self, task: Task, nodes: List[EdgeNode]) -> Optional[EdgeNode]:
        if not nodes:
            return None

        for _ in range(len(nodes)):
            node = nodes[self._index % len(nodes)]
            self._index += 1
            if node.is_available:
                return node

        return None
```

**最小负载调度**:
```python
class LeastLoadScheduler(Scheduler):
    def select_node(self, task: Task, nodes: List[EdgeNode]) -> Optional[EdgeNode]:
        if not nodes:
            return None

        available = [n for n in nodes if n.is_available]
        if not available:
            return None

        return min(available, key=lambda n: n.load_factor)
```

**加权调度**:
```python
class WeightedScheduler(Scheduler):
    def select_node(self, task: Task, nodes: List[EdgeNode]) -> Optional[EdgeNode]:
        if not nodes:
            return None

        available = [n for n in nodes if n.is_available]
        if not available:
            return None

        # 计算权重：容量 * (1 - 负载因子)
        weights = []
        for node in available:
            weight = node.capacity * (1 - node.load_factor)
            weights.append(max(weight, 0.1))

        # 加权随机选择
        total = sum(weights)
        r = random.uniform(0, total)
        cumulative = 0.0

        for node, weight in zip(available, weights):
            cumulative += weight
            if r <= cumulative:
                return node

        return available[-1]
```

**优先级调度**:
```python
class PriorityScheduler(Scheduler):
    def __init__(self):
        self._rr_scheduler = RoundRobinScheduler()

    def select_node(self, task: Task, nodes: List[EdgeNode]) -> Optional[EdgeNode]:
        if not nodes:
            return None

        available = [n for n in nodes if n.is_available]
        if not available:
            return None

        if task.priority in (TaskPriority.HIGH, TaskPriority.CRITICAL):
            # 高优先级任务分配到负载最低的节点
            return min(available, key=lambda n: n.load_factor)
        else:
            # 普通任务使用轮询
            return self._rr_scheduler.select_node(task, available)
```

**位置感知调度**:
```python
class LocationAwareScheduler(Scheduler):
    def __init__(self, task_location: Optional[Dict[str, float]] = None):
        self.task_location = task_location or {"lat": 0.0, "lon": 0.0}

    def _calculate_distance(self, loc1, loc2) -> float:
        lat_diff = loc1.get("lat", 0) - loc2.get("lat", 0)
        lon_diff = loc1.get("lon", 0) - loc2.get("lon", 0)
        return (lat_diff ** 2 + lon_diff ** 2) ** 0.5

    def select_node(self, task: Task, nodes: List[EdgeNode]) -> Optional[EdgeNode]:
        if not nodes:
            return None

        available = [n for n in nodes if n.is_available]
        if not available:
            return None

        return min(
            available,
            key=lambda n: self._calculate_distance(
                self.task_location, n.location
            ),
        )
```

#### 设计决策

1. **抽象基类**: 定义统一的调度器接口
2. **策略模式**: 不同调度算法可以互换
3. **批量调度**: 支持一次调度多个任务

### 4. EdgeCluster 实现

**文件**: `src/edge_cluster.py`

#### 关键实现

**节点管理**:
```python
def add_node(self, node: EdgeNode) -> bool:
    if node.node_id in self._nodes:
        return False
    self._nodes[node.node_id] = node
    return True

def remove_node(self, node_id: str) -> bool:
    if node_id not in self._nodes:
        return False
    node = self._nodes[node_id]
    if node.current_load > 0:
        node.status = NodeStatus.OFFLINE
        return False
    del self._nodes[node_id]
    return True
```

**任务分发**:
```python
def submit_task(self, task: Task) -> bool:
    nodes = self.active_nodes
    if not nodes:
        return False

    success = self.scheduler.schedule(task, nodes)

    self._task_history.append({
        "task_id": task.task_id,
        "action": "submit",
        "success": success,
        "timestamp": time.time(),
    })

    return success
```

**健康检查**:
```python
def health_check(self) -> Dict[str, Any]:
    healthy_nodes = 0
    unhealthy_nodes = 0

    for node in self._nodes.values():
        if node.is_alive() and node.status != NodeStatus.OFFLINE:
            healthy_nodes += 1
        else:
            unhealthy_nodes += 1

    return {
        "cluster_id": self.cluster_id,
        "healthy": unhealthy_nodes == 0,
        "total_nodes": self.node_count,
        "healthy_nodes": healthy_nodes,
        "unhealthy_nodes": unhealthy_nodes,
    }
```

#### 设计决策

1. **任务历史记录**: 用于统计和调试
2. **优雅的节点移除**: 有活跃任务的节点标记为离线而不是直接删除
3. **使用调度器**: 解耦任务分发逻辑

### 5. Coordinator 实现

**文件**: `src/coordinator.py`

#### 关键实现

**任务提交**:
```python
def submit_task(self, task: Task, cluster_id: Optional[str] = None, callback: Optional[Callable] = None) -> bool:
    if callback:
        self._task_callbacks[task.task_id] = callback

    # 指定集群
    if cluster_id:
        cluster = self.get_cluster(cluster_id)
        if cluster:
            success = cluster.submit_task(task)
            if success:
                self._stats["tasks_submitted"] += 1
            return success
        return False

    # 自动选择集群（选择负载最低的）
    for cluster in sorted(
        self._clusters.values(),
        key=lambda c: c.current_load / max(c.total_capacity, 1),
    ):
        if cluster.submit_task(task):
            self._stats["tasks_submitted"] += 1
            return True

    # 没有可用集群，加入待处理队列
    self._pending_tasks.append(task)
    self._stats["tasks_queued"] += 1
    return False
```

**任务完成**:
```python
def complete_task(self, task_id: str, node_id: str, cluster_id: str, result: Any = None) -> bool:
    cluster = self.get_cluster(cluster_id)
    if cluster is None:
        return False

    success = cluster.complete_task(task_id, node_id, result)

    if success:
        self._stats["tasks_completed"] += 1
        self._completed_tasks[task_id] = TaskResult(
            task_id=task_id,
            success=True,
            data=result,
            node_id=node_id,
        )

        # 触发回调
        if task_id in self._task_callbacks:
            callback = self._task_callbacks.pop(task_id)
            callback(self._completed_tasks[task_id])

        # 尝试处理待处理队列
        self._process_pending_tasks()

    return success
```

**待处理任务处理**:
```python
def _process_pending_tasks(self) -> None:
    if not self._pending_tasks:
        return

    remaining = []
    for task in self._pending_tasks:
        success = False
        for cluster in self._clusters.values():
            if cluster.submit_task(task):
                success = True
                self._stats["tasks_submitted"] += 1
                break

        if not success:
            remaining.append(task)

    self._pending_tasks = remaining
```

#### 设计决策

1. **自动集群选择**: 选择负载最低的集群
2. **待处理队列**: 没有可用集群时暂存任务
3. **回调机制**: 支持异步结果通知
4. **统计信息**: 跟踪系统运行状态

## 关键算法

### 1. 负载因子计算

```python
@property
def load_factor(self) -> float:
    if self.capacity == 0:
        return 1.0
    return self.current_load / self.capacity
```

### 2. 节点可用性检查

```python
@property
def is_available(self) -> bool:
    return (
        self.status in (NodeStatus.IDLE, NodeStatus.BUSY)
        and self.current_load < self.capacity
    )
```

### 3. 距离计算（简化版）

```python
def _calculate_distance(self, loc1, loc2) -> float:
    lat_diff = loc1.get("lat", 0) - loc2.get("lat", 0)
    lon_diff = loc1.get("lon", 0) - loc2.get("lon", 0)
    return (lat_diff ** 2 + lon_diff ** 2) ** 0.5
```

## 错误处理

### 1. 任务提交失败

当节点不可用时，任务被加入队列：
```python
if not self.is_available:
    self._task_queue.append(task)
    return False
```

### 2. 任务完成失败

当任务 ID 不存在时，返回 None：
```python
if task_id not in self._active_tasks:
    return None
```

### 3. 节点移除失败

当节点有活跃任务时，标记为离线：
```python
if node.current_load > 0:
    node.status = NodeStatus.OFFLINE
    return False
```

## 性能优化

### 1. 数据结构选择

- 使用 `deque` 作为任务队列：O(1) 的入队和出队
- 使用 `dict` 存储活跃任务：O(1) 的查找和删除
- 使用 `list` 存储节点：支持快速遍历

### 2. 算法优化

- 轮询调度：O(1) 的节点选择
- 最小负载调度：O(n) 的节点选择
- 加权调度：O(n) 的节点选择

### 3. 内存优化

- 任务完成后及时清理
- 使用弱引用存储回调（可选）

## 测试策略

### 1. 单元测试

每个组件都有对应的测试文件：
- `test_edge_node.py`
- `test_task.py`
- `test_scheduler.py`
- `test_edge_cluster.py`
- `test_coordinator.py`

### 2. 测试覆盖

测试覆盖以下场景：
- 正常流程
- 边界条件
- 错误处理
- 并发场景（可选）

### 3. 测试工具

使用 pytest 作为测试框架，支持：
- 参数化测试
- 测试夹具
- 测试覆盖率

## 参考资料

1. [Python 标准库文档](https://docs.python.org/3/library/)
2. [pytest 文档](https://docs.pytest.org/)
3. [设计模式](https://refactoring.guru/design-patterns)

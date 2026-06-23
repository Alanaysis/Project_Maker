# 04 - 测试阶段

## 测试概述

本文档详细说明边缘计算框架的测试策略、测试用例和测试结果。

## 测试策略

### 1. 测试金字塔

```
        /\
       /  \        E2E 测试（少量）
      /    \
     /------\      集成测试（适量）
    /        \
   /----------\    单元测试（大量）
```

### 2. 测试类型

- **单元测试**: 测试单个组件的功能
- **集成测试**: 测试组件之间的交互
- **端到端测试**: 测试完整的业务流程

### 3. 测试覆盖率目标

- 语句覆盖率: > 90%
- 分支覆盖率: > 80%
- 函数覆盖率: 100%

## 测试环境

### 依赖

```bash
pip install pytest
pip install pytest-cov  # 可选，用于覆盖率报告
```

### 运行测试

```bash
# 运行所有测试
python3 -m pytest tests/ -v

# 运行特定测试文件
python3 -m pytest tests/test_edge_node.py -v

# 运行带覆盖率的测试
python3 -m pytest tests/ -v --cov=src
```

## 测试用例

### 1. EdgeNode 测试

**文件**: `tests/test_edge_node.py`

#### 测试用例列表

| 测试用例 | 描述 | 预期结果 |
|---------|------|---------|
| test_node_creation | 测试节点创建 | 属性正确初始化 |
| test_node_with_custom_id | 测试自定义 ID | ID 正确设置 |
| test_node_types | 测试节点类型 | 类型正确 |
| test_submit_task | 测试提交任务 | 任务成功提交 |
| test_submit_task_when_full | 测试满载提交 | 任务被拒绝 |
| test_complete_task | 测试完成任务 | 任务状态更新 |
| test_fail_task | 测试任务失败 | 失败计数增加 |
| test_node_status_updates | 测试状态更新 | 状态正确转换 |
| test_heartbeat | 测试心跳 | 心跳时间更新 |
| test_node_stats | 测试统计信息 | 统计数据正确 |
| test_node_repr | 测试字符串表示 | 格式正确 |

#### 关键测试代码

```python
def test_submit_task(self):
    """测试提交任务"""
    node = EdgeNode(capacity=2)
    task = Task(name="test-task")

    result = node.submit_task(task)

    assert result is True
    assert node.current_load == 1
    assert task.status == TaskStatus.PROCESSING
    assert task.assigned_node == node.node_id

def test_node_status_updates(self):
    """测试节点状态更新"""
    node = EdgeNode(capacity=2)

    assert node.status == NodeStatus.IDLE

    task1 = Task(name="task-1")
    node.submit_task(task1)
    assert node.status == NodeStatus.BUSY

    task2 = Task(name="task-2")
    node.submit_task(task2)
    assert node.status == NodeStatus.BUSY

    node.complete_task(task1.task_id)
    assert node.status == NodeStatus.BUSY

    node.complete_task(task2.task_id)
    assert node.status == NodeStatus.IDLE
```

### 2. Task 测试

**文件**: `tests/test_task.py`

#### 测试用例列表

| 测试用例 | 描述 | 预期结果 |
|---------|------|---------|
| test_task_creation | 测试任务创建 | 属性正确初始化 |
| test_task_with_custom_id | 测试自定义 ID | ID 正确设置 |
| test_task_priority | 测试优先级 | 优先级正确 |
| test_task_priority_ordering | 测试优先级排序 | 排序正确 |
| test_task_lifecycle | 测试生命周期 | 状态正确转换 |
| test_task_failure | 测试任务失败 | 失败状态正确 |
| test_task_cancellation | 测试任务取消 | 取消成功 |
| test_cannot_cancel_finished_task | 测试取消已完成任务 | 取消失败 |
| test_task_timing | 测试计时 | 时间计算正确 |
| test_task_callback | 测试回调 | 回调触发正确 |
| test_task_to_dict | 测试转字典 | 字典格式正确 |
| test_task_repr | 测试字符串表示 | 格式正确 |

#### 关键测试代码

```python
def test_task_lifecycle(self):
    """测试任务生命周期"""
    task = Task(name="lifecycle-task")

    # 初始状态
    assert task.status == TaskStatus.PENDING
    assert task.assigned_node is None

    # 开始处理
    task.start_processing("node-1")
    assert task.status == TaskStatus.PROCESSING
    assert task.assigned_node == "node-1"

    # 完成
    task.complete({"result": "success"})
    assert task.status == TaskStatus.COMPLETED
    assert task.is_finished is True
    assert task.result is not None
    assert task.result.success is True

def test_task_callback(self):
    """测试任务回调"""
    callback_results = []

    def callback(result):
        callback_results.append(result)

    task = Task(name="callback-task", callback=callback)
    task.start_processing("node-1")
    task.complete({"data": "test"})

    assert len(callback_results) == 1
    assert callback_results[0].success is True
```

### 3. Scheduler 测试

**文件**: `tests/test_scheduler.py`

#### 测试用例列表

| 测试用例 | 描述 | 预期结果 |
|---------|------|---------|
| test_basic_scheduling | 测试基本调度 | 任务均匀分配 |
| test_schedule_batch | 测试批量调度 | 所有任务调度成功 |
| test_no_available_nodes | 测试无可用节点 | 调度失败 |
| test_select_least_loaded | 测试最小负载选择 | 选择负载最低的节点 |
| test_equal_load_distribution | 测试等负载分配 | 选择第一个节点 |
| test_capacity_based_scheduling | 测试基于容量的调度 | 大容量节点接收更多任务 |
| test_high_priority_to_best_node | 测试高优先级调度 | 高优先级任务分配到最佳节点 |
| test_select_nearest_node | 测试最近节点选择 | 选择距离最近的节点 |

#### 关键测试代码

```python
def test_basic_scheduling(self):
    """测试基本调度"""
    scheduler = RoundRobinScheduler()
    nodes = [
        EdgeNode(name="node-1", capacity=2),
        EdgeNode(name="node-2", capacity=2),
        EdgeNode(name="node-3", capacity=2),
    ]

    task1 = Task(name="task-1")
    task2 = Task(name="task-2")
    task3 = Task(name="task-3")

    scheduler.schedule(task1, nodes)
    scheduler.schedule(task2, nodes)
    scheduler.schedule(task3, nodes)

    assert nodes[0].current_load == 1
    assert nodes[1].current_load == 1
    assert nodes[2].current_load == 1

def test_select_least_loaded(self):
    """测试选择负载最低的节点"""
    scheduler = LeastLoadScheduler()

    node1 = EdgeNode(name="node-1", capacity=5)
    node2 = EdgeNode(name="node-2", capacity=5)

    # 给 node1 添加一些负载
    for i in range(3):
        task = Task(name=f"task-{i}")
        node1.submit_task(task)

    nodes = [node1, node2]
    new_task = Task(name="new-task")

    scheduler.schedule(new_task, nodes)

    # 应该选择 node2（负载更低）
    assert node2.current_load == 1
    assert node1.current_load == 3
```

### 4. EdgeCluster 测试

**文件**: `tests/test_edge_cluster.py`

#### 测试用例列表

| 测试用例 | 描述 | 预期结果 |
|---------|------|---------|
| test_cluster_creation | 测试集群创建 | 属性正确初始化 |
| test_add_node | 测试添加节点 | 节点添加成功 |
| test_add_duplicate_node | 测试重复添加 | 添加失败 |
| test_remove_node | 测试移除节点 | 节点移除成功 |
| test_remove_node_with_active_tasks | 测试移除有任务的节点 | 移除失败 |
| test_submit_task | 测试提交任务 | 任务调度成功 |
| test_submit_task_no_nodes | 测试无节点提交 | 提交失败 |
| test_submit_tasks_batch | 测试批量提交 | 所有任务提交成功 |
| test_complete_task | 测试完成任务 | 任务完成成功 |
| test_complete_task_wrong_node | 测试错误节点完成 | 完成失败 |
| test_cluster_stats | 测试集群统计 | 统计数据正确 |
| test_health_check | 测试健康检查 | 健康状态正确 |
| test_health_check_with_offline_node | 测试有离线节点 | 健康状态为 false |
| test_active_nodes | 测试活跃节点 | 只返回在线节点 |
| test_cluster_repr | 测试字符串表示 | 格式正确 |

#### 关键测试代码

```python
def test_submit_task(self):
    """测试提交任务"""
    cluster = EdgeCluster(scheduler=RoundRobinScheduler())
    node = EdgeNode(name="node-1", capacity=5)

    cluster.add_node(node)

    task = Task(name="task-1")
    result = cluster.submit_task(task)

    assert result is True
    assert node.current_load == 1

def test_health_check(self):
    """测试健康检查"""
    cluster = EdgeCluster()

    node = EdgeNode(name="node-1", capacity=5)
    cluster.add_node(node)

    health = cluster.health_check()

    assert health["healthy"] is True
    assert health["total_nodes"] == 1
    assert health["healthy_nodes"] == 1
    assert health["unhealthy_nodes"] == 0
```

### 5. Coordinator 测试

**文件**: `tests/test_coordinator.py`

#### 测试用例列表

| 测试用例 | 描述 | 预期结果 |
|---------|------|---------|
| test_coordinator_creation | 测试协调器创建 | 属性正确初始化 |
| test_add_cluster | 测试添加集群 | 集群添加成功 |
| test_add_duplicate_cluster | 测试重复添加 | 添加失败 |
| test_remove_cluster | 测试移除集群 | 集群移除成功 |
| test_remove_cluster_with_load | 测试移除有负载的集群 | 移除失败 |
| test_submit_task_to_specific_cluster | 测试提交到指定集群 | 任务提交成功 |
| test_submit_task_auto_select_cluster | 测试自动选择集群 | 任务提交成功 |
| test_submit_task_no_cluster | 测试无集群提交 | 任务加入队列 |
| test_submit_tasks_batch | 测试批量提交 | 所有任务提交成功 |
| test_complete_task | 测试完成任务 | 任务完成成功 |
| test_task_callback | 测试任务回调 | 回调触发正确 |
| test_get_task_result | 测试获取结果 | 结果正确 |
| test_system_stats | 测试系统统计 | 统计数据正确 |
| test_health_check | 测试健康检查 | 健康状态正确 |
| test_coordinator_repr | 测试字符串表示 | 格式正确 |

#### 关键测试代码

```python
def test_submit_task_auto_select_cluster(self):
    """测试自动选择集群提交任务"""
    coordinator = Coordinator()

    cluster1 = EdgeCluster(cluster_id="cluster-1")
    node1 = EdgeNode(name="node-1", capacity=5)
    cluster1.add_node(node1)

    cluster2 = EdgeCluster(cluster_id="cluster-2")
    node2 = EdgeNode(name="node-2", capacity=10)
    cluster2.add_node(node2)

    coordinator.add_cluster(cluster1)
    coordinator.add_cluster(cluster2)

    task = Task(name="task-1")
    result = coordinator.submit_task(task)

    assert result is True

def test_task_callback(self):
    """测试任务回调"""
    coordinator = Coordinator()

    cluster = EdgeCluster(cluster_id="cluster-1")
    node = EdgeNode(name="node-1", capacity=5)
    cluster.add_node(node)

    coordinator.add_cluster(cluster)

    callback_results = []

    def callback(result):
        callback_results.append(result)

    task = Task(name="task-1")
    coordinator.submit_task(task, cluster_id="cluster-1", callback=callback)

    coordinator.complete_task(
        task.task_id, node.node_id, "cluster-1", {"output": "done"}
    )

    assert len(callback_results) == 1
    assert callback_results[0].success is True
```

## 测试结果

### 测试执行结果

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0
collected 63 items

tests/test_coordinator.py::TestCoordinator::test_coordinator_creation PASSED
tests/test_coordinator.py::TestCoordinator::test_add_cluster PASSED
tests/test_coordinator.py::TestCoordinator::test_add_duplicate_cluster PASSED
tests/test_coordinator.py::TestCoordinator::test_remove_cluster PASSED
tests/test_coordinator.py::TestCoordinator::test_remove_cluster_with_load PASSED
tests/test_coordinator.py::TestCoordinator::test_submit_task_to_specific_cluster PASSED
tests/test_coordinator.py::TestCoordinator::test_submit_task_auto_select_cluster PASSED
tests/test_coordinator.py::TestCoordinator::test_submit_task_no_cluster PASSED
tests/test_coordinator.py::TestCoordinator::test_submit_tasks_batch PASSED
tests/test_coordinator.py::TestCoordinator::test_complete_task PASSED
tests/test_coordinator.py::TestCoordinator::test_task_callback PASSED
tests/test_coordinator.py::TestCoordinator::test_get_task_result PASSED
tests/test_coordinator.py::TestCoordinator::test_system_stats PASSED
tests/test_coordinator.py::TestCoordinator::test_health_check PASSED
tests/test_coordinator.py::TestCoordinator::test_coordinator_repr PASSED
tests/test_edge_cluster.py::TestEdgeCluster::test_cluster_creation PASSED
tests/test_edge_cluster.py::TestEdgeCluster::test_add_node PASSED
tests/test_edge_cluster.py::TestEdgeCluster::test_add_duplicate_node PASSED
tests/test_edge_cluster.py::TestEdgeCluster::test_remove_node PASSED
tests/test_edge_cluster.py::TestEdgeCluster::test_remove_node_with_active_tasks PASSED
tests/test_edge_cluster.py::TestEdgeCluster::test_submit_task PASSED
tests/test_edge_cluster.py::TestEdgeCluster::test_submit_task_no_nodes PASSED
tests/test_edge_cluster.py::TestEdgeCluster::test_submit_tasks_batch PASSED
tests/test_edge_cluster.py::TestEdgeCluster::test_complete_task PASSED
tests/test_edge_cluster.py::TestEdgeCluster::test_complete_task_wrong_node PASSED
tests/test_edge_cluster.py::TestEdgeCluster::test_cluster_stats PASSED
tests/test_edge_cluster.py::TestEdgeCluster::test_health_check PASSED
tests/test_edge_cluster.py::TestEdgeCluster::test_health_check_with_offline_node PASSED
tests/test_edge_cluster.py::TestEdgeCluster::test_active_nodes PASSED
tests/test_edge_cluster.py::TestEdgeCluster::test_cluster_repr PASSED
tests/test_edge_node.py::TestEdgeNode::test_node_creation PASSED
tests/test_edge_node.py::TestEdgeNode::test_node_with_custom_id PASSED
tests/test_edge_node.py::TestEdgeNode::test_node_types PASSED
tests/test_edge_node.py::TestEdgeNode::test_submit_task PASSED
tests/test_edge_node.py::TestEdgeNode::test_submit_task_when_full PASSED
tests/test_edge_node.py::TestEdgeNode::test_complete_task PASSED
tests/test_edge_node.py::TestEdgeNode::test_fail_task PASSED
tests/test_edge_node.py::TestEdgeNode::test_node_status_updates PASSED
tests/test_edge_node.py::TestEdgeNode::test_heartbeat PASSED
tests/test_edge_node.py::TestEdgeNode::test_node_stats PASSED
tests/test_edge_node.py::TestEdgeNode::test_node_repr PASSED
tests/test_scheduler.py::TestRoundRobinScheduler::test_basic_scheduling PASSED
tests/test_scheduler.py::TestRoundRobinScheduler::test_schedule_batch PASSED
tests/test_scheduler.py::TestRoundRobinScheduler::test_no_available_nodes PASSED
tests/test_scheduler.py::TestLeastLoadScheduler::test_select_least_loaded PASSED
tests/test_scheduler.py::TestLeastLoadScheduler::test_equal_load_distribution PASSED
tests/test_scheduler.py::TestWeightedScheduler::test_capacity_based_scheduling PASSED
tests/test_scheduler.py::TestPriorityScheduler::test_high_priority_to_best_node PASSED
tests/test_scheduler.py::TestLocationAwareScheduler::test_select_nearest_node PASSED
tests/test_task.py::TestTask::test_task_creation PASSED
tests/test_task.py::TestTask::test_task_with_custom_id PASSED
tests/test_task.py::TestTask::test_task_priority PASSED
tests/test_task.py::TestTask::test_task_priority_ordering PASSED
tests/test_task.py::TestTask::test_task_lifecycle PASSED
tests/test_task.py::TestTask::test_task_failure PASSED
tests/test_task.py::TestTask::test_task_cancellation PASSED
tests/test_task.py::TestTask::test_cannot_cancel_finished_task PASSED
tests/test_task.py::TestTask::test_task_timing PASSED
tests/test_task.py::TestTask::test_task_callback PASSED
tests/test_task.py::TestTask::test_task_to_dict PASSED
tests/test_task.py::TestTask::test_task_repr PASSED
tests/test_task.py::TestTaskResult::test_result_creation PASSED
tests/test_task.py::TestTaskResult::test_failed_result PASSED

============================== 63 passed in 0.07s ===============================
```

### 测试统计

- **总测试数**: 63
- **通过**: 63
- **失败**: 0
- **错误**: 0
- **执行时间**: 0.07s

## 测试最佳实践

### 1. 测试命名规范

- 测试文件: `test_<module>.py`
- 测试类: `Test<ClassName>`
- 测试方法: `test_<功能描述>`

### 2. 测试结构

每个测试遵循 AAA 模式：
- **Arrange**: 准备测试数据
- **Act**: 执行被测试的操作
- **Assert**: 验证结果

### 3. 测试独立性

每个测试应该：
- 独立运行，不依赖其他测试
- 不修改共享状态
- 清理创建的资源

### 4. 测试覆盖

- 正常流程测试
- 边界条件测试
- 错误处理测试
- 并发场景测试（可选）

## 持续集成

### GitHub Actions 配置示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11, 3.12]

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pytest
    - name: Run tests
      run: |
        python -m pytest tests/ -v
```

## 参考资料

1. [pytest 官方文档](https://docs.pytest.org/)
2. [Python 测试最佳实践](https://docs.python.org/3/library/unittest.html)
3. [测试驱动开发](https://en.wikipedia.org/wiki/Test-driven_development)

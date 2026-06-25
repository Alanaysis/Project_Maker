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

### 6. DataProcessor 测试

**文件**: `tests/test_data_processor.py`

#### 测试用例列表

| 测试用例 | 描述 | 预期结果 |
|---------|------|---------|
| test_eq_operator | 测试等于操作符 | 正确匹配 |
| test_gt_operator | 测试大于操作符 | 正确比较 |
| test_in_operator | 测试在列表中 | 正确匹配 |
| test_tags_field | 测试标签字段过滤 | 正确过滤 |
| test_negate | 测试取反 | 正确取反 |
| test_single_rule | 测试单规则过滤 | 正确过滤 |
| test_and_mode | 测试 AND 模式 | 所有条件匹配 |
| test_or_mode | 测试 OR 模式 | 任一条件匹配 |
| test_avg_aggregation | 测试平均值聚合 | 计算正确 |
| test_count_aggregation | 测试计数聚合 | 计数正确 |
| test_min_max_aggregation | 测试最小最大值 | 结果正确 |
| test_forward_rule | 测试转发规则 | 数据转发 |
| test_drop_rule | 测试丢弃规则 | 数据丢弃 |
| test_transform_rule | 测试转换规则 | 数据转换 |
| test_alert_rule | 测试告警规则 | 触发告警 |
| test_rule_priority | 测试规则优先级 | 高优先级先执行 |
| test_process_batch | 测试批量处理 | 正确处理 |
| test_stats | 测试统计信息 | 统计正确 |

#### 关键测试代码

```python
def test_eq_operator(self):
    """测试等于操作符"""
    rule = FilterRule(field="source", operator=FilterOperator.EQ, value="sensor-1")
    dp_match = DataPoint(timestamp=0, source="sensor-1", metric="test", value=1)
    dp_no_match = DataPoint(timestamp=0, source="sensor-2", metric="test", value=1)

    assert rule.matches(dp_match) is True
    assert rule.matches(dp_no_match) is False

def test_drop_rule(self):
    """测试丢弃规则"""
    engine = RuleEngine()
    engine.add_rule(Rule(
        rule_id="r1",
        name="drop bad data",
        conditions=[FilterRule(field="value", operator=FilterOperator.LT, value=0)],
        action=RuleAction.DROP,
    ))

    dp_good = DataPoint(timestamp=0, source="s", metric="m", value=10)
    dp_bad = DataPoint(timestamp=0, source="s", metric="m", value=-1)

    assert engine.process(dp_good) is not None
    assert engine.process(dp_bad) is None
```

### 7. CloudSync 测试

**文件**: `tests/test_cloud_sync.py`

#### 测试用例列表

| 测试用例 | 描述 | 预期结果 |
|---------|------|---------|
| test_connect_disconnect | 测试连接断开 | 状态正确 |
| test_upload_data | 测试上传数据 | 上传成功 |
| test_upload_when_disconnected | 测试断开时上传 | 上传失败 |
| test_download_data | 测试下载数据 | 下载成功 |
| test_get_config | 测试获取配置 | 配置正确 |
| test_report_status | 测试状态上报 | 上报成功 |
| test_queue_data | 测试数据入队 | 入队成功 |
| test_upload_batch | 测试批量上传 | 上传成功 |
| test_upload_batch_size_limit | 测试批量大小限制 | 正确限制 |
| test_upload_callback | 测试上传回调 | 回调触发 |
| test_upload_stats | 测试上传统计 | 统计正确 |
| test_get_default | 测试获取默认配置 | 默认值正确 |
| test_set_override | 测试设置覆盖 | 覆盖生效 |
| test_remove_override | 测试移除覆盖 | 覆盖移除 |
| test_sync_from_cloud | 测试云端同步 | 同步成功 |
| test_watch_config_changes | 测试配置监视 | 变更通知 |
| test_start_stop | 测试启动停止 | 状态正确 |
| test_sync_data | 测试数据同步 | 同步成功 |
| test_sync_batch | 测试批量同步 | 同步成功 |
| test_report_status | 测试状态上报 | 上报成功 |
| test_sync_history | 测试同步历史 | 历史正确 |

#### 关键测试代码

```python
def test_upload_batch(self, mock_connector, sync_config):
    """测试批量上传"""
    uploader = DataUploader(mock_connector, sync_config)

    # 入队多个数据
    for i in range(5):
        uploader.queue_data(
            data_type="sensor",
            data_id=f"sensor-{i}",
            data={"value": i * 10.0},
        )

    # 执行批量上传
    result = uploader.upload_batch()

    assert result["success"] is True
    assert result["uploaded"] == 5
    assert uploader.get_pending_count() == 0

def test_sync_from_cloud(self, mock_connector):
    """测试从云端同步配置"""
    manager = ConfigManager(mock_connector, "node-1")

    result = manager.sync_from_cloud()
    assert result["success"] is True
    assert manager.get("sync_interval") == 60
```

### 8. IoTGateway 测试

**文件**: `tests/test_iot_gateway.py`

#### 测试用例列表

| 测试用例 | 描述 | 预期结果 |
|---------|------|---------|
| test_device_creation | 测试设备创建 | 属性正确 |
| test_update_status | 测试状态更新 | 状态正确 |
| test_is_alive | 测试存活检查 | 检查正确 |
| test_to_dict | 测试字典转换 | 转换正确 |
| test_reading_creation | 测试读数创建 | 属性正确 |
| test_register_device | 测试设备注册 | 注册成功 |
| test_register_duplicate | 测试重复注册 | 注册失败 |
| test_unregister_device | 测试设备注销 | 注销成功 |
| test_get_device | 测试获取设备 | 获取成功 |
| test_get_devices_by_type | 测试按类型获取 | 获取成功 |
| test_get_online_devices | 测试获取在线设备 | 获取成功 |
| test_heartbeat | 测试心跳 | 心跳成功 |
| test_check_device_health | 测试健康检查 | 检查正确 |
| test_stats | 测试统计信息 | 统计正确 |
| test_add_reading | 测试添加读数 | 添加成功 |
| test_get_recent | 测试获取最近数据 | 获取成功 |
| test_max_size | 测试最大容量 | 限制正确 |
| test_clear | 测试清空缓冲区 | 清空成功 |
| test_add_rule | 测试添加规则 | 添加成功 |
| test_check_triggers_alert | 测试触发告警 | 告警触发 |
| test_no_alert_within_threshold | 测试阈值内不触发 | 无告警 |
| test_alert_callback | 测试告警回调 | 回调触发 |
| test_acknowledge_alert | 测试确认告警 | 确认成功 |
| test_get_alerts_by_device | 测试按设备获取告警 | 获取成功 |
| test_calculate_stats | 测试统计计算 | 计算正确 |
| test_detect_trend_increasing | 测试上升趋势 | 趋势正确 |
| test_detect_trend_stable | 测试稳定趋势 | 趋势正确 |
| test_detect_anomalies | 测试异常检测 | 检测正确 |
| test_gateway_creation | 测试网关创建 | 创建成功 |
| test_register_device | 测试设备注册 | 注册成功 |
| test_start_stop | 测试启动停止 | 状态正确 |
| test_receive_data | 测试接收数据 | 接收成功 |
| test_receive_data_triggers_alert | 测试数据触发告警 | 告警触发 |
| test_data_callback | 测试数据回调 | 回调触发 |
| test_get_device_summary | 测试设备摘要 | 摘要正确 |
| test_gateway_stats | 测试网关统计 | 统计正确 |
| test_device_offline_after_timeout | 测试超时离线 | 离线正确 |

#### 关键测试代码

```python
def test_receive_data_triggers_alert(self, sample_device):
    """测试数据接收触发告警"""
    gateway = IoTGateway()
    gateway.register_device(sample_device)
    gateway.start()

    # 添加告警规则
    gateway.add_alert_rule(
        rule_id="r1",
        data_type=DataType.TEMPERATURE,
        condition="gt",
        threshold=30.0,
        level=AlertLevel.WARNING,
    )

    # 高温数据
    reading = SensorReading(
        reading_id="r-1",
        device_id="device-1",
        data_type=DataType.TEMPERATURE,
        value=35.0,
        unit="°C",
    )

    result = gateway.receive_data(reading)
    assert result["success"] is True
    assert result["alert"] is not None

def test_detect_anomalies(self):
    """测试异常检测"""
    analyzer = RealtimeAnalyzer()

    # 正常数据 + 异常值
    readings = [
        SensorReading(f"r-{i}", "device-1", DataType.TEMPERATURE, 25.0, "°C")
        for i in range(9)
    ]
    readings.append(
        SensorReading("r-anomaly", "device-1", DataType.TEMPERATURE, 100.0, "°C")
    )

    anomalies = analyzer.detect_anomalies(readings)
    assert len(anomalies) == 1
    assert anomalies[0].value == 100.0
```

## 测试结果

### 测试执行结果

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0
collected 147 items

tests/test_coordinator.py::TestCoordinator::test_coordinator_creation PASSED
tests/test_coordinator.py::TestCoordinator::test_add_cluster PASSED
...
tests/test_data_processor.py::TestRuleEngine::test_stats PASSED
tests/test_cloud_sync.py::TestCloudSyncManager::test_config_sync PASSED
tests/test_iot_gateway.py::TestIoTGateway::test_device_offline_after_timeout PASSED

============================== 147 passed in 0.12s ==============================
```

### 测试统计

- **总测试数**: 147
- **通过**: 147
- **失败**: 0
- **错误**: 0
- **执行时间**: 0.12s

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

### 5. 测试夹具

使用 pytest 夹具管理测试数据：

```python
@pytest.fixture
def mock_connector():
    """创建模拟云端连接器"""
    connector = MockCloudConnector(endpoint="https://test.cloud.com")
    connector.connect()
    return connector

@pytest.fixture
def sample_device():
    """创建测试设备"""
    return IoTDevice(
        device_id="device-1",
        name="Temperature Sensor",
        device_type="sensor",
    )
```

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

"""Edge Computing Framework - 边缘计算框架

实现边缘节点管理、任务分发、结果收集、负载均衡、数据处理、云端同步和 IoT 网关。
"""

from .edge_node import EdgeNode, NodeType, NodeStatus, NodeMetrics
from .task import Task, TaskStatus, TaskPriority, TaskResult
from .scheduler import (
    Scheduler, RoundRobinScheduler, LeastLoadScheduler,
    WeightedScheduler, PriorityScheduler, LocationAwareScheduler,
)
from .edge_cluster import EdgeCluster
from .coordinator import Coordinator
from .data_processor import (
    DataPoint, FilterOperator, AggregationType, RuleAction,
    FilterRule, DataFilter, DataAggregator, Rule, RuleEngine,
)
from .cloud_sync import (
    SyncStatus, SyncDirection, ConflictResolution,
    SyncConfig, SyncRecord, CloudConnector, MockCloudConnector,
    DataUploader, ConfigManager, CloudSyncManager,
)
from .iot_gateway import (
    DeviceStatus, DataType, AlertLevel,
    IoTDevice, SensorReading, Alert,
    DeviceRegistry, DataBuffer, AlertManager, RealtimeAnalyzer, IoTGateway,
)

__version__ = "0.2.0"
__all__ = [
    # Edge Node
    "EdgeNode",
    "NodeType",
    "NodeStatus",
    "NodeMetrics",
    # Task
    "Task",
    "TaskStatus",
    "TaskPriority",
    "TaskResult",
    # Scheduler
    "Scheduler",
    "RoundRobinScheduler",
    "LeastLoadScheduler",
    "WeightedScheduler",
    "PriorityScheduler",
    "LocationAwareScheduler",
    # Edge Cluster
    "EdgeCluster",
    # Coordinator
    "Coordinator",
    # Data Processor
    "DataPoint",
    "FilterOperator",
    "AggregationType",
    "RuleAction",
    "FilterRule",
    "DataFilter",
    "DataAggregator",
    "Rule",
    "RuleEngine",
    # Cloud Sync
    "SyncStatus",
    "SyncDirection",
    "ConflictResolution",
    "SyncConfig",
    "SyncRecord",
    "CloudConnector",
    "MockCloudConnector",
    "DataUploader",
    "ConfigManager",
    "CloudSyncManager",
    # IoT Gateway
    "DeviceStatus",
    "DataType",
    "AlertLevel",
    "IoTDevice",
    "SensorReading",
    "Alert",
    "DeviceRegistry",
    "DataBuffer",
    "AlertManager",
    "RealtimeAnalyzer",
    "IoTGateway",
]

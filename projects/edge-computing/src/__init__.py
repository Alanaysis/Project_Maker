"""Edge Computing Framework - 边缘计算框架

实现边缘节点管理、任务分发、结果收集和负载均衡。
"""

from .edge_node import EdgeNode, NodeType, NodeStatus
from .task import Task, TaskStatus, TaskPriority
from .scheduler import Scheduler, RoundRobinScheduler, LeastLoadScheduler
from .edge_cluster import EdgeCluster
from .coordinator import Coordinator

__version__ = "0.1.0"
__all__ = [
    "EdgeNode",
    "NodeType",
    "NodeStatus",
    "Task",
    "TaskStatus",
    "TaskPriority",
    "Scheduler",
    "RoundRobinScheduler",
    "LeastLoadScheduler",
    "EdgeCluster",
    "Coordinator",
]

"""边缘节点模块 - 定义和管理边缘计算节点"""

import uuid
import time
import asyncio
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from collections import deque


class NodeType(Enum):
    """节点类型"""
    EDGE = "edge"          # 边缘节点
    FOG = "fog"            # 雾节点
    CLOUD = "cloud"        # 云节点


class NodeStatus(Enum):
    """节点状态"""
    IDLE = "idle"          # 空闲
    BUSY = "busy"          # 忙碌
    OFFLINE = "offline"    # 离线
    MAINTENANCE = "maintenance"  # 维护中


@dataclass
class NodeMetrics:
    """节点性能指标"""
    cpu_usage: float = 0.0        # CPU 使用率 (0-100)
    memory_usage: float = 0.0     # 内存使用率 (0-100)
    network_latency: float = 0.0  # 网络延迟 (ms)
    tasks_completed: int = 0      # 已完成任务数
    tasks_failed: int = 0         # 失败任务数
    total_processing_time: float = 0.0  # 总处理时间


class EdgeNode:
    """边缘节点

    表示边缘计算网络中的一个计算节点，具有以下能力：
    - 任务处理
    - 资源监控
    - 状态管理
    """

    def __init__(
        self,
        node_id: Optional[str] = None,
        name: str = "",
        node_type: NodeType = NodeType.EDGE,
        capacity: int = 10,
        location: Optional[Dict[str, float]] = None,
    ):
        self.node_id = node_id or str(uuid.uuid4())
        self.name = name or f"node-{self.node_id[:8]}"
        self.node_type = node_type
        self.capacity = capacity  # 最大并发任务数
        self.location = location or {"lat": 0.0, "lon": 0.0}

        self.status = NodeStatus.IDLE
        self.metrics = NodeMetrics()
        self._task_queue: deque = deque()
        self._active_tasks: Dict[str, Any] = {}
        self._created_at = time.time()
        self._last_heartbeat = time.time()

    @property
    def current_load(self) -> int:
        """当前负载（活跃任务数）"""
        return len(self._active_tasks)

    @property
    def load_factor(self) -> float:
        """负载因子 (0.0 - 1.0)"""
        if self.capacity == 0:
            return 1.0
        return self.current_load / self.capacity

    @property
    def is_available(self) -> bool:
        """是否可用"""
        return (
            self.status in (NodeStatus.IDLE, NodeStatus.BUSY)
            and self.current_load < self.capacity
        )

    @property
    def uptime(self) -> float:
        """运行时间（秒）"""
        return time.time() - self._created_at

    def heartbeat(self) -> None:
        """更新心跳"""
        self._last_heartbeat = time.time()

    def is_alive(self, timeout: float = 30.0) -> bool:
        """检查节点是否存活"""
        return (time.time() - self._last_heartbeat) < timeout

    def submit_task(self, task: Any) -> bool:
        """提交任务到节点

        Args:
            task: 要提交的任务

        Returns:
            bool: 是否成功提交
        """
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

    def complete_task(self, task_id: str, result: Any = None) -> Optional[Any]:
        """完成任务

        Args:
            task_id: 任务 ID
            result: 任务结果

        Returns:
            任务结果或 None
        """
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

    def fail_task(self, task_id: str, error: str = "") -> bool:
        """标记任务失败

        Args:
            task_id: 任务 ID
            error: 错误信息

        Returns:
            bool: 是否成功标记
        """
        if task_id not in self._active_tasks:
            return False

        task_info = self._active_tasks.pop(task_id)
        task = task_info["task"]
        task.fail(error)

        self.metrics.tasks_failed += 1
        self._update_status()

        return True

    def _update_status(self) -> None:
        """更新节点状态"""
        if self.current_load == 0:
            self.status = NodeStatus.IDLE
        elif self.current_load < self.capacity:
            self.status = NodeStatus.BUSY
        else:
            self.status = NodeStatus.BUSY

    def update_metrics(self, **kwargs) -> None:
        """更新性能指标"""
        for key, value in kwargs.items():
            if hasattr(self.metrics, key):
                setattr(self.metrics, key, value)

    def get_stats(self) -> Dict[str, Any]:
        """获取节点统计信息"""
        avg_time = 0.0
        if self.metrics.tasks_completed > 0:
            avg_time = self.metrics.total_processing_time / self.metrics.tasks_completed

        return {
            "node_id": self.node_id,
            "name": self.name,
            "type": self.node_type.value,
            "status": self.status.value,
            "capacity": self.capacity,
            "current_load": self.current_load,
            "load_factor": self.load_factor,
            "tasks_completed": self.metrics.tasks_completed,
            "tasks_failed": self.metrics.tasks_failed,
            "avg_processing_time": avg_time,
            "queue_size": len(self._task_queue),
            "uptime": self.uptime,
        }

    def __repr__(self) -> str:
        return (
            f"EdgeNode(id={self.node_id[:8]}, name={self.name}, "
            f"type={self.node_type.value}, status={self.status.value}, "
            f"load={self.current_load}/{self.capacity})"
        )

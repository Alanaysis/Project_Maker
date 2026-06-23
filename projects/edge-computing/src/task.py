"""任务模块 - 定义边缘计算任务"""

import uuid
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Callable


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"          # 等待中
    QUEUED = "queued"            # 已排队
    PROCESSING = "processing"    # 处理中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 失败
    CANCELLED = "cancelled"      # 已取消


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class TaskResult:
    """任务结果"""
    task_id: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    processing_time: float = 0.0
    node_id: Optional[str] = None


class Task:
    """边缘计算任务

    表示一个需要在边缘节点上执行的计算任务。
    """

    def __init__(
        self,
        task_id: Optional[str] = None,
        name: str = "",
        payload: Any = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: float = 30.0,
        callback: Optional[Callable] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.task_id = task_id or str(uuid.uuid4())
        self.name = name or f"task-{self.task_id[:8]}"
        self.payload = payload
        self.priority = priority
        self.timeout = timeout
        self.callback = callback
        self.metadata = metadata or {}

        self.status = TaskStatus.PENDING
        self.result: Optional[TaskResult] = None
        self.assigned_node: Optional[str] = None

        self._created_at = time.time()
        self._started_at: Optional[float] = None
        self._completed_at: Optional[float] = None
        self._error: Optional[str] = None

    @property
    def wait_time(self) -> float:
        """等待时间（秒）"""
        if self._started_at:
            return self._started_at - self._created_at
        return time.time() - self._created_at

    @property
    def processing_time(self) -> float:
        """处理时间（秒）"""
        if self._started_at is None:
            return 0.0
        end_time = self._completed_at or time.time()
        return end_time - self._started_at

    @property
    def total_time(self) -> float:
        """总时间（秒）"""
        end_time = self._completed_at or time.time()
        return end_time - self._created_at

    @property
    def is_finished(self) -> bool:
        """是否已结束"""
        return self.status in (
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        )

    def start_processing(self, node_id: str) -> None:
        """开始处理"""
        self.status = TaskStatus.PROCESSING
        self.assigned_node = node_id
        self._started_at = time.time()

    def complete(self, data: Any = None) -> None:
        """完成任务"""
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

    def fail(self, error: str = "") -> None:
        """标记失败"""
        self._completed_at = time.time()
        self.status = TaskStatus.FAILED
        self._error = error
        self.result = TaskResult(
            task_id=self.task_id,
            success=False,
            error=error,
            processing_time=self.processing_time,
            node_id=self.assigned_node,
        )
        if self.callback:
            self.callback(self.result)

    def cancel(self) -> bool:
        """取消任务"""
        if self.is_finished:
            return False
        self.status = TaskStatus.CANCELLED
        self._completed_at = time.time()
        return True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "status": self.status.value,
            "priority": self.priority.value,
            "assigned_node": self.assigned_node,
            "wait_time": self.wait_time,
            "processing_time": self.processing_time,
            "total_time": self.total_time,
            "metadata": self.metadata,
        }

    def __repr__(self) -> str:
        return (
            f"Task(id={self.task_id[:8]}, name={self.name}, "
            f"status={self.status.value}, priority={self.priority.name})"
        )

    def __lt__(self, other: "Task") -> bool:
        """用于优先级排序"""
        return self.priority.value > other.priority.value

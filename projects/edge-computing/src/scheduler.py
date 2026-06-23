"""调度器模块 - 任务调度和负载均衡"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import random
import heapq

try:
    from .edge_node import EdgeNode, NodeStatus
    from .task import Task, TaskPriority
except ImportError:
    from edge_node import EdgeNode, NodeStatus
    from task import Task, TaskPriority


class Scheduler(ABC):
    """调度器基类

    定义任务调度的接口，支持多种调度策略。
    """

    @abstractmethod
    def select_node(self, task: Task, nodes: List[EdgeNode]) -> Optional[EdgeNode]:
        """选择节点执行任务

        Args:
            task: 要调度的任务
            nodes: 可用节点列表

        Returns:
            选中的节点或 None
        """
        pass

    def schedule(self, task: Task, nodes: List[EdgeNode]) -> bool:
        """调度任务到节点

        Args:
            task: 要调度的任务
            nodes: 可用节点列表

        Returns:
            bool: 是否成功调度
        """
        available_nodes = [
            n for n in nodes
            if n.is_available and n.status != NodeStatus.OFFLINE
        ]

        if not available_nodes:
            return False

        node = self.select_node(task, available_nodes)
        if node is None:
            return False

        return node.submit_task(task)

    def schedule_batch(
        self, tasks: List[Task], nodes: List[EdgeNode]
    ) -> Dict[str, bool]:
        """批量调度任务

        Args:
            tasks: 任务列表
            nodes: 可用节点列表

        Returns:
            Dict[task_id, success]
        """
        results = {}
        # 按优先级排序
        sorted_tasks = sorted(tasks, key=lambda t: t.priority.value, reverse=True)

        for task in sorted_tasks:
            results[task.task_id] = self.schedule(task, nodes)

        return results


class RoundRobinScheduler(Scheduler):
    """轮询调度器

    按顺序将任务分配给各个节点，实现简单的负载均衡。
    """

    def __init__(self):
        self._index = 0

    def select_node(self, task: Task, nodes: List[EdgeNode]) -> Optional[EdgeNode]:
        if not nodes:
            return None

        # 轮询选择
        for _ in range(len(nodes)):
            node = nodes[self._index % len(nodes)]
            self._index += 1
            if node.is_available:
                return node

        return None


class LeastLoadScheduler(Scheduler):
    """最小负载调度器

    选择当前负载最低的节点，实现动态负载均衡。
    """

    def select_node(self, task: Task, nodes: List[EdgeNode]) -> Optional[EdgeNode]:
        if not nodes:
            return None

        # 按负载因子排序，选择负载最低的节点
        available = [n for n in nodes if n.is_available]
        if not available:
            return None

        return min(available, key=lambda n: n.load_factor)


class WeightedScheduler(Scheduler):
    """加权调度器

    根据节点容量和当前负载进行加权选择。
    容量越高、负载越低的节点被选中的概率越大。
    """

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
            weights.append(max(weight, 0.1))  # 最小权重 0.1

        # 加权随机选择
        total = sum(weights)
        r = random.uniform(0, total)
        cumulative = 0.0

        for node, weight in zip(available, weights):
            cumulative += weight
            if r <= cumulative:
                return node

        return available[-1]


class PriorityScheduler(Scheduler):
    """优先级调度器

    高优先级任务优先分配到性能更好的节点。
    """

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


class LocationAwareScheduler(Scheduler):
    """位置感知调度器

    根据任务来源位置选择最近的边缘节点，减少网络延迟。
    """

    def __init__(self, task_location: Optional[Dict[str, float]] = None):
        self.task_location = task_location or {"lat": 0.0, "lon": 0.0}

    def _calculate_distance(
        self, loc1: Dict[str, float], loc2: Dict[str, float]
    ) -> float:
        """计算两点间的距离（简化版）"""
        lat_diff = loc1.get("lat", 0) - loc2.get("lat", 0)
        lon_diff = loc1.get("lon", 0) - loc2.get("lon", 0)
        return (lat_diff ** 2 + lon_diff ** 2) ** 0.5

    def select_node(self, task: Task, nodes: List[EdgeNode]) -> Optional[EdgeNode]:
        if not nodes:
            return None

        available = [n for n in nodes if n.is_available]
        if not available:
            return None

        # 选择距离最近的节点
        return min(
            available,
            key=lambda n: self._calculate_distance(
                self.task_location, n.location
            ),
        )

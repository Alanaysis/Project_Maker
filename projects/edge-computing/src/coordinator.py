"""协调器模块 - 边缘计算核心协调组件"""

import time
import asyncio
from typing import Dict, List, Optional, Any, Callable
from concurrent.futures import ThreadPoolExecutor, Future
from collections import defaultdict

try:
    from .edge_node import EdgeNode, NodeType, NodeStatus
    from .task import Task, TaskStatus, TaskPriority, TaskResult
    from .edge_cluster import EdgeCluster
    from .scheduler import Scheduler, RoundRobinScheduler, LeastLoadScheduler
except ImportError:
    from edge_node import EdgeNode, NodeType, NodeStatus
    from task import Task, TaskStatus, TaskPriority, TaskResult
    from edge_cluster import EdgeCluster
    from scheduler import Scheduler, RoundRobinScheduler, LeastLoadScheduler


class Coordinator:
    """边缘计算协调器

    作为边缘计算系统的核心组件，负责：
    - 管理多个边缘集群
    - 协调任务分发
    - 收集和聚合结果
    - 监控系统状态
    """

    def __init__(
        self,
        coordinator_id: str = "coordinator-1",
        max_workers: int = 4,
        scheduler: Optional[Scheduler] = None,
    ):
        self.coordinator_id = coordinator_id
        self.max_workers = max_workers
        self.scheduler = scheduler or LeastLoadScheduler()

        self._clusters: Dict[str, EdgeCluster] = {}
        self._pending_tasks: List[Task] = []
        self._completed_tasks: Dict[str, TaskResult] = {}
        self._task_callbacks: Dict[str, Callable] = {}
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._running = False
        self._stats = defaultdict(int)

    @property
    def total_nodes(self) -> int:
        """总节点数"""
        return sum(c.node_count for c in self._clusters.values())

    @property
    def total_capacity(self) -> int:
        """总容量"""
        return sum(c.total_capacity for c in self._clusters.values())

    @property
    def current_load(self) -> int:
        """当前总负载"""
        return sum(c.current_load for c in self._clusters.values())

    def add_cluster(self, cluster: EdgeCluster) -> bool:
        """添加集群

        Args:
            cluster: 边缘集群

        Returns:
            bool: 是否成功添加
        """
        if cluster.cluster_id in self._clusters:
            return False

        self._clusters[cluster.cluster_id] = cluster
        return True

    def remove_cluster(self, cluster_id: str) -> bool:
        """移除集群

        Args:
            cluster_id: 集群 ID

        Returns:
            bool: 是否成功移除
        """
        if cluster_id not in self._clusters:
            return False

        cluster = self._clusters[cluster_id]
        if cluster.current_load > 0:
            return False

        del self._clusters[cluster_id]
        return True

    def get_cluster(self, cluster_id: str) -> Optional[EdgeCluster]:
        """获取集群"""
        return self._clusters.get(cluster_id)

    def register_task_callback(self, task_id: str, callback: Callable) -> None:
        """注册任务完成回调"""
        self._task_callbacks[task_id] = callback

    def submit_task(
        self,
        task: Task,
        cluster_id: Optional[str] = None,
        callback: Optional[Callable] = None,
    ) -> bool:
        """提交任务

        Args:
            task: 要提交的任务
            cluster_id: 指定集群 ID（可选）
            callback: 完成回调（可选）

        Returns:
            bool: 是否成功提交
        """
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

    def submit_tasks(
        self,
        tasks: List[Task],
        callback: Optional[Callable] = None,
    ) -> Dict[str, bool]:
        """批量提交任务

        Args:
            tasks: 任务列表
            callback: 完成回调（可选）

        Returns:
            Dict[task_id, success]
        """
        results = {}

        # 按优先级排序
        sorted_tasks = sorted(tasks, key=lambda t: t.priority.value, reverse=True)

        for task in sorted_tasks:
            results[task.task_id] = self.submit_task(task, callback=callback)

        return results

    def complete_task(
        self,
        task_id: str,
        node_id: str,
        cluster_id: str,
        result: Any = None,
    ) -> bool:
        """完成任务

        Args:
            task_id: 任务 ID
            node_id: 节点 ID
            cluster_id: 集群 ID
            result: 任务结果

        Returns:
            bool: 是否成功完成
        """
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

    def _process_pending_tasks(self) -> None:
        """处理待处理任务队列"""
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

    def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """获取任务结果"""
        return self._completed_tasks.get(task_id)

    def get_all_results(self) -> Dict[str, TaskResult]:
        """获取所有任务结果"""
        return self._completed_tasks.copy()

    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        clusters_stats = {}
        for cluster_id, cluster in self._clusters.items():
            clusters_stats[cluster_id] = cluster.get_cluster_stats()

        return {
            "coordinator_id": self.coordinator_id,
            "total_clusters": len(self._clusters),
            "total_nodes": self.total_nodes,
            "total_capacity": self.total_capacity,
            "current_load": self.current_load,
            "load_factor": self.current_load / max(self.total_capacity, 1),
            "pending_tasks": len(self._pending_tasks),
            "completed_tasks": len(self._completed_tasks),
            "stats": dict(self._stats),
            "clusters": clusters_stats,
        }

    def health_check(self) -> Dict[str, Any]:
        """系统健康检查"""
        cluster_health = {}
        all_healthy = True

        for cluster_id, cluster in self._clusters.items():
            health = cluster.health_check()
            cluster_health[cluster_id] = health
            if not health["healthy"]:
                all_healthy = False

        return {
            "coordinator_id": self.coordinator_id,
            "healthy": all_healthy,
            "clusters": cluster_health,
            "pending_tasks": len(self._pending_tasks),
        }

    def shutdown(self) -> None:
        """关闭协调器"""
        self._running = False
        self._executor.shutdown(wait=False)

    def __repr__(self) -> str:
        return (
            f"Coordinator(id={self.coordinator_id}, clusters={len(self._clusters)}, "
            f"nodes={self.total_nodes}, load={self.current_load}/{self.total_capacity})"
        )

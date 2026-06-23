"""边缘集群模块 - 管理边缘节点集群"""

import time
from typing import Dict, List, Optional, Any
from collections import defaultdict

try:
    from .edge_node import EdgeNode, NodeType, NodeStatus
    from .task import Task, TaskStatus
    from .scheduler import Scheduler, RoundRobinScheduler
except ImportError:
    from edge_node import EdgeNode, NodeType, NodeStatus
    from task import Task, TaskStatus
    from scheduler import Scheduler, RoundRobinScheduler


class EdgeCluster:
    """边缘集群

    管理一组边缘节点，提供统一的任务分发和结果收集接口。
    """

    def __init__(
        self,
        cluster_id: str = "default",
        scheduler: Optional[Scheduler] = None,
    ):
        self.cluster_id = cluster_id
        self.scheduler = scheduler or RoundRobinScheduler()
        self._nodes: Dict[str, EdgeNode] = {}
        self._task_history: List[Dict[str, Any]] = []
        self._created_at = time.time()

    @property
    def node_count(self) -> int:
        """节点数量"""
        return len(self._nodes)

    @property
    def active_nodes(self) -> List[EdgeNode]:
        """活跃节点列表"""
        return [
            n for n in self._nodes.values()
            if n.status != NodeStatus.OFFLINE
        ]

    @property
    def total_capacity(self) -> int:
        """总容量"""
        return sum(n.capacity for n in self._nodes.values())

    @property
    def current_load(self) -> int:
        """当前总负载"""
        return sum(n.current_load for n in self._nodes.values())

    def add_node(self, node: EdgeNode) -> bool:
        """添加节点到集群

        Args:
            node: 边缘节点

        Returns:
            bool: 是否成功添加
        """
        if node.node_id in self._nodes:
            return False

        self._nodes[node.node_id] = node
        return True

    def remove_node(self, node_id: str) -> bool:
        """从集群移除节点

        Args:
            node_id: 节点 ID

        Returns:
            bool: 是否成功移除
        """
        if node_id not in self._nodes:
            return False

        node = self._nodes[node_id]
        if node.current_load > 0:
            # 节点有活跃任务，标记为离线
            node.status = NodeStatus.OFFLINE
            return False

        del self._nodes[node_id]
        return True

    def get_node(self, node_id: str) -> Optional[EdgeNode]:
        """获取节点"""
        return self._nodes.get(node_id)

    def submit_task(self, task: Task) -> bool:
        """提交任务到集群

        Args:
            task: 要提交的任务

        Returns:
            bool: 是否成功提交
        """
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

    def submit_tasks(self, tasks: List[Task]) -> Dict[str, bool]:
        """批量提交任务

        Args:
            tasks: 任务列表

        Returns:
            Dict[task_id, success]
        """
        nodes = self.active_nodes
        if not nodes:
            return {t.task_id: False for t in tasks}

        results = self.scheduler.schedule_batch(tasks, nodes)

        for task in tasks:
            self._task_history.append({
                "task_id": task.task_id,
                "action": "submit",
                "success": results.get(task.task_id, False),
                "timestamp": time.time(),
            })

        return results

    def complete_task(self, task_id: str, node_id: str, result: Any = None) -> bool:
        """完成任务

        Args:
            task_id: 任务 ID
            node_id: 节点 ID
            result: 任务结果

        Returns:
            bool: 是否成功完成
        """
        node = self.get_node(node_id)
        if node is None:
            return False

        success = node.complete_task(task_id, result) is not None

        self._task_history.append({
            "task_id": task_id,
            "action": "complete",
            "node_id": node_id,
            "success": success,
            "timestamp": time.time(),
        })

        return success

    def get_cluster_stats(self) -> Dict[str, Any]:
        """获取集群统计信息"""
        nodes_stats = []
        status_counts = defaultdict(int)

        for node in self._nodes.values():
            nodes_stats.append(node.get_stats())
            status_counts[node.status.value] += 1

        completed = sum(
            1 for h in self._task_history
            if h.get("action") == "complete" and h.get("success")
        )
        failed = sum(
            1 for h in self._task_history
            if h.get("action") == "complete" and not h.get("success")
        )

        return {
            "cluster_id": self.cluster_id,
            "node_count": self.node_count,
            "total_capacity": self.total_capacity,
            "current_load": self.current_load,
            "load_factor": self.current_load / max(self.total_capacity, 1),
            "node_status_counts": dict(status_counts),
            "tasks_completed": completed,
            "tasks_failed": failed,
            "nodes": nodes_stats,
        }

    def get_node_stats(self) -> List[Dict[str, Any]]:
        """获取所有节点统计信息"""
        return [node.get_stats() for node in self._nodes.values()]

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
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

    def __repr__(self) -> str:
        return (
            f"EdgeCluster(id={self.cluster_id}, nodes={self.node_count}, "
            f"load={self.current_load}/{self.total_capacity})"
        )

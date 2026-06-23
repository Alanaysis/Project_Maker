"""边缘集群测试"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from edge_node import EdgeNode, NodeType, NodeStatus
from task import Task, TaskPriority
from edge_cluster import EdgeCluster
from scheduler import RoundRobinScheduler, LeastLoadScheduler


class TestEdgeCluster:
    """边缘集群测试类"""

    def test_cluster_creation(self):
        """测试集群创建"""
        cluster = EdgeCluster(cluster_id="test-cluster")

        assert cluster.cluster_id == "test-cluster"
        assert cluster.node_count == 0
        assert cluster.total_capacity == 0
        assert cluster.current_load == 0

    def test_add_node(self):
        """测试添加节点"""
        cluster = EdgeCluster()
        node = EdgeNode(name="node-1", capacity=5)

        result = cluster.add_node(node)

        assert result is True
        assert cluster.node_count == 1
        assert cluster.total_capacity == 5

    def test_add_duplicate_node(self):
        """测试添加重复节点"""
        cluster = EdgeCluster()
        node = EdgeNode(node_id="same-id", name="node-1")

        cluster.add_node(node)
        result = cluster.add_node(node)

        assert result is False
        assert cluster.node_count == 1

    def test_remove_node(self):
        """测试移除节点"""
        cluster = EdgeCluster()
        node = EdgeNode(name="node-1", capacity=5)

        cluster.add_node(node)
        result = cluster.remove_node(node.node_id)

        assert result is True
        assert cluster.node_count == 0

    def test_remove_node_with_active_tasks(self):
        """测试移除有活跃任务的节点"""
        cluster = EdgeCluster()
        node = EdgeNode(name="node-1", capacity=5)

        cluster.add_node(node)

        task = Task(name="task-1")
        node.submit_task(task)

        result = cluster.remove_node(node.node_id)

        assert result is False
        assert cluster.node_count == 1

    def test_submit_task(self):
        """测试提交任务"""
        cluster = EdgeCluster(scheduler=RoundRobinScheduler())
        node = EdgeNode(name="node-1", capacity=5)

        cluster.add_node(node)

        task = Task(name="task-1")
        result = cluster.submit_task(task)

        assert result is True
        assert node.current_load == 1

    def test_submit_task_no_nodes(self):
        """测试没有节点时提交任务"""
        cluster = EdgeCluster()

        task = Task(name="task-1")
        result = cluster.submit_task(task)

        assert result is False

    def test_submit_tasks_batch(self):
        """测试批量提交任务"""
        cluster = EdgeCluster(scheduler=RoundRobinScheduler())

        nodes = [
            EdgeNode(name="node-1", capacity=5),
            EdgeNode(name="node-2", capacity=5),
        ]

        for node in nodes:
            cluster.add_node(node)

        tasks = [Task(name=f"task-{i}") for i in range(6)]

        results = cluster.submit_tasks(tasks)

        assert all(results.values())
        assert cluster.current_load == 6

    def test_complete_task(self):
        """测试完成任务"""
        cluster = EdgeCluster()
        node = EdgeNode(name="node-1", capacity=5)

        cluster.add_node(node)

        task = Task(name="task-1")
        cluster.submit_task(task)

        result = cluster.complete_task(task.task_id, node.node_id, {"output": "done"})

        assert result is True
        assert node.current_load == 0
        assert node.metrics.tasks_completed == 1

    def test_complete_task_wrong_node(self):
        """测试在错误节点完成任务"""
        cluster = EdgeCluster()
        node = EdgeNode(name="node-1", capacity=5)

        cluster.add_node(node)

        task = Task(name="task-1")
        cluster.submit_task(task)

        result = cluster.complete_task(task.task_id, "wrong-node-id")

        assert result is False

    def test_cluster_stats(self):
        """测试集群统计"""
        cluster = EdgeCluster(cluster_id="stats-cluster")

        node1 = EdgeNode(name="node-1", capacity=5)
        node2 = EdgeNode(name="node-2", capacity=10)

        cluster.add_node(node1)
        cluster.add_node(node2)

        stats = cluster.get_cluster_stats()

        assert stats["cluster_id"] == "stats-cluster"
        assert stats["node_count"] == 2
        assert stats["total_capacity"] == 15
        assert stats["current_load"] == 0

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

    def test_health_check_with_offline_node(self):
        """测试有离线节点的健康检查"""
        cluster = EdgeCluster()

        node = EdgeNode(name="node-1", capacity=5)
        node.status = NodeStatus.OFFLINE
        cluster.add_node(node)

        health = cluster.health_check()

        assert health["healthy"] is False
        assert health["unhealthy_nodes"] == 1

    def test_active_nodes(self):
        """测试活跃节点"""
        cluster = EdgeCluster()

        node1 = EdgeNode(name="online", capacity=5)
        node2 = EdgeNode(name="offline", capacity=5)
        node2.status = NodeStatus.OFFLINE

        cluster.add_node(node1)
        cluster.add_node(node2)

        active = cluster.active_nodes

        assert len(active) == 1
        assert active[0].name == "online"

    def test_cluster_repr(self):
        """测试集群字符串表示"""
        cluster = EdgeCluster(cluster_id="repr-cluster")

        node = EdgeNode(name="node-1", capacity=5)
        cluster.add_node(node)

        repr_str = repr(cluster)

        assert "repr-cluster" in repr_str
        assert "1" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

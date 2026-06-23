"""协调器测试"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from edge_node import EdgeNode
from task import Task, TaskPriority
from edge_cluster import EdgeCluster
from coordinator import Coordinator
from scheduler import LeastLoadScheduler


class TestCoordinator:
    """协调器测试类"""

    def test_coordinator_creation(self):
        """测试协调器创建"""
        coordinator = Coordinator(coordinator_id="test-coord")

        assert coordinator.coordinator_id == "test-coord"
        assert len(coordinator._clusters) == 0
        assert coordinator.total_nodes == 0
        assert coordinator.total_capacity == 0

    def test_add_cluster(self):
        """测试添加集群"""
        coordinator = Coordinator()
        cluster = EdgeCluster(cluster_id="cluster-1")

        result = coordinator.add_cluster(cluster)

        assert result is True
        assert len(coordinator._clusters) == 1

    def test_add_duplicate_cluster(self):
        """测试添加重复集群"""
        coordinator = Coordinator()
        cluster = EdgeCluster(cluster_id="cluster-1")

        coordinator.add_cluster(cluster)
        result = coordinator.add_cluster(cluster)

        assert result is False

    def test_remove_cluster(self):
        """测试移除集群"""
        coordinator = Coordinator()
        cluster = EdgeCluster(cluster_id="cluster-1")

        coordinator.add_cluster(cluster)
        result = coordinator.remove_cluster("cluster-1")

        assert result is True
        assert len(coordinator._clusters) == 0

    def test_remove_cluster_with_load(self):
        """测试移除有负载的集群"""
        coordinator = Coordinator()
        cluster = EdgeCluster(cluster_id="cluster-1")
        node = EdgeNode(name="node-1", capacity=5)
        cluster.add_node(node)

        coordinator.add_cluster(cluster)

        task = Task(name="task-1")
        cluster.submit_task(task)

        result = coordinator.remove_cluster("cluster-1")

        assert result is False

    def test_submit_task_to_specific_cluster(self):
        """测试提交任务到指定集群"""
        coordinator = Coordinator()
        cluster = EdgeCluster(cluster_id="target-cluster")
        node = EdgeNode(name="node-1", capacity=5)
        cluster.add_node(node)

        coordinator.add_cluster(cluster)

        task = Task(name="task-1")
        result = coordinator.submit_task(task, cluster_id="target-cluster")

        assert result is True
        assert node.current_load == 1

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

    def test_submit_task_no_cluster(self):
        """测试没有集群时提交任务"""
        coordinator = Coordinator()

        task = Task(name="task-1")
        result = coordinator.submit_task(task)

        assert result is False
        assert len(coordinator._pending_tasks) == 1

    def test_submit_tasks_batch(self):
        """测试批量提交任务"""
        coordinator = Coordinator()

        cluster = EdgeCluster(cluster_id="cluster-1")
        node = EdgeNode(name="node-1", capacity=10)
        cluster.add_node(node)

        coordinator.add_cluster(cluster)

        tasks = [Task(name=f"task-{i}") for i in range(5)]
        results = coordinator.submit_tasks(tasks)

        assert all(results.values())

    def test_complete_task(self):
        """测试完成任务"""
        coordinator = Coordinator()

        cluster = EdgeCluster(cluster_id="cluster-1")
        node = EdgeNode(name="node-1", capacity=5)
        cluster.add_node(node)

        coordinator.add_cluster(cluster)

        task = Task(name="task-1")
        coordinator.submit_task(task, cluster_id="cluster-1")

        result = coordinator.complete_task(
            task.task_id, node.node_id, "cluster-1", {"output": "done"}
        )

        assert result is True
        assert node.current_load == 0

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

    def test_get_task_result(self):
        """测试获取任务结果"""
        coordinator = Coordinator()

        cluster = EdgeCluster(cluster_id="cluster-1")
        node = EdgeNode(name="node-1", capacity=5)
        cluster.add_node(node)

        coordinator.add_cluster(cluster)

        task = Task(name="task-1")
        coordinator.submit_task(task, cluster_id="cluster-1")

        coordinator.complete_task(
            task.task_id, node.node_id, "cluster-1", {"output": "result"}
        )

        result = coordinator.get_task_result(task.task_id)

        assert result is not None
        assert result.success is True
        assert result.data == {"output": "result"}

    def test_system_stats(self):
        """测试系统统计"""
        coordinator = Coordinator(coordinator_id="stats-coord")

        cluster = EdgeCluster(cluster_id="cluster-1")
        node = EdgeNode(name="node-1", capacity=10)
        cluster.add_node(node)

        coordinator.add_cluster(cluster)

        stats = coordinator.get_system_stats()

        assert stats["coordinator_id"] == "stats-coord"
        assert stats["total_clusters"] == 1
        assert stats["total_nodes"] == 1
        assert stats["total_capacity"] == 10

    def test_health_check(self):
        """测试健康检查"""
        coordinator = Coordinator()

        cluster = EdgeCluster(cluster_id="cluster-1")
        node = EdgeNode(name="node-1", capacity=5)
        cluster.add_node(node)

        coordinator.add_cluster(cluster)

        health = coordinator.health_check()

        assert health["healthy"] is True
        assert "cluster-1" in health["clusters"]

    def test_coordinator_repr(self):
        """测试协调器字符串表示"""
        coordinator = Coordinator(coordinator_id="repr-coord")

        repr_str = repr(coordinator)

        assert "repr-coord" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""边缘节点测试"""

import pytest
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from edge_node import EdgeNode, NodeType, NodeStatus
from task import Task, TaskPriority, TaskStatus


class TestEdgeNode:
    """边缘节点测试类"""

    def test_node_creation(self):
        """测试节点创建"""
        node = EdgeNode(name="test-node", node_type=NodeType.EDGE, capacity=5)

        assert node.name == "test-node"
        assert node.node_type == NodeType.EDGE
        assert node.capacity == 5
        assert node.status == NodeStatus.IDLE
        assert node.current_load == 0
        assert node.load_factor == 0.0
        assert node.is_available is True

    def test_node_with_custom_id(self):
        """测试自定义 ID 的节点"""
        node = EdgeNode(node_id="custom-id-123", name="custom-node")

        assert node.node_id == "custom-id-123"
        assert node.name == "custom-node"

    def test_node_types(self):
        """测试不同节点类型"""
        edge = EdgeNode(node_type=NodeType.EDGE)
        fog = EdgeNode(node_type=NodeType.FOG)
        cloud = EdgeNode(node_type=NodeType.CLOUD)

        assert edge.node_type == NodeType.EDGE
        assert fog.node_type == NodeType.FOG
        assert cloud.node_type == NodeType.CLOUD

    def test_submit_task(self):
        """测试提交任务"""
        node = EdgeNode(capacity=2)
        task = Task(name="test-task")

        result = node.submit_task(task)

        assert result is True
        assert node.current_load == 1
        assert task.status == TaskStatus.PROCESSING
        assert task.assigned_node == node.node_id

    def test_submit_task_when_full(self):
        """测试节点满时提交任务"""
        node = EdgeNode(capacity=1)
        task1 = Task(name="task-1")
        task2 = Task(name="task-2")

        node.submit_task(task1)
        result = node.submit_task(task2)

        assert result is False
        assert node.current_load == 1

    def test_complete_task(self):
        """测试完成任务"""
        node = EdgeNode(capacity=5)
        task = Task(name="test-task")

        node.submit_task(task)
        result = node.complete_task(task.task_id, {"output": "success"})

        assert result is not None
        assert node.current_load == 0
        assert node.metrics.tasks_completed == 1
        assert task.status == TaskStatus.COMPLETED

    def test_fail_task(self):
        """测试任务失败"""
        node = EdgeNode(capacity=5)
        task = Task(name="test-task")

        node.submit_task(task)
        result = node.fail_task(task.task_id, "connection error")

        assert result is True
        assert node.current_load == 0
        assert node.metrics.tasks_failed == 1
        assert task.status == TaskStatus.FAILED

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

    def test_heartbeat(self):
        """测试心跳"""
        node = EdgeNode()

        assert node.is_alive() is True

        node._last_heartbeat = time.time() - 60
        assert node.is_alive(timeout=30) is False

    def test_node_stats(self):
        """测试节点统计"""
        node = EdgeNode(name="stats-node", capacity=10)

        task = Task(name="test-task")
        node.submit_task(task)
        node.complete_task(task.task_id, "result")

        stats = node.get_stats()

        assert stats["name"] == "stats-node"
        assert stats["capacity"] == 10
        assert stats["tasks_completed"] == 1
        assert stats["tasks_failed"] == 0

    def test_node_repr(self):
        """测试节点字符串表示"""
        node = EdgeNode(node_id="12345678-1234-1234-1234-123456789012", name="repr-node")

        repr_str = repr(node)
        assert "repr-node" in repr_str
        assert "12345678" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""调度器测试"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from edge_node import EdgeNode, NodeType
from task import Task, TaskPriority
from scheduler import (
    RoundRobinScheduler,
    LeastLoadScheduler,
    WeightedScheduler,
    PriorityScheduler,
    LocationAwareScheduler,
)


class TestRoundRobinScheduler:
    """轮询调度器测试"""

    def test_basic_scheduling(self):
        """测试基本调度"""
        scheduler = RoundRobinScheduler()
        nodes = [
            EdgeNode(name="node-1", capacity=2),
            EdgeNode(name="node-2", capacity=2),
            EdgeNode(name="node-3", capacity=2),
        ]

        task1 = Task(name="task-1")
        task2 = Task(name="task-2")
        task3 = Task(name="task-3")

        scheduler.schedule(task1, nodes)
        scheduler.schedule(task2, nodes)
        scheduler.schedule(task3, nodes)

        assert nodes[0].current_load == 1
        assert nodes[1].current_load == 1
        assert nodes[2].current_load == 1

    def test_schedule_batch(self):
        """测试批量调度"""
        scheduler = RoundRobinScheduler()
        nodes = [
            EdgeNode(name="node-1", capacity=5),
            EdgeNode(name="node-2", capacity=5),
        ]

        tasks = [Task(name=f"task-{i}") for i in range(6)]

        results = scheduler.schedule_batch(tasks, nodes)

        assert all(results.values())
        assert nodes[0].current_load == 3
        assert nodes[1].current_load == 3

    def test_no_available_nodes(self):
        """测试没有可用节点"""
        scheduler = RoundRobinScheduler()
        nodes = []

        task = Task(name="task-1")
        result = scheduler.schedule(task, nodes)

        assert result is False


class TestLeastLoadScheduler:
    """最小负载调度器测试"""

    def test_select_least_loaded(self):
        """测试选择负载最低的节点"""
        scheduler = LeastLoadScheduler()

        node1 = EdgeNode(name="node-1", capacity=5)
        node2 = EdgeNode(name="node-2", capacity=5)

        # 给 node1 添加一些负载
        for i in range(3):
            task = Task(name=f"task-{i}")
            node1.submit_task(task)

        nodes = [node1, node2]
        new_task = Task(name="new-task")

        scheduler.schedule(new_task, nodes)

        # 应该选择 node2（负载更低）
        assert node2.current_load == 1
        assert node1.current_load == 3

    def test_equal_load_distribution(self):
        """测试负载相等时的分配"""
        scheduler = LeastLoadScheduler()
        nodes = [
            EdgeNode(name="node-1", capacity=5),
            EdgeNode(name="node-2", capacity=5),
        ]

        task = Task(name="task-1")
        scheduler.schedule(task, nodes)

        # 负载相等时选择第一个
        assert nodes[0].current_load == 1 or nodes[1].current_load == 1


class TestWeightedScheduler:
    """加权调度器测试"""

    def test_capacity_based_scheduling(self):
        """测试基于容量的调度"""
        scheduler = WeightedScheduler()

        # 不同容量的节点
        nodes = [
            EdgeNode(name="small", capacity=2),
            EdgeNode(name="medium", capacity=5),
            EdgeNode(name="large", capacity=10),
        ]

        # 提交多个任务，大容量节点应该接收更多
        task_counts = {n.name: 0 for n in nodes}
        for i in range(30):
            task = Task(name=f"task-{i}")
            selected = scheduler.select_node(task, nodes)
            if selected:
                task_counts[selected.name] += 1

        # 大容量节点应该接收最多任务
        assert task_counts["large"] > task_counts["small"]


class TestPriorityScheduler:
    """优先级调度器测试"""

    def test_high_priority_to_best_node(self):
        """测试高优先级任务分配到最佳节点"""
        scheduler = PriorityScheduler()

        node1 = EdgeNode(name="node-1", capacity=5)
        node2 = EdgeNode(name="node-2", capacity=5)

        # 给 node1 添加一些负载
        for i in range(3):
            task = Task(name=f"task-{i}")
            node1.submit_task(task)

        nodes = [node1, node2]

        # 高优先级任务应该分配到负载最低的节点
        high_task = Task(name="high-task", priority=TaskPriority.HIGH)
        scheduler.schedule(high_task, nodes)

        assert node2.current_load == 1


class TestLocationAwareScheduler:
    """位置感知调度器测试"""

    def test_select_nearest_node(self):
        """测试选择最近的节点"""
        scheduler = LocationAwareScheduler(task_location={"lat": 40.0, "lon": -74.0})

        nodes = [
            EdgeNode(name="near", location={"lat": 40.1, "lon": -74.1}),
            EdgeNode(name="far", location={"lat": 35.0, "lon": -80.0}),
        ]

        task = Task(name="location-task")
        scheduler.schedule(task, nodes)

        # 应该选择最近的节点
        assert nodes[0].current_load == 1
        assert nodes[1].current_load == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

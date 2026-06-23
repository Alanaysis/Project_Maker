"""任务测试"""

import pytest
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from task import Task, TaskStatus, TaskPriority, TaskResult


class TestTask:
    """任务测试类"""

    def test_task_creation(self):
        """测试任务创建"""
        task = Task(name="test-task")

        assert task.name == "test-task"
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.NORMAL
        assert task.is_finished is False

    def test_task_with_custom_id(self):
        """测试自定义 ID 的任务"""
        task = Task(task_id="custom-task-123", name="custom-task")

        assert task.task_id == "custom-task-123"
        assert task.name == "custom-task"

    def test_task_priority(self):
        """测试任务优先级"""
        low = Task(priority=TaskPriority.LOW)
        normal = Task(priority=TaskPriority.NORMAL)
        high = Task(priority=TaskPriority.HIGH)
        critical = Task(priority=TaskPriority.CRITICAL)

        assert low.priority == TaskPriority.LOW
        assert normal.priority == TaskPriority.NORMAL
        assert high.priority == TaskPriority.HIGH
        assert critical.priority == TaskPriority.CRITICAL

    def test_task_priority_ordering(self):
        """测试任务优先级排序"""
        tasks = [
            Task(name="low", priority=TaskPriority.LOW),
            Task(name="high", priority=TaskPriority.HIGH),
            Task(name="normal", priority=TaskPriority.NORMAL),
            Task(name="critical", priority=TaskPriority.CRITICAL),
        ]

        sorted_tasks = sorted(tasks)

        assert sorted_tasks[0].name == "critical"
        assert sorted_tasks[1].name == "high"
        assert sorted_tasks[2].name == "normal"
        assert sorted_tasks[3].name == "low"

    def test_task_lifecycle(self):
        """测试任务生命周期"""
        task = Task(name="lifecycle-task")

        # 初始状态
        assert task.status == TaskStatus.PENDING
        assert task.assigned_node is None

        # 开始处理
        task.start_processing("node-1")
        assert task.status == TaskStatus.PROCESSING
        assert task.assigned_node == "node-1"

        # 完成
        task.complete({"result": "success"})
        assert task.status == TaskStatus.COMPLETED
        assert task.is_finished is True
        assert task.result is not None
        assert task.result.success is True

    def test_task_failure(self):
        """测试任务失败"""
        task = Task(name="fail-task")

        task.start_processing("node-1")
        task.fail("connection timeout")

        assert task.status == TaskStatus.FAILED
        assert task.is_finished is True
        assert task.result is not None
        assert task.result.success is False
        assert task.result.error == "connection timeout"

    def test_task_cancellation(self):
        """测试任务取消"""
        task = Task(name="cancel-task")

        result = task.cancel()
        assert result is True
        assert task.status == TaskStatus.CANCELLED
        assert task.is_finished is True

    def test_cannot_cancel_finished_task(self):
        """测试无法取消已完成的任务"""
        task = Task(name="finished-task")
        task.start_processing("node-1")
        task.complete()

        result = task.cancel()
        assert result is False

    def test_task_timing(self):
        """测试任务计时"""
        task = Task(name="timing-task")

        # 等待时间
        time.sleep(0.01)
        assert task.wait_time > 0

        # 处理时间
        task.start_processing("node-1")
        time.sleep(0.01)
        assert task.processing_time > 0

        # 完成后处理时间固定
        task.complete()
        processing_time = task.processing_time
        time.sleep(0.01)
        assert task.processing_time == processing_time

    def test_task_callback(self):
        """测试任务回调"""
        callback_results = []

        def callback(result):
            callback_results.append(result)

        task = Task(name="callback-task", callback=callback)
        task.start_processing("node-1")
        task.complete({"data": "test"})

        assert len(callback_results) == 1
        assert callback_results[0].success is True

    def test_task_to_dict(self):
        """测试任务转字典"""
        task = Task(name="dict-task", priority=TaskPriority.HIGH)

        task_dict = task.to_dict()

        assert task_dict["name"] == "dict-task"
        assert task_dict["priority"] == TaskPriority.HIGH.value
        assert task_dict["status"] == TaskStatus.PENDING.value

    def test_task_repr(self):
        """测试任务字符串表示"""
        task = Task(task_id="12345678-1234-1234-1234-123456789012", name="repr-task")

        repr_str = repr(task)
        assert "repr-task" in repr_str
        assert "12345678" in repr_str


class TestTaskResult:
    """任务结果测试类"""

    def test_result_creation(self):
        """测试结果创建"""
        result = TaskResult(
            task_id="task-1",
            success=True,
            data={"output": "test"},
            processing_time=1.5,
            node_id="node-1",
        )

        assert result.task_id == "task-1"
        assert result.success is True
        assert result.data == {"output": "test"}
        assert result.processing_time == 1.5
        assert result.node_id == "node-1"

    def test_failed_result(self):
        """测试失败结果"""
        result = TaskResult(
            task_id="task-2",
            success=False,
            error="timeout",
        )

        assert result.success is False
        assert result.error == "timeout"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

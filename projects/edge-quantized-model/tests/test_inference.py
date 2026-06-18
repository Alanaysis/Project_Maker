"""
推理模块测试

测试推理相关的功能
"""

import pytest
import numpy as np
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.inference.graph import ComputeGraph, GraphNode
from src.inference.memory import MemoryPool, TensorAllocator
from src.inference.executor import Executor


class TestComputeGraph:
    """计算图测试"""

    def test_add_node(self):
        """测试添加节点"""
        graph = ComputeGraph()

        node = GraphNode(
            name="conv1",
            op_type="Conv",
            inputs=["input"],
            outputs=["output"],
            params={"stride": 1, "padding": 1},
        )

        graph.add_node(node)

        assert "conv1" in graph.nodes
        assert graph.nodes["conv1"].op_type == "Conv"

    def test_topological_sort(self):
        """测试拓扑排序"""
        graph = ComputeGraph()

        # 创建简单的计算图
        # input -> conv1 -> relu1 -> output
        graph.add_node(GraphNode(
            name="conv1",
            op_type="Conv",
            inputs=["input"],
            outputs=["conv1_out"],
        ))
        graph.add_node(GraphNode(
            name="relu1",
            op_type="Relu",
            inputs=["conv1_out"],
            outputs=["output"],
        ))

        graph.set_input("input", (1, 3, 32, 32))
        graph.set_output("output")

        # 拓扑排序
        order = graph.topological_sort()

        # 验证顺序
        assert order.index("conv1") < order.index("relu1")

    def test_get_predecessors(self):
        """测试获取前驱节点"""
        graph = ComputeGraph()

        graph.add_node(GraphNode(
            name="conv1",
            op_type="Conv",
            inputs=["input"],
            outputs=["conv1_out"],
        ))
        graph.add_node(GraphNode(
            name="relu1",
            op_type="Relu",
            inputs=["conv1_out"],
            outputs=["output"],
        ))

        predecessors = graph.get_predecessors("relu1")
        assert "conv1" in predecessors

    def test_get_successors(self):
        """测试获取后继节点"""
        graph = ComputeGraph()

        graph.add_node(GraphNode(
            name="conv1",
            op_type="Conv",
            inputs=["input"],
            outputs=["conv1_out"],
        ))
        graph.add_node(GraphNode(
            name="relu1",
            op_type="Relu",
            inputs=["conv1_out"],
            outputs=["output"],
        ))

        successors = graph.get_successors("conv1")
        assert "relu1" in successors

    def test_validate(self):
        """测试图验证"""
        graph = ComputeGraph()

        graph.add_node(GraphNode(
            name="conv1",
            op_type="Conv",
            inputs=["input"],
            outputs=["output"],
        ))
        graph.set_input("input", (1, 3, 32, 32))
        graph.set_output("output")

        errors = graph.validate()
        assert len(errors) == 0


class TestMemoryPool:
    """内存池测试"""

    def test_allocate_and_free(self):
        """测试分配和释放"""
        pool = MemoryPool(1000)

        # 分配
        data = pool.allocate("test", 100)
        assert data.shape == (100,)

        # 释放
        pool.free("test")

    def test_allocate_multiple(self):
        """测试多次分配"""
        pool = MemoryPool(1000)

        data1 = pool.allocate("test1", 100)
        data2 = pool.allocate("test2", 200)

        assert data1.shape == (100,)
        assert data2.shape == (200,)

        pool.free("test1")
        pool.free("test2")

    def test_memory_exhaustion(self):
        """测试内存耗尽"""
        pool = MemoryPool(100)

        # 分配 100 元素
        pool.allocate("test1", 100)

        # 尝试再分配，应该失败
        with pytest.raises(MemoryError):
            pool.allocate("test2", 10)

        pool.free("test1")

    def test_memory_reuse(self):
        """测试内存复用"""
        pool = MemoryPool(1000)

        # 分配并释放
        pool.allocate("test1", 100)
        pool.free("test1")

        # 再次分配，应该复用
        pool.allocate("test2", 100)
        pool.free("test2")

    def test_get_usage(self):
        """测试获取使用情况"""
        pool = MemoryPool(1000)

        pool.allocate("test1", 100)
        usage = pool.get_usage()

        assert usage["total"] == 1000
        assert usage["allocated"] == 100
        assert usage["free"] == 900

        pool.free("test1")


class TestTensorAllocator:
    """张量分配器测试"""

    def test_allocate_tensor(self):
        """测试分配张量"""
        pool = MemoryPool(10000)
        allocator = TensorAllocator(pool)

        tensor = allocator.allocate_tensor("test", (3, 32, 32))

        assert tensor.shape == (3, 32, 32)
        assert tensor.dtype == np.float32

        allocator.release_tensor("test")

    def test_tensor_reference_counting(self):
        """测试张量引用计数"""
        pool = MemoryPool(10000)
        allocator = TensorAllocator(pool)

        # 分配
        allocator.allocate_tensor("test", (10, 10))

        # 增加引用
        allocator.allocate_tensor("test", (10, 10))

        # 释放一次
        allocator.release_tensor("test")

        # 张量仍然存在
        tensor = allocator.get_tensor("test")
        assert tensor is not None

        # 再次释放
        allocator.release_tensor("test")


class TestExecutor:
    """执行器测试"""

    def test_simple_graph_execution(self):
        """测试简单图执行"""
        graph = ComputeGraph()

        # 创建简单的 ReLU 图
        # input -> relu -> output
        graph.add_node(GraphNode(
            name="relu",
            op_type="Relu",
            inputs=["input"],
            outputs=["output"],
        ))

        graph.set_input("input", (1, 3, 4, 4))
        graph.set_output("output")

        # 创建执行器
        executor = Executor(graph)

        # 执行
        inputs = {"input": np.random.randn(1, 3, 4, 4).astype(np.float32)}
        outputs = executor.execute(inputs)

        # 验证
        assert "output" in outputs
        assert outputs["output"].shape == (1, 3, 4, 4)
        assert np.all(outputs["output"] >= 0)  # ReLU 输出应该非负

    def test_performance_stats(self):
        """测试性能统计"""
        graph = ComputeGraph()

        graph.add_node(GraphNode(
            name="relu",
            op_type="Relu",
            inputs=["input"],
            outputs=["output"],
        ))

        graph.set_input("input", (1, 3, 4, 4))
        graph.set_output("output")

        executor = Executor(graph)

        # 执行多次
        inputs = {"input": np.random.randn(1, 3, 4, 4).astype(np.float32)}
        for _ in range(10):
            executor.execute(inputs)

        # 获取统计
        stats = executor.get_performance_stats()
        assert stats["total_time_ms"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
执行器模块

负责执行计算图中的算子
"""

import numpy as np
from typing import Dict, List, Optional, Any
import logging
import time

from .graph import ComputeGraph, GraphNode
from .memory import MemoryPool, TensorAllocator

logger = logging.getLogger(__name__)


class Operator:
    """算子基类"""

    def execute(
        self,
        inputs: Dict[str, np.ndarray],
        params: Dict[str, Any],
    ) -> Dict[str, np.ndarray]:
        """
        执行算子

        Args:
            inputs: 输入张量字典
            params: 算子参数

        Returns:
            输出张量字典
        """
        raise NotImplementedError


class Conv2dOperator(Operator):
    """卷积算子"""

    def execute(self, inputs, params):
        x = inputs['input']
        weight = inputs['weight']
        bias = inputs.get('bias', None)

        stride = params.get('stride', 1)
        padding = params.get('padding', 0)

        # 简化实现：使用 NumPy 实现卷积
        output = self._conv2d(x, weight, bias, stride, padding)

        return {'output': output}

    def _conv2d(self, x, weight, bias, stride, padding):
        """卷积实现"""
        batch, in_channels, h, w = x.shape
        out_channels, _, kh, kw = weight.shape

        # 添加 padding
        if padding > 0:
            x = np.pad(x, ((0, 0), (0, 0), (padding, padding), (padding, padding)))

        # 计算输出尺寸
        out_h = (h + 2 * padding - kh) // stride + 1
        out_w = (w + 2 * padding - kw) // stride + 1

        output = np.zeros((batch, out_channels, out_h, out_w))

        # 卷积计算
        for b in range(batch):
            for oc in range(out_channels):
                for oh in range(out_h):
                    for ow in range(out_w):
                        h_start = oh * stride
                        w_start = ow * stride
                        receptive_field = x[b, :, h_start:h_start+kh, w_start:w_start+kw]
                        output[b, oc, oh, ow] = np.sum(receptive_field * weight[oc])

                        if bias is not None:
                            output[b, oc, oh, ow] += bias[oc]

        return output


class LinearOperator(Operator):
    """全连接算子"""

    def execute(self, inputs, params):
        x = inputs['input']
        weight = inputs['weight']
        bias = inputs.get('bias', None)

        output = np.dot(x, weight.T)
        if bias is not None:
            output += bias

        return {'output': output}


class ReLUOperator(Operator):
    """ReLU 激活函数"""

    def execute(self, inputs, params):
        x = inputs['input']
        return {'output': np.maximum(0, x)}


class MaxPoolOperator(Operator):
    """最大池化算子"""

    def execute(self, inputs, params):
        x = inputs['input']
        kernel_size = params.get('kernel_size', 2)
        stride = params.get('stride', 2)

        batch, channels, h, w = x.shape
        out_h = (h - kernel_size) // stride + 1
        out_w = (w - kernel_size) // stride + 1

        output = np.zeros((batch, channels, out_h, out_w))

        for b in range(batch):
            for c in range(channels):
                for oh in range(out_h):
                    for ow in range(out_w):
                        h_start = oh * stride
                        w_start = ow * stride
                        receptive_field = x[b, c, h_start:h_start+kernel_size, w_start:w_start+kernel_size]
                        output[b, c, oh, ow] = np.max(receptive_field)

        return {'output': output}


class AveragePoolOperator(Operator):
    """平均池化算子"""

    def execute(self, inputs, params):
        x = inputs['input']
        kernel_size = params.get('kernel_size', 2)
        stride = params.get('stride', 2)

        batch, channels, h, w = x.shape
        out_h = (h - kernel_size) // stride + 1
        out_w = (w - kernel_size) // stride + 1

        output = np.zeros((batch, channels, out_h, out_w))

        for b in range(batch):
            for c in range(channels):
                for oh in range(out_h):
                    for ow in range(out_w):
                        h_start = oh * stride
                        w_start = ow * stride
                        receptive_field = x[b, c, h_start:h_start+kernel_size, w_start:w_start+kernel_size]
                        output[b, c, oh, ow] = np.mean(receptive_field)

        return {'output': output}


class AddOperator(Operator):
    """加法算子"""

    def execute(self, inputs, params):
        a = inputs['input_a']
        b = inputs['input_b']
        return {'output': a + b}


class ReshapeOperator(Operator):
    """Reshape 算子"""

    def execute(self, inputs, params):
        x = inputs['input']
        shape = params.get('shape', (-1,))
        return {'output': x.reshape(shape)}


class FlattenOperator(Operator):
    """Flatten 算子"""

    def execute(self, inputs, params):
        x = inputs['input']
        return {'output': x.reshape(x.shape[0], -1)}


class OperatorRegistry:
    """算子注册表"""

    _operators: Dict[str, Operator] = {
        'Conv': Conv2dOperator(),
        'Linear': LinearOperator(),
        'Relu': ReLUOperator(),
        'MaxPool': MaxPoolOperator(),
        'AveragePool': AveragePoolOperator(),
        'Add': AddOperator(),
        'Reshape': ReshapeOperator(),
        'Flatten': FlattenOperator(),
    }

    @classmethod
    def get(cls, op_type: str) -> Optional[Operator]:
        """获取算子"""
        return cls._operators.get(op_type)

    @classmethod
    def register(cls, op_type: str, operator: Operator):
        """注册算子"""
        cls._operators[op_type] = operator


class Executor:
    """
    执行器

    负责按拓扑序执行计算图中的算子
    """

    def __init__(
        self,
        graph: ComputeGraph,
        memory_pool: Optional[MemoryPool] = None,
    ):
        """
        初始化执行器

        Args:
            graph: 计算图
            memory_pool: 内存池（可选）
        """
        self.graph = graph
        self.memory_pool = memory_pool or MemoryPool(1024 * 1024)  # 默认 1M 元素
        self.tensor_allocator = TensorAllocator(self.memory_pool)
        self.tensor_cache: Dict[str, np.ndarray] = {}

        # 性能统计
        self.execution_times: Dict[str, float] = {}

    def execute(
        self,
        inputs: Dict[str, np.ndarray],
        output_names: Optional[List[str]] = None,
    ) -> Dict[str, np.ndarray]:
        """
        执行计算图

        Args:
            inputs: 输入张量字典
            output_names: 需要输出的张量名称，如果为 None 则返回所有输出

        Returns:
            输出张量字典
        """
        logger.info("开始执行计算图")

        # 清空缓存
        self.tensor_cache.clear()
        self.execution_times.clear()

        # 设置输入
        for name, tensor in inputs.items():
            self.tensor_cache[name] = tensor

        # 拓扑排序
        try:
            topo_order = self.graph.topological_sort()
        except ValueError as e:
            logger.error(f"拓扑排序失败: {e}")
            raise

        # 按拓扑序执行
        for node_name in topo_order:
            node = self.graph.nodes[node_name]

            # 获取输入
            node_inputs = {}
            for inp_name in node.inputs:
                if inp_name in self.tensor_cache:
                    node_inputs[inp_name] = self.tensor_cache[inp_name]
                else:
                    raise ValueError(f"找不到输入张量: {inp_name}")

            # 执行算子
            start_time = time.time()
            outputs = self._execute_operator(node, node_inputs)
            end_time = time.time()

            # 记录执行时间
            self.execution_times[node_name] = end_time - start_time

            # 缓存输出
            for out_name, out_tensor in outputs.items():
                self.tensor_cache[out_name] = out_tensor

            logger.debug(f"执行节点 {node_name} ({node.op_type}): "
                        f"time={self.execution_times[node_name]*1000:.2f}ms")

        # 获取输出
        if output_names is None:
            output_names = self.graph.outputs

        result = {}
        for name in output_names:
            if name in self.tensor_cache:
                result[name] = self.tensor_cache[name]
            else:
                logger.warning(f"输出张量 {name} 不存在")

        logger.info(f"计算图执行完成，总时间: {sum(self.execution_times.values())*1000:.2f}ms")

        return result

    def _execute_operator(
        self,
        node: GraphNode,
        inputs: Dict[str, np.ndarray],
    ) -> Dict[str, np.ndarray]:
        """
        执行单个算子

        Args:
            node: 图节点
            inputs: 输入张量

        Returns:
            输出张量
        """
        # 获取算子实现
        operator = OperatorRegistry.get(node.op_type)
        if operator is None:
            raise ValueError(f"不支持的算子类型: {node.op_type}")

        # 执行算子
        return operator.execute(inputs, node.params)

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计

        Returns:
            性能统计字典
        """
        if not self.execution_times:
            return {}

        total_time = sum(self.execution_times.values())

        # 按算子类型统计
        op_times = {}
        for node_name, exec_time in self.execution_times.items():
            node = self.graph.nodes[node_name]
            op_type = node.op_type
            if op_type not in op_times:
                op_times[op_type] = []
            op_times[op_type].append(exec_time)

        op_stats = {}
        for op_type, times in op_times.items():
            op_stats[op_type] = {
                "count": len(times),
                "total_ms": sum(times) * 1000,
                "avg_ms": np.mean(times) * 1000,
                "max_ms": max(times) * 1000,
                "min_ms": min(times) * 1000,
            }

        return {
            "total_time_ms": total_time * 1000,
            "node_times": {name: t * 1000 for name, t in self.execution_times.items()},
            "op_stats": op_stats,
        }

    def reset(self):
        """重置执行器"""
        self.tensor_cache.clear()
        self.execution_times.clear()
        self.tensor_allocator.reset()

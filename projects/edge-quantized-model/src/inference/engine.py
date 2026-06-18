"""
推理引擎模块

提供高层推理接口，整合计算图、执行器和内存管理
"""

import numpy as np
from typing import Dict, List, Optional, Any, Union
import logging
import time

from .graph import ComputeGraph, GraphNode
from .executor import Executor, OperatorRegistry
from .memory import MemoryPool

logger = logging.getLogger(__name__)


class InferenceEngine:
    """
    推理引擎

    提供高层推理接口，支持：
    - 模型加载
    - 推理执行
    - 性能监控
    - 结果后处理

    使用示例:
        engine = InferenceEngine("model.onnx")
        result = engine.inference(input_data)
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        graph: Optional[ComputeGraph] = None,
        memory_pool_size: int = 1024 * 1024,
    ):
        """
        初始化推理引擎

        Args:
            model_path: 模型文件路径（支持 ONNX）
            graph: 计算图（直接提供）
            memory_pool_size: 内存池大小
        """
        self.graph = graph
        self.memory_pool = MemoryPool(memory_pool_size)
        self.executor = None
        self.is_loaded = False

        # 性能统计
        self.inference_times: List[float] = []
        self.total_inferences = 0

        # 加载模型
        if model_path is not None:
            self.load_model(model_path)
        elif graph is not None:
            self._init_executor()

    def load_model(self, model_path: str):
        """
        加载模型

        Args:
            model_path: 模型文件路径
        """
        logger.info(f"加载模型: {model_path}")

        if model_path.endswith('.onnx'):
            self._load_onnx(model_path)
        else:
            raise ValueError(f"不支持的模型格式: {model_path}")

        self._init_executor()
        self.is_loaded = True

        logger.info(f"模型加载完成: {len(self.graph.nodes)} 个节点")

    def _load_onnx(self, model_path: str):
        """
        加载 ONNX 模型

        Args:
            model_path: ONNX 模型路径
        """
        try:
            import onnx
            model = onnx.load(model_path)
            self._convert_onnx_to_graph(model)
        except ImportError:
            raise ImportError("需要安装 onnx 库: pip install onnx")

    def _convert_onnx_to_graph(self, onnx_model):
        """
        将 ONNX 模型转换为计算图

        Args:
            onnx_model: ONNX 模型
        """
        self.graph = ComputeGraph()

        # 添加输入
        for input in onnx_model.graph.input:
            shape = tuple(d.dim_value for d in input.type.tensor_type.shape.dim)
            self.graph.set_input(input.name, shape)

        # 添加节点
        for node in onnx_model.graph.node:
            graph_node = GraphNode(
                name=node.name or f"{node.op_type}_{id(node)}",
                op_type=node.op_type,
                inputs=list(node.input),
                outputs=list(node.output),
                params={attr.name: self._convert_onnx_attr(attr) for attr in node.attribute},
            )
            self.graph.add_node(graph_node)

        # 添加输出
        for output in onnx_model.graph.output:
            self.graph.set_output(output.name)

    def _convert_onnx_attr(self, attr):
        """转换 ONNX 属性"""
        if attr.type == 1:  # FLOAT
            return attr.f
        elif attr.type == 2:  # INT
            return attr.i
        elif attr.type == 3:  # STRING
            return attr.s.decode()
        elif attr.type == 4:  # FLOATS
            return list(attr.floats)
        elif attr.type == 5:  # INTS
            return list(attr.ints)
        else:
            return None

    def _init_executor(self):
        """初始化执行器"""
        self.executor = Executor(self.graph, self.memory_pool)

    def inference(
        self,
        inputs: Dict[str, np.ndarray],
        output_names: Optional[List[str]] = None,
    ) -> Dict[str, np.ndarray]:
        """
        执行推理

        Args:
            inputs: 输入张量字典
            output_names: 需要输出的张量名称

        Returns:
            输出张量字典
        """
        if not self.is_loaded:
            raise RuntimeError("模型未加载")

        logger.info("开始推理")

        # 执行推理
        start_time = time.time()
        results = self.executor.execute(inputs, output_names)
        end_time = time.time()

        # 记录性能
        inference_time = end_time - start_time
        self.inference_times.append(inference_time)
        self.total_inferences += 1

        logger.info(f"推理完成: time={inference_time*1000:.2f}ms")

        return results

    def benchmark(
        self,
        inputs: Dict[str, np.ndarray],
        num_iterations: int = 100,
        warmup_iterations: int = 10,
    ) -> Dict[str, float]:
        """
        性能基准测试

        Args:
            inputs: 输入张量
            num_iterations: 测试迭代次数
            warmup_iterations: 预热迭代次数

        Returns:
            性能统计
        """
        logger.info(f"开始基准测试: iterations={num_iterations}, warmup={warmup_iterations}")

        # 预热
        for _ in range(warmup_iterations):
            self.inference(inputs)

        # 测试
        times = []
        for _ in range(num_iterations):
            start_time = time.time()
            self.inference(inputs)
            end_time = time.time()
            times.append(end_time - start_time)

        times = np.array(times)

        return {
            "mean_ms": float(np.mean(times) * 1000),
            "std_ms": float(np.std(times) * 1000),
            "min_ms": float(np.min(times) * 1000),
            "max_ms": float(np.max(times) * 1000),
            "median_ms": float(np.median(times) * 1000),
            "p95_ms": float(np.percentile(times, 95) * 1000),
            "p99_ms": float(np.percentile(times, 99) * 1000),
            "fps": float(1.0 / np.mean(times)),
            "iterations": num_iterations,
        }

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计

        Returns:
            性能统计字典
        """
        if not self.inference_times:
            return {}

        times = np.array(self.inference_times)

        stats = {
            "total_inferences": self.total_inferences,
            "mean_ms": float(np.mean(times) * 1000),
            "std_ms": float(np.std(times) * 1000),
            "min_ms": float(np.min(times) * 1000),
            "max_ms": float(np.max(times) * 1000),
        }

        # 添加执行器统计
        if self.executor:
            stats["executor"] = self.executor.get_performance_stats()

        return stats

    def reset_stats(self):
        """重置性能统计"""
        self.inference_times.clear()
        self.total_inferences = 0

    def get_graph_summary(self) -> str:
        """
        获取计算图摘要

        Returns:
            摘要字符串
        """
        if self.graph is None:
            return "No graph loaded"
        return self.graph.summary()

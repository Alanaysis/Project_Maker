"""
算子融合模块

提供算子融合功能，优化推理性能：
- Conv + BN 融合
- Conv + BN + ReLU 融合
- Linear + ReLU 融合
"""

import numpy as np
from typing import Dict, Tuple, Optional, Any, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class FusionPattern:
    """
    融合模式

    Attributes:
        pattern: 算子类型序列
        fusion_func: 融合函数
        name: 融合名称
    """
    pattern: List[str]
    fusion_func: callable
    name: str


def fuse_conv_bn(
    conv_weight: np.ndarray,
    conv_bias: Optional[np.ndarray],
    bn_mean: np.ndarray,
    bn_var: np.ndarray,
    bn_weight: np.ndarray,
    bn_bias: np.ndarray,
    eps: float = 1e-5,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    融合 Conv 和 BN

    融合公式：
    scale = gamma / sqrt(var + eps)
    fused_weight = conv_weight * scale
    fused_bias = (conv_bias - mean) * scale + beta

    Args:
        conv_weight: 卷积权重 [out_channels, in_channels, kh, kw]
        conv_bias: 卷积偏置 [out_channels]
        bn_mean: BN 均值 [out_channels]
        bn_var: BN 方差 [out_channels]
        bn_weight: BN 缩放因子 (gamma) [out_channels]
        bn_bias: BN 偏置 (beta) [out_channels]
        eps: 数值稳定性参数

    Returns:
        (fused_weight, fused_bias)
    """
    # 计算缩放因子
    scale = bn_weight / np.sqrt(bn_var + eps)

    # 融合权重
    fused_weight = conv_weight * scale.reshape(-1, 1, 1, 1)

    # 融合偏置
    if conv_bias is not None:
        fused_bias = (conv_bias - bn_mean) * scale + bn_bias
    else:
        fused_bias = -bn_mean * scale + bn_bias

    return fused_weight, fused_bias


def fuse_conv_bn_relu(
    conv_weight: np.ndarray,
    conv_bias: Optional[np.ndarray],
    bn_mean: np.ndarray,
    bn_var: np.ndarray,
    bn_weight: np.ndarray,
    bn_bias: np.ndarray,
    eps: float = 1e-5,
) -> Tuple[np.ndarray, np.ndarray, bool]:
    """
    融合 Conv + BN + ReLU

    Args:
        conv_weight: 卷积权重
        conv_bias: 卷积偏置
        bn_mean: BN 均值
        bn_var: BN 方差
        bn_weight: BN 缩放因子
        bn_bias: BN 偏置
        eps: 数值稳定性参数

    Returns:
        (fused_weight, fused_bias, has_relu)
    """
    fused_weight, fused_bias = fuse_conv_bn(
        conv_weight, conv_bias, bn_mean, bn_var, bn_weight, bn_bias, eps
    )

    return fused_weight, fused_bias, True


def fuse_linear_relu(
    linear_weight: np.ndarray,
    linear_bias: Optional[np.ndarray],
) -> Tuple[np.ndarray, Optional[np.ndarray], bool]:
    """
    融合 Linear + ReLU

    Args:
        linear_weight: 全连接权重
        linear_bias: 全连接偏置

    Returns:
        (fused_weight, fused_bias, has_relu)
    """
    # Linear + ReLU 的融合不需要修改权重和偏置
    # ReLU 在执行时应用
    return linear_weight, linear_bias, True


class OperatorFusion:
    """
    算子融合器

    自动检测和应用算子融合模式

    使用示例:
        fusion = OperatorFusion()
        optimized_graph = fusion.fuse(graph)
    """

    def __init__(self):
        """初始化融合器"""
        self.patterns = [
            FusionPattern(
                pattern=['Conv', 'BatchNormalization', 'Relu'],
                fusion_func=fuse_conv_bn_relu,
                name='Conv+BN+ReLU',
            ),
            FusionPattern(
                pattern=['Conv', 'BatchNormalization'],
                fusion_func=fuse_conv_bn,
                name='Conv+BN',
            ),
            FusionPattern(
                pattern=['Linear', 'Relu'],
                fusion_func=fuse_linear_relu,
                name='Linear+ReLU',
            ),
        ]

        # 统计信息
        self.fusion_stats = {}

    def fuse(self, graph: 'ComputeGraph') -> 'ComputeGraph':
        """
        对计算图执行融合优化

        Args:
            graph: 输入计算图

        Returns:
            优化后的计算图
        """
        logger.info("开始算子融合优化")

        self.fusion_stats = {}

        # 尝试每种融合模式
        for pattern in self.patterns:
            graph = self._apply_pattern(graph, pattern)

        # 输出统计
        total_fusions = sum(self.fusion_stats.values())
        logger.info(f"融合优化完成: 共 {total_fusions} 处融合")
        for name, count in self.fusion_stats.items():
            if count > 0:
                logger.info(f"  {name}: {count} 处")

        return graph

    def _apply_pattern(
        self,
        graph: 'ComputeGraph',
        pattern: FusionPattern,
    ) -> 'ComputeGraph':
        """
        应用融合模式

        Args:
            graph: 计算图
            pattern: 融合模式

        Returns:
            优化后的计算图
        """
        # 查找匹配的节点序列
        matches = self._find_pattern_matches(graph, pattern.pattern)

        if not matches:
            return graph

        # 应用融合
        for match in matches:
            graph = self._apply_fusion(graph, match, pattern)

        self.fusion_stats[pattern.name] = len(matches)

        return graph

    def _find_pattern_matches(
        self,
        graph: 'ComputeGraph',
        pattern: List[str],
    ) -> List[List[str]]:
        """
        查找匹配的节点序列

        Args:
            graph: 计算图
            pattern: 算子类型序列

        Returns:
            匹配的节点名称序列列表
        """
        matches = []

        # 拓扑排序
        try:
            topo_order = graph.topological_sort()
        except ValueError:
            return matches

        # 查找匹配
        for i, node_name in enumerate(topo_order):
            node = graph.nodes[node_name]

            # 检查是否是模式的起始
            if node.op_type == pattern[0]:
                # 尝试匹配整个模式
                match = [node_name]
                current_node = node

                for j in range(1, len(pattern)):
                    # 查找后继节点
                    successors = graph.get_successors(current_node.name)

                    # 查找匹配的后继
                    found = False
                    for succ_name in successors:
                        succ_node = graph.nodes[succ_name]
                        if succ_node.op_type == pattern[j]:
                            match.append(succ_name)
                            current_node = succ_node
                            found = True
                            break

                    if not found:
                        break

                # 如果完整匹配
                if len(match) == len(pattern):
                    matches.append(match)

        return matches

    def _apply_fusion(
        self,
        graph: 'ComputeGraph',
        match: List[str],
        pattern: FusionPattern,
    ) -> 'ComputeGraph':
        """
        应用融合

        Args:
            graph: 计算图
            match: 匹配的节点序列
            pattern: 融合模式

        Returns:
            优化后的计算图
        """
        # 获取节点
        nodes = [graph.nodes[name] for name in match]

        # 创建融合节点
        fused_node = self._create_fused_node(nodes, pattern)

        # 更新图
        # 1. 添加融合节点
        graph.add_node(fused_node)

        # 2. 重定向边
        # 获取第一个节点的输入
        first_node = nodes[0]
        # 获取最后一个节点的输出
        last_node = nodes[-1]

        # 更新输入边
        for inp in first_node.inputs:
            # 找到产生这个输入的节点
            source_node = graph.get_node_for_input(inp)
            if source_node:
                # 更新源节点的输出
                source = graph.nodes[source_node]
                source.outputs = [
                    fused_node.inputs[0] if o == inp else o
                    for o in source.outputs
                ]

        # 更新输出边
        for out in last_node.outputs:
            # 找到消费这个输出的节点
            consumer_nodes = graph.get_nodes_for_output(out)
            for consumer_name in consumer_nodes:
                consumer = graph.nodes[consumer_name]
                consumer.inputs = [
                    fused_node.outputs[0] if i == out else i
                    for i in consumer.inputs
                ]

        # 3. 删除原始节点
        for name in match:
            graph.remove_node(name)

        return graph

    def _create_fused_node(
        self,
        nodes: List['GraphNode'],
        pattern: FusionPattern,
    ) -> 'GraphNode':
        """
        创建融合节点

        Args:
            nodes: 原始节点列表
            pattern: 融合模式

        Returns:
            融合后的节点
        """
        # 合并参数
        fused_params = {}
        for node in nodes:
            fused_params.update(node.params)

        # 标记融合
        fused_params['_fused_ops'] = [n.op_type for n in nodes]
        fused_params['_has_relu'] = 'Relu' in [n.op_type for n in nodes]

        # 创建融合节点
        fused_node = GraphNode(
            name=f"_fused_{'_'.join(n.name for n in nodes)}",
            op_type=nodes[0].op_type,  # 使用第一个算子的类型
            inputs=nodes[0].inputs,
            outputs=nodes[-1].outputs,
            params=fused_params,
        )

        return fused_node

    def get_fusion_stats(self) -> Dict[str, int]:
        """
        获取融合统计

        Returns:
            融合统计字典
        """
        return self.fusion_stats.copy()

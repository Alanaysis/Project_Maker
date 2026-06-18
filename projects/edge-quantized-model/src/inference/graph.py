"""
计算图模块

实现计算图的数据结构和操作：
- 节点定义
- 图构建
- 拓扑排序
- 图优化
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque


@dataclass
class GraphNode:
    """
    计算图节点

    Attributes:
        name: 节点名称
        op_type: 算子类型
        inputs: 输入名称列表
        outputs: 输出名称列表
        params: 算子参数
        attrs: 节点属性
    """
    name: str
    op_type: str
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    params: Dict[str, Any] = field(default_factory=dict)
    attrs: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self):
        return f"GraphNode(name='{self.name}', op_type='{self.op_type}')"


class ComputeGraph:
    """
    计算图

    表示模型的计算流程，支持：
    - 节点添加和删除
    - 拓扑排序
    - 图优化
    - 子图提取
    """

    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.inputs: List[str] = []
        self.outputs: List[str] = []
        self._adjacency: Dict[str, List[str]] = defaultdict(list)  # 前驱 -> 后继
        self._reverse_adjacency: Dict[str, List[str]] = defaultdict(list)  # 后继 -> 前驱
        self._tensor_shapes: Dict[str, Tuple[int, ...]] = {}

    def add_node(self, node: GraphNode):
        """
        添加节点

        Args:
            node: 图节点
        """
        self.nodes[node.name] = node

        # 更新邻接关系
        for inp in node.inputs:
            self._adjacency[inp].append(node.name)
            self._reverse_adjacency[node.name].append(inp)

    def remove_node(self, name: str):
        """
        删除节点

        Args:
            name: 节点名称
        """
        if name not in self.nodes:
            raise ValueError(f"节点 {name} 不存在")

        node = self.nodes[name]

        # 更新邻接关系
        for inp in node.inputs:
            if name in self._adjacency[inp]:
                self._adjacency[inp].remove(name)

        for out in node.outputs:
            if out in self._reverse_adjacency:
                for successor in self._adjacency.get(out, []):
                    if name in self._reverse_adjacency[successor]:
                        self._reverse_adjacency[successor].remove(name)

        # 删除节点
        del self.nodes[name]

    def set_input(self, name: str, shape: Tuple[int, ...]):
        """
        设置输入

        Args:
            name: 输入名称
            shape: 输入形状
        """
        if name not in self.inputs:
            self.inputs.append(name)
        self._tensor_shapes[name] = shape

    def set_output(self, name: str):
        """
        设置输出

        Args:
            name: 输出名称
        """
        if name not in self.outputs:
            self.outputs.append(name)

    def set_tensor_shape(self, name: str, shape: Tuple[int, ...]):
        """
        设置张量形状

        Args:
            name: 张量名称
            shape: 形状
        """
        self._tensor_shapes[name] = shape

    def get_tensor_shape(self, name: str) -> Optional[Tuple[int, ...]]:
        """
        获取张量形状

        Args:
            name: 张量名称

        Returns:
            张量形状，如果不存在返回 None
        """
        return self._tensor_shapes.get(name)

    def topological_sort(self) -> List[str]:
        """
        拓扑排序

        使用 Kahn 算法进行拓扑排序

        Returns:
            排序后的节点名称列表

        Raises:
            ValueError: 如果图中存在环
        """
        # 计算入度
        in_degree = defaultdict(int)
        for node_name in self.nodes:
            in_degree[node_name] = len(self._reverse_adjacency.get(node_name, []))

        # 初始化队列
        queue = deque()
        for node_name in self.nodes:
            if in_degree[node_name] == 0:
                queue.append(node_name)

        result = []

        while queue:
            node_name = queue.popleft()
            result.append(node_name)

            # 更新后继节点的入度
            node = self.nodes[node_name]
            for output in node.outputs:
                for successor in self._adjacency.get(output, []):
                    in_degree[successor] -= 1
                    if in_degree[successor] == 0:
                        queue.append(successor)

        # 检查是否有环
        if len(result) != len(self.nodes):
            raise ValueError("图中存在环")

        return result

    def get_predecessors(self, name: str) -> List[str]:
        """
        获取前驱节点

        Args:
            name: 节点名称

        Returns:
            前驱节点名称列表
        """
        return self._reverse_adjacency.get(name, [])

    def get_successors(self, name: str) -> List[str]:
        """
        获取后继节点

        Args:
            name: 节点名称

        Returns:
            后继节点名称列表
        """
        node = self.nodes[name]
        successors = []
        for output in node.outputs:
            successors.extend(self._adjacency.get(output, []))
        return list(set(successors))

    def get_node_for_input(self, tensor_name: str) -> Optional[str]:
        """
        获取产生指定张量的节点

        Args:
            tensor_name: 张量名称

        Returns:
            节点名称，如果不存在返回 None
        """
        for node_name, node in self.nodes.items():
            if tensor_name in node.outputs:
                return node_name
        return None

    def get_nodes_for_output(self, tensor_name: str) -> List[str]:
        """
        获取消费指定张量的节点

        Args:
            tensor_name: 张量名称

        Returns:
            节点名称列表
        """
        nodes = []
        for node_name, node in self.nodes.items():
            if tensor_name in node.inputs:
                nodes.append(node_name)
        return nodes

    def validate(self) -> List[str]:
        """
        验证图的有效性

        Returns:
            错误信息列表，空列表表示图有效
        """
        errors = []

        # 检查输入节点
        for inp in self.inputs:
            if inp not in self._tensor_shapes:
                errors.append(f"输入 {inp} 缺少形状信息")

        # 检查节点依赖
        for node_name, node in self.nodes.items():
            for inp in node.inputs:
                # 检查输入是否来自其他节点的输出或是图输入
                source_node = self.get_node_for_input(inp)
                if source_node is None and inp not in self.inputs:
                    errors.append(f"节点 {node_name} 的输入 {inp} 不存在")

        return errors

    def get_subgraph(self, start_node: str, end_node: str) -> 'ComputeGraph':
        """
        获取子图

        Args:
            start_node: 起始节点
            end_node: 结束节点

        Returns:
            子图
        """
        # BFS 获取子图中的节点
        subgraph_nodes = set()
        queue = deque([start_node])

        while queue:
            node_name = queue.popleft()
            if node_name in subgraph_nodes:
                continue

            subgraph_nodes.add(node_name)

            if node_name == end_node:
                break

            # 添加后继节点
            for successor in self.get_successors(node_name):
                if successor not in subgraph_nodes:
                    queue.append(successor)

        # 创建子图
        subgraph = ComputeGraph()
        for node_name in subgraph_nodes:
            subgraph.add_node(self.nodes[node_name])

        return subgraph

    def summary(self) -> str:
        """
        获取图的摘要信息

        Returns:
            摘要字符串
        """
        lines = [
            f"ComputeGraph Summary:",
            f"  Nodes: {len(self.nodes)}",
            f"  Inputs: {self.inputs}",
            f"  Outputs: {self.outputs}",
            f"  Node types:",
        ]

        # 统计节点类型
        op_counts = defaultdict(int)
        for node in self.nodes.values():
            op_counts[node.op_type] += 1

        for op_type, count in sorted(op_counts.items()):
            lines.append(f"    {op_type}: {count}")

        return "\n".join(lines)

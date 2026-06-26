"""
布局测量系统 - Layout Measurement

鸿蒙布局测量流程：
1. 父容器下发约束 (measure)
2. 子组件根据约束计算自身尺寸
3. 子组件返回测量结果
4. 父容器根据结果布局子组件

鸿蒙使用双遍测量：
- 第一遍：测量所有子组件
- 第二遍：布局所有子组件
"""

from typing import Dict, Optional
from .constraints import Constraints


class Measurement:
    """测量结果"""

    def __init__(self, width: float = 0, height: float = 0):
        self.width = width
        self.height = height

    def to_dict(self) -> Dict:
        return {'width': self.width, 'height': self.height}

    def __repr__(self):
        return f'Measurement({self.width}x{self.height})'


class LayoutMeasurer:
    """
    布局测量器

    模拟鸿蒙的布局测量流程：
    1. 根据约束测量子组件
    2. 计算容器最终尺寸
    3. 返回布局结果
    """

    def __init__(self):
        self._measure_log: list = []

    def measure_column(self, children_measurements: list,
                       constraints: Constraints,
                       gap: float = 0) -> Measurement:
        """测量 Column 容器"""
        max_width = 0
        total_height = 0

        for i, child_m in enumerate(children_measurements):
            total_height += child_m.height
            max_width = max(max_width, child_m.width)
            if i > 0:
                total_height += gap

        # 应用约束
        final_width = (constraints.width['definite']
                       if constraints.width['definite'] is not None
                       else min(max_width, constraints.width['max']))
        final_height = (constraints.height['definite']
                        if constraints.height['definite'] is not None
                        else min(total_height, constraints.height['max']))

        result = Measurement(
            width=max(final_width, constraints.width['min']),
            height=max(final_height, constraints.height['min']),
        )
        self._measure_log.append({'type': 'Column', 'result': result.to_dict()})
        return result

    def measure_row(self, children_measurements: list,
                    constraints: Constraints,
                    gap: float = 0) -> Measurement:
        """测量 Row 容器"""
        max_height = 0
        total_width = 0

        for i, child_m in enumerate(children_measurements):
            total_width += child_m.width
            max_height = max(max_height, child_m.height)
            if i > 0:
                total_width += gap

        final_width = (constraints.width['definite']
                       if constraints.width['definite'] is not None
                       else min(total_width, constraints.width['max']))
        final_height = (constraints.height['definite']
                        if constraints.height['definite'] is not None
                        else max_height)

        result = Measurement(
            width=max(final_width, constraints.width['min']),
            height=max(final_height, constraints.height['min']),
        )
        self._measure_log.append({'type': 'Row', 'result': result.to_dict()})
        return result

    def measure_stack(self, children_measurements: list,
                      constraints: Constraints) -> Measurement:
        """测量 Stack 容器"""
        max_width = max((m.width for m in children_measurements), default=0)
        max_height = max((m.height for m in children_measurements), default=0)

        final_width = (constraints.width['definite']
                       if constraints.width['definite'] is not None
                       else max_width)
        final_height = (constraints.height['definite']
                        if constraints.height['definite'] is not None
                        else max_height)

        result = Measurement(
            width=max(final_width, constraints.width['min']),
            height=max(final_height, constraints.height['min']),
        )
        self._measure_log.append({'type': 'Stack', 'result': result.to_dict()})
        return result

    def get_measure_log(self) -> list:
        return list(self._measure_log)

    def __repr__(self):
        return f'LayoutMeasurer(log_entries={len(self._measure_log)})'

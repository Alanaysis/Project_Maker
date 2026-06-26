"""
布局约束系统 - Layout Constraints

鸿蒙 ArkUI 的布局约束系统：
- 确定约束 (definite): 固定尺寸
- 最小约束 (min): 最小尺寸
- 最大约束 (max): 最大尺寸
- 比例约束 (proportion): 百分比

约束传播：
父容器 -> 测量子组件 -> 子组件返回测量结果 -> 父容器布局
"""

from typing import Dict, Optional


class Constraints:
    """
    布局约束

    鸿蒙布局约束系统：
    - width: 宽度约束 { min, max, definite }
    - height: 高度约束 { min, max, definite }
    """

    def __init__(self):
        self.width = {'min': 0, 'max': float('inf'), 'definite': None}
        self.height = {'min': 0, 'max': float('inf'), 'definite': None}

    def set_width(self, definite: Optional[float] = None,
                  min_width: Optional[float] = None,
                  max_width: Optional[float] = None):
        if definite is not None:
            self.width['definite'] = definite
        if min_width is not None:
            self.width['min'] = min_width
        if max_width is not None:
            self.width['max'] = max_width

    def set_height(self, definite: Optional[float] = None,
                   min_height: Optional[float] = None,
                   max_height: Optional[float] = None):
        if definite is not None:
            self.height['definite'] = definite
        if min_height is not None:
            self.height['min'] = min_height
        if max_height is not None:
            self.height['max'] = max_height

    def has_definite_width(self) -> bool:
        return self.width['definite'] is not None

    def has_definite_height(self) -> bool:
        return self.height['definite'] is not None

    def to_dict(self) -> Dict:
        return {
            'width': dict(self.width),
            'height': dict(self.height),
        }

    def __repr__(self):
        return f'Constraints(w={self.width}, h={self.height})'

"""
跨平台框架原理 - Cross-Platform Framework Principles

核心模块：渲染树布局引擎
功能：模拟 Flutter 的布局系统（BoxConstraints, Layout, Size）

跨平台框架原理说明：
Flutter 的布局系统采用约束-尺寸-位置（Constraints-Size-Position）模型：

1. 约束（Constraints）：父 Widget 传递给子 Widget 的约束
   - minWidth / maxWidth
   - minHeight / maxHeight

2. 尺寸（Size）：子 Widget 在约束内选择自己的大小

3. 位置（Position）：父 Widget 决定子 Widget 在其内部的位置

布局方向：
- 自上而下传递约束（Constraints pass）
- 自下而上传递尺寸（Size pass）
- 自顶向下设置位置（Position pass）

本模块模拟：
1. BoxConstraints - 布局约束
2. LayoutPass - 布局传递
3. FlexLayout - 弹性布局
4. StackLayout - 层叠布局
5. CustomLayout - 自定义布局
"""

from typing import Any, Dict, List, Optional, Tuple
from .rendering_engine import Rect, Offset


# ============================================================
# 布局约束 (BoxConstraints)
# ============================================================
class BoxConstraints:
    """
    BoxConstraints - 盒模型布局约束

    在 Flutter 中，约束由父 Widget 传递给子 Widget。
    子 Widget 必须在这些约束内选择自己的大小。

    约束规则：
    - minWidth <= maxWidth
    - minHeight <= maxHeight
    - 0 <= minWidth <= maxWidth
    - 0 <= minHeight <= maxHeight

    特殊约束值：
    - minWidth = 0, maxWidth = infinity: 最大可用空间
    - minWidth = 100, maxWidth = 100: 固定宽度
    - minWidth = 0, maxWidth = 0: 零大小
    """

    def __init__(self,
                 min_width: float = 0.0,
                 max_width: float = float('inf'),
                 min_height: float = 0.0,
                 max_height: float = float('inf')):
        self._min_width = min_width
        self._max_width = max_width
        self._min_height = min_height
        self._max_height = max_height

    @property
    def min_width(self) -> float:
        return self._min_width

    @property
    def max_width(self) -> float:
        return self._max_width

    @property
    def min_height(self) -> float:
        return self._min_height

    @property
    def max_height(self) -> float:
        return self._max_height

    @property
    def is_unconstrained(self) -> bool:
        """检查是否无约束（无限大）"""
        return (self._max_width == float('inf') and
                self._max_height == float('inf'))

    @property
    def is_tight(self) -> bool:
        """检查是否固定大小（min == max）"""
        return (self._min_width == self._max_width and
                self._min_height == self._max_height)

    def enforce(self, size: Rect) -> Rect:
        """
        在约束内强制执行大小

        子 Widget 选择的大小必须在约束范围内。
        """
        width = max(self._min_width, min(self._max_width, size.width))
        height = max(self._min_height, min(self._max_height, size.height))
        return Rect.from_sizes(size.left, size.top, width, height)

    def expand(self) -> 'BoxConstraints':
        """返回无约束的副本"""
        return BoxConstraints(0, float('inf'), 0, float('inf'))

    def tight(self, size: Rect) -> 'BoxConstraints':
        """返回固定大小的约束"""
        return BoxConstraints(size.width, size.width, size.height, size.height)

    def tighten(self) -> 'BoxConstraints':
        """将约束收紧为固定大小"""
        return BoxConstraints(self._min_width, self._max_width,
                              self._min_height, self._max_height)

    def __repr__(self):
        w = f"[{self._min_width}, {self._max_width}]"
        h = f"[{self._min_height}, {self._max_height}]"
        return f"BoxConstraints({w}, {h})"


# ============================================================
# 布局结果 (LayoutResult)
# ============================================================
class LayoutResult:
    """布局计算的结果"""

    def __init__(self, size: Rect, offset: Offset = Offset(0, 0)):
        self._size = size
        self._offset = offset

    @property
    def size(self) -> Rect:
        return self._size

    @property
    def offset(self) -> Offset:
        return self._offset

    def to_dict(self) -> Dict[str, Any]:
        return {
            "size": self._size.to_dict(),
            "offset": {"dx": self._offset.dx, "dy": self._offset.dy},
        }


# ============================================================
# 布局引擎 (LayoutEngine)
# ============================================================
class LayoutEngine:
    """
    布局引擎

    模拟 Flutter 的三遍布局算法：
    1. Constraints pass（自上而下）：父传递约束给子
    2. Size pass（自下而上）：子报告大小给父
    3. Position pass（自顶向下）：父设置子位置

    布局树示例：
                    [0,∞]x[0,∞]
                    Container
                   /          \
           [0,∞]x[0,∞]    [0,∞]x[0,∞]
           Text              Icon
           (80x30)           (24x24)
    """

    def __init__(self):
        self._layout_log: List[str] = []
        self._pass_count = 0

    def layout(self, root_widget: Any, available_size: Tuple[float, float]) -> LayoutResult:
        """
        从根 Widget 开始执行布局

        Args:
            root_widget: 根 Widget
            available_size: 可用空间（父级约束）

        Returns:
            布局结果（最终大小和位置）
        """
        self._layout_log = []
        self._pass_count = 0

        # 创建约束
        constraints = BoxConstraints(0, available_size[0], 0, available_size[1])

        # 执行布局
        result = self._layout_node(root_widget, constraints)

        self._log(f"布局完成: 大小={result.size.width}x{result.size.height}, "
                  f"传递次数={self._pass_count}")

        return result

    def _layout_node(self, widget: Any, constraints: BoxConstraints) -> LayoutResult:
        """递归布局单个节点"""
        self._pass_count += 1

        # 获取小部件的布局策略
        layout_type = getattr(widget, 'layout_type', 'box')

        if layout_type == 'box':
            return self._layout_box(widget, constraints)
        elif layout_type == 'flex':
            return self._layout_flex(widget, constraints)
        elif layout_type == 'stack':
            return self._layout_stack(widget, constraints)
        else:
            return self._layout_box(widget, constraints)

    def _layout_box(self, widget: Any, constraints: BoxConstraints) -> LayoutResult:
        """盒模型布局"""
        # 子 widget 报告其首选大小
        preferred_size = getattr(widget, 'preferred_size', None)
        if preferred_size:
            size = constraints.enforce(preferred_size)
        else:
            size = constraints.enforce(Rect(0, 0, 100, 50))

        self._log(f"  Box布局: 约束={constraints}, 大小={size.width}x{size.height}")

        # 递归布局子元素
        children = getattr(widget, 'children', [])
        for child in children:
            child_constraints = BoxConstraints(0, size.width, 0, size.height)
            self._layout_node(child, child_constraints)

        return LayoutResult(size)

    def _layout_flex(self, widget: Any, constraints: BoxConstraints) -> LayoutResult:
        """弹性布局（Row/Column）"""
        direction = getattr(widget, 'direction', 'horizontal')
        children = getattr(widget, 'children', [])

        if not children:
            return LayoutResult(Rect(0, 0, 0, 0))

        # 计算主轴方向的大小
        total_main = 0
        for child in children:
            child_result = self._layout_node(child, BoxConstraints(0, float('inf'), 0, float('inf')))
            if direction == 'horizontal':
                total_main += child_result.size.width
            else:
                total_main += child_result.size.height

        if direction == 'horizontal':
            final_size = constraints.enforce(Rect(0, 0, total_main, constraints.max_height))
        else:
            final_size = constraints.enforce(Rect(0, 0, constraints.max_width, total_main))

        self._log(f"  Flex布局: 方向={direction}, 总大小={final_size.width}x{final_size.height}")

        return LayoutResult(final_size)

    def _layout_stack(self, widget: Any, constraints: BoxConstraints) -> LayoutResult:
        """层叠布局（Stack）"""
        children = getattr(widget, 'children', [])

        # Stack 的大小由父约束决定
        final_size = constraints.enforce(Rect(0, 0, constraints.max_width, constraints.max_height))

        # 所有子元素占据相同空间
        for child in children:
            self._layout_node(child, constraints)

        self._log(f"  Stack布局: 大小={final_size.width}x{final_size.height}")

        return LayoutResult(final_size)

    def _log(self, message: str):
        self._layout_log.append(message)

    @property
    def layout_log(self) -> List[str]:
        return self._layout_log

    @property
    def pass_count(self) -> int:
        return self._pass_count


# ============================================================
# 布局策略 (LayoutStrategy)
# ============================================================
class LayoutStrategy:
    """
    布局策略基类

    定义布局算法的接口。
    不同的布局 Widget 使用不同的策略。
    """

    def compute_layout(self, constraints: BoxConstraints) -> Rect:
        """计算布局大小"""
        raise NotImplementedError

    def get_child_constraints(self, constraints: BoxConstraints,
                              index: int) -> BoxConstraints:
        """为子元素计算约束"""
        return constraints

    def position_child(self, child_offset: Offset, child_size: Rect) -> Offset:
        """计算子元素的位置"""
        return child_offset


class BoxLayoutStrategy(LayoutStrategy):
    """盒模型布局策略"""

    def __init__(self, min_size: Optional[Rect] = None, max_size: Optional[Rect] = None):
        self._min_size = min_size
        self._max_size = max_size

    def compute_layout(self, constraints: BoxConstraints) -> Rect:
        min_w = self._min_size.width if self._min_size else 0
        min_h = self._min_size.height if self._min_size else 0
        max_w = self._max_size.width if self._max_size else constraints.max_width
        max_h = self._max_size.height if self._max_size else constraints.max_height
        return Rect(0, 0, max(min_w, min(max_w, 100)), max(min_h, min(max_h, 50)))


class FlexLayoutStrategy(LayoutStrategy):
    """弹性布局策略"""

    def __init__(self, direction: str = "horizontal",
                 main_axis_spacing: float = 0.0):
        self._direction = direction
        self._main_axis_spacing = main_axis_spacing

    def compute_layout(self, constraints: BoxConstraints) -> Rect:
        # 弹性布局的大小由子元素决定
        if self._direction == "horizontal":
            return Rect(0, 0, constraints.max_width, constraints.max_height)
        else:
            return Rect(0, 0, constraints.max_width, constraints.max_height)

    def get_child_constraints(self, constraints: BoxConstraints,
                              index: int) -> BoxConstraints:
        if self._direction == "horizontal":
            # Row: 宽度不限，高度受约束
            return BoxConstraints(0, constraints.max_width, 0, constraints.max_height)
        else:
            # Column: 宽度受约束，高度不限
            return BoxConstraints(0, constraints.max_width, 0, constraints.max_height)


class StackLayoutStrategy(LayoutStrategy):
    """层叠布局策略"""

    def compute_layout(self, constraints: BoxConstraints) -> Rect:
        # Stack 使用父约束作为最终大小
        return constraints.enforce(Rect(0, 0, constraints.max_width, constraints.max_height))

    def get_child_constraints(self, constraints: BoxConstraints,
                              index: int) -> BoxConstraints:
        # 所有子元素获得相同的约束
        return constraints


# ============================================================
# 布局调试工具
# ============================================================
class LayoutDebugger:
    """
    布局调试工具

    用于可视化布局树和约束传播。
    在 Flutter DevTools 中也有类似功能。
    """

    def __init__(self):
        self._tree: List[Dict[str, Any]] = []

    def record_layout(self, widget_name: str, constraints: BoxConstraints,
                      size: Rect, parent: Optional[str] = None):
        """记录一次布局操作"""
        self._tree.append({
            "widget": widget_name,
            "constraints": {
                "min_width": constraints.min_width,
                "max_width": constraints.max_width,
                "min_height": constraints.min_height,
                "max_height": constraints.max_height,
            },
            "size": size.to_dict(),
            "parent": parent,
        })

    def get_tree(self) -> List[Dict[str, Any]]:
        return self._tree

    def get_summary(self) -> Dict[str, Any]:
        """获取布局树摘要"""
        return {
            "total_widgets": len(self._tree),
            "widgets": [entry["widget"] for entry in self._tree],
        }

    def to_text(self, indent: int = 0) -> str:
        """以文本形式输出布局树"""
        lines = []
        prefix = "  " * indent
        for entry in self._tree:
            c = entry["constraints"]
            size = entry["size"]
            lines.append(
                f"{prefix}{entry['widget']}: "
                f"constraints=[{c['min_width']},{c['max_width']}]x[{c['min_height']},{c['max_height']}] "
                f"→ size={size['width']}x{size['height']}"
            )
        return "\n".join(lines)

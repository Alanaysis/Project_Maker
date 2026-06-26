"""
布局系统模拟 - Layout System Simulation

Android 的布局系统定义了 View 在屏幕上的排列方式。
布局类继承自 ViewGroup，负责测量和排列子 View。

The Android layout system defines how Views are arranged on screen.
Layout classes inherit from ViewGroup and are responsible for measuring
and arranging child Views.

主要布局类型：
- LinearLayout: 线性布局（水平或垂直排列）
- RelativeLayout: 相对布局（相对于兄弟 View 或父容器定位）
- ConstraintLayout: 约束布局（通过约束关系定位）
- FrameLayout: 帧布局（子 View 堆叠）
- GridLayout: 网格布局
"""

import logging
from typing import Optional, List, Dict, Any
from .view import View, ViewGroup, ViewDimensions

logger = logging.getLogger(__name__)


class LinearLayout(ViewGroup):
    """
    LinearLayout - 线性布局

    将子 View 按照水平或垂直方向依次排列。

    Arranges child Views in a single row (horizontal) or
    a single column (vertical).

    关键属性：
    - orientation: 排列方向 (horizontal, vertical)
    - gravity: 对齐方式
    - weightSum: 权重总和
    - layout_weight: 子 View 的权重（分配剩余空间）
    - padding: 内边距
    """

    def __init__(self, orientation: str = "vertical"):
        super().__init__("LinearLayout")
        self._layout_mode = "linear"
        self.orientation = orientation  # "horizontal" or "vertical"
        self.gravity: Optional[str] = None
        self.weight_sum: float = 0.0
        self.internal_padding: Dict[str, int] = {
            "left": 0, "right": 0, "top": 0, "bottom": 0
        }

    def set_orientation(self, orientation: str) -> "LinearLayout":
        self.orientation = orientation
        return self

    def set_weight_sum(self, weight_sum: float) -> "LinearLayout":
        self.weight_sum = weight_sum
        return self

    def measure(self, width_spec: int, height_spec: int) -> ViewDimensions:
        """
        测量 LinearLayout

        对于垂直布局：宽度取最大值，高度累加
        对于水平布局：高度取最大值，宽度累加
        """
        if self.orientation == "vertical":
            max_width = 0
            total_height = 0
            for child in self._children:
                if child.visibility == "gone":
                    continue
                child.measure(View.MATCH_PARENT, View.WRAP_CONTENT)
                max_width = max(max_width, child.dimensions.measured_width)
                total_height += child.dimensions.measured_height
            # 应用 padding
            max_width += self.internal_padding["left"] + self.internal_padding["right"]
            total_height += self.internal_padding["top"] + self.internal_padding["bottom"]
            self.dimensions.measured_width = max_width
            self.dimensions.measured_height = total_height
        else:
            total_width = 0
            max_height = 0
            for child in self._children:
                if child.visibility == "gone":
                    continue
                child.measure(View.WRAP_CONTENT, View.MATCH_PARENT)
                total_width += child.dimensions.measured_width
                max_height = max(max_height, child.dimensions.measured_height)
            total_width += self.internal_padding["left"] + self.internal_padding["right"]
            max_height += self.internal_padding["top"] + self.internal_padding["bottom"]
            self.dimensions.measured_width = total_width
            self.dimensions.measured_height = max_height

        self.dimensions.width = self.dimensions.measured_width
        self.dimensions.height = self.dimensions.measured_height
        return self.dimensions

    def layout_children(self, x_offset: int, y_offset: int) -> None:
        """
        布局 LinearLayout 的子 View

        按照 orientation 方向依次排布子 View。
        """
        if self.orientation == "vertical":
            current_y = y_offset + self.internal_padding["top"]
            for child in self._children:
                if child.visibility == "gone":
                    continue
                child_width = child.dimensions.measured_width
                child_height = child.dimensions.measured_height
                # 应用 gravity
                if self.gravity == "center":
                    child_x = x_offset + (self.dimensions.measured_width - child_width) // 2
                elif self.gravity == "right":
                    child_x = x_offset + self.dimensions.measured_width - child_width - self.internal_padding["right"]
                else:
                    child_x = x_offset + self.internal_padding["left"]
                child.layout(child_x, current_y, child_width, child_height)
                current_y += child_height + self.internal_padding["bottom"]
        else:
            current_x = x_offset + self.internal_padding["left"]
            for child in self._children:
                if child.visibility == "gone":
                    continue
                child_width = child.dimensions.measured_width
                child_height = child.dimensions.measured_height
                child.layout(current_x, y_offset, child_width, child_height)
                current_x += child_width + self.internal_padding["right"]


class RelativeLayout(ViewGroup):
    """
    RelativeLayout - 相对布局

    允许子 View 相对于其他兄弟 View 或父容器定位。

    Allows child Views to be positioned relative to each other
    or to the parent container.

    支持的相对定位规则：
    - above: 在指定 View 上方
    - below: 在指定 View 下方
    - left_of: 在指定 View 左侧
    - right_of: 在指定 View 右侧
    - align_parent_top: 对齐父容器顶部
    - align_parent_bottom: 对齐父容器底部
    - align_parent_left: 对齐父容器左侧
    - align_parent_right: 对齐父容器右侧
    - center_in_parent: 在父容器中居中
    """

    def __init__(self):
        super().__init__("RelativeLayout")
        self._constraints: Dict[int, Dict[str, Any]] = {}
        self._view_positions: Dict[int, ViewDimensions] = {}

    def add_constraint(self, view_id: int, rule: str, target_id: Optional[int] = None) -> "RelativeLayout":
        """添加约束规则"""
        if view_id not in self._constraints:
            self._constraints[view_id] = {}
        self._constraints[view_id][rule] = target_id
        return self

    def measure(self, width_spec: int, height_spec: int) -> ViewDimensions:
        """测量所有子 View"""
        for child in self._children:
            if child.visibility == "gone":
                continue
            child.measure(View.MATCH_PARENT, View.MATCH_PARENT)
        self.dimensions.measured_width = width_spec
        self.dimensions.measured_height = height_spec
        self.dimensions.width = width_spec
        self.dimensions.height = height_spec
        return self.dimensions

    def layout_children(self, x_offset: int, y_offset: int) -> None:
        """
        布局 RelativeLayout 的子 View

        根据约束规则计算每个子 View 的位置。
        """
        self._view_positions = {}

        # 首先布局有父容器对齐约束的 View
        for child in self._children:
            if child.visibility == "gone":
                continue
            constraints = self._constraints.get(child.id, {})

            x = x_offset
            y = y_offset

            if "align_parent_top" in constraints:
                y = y_offset
            elif "align_parent_bottom" in constraints:
                y = y_offset + self.dimensions.measured_height - child.dimensions.measured_height

            if "align_parent_left" in constraints:
                x = x_offset
            elif "align_parent_right" in constraints:
                x = x_offset + self.dimensions.measured_width - child.dimensions.measured_width

            if "center_in_parent" in constraints:
                x = x_offset + (self.dimensions.measured_width - child.dimensions.measured_width) // 2
                y = y_offset + (self.dimensions.measured_height - child.dimensions.measured_height) // 2

            # 处理相对兄弟 View 的约束
            for rule, target_id in constraints.items():
                if target_id is None:
                    continue
                target_pos = self._view_positions.get(target_id)
                if not target_pos:
                    continue

                if rule == "below":
                    y = target_pos.y + target_pos.height
                elif rule == "above":
                    y = target_pos.y - child.dimensions.measured_height
                elif rule == "left_of":
                    x = target_pos.x - child.dimensions.measured_width
                elif rule == "right_of":
                    x = target_pos.x + target_pos.width

            child.layout(x, y, child.dimensions.measured_width, child.dimensions.measured_height)
            self._view_positions[child.id] = child.dimensions


class ConstraintLayout(ViewGroup):
    """
    ConstraintLayout - 约束布局

    Android 推荐的现代布局方式，通过约束关系定位子 View。
    相比 RelativeLayout，性能更好，功能更强大。

    The modern layout recommended by Android. Positions children through
    constraints. Better performance than RelativeLayout with more features.

    约束类型：
    - start_toStartOf: 左边缘对齐
    - endToEndOf: 右边缘对齐
    - topToTopOf: 顶部对齐
    - bottomToBottomOf: 底部对齐
    - centerInParent: 在父容器中居中
    - margin: 边距
    """

    def __init__(self):
        super().__init__("ConstraintLayout")
        self._constraints: Dict[int, Dict[str, Any]] = {}
        self._margins: Dict[int, Dict[str, int]] = {}

    def add_constraint(self, view_id: int, rule: str, target_id: Optional[int] = None,
                       margin: int = 0) -> "ConstraintLayout":
        """添加约束"""
        if view_id not in self._constraints:
            self._constraints[view_id] = {}
        self._constraints[view_id][rule] = target_id
        if margin > 0:
            if view_id not in self._margins:
                self._margins[view_id] = {"left": 0, "right": 0, "top": 0, "bottom": 0}
            self._margins[view_id]["left"] = margin
        return self

    def measure(self, width_spec: int, height_spec: int) -> ViewDimensions:
        for child in self._children:
            if child.visibility == "gone":
                continue
            child.measure(View.MATCH_PARENT, View.MATCH_PARENT)
        self.dimensions.measured_width = width_spec
        self.dimensions.measured_height = height_spec
        self.dimensions.width = width_spec
        self.dimensions.height = height_spec
        return self.dimensions

    def layout_children(self, x_offset: int, y_offset: int) -> None:
        """布局 ConstraintLayout 的子 View"""
        view_positions: Dict[int, ViewDimensions] = {}

        for child in self._children:
            if child.visibility == "gone":
                continue
            constraints = self._constraints.get(child.id, {})
            margins = self._margins.get(child.id, {"left": 0, "right": 0, "top": 0, "bottom": 0})

            x = x_offset + margins["left"]
            y = y_offset + margins["top"]

            for rule, target_id in constraints.items():
                if rule == "center_in_parent":
                    x = x_offset + (self.dimensions.measured_width - child.dimensions.measured_width) // 2
                    y = y_offset + (self.dimensions.measured_height - child.dimensions.measured_height) // 2
                elif rule == "align_parent_left":
                    x = x_offset
                elif rule == "align_parent_top":
                    y = y_offset
                elif rule == "align_parent_right":
                    x = x_offset + self.dimensions.measured_width - child.dimensions.measured_width
                elif rule == "align_parent_bottom":
                    y = y_offset + self.dimensions.measured_height - child.dimensions.measured_height
                elif target_id is not None and target_id in view_positions:
                    target = view_positions[target_id]
                    if rule == "start_toStartOf":
                        x = target.x
                    elif rule == "endToEndOf":
                        x = target.x + target.width - child.dimensions.measured_width
                    elif rule == "topToTopOf":
                        y = target.y
                    elif rule == "bottomToBottomOf":
                        y = target.y + target.height - child.dimensions.measured_height
                    elif rule == "left_toRightOf":
                        x = target.x + target.width + margins["left"]
                    elif rule == "top_toBottomOf":
                        y = target.y + target.height + margins["top"]

            child.layout(x, y, child.dimensions.measured_width, child.dimensions.measured_height)
            view_positions[child.id] = child.dimensions


class FrameLayout(ViewGroup):
    """
    FrameLayout - 帧布局

    最简单的布局类型，所有子 View 都堆叠在左上角。
    通常用于单个子 View 或需要重叠的场景。

    The simplest layout type. All child Views are stacked in the top-left corner.
    Typically used for a single child or overlapping views.
    """

    def __init__(self):
        super().__init__("FrameLayout")

    def measure(self, width_spec: int, height_spec: int) -> ViewDimensions:
        max_width = 0
        max_height = 0
        for child in self._children:
            if child.visibility == "gone":
                continue
            child.measure(View.MATCH_PARENT, View.MATCH_PARENT)
            max_width = max(max_width, child.dimensions.measured_width)
            max_height = max(max_height, child.dimensions.measured_height)
        self.dimensions.measured_width = max_width if max_width > 0 else width_spec
        self.dimensions.measured_height = max_height if max_height > 0 else height_spec
        self.dimensions.width = self.dimensions.measured_width
        self.dimensions.height = self.dimensions.measured_height
        return self.dimensions

    def layout_children(self, x_offset: int, y_offset: int) -> None:
        for child in self._children:
            if child.visibility == "gone":
                continue
            child.layout(x_offset, y_offset,
                         child.dimensions.measured_width,
                         child.dimensions.measured_height)


class GridLayout(ViewGroup):
    """
    GridLayout - 网格布局

    将子 View 排列在行和列组成的网格中。

    Arranges child Views in a grid of rows and columns.
    """

    def __init__(self, rows: int = 1, cols: int = 1):
        super().__init__("GridLayout")
        self.rows = rows
        self.cols = cols

    def measure(self, width_spec: int, height_spec: int) -> ViewDimensions:
        for child in self._children:
            if child.visibility == "gone":
                continue
            child.measure(View.MATCH_PARENT, View.MATCH_PARENT)
        self.dimensions.measured_width = width_spec
        self.dimensions.measured_height = height_spec
        self.dimensions.width = width_spec
        self.dimensions.height = height_spec
        return self.dimensions

    def layout_children(self, x_offset: int, y_offset: int) -> None:
        cell_width = self.dimensions.measured_width // self.cols
        cell_height = self.dimensions.measured_height // self.rows

        for index, child in enumerate(self._children):
            if child.visibility == "gone":
                continue
            row = index // self.cols
            col = index % self.cols
            x = x_offset + col * cell_width
            y = y_offset + row * cell_height
            child.layout(x, y, cell_width, cell_height)


def create_linear_layout(orientation: str = "vertical") -> LinearLayout:
    """创建 LinearLayout 的工厂函数"""
    return LinearLayout(orientation)


def create_relative_layout() -> RelativeLayout:
    """创建 RelativeLayout 的工厂函数"""
    return RelativeLayout()


def create_constraint_layout() -> ConstraintLayout:
    """创建 ConstraintLayout 的工厂函数"""
    return ConstraintLayout()


def create_frame_layout() -> FrameLayout:
    """创建 FrameLayout 的工厂函数"""
    return FrameLayout()


def create_grid_layout(rows: int = 1, cols: int = 1) -> GridLayout:
    """创建 GridLayout 的工厂函数"""
    return GridLayout(rows, cols)


def measure_and_layout(root: ViewGroup) -> Dict[str, Any]:
    """
    对根 View 执行测量和布局

    模拟 Android 的 measure -> layout 流程。

    Simulates Android's measure -> layout flow.

    Returns:
        布局结果信息
    """
    # 测量
    root.measure(800, 1200)
    # 布局
    root.layout_children(0, 0)

    # 收集所有 View 的位置信息
    positions = collect_positions(root)

    # 绘制
    draws = []
    if hasattr(root, 'draw'):
        draws.append(root.draw())
    if hasattr(root, 'draw_children'):
        draws.extend(root.draw_children())

    return {
        "root": root,
        "measurements": root.dimensions,
        "positions": positions,
        "draws": draws,
    }


def collect_positions(view: View, depth: int = 0) -> List[Dict[str, Any]]:
    """递归收集所有 View 的位置信息"""
    result = [{
        "id": view.id,
        "type": view.view_type,
        "x": view.dimensions.x,
        "y": view.dimensions.y,
        "width": view.dimensions.width,
        "height": view.dimensions.height,
        "depth": depth,
    }]
    if hasattr(view, '_children'):
        for child in view._children:
            result.extend(collect_positions(child, depth + 1))
    return result

"""
布局容器 - Layout Containers

鸿蒙 ArkUI 提供多种布局容器：

1. Column (垂直布局): 子组件垂直排列
2. Row (水平布局): 子组件水平排列
3. Stack (堆栈布局): 子组件层叠排列
4. Flex (弹性布局): 类似 CSS Flexbox
5. Grid (网格布局): 行列网格排列
6. RelativeContainer (相对布局): 相对定位

ArkTS 示例：
```
Column() {
  Text('First')
  Text('Second')
}
.width('100%')
.height('100%')
.gap(10)
.justifyContent(FlexAlign.Start)

Stack() {
  Image('background')
  Text('Overlay')
}
```
"""

from typing import Any, Dict, List, Optional
from .base import BaseComponent


class Column(BaseComponent):
    """
    垂直布局容器 - 模拟 ArkUI 的 Column 组件

    子组件垂直排列，支持：
    - 主轴对齐 (垂直方向)
    - 交叉轴对齐 (水平方向)
    - 子组件间距
    - 子组件拉伸
    """

    ALIGN_ITEMS = ['Start', 'Center', 'End', 'Stretch']
    JUSTIFY_CONTENT = ['Start', 'Center', 'End', 'SpaceBetween', 'SpaceAround', 'SpaceEvenly']

    def __init__(self, parent=None):
        super().__init__(name='Column', parent=parent)
        self.layout_config = {
            'gap': 0,              # 子组件间距
            'alignItems': 'Start',  # 交叉轴对齐
            'justifyContent': 'Start',  # 主轴对齐
            'width': None,
            'height': None,
        }

    def gap(self, gap: float) -> 'Column':
        """设置子组件间距（单位：vp）"""
        self.layout_config['gap'] = gap
        return self

    def align_items(self, align: str) -> 'Column':
        """设置交叉轴对齐方式"""
        if align in self.ALIGN_ITEMS:
            self.layout_config['alignItems'] = align
        return self

    def justify_content(self, justify: str) -> 'Column':
        """设置主轴对齐方式"""
        if justify in self.JUSTIFY_CONTENT:
            self.layout_config['justifyContent'] = justify
        return self

    def measure(self) -> Dict[str, float]:
        """测量容器尺寸"""
        total_height = 0
        max_width = 0
        for i, child in enumerate(self.children):
            child.measure()
            total_height += child.measured_height
            if i > 0:
                total_height += self.layout_config['gap']
            max_width = max(max_width, child.measured_width)

        self.measured_width = self.layout_config['width'] or max_width
        self.measured_height = self.layout_config['height'] or total_height
        return {'width': self.measured_width, 'height': self.measured_height}

    def render(self, depth: int = 0) -> str:
        indent = '  ' * depth
        lines = [f'{indent}[Column] gap={self.layout_config["gap"]} align={self.layout_config["alignItems"]}']
        lines.append(f'{indent}  justify={self.layout_config["justifyContent"]} children={len(self.children)}')
        return '\n'.join(lines)


class Row(BaseComponent):
    """
    水平布局容器 - 模拟 ArkUI 的 Row 组件

    子组件水平排列，支持：
    - 主轴对齐 (水平方向)
    - 交叉轴对齐 (垂直方向)
    - 子组件间距
    - 子组件拉伸
    """

    ALIGN_ITEMS = ['Start', 'Center', 'End', 'Stretch']
    JUSTIFY_CONTENT = ['Start', 'Center', 'End', 'SpaceBetween', 'SpaceAround', 'SpaceEvenly']

    def __init__(self, parent=None):
        super().__init__(name='Row', parent=parent)
        self.layout_config = {
            'gap': 0,
            'alignItems': 'Center',
            'justifyContent': 'Start',
            'width': None,
            'height': None,
        }

    def gap(self, gap: float) -> 'Row':
        """设置子组件间距"""
        self.layout_config['gap'] = gap
        return self

    def align_items(self, align: str) -> 'Row':
        """设置交叉轴对齐方式"""
        if align in self.ALIGN_ITEMS:
            self.layout_config['alignItems'] = align
        return self

    def justify_content(self, justify: str) -> 'Row':
        """设置主轴对齐方式"""
        if justify in self.JUSTIFY_CONTENT:
            self.layout_config['justifyContent'] = justify
        return self

    def measure(self) -> Dict[str, float]:
        """测量容器尺寸"""
        total_width = 0
        max_height = 0
        for i, child in enumerate(self.children):
            child.measure()
            total_width += child.measured_width
            if i > 0:
                total_width += self.layout_config['gap']
            max_height = max(max_height, child.measured_height)

        self.measured_width = self.layout_config['width'] or total_width
        self.measured_height = self.layout_config['height'] or max_height
        return {'width': self.measured_width, 'height': self.measured_height}

    def render(self, depth: int = 0) -> str:
        indent = '  ' * depth
        lines = [f'{indent}[Row] gap={self.layout_config["gap"]} align={self.layout_config["alignItems"]}']
        lines.append(f'{indent}  justify={self.layout_config["justifyContent"]} children={len(self.children)}')
        return '\n'.join(lines)


class Stack(BaseComponent):
    """
    堆栈布局容器 - 模拟 ArkUI 的 Stack 组件

    子组件层叠排列，先添加的在后，后添加的在前。
    类似 CSS 的 position: relative/absolute。

    鸿蒙 Stack 特性：
    1. 子组件按添加顺序层叠
    2. 支持对齐方式
    3. 支持溢出处理
    """

    ALIGN_ITEMS = ['Start', 'Center', 'End']

    def __init__(self, parent=None):
        super().__init__(name='Stack', parent=parent)
        self.layout_config = {
            'alignItems': 'Start',
            'justification': 'Start',
            'width': None,
            'height': None,
        }

    def align_items(self, align: str) -> 'Stack':
        """设置对齐方式"""
        if align in self.ALIGN_ITEMS:
            self.layout_config['alignItems'] = align
        return self

    def measure(self) -> Dict[str, float]:
        """测量容器尺寸（取所有子组件的最大尺寸）"""
        max_width = 0
        max_height = 0
        for child in self.children:
            child.measure()
            max_width = max(max_width, child.measured_width)
            max_height = max(max_height, child.measured_height)

        self.measured_width = self.layout_config['width'] or max_width
        self.measured_height = self.layout_config['height'] or max_height
        return {'width': self.measured_width, 'height': self.measured_height}

    def render(self, depth: int = 0) -> str:
        indent = '  ' * depth
        lines = [f'{indent}[Stack] align={self.layout_config["alignItems"]} children={len(self.children)}']
        return '\n'.join(lines)


class Flex(BaseComponent):
    """
    弹性布局容器 - 模拟 ArkUI 的 Flex 组件

    类似 CSS Flexbox，支持：
    - 排列方向 (row/column)
    - 主轴对齐
    - 交叉轴对齐
    - 换行
    - 子组件 flex 增长/收缩
    """

    DIRECTION = ['Row', 'Column']
    ALIGN_ITEMS = ['Start', 'Center', 'End', 'Stretch']
    JUSTIFY_CONTENT = ['Start', 'Center', 'End', 'SpaceBetween', 'SpaceAround', 'SpaceEvenly']
    WRAP = ['NoWrap', 'Wrap']

    def __init__(self, direction: str = 'Row', parent=None):
        super().__init__(name='Flex', parent=parent)
        self.layout_config = {
            'direction': direction,
            'alignItems': 'Stretch',
            'justifyContent': 'Start',
            'flexWrap': 'NoWrap',
            'width': None,
            'height': None,
        }
        self._flex_grow: List[float] = []
        self._flex_shrink: List[float] = []

    def flex_direction(self, direction: str) -> 'Flex':
        """设置排列方向"""
        if direction in self.DIRECTION:
            self.layout_config['direction'] = direction
        return self

    def flex_wrap(self, wrap: str) -> 'Flex':
        """设置换行"""
        if wrap in self.WRAP:
            self.layout_config['flexWrap'] = wrap
        return self

    def flex_grow(self, child_index: int, grow: float) -> 'Flex':
        """设置子组件的 flex-grow"""
        while len(self._flex_grow) <= child_index:
            self._flex_grow.append(0)
        self._flex_grow[child_index] = grow
        return self

    def flex_shrink(self, child_index: int, shrink: float) -> 'Flex':
        """设置子组件的 flex-shrink"""
        while len(self._flex_shrink) <= child_index:
            self._flex_shrink.append(1)
        self._flex_shrink[child_index] = shrink
        return self

    def align_items(self, align: str) -> 'Flex':
        if align in self.ALIGN_ITEMS:
            self.layout_config['alignItems'] = align
        return self

    def justify_content(self, justify: str) -> 'Flex':
        if justify in self.JUSTIFY_CONTENT:
            self.layout_config['justifyContent'] = justify
        return self

    def measure(self) -> Dict[str, float]:
        for child in self.children:
            child.measure()

        direction = self.layout_config['direction']
        if direction == 'Column':
            total_height = sum(c.measured_height for c in self.children)
            max_width = max((c.measured_width for c in self.children), default=0)
            self.measured_width = self.layout_config['width'] or max_width
            self.measured_height = self.layout_config['height'] or total_height
        else:
            total_width = sum(c.measured_width for c in self.children)
            max_height = max((c.measured_height for c in self.children), default=0)
            self.measured_width = self.layout_config['width'] or total_width
            self.measured_height = self.layout_config['height'] or max_height

        return {'width': self.measured_width, 'height': self.measured_height}

    def render(self, depth: int = 0) -> str:
        indent = '  ' * depth
        lines = [f'{indent}[Flex] direction={self.layout_config["direction"]} wrap={self.layout_config["flexWrap"]}']
        lines.append(f'{indent}  align={self.layout_config["alignItems"]} justify={self.layout_config["justifyContent"]}')
        return '\n'.join(lines)


class Grid(BaseComponent):
    """
    网格布局容器 - 模拟 ArkUI 的 Grid 组件

    支持行列网格排列：
    - 固定列数
    - 列宽配置
    - 行高配置
    - 网格间距
    """

    def __init__(self, columns: int = 3, parent=None):
        super().__init__(name='Grid', parent=parent)
        self.layout_config = {
            'columns': columns,
            'columnWidth': None,
            'rowHeight': None,
            'gap': {'row': 0, 'column': 0},
            'width': None,
            'height': None,
        }

    def grid_columns(self, count: int) -> 'Grid':
        """设置列数"""
        self.layout_config['columns'] = count
        return self

    def grid_gap(self, row: float = 0, column: float = 0) -> 'Grid':
        """设置网格间距"""
        self.layout_config['gap'] = {'row': row, 'column': column}
        return self

    def measure(self) -> Dict[str, float]:
        cols = self.layout_config['columns']
        if cols == 0 or len(self.children) == 0:
            self.measured_width = self.layout_config['width'] or 0
            self.measured_height = self.layout_config['height'] or 0
            return {'width': self.measured_width, 'height': self.measured_height}

        rows = (len(self.children) + cols - 1) // cols
        max_child_width = max((c.measured_width for c in self.children), default=0)
        max_child_height = max((c.measured_height for c in self.children), default=0)

        total_width = max_child_width * cols + self.layout_config['gap']['column'] * (cols - 1)
        total_height = max_child_height * rows + self.layout_config['gap']['row'] * (rows - 1)

        self.measured_width = self.layout_config['width'] or total_width
        self.measured_height = self.layout_config['height'] or total_height
        return {'width': self.measured_width, 'height': self.measured_height}

    def render(self, depth: int = 0) -> str:
        indent = '  ' * depth
        lines = [f'{indent}[Grid] columns={self.layout_config["columns"]} children={len(self.children)}']
        return '\n'.join(lines)

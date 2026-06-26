"""
跨平台框架原理 - Cross-Platform Framework Principles

核心模块：Widget 树构建器
功能：模拟 Flutter Widget 树的构建和元素树（Element Tree）的生成

跨平台框架原理说明：
Flutter 的 UI 由 Widget 树定义。Widget 是不可变的配置描述，不是实际的 UI 元素。
Widget 树通过 Element 树转换为 Render 对象树（可渲染的）。

Widget Tree → Element Tree → Render Tree

Widget 的三大类型：
1. StatelessWidget - 无状态 Widget
2. StatefulWidget - 有状态 Widget（可更新）
3. RenderObjectWidget - 自定义渲染 Widget

本模块模拟：
1. Widget 定义和组合
2. Element 树构建
3. Render 对象生成
4. Widget 生命周期
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Type, Union
from .rendering_engine import Color, Colors, Rect, Offset, Paint, FillStyle


# ============================================================
# Widget 基类
# ============================================================
class WidgetType(Enum):
    """Widget 类型"""
    STATELESS = "stateless"
    STATEFUL = "stateful"


class Widget:
    """
    Widget 基类

    Widget 是 Flutter UI 的构建块。
    在 Flutter 中，Widget 是：
    - 不可变的（immutable）
    - 轻量级（lightweight）
    - 描述性的（descriptive）

    当 Widget 树变化时，Flutter 会：
    1. 构建新的 Widget 树
    2. 与旧树对比（diff）
    3. 更新 Element 树
    4. 重建 Render 树
    5. 执行绘制
    """

    def __init__(self, key: Optional[str] = None):
        self._key = key
        self._widget_type: WidgetType = WidgetType.STATELESS
        self._children: List['Widget'] = []
        self._element: Optional['Element'] = None
        self._render_object: Optional['RenderObject'] = None

    @property
    def key(self) -> Optional[str]:
        return self._key

    @property
    def widget_type(self) -> WidgetType:
        return self._widget_type

    @property
    def children(self) -> List['Widget']:
        return self._children

    def append_child(self, child: 'Widget'):
        """添加子 Widget"""
        self._children.append(child)

    def build(self) -> 'Element':
        """
        构建 Element 树

        Element 是 Widget 和 Render 对象之间的桥梁。
        每个 Widget 对应一个 Element。
        """
        if self._element is None:
            self._element = self._create_element()
        self._element.mount(parent=None)
        return self._element

    def _create_element(self) -> 'Element':
        """创建对应的 Element"""
        if self._widget_type == WidgetType.STATELESS:
            return StatelessElement(self)
        else:
            return StatefulElement(self)

    def to_dict(self) -> Dict[str, Any]:
        """序列化 Widget"""
        return {
            "type": self._widget_type.value,
            "key": self._key,
            "children": len(self._children),
        }

    def __repr__(self):
        return f"Widget(type={self._widget_type.value}, key={self._key})"


class StatelessWidget(Widget):
    """
    StatelessWidget - 无状态 Widget

    用于 UI 不随时间变化的场景。
    例如：Text, Icon, Image, Container（无状态部分）

    特点：
    - 不可变配置
    - 每次构建返回相同结构
    """

    def __init__(self, key: Optional[str] = None, **kwargs):
        super().__init__(key)
        self._widget_type = WidgetType.STATELESS
        self._props = kwargs


class Element:
    """
    Element - Widget 和 Render 对象之间的桥梁

    Element 树是 Flutter 渲染的核心：
    1. 每个 Widget 对应一个 Element
    2. Element 管理对应的 Render 对象
    3. Element 负责处理 Widget 更新和 Render 对象复用

    关键方法：
    - mount(): 挂载 Element
    - update(): 更新 Widget 配置
    - unmount(): 卸载 Element
    """

    def __init__(self, widget: Widget):
        self._widget = widget
        self._parent: Optional['Element'] = None
        self._children: List['Element'] = []
        self._render_object: Optional['RenderObject'] = None
        self._mounted = False
        self._debug_name = widget.__class__.__name__ or type(widget).__name__

    @property
    def widget(self) -> Widget:
        return self._widget

    @property
    def parent(self) -> Optional['Element']:
        return self._parent

    @property
    def children(self) -> List['Element']:
        return self._children

    @property
    def render_object(self) -> Optional['RenderObject']:
        return self._render_object

    @property
    def is_mounted(self) -> bool:
        return self._mounted

    def mount(self, parent: Optional['Element'] = None):
        """挂载 Element"""
        self._parent = parent
        self._mounted = True

        # 递归挂载子 Element
        for child_widget in self._widget.children:
            child_element = child_widget._create_element()
            child_element.mount(parent=self)
            self._children.append(child_element)

        # 创建 Render 对象
        self._render_object = self._build_render_object()
        self._render_object.mount()

    def _build_render_object(self) -> 'RenderObject':
        """构建 Render 对象"""
        widget_type = self._widget.widget_type
        if widget_type == WidgetType.STATELESS:
            return RenderBox(self._widget)
        else:
            return RenderBox(self._widget)

    def update(self, new_widget: Widget):
        """更新 Widget 配置"""
        self._widget = new_widget
        # 递归更新子 Element
        for i, child_widget in enumerate(new_widget.children):
            if i < len(self._children):
                self._children[i].update(child_widget)
            else:
                child_element = child_widget._create_element()
                child_element.mount(parent=self)
                self._children.append(child_element)

    def unmount(self):
        """卸载 Element"""
        self._mounted = False
        for child in self._children:
            child.unmount()
        self._children.clear()
        if self._render_object:
            self._render_object.unmount()

    def get_descendants(self) -> List['Element']:
        """获取所有后代 Element"""
        descendants = []
        for child in self._children:
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants

    def to_dict(self, depth: int = 0) -> Dict[str, Any]:
        """序列化 Element 树"""
        result = {
            "type": self._debug_name,
            "mounted": self._mounted,
            "render_object": self._render_object.to_dict() if self._render_object else None,
            "children": [],
        }
        for child in self._children:
            result["children"].append(child.to_dict(depth + 1))
        return result

    def __repr__(self):
        return f"Element({self._debug_name}, mounted={self._mounted})"


class StatefulElement(Element):
    """StatefulElement 管理有状态 Widget 的生命周期"""

    def __init__(self, widget: Widget):
        super().__init__(widget)
        self._state: Optional[Dict[str, Any]] = {}
        self._dirty = False

    @property
    def state(self) -> Dict[str, Any]:
        return self._state

    @property
    def is_dirty(self) -> bool:
        return self._dirty

    def set_state(self, updates: Dict[str, Any]):
        """更新状态并标记为脏（需要重建）"""
        self._state.update(updates)
        self._dirty = True

    def clear_dirty(self):
        """清除脏标记"""
        self._dirty = False

    def rebuild(self) -> 'RenderObject':
        """重建 Render 对象"""
        self.clear_dirty()
        render_obj = self._build_render_object()
        self._render_object = render_obj
        return render_obj


class StatelessElement(Element):
    """StatelessElement 管理无状态 Widget 的生命周期"""

    def __init__(self, widget: Widget):
        super().__init__(widget)
        self._dirty = False

    @property
    def is_dirty(self) -> bool:
        return self._dirty

    def clear_dirty(self):
        self._dirty = False

    def rebuild(self) -> 'RenderObject':
        self.clear_dirty()
        render_obj = self._build_render_object()
        self._render_object = render_obj
        return render_obj


# ============================================================
# Render 对象
# ============================================================
class RenderObjectType(Enum):
    """Render 对象类型"""
    BOX = "box"           # 盒模型（矩形）
    FLEX = "flex"         # 弹性布局
    STACK = "stack"       # 层叠布局
    CUSTOM = "custom"     # 自定义渲染


class RenderObject:
    """
    RenderObject - 可渲染对象

    RenderObject 是实际负责布局、绘制和命中测试的对象。
    在 Flutter 中，RenderObject 树是渲染的中间表示。

    RenderObject 的主要职责：
    1. 布局（Layout）- 确定大小和位置
    2. 绘制（Paint）- 执行 Canvas 绘制命令
    3. 命中测试（Hit testing）- 处理触摸事件
    """

    def __init__(self, render_type: RenderObjectType = RenderObjectType.BOX):
        self._type = render_type
        self._size: Optional[Rect] = None
        self._parent: Optional['RenderObject'] = None
        self._children: List['RenderObject'] = []
        self._mounted = False

    @property
    def type(self) -> RenderObjectType:
        return self._type

    @property
    def size(self) -> Optional[Rect]:
        return self._size

    @property
    def children(self) -> List['RenderObject']:
        return self._children

    def mount(self):
        self._mounted = True

    def unmount(self):
        self._mounted = False

    def layout(self, constraints: Rect):
        """执行布局计算"""
        self._size = constraints

    def paint(self, canvas: 'Canvas') -> List[Dict[str, Any]]:
        """执行绘制"""
        return []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self._type.value,
            "size": self._size.to_dict() if self._size else None,
            "mounted": self._mounted,
            "children": len(self._children),
        }

    def __repr__(self):
        return f"RenderObject(type={self._type.value})"


class RenderBox(RenderObject):
    """
    RenderBox - 盒模型渲染对象

    RenderBox 是最常用的 RenderObject 类型。
    它处理矩形区域的布局、绘制和命中测试。

    大多数 Flutter 内置 Widget 都使用 RenderBox：
    - Container → RenderBox
    - Text → RenderParagraph（也是 RenderBox 的子类）
    - Row/Column → RenderFlex（也是 RenderBox 的子类）
    """

    def __init__(self, widget: Optional[Widget] = None):
        super().__init__(RenderObjectType.BOX)
        self._widget = widget
        self._alignment = Offset(0, 0)
        self._padding: Optional[Rect] = None
        self._color: Optional[Color] = None
        self._margin: Optional[Rect] = None

    @property
    def widget(self) -> Optional[Widget]:
        return self._widget

    @property
    def alignment(self) -> Offset:
        return self._alignment

    @alignment.setter
    def alignment(self, value: Offset):
        self._alignment = value

    @property
    def padding(self) -> Optional[Rect]:
        return self._padding

    @padding.setter
    def padding(self, value: Optional[Rect]):
        self._padding = value

    @property
    def color(self) -> Optional[Color]:
        return self._color

    @color.setter
    def color(self, value: Optional[Color]):
        self._color = value

    @property
    def margin(self) -> Optional[Rect]:
        return self._margin

    @margin.setter
    def margin(self, value: Optional[Rect]):
        self._margin = value

    def layout(self, constraints: Rect):
        """
        执行盒模型布局

        布局约束（Constraints）：
        - minWidth / maxWidth
        - minHeight / maxHeight

        布局过程：
        1. 父 Widget 传递约束给子 Widget
        2. 子 Widget 根据自身内容确定大小
        3. 最终确定布局
        """
        # 应用边距
        if self._margin:
            inner = constraints
        else:
            inner = constraints

        # 应用内边距
        if self._padding:
            inner = Rect(
                inner.left + self._padding.left,
                inner.top + self._padding.top,
                inner.right - self._padding.right,
                inner.bottom - self._padding.bottom,
            )

        self._size = inner

        # 递归布局子 RenderObject
        for child in self._children:
            child.layout(inner)

    def paint(self, canvas: 'Canvas') -> List[Dict[str, Any]]:
        """执行盒模型绘制"""
        commands = []

        if self._size and self._color:
            paint = Paint()
            paint.color = self._color
            paint.fill_style = FillStyle.FILL
            canvas.draw_rect(self._size, paint)
            commands.append({"type": "rect", "color": self._color.to_hex()})

        # 递归绘制子 RenderObject
        for child in self._children:
            commands.extend(child.paint(canvas))

        return commands

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            "alignment": self._alignment.dx,
            "padding": self._padding.to_dict() if self._padding else None,
            "color": self._color.to_hex() if self._color else None,
            "margin": self._margin.to_dict() if self._margin else None,
        })
        return result


class RenderStack(RenderObject):
    """
    RenderStack - 层叠布局渲染对象

    对应 Flutter 的 Stack Widget。
    子 Widget 按顺序层叠，后面的覆盖前面的。
    """

    def __init__(self):
        super().__init__(RenderObjectType.STACK)

    def layout(self, constraints: Rect):
        """层叠布局：所有子元素占据相同空间"""
        self._size = constraints
        for child in self._children:
            child.layout(constraints)

    def paint(self, canvas: 'Canvas') -> List[Dict[str, Any]]:
        """层叠绘制：按顺序绘制每个子元素"""
        commands = []
        for child in self._children:
            commands.extend(child.paint(canvas))
        return commands


class RenderFlex(RenderObject):
    """
    RenderFlex - 弹性布局渲染对象

    对应 Flutter 的 Row/Column Widget。
    子元素沿主轴方向排列。
    """

    def __init__(self, direction: str = "horizontal"):
        super().__init__(RenderObjectType.FLEX)
        self._direction = direction  # "horizontal" or "vertical"
        self._main_axis_spacing = 0.0
        self._cross_axis_alignment = 0.5  # 0.0 = start, 0.5 = center, 1.0 = end

    @property
    def direction(self) -> str:
        return self._direction

    def layout(self, constraints: Rect):
        """弹性布局计算"""
        self._size = constraints

        if self._direction == "horizontal":
            total_width = constraints.width
            x = constraints.left
            for child in self._children:
                child_width = min(total_width, child._size.width if child._size else 100)
                child.layout(Rect(x, constraints.top, x + child_width, constraints.bottom))
                x += child_width + self._main_axis_spacing
        else:
            total_height = constraints.height
            y = constraints.top
            for child in self._children:
                child_height = min(total_height, child._size.height if child._size else 50)
                child.layout(Rect(constraints.left, y, constraints.right, y + child_height))
                y += child_height + self._main_axis_spacing

    def paint(self, canvas: 'Canvas') -> List[Dict[str, Any]]:
        commands = []
        for child in self._children:
            commands.extend(child.paint(canvas))
        return commands

"""
Jetpack Compose 概念模拟 - Jetpack Compose Concepts Simulation

Jetpack Compose 是 Android 的现代声明式 UI 工具包。
它使用 Kotlin 函数（@Composable）来描述 UI，而不是 XML 布局文件。

Jetpack Compose is Android's modern declarative UI toolkit.
It uses Kotlin functions (@Composable) to describe UI instead of XML layouts.

核心概念：
1. 声明式 UI - 描述 "是什么" 而非 "怎么做"
2. Composable 函数 - 标记为 @Composable 的函数
3. 状态管理 - State, MutableState, StateFlow
4. 布局原语 - Row, Column, Box
5. 重组 (Recomposition) - 状态变化时自动更新 UI

Key Concepts:
1. Declarative UI - Describe "what" not "how"
2. Composable functions - Functions marked with @Composable
3. State management - State, MutableState, StateFlow
4. Layout primitives - Row, Column, Box
5. Recomposition - UI auto-updates on state changes
"""

import logging
import time
from enum import Enum
from typing import Optional, Dict, Any, List, Callable, TypeVar, Generic
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class LayoutDirection(Enum):
    """布局方向"""
    LTR = "ltr"   # 从左到右
    RTL = "rtl"   # 从右到左


class MeasurePolicy:
    """测量策略"""
    def measure(self, constraints: Dict[str, int]) -> Dict[str, int]:
        return constraints


@dataclass
class BoxConstraints:
    """
    BoxConstraints - 测量约束

    定义 View 的最小和最大宽高。

    Defines minimum and maximum width/height for a View.
    """
    min_width: int = 0
    max_width: int = 800
    min_height: int = 0
    max_height: int = 1200

    def at_least(self, min_width: int = 0, min_height: int = 0) -> "BoxConstraints":
        """设置最小约束"""
        return BoxConstraints(
            min_width=max(self.min_width, min_width),
            max_width=self.max_width,
            min_height=max(self.min_height, min_height),
            max_height=self.max_height,
        )

    def fixed(self, width: int, height: int) -> "BoxConstraints":
        """设置固定约束"""
        return BoxConstraints(
            min_width=width, max_width=width,
            min_height=height, max_height=height,
        )

    def wrap_content(self) -> "BoxConstraints":
        """设置为包裹内容"""
        return BoxConstraints(
            min_width=0, max_width=800,
            min_height=0, max_height=1200,
        )


class ComposableFunction:
    """
    Composable 函数 - 模拟 @Composable 标记的函数

    Composable 函数是 Jetpack Compose 的构建块。
    当状态变化时，Compose 会自动重组（recompose）受影响的 Composable。

    Composable functions are the building blocks of Jetpack Compose.
    When state changes, Compose automatically recomposes affected composables.
    """

    def __init__(self, name: str, func: Callable, dependencies: List[str] = None):
        self.name = name
        self.func = func
        self.dependencies = dependencies or []
        self._call_count = 0
        self._last_recompose_time: Optional[float] = None
        self._recompose_log: List[float] = []

    def __call__(self, *args, **kwargs) -> Any:
        self._call_count += 1
        self._last_recompose_time = time.time()
        self._recompose_log.append(self._last_recompose_time)
        logger.debug(f"Composable '{self.name}' called (#{self._call_count})")
        return self.func(*args, **kwargs)

    @property
    def call_count(self) -> int:
        return self._call_count

    def __str__(self) -> str:
        return f"Composable({self.name}, calls={self._call_count})"


class StateManager:
    """
    状态管理器 - State Manager

    Jetpack Compose 的核心是状态管理。
    状态变化会触发重组（recomposition），自动更新 UI。

    The core of Jetpack Compose is state management.
    State changes trigger recomposition, automatically updating the UI.
    """

    def __init__(self, name: str = "state"):
        self.name = name
        self._value: Any = None
        self._observers: List[Callable] = []
        self._version = 0

    @property
    def value(self) -> Any:
        return self._value

    @value.setter
    def value(self, new_value: Any) -> None:
        if self._value != new_value:
            old_value = self._value
            self._value = new_value
            self._version += 1
            logger.debug(f"State '{self.name}' changed: {old_value} -> {new_value} "
                         f"(version={self._version})")
            # 通知所有观察者
            for observer in self._observers:
                observer(new_value)

    def observe(self, observer: Callable) -> None:
        """注册状态观察者"""
        self._observers.append(observer)

    def remove_observer(self, observer: Callable) -> None:
        """移除状态观察者"""
        if observer in self._observers:
            self._observers.remove(observer)

    def snapshot(self) -> Any:
        """获取状态的快照（不可变视图）"""
        return self._value

    def __str__(self) -> str:
        return f"State({self.name}={self._value}, version={self._version})"


class MutableState(StateManager):
    """
    MutableState - 可变状态

    Jetpack Compose 中的可变状态，可以触发重组。

    Mutable state in Jetpack Compose that can trigger recomposition.
    """

    def __init__(self, initial_value: Any = None, name: str = "mutable_state"):
        super().__init__(name)
        self.value = initial_value

    def __repr__(self) -> str:
        return f"MutableState({self.name}={self.value})"


class StateHolder:
    """
    状态持有者 - 管理 Composable 的状态

    模拟 Compose 中的 remember 机制。

    Simulates the remember mechanism in Compose.
    """

    def __init__(self):
        self._states: Dict[str, StateManager] = {}
        self._composables: Dict[str, ComposableFunction] = {}

    def remember_state(self, name: str, initial_value: Any = None) -> MutableState:
        """记住状态（类似 remember {}）"""
        if name not in self._states:
            self._states[name] = MutableState(initial_value, name)
        return self._states[name]

    def remember_composable(self, name: str, func: Callable,
                            dependencies: List[str] = None) -> ComposableFunction:
        """记住 Composable 函数（类似 remember {}）"""
        if name not in self._composables:
            self._composables[name] = ComposableFunction(name, func, dependencies)
        return self._composables[name]

    def get_state(self, name: str) -> Optional[StateManager]:
        return self._states.get(name)

    def get_composable(self, name: str) -> Optional[ComposableFunction]:
        return self._composables.get(name)

    def clear(self) -> None:
        self._states.clear()
        self._composables.clear()

    def __str__(self) -> str:
        return (f"StateHolder(states={len(self._states)}, "
                f"composables={len(self._composables)})")


# ---- Compose 布局原语 ----

class Column:
    """
    Column - 垂直排列子元素

    将子元素按照垂直方向依次排列。

    Arranges children vertically, one after another.

    属性：
    - horizontalAlignment: 水平对齐方式
    - verticalArrangement: 垂直排列方式
    - modifier: 修饰符（padding, margin 等）
    """

    def __init__(self, horizontal_alignment: str = "start",
                 vertical_arrangement: str = "top",
                 modifier: Optional[Dict[str, Any]] = None):
        self.horizontal_alignment = horizontal_alignment
        self.vertical_arrangement = vertical_arrangement
        self.modifier = modifier or {}
        self._children: List[str] = []
        self._measured_height: int = 0
        self._layout_log: List[str] = []

    def add_child(self, child: str, modifier: Optional[Dict[str, Any]] = None) -> "Column":
        """添加子元素"""
        self._children.append(child)
        self._layout_log.append(f"  Child: {child}")
        return self

    def measure(self, max_height: int = 1200) -> int:
        """测量 Column 高度"""
        child_height = 0
        for child in self._children:
            # 模拟子元素高度
            child_height += 50
        self._measured_height = min(child_height, max_height)
        return self._measured_height

    def layout(self, max_height: int = 1200) -> Dict[str, Any]:
        """布局 Column 及其子元素"""
        current_y = self.modifier.get("padding_top", 0)
        layout_result = {"children": []}

        for child in self._children:
            child_layout = {
                "name": child,
                "y": current_y,
                "height": 50,
            }
            layout_result["children"].append(child_layout)
            current_y += 50
            self._layout_log.append(f"  Layout {child}: y={current_y - 50}")

        self._measured_height = current_y
        return layout_result

    def __str__(self) -> str:
        return (f"Column[{len(self._children)} children, "
                f"align={self.horizontal_alignment}, "
                f"arrange={self.vertical_arrangement}]")


class Row:
    """
    Row - 水平排列子元素

    将子元素按照水平方向依次排列。

    Arranges children horizontally, side by side.

    属性：
    - verticalAlignment: 垂直对齐方式
    - horizontalArrangement: 水平排列方式
    - modifier: 修饰符
    """

    def __init__(self, vertical_alignment: str = "top",
                 horizontal_arrangement: str = "start",
                 modifier: Optional[Dict[str, Any]] = None):
        self.vertical_alignment = vertical_alignment
        self.horizontal_arrangement = horizontal_arrangement
        self.modifier = modifier or {}
        self._children: List[str] = []
        self._measured_width: int = 0
        self._layout_log: List[str] = []

    def add_child(self, child: str, modifier: Optional[Dict[str, Any]] = None) -> "Row":
        """添加子元素"""
        self._children.append(child)
        self._layout_log.append(f"  Child: {child}")
        return self

    def measure(self, max_width: int = 800) -> int:
        """测量 Row 宽度"""
        child_width = 0
        for child in self._children:
            child_width += 50
        self._measured_width = min(child_width, max_width)
        return self._measured_width

    def layout(self, max_width: int = 800) -> Dict[str, Any]:
        """布局 Row 及其子元素"""
        current_x = self.modifier.get("padding_left", 0)
        layout_result = {"children": []}

        for child in self._children:
            child_layout = {
                "name": child,
                "x": current_x,
                "width": 50,
            }
            layout_result["children"].append(child_layout)
            current_x += 50
            self._layout_log.append(f"  Layout {child}: x={current_x - 50}")

        self._measured_width = current_x
        return layout_result

    def __str__(self) -> str:
        return (f"Row[{len(self._children)} children, "
                f"align={self.vertical_alignment}, "
                f"arrange={self.horizontal_arrangement}]")


class Box:
    """
    Box - 堆叠子元素

    将子元素堆叠在一起，第一个在底层，最后一个在顶层。

    Stacks children on top of each other, first at bottom, last at top.

    属性：
    - contentAlignment: 内容对齐方式
    - modifier: 修饰符
    """

    def __init__(self, content_alignment: str = "top_start",
                 modifier: Optional[Dict[str, Any]] = None):
        self.content_alignment = content_alignment
        self.modifier = modifier or {}
        self._children: List[str] = []
        self._measured_width: int = 0
        self._measured_height: int = 0
        self._layout_log: List[str] = []

    def add_child(self, child: str, modifier: Optional[Dict[str, Any]] = None) -> "Box":
        """添加子元素"""
        self._children.append(child)
        self._layout_log.append(f"  Child: {child}")
        return self

    def measure(self, max_width: int = 800, max_height: int = 1200) -> Dict[str, int]:
        """测量 Box 尺寸"""
        self._measured_width = max_width
        self._measured_height = max_height
        return {"width": self._measured_width, "height": self._measured_height}

    def layout(self, max_width: int = 800, max_height: int = 1200) -> Dict[str, Any]:
        """布局 Box 及其子元素"""
        layout_result = {
            "width": max_width,
            "height": max_height,
            "children": [],
        }

        for child in self._children:
            child_layout = {
                "name": child,
                "alignment": self.content_alignment,
            }
            layout_result["children"].append(child_layout)

        self._measured_width = max_width
        self._measured_height = max_height
        return layout_result

    def __str__(self) -> str:
        return (f"Box[{len(self._children)} children, "
                f"align={self.content_alignment}]")


class LazyColumn:
    """
    LazyColumn - 可滚动垂直列表

    只渲染可见区域的 Composable，用于高效显示大量数据。

    Only renders composables in the visible area for efficient display
    of large datasets.

    类似 RecyclerView/ListView。
    """

    def __init__(self, modifier: Optional[Dict[str, Any]] = None):
        self.modifier = modifier or {}
        self._items: List[Dict[str, Any]] = []
        self._measured_height: int = 0

    def item(self, key: str, content: str = "") -> "LazyColumn":
        """添加单个 Item"""
        self._items.append({"type": "item", "key": key, "content": content})
        return self

    def items(self, key_prefix: str, count: int, content: str = "Item") -> "LazyColumn":
        """添加多个 Items"""
        for i in range(count):
            self._items.append({
                "type": "item",
                "key": f"{key_prefix}_{i}",
                "content": f"{content} {i+1}",
            })
        return self

    def measure(self, visible_height: int = 800) -> int:
        """测量可见高度"""
        self._measured_height = visible_height
        return visible_height

    def get_visible_items(self, visible_height: int = 800) -> List[Dict[str, Any]]:
        """获取可见区域 Items（模拟懒加载）"""
        item_height = 50
        visible_count = visible_height // item_height
        return self._items[:visible_count]

    def __str__(self) -> str:
        return f"LazyColumn[{len(self._items)} items]"


class Modifier:
    """
    Modifier - 修饰符

    用于添加 padding、margin、size、background 等属性。
    支持链式调用。

    Used to add padding, margin, size, background, etc.
    Supports method chaining.
    """

    def __init__(self, properties: Optional[Dict[str, Any]] = None):
        self._properties = properties or {}

    def padding(self, left: int = 0, right: int = 0,
                top: int = 0, bottom: int = 0) -> "Modifier":
        """添加内边距"""
        props = dict(self._properties)
        if "padding" not in props:
            props["padding"] = {"left": 0, "right": 0, "top": 0, "bottom": 0}
        padding = props["padding"]
        padding["left"] += left
        padding["right"] += right
        padding["top"] += top
        padding["bottom"] += bottom
        props["padding"] = padding
        return Modifier(props)

    def margin(self, left: int = 0, right: int = 0,
               top: int = 0, bottom: int = 0) -> "Modifier":
        """添加外边距"""
        props = dict(self._properties)
        if "margin" not in props:
            props["margin"] = {"left": 0, "right": 0, "top": 0, "bottom": 0}
        margin = props["margin"]
        margin["left"] += left
        margin["right"] += right
        margin["top"] += top
        margin["bottom"] += bottom
        props["margin"] = margin
        return Modifier(props)

    def size(self, width: int, height: int) -> "Modifier":
        """设置固定尺寸"""
        props = dict(self._properties)
        props["width"] = width
        props["height"] = height
        return Modifier(props)

    def width(self, width: int) -> "Modifier":
        """设置宽度"""
        props = dict(self._properties)
        props["width"] = width
        return Modifier(props)

    def height(self, height: int) -> "Modifier":
        """设置高度"""
        props = dict(self._properties)
        props["height"] = height
        return Modifier(props)

    def background(self, color: str) -> "Modifier":
        """设置背景颜色"""
        props = dict(self._properties)
        props["background"] = color
        return Modifier(props)

    def clip(self) -> "Modifier":
        """裁剪（圆角等）"""
        props = dict(self._properties)
        props["clip"] = True
        return Modifier(props)

    def shadow(self, elevation: int = 4) -> "Modifier":
        """添加阴影"""
        props = dict(self._properties)
        props["shadow"] = elevation
        return Modifier(props)

    def click(self) -> "Modifier":
        """添加点击能力"""
        props = dict(self._properties)
        props["clickable"] = True
        return Modifier(props)

    def fill_max_width(self) -> "Modifier":
        """填充最大宽度"""
        props = dict(self._properties)
        props["fill_max_width"] = True
        return Modifier(props)

    def fill_max_height(self) -> "Modifier":
        """填充最大高度"""
        props = dict(self._properties)
        props["fill_max_height"] = True
        return Modifier(props)

    def weight(self, weight: float) -> "Modifier":
        """设置权重（用于 Row/Column）"""
        props = dict(self._properties)
        props["weight"] = weight
        return Modifier(props)

    def properties(self) -> Dict[str, Any]:
        """获取所有属性"""
        return dict(self._properties)

    def __str__(self) -> str:
        return f"Modifier({self._properties})"


def modifier() -> Modifier:
    """创建 Modifier 的便捷函数"""
    return Modifier()


# ---- 文本组件 ----

class Text:
    """
    Text - Compose 文本组件

    在屏幕上显示文本。

    Displays text on screen.
    """

    def __init__(self, text: str, color: str = "black",
                 font_size: int = 16, modifier: Optional[Modifier] = None):
        self.text = text
        self.color = color
        self.font_size = font_size
        self.modifier = modifier or Modifier()
        self._measured_width: int = len(text) * font_size // 2

    def measure(self) -> int:
        self._measured_width = len(self.text) * self.font_size // 2
        return self._measured_width

    def __str__(self) -> str:
        return f"Text('{self.text}', size={self.font_size}, color={self.color})"


# ---- 按钮组件 ----

class Button:
    """
    Button - Compose 按钮组件

    可点击的按钮。

    A clickable button.
    """

    def __init__(self, onClick: Callable, text: str = "Button",
                 modifier: Optional[Modifier] = None):
        self.onClick = onClick
        self.text = text
        self.modifier = modifier or Modifier()
        self._click_count: int = 0

    def click(self) -> str:
        """模拟点击"""
        self._click_count += 1
        result = self.onClick()
        return f"Button clicked (#{self._click_count}): {result}"

    def __str__(self) -> str:
        return f"Button('{self.text}', clicks={self._click_count})"

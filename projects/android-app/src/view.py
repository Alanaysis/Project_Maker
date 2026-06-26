"""
View 系统模拟 - View System Simulation

Android 的 View 系统是 UI 框架的基础。View 是屏幕上的一块矩形区域，
负责绘制内容和处理事件。ViewGroup 是 View 的子类，可以作为容器容纳其他 View。

The Android View system is the foundation of the UI framework. A View is a
rectangular area on screen that handles drawing and events. ViewGroup is a
subclass of View that can contain other Views.

View 层次结构：
- View: 基础 UI 组件
- ViewGroup: View 容器
- TextView: 文本显示
- Button: 按钮
- ImageView: 图片显示
- EditText: 文本输入
- etc.

布局系统（LinearLayout, RelativeLayout, ConstraintLayout 等）
是 ViewGroup 的具体实现。
"""

import logging
from enum import Enum
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class ViewGravity(Enum):
    """重力/对齐方式"""
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"
    CENTER = "center"
    CENTER_HORIZONTAL = "center_horizontal"
    CENTER_VERTICAL = "center_vertical"
    START = "start"
    END = "end"
    FILL = "fill"
    NONE = "none"


class ViewMeasureSpecMode(Enum):
    """测量模式"""
    EXACTLY = "EXACTLY"  # 确切大小
    AT_MOST = "AT_MOST"  # 最大大小
    UNSPECIFIED = "UNSPECIFIED"  # 未指定


@dataclass
class ViewDimensions:
    """View 尺寸"""
    width: int = 0
    height: int = 0
    x: int = 0
    y: int = 0
    measured_width: int = 0
    measured_height: int = 0
    layout_width: int = 0
    layout_height: int = 0

    @property
    def is_wrap_content(self) -> bool:
        return self.layout_width < 0 or self.layout_height < 0

    @property
    def is_match_parent(self) -> bool:
        return self.layout_width > 0 or self.layout_height > 0


class View:
    """
    View 基类 - Base View Class

    View 是 Android UI 系统的基本构建块。每个 View 对象在屏幕上绘制内容
    并处理与该内容相关的事件。

    The View object is the basic building block of the UI. Each View draws
    content on screen and handles events related to that content.

    关键属性：
    - id: View 的唯一标识
    - visibility: 可见性 (VISIBLE, INVISIBLE, GONE)
    - padding: 内边距
    - margin: 外边距
    - background: 背景
    - text: 文本内容
    """

    # 特殊布局参数值
    MATCH_PARENT = 1  # 匹配父容器大小
    WRAP_CONTENT = -1  # 包裹内容大小
    FILL = 0  # 填充

    _next_id = 1000  # View ID 起始值

    def __init__(self, view_type: str = "View"):
        self.id: int = View._next_id
        View._next_id += 1
        self.view_type = view_type
        self.visibility: str = "visible"  # visible, invisible, gone
        self.padding: Dict[str, int] = {"left": 0, "right": 0, "top": 0, "bottom": 0}
        self.margin: Dict[str, int] = {"left": 0, "right": 0, "top": 0, "bottom": 0}
        self.background: Optional[str] = None
        self.text: str = ""
        self.tag: Any = None  # 任意标签数据
        self.enabled: bool = True
        self.clickable: bool = False
        self.click_handler: Optional[Callable] = None
        self.long_click_handler: Optional[Callable] = None
        self.content_description: Optional[str] = None
        self.dimensions = ViewDimensions()
        self._children: List[View] = []
        self._parent: Optional["ViewGroup"] = None
        self._draw_log: List[str] = []
        self._event_log: List[str] = []

    def set_text(self, text: str) -> "View":
        """设置文本内容"""
        self.text = text
        return self

    def set_background(self, color: str) -> "View":
        """设置背景颜色"""
        self.background = color
        return self

    def set_visibility(self, visibility: str) -> "View":
        """设置可见性 (visible, invisible, gone)"""
        self.visibility = visibility
        return self

    def set_padding(self, left: int = 0, right: int = 0,
                    top: int = 0, bottom: int = 0) -> "View":
        """设置内边距"""
        self.padding = {"left": left, "right": right, "top": top, "bottom": bottom}
        return self

    def set_margin(self, left: int = 0, right: int = 0,
                   top: int = 0, bottom: int = 0) -> "View":
        """设置外边距"""
        self.margin = {"left": left, "right": right, "top": top, "bottom": bottom}
        return self

    def set_tag(self, tag: Any) -> "View":
        """设置标签"""
        self.tag = tag
        return self

    def set_click_handler(self, handler: Callable) -> "View":
        """设置点击事件处理器"""
        self.clickable = True
        self.click_handler = handler
        return self

    def set_long_click_handler(self, handler: Callable) -> "View":
        """设置长按事件处理器"""
        self.clickable = True
        self.long_click_handler = handler
        return self

    def on_click(self, source: str = "user") -> str:
        """处理点击事件"""
        if not self.enabled or not self.clickable:
            msg = f"{self.view_type}(id={self.id}): click ignored (disabled/not clickable)"
            self._event_log.append(msg)
            return msg

        if self.click_handler:
            result = self.click_handler(self)
            msg = f"{self.view_type}(id={self.id}): clicked ({source}) -> {result}"
        else:
            msg = f"{self.view_type}(id={self.id}): clicked ({source})"
        self._event_log.append(msg)
        logger.debug(msg)
        return msg

    def on_long_click(self, source: str = "user") -> str:
        """处理长按事件"""
        if not self.enabled or not self.clickable:
            return f"{self.view_type}(id={self.id}): long click ignored"

        if self.long_click_handler:
            result = self.long_click_handler(self)
            return f"{self.view_type}(id={self.id}): long clicked -> {result}"
        return f"{self.view_type}(id={self.id}): long clicked"

    def measure(self, width_spec: int, height_spec: int) -> ViewDimensions:
        """
        测量 View 尺寸

        Android 的测量过程分为两步：measure 和 layout。
        measure 确定 View 的期望大小，layout 确定实际位置。

        Args:
            width_spec: 宽度测量规格 (MATCH_PARENT, WRAP_CONTENT, 或具体像素值)
            height_spec: 高度测量规格
        """
        if width_spec == View.MATCH_PARENT:
            self.dimensions.measured_width = 800  # 假设父容器宽度
        elif width_spec == View.WRAP_CONTENT:
            # 根据内容估算大小
            self.dimensions.measured_width = max(len(self.text) * 8, 50)
        else:
            self.dimensions.measured_width = width_spec

        if height_spec == View.MATCH_PARENT:
            self.dimensions.measured_height = 1200  # 假设父容器高度
        elif height_spec == View.WRAP_CONTENT:
            self.dimensions.measured_height = max(len(self.text) * 16, 40)
        else:
            self.dimensions.measured_height = height_spec

        self.dimensions.width = self.dimensions.measured_width
        self.dimensions.height = self.dimensions.measured_height
        return self.dimensions

    def layout(self, x: int, y: int, width: int, height: int) -> None:
        """
        布局 View 位置

        Args:
            x: 左边缘位置
            y: 上边缘位置
            width: 宽度
            height: 高度
        """
        self.dimensions.x = x
        self.dimensions.y = y
        self.dimensions.width = width
        self.dimensions.height = height

    def draw(self) -> str:
        """
        绘制 View（模拟）

        Returns:
            绘制描述字符串
        """
        if self.visibility == "gone":
            return ""

        draw_desc = self._describe_view()
        self._draw_log.append(draw_desc)
        return draw_desc

    def _describe_view(self) -> str:
        """生成 View 的描述"""
        parts = [f"{self.view_type}(id={self.id})"]
        if self.text:
            parts.append(f"text='{self.text}'")
        if self.background:
            parts.append(f"bg={self.background}")
        parts.append(f"pos=({self.dimensions.x},{self.dimensions.y})")
        parts.append(f"size=({self.dimensions.width}x{self.dimensions.height})")
        parts.append(f"vis={self.visibility}")
        return " ".join(parts)

    def find_view_by_id(self, target_id: int) -> Optional["View"]:
        """
        递归查找 View

        Args:
            target_id: 目标 View ID
        Returns:
            找到的 View 或 None
        """
        if self.id == target_id:
            return self
        for child in self._children:
            result = child.find_view_by_id(target_id)
            if result:
                return result
        return None

    def get_hierarchy_string(self, indent: int = 0) -> str:
        """获取 View 层次结构的字符串表示"""
        prefix = "  " * indent
        desc = self._describe_view()
        result = f"{prefix}{desc}"

        if hasattr(self, '_children') and self._children:
            for child in self._children:
                result += "\n" + child.get_hierarchy_string(indent + 1)

        return result

    def __str__(self) -> str:
        return self._describe_view()

    def __repr__(self) -> str:
        return self.__str__()


class ViewGroup(View):
    """
    ViewGroup - View 容器基类

    ViewGroup 是 View 的子类，作为其他 View 的容器。
    所有布局类（LinearLayout, RelativeLayout 等）都继承自 ViewGroup。

    ViewGroup is a subclass of View that acts as a container for other Views.
    All layout classes (LinearLayout, RelativeLayout, etc.) inherit from ViewGroup.
    """

    def __init__(self, view_type: str = "ViewGroup"):
        super().__init__(view_type)
        self._children: List[View] = []
        self._layout_mode: str = "linear"

    def add_child(self, child: View) -> "ViewGroup":
        """添加子 View"""
        child._parent = self
        self._children.append(child)
        logger.debug(f"Added child {child.view_type}(id={child.id}) to {self.view_type}")
        return self

    def remove_child(self, child: View) -> bool:
        """移除子 View"""
        if child in self._children:
            self._children.remove(child)
            child._parent = None
            return True
        return False

    def clear_children(self) -> List[View]:
        """清除所有子 View"""
        children = list(self._children)
        for child in self._children:
            child._parent = None
        self._children = []
        return children

    def measure_children(self, width_spec: int, height_spec: int) -> None:
        """测量所有子 View"""
        for child in self._children:
            child.measure(width_spec, height_spec)

    def layout_children(self, x_offset: int, y_offset: int) -> None:
        """布局所有子 View（由子类实现具体逻辑）"""
        pass

    def draw_children(self) -> List[str]:
        """绘制所有子 View"""
        draws = []
        for child in self._children:
            if child.visibility != "gone":
                draw = child.draw()
                if draw:
                    draws.append(draw)
                # 递归绘制子 View
                if hasattr(child, 'draw_children'):
                    draws.extend(child.draw_children())
        return draws

    def get_child_count(self) -> int:
        return len(self._children)

    def get_child_at(self, index: int) -> Optional[View]:
        if 0 <= index < len(self._children):
            return self._children[index]
        return None

    def get_hierarchy_string(self, indent: int = 0) -> str:
        """获取 View 层次结构的字符串表示"""
        prefix = "  " * indent
        desc = self._describe_view()
        result = f"{prefix}{desc} [{len(self._children)} children]"

        if self._children:
            for child in self._children:
                result += "\n" + child.get_hierarchy_string(indent + 1)

        return result

    def __str__(self) -> str:
        return f"{self.view_type}[{len(self._children)} children]"

    def __repr__(self) -> str:
        return self.__str__()


# ---- 具体 View 组件 ----

class TextView(View):
    """
    TextView - 文本显示组件

    用于在屏幕上显示文本内容。是最常用的 View 之一。

    Used to display text content on screen. One of the most commonly used Views.
    """

    def __init__(self, text: str = ""):
        super().__init__("TextView")
        self.text = text
        self.text_color: str = "black"
        self.text_size: int = 16
        self.gravity: ViewGravity = ViewGravity.LEFT
        self.hint: Optional[str] = None
        self.max_lines: int = 0  # 0 表示无限制
        self.ellipsize: str = "none"  # start, middle, end, none
        self.set_text(text)

    def set_text_color(self, color: str) -> "TextView":
        self.text_color = color
        return self

    def set_text_size(self, size: int) -> "TextView":
        self.text_size = size
        return self

    def set_gravity(self, gravity: ViewGravity) -> "TextView":
        self.gravity = gravity
        return self

    def set_hint(self, hint: str) -> "TextView":
        self.hint = hint
        return self

    def _describe_view(self) -> str:
        parts = [f"TextView(id={self.id})"]
        if self.text:
            parts.append(f"text='{self.text}'")
        else:
            parts.append(f"hint='{self.hint}'")
        parts.append(f"color={self.text_color}")
        parts.append(f"size={self.text_size}")
        parts.append(f"gravity={self.gravity.value}")
        parts.append(f"pos=({self.dimensions.x},{self.dimensions.y})")
        parts.append(f"size=({self.dimensions.width}x{self.dimensions.height})")
        parts.append(f"vis={self.visibility}")
        return " ".join(parts)


class Button(View):
    """
    Button - 按钮组件

    可点击的按钮，用于响应用户的点击操作。

    A clickable button that responds to user tap actions.
    """

    def __init__(self, text: str = ""):
        super().__init__("Button")
        self.set_text(text)
        self.clickable = True
        self.background_tint: str = "#2196F3"
        self.enabled = True

    def set_background_tint(self, color: str) -> "Button":
        self.background_tint = color
        return self

    def _describe_view(self) -> str:
        parts = [f"Button(id={self.id})"]
        if self.text:
            parts.append(f"text='{self.text}'")
        parts.append(f"bg={self.background_tint}")
        parts.append(f"enabled={self.enabled}")
        parts.append(f"pos=({self.dimensions.x},{self.dimensions.y})")
        parts.append(f"size=({self.dimensions.width}x{self.dimensions.height})")
        parts.append(f"vis={self.visibility}")
        return " ".join(parts)


class ImageView(View):
    """
    ImageView - 图片显示组件

    用于显示图片资源。

    Used to display image resources.
    """

    def __init__(self, src: str = "", content_desc: Optional[str] = None):
        super().__init__("ImageView")
        self.src = src
        self.content_description = content_desc
        self.scale_type: str = "fit_center"  # fit_center, center_crop, center_inside
        self.image_width: int = 200
        self.image_height: int = 200

    def set_scale_type(self, scale_type: str) -> "ImageView":
        self.scale_type = scale_type
        return self

    def _describe_view(self) -> str:
        parts = [f"ImageView(id={self.id})"]
        if self.src:
            parts.append(f"src='{self.src}'")
        if self.content_description:
            parts.append(f"desc='{self.content_description}'")
        parts.append(f"scale={self.scale_type}")
        parts.append(f"pos=({self.dimensions.x},{self.dimensions.y})")
        parts.append(f"size=({self.dimensions.width}x{self.dimensions.height})")
        parts.append(f"vis={self.visibility}")
        return " ".join(parts)


class EditText(View):
    """
    EditText - 文本输入组件

    可编辑的文本框，用于接收用户输入。

    An editable text box for receiving user input.
    """

    def __init__(self, hint: str = ""):
        super().__init__("EditText")
        self.hint = hint
        self.text = ""
        self.input_type: str = "text"  # text, number, email, password, phone
        self.max_length: int = 0  # 0 表示无限制
        self.enabled = True

    def set_input_type(self, input_type: str) -> "EditText":
        self.input_type = input_type
        return self

    def set_text(self, text: str) -> "EditText":
        self.text = text
        return self

    def _describe_view(self) -> str:
        parts = [f"EditText(id={self.id})"]
        if self.hint:
            parts.append(f"hint='{self.hint}'")
        if self.text:
            parts.append(f"text='{self.text}'")
        parts.append(f"type={self.input_type}")
        parts.append(f"pos=({self.dimensions.x},{self.dimensions.y})")
        parts.append(f"size=({self.dimensions.width}x{self.dimensions.height})")
        parts.append(f"vis={self.visibility}")
        return " ".join(parts)


class ProgressBar(View):
    """
    ProgressBar - 进度条组件

    用于显示操作的进度。

    Used to show the progress of an operation.
    """

    def __init__(self, max_progress: int = 100):
        super().__init__("ProgressBar")
        self.max_progress = max_progress
        self.current_progress: int = 0
        self.indeterminate: bool = True  # 不确定模式（动画）

    def set_progress(self, progress: int) -> "ProgressBar":
        self.current_progress = min(progress, self.max_progress)
        if progress < self.max_progress:
            self.indeterminate = False
        return self

    def set_indeterminate(self, indeterminate: bool) -> "ProgressBar":
        self.indeterminate = indeterminate
        return self

    def _describe_view(self) -> str:
        if self.indeterminate:
            mode = "indeterminate"
        else:
            mode = f"{self.current_progress}/{self.max_progress}"
        return (f"ProgressBar(id={self.id}) "
                f"progress={mode} "
                f"pos=({self.dimensions.x},{self.dimensions.y}) "
                f"vis={self.visibility}")


class Switch(View):
    """
    Switch - 开关组件

    用于在两个状态之间切换。

    Used to toggle between two states.
    """

    def __init__(self, text_on: str = "ON", text_off: str = "OFF"):
        super().__init__("Switch")
        self.checked: bool = False
        self.text_on = text_on
        self.text_off = text_off
        self.text = self.text_off

    def toggle(self) -> str:
        """切换开关状态"""
        self.checked = not self.checked
        self.text = self.text_on if self.checked else self.text_off
        return f"Switch: {self.text}"

    def set_checked(self, checked: bool) -> "Switch":
        self.checked = checked
        self.text = self.text_on if checked else self.text_off
        return self

    def _describe_view(self) -> str:
        return (f"Switch(id={self.id}) "
                f"checked={self.checked} "
                f"text='{self.text}' "
                f"pos=({self.dimensions.x},{self.dimensions.y}) "
                f"vis={self.visibility}")


class CheckBox(View):
    """
    CheckBox - 复选框组件

    用于在两个状态之间选择（选中/未选中）。

    Used for binary selection (checked/unchecked).
    """

    def __init__(self, text: str = ""):
        super().__init__("CheckBox")
        self.set_text(text)
        self.checked: bool = False
        self.clickable = True

    def toggle(self) -> bool:
        """切换选中状态"""
        self.checked = not self.checked
        return self.checked

    def set_checked(self, checked: bool) -> "CheckBox":
        self.checked = checked
        return self

    def _describe_view(self) -> str:
        return (f"CheckBox(id={self.id}) "
                f"text='{self.text}' "
                f"checked={self.checked} "
                f"pos=({self.dimensions.x},{self.dimensions.y}) "
                f"vis={self.visibility}")

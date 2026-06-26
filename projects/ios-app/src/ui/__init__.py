"""
UI 模块 - UI Module

本模块模拟 iOS UIKit 核心组件：
- UIView: 视图基类
- UIViewController: 视图控制器
- UINavigationController: 导航控制器
- UITableView: 表格视图
- Auto Layout: 自动布局系统
"""

from enum import Enum
from typing import Optional, List, Dict, Any, Callable, Tuple
from collections import OrderedDict


# ============================================================
# UIView - 视图基类
# ============================================================


class UIViewContentMode(Enum):
    """UIView 内容模式 - 类比 UIViewContentMode"""
    SCALE_TO_FIT = "scaleToFill"
    CENTER = "center"
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"
    TOP_LEFT = "topLeft"
    TOP_RIGHT = "topRight"
    BOTTOM_LEFT = "bottomLeft"
    BOTTOM_RIGHT = "bottomRight"


class UIView:
    """
    UIView 模拟器 - 模拟 iOS UIView 类

    UIView 是 iOS UI 的基础构建块：
    - 所有 UI 控件的基类
    - 管理帧 (frame)、边界 (bounds)、中心点 (center)
    - 支持子视图层次
    - 支持手势识别
    - 支持绘制 (drawRect)

    在 Python 中，我们用简单的属性模拟这些概念。
    """

    def __init__(self, frame: Optional[Tuple[float, float, float, float]] = None):
        """
        初始化 UIView

        Args:
            frame: (x, y, width, height) 视图的帧矩形
        """
        # 帧矩形 - 在父视图坐标系中的位置和大小
        self._frame = frame or (0, 0, 100, 100)
        self._x, self._y, self._width, self._height = self._frame

        # 边界矩形 - 在自身坐标系中的位置和大小
        self._bounds = (0, 0, self._width, self._height)

        # 中心点
        self._center = (self._x + self._width / 2, self._y + self._height / 2)

        # 视图属性
        self._background_color: Optional[str] = None
        self._border_color: Optional[str] = None
        self._border_width: float = 0
        self._cornerRadius: float = 0
        self._alpha: float = 1.0
        self._hidden: bool = False
        self._userInteractionEnabled: bool = True  # pylint: disable=invalid-name
        self._contentMode: UIViewContentMode = UIViewContentMode.SCALE_TO_FIT
        self._tag: int = 0
        self._name: str = ""

        # 子视图和父视图
        self._superview: Optional["UIView"] = None
        self._subviews: List["UIView"] = []

        # 手势识别器
        self._gestures: List["UIGestureRecognizer"] = []

        # 回调
        self._touch_down_handler: Optional[Callable] = None
        self._touch_up_handler: Optional[Callable] = None

        # 绘制回调
        self._draw_handler: Optional[Callable] = None

        print(f"[UIView] 创建视图 frame={self._frame}")

    @property
    def frame(self) -> Tuple[float, float, float, float]:
        return self._frame

    @frame.setter
    def frame(self, value: Tuple[float, float, float, float]):
        self._frame = value
        self._x, self._y, self._width, self._height = value
        self._center = (self._x + self._width / 2, self._y + self._height / 2)
        print(f"[UIView] 设置 frame: {value}")

    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        return self._bounds

    @bounds.setter
    def bounds(self, value: Tuple[float, float, float, float]):
        self._bounds = value
        print(f"[UIView] 设置 bounds: {value}")

    @property
    def center(self) -> Tuple[float, float]:
        return self._center

    @center.setter
    def center(self, value: Tuple[float, float]):
        self._center = value
        # 更新 frame
        self._x = value[0] - self._width / 2
        self._y = value[1] - self._height / 2
        self._frame = (self._x, self._y, self._width, self._height)
        print(f"[UIView] 设置 center: {value}")

    @property
    def x(self) -> float:
        return self._x

    @x.setter
    def x(self, value: float):
        self._x = value
        self._frame = (self._x, self._y, self._width, self._height)
        self._center = (self._x + self._width / 2, self._y + self._height / 2)

    @property
    def y(self) -> float:
        return self._y

    @y.setter
    def y(self, value: float):
        self._y = value
        self._frame = (self._x, self._y, self._width, self._height)
        self._center = (self._x + self._width / 2, self._y + self._height / 2)

    @property
    def width(self) -> float:
        return self._width

    @width.setter
    def width(self, value: float):
        self._width = value
        self._frame = (self._x, self._y, self._width, self._height)
        self._center = (self._x + self._width / 2, self._y + self._height / 2)

    @property
    def height(self) -> float:
        return self._height

    @height.setter
    def height(self, value: float):
        self._height = value
        self._frame = (self._x, self._y, self._width, self._height)
        self._center = (self._x + self._width / 2, self._y + self._height / 2)

    @property
    def superview(self) -> Optional["UIView"]:
        return self._superview

    @property
    def subviews(self) -> List["UIView"]:
        return self._subviews.copy()

    @property
    def tag(self) -> int:
        return self._tag

    @tag.setter
    def tag(self, value: int):
        self._tag = value

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def alpha(self) -> float:
        return self._alpha

    @alpha.setter
    def alpha(self, value: float):
        self._alpha = max(0.0, min(1.0, value))

    @property
    def is_hidden(self) -> bool:
        return self._hidden

    @property
    def is_visible(self) -> bool:
        return not self._hidden

    def add_subview(self, subview: "UIView"):
        """
        添加子视图 - 模拟 addSubview:

        这是 iOS 视图层次的核心操作。
        """
        # 如果子视图已有父视图，先移除
        if subview._superview:
            subview._superview._subviews.remove(subview)

        subview._superview = self
        self._subviews.append(subview)
        print(f"[UIView] 添加子视图: {subview.name or subview.__class__.__name__} "
              f"to {self.name or self.__class__.__name__}")

    def remove_from_superview(self):
        """从父视图中移除 - 模拟 removeFromSuperview"""
        if self._superview:
            self._superview._subviews.remove(self)
            self._superview = None
            print(f"[UIView] 移除视图: {self.name or self.__class__.__name__}")

    def bring_to_front(self):
        """将视图移到最前面"""
        if self._superview and self in self._superview._subviews:
            self._superview._subviews.remove(self)
            self._superview._subviews.append(self)
            print(f"[UIView] 视图 {self.name} 移到最前面")

    def send_to_back(self):
        """将视图移到最后面"""
        if self._superview and self in self._superview._subviews:
            self._superview._subviews.remove(self)
            self._superview._subviews.insert(0, self)
            print(f"[UIView] 视图 {self.name} 移到最后面")

    def viewWithTag(self, tag: int) -> Optional["UIView"]:
        """
        通过 tag 查找子视图 - 模拟 viewWithTag:

        递归搜索所有子视图。
        """
        if self._tag == tag:
            return self
        for subview in self._subviews:
            result = subview.viewWithTag(tag)
            if result:
                return result
        return None

    def hitTest(self, point: Tuple[float, float]) -> Optional["UIView"]:
        """
        触摸事件命中测试 - 模拟 hitTest:withEvent:

        确定哪个视图接收触摸事件。
        从最顶层（最后添加）的子视图开始检查。
        """
        if self._hidden or self._alpha <= 0 or not self._userInteractionEnabled:
            return None

        # 检查点是否在当前视图内
        x, y = point
        frame_x, frame_y, frame_w, frame_h = self._frame
        if frame_x <= x <= frame_x + frame_w and frame_y <= y <= frame_y + frame_h:
            # 从顶层子视图开始检查
            for subview in reversed(self._subviews):
                # 将点转换到子视图坐标系
                sub_x = x - frame_x
                sub_y = y - frame_y
                result = subview.hitTest((sub_x, sub_y))
                if result:
                    return result
            return self
        return None

    def set_touch_handlers(self, down: Optional[Callable] = None,
                           up: Optional[Callable] = None):
        """设置触摸回调"""
        self._touch_down_handler = down
        self._touch_up_handler = up

    def handle_touch_down(self, point: Tuple[float, float]):
        """处理触摸开始事件"""
        if self._touch_down_handler:
            self._touch_down_handler(point)

    def handle_touch_up(self, point: Tuple[float, float]):
        """处理触摸结束事件"""
        if self._touch_up_handler:
            self._touch_up_handler(point)

    def set_draw_handler(self, handler: Callable):
        """设置绘制回调 - 模拟 drawRect:"""
        self._draw_handler = handler

    def draw(self):
        """执行绘制回调"""
        if self._draw_handler:
            self._draw_handler(self)

    def layoutSubviews(self):
        """
        布局子视图 - 模拟 layoutSubviews

        iOS 会在适当时机自动调用此方法。
        子类可以重写此方法自定义布局逻辑。
        """
        pass

    def setNeedsLayout(self):
        """标记需要重新布局"""
        print(f"[UIView] 标记需要布局: {self.name or self.__class__.__name__}")

    def layoutIfNeeded(self):
        """执行布局"""
        self.layoutSubviews()
        for subview in self._subviews:
            subview.layoutIfNeeded()

    def __repr__(self):
        return (f"<{self.__class__.__name__} "
                f"frame={self._frame} "
                f"name='{self._name}' "
                f"alpha={self._alpha} "
                f"hidden={self._hidden}>")


# ============================================================
# UILabel - 标签视图
# ============================================================


class UILabel(UIView):
    """UILabel 模拟器 - 模拟 iOS UILabel"""

    def __init__(self, frame: Optional[Tuple[float, float, float, float]] = None):
        super().__init__(frame)
        self._text: str = ""
        self._font_name: str = "System"
        self._font_size: float = 17.0
        self._text_color: str = "#000000"
        self._text_alignment: str = "left"
        self._number_of_lines: int = 0  # 0 = 无限制
        self._name = "UILabel"

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str):
        self._text = value
        print(f"[UILabel] 设置文本: '{value[:50]}{'...' if len(value) > 50 else ''}'")

    @property
    def font_name(self) -> str:
        return self._font_name

    @property
    def font_size(self) -> float:
        return self._font_size

    @property
    def text_color(self) -> str:
        return self._text_color

    @text_color.setter
    def text_color(self, value: str):
        self._text_color = value

    @property
    def text_alignment(self) -> str:
        return self._text_alignment

    @text_alignment.setter
    def text_alignment(self, value: str):
        self._text_alignment = value

    @property
    def number_of_lines(self) -> int:
        return self._number_of_lines

    @number_of_lines.setter
    def number_of_lines(self, value: int):
        self._number_of_lines = value

    def __repr__(self):
        return (f"<UILabel text='{self._text[:30]}' "
                f"font={self._font_name}@{self._font_size} "
                f"frame={self._frame}>")


# ============================================================
# UIButton - 按钮视图
# ============================================================


class UIButton(UIView):
    """
    UIButton 模拟器 - 模拟 iOS UIButton

    UIButton 处理用户交互：
    - addTarget:action:forControlEvents:
    - 触摸事件回调
    """

    def __init__(self, frame: Optional[Tuple[float, float, float, float]] = None):
        super().__init__(frame)
        self._title_normal: str = ""
        self._title_highlighted: str = ""
        self._background_color_normal: str = "#007AFF"
        self._background_color_highlighted: str = "#0056CC"
        self._name = "UIButton"
        # 事件处理器: event_type -> callback
        self._event_handlers: Dict[str, Callable] = {}

    def set_title(self, title: str, state: str = "normal"):
        """设置按钮标题 - 模拟 setTitle:forState:"""
        if state == "normal":
            self._title_normal = title
        elif state == "highlighted":
            self._title_highlighted = title
        print(f"[UIButton] 设置标题: '{title}' [{state}]")

    def add_target(self, action: Callable, for_event: str = "touchUpInside"):
        """
        添加事件目标 - 模拟 addTarget:action:forControlEvents:

        这是 iOS 事件处理的核心模式。
        """
        self._event_handlers[for_event] = action
        print(f"[UIButton] 添加事件目标: {action.__name__} [{for_event}]")

    def send_event(self, event: str = "touchUpInside"):
        """发送事件"""
        if event in self._event_handlers:
            handler = self._event_handlers[event]
            handler(self)
            print(f"[UIButton] 发送事件: {event} -> {handler.__name__}")

    def __repr__(self):
        return (f"<UIButton title='{self._title_normal}' "
                f"frame={self._frame} "
                f"handlers={list(self._event_handlers.keys())}>")


# ============================================================
# UIImageView - 图片视图
# ============================================================


class UIImageView(UIView):
    """UIImageView 模拟器 - 模拟 iOS UIImageView"""

    def __init__(self, frame: Optional[Tuple[float, float, float, float]] = None):
        super().__init__(frame)
        self._image_name: str = ""
        self._image_data: Optional[bytes] = None
        self._name = "UIImageView"

    @property
    def image_name(self) -> str:
        return self._image_name

    @image_name.setter
    def image_name(self, value: str):
        self._image_name = value
        print(f"[UIImageView] 设置图片: {value}")

    def __repr__(self):
        return f"<UIImageView image='{self._image_name}' frame={self._frame}>"


# ============================================================
# UITextField - 文本输入框
# ============================================================


class UITextField(UIView):
    """UITextField 模拟器 - 模拟 iOS UITextField"""

    def __init__(self, frame: Optional[Tuple[float, float, float, float]] = None):
        super().__init__(frame)
        self._text: str = ""
        self._placeholder: str = ""
        self._keyboard_type: str = "default"
        self._border_style: str = "none"
        self._name = "UITextField"
        self._delegate = None

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str):
        self._text = value
        if self._delegate and hasattr(self._delegate, "textField_didChange"):
            self._delegate.textField_didChange(self, value)

    @property
    def placeholder(self) -> str:
        return self._placeholder

    @placeholder.setter
    def placeholder(self, value: str):
        self._placeholder = value

    def __repr__(self):
        return (f"<UITextField text='{self._text}' "
                f"placeholder='{self._placeholder}' "
                f"frame={self._frame}>")


# ============================================================
# UIScrollView - 可滚动视图
# ============================================================


class UIScrollView(UIView):
    """UIScrollView 模拟器 - 模拟 iOS UIScrollView"""

    def __init__(self, frame: Optional[Tuple[float, float, float, float]] = None):
        super().__init__(frame)
        self._content_offset: Tuple[float, float] = (0, 0)
        self._content_size: Tuple[float, float] = (0, 0)
        self._bounces: bool = True
        self._shows_scroll_indicator: bool = True
        self._name = "UIScrollView"
        self._delegate = None

    @property
    def content_offset(self) -> Tuple[float, float]:
        return self._content_offset

    @content_offset.setter
    def content_offset(self, value: Tuple[float, float]):
        self._content_offset = value
        if self._delegate and hasattr(self._delegate, "scrollView_didScroll"):
            self._delegate.scrollView_didScroll(self, value)

    @property
    def content_size(self) -> Tuple[float, float]:
        return self._content_size

    @content_size.setter
    def content_size(self, value: Tuple[float, float]):
        self._content_size = value

    def __repr__(self):
        return (f"<UIScrollView contentOffset={self._content_offset} "
                f"contentSize={self._content_size} "
                f"frame={self._frame}>")


# ============================================================
# UIViewController - 视图控制器
# ============================================================


class UIViewController:
    """
    UIViewController 模拟器 - 模拟 iOS UIViewController

    UIViewController 是 MVC 架构中的 Controller：
    - 管理一个 UIView 层次
    - 处理视图生命周期
    - 协调 Model 和 View

    生命周期方法：
    - viewDidLoad: 视图加载完成
    - viewWillAppear: 视图即将显示
    - viewDidAppear: 视图已显示
    - viewWillDisappear: 视图即将消失
    - viewDidDisappear: 视图已消失
    - viewDidDisappear: 视图已消失
    """

    def __init__(self, title: str = ""):
        self._title = title
        self._view: Optional[UIView] = None
        self._navigation_controller: Optional["UINavigationController"] = None
        self._parent: Optional["UIViewController"] = None
        self._child_view_controllers: List["UIViewController"] = []
        self._nibName: Optional[str] = None
        self._nibBundle: Any = None
        self._modal_parent: Optional["UIViewController"] = None
        self._name = title or self.__class__.__name__

        # 生命周期状态
        self._view_loaded = False
        self._view_appeared = False

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str):
        self._title = value
        print(f"[UIViewController] 设置标题: '{value}'")

    @property
    def view(self) -> Optional[UIView]:
        return self._view

    @property
    def navigation_controller(self) -> Optional["UINavigationController"]:
        return self._navigation_controller

    @property
    def parent(self) -> Optional["UIViewController"]:
        return self._parent

    @property
    def name(self) -> str:
        return self._name

    def load_view(self):
        """加载视图 - 模拟 loadView"""
        if self._view is None:
            # 创建根视图
            self._view = UIView(frame=(0, 0, 375, 667))  # iPhone 标准尺寸
            self._view.name = f"{self.__class__.__name__}_root"
            print(f"[UIViewController] 加载视图: {self.__class__.__name__}")

    def view_did_load(self):
        """视图加载完成 - 模拟 viewDidLoad"""
        self._view_loaded = True
        print(f"[UIViewController] viewDidLoad: {self.__class__.__name__}")

    def view_will_appear(self):
        """视图即将显示 - 模拟 viewWillAppear:"""
        print(f"[UIViewController] viewWillAppear: {self.__class__.__name__}")

    def view_did_appear(self):
        """视图已显示 - 模拟 viewDidAppear:"""
        self._view_appeared = True
        print(f"[UIViewController] viewDidAppear: {self.__class__.__name__}")

    def view_will_disappear(self):
        """视图即将消失 - 模拟 viewWillDisappear:"""
        print(f"[UIViewController] viewWillDisappear: {self.__class__.__name__}")

    def view_did_disappear(self):
        """视图已消失 - 模拟 viewDidDisappear:"""
        self._view_appeared = False
        print(f"[UIViewController] viewDidDisappear: {self.__class__.__name__}")

    def add_child(self, child: "UIViewController"):
        """添加子视图控制器 - 模拟 addChildViewController:"""
        self._child_view_controllers.append(child)
        child._parent = self
        print(f"[UIViewController] 添加子控制器: {child.__class__.__name__}")

    def remove_child(self, child: "UIViewController"):
        """移除子视图控制器 - 模拟 removeFromParentViewController:"""
        if child in self._child_view_controllers:
            self._child_view_controllers.remove(child)
            child._parent = None
            print(f"[UIViewController] 移除子控制器: {child.__class__.__name__}")

    def present(self, viewController: "UIViewController", animated: bool = True):
        """
        展示模态视图控制器 - 模拟 presentViewController:animated:completion:
        """
        self._modal_parent = viewController
        print(f"[UIViewController] 模态展示: {self.__class__.__name__} -> {viewController.__class__.__name__}")

    def dismiss(self, animated: bool = True):
        """
        dismiss 模态视图控制器 - 模拟 dismissViewControllerAnimated:completion:
        """
        if self._modal_parent:
            print(f"[UIViewController] dismiss: {self.__class__.__name__}")
            self._modal_parent = None

    def __repr__(self):
        return (f"<{self.__class__.__name__} "
                f"title='{self._title}' "
                f"viewLoaded={self._view_loaded} "
                f"viewAppeared={self._view_appeared}>")


# ============================================================
# UINavigationController - 导航控制器
# ============================================================


class UINavigationController(UIViewController):
    """
    UINavigationController 模拟器 - 模拟 iOS UINavigationController

    导航控制器管理一个视图控制器栈：
    - pushViewController: 压入新视图
    - popViewController: 弹出当前视图
    - popToRootViewController: 弹出到根视图

    类比 Python 的调用栈。
    """

    def __init__(self, rootViewController: UIViewController):
        super().__init__(rootViewController.title)
        self._view = rootViewController.view if rootViewController else UIView()
        self._view_controller_stack: List[UIViewController] = []
        self._root_view_controller = rootViewController
        self._interactive_pop_enabled: bool = True

        if rootViewController:
            self._view_controller_stack.append(rootViewController)
            rootViewController._navigation_controller = self
            print(f"[UINavigationController] 创建导航控制器, 根视图: {rootViewController.__class__.__name__}")

    @property
    def view_controller_stack(self) -> List[UIViewController]:
        return self._view_controller_stack.copy()

    @property
    def top_view_controller(self) -> Optional[UIViewController]:
        return self._view_controller_stack[-1] if self._view_controller_stack else None

    @property
    def visible_view_controller(self) -> Optional[UIViewController]:
        return self.top_view_controller

    @property
    def navigation_bar_height(self) -> float:
        return 44.0  # iOS 标准导航栏高度

    def push_view_controller(self, viewController: UIViewController, animated: bool = True):
        """
        压入视图控制器 - 模拟 pushViewController:animated:

        将新视图控制器推入栈顶，显示其视图。
        """
        # 将当前 top VC 的 view 从 superview 移除
        if self.top_view_controller and self.top_view_controller.view:
            self.top_view_controller.view.remove_from_superview()

        # 设置新 VC 的导航控制器引用
        viewController._navigation_controller = self

        # 生命周期回调
        if self.top_view_controller:
            self.top_view_controller.view_will_disappear()
            self.top_view_controller.view_did_disappear()

        # 压入新 VC
        self._view_controller_stack.append(viewController)
        viewController.view_will_appear()
        viewController.view_did_appear()

        # 将新 VC 的 view 添加到导航控制器的 view
        if viewController.view:
            self._view.add_subview(viewController.view)

        print(f"[UINavigationController] push: {viewController.__class__.__name__} "
              f"(栈深度: {len(self._view_controller_stack)})")

    def pop_view_controller(self, animated: bool = True) -> Optional[UIViewController]:
        """
        弹出视图控制器 - 模拟 popViewControllerAnimated:

        弹出栈顶视图控制器，显示前一个视图。
        """
        if len(self._view_controller_stack) <= 1:
            print("[UINavigationController] 无法弹出: 只有一个视图控制器")
            return None

        popping = self._view_controller_stack.pop()
        popping.view_will_disappear()
        popping.view_did_disappear()

        if self.top_view_controller:
            self.top_view_controller.view_will_appear()
            self.top_view_controller.view_did_appear()

        print(f"[UINavigationController] pop: {popping.__class__.__name__} "
              f"(栈深度: {len(self._view_controller_stack)})")
        return popping

    def pop_to_root_controller(self, animated: bool = True) -> List[UIViewController]:
        """
        弹出到根视图控制器 - 模拟 popToRootViewControllerAnimated:

        弹出所有非根视图控制器。
        """
        popped = []
        while len(self._view_controller_stack) > 1:
            vc = self._view_controller_stack.pop()
            vc.view_will_disappear()
            vc.view_did_disappear()
            popped.append(vc)

        if self.top_view_controller:
            self.top_view_controller.view_will_appear()
            self.top_view_controller.view_did_appear()

        print(f"[UINavigationController] popToRoot: 弹出 {len(popped)} 个视图")
        return popped

    def __repr__(self):
        return (f"<UINavigationController "
                f"stack={len(self._view_controller_stack)} "
                f"top='{self.top_view_controller.__class__.__name__ if self.top_view_controller else 'none'}'>")


# ============================================================
# UITableView - 表格视图
# ============================================================


class UITableViewStyle(Enum):
    """UITableView 样式"""
    PLAIN = "plain"
    GROUPED = "grouped"


class UITableView(UIView):
    """
    UITableView 模拟器 - 模拟 iOS UITableView

    UITableView 是 iOS 中最常用的视图之一：
    - 显示行列表
    - 支持分组
    - 可滚动
    - 通过 dataSource 获取数据
    - 通过 delegate 处理交互

    类比 Python 的列表 + 渲染循环。
    """

    def __init__(self, frame: Optional[Tuple[float, float, float, float]] = None,
                 style: UITableViewStyle = UITableViewStyle.PLAIN):
        super().__init__(frame)
        self._style = style
        self._name = "UITableView"
        self._dataSource = None
        self._delegate = None
        self._rows: List[Any] = []
        self._sections: List[List[Any]] = []
        self._selected_row: Optional[Tuple[int, int]] = None  # (section, row)
        self._cell_height: float = 44.0
        self._separator_style: str = "singleLine"
        self._background_color: str = "#FFFFFF"
        self._estimated_row_height: float = 44.0
        self._section_header_height: float = 0.0
        self._section_footer_height: float = 0.0

    @property
    def data_source(self):
        return self._dataSource

    @data_source.setter
    def data_source(self, value):
        self._dataSource = value
        # 如果 dataSource 有方法，尝试获取数据
        if value and hasattr(value, "numberOfSections"):
            self._reload_data()

    @property
    def delegate(self):
        return self._delegate

    @delegate.setter
    def delegate(self, value):
        self._delegate = value

    @property
    def selected_row(self) -> Optional[Tuple[int, int]]:
        return self._selected_row

    def _reload_data(self):
        """重新加载数据 - 模拟 reloadData"""
        if not self._dataSource:
            return

        if hasattr(self._dataSource, "numberOfSections"):
            num_sections = self._dataSource.numberOfSections(self)
            self._sections = []
            for section in range(num_sections):
                if hasattr(self._dataSource, "numberOfRowsInSection"):
                    num_rows = self._dataSource.numberOfRowsInSection(self, section)
                    rows = []
                    for row in range(num_rows):
                        if hasattr(self._dataSource, "cellForRowAtIndexPath"):
                            cell = self._dataSource.cellForRowAtIndexPath(self, (section, row))
                            rows.append(cell)
                        else:
                            rows.append(f"Row {row}")
                    self._sections.append(rows)
        else:
            # 单section模式
            if hasattr(self._dataSource, "items"):
                self._sections = [self._dataSource.items]
            elif hasattr(self._dataSource, "get_items"):
                self._sections = [self._dataSource.get_items()]
            else:
                self._sections = []

        print(f"[UITableView] 重新加载数据: {len(self._sections)} sections")

    def reload_data(self):
        """公开的重载数据方法"""
        self._reload_data()

    def select_row(self, section: int, row: int, animated: bool = True):
        """选择行 - 模拟 selectRowAtIndexPath:animated:scrollPosition:"""
        self._selected_row = (section, row)
        if self._delegate and hasattr(self._delegate, "tableView_didSelectRowAtIndexPath"):
            self._delegate.tableView_didSelectRowAtIndexPath(self, (section, row))
        print(f"[UITableView] 选择行: section={section}, row={row}")

    def get_cell_at(self, section: int, row: int) -> Any:
        """获取指定位置的单元格"""
        if 0 <= section < len(self._sections) and 0 <= row < len(self._sections[section]):
            return self._sections[section][row]
        return None

    def number_of_sections(self) -> int:
        """获取分区数"""
        return len(self._sections)

    def number_of_rows_in_section(self, section: int) -> int:
        """获取指定分区的行数"""
        if 0 <= section < len(self._sections):
            return len(self._sections[section])
        return 0

    def __repr__(self):
        return (f"<UITableView sections={len(self._sections)} "
                f"selected={self._selected_row} "
                f"style={self._style.value}>")


# ============================================================
# Auto Layout - 自动布局系统
# ============================================================


class NSLayoutAttribute(Enum):
    """布局属性 - 类比 NSLayoutAttribute"""
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"
    LEADING = "leading"
    TRAILING = "trailing"
    WIDTH = "width"
    HEIGHT = "height"
    CENTER_X = "centerX"
    CENTER_Y = "centerY"
    ALIGN_LEADING = "alignLeading"
    ALIGN_TRAILING = "alignTrailing"
    ALIGN_TOP = "alignTop"
    ALIGN_BOTTOM = "alignBottom"
    CENTER = "center"


class NSLayoutConstraint:
    """
    NSLayoutConstraint 模拟器 - 模拟 iOS 约束

    约束格式：
    item1.attribute1 multiplier * item2.attribute2 = constant

    例如：
    label.centerX = superview.centerX * 1.0 + 0
    label.width = 100
    """

    def __init__(self, item1: UIView, attr1: NSLayoutAttribute,
                 multiplier: float, item2: Optional[UIView],
                 attr2: NSLayoutAttribute, constant: float):
        self.item1 = item1
        self.attr1 = attr1
        self.multiplier = multiplier
        self.item2 = item2
        self.attr2 = attr2
        self.constant = constant
        self._priority: float = 1000.0
        self._active: bool = False
        self._identifier: str = ""

    @property
    def priority(self) -> float:
        return self._priority

    @priority.setter
    def priority(self, value: float):
        self._priority = value

    @property
    def is_active(self) -> bool:
        return self._active

    @is_active.setter
    def is_active(self, value: bool):
        self._active = value

    @property
    def identifier(self) -> str:
        return self._identifier

    @identifier.setter
    def identifier(self, value: str):
        self._identifier = value

    def activate(self):
        """激活约束"""
        self._active = True
        print(f"[Constraint] 激活约束: {self.item1.name or 'view1'}.{self.attr1.value} "
              f"= {self.multiplier} * "
              f"({'view2' if self.item2 else 'constant'}.{self.attr2.value if self.item2 else 'N/A'}) "
              f"+ {self.constant}")

    def deactivate(self):
        """停用约束"""
        self._active = False
        print(f"[Constraint] 停用约束: {self.item1.name or 'view1'}.{self.attr1.value}")

    def __repr__(self):
        return (f"<NSLayoutConstraint {self.item1.name or 'view1'}.{self.attr1.value} "
                f"= {self.multiplier} * "
                f"({'view2' if self.item2 else 'const'}.{self.attr2.value if self.item2 else 'N/A'}) "
                f"+ {self.constant}>")


class UILayoutGuide:
    """
    UILayoutGuide 模拟器 - 模拟 iOS 布局辅助类

    布局辅助类不直接渲染内容，而是帮助定义视图布局。
    常用：UIEdgeInsets, UILayoutGuide
    """

    def __init__(self):
        self._frame: Tuple[float, float, float, float] = (0, 0, 0, 0)
        self._superview: Optional[UIView] = None
        self._name = ""

    @property
    def frame(self) -> Tuple[float, float, float, float]:
        return self._frame

    @frame.setter
    def frame(self, value: Tuple[float, float, float, float]):
        self._frame = value

    @property
    def superview(self) -> Optional[UIView]:
        return self._superview

    def __repr__(self):
        return f"<UILayoutGuide frame={self._frame}>"


class UILayoutGuideFactory:
    """布局辅助类工厂"""

    @staticmethod
    def create_guide(name: str = "") -> UILayoutGuide:
        guide = UILayoutGuide()
        guide._name = name
        print(f"[LayoutGuide] 创建布局辅助: {name}")
        return guide


class UILayout:
    """
    Auto Layout 引擎模拟器 - 模拟 iOS Auto Layout

    iOS Auto Layout 工作原理：
    1. 添加约束到视图
    2. 调用 setNeedsUpdateConstraints 标记需要更新
    3. 调用 updateConstraints 更新约束
    4. 调用 setNeedsLayout 标记需要布局
    5. 调用 layoutIfNeeded 执行布局

    在 Python 中，我们简化为直接计算约束。
    """

    def __init__(self):
        self._constraints: List[NSLayoutConstraint] = []

    @property
    def constraints(self) -> List[NSLayoutConstraint]:
        return self._constraints.copy()

    def add_constraint(self, constraint: NSLayoutConstraint):
        """添加约束 - 模拟 addConstraint:"""
        self._constraints.append(constraint)
        constraint.activate()

    def add_constraints(self, constraints: List[NSLayoutConstraint]):
        """添加多个约束 - 模拟 addConstraints:"""
        for c in constraints:
            self.add_constraint(c)
        print(f"[UILayout] 添加 {len(constraints)} 个约束")

    def remove_constraint(self, constraint: NSLayoutConstraint):
        """移除约束 - 模拟 removeConstraint:"""
        if constraint in self._constraints:
            constraint.deactivate()
            self._constraints.remove(constraint)
            print(f"[UILayout] 移除约束: {constraint.identifier or str(constraint)}")

    def remove_constraints(self, constraints: List[NSLayoutConstraint]):
        """移除多个约束 - 模拟 removeConstraints:"""
        for c in constraints:
            self.remove_constraint(c)
        print(f"[UILayout] 移除 {len(constraints)} 个约束")

    def activate_constraints(self, constraints: List[NSLayoutConstraint]):
        """激活约束 - 模拟 activateConstraints:"""
        for c in constraints:
            c.is_active = True
            c.activate()
        print(f"[UILayout] 激活 {len(constraints)} 个约束")

    def deactivate_constraints(self, constraints: List[NSLayoutConstraint]):
        """停用约束 - 模拟 deactivateConstraints:"""
        for c in constraints:
            c.is_active = False
            c.deactivate()
        print(f"[UILayout] 停用 {len(constraints)} 个约束")

    def resolve_constraints(self, root_view: UIView):
        """
        解析约束 - 模拟 Auto Layout 引擎

        根据约束计算每个视图的最终 frame。
        """
        print(f"[UILayout] 解析约束 (共 {len(self._constraints)} 个)")
        for constraint in self._constraints:
            if not constraint.is_active:
                continue
            self._apply_constraint(constraint, root_view)

    def _apply_constraint(self, constraint: NSLayoutConstraint, root_view: UIView):
        """应用单个约束"""
        item1 = constraint.item1
        item2 = constraint.item2
        m = constraint.multiplier
        c = constraint.constant

        if item2 is None:
            # 常量约束，如 width=100
            if constraint.attr1 == NSLayoutAttribute.WIDTH:
                item1.width = c
            elif constraint.attr1 == NSLayoutAttribute.HEIGHT:
                item1.height = c
            elif constraint.attr1 == NSLayoutAttribute.TOP:
                item1.y = c
            elif constraint.attr1 == NSLayoutAttribute.LEFT:
                item1.x = c
        elif item2 and item1:
            # 视图间约束
            if constraint.attr1 == NSLayoutAttribute.CENTER_X and constraint.attr2 == NSLayoutAttribute.CENTER_X:
                # centerX = multiplier * superview.centerX + constant
                if item2 is root_view or self._is_ancestor(item2, root_view):
                    superview_center_x = item2.x + item2.width / 2
                    item1.center = (superview_center_x * m + c, item1.center[1])
            elif constraint.attr1 == NSLayoutAttribute.LEFT and constraint.attr2 == NSLayoutAttribute.LEFT:
                if item2 is root_view or self._is_ancestor(item2, root_view):
                    item1.x = item2.x + c

    def _is_ancestor(self, view: UIView, ancestor: UIView) -> bool:
        """检查 view 是否是 ancestor 的祖先"""
        current = view
        while current:
            if current is ancestor:
                return True
            current = current._superview
        return False

    def __repr__(self):
        return f"<UILayout constraints={len(self._constraints)}>"


# ============================================================
# UIGestureRecognizer - 手势识别器
# ============================================================


class UIGestureRecognizerState(Enum):
    """手势识别器状态"""
    BEGAN = "began"
    CHANGED = "changed"
    ENDED = "ended"
    CANCELLED = "cancelled"
    FAILED = "failed"
    RECOGNIZED = "recognized"


class UIGestureRecognizer:
    """
    UIGestureRecognizer 基类 - 模拟 iOS 手势识别器

    手势识别器监听触摸事件并识别特定手势。
    """

    def __init__(self, callback: Optional[Callable] = None):
        self._state = UIGestureRecognizerState.FAILED
        self._callback = callback
        self._view: Optional[UIView] = None
        self._name = self.__class__.__name__

    @property
    def state(self) -> UIGestureRecognizerState:
        return self._state

    @property
    def view(self) -> Optional[UIView]:
        return self._view

    def add_to_view(self, view: UIView):
        """添加到视图 - 模拟 addGestureRecognizer:"""
        self._view = view
        view._gestures.append(self)
        print(f"[Gesture] 添加手势: {self._name} to {view.name or view.__class__.__name__}")

    def remove_from_view(self):
        """从视图移除 - 模拟 removeGestureRecognizer:"""
        if self._view and self in self._view._gestures:
            self._view._gestures.remove(self)
            self._view = None

    def reset(self):
        """重置手势状态"""
        self._state = UIGestureRecognizerState.FAILED

    def __repr__(self):
        return f"<{self._name} state={self._state.value}>"


class UITapGestureRecognizer(UIGestureRecognizer):
    """ UITapGestureRecognizer - 模拟点击手势"""

    def __init__(self, callback: Optional[Callable] = None, number_of_taps: int = 1):
        super().__init__(callback)
        self._name = "UITapGestureRecognizer"
        self._number_of_taps = number_of_taps

    def recognize(self, view: UIView, point: Tuple[float, float]):
        """识别点击手势"""
        self._state = UIGestureRecognizerState.RECOGNIZED
        if self._callback:
            self._callback(self, point)
        print(f"[UITapGestureRecognizer] 点击识别: {self._number_of_taps} taps at {point}")


class UIPanGestureRecognizer(UIGestureRecognizer):
    """ UIPanGestureRecognizer - 模拟拖动手势"""

    def __init__(self, callback: Optional[Callable] = None):
        super().__init__(callback)
        self._name = "UIPanGestureRecognizer"
        self._start_point: Tuple[float, float] = (0, 0)
        self._current_point: Tuple[float, float] = (0, 0)

    def recognize(self, view: UIView, point: Tuple[float, float]):
        """识别拖动手势"""
        if self._state == UIGestureRecognizerState.FAILED:
            self._state = UIGestureRecognizerState.BEGAN
            self._start_point = point
        elif self._state == UIGestureRecognizerState.BEGAN:
            self._state = UIGestureRecognizerState.CHANGED
            self._current_point = point

        if self._callback:
            self._callback(self, point)


class UISwipeGestureRecognizer(UIGestureRecognizer):
    """ UISwipeGestureRecognizer - 模拟滑动手势"""

    def __init__(self, direction: str = "right", callback: Optional[Callable] = None):
        super().__init__(callback)
        self._name = "UISwipeGestureRecognizer"
        self._direction = direction

    def recognize(self, view: UIView, point: Tuple[float, float]):
        """识别滑动手势"""
        self._state = UIGestureRecognizerState.RECOGNIZED
        if self._callback:
            self._callback(self, point)
        print(f"[UISwipeGestureRecognizer] 滑动识别: {self._direction}")


class UIPinchGestureRecognizer(UIGestureRecognizer):
    """ UIPinchGestureRecognizer - 模拟捏合手势"""

    def __init__(self, callback: Optional[Callable] = None):
        super().__init__(callback)
        self._name = "UIPinchGestureRecognizer"
        self._scale: float = 1.0

    def recognize(self, view: UIView, point: Tuple[float, float], scale: float = 1.0):
        """识别捏合手势"""
        self._scale = scale
        self._state = UIGestureRecognizerState.RECOGNIZED
        if self._callback:
            self._callback(self, point)


class UIRotationGestureRecognizer(UIGestureRecognizer):
    """ UIRotationGestureRecognizer - 模拟旋转手势"""

    def __init__(self, callback: Optional[Callable] = None):
        super().__init__(callback)
        self._name = "UIRotationGestureRecognizer"
        self._rotation: float = 0.0

    def recognize(self, view: UIView, point: Tuple[float, float], rotation: float = 0.0):
        """识别旋转手势"""
        self._rotation = rotation
        self._state = UIGestureRecognizerState.RECOGNIZED
        if self._callback:
            self._callback(self, point)


class UILongPressGestureRecognizer(UIGestureRecognizer):
    """ UILongPressGestureRecognizer - 模拟长按手势"""

    def __init__(self, callback: Optional[Callable] = None, minimum_press_time: float = 0.5):
        super().__init__(callback)
        self._name = "UILongPressGestureRecognizer"
        self._minimum_press_time = minimum_press_time
        self._press_start: float = 0

    def recognize(self, view: UIView, point: Tuple[float, float], elapsed: float = 0):
        """识别长按手势"""
        if elapsed >= self._minimum_press_time:
            self._state = UIGestureRecognizerState.RECOGNIZED
            if self._callback:
                self._callback(self, point)

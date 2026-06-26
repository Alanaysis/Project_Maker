"""
组件基类 - Component Base

鸿蒙 ArkUI 中的组件是 UI 的基本构建块。
所有 ArkUI 组件都继承自一个基类，具有：
- 属性系统 (Properties)
- 事件系统 (Events)
- 样式系统 (Styles)
- 生命周期回调 (Lifecycle callbacks)

在 ArkTS 中，组件通过装饰器标记，如 @Component。
这里我们用 Python 模拟这个机制。
"""

import copy
from typing import Any, Callable, Dict, List, Optional


# 鸿蒙组件生命周期阶段
class LifecyclePhase:
    """
    组件生命周期阶段枚举

    鸿蒙 ArkUI 组件有明确的生命周期：
    1. aboutToAppear: 组件即将出现，用于初始化
    2. aboutToDisappear: 组件即将消失，用于清理
    3. onAreaChange: 组件区域变化时触发
    """
    ABOUT_TO_APPEAR = 'aboutToAppear'
    ABOUT_TO_DISAPPEAR = 'aboutToDisappear'
    ON_AREA_CHANGE = 'onAreaChange'
    ON_TOUCH = 'onTouch'
    ON_CLICK = 'onClick'


class ComponentStyle:
    """
    组件样式系统

    模拟 ArkUI 的链式样式调用：
    .width(100).height(50).backgroundColor('#FFFFFF')
    """
    DEFAULT_STYLES = {
        'width': None,
        'height': None,
        'minWidth': None,
        'minHeight': None,
        'maxWidth': None,
        'maxHeight': None,
        'padding': {'top': 0, 'left': 0, 'right': 0, 'bottom': 0},
        'margin': {'top': 0, 'left': 0, 'right': 0, 'bottom': 0},
        'backgroundColor': None,
        'borderRadius': None,
        'opacity': 1.0,
        'visibility': 'visible',  # visible, hidden, none
        'rotation': 0,
        'scale': {'x': 1, 'y': 1},
        'translate': {'x': 0, 'y': 0},
        'zIndex': 0,
    }

    def __init__(self):
        self._styles = copy.deepcopy(self.DEFAULT_STYLES)

    def apply(self, key: str, value: Any) -> 'ComponentStyle':
        """链式调用：设置样式属性"""
        self._styles[key] = value
        return self

    def get(self, key: str, default=None) -> Any:
        return self._styles.get(key, default)

    def to_dict(self) -> Dict:
        return copy.deepcopy(self._styles)


class BaseComponent:
    """
    组件基类 - 所有 ArkUI 组件的父类

    模拟鸿蒙 ArkUI 的组件模型：
    - 每个组件有唯一的 id
    - 组件可以包含子组件 (children)
    - 组件有样式系统
    - 组件有生命周期回调
    - 组件支持事件处理

    ArkTS 示例：
    ```
    @Component
    struct MyComponent {
      build() {
        Column() {
          Text('Hello')
            .fontSize(24)
            .fontWeight(FontWeight.Bold)
        }
        .width('100%')
        .height('100%')
      }
    }
    ```
    """

    _component_counter = 0

    def __init__(self, name: str = 'Component', parent: Optional['BaseComponent'] = None):
        # 自动生成唯一 ID
        BaseComponent._component_counter += 1
        self.id = f'{name}_{BaseComponent._component_counter}'
        self.name = name
        self.parent = parent

        # 子组件列表 - 模拟 ArkUI 的组件树
        self.children: List['BaseComponent'] = []

        # 样式系统
        self.style = ComponentStyle()

        # 属性字典 - 存储组件数据属性
        self.properties: Dict[str, Any] = {}

        # 事件处理器
        self._event_handlers: Dict[str, List[Callable]] = {}

        # 生命周期回调
        self._lifecycle_callbacks: Dict[str, List[Callable]] = {
            LifecyclePhase.ABOUT_TO_APPEAR: [],
            LifecyclePhase.ABOUT_TO_DISAPPEAR: [],
            LifecyclePhase.ON_AREA_CHANGE: [],
        }

        # 渲染状态
        self.is_rendered = False
        self.render_count = 0

        # 测量结果
        self.measured_width = 0
        self.measured_height = 0

    def add_child(self, child: 'BaseComponent') -> 'BaseComponent':
        """
        添加子组件

        在 ArkUI 中，子组件通过嵌套语法添加：
        Column() {
          Text('First')
          Text('Second')
        }
        """
        child.parent = self
        self.children.append(child)
        return self

    def set_property(self, key: str, value: Any) -> 'BaseComponent':
        """设置组件属性"""
        self.properties[key] = value
        return self

    def on(self, event: str, handler: Callable) -> 'BaseComponent':
        """
        注册事件处理器

        模拟 ArkUI 的事件系统：
        .onClick(() => { ... })
        .onTouch((event) => { ... })
        """
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)
        return self

    def trigger_event(self, event: str, *args, **kwargs) -> List[Any]:
        """触发事件，调用所有注册的处理函数"""
        results = []
        if event in self._event_handlers:
            for handler in self._event_handlers[event]:
                try:
                    result = handler(*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    print(f'[Event Error] {event} handler failed: {e}')
        return results

    def on_lifecycle(self, phase: str, callback: Callable) -> 'BaseComponent':
        """注册生命周期回调"""
        if phase in self._lifecycle_callbacks:
            self._lifecycle_callbacks[phase].append(callback)
        return self

    def trigger_lifecycle(self, phase: str, *args, **kwargs) -> List[Any]:
        """触发生命周期事件"""
        results = []
        if phase in self._lifecycle_callbacks:
            for callback in self._lifecycle_callbacks[phase]:
                try:
                    result = callback(*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    print(f'[Lifecycle Error] {phase} callback failed: {e}')
        return results

    def render(self, depth: int = 0) -> str:
        """
        渲染组件树

        模拟 ArkUI 的声明式渲染：
        UI = f(state)

        当状态变化时，UI 自动重建。
        """
        indent = '  ' * depth
        lines = [f'{indent}[{self.name}] id={self.id}']

        # 显示样式信息
        styles = self.style.to_dict()
        visible_styles = {k: v for k, v in styles.items() if v is not None and v != 0 and v != 1.0}
        if visible_styles:
            lines.append(f'{indent}  styles={visible_styles}')

        # 显示属性
        if self.properties:
            lines.append(f'{indent}  props={self.properties}')

        # 递归渲染子组件
        for child in self.children:
            child_lines = child.render(depth + 1)
            lines.append(child_lines)

        return '\n'.join(lines)

    def get_component_by_id(self, component_id: str) -> Optional['BaseComponent']:
        """通过 ID 查找组件（深度优先搜索）"""
        if self.id == component_id:
            return self
        for child in self.children:
            result = child.get_component_by_id(component_id)
            if result:
                return result
        return None

    def find_children(self, name: str) -> List['BaseComponent']:
        """查找所有同名子组件"""
        results = []
        for child in self.children:
            if child.name == name:
                results.append(child)
            results.extend(child.find_children(name))
        return results

    def count_components(self) -> int:
        """统计组件树中的总组件数"""
        count = 1  # 自身
        for child in self.children:
            count += child.count_components()
        return count

    def __str__(self):
        return f'<{self.name} id={self.id} children={len(self.children)}>'

    def __repr__(self):
        return self.__str__()

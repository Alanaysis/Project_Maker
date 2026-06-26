"""
Button 按钮组件 - Button Component

鸿蒙 ArkUI 中的 Button 组件用于创建可点击的按钮。

ArkTS 示例：
```
Button('Submit')
  .type(ButtonType.Capsule)
  .backgroundColor('#007DFF')
  .fontColor('#FFFFFF')
  .fontSize(16)
  .onClick(() => {
    console.log('Button clicked!')
  })
```

支持：
- 多种按钮类型（默认、胶囊、圆角等）
- 按钮状态（正常、按下、禁用）
- 点击事件
"""

from typing import Callable, Optional
from .base import BaseComponent, LifecyclePhase


class Button(BaseComponent):
    """
    按钮组件 - 模拟 ArkUI 的 Button 组件

    鸿蒙 Button 特性：
    1. 支持多种形状类型
    2. 支持按钮状态样式
    3. 支持点击事件
    4. 支持禁用状态
    """

    BUTTON_TYPES = ['default', 'Capsule', 'Circle', 'Rect']

    def __init__(self, content: str = '', parent=None):
        super().__init__(name='Button', parent=parent)
        self.set_property('content', content)

        # 按钮状态
        self.state = 'normal'  # normal, pressed, disabled

        # 按钮样式
        self.button_style = {
            'type': 'Capsule',    # 默认胶囊形状
            'backgroundColor': '#007DFF',
            'fontColor': '#FFFFFF',
            'fontSize': 16,
            'width': None,
            'height': 44,         # 默认高度 44vp
            'padding': {'top': 10, 'left': 24, 'right': 24, 'bottom': 10},
        }

        # 按下状态样式
        self.pressed_style = {
            'backgroundColor': '#0066CC',
            'opacity': 0.8,
        }

    def button_type(self, btn_type: str) -> 'Button':
        """设置按钮类型"""
        if btn_type in self.BUTTON_TYPES:
            self.button_style['type'] = btn_type
        return self

    def background_color(self, color: str) -> 'Button':
        """设置背景颜色"""
        self.button_style['backgroundColor'] = color
        return self

    def font_color(self, color: str) -> 'Button':
        """设置字体颜色"""
        self.button_style['fontColor'] = color
        return self

    def font_size(self, size: float) -> 'Button':
        """设置字体大小"""
        self.button_style['fontSize'] = size
        return self

    def set_disabled(self, disabled: bool) -> 'Button':
        """设置禁用状态"""
        if disabled:
            self.state = 'disabled'
            self.button_style['backgroundColor'] = '#CCCCCC'
            self.button_style['fontColor'] = '#999999'
        else:
            self.state = 'normal'
            self.button_style['backgroundColor'] = '#007DFF'
            self.button_style['fontColor'] = '#FFFFFF'
        return self

    def on_click(self, handler: Callable) -> 'Button':
        """绑定点击事件"""
        return self.on(LifecyclePhase.ON_CLICK, handler)

    def trigger_click(self) -> list:
        """触发点击事件"""
        if self.state == 'disabled':
            return []
        self.state = 'pressed'
        result = self.trigger_event(LifecyclePhase.ON_CLICK)
        self.state = 'normal'
        return result

    def render(self, depth: int = 0) -> str:
        """渲染按钮组件"""
        indent = '  ' * depth
        content = self.properties.get('content', '')
        lines = [f'{indent}[Button] "{content}" state={self.state}']
        lines.append(f'{indent}  type={self.button_style["type"]}')
        lines.append(f'{indent}  bg={self.button_style["backgroundColor"]} font={self.button_style["fontColor"]}')
        return '\n'.join(lines)

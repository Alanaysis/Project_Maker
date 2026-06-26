"""
TextInput 输入组件 - TextInput Component

鸿蒙 ArkUI 中的 TextInput 组件用于文本输入。

ArkTS 示例：
```
TextInput({ placeholder: '请输入用户名' })
  .type(InputType.TEXT)
  .maxLength(20)
  .onChange((value) => {
    console.log('Input changed:', value)
  })
```

支持：
- 多种输入类型（文本、密码、邮箱、电话等）
- 输入长度限制
- 输入验证
- 输入变化回调
"""

from typing import Callable, Optional
from .base import BaseComponent, LifecyclePhase


class TextInput(BaseComponent):
    """
    输入组件 - 模拟 ArkUI 的 TextInput 组件

    鸿蒙 TextInput 特性：
    1. 支持多种输入类型
    2. 支持输入验证
    3. 支持占位符文本
    4. 支持输入变化回调
    """

    INPUT_TYPES = ['TEXT', 'PASSWORD', 'EMAIL', 'PHONE', 'NUMBER', 'URL', 'SEARCH']

    def __init__(self, placeholder: str = '', parent=None):
        super().__init__(name='TextInput', parent=parent)
        self.set_property('placeholder', placeholder)
        self.set_property('value', '')

        # 输入配置
        self.input_config = {
            'type': 'TEXT',
            'maxLength': -1,       # -1 表示无限制
            'minLength': 0,
            'readOnly': False,
            'fontColor': '#000000',
            'fontSize': 16,
            'backgroundColor': '#FFFFFF',
            'placeholderColor': '#999999',
            'border': {'width': 0, 'color': '#E1E1E1', 'radius': 0},
        }

        # 验证状态
        self.validation_state = {
            'isValid': True,
            'errorMessage': '',
        }

    def input_type(self, input_type: str) -> 'TextInput':
        """设置输入类型"""
        if input_type in self.INPUT_TYPES:
            self.input_config['type'] = input_type
        return self

    def max_length(self, length: int) -> 'TextInput':
        """设置最大输入长度"""
        self.input_config['maxLength'] = length
        return self

    def read_only(self, readOnly: bool) -> 'TextInput':
        """设置只读模式"""
        self.input_config['readOnly'] = readOnly
        return self

    def placeholder_color(self, color: str) -> 'TextInput':
        """设置占位符颜色"""
        self.input_config['placeholderColor'] = color
        return self

    def border_style(self, width: float, color: str, radius: float = 0) -> 'TextInput':
        """设置边框样式"""
        self.input_config['border'] = {
            'width': width,
            'color': color,
            'radius': radius,
        }
        return self

    def validate(self, validator: Callable) -> bool:
        """
        执行输入验证

        validator 应该返回 (is_valid, error_message)
        """
        value = self.properties.get('value', '')
        is_valid, error_msg = validator(value)
        self.validation_state = {
            'isValid': is_valid,
            'errorMessage': error_msg,
        }
        return is_valid

    def update_value(self, value: str) -> bool:
        """
        更新输入值

        模拟输入变化：
        1. 检查最大长度
        2. 执行验证
        3. 触发 onChange 事件
        """
        max_len = self.input_config['maxLength']
        if max_len > 0 and len(value) > max_len:
            value = value[:max_len]

        self.properties['value'] = value
        return self.trigger_event(LifecyclePhase.ON_TOUCH, {'type': 'onChange', 'value': value})

    def render(self, depth: int = 0) -> str:
        """渲染输入组件"""
        indent = '  ' * depth
        value = self.properties.get('value', '')
        placeholder = self.properties.get('placeholder', '')
        display = value if value else f'[{placeholder}]'
        lines = [f'{indent}[TextInput] value="{display}"']
        lines.append(f'{indent}  type={self.input_config["type"]} maxLen={self.input_config["maxLength"]}')
        if not self.validation_state['isValid']:
            lines.append(f'{indent}  validation_error={self.validation_state["errorMessage"]}')
        return '\n'.join(lines)

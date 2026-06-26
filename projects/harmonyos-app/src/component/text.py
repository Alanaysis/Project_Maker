"""
Text 文本组件 - Text Component

鸿蒙 ArkUI 中的 Text 组件用于显示文本内容。

ArkTS 示例：
```
Text('Hello HarmonyOS')
  .fontSize(24)
  .fontWeight(FontWeight.Bold)
  .fontColor('#333333')
  .onClick(() => { ... })
```

支持：
- 富文本（通过 AppendText 链式构建）
- 文本样式（字体大小、粗细、颜色、下划线等）
- 文本溢出处理（裁剪、省略号）
- 点击事件
"""

from typing import List, Optional
from .base import BaseComponent, ComponentStyle


class Text(BaseComponent):
    """
    文本组件 - 模拟 ArkUI 的 Text 组件

    鸿蒙 Text 组件特性：
    1. 支持富文本构建（不同样式的文本片段）
    2. 支持多种文本样式
    3. 支持文本溢出处理
    4. 支持点击事件
    """

    def __init__(self, content: str = '', parent=None):
        super().__init__(name='Text', parent=parent)
        self.set_property('content', content)

        # 富文本片段列表
        self.rich_text_segments: List[Dict] = []

        # 默认文本样式
        self.text_style = {
            'fontSize': 14,       # 默认 14 vp
            'fontWeight': 'normal',
            'fontColor': '#000000',
            'fontFamily': 'HarmonySans',
            'lineHeight': None,
            'letterSpacing': 0,
            'textAlign': 'start',  # start, center, end
            'textOverflow': 'ellipsis',  # clip, ellipsis, none
            'maxLines': None,
            'decoration': {'type': 'none', 'color': '#000000'},
            'backgroundColor': None,
        }

    def font_size(self, size: float) -> 'Text':
        """设置字体大小（单位：vp）"""
        self.text_style['fontSize'] = size
        return self

    def font_weight(self, weight: str) -> 'Text':
        """
        设置字体粗细

        鸿蒙 fontWeight 值：
        - 'normal' / 400
        - 'bold' / 700
        - 100, 200, 300, 500, 600, 800, 900
        """
        self.text_style['fontWeight'] = weight
        return self

    def font_color(self, color: str) -> 'Text':
        """设置字体颜色"""
        self.text_style['fontColor'] = color
        return self

    def font_family(self, family: str) -> 'Text':
        """设置字体族"""
        self.text_style['fontFamily'] = family
        return self

    def line_height(self, height: float) -> 'Text':
        """设置行高"""
        self.text_style['lineHeight'] = height
        return self

    def text_align(self, align: str) -> 'Text':
        """设置文本对齐方式"""
        self.text_style['textAlign'] = align
        return self

    def text_overflow(self, overflow: str) -> 'Text':
        """
        设置文本溢出处理

        - 'clip': 裁剪超出部分
        - 'ellipsis': 显示省略号
        - 'none': 不处理溢出
        """
        self.text_style['textOverflow'] = overflow
        return self

    def max_lines(self, lines: int) -> 'Text':
        """设置最大行数，超出显示省略号"""
        self.text_style['maxLines'] = lines
        return self

    def text_decoration(self, type: str, color: str = '#000000') -> 'Text':
        """
        设置文本装饰线

        type: 'underline', 'lineThrough', 'overline', 'none'
        """
        self.text_style['decoration'] = {'type': type, 'color': color}
        return self

    def append_text(self, content: str, **kwargs) -> 'Text':
        """
        添加富文本片段

        模拟 ArkUI 的 AppendText：
        Text()
          .append('Hello ')
          .append('World', { fontColor: '#FF0000', fontWeight: 'bold' })
        """
        segment = {'content': content, 'style': kwargs}
        self.rich_text_segments.append(segment)
        return self

    def get_display_content(self) -> str:
        """获取最终显示的文本内容"""
        if self.rich_text_segments:
            return ''.join(seg['content'] for seg in self.rich_text_segments)
        return self.properties.get('content', '')

    def render(self, depth: int = 0) -> str:
        """渲染文本组件"""
        indent = '  ' * depth
        content = self.get_display_content()
        # 截断过长内容
        if len(content) > 50:
            content = content[:47] + '...'
        lines = [f'{indent}[Text] "{content}"']

        # 显示文本样式
        visible_styles = {
            k: v for k, v in self.text_style.items()
            if v is not None and v != 'normal' and v != '#000000'
            and v != 14 and v != 0 and v != 'start' and v != 'none'
        }
        if visible_styles:
            lines.append(f'{indent}  textStyle={visible_styles}')

        # 显示富文本片段
        if self.rich_text_segments:
            lines.append(f'{indent}  segments={len(self.rich_text_segments)} rich text parts')

        return '\n'.join(lines)

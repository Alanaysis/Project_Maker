"""
Image 图片组件 - Image Component

鸿蒙 ArkUI 中的 Image 组件用于显示图片。

ArkTS 示例：
```
Image($r('app.media.icon'))
  .width(100)
  .height(100)
  .objectFit(ImageFit.Cover)
  .borderRadius(50)
```

支持：
- 多种图片加载方式（资源、网络、本地）
- 图片缩放模式
- 图片裁剪（圆角等）
- 图片加载状态回调
"""

from typing import Optional
from .base import BaseComponent


class Image(BaseComponent):
    """
    图片组件 - 模拟 ArkUI 的 Image 组件

    鸿蒙 Image 组件特性：
    1. 支持多种图片源
    2. 支持多种缩放模式
    3. 支持图片裁剪
    4. 支持加载状态回调
    """

    FIT_MODES = ['Fill', 'Contain', 'Cover', 'Crop', 'Inside', 'ScaleDown']

    def __init__(self, source: str = '', parent=None):
        super().__init__(name='Image', parent=parent)
        self.set_property('source', source)

        # 图片状态
        self.load_state = 'idle'  # idle, loading, success, error

        # 图片样式
        self.image_style = {
            'objectFit': 'Contain',
            'borderRadius': 0,
            'width': None,
            'height': None,
            'opacity': 1.0,
        }

        # 图片原始尺寸
        self.natural_width = 0
        self.natural_height = 0

    def image_fit(self, mode: str) -> 'Image':
        """
        设置图片缩放模式

        - 'Fill': 拉伸填充，可能变形
        - 'Contain': 完整显示，保持比例
        - 'Cover': 填充，可能裁剪
        - 'Crop': 裁剪后填充
        - 'Inside': 缩小保持比例
        - 'ScaleDown': 缩小或不变
        """
        if mode in self.FIT_MODES:
            self.image_style['objectFit'] = mode
        return self

    def border_radius(self, radius: float) -> 'Image':
        """设置圆角半径"""
        self.image_style['borderRadius'] = radius
        return self

    def image_size(self, width: float, height: float) -> 'Image':
        """设置图片显示尺寸"""
        self.image_style['width'] = width
        self.image_style['height'] = height
        return self

    def set_load_state(self, state: str):
        """
        设置图片加载状态

        模拟图片加载流程：
        idle -> loading -> success/error
        """
        self.load_state = state
        if state == 'success':
            self.trigger_lifecycle('onImageLoad', {'width': self.natural_width, 'height': self.natural_height})
        elif state == 'error':
            self.trigger_lifecycle('onImageError', {'message': 'Failed to load image'})

    def render(self, depth: int = 0) -> str:
        """渲染图片组件"""
        indent = '  ' * depth
        source = self.properties.get('source', '')
        if len(source) > 40:
            source = source[:37] + '...'
        lines = [f'{indent}[Image] source="{source}"']
        lines.append(f'{indent}  fit={self.image_style["objectFit"]} state={self.load_state}')
        if self.image_style['borderRadius'] > 0:
            lines.append(f'{indent}  borderRadius={self.image_style["borderRadius"]}')
        return '\n'.join(lines)

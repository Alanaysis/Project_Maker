"""
跨平台框架原理 - Cross-Platform Framework Principles

核心模块：Skia 渲染引擎模拟器
功能：模拟 Flutter 使用的 Skia 图形库的核心渲染功能

跨平台框架原理说明：
Flutter 不使用原生控件，而是使用 Skia 图形引擎直接在画布上绘制 UI。
这带来了以下优势：
1. 跨平台一致性 - 同一套代码在所有平台上渲染相同的像素
2. 高性能 - 直接调用 GPU，绕过原生 UI 框架
3. 完全控制 - 可以创建任何自定义的视觉效果

渲染管线（Rendering Pipeline）：
Widget Tree → Element Tree → Render Tree → Scene → Raster → GPU → Screen

本模块模拟：
1. Canvas（画布）- 二维绘图表面
2. Paint（画笔）- 颜色、样式、混合模式
3. Path（路径）- 矢量图形定义
4. Layer（图层）- 分层渲染
5. Scene（场景）- 最终渲染场景
"""

import math
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union


# ============================================================
# 颜色系统 (Color System)
# ============================================================
class Color:
    """
    Skia 颜色模拟

    RGBA 8888 格式：
    - R: 红色 (0-255)
    - G: 绿色 (0-255)
    - B: 蓝色 (0-255)
    - A: 透明度 (0-255, 0=完全透明, 255=完全不透明)
    """

    def __init__(self, r: int = 0, g: int = 0, b: int = 0, a: int = 255):
        self._r = max(0, min(255, r))
        self._g = max(0, min(255, g))
        self._b = max(0, min(255, b))
        self._a = max(0, min(255, a))

    @property
    def r(self) -> int:
        return self._r

    @property
    def g(self) -> int:
        return self._g

    @property
    def b(self) -> int:
        return self._b

    @property
    def a(self) -> int:
        return self._a

    def with_alpha(self, alpha: int) -> 'Color':
        """返回带有新透明度颜色的副本"""
        return Color(self._r, self._g, self._b, alpha)

    def lerp(self, other: 'Color', t: float) -> 'Color':
        """线性插值：在两个颜色之间插值"""
        t = max(0.0, min(1.0, t))
        return Color(
            r=int(self._r + (other._r - self._r) * t),
            g=int(self._g + (other._g - self._g) * t),
            b=int(self._b + (other._b - self._b) * t),
            a=int(self._a + (other._a - self._a) * t),
        )

    def to_hex(self) -> str:
        """转换为十六进制颜色字符串"""
        return f"#{self._r:02x}{self._g:02x}{self._b:02x}{self._a:02x}"

    def __repr__(self):
        return f"Color(0x{self._a:02x}{self._r:02x}{self._g:02x}{self._b:02x})"

    def __eq__(self, other):
        return (self._r, self._g, self._b, self._a) == (other._r, other._g, other._b, other._a)


# 预定义常用颜色
class Colors:
    """预定义颜色常量"""
    TRANSPARENT = Color(0, 0, 0, 0)
    BLACK = Color(0, 0, 0, 255)
    WHITE = Color(255, 255, 255, 255)
    RED = Color(244, 67, 54, 255)
    GREEN = Color(76, 175, 80, 255)
    BLUE = Color(33, 150, 243, 255)
    PRIMARY = Color(66, 165, 245, 255)
    BACKGROUND = Color(255, 255, 255, 255)
    SURFACE = Color(255, 255, 255, 255)
    ERROR = Color(211, 47, 47, 255)


# ============================================================
# 画笔 (Paint)
# ============================================================
class FillStyle(Enum):
    """填充样式"""
    STROKE = "stroke"        # 只描边
    FILL = "fill"            # 只填充
    STROKE_AND_FILL = "stroke_and_fill"  # 描边+填充


class BlendMode(Enum):
    """混合模式"""
    SOURCE = "source"
    SOURCE_OVER = "source_over"
    MULTIPLY = "multiply"
    SCREEN = "screen"
    OVERLAY = "overlay"


class Paint:
    """
    Skia Paint 模拟

    Paint 对象描述了如何绘制几何图形（路径、矩形等）。
    它包含颜色、样式、混合模式等属性。

    Flutter 中：
    paint = Paint()
      ..color = Colors.blue
      ..style = PaintingStyle.fill
    canvas.drawRect(rect, paint)
    """

    def __init__(self):
        self._color = Colors.WHITE
        self._fill_style = FillStyle.FILL
        self._stroke_width = 1.0
        self._blend_mode = BlendMode.SOURCE_OVER
        self._anti_alias = True

    @property
    def color(self) -> Color:
        return self._color

    @color.setter
    def color(self, value: Color):
        self._color = value

    @property
    def fill_style(self) -> FillStyle:
        return self._fill_style

    @fill_style.setter
    def fill_style(self, value: FillStyle):
        self._fill_style = value

    @property
    def stroke_width(self) -> float:
        return self._stroke_width

    @stroke_width.setter
    def stroke_width(self, value: float):
        self._stroke_width = value

    @property
    def blend_mode(self) -> BlendMode:
        return self._blend_mode

    @blend_mode.setter
    def blend_mode(self, value: BlendMode):
        self._blend_mode = value

    @property
    def anti_alias(self) -> bool:
        return self._anti_alias

    @anti_alias.setter
    def anti_alias(self, value: bool):
        self._anti_alias = value

    def with_color(self, color: Color) -> 'Paint':
        """返回带有新颜色的画笔副本"""
        p = Paint()
        p._color = color
        p._fill_style = self._fill_style
        p._stroke_width = self._stroke_width
        p._blend_mode = self._blend_mode
        p._anti_alias = self._anti_alias
        return p

    def to_dict(self) -> Dict[str, Any]:
        """序列化画笔属性"""
        return {
            "color": self._color.to_hex(),
            "fill_style": self._fill_style.value,
            "stroke_width": self._stroke_width,
            "blend_mode": self._blend_mode.value,
            "anti_alias": self._anti_alias,
        }


# ============================================================
# 矩形 (Rect)
# ============================================================
class Rect:
    """
    矩形表示

    使用 left, top, right, bottom 坐标定义。
    在 Skia 中，Y 轴向下为正。
    """

    def __init__(self, left: float = 0.0, top: float = 0.0,
                 right: float = 0.0, bottom: float = 0.0):
        self._left = left
        self._top = top
        self._right = right
        self._bottom = bottom

    @property
    def left(self) -> float:
        return self._left

    @property
    def top(self) -> float:
        return self._top

    @property
    def right(self) -> float:
        return self._right

    @property
    def bottom(self) -> float:
        return self._bottom

    @property
    def width(self) -> float:
        return self._right - self._left

    @property
    def height(self) -> float:
        return self._bottom - self._top

    @property
    def center_x(self) -> float:
        return (self._left + self._right) / 2

    @property
    def center_y(self) -> float:
        return (self._top + self._bottom) / 2

    def centered_at(self, cx: float, cy: float) -> 'Rect':
        """返回以指定点为中心的矩形副本"""
        w = self.width
        h = self.height
        return Rect(cx - w/2, cy - h/2, cx + w/2, cy + h/2)

    def intersects(self, other: 'Rect') -> bool:
        """检查两个矩形是否相交"""
        return not (self.right < other.left or self.left > other.right or
                    self.bottom < other.top or self.top > other.bottom)

    def expanded(self, dx: float, dy: float) -> 'Rect':
        """返回扩展后的矩形"""
        return Rect(
            self._left - dx, self._top - dy,
            self._right + dx, self._bottom + dy
        )

    def to_dict(self) -> Dict[str, float]:
        return {
            "left": self._left, "top": self._top,
            "right": self._right, "bottom": self._bottom,
            "width": self.width, "height": self.height,
        }

    def __repr__(self):
        return f"Rect(l={self._left}, t={self._top}, r={self._right}, b={self._bottom})"

    @staticmethod
    def from_sizes(left: float, top: float, width: float, height: float) -> 'Rect':
        return Rect(left, top, left + width, top + height)


# ============================================================
# 点 (Offset)
# ============================================================
class Offset:
    """
    二维偏移量

    在 Skia 中，Offset 表示坐标空间中的点。
    (0, 0) 通常是画布的左上角。
    """

    def __init__(self, dx: float = 0.0, dy: float = 0.0):
        self._dx = dx
        self._dy = dy

    @property
    def dx(self) -> float:
        return self._dx

    @property
    def dy(self) -> float:
        return self._dy

    def distance_to(self, other: 'Offset') -> float:
        """计算到另一个点的距离"""
        return math.sqrt((self._dx - other._dx) ** 2 + (self._dy - other._dy) ** 2)

    def lerp(self, other: 'Offset', t: float) -> 'Offset':
        """线性插值"""
        return Offset(
            self._dx + (other._dx - self._dx) * t,
            self._dy + (other._dy - self._dy) * t,
        )

    def __add__(self, other: 'Offset') -> 'Offset':
        return Offset(self._dx + other._dx, self._dy + other._dy)

    def __repr__(self):
        return f"Offset(dx={self._dx}, dy={self._dy})"


# ============================================================
# 路径 (Path)
# ============================================================
class Path:
    """
    Skia 路径模拟

    Path 描述了要绘制的矢量图形。
    它由一系列子路径组成，包括：
    - 直线 (lineTo)
    - 圆弧 (arcTo)
    - 贝塞尔曲线 (cubicTo/quadraticBezierTo)
    - 椭圆 (addOval)
    - 矩形 (addRect)

    Flutter 中：
    canvas.drawPath(path, paint)
    """

    def __init__(self):
        self._subpaths: List[List[Tuple[str, Dict]]] = []
        self._bounds: Optional[Rect] = None

    def move_to(self, x: float, y: float) -> 'Path':
        """移动到指定点（开始新子路径）"""
        self._subpaths.append([("moveTo", {"x": x, "y": y})])
        return self

    def line_to(self, x: float, y: float) -> 'Path':
        """添加直线到指定点"""
        if self._subpaths:
            self._subpaths[-1].append(("lineTo", {"x": x, "y": y}))
        return self

    def close(self) -> 'Path':
        """闭合当前子路径"""
        if self._subpaths:
            self._subpaths[-1].append(("close", {}))
        return self

    def add_rect(self, rect: Rect) -> 'Path':
        """添加矩形到路径"""
        self._subpaths.append([
            ("moveTo", {"x": rect.left, "y": rect.top}),
            ("lineTo", {"x": rect.right, "y": rect.top}),
            ("lineTo", {"x": rect.right, "y": rect.bottom}),
            ("lineTo", {"x": rect.left, "y": rect.bottom}),
            ("close", {}),
        ])
        return self

    def add_oval(self, rect: Rect) -> 'Path':
        """添加内切椭圆到路径"""
        cx, cy = rect.center_x, rect.center_y
        rx = rect.width / 2
        ry = rect.height / 2
        # 用贝塞尔曲线近似椭圆
        k = 0.5522847498  # 椭圆控制点系数
        segments = [
            ("moveTo", {"x": cx, "y": cy - ry}),
            ("cubicTo", {"x1": cx + k*rx, "y1": cy - ry,
                         "x2": cx + rx, "y2": cy - k*ry,
                         "x3": cx + rx, "y3": cy}),
            ("cubicTo", {"x1": cx + rx, "y1": cy + k*ry,
                         "x2": cx + k*rx, "y2": cy + ry,
                         "x3": cx, "y3": cy + ry}),
            ("cubicTo", {"x1": cx - k*rx, "y1": cy + ry,
                         "x2": cx - rx, "y2": cy + k*ry,
                         "x3": cx - rx, "y3": cy}),
            ("cubicTo", {"x1": cx - rx, "y1": cy - k*ry,
                         "x2": cx - k*rx, "y2": cy - ry,
                         "x3": cx, "y3": cy - ry}),
        ]
        self._subpaths.append(segments)
        return self

    def add_circle(self, cx: float, cy: float, radius: float) -> 'Path':
        """添加圆形到路径"""
        rect = Rect(cx - radius, cy - radius, cx + radius, cy + radius)
        return self.add_oval(rect)

    @property
    def bounds(self) -> Optional[Rect]:
        """计算路径的边界框"""
        return self._bounds

    def compute_bounds(self) -> Rect:
        """计算路径的边界框"""
        if not self._subpaths:
            return Rect()

        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')

        for subpath in self._subpaths:
            for cmd, params in subpath:
                if 'x' in params:
                    min_x = min(min_x, params['x'])
                    max_x = max(max_x, params['x'])
                if 'y' in params:
                    min_y = min(min_y, params['y'])
                    max_y = max(max_y, params['y'])

        self._bounds = Rect(min_x, min_y, max_x, max_y)
        return self._bounds

    def to_dict(self) -> Dict[str, Any]:
        """序列化路径"""
        return {
            "subpaths": len(self._subpaths),
            "commands": sum(len(sp) for sp in self._subpaths),
            "bounds": self.compute_bounds().to_dict() if self._bounds else None,
        }

    def __repr__(self):
        return f"Path(subpaths={len(self._subpaths)}, commands={sum(len(sp) for sp in self._subpaths)})"


# ============================================================
# 图层 (Layer)
# ============================================================
class LayerType(Enum):
    """图层类型"""
    CLIP = "clip"              # 裁剪图层
    SAVE_LAYER = "save_layer"  # 保存图层（用于离屏渲染）
    GROUP = "group"            # 图层组


class Layer:
    """
    渲染图层

    Flutter 使用图层来实现：
    - 裁剪（Clip）
    - 动画（Animation）
    - 混合（Blending）
    - 离屏渲染（Off-screen rendering）

    图层树是渲染树的重要组成部分。
    """

    def __init__(self, layer_type: LayerType = LayerType.GROUP):
        self._type = layer_type
        self._children: List['Layer'] = []
        self._bounds: Optional[Rect] = None
        self._paint: Optional[Paint] = None
        self._saved = False

    def add_child(self, child: 'Layer'):
        self._children.append(child)

    @property
    def type(self) -> LayerType:
        return self._type

    @property
    def children(self) -> List['Layer']:
        return self._children

    def save_layer(self, bounds: Rect, paint: Optional[Paint] = None):
        """保存图层（用于离屏渲染）"""
        self._saved = True
        self._bounds = bounds
        self._paint = paint

    def restore(self):
        """恢复图层状态"""
        self._saved = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self._type.value,
            "children": len(self._children),
            "saved": self._saved,
            "paint": self._paint.to_dict() if self._paint else None,
        }


# ============================================================
# 画布 (Canvas)
# ============================================================
class Canvas:
    """
    Skia 画布模拟

    Canvas 是 Flutter 渲染引擎的核心抽象。
    所有绘制操作都通过 Canvas 进行。

    在 Flutter 中：
    1. Widget 树构建完成后，生成 Render 树
    2. Render 对象在 Canvas 上执行绘制
    3. 最终生成 Scene 发送给 GPU 渲染

    Canvas 操作包括：
    - 绘制基本形状（矩形、圆形、椭圆）
    - 绘制路径
    - 绘制文本
    - 变换（平移、旋转、缩放）
    - 裁剪
    """

    def __init__(self, width: float = 800, height: float = 600):
        self._width = width
        self._height = height
        self._draw_commands: List[Dict[str, Any]] = []
        self._layer_stack: List[Layer] = []
        self._transform: List[List[float]] = self._identity_matrix()
        self._clip_rect: Optional[Rect] = None
        self._dpi = 3.0  # 像素密度（3x for high DPI）
        self._pixel_size = (width * self._dpi, height * self._dpi)

    @property
    def size(self) -> Tuple[float, float]:
        return (self._width, self._height)

    @property
    def draw_commands(self) -> List[Dict[str, Any]]:
        return self._draw_commands

    @property
    def pixel_size(self) -> Tuple[int, int]:
        return self._pixel_size

    def save_layer(self, bounds: Rect, paint: Optional[Paint] = None) -> Layer:
        """保存图层并开始离屏渲染"""
        layer = Layer(LayerType.SAVE_LAYER)
        layer.save_layer(bounds, paint)
        self._layer_stack.append(layer)
        return layer

    def restore(self):
        """恢复画布状态（弹出图层）"""
        if self._layer_stack:
            self._layer_stack.pop()

    def translate(self, dx: float, dy: float):
        """平移变换"""
        self._transform = self._multiply_matrix(
            [[1, 0, dx], [0, 1, dy], [0, 0, 1]],
            self._transform
        )

    def scale(self, sx: float, sy: Optional[float] = None):
        """缩放变换"""
        sy = sy if sy is not None else sx
        self._transform = self._multiply_matrix(
            [[sx, 0, 0], [0, sy, 0], [0, 0, 1]],
            self._transform
        )

    def rotate(self, angle_degrees: float):
        """旋转变换（角度制）"""
        angle_rad = math.radians(angle_degrees)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        self._transform = self._multiply_matrix(
            [[cos_a, sin_a, 0], [-sin_a, cos_a, 0], [0, 0, 1]],
            self._transform
        )

    def clip_rect(self, rect: Rect):
        """裁剪画布"""
        self._clip_rect = rect

    def draw_rect(self, rect: Rect, paint: Paint):
        """绘制矩形"""
        if self._clip_rect and not self._clip_rect.intersects(rect):
            return  # 被裁剪，跳过

        path = Path()
        path.add_rect(rect)
        self._draw_commands.append({
            "type": "draw_rect",
            "rect": rect.to_dict(),
            "paint": paint.to_dict(),
        })

    def draw_circle(self, cx: float, cy: float, radius: float, paint: Paint):
        """绘制圆形"""
        rect = Rect(cx - radius, cy - radius, cx + radius, cy + radius)
        path = Path()
        path.add_oval(rect)
        self._draw_commands.append({
            "type": "draw_circle",
            "center": {"x": cx, "y": cy},
            "radius": radius,
            "paint": paint.to_dict(),
        })

    def draw_path(self, path: Path, paint: Paint):
        """绘制路径"""
        self._draw_commands.append({
            "type": "draw_path",
            "path": path.to_dict(),
            "paint": paint.to_dict(),
        })

    def draw_text(self, text: str, x: float, y: float,
                  paint: Paint, font_size: float = 16.0):
        """绘制文本"""
        self._draw_commands.append({
            "type": "draw_text",
            "text": text,
            "position": {"x": x, "y": y},
            "font_size": font_size,
            "paint": paint.to_dict(),
        })

    def draw_line(self, p1: Offset, p2: Offset, paint: Paint):
        """绘制直线"""
        self._draw_commands.append({
            "type": "draw_line",
            "start": {"x": p1.dx, "y": p1.dy},
            "end": {"x": p2.dx, "y": p2.dy},
            "paint": paint.to_dict(),
        })

    def clear(self, color: Color = Colors.TRANSPARENT):
        """清除画布"""
        self._draw_commands.append({
            "type": "clear",
            "color": color.to_hex(),
        })

    def get_scene(self) -> 'Scene':
        """获取渲染场景"""
        return Scene(self._draw_commands.copy(), (self._width, self._height))

    def _identity_matrix(self) -> List[List[float]]:
        return [[1, 0, 0], [0, 1, 0], [0, 0, 1]]

    def _multiply_matrix(self, a: List[List[float]],
                         b: List[List[float]]) -> List[List[float]]:
        """矩阵乘法（变换矩阵组合）"""
        result = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    result[i][j] += a[i][k] * b[k][j]
        return result


# ============================================================
# 渲染场景 (Scene)
# ============================================================
class Scene:
    """
    渲染场景

    Scene 是 Canvas 上所有绘制操作的最终结果。
    在 Flutter 中，Scene 会被发送到 GPU 进行光栅化。

    渲染管线：
    1. Widget 树 → Render 树
    2. Render 对象 → Scene（绘制命令）
    3. Scene → GPU Scene（光栅化）
    4. GPU Scene → Display（合成）
    """

    def __init__(self, commands: List[Dict[str, Any]], size: Tuple[float, float]):
        self._commands = commands
        self._size = size
        self._timestamp = time.time()

    @property
    def commands(self) -> List[Dict[str, Any]]:
        return self._commands

    @property
    def size(self) -> Tuple[float, float]:
        return self._size

    @property
    def command_count(self) -> int:
        return len(self._commands)

    @property
    def timestamp(self) -> float:
        return self._timestamp

    def summary(self) -> Dict[str, Any]:
        """生成场景摘要"""
        type_counts = {}
        for cmd in self._commands:
            t = cmd['type']
            type_counts[t] = type_counts.get(t, 0) + 1

        return {
            "size": self._size,
            "command_count": self.command_count,
            "command_types": type_counts,
            "timestamp": self._timestamp,
        }

    def __repr__(self):
        return f"Scene(size={self._size}, commands={self.command_count})"

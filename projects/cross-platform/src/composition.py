"""
跨平台框架原理 - Cross-Platform Framework Principles

核心模块：Composition Layer（合成图层）
功能：模拟 Flutter 的图层合成和渲染管线

跨平台框架原理说明：
Flutter 的渲染管线：
1. Widget 树 → Element 树 → Render 树
2. Render 对象 → Scene（绘制命令）
3. Scene → GPU Scene（光栅化）
4. GPU Scene → Display（合成显示）

图层合成（Layer Compositing）是渲染管线的关键步骤：
- 每个 RenderObject 可能对应一个或多个 Layer
- Layer 树定义了绘制的层次关系
- 合成器（Compositor）将 Layer 树转换为 GPU 命令
- GPU 执行光栅化并输出到屏幕

本模块模拟：
1. Layer 树构建
2. Layer 合成
3. GPU 命令生成
4. 帧渲染
"""

from typing import Any, Dict, List, Optional, Tuple
import time

from .rendering_engine import (
    Color, Colors, Rect, Offset, Paint, FillStyle,
    BlendMode, Canvas, Scene, Layer, LayerType
)


# ============================================================
# 合成图层类型 (Compositing Layer Types)
# ============================================================
class CompositingLayerType:
    """合成图层类型"""
    # 基础图层
    BITMAP = "bitmap"           # 位图图层（离屏缓存）
    GL = "gl"                   # OpenGL 图层（GPU 加速）
    
    # 变换图层
    TRANSFORM = "transform"     # 变换图层（用于动画）
    
    # 裁剪图层
    CLIP = "clip"               # 裁剪图层
    
    # 混合图层
    SAVE_LAYER = "save_layer"   # 保存图层（离屏渲染+混合）
    
    # 特殊图层
    RASTER_CACHE = "raster_cache"  # 光栅缓存（缓存渲染结果）
    OPACITY = "opacity"         # 透明度图层
    PHYSICAL_MODEL = "physical_model"  # 物理模型（阴影、圆角）


# ============================================================
# 光栅缓存 (RasterCache)
# ============================================================
class RasterCache:
    """
    光栅缓存

    RasterCache 缓存已光栅化的图层，避免重复渲染。
    对于频繁动画的元素特别有用。

    在 Flutter 中：
    - 当 Widget 的 isComplex 或 willChange 属性为 true 时
    - Flutter 会自动将其缓存到 RasterCache
    - 动画时直接复用缓存的位图
    """

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._hit_count = 0
        self._miss_count = 0

    def cache(self, key: str, layer: Layer, bounds: Rect):
        """缓存图层"""
        self._cache[key] = {
            "layer": layer.to_dict(),
            "bounds": bounds.to_dict(),
            "timestamp": layer._saved,
        }

    def get(self, key: str) -> Optional[Dict]:
        """获取缓存的图层"""
        if key in self._cache:
            self._hit_count += 1
            return self._cache[key]
        self._miss_count += 1
        return None

    @property
    def stats(self) -> Dict[str, int]:
        total = self._hit_count + self._miss_count
        hit_rate = (self._hit_count / total * 100) if total > 0 else 0
        return {
            "cache_size": len(self._cache),
            "hits": self._hit_count,
            "misses": self._miss_count,
            "hit_rate": round(hit_rate, 2),
        }


# ============================================================
# 图层合成器 (LayerCompositor)
# ============================================================
class LayerCompositor:
    """
    图层合成器

    LayerCompositor 负责将 Layer 树转换为 GPU 可执行的命令。
    这是 Flutter 渲染管线的核心组件。

    合成过程：
    1. 遍历 Layer 树
    2. 为每个图层分配 GPU 资源
    3. 生成绘制命令序列
    4. 发送到 GPU 执行
    """

    def __init__(self):
        self._gpu_commands: List[Dict[str, Any]] = []
        self._layer_count = 0
        self._frame_count = 0

    def composite(self, root_layer: Layer, canvas: Canvas) -> Scene:
        """
        合成图层树

        Args:
            root_layer: 根图层
            canvas: 目标画布

        Returns:
            渲染场景
        """
        self._gpu_commands = []
        self._frame_count += 1

        # 递归合成每个图层
        self._composite_layer(root_layer, canvas, Offset(0, 0))

        return canvas.get_scene()

    def _composite_layer(self, layer: Layer, canvas: Canvas,
                         parent_offset: Offset):
        """递归合成单个图层"""
        self._layer_count += 1

        if layer.type == LayerType.SAVE_LAYER:
            # 离屏渲染
            bounds = Rect(0, 0, 100, 100)  # 简化
            layer.save_layer(bounds, layer._paint)
            
            # 在离屏 Canvas 上绘制
            offscreen = Canvas(bounds.width, bounds.height)
            for child in layer.children:
                self._composite_layer(child, offscreen, parent_offset)
            
            # 将离屏结果绘制到主 Canvas
            paint = Paint()
            paint.color = Colors.WHITE.with_alpha(200) if layer._paint else Colors.WHITE
            canvas.draw_rect(bounds, paint)
            
            layer.restore()

        elif layer.type == LayerType.CLIP:
            # 裁剪
            if layer._bounds:
                canvas.clip_rect(layer._bounds)
            for child in layer.children:
                self._composite_layer(child, canvas, parent_offset)
            canvas.restore()

        else:
            # 普通图层组
            for child in layer.children:
                self._composite_layer(child, canvas, parent_offset)

        # 记录 GPU 命令
        self._gpu_commands.append({
            "layer_type": layer.type.value,
            "children": len(layer.children),
        })

    @property
    def gpu_commands(self) -> List[Dict[str, Any]]:
        return self._gpu_commands.copy()

    @property
    def stats(self) -> Dict[str, int]:
        return {
            "layers_composited": self._layer_count,
            "frames_rendered": self._frame_count,
            "gpu_command_count": len(self._gpu_commands),
        }


# ============================================================
# 帧渲染器 (FrameRenderer)
# ============================================================
class FrameRenderer:
    """
    帧渲染器

    FrameRenderer 管理整个渲染帧的生成。
    在 Flutter 中，每帧大约需要 16.67ms（60fps）或 8.33ms（120fps）。

    帧生命周期：
    1. Begin frame - 开始新帧
    2. Build phase - 构建 Widget/Element 树
    3. Layout phase - 执行布局
    4. Paint phase - 执行绘制
    5. Compositing phase - 图层合成
    6. Raster phase - 光栅化
    7. Send phase - 发送到 GPU
    8. End frame - 完成帧
    """

    def __init__(self):
        self._frames: List[Dict[str, Any]] = []
        self._fps_history: List[float] = []
        self._current_frame_start = 0.0

    def begin_frame(self):
        """开始新帧"""
        self._current_frame_start = time.time()

    def end_frame(self, frame_info: Dict[str, Any]):
        """完成帧"""
        elapsed = (time.time() - self._current_frame_start) * 1000  # ms
        fps = 1000 / elapsed if elapsed > 0 else 0

        frame = {
            **frame_info,
            "elapsed_ms": round(elapsed, 2),
            "fps": round(fps, 2),
            "timestamp": time.time(),
        }
        self._frames.append(frame)
        self._fps_history.append(fps)

        # 保持最近 60 帧的历史
        if len(self._fps_history) > 60:
            self._fps_history.pop(0)

    def get_average_fps(self) -> float:
        """获取平均 FPS"""
        if not self._fps_history:
            return 0
        return sum(self._fps_history) / len(self._fps_history)

    def get_frame_history(self) -> List[Dict[str, Any]]:
        return self._frames.copy()

    def get_stats(self) -> Dict[str, Any]:
        """获取帧统计"""
        return {
            "total_frames": len(self._frames),
            "average_fps": round(self.get_average_fps(), 2),
            "min_fps": round(min(self._fps_history), 2) if self._fps_history else 0,
            "max_fps": round(max(self._fps_history), 2) if self._fps_history else 0,
        }


# ============================================================
# 渲染管线 (RenderingPipeline)
# ============================================================
class RenderingPipeline:
    """
    渲染管线

    模拟 Flutter 的完整渲染管线：
    Widget → Element → Render → Scene → GPU → Display

    这是跨平台框架的核心原理：
    1. 跨平台 UI 描述（Widget 树）
    2. 统一渲染引擎（Skia）
    3. 原生平台输出（GPU/Display）
    """

    def __init__(self):
        self._compositor = LayerCompositor()
        self._frame_renderer = FrameRenderer()
        self._raster_cache = RasterCache()
        self._pipeline_log: List[str] = []

    def log(self, message: str):
        self._pipeline_log.append(message)

    def render(self, root_layer: Layer, canvas_size: Tuple[float, float] = (800, 600)) -> Scene:
        """
        执行完整渲染管线

        Args:
            root_layer: 根图层
            canvas_size: 画布尺寸

        Returns:
            渲染场景
        """
        self._frame_renderer.begin_frame()
        self.log("开始渲染帧")

        # Phase 1: 创建画布
        canvas = Canvas(canvas_size[0], canvas_size[1])
        canvas.clear(Colors.BACKGROUND)
        self.log(f"Phase 1: 画布创建 {canvas_size[0]}x{canvas_size[1]}")

        # Phase 2: 图层合成
        scene = self._compositor.composite(root_layer, canvas)
        self.log(f"Phase 2: 图层合成完成，图层数={self._compositor.stats['layers_composited']}")

        # Phase 3: 获取场景
        self.log(f"Phase 3: 场景生成，命令数={scene.command_count}")

        # Phase 4: 完成帧
        frame_info = {
            "layers": self._compositor.stats['layers_composited'],
            "commands": scene.command_count,
        }
        self._frame_renderer.end_frame(frame_info)
        self.log(f"Phase 4: 帧完成，FPS={self._frame_renderer.get_average_fps()}")

        return scene

    @property
    def pipeline_log(self) -> List[str]:
        return self._pipeline_log.copy()

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "compositor": self._compositor.stats,
            "frame_renderer": self._frame_renderer.get_stats(),
            "raster_cache": self._raster_cache.stats,
        }

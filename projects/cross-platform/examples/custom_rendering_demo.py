"""
示例 3: 自定义渲染演示
演示 Skia 渲染引擎的核心功能

跨平台原理：
Flutter 使用 Skia 图形引擎渲染 UI。
与原生 UI 框架不同，Flutter 不依赖原生控件，
而是直接通过 Skia 绘制所有像素。

渲染管线：
1. 创建 Canvas（画布）
2. 设置 Paint（画笔）
3. 定义 Path（路径）
4. 执行绘制命令
5. 生成 Scene（场景）
6. 发送到 GPU 光栅化
"""

import sys
import os
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rendering_engine import (
    Color, Colors, Rect, Offset, Paint, FillStyle,
    BlendMode, Canvas, Scene, Path, Layer, LayerType
)
from src.composition import (
    RenderingPipeline, RasterCache, FrameRenderer
)


def demo():
    """自定义渲染演示"""
    print("=" * 60)
    print("自定义渲染 (Custom Rendering) 演示")
    print("Skia Rendering Engine Demo")
    print("=" * 60)

    # 1. 颜色系统
    print("\n1. 颜色系统 (Color System)")
    print("-" * 40)

    # 创建颜色
    red = Color(244, 67, 54)
    blue = Color(33, 150, 243)
    green = Color(76, 175, 80)

    print(f"红色: {red.to_hex()}")
    print(f"蓝色: {blue.to_hex()}")
    print(f"绿色: {green.to_hex()}")

    # 颜色插值（用于动画）
    t = 0.5
    gradient = red.lerp(blue, t)
    print(f"红→蓝 插值 (t={t}): {gradient.to_hex()}")

    # 透明度
    semi_transparent = Colors.BLUE.with_alpha(128)
    print(f"半透明蓝色: {semi_transparent.to_hex()}")

    # 2. 绘制基本形状
    print("\n2. 绘制基本形状")
    print("-" * 40)

    canvas = Canvas(800, 600)
    canvas.clear(Colors.BACKGROUND)

    # 绘制矩形
    rect_paint = Paint()
    rect_paint.color = Colors.BLUE
    rect_paint.fill_style = FillStyle.FILL
    canvas.draw_rect(Rect(50, 50, 200, 150), rect_paint)

    # 绘制圆形
    circle_paint = Paint()
    circle_paint.color = Colors.RED
    circle_paint.fill_style = FillStyle.FILL
    canvas.draw_circle(400, 150, 60, circle_paint)

    # 绘制椭圆
    oval_paint = Paint()
    oval_paint.color = Colors.GREEN
    oval_paint.fill_style = FillStyle.FILL
    oval_path = Path()
    oval_path.add_oval(Rect(550, 80, 750, 220))
    canvas.draw_path(oval_path, oval_paint)

    # 绘制直线
    line_paint = Paint()
    line_paint.color = Colors.BLACK
    line_paint.stroke_width = 2.0
    canvas.draw_line(Offset(50, 300), Offset(750, 300), line_paint)

    # 绘制多条线（波浪效果）
    wave_paint = Paint()
    wave_paint.color = Colors.PRIMARY
    wave_paint.stroke_width = 3.0
    for i in range(5):
        y = 320 + i * 40
        start_x = 50 + i * 20
        end_x = 750 - i * 20
        canvas.draw_line(Offset(start_x, y), Offset(end_x, y), wave_paint)

    # 绘制文本
    text_paint = Paint()
    text_paint.color = Colors.BLACK
    canvas.draw_text("Flutter Skia Engine", 250, 450, text_paint, font_size=24)
    canvas.draw_text("Cross-Platform Rendering", 220, 490, text_paint, font_size=16)

    scene = canvas.get_scene()
    summary = scene.summary()
    print(f"画布大小: {canvas.size[0]} x {canvas.size[1]}")
    print(f"绘制命令: {summary['command_types']}")
    print(f"像素尺寸: {canvas.pixel_size[0]} x {canvas.pixel_size[1]} (DPI: {canvas._dpi}x)")

    # 3. 路径绘制
    print("\n3. 路径绘制 (Path Drawing)")
    print("-" * 40)

    path_canvas = Canvas(800, 400)
    path_canvas.clear(Colors.BACKGROUND)

    # 创建自定义路径
    star_path = Path()
    cx, cy, outer_r, inner_r = 400, 200, 100, 40
    points = []
    for i in range(10):
        angle = math.radians(i * 36 - 90)
        r = outer_r if i % 2 == 0 else inner_r
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        if i == 0:
            star_path.move_to(x, y)
        else:
            star_path.line_to(x, y)
    star_path.close()

    star_paint = Paint()
    star_paint.color = Color(255, 193, 7)
    star_paint.fill_style = FillStyle.FILL
    path_canvas.draw_path(star_path, star_paint)

    # 绘制多边形
    poly_path = Path()
    poly_path.move_to(200, 100)
    poly_path.line_to(300, 300)
    poly_path.line_to(100, 300)
    poly_path.close()

    poly_paint = Paint()
    poly_paint.color = Color(156, 39, 176)
    poly_paint.fill_style = FillStyle.FILL
    path_canvas.draw_path(poly_path, poly_paint)

    # 绘制三角形
    tri_path = Path()
    tri_path.move_to(600, 100)
    tri_path.line_to(700, 300)
    tri_path.line_to(500, 300)
    tri_path.close()

    tri_paint = Paint()
    tri_paint.color = Color(63, 81, 181)
    tri_paint.fill_style = FillStyle.FILL
    path_canvas.draw_path(tri_path, tri_paint)

    path_scene = path_canvas.get_scene()
    print(f"路径命令数: {path_scene.command_count}")
    print(f"星形路径: {star_path.to_dict()}")

    # 4. 图层合成
    print("\n4. 图层合成 (Layer Compositing)")
    print("-" * 40)

    # 创建图层树
    root_layer = Layer(LayerType.GROUP)

    # 背景层
    bg_layer = Layer(LayerType.SAVE_LAYER)
    bg_paint = Paint()
    bg_paint.color = Colors.WHITE
    bg_layer.save_layer(Rect(0, 0, 800, 600), bg_paint)
    root_layer.add_child(bg_layer)

    # 内容层
    content_layer = Layer(LayerType.GROUP)
    content_layer.add_child(Layer(LayerType.GROUP))
    content_layer.add_child(Layer(LayerType.GROUP))
    root_layer.add_child(content_layer)

    # 叠加层
    overlay_layer = Layer(LayerType.SAVE_LAYER)
    overlay_paint = Paint()
    overlay_paint.color = Colors.BLUE.with_alpha(30)
    overlay_layer.save_layer(Rect(0, 500, 800, 600), overlay_paint)
    root_layer.add_child(overlay_layer)

    # 5. 渲染管线
    print("\n5. 渲染管线 (Rendering Pipeline)")
    print("-" * 40)

    pipeline = RenderingPipeline()
    scene = pipeline.render(root_layer, (800, 600))

    print(f"渲染管线日志:")
    for log in pipeline.pipeline_log:
        print(f"  {log}")

    print(f"\n渲染统计:")
    stats = pipeline.stats
    print(f"  合成器: {stats['compositor']}")
    print(f"  帧渲染: {stats['frame_renderer']}")
    print(f"  光栅缓存: {stats['raster_cache']}")

    # 6. 光栅缓存
    print("\n6. 光栅缓存 (RasterCache)")
    print("-" * 40)

    cache = RasterCache()
    test_layer = Layer(LayerType.GROUP)
    test_layer.add_child(Layer(LayerType.GROUP))

    cache.cache("widget_1", test_layer, Rect(0, 0, 100, 100))
    cache.cache("widget_2", test_layer, Rect(100, 0, 200, 100))

    hit = cache.get("widget_1")
    miss = cache.get("widget_3")  # 不存在的 key

    print(f"缓存命中: {hit is not None}")
    print(f"缓存未命中: {miss is None}")
    print(f"缓存统计: {cache.stats}")

    print("\n" + "=" * 60)
    print("演示完成！")
    print("Key concept: Flutter 使用 Skia 引擎直接渲染所有 UI，")
    print("不依赖原生控件，实现跨平台一致性。")
    print("=" * 60)


if __name__ == "__main__":
    demo()

"""
跨平台框架原理 - 测试套件
测试渲染引擎核心功能
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rendering_engine import (
    Color, Colors, Paint, FillStyle, BlendMode,
    Rect, Offset, Path, Canvas, Scene, Layer, LayerType
)


class TestColor(unittest.TestCase):
    """测试颜色系统"""

    def test_create_color(self):
        """测试创建颜色"""
        c = Color(255, 128, 64, 200)
        self.assertEqual(c.r, 255)
        self.assertEqual(c.g, 128)
        self.assertEqual(c.b, 64)
        self.assertEqual(c.a, 200)

    def test_clamping(self):
        """测试颜色值钳位"""
        c = Color(300, -10, 128)
        self.assertEqual(c.r, 255)
        self.assertEqual(c.g, 0)

    def test_with_alpha(self):
        """测试设置透明度"""
        c = Color(255, 0, 0).with_alpha(128)
        self.assertEqual(c.a, 128)
        self.assertEqual(c.r, 255)

    def test_lerp(self):
        """测试颜色插值"""
        c1 = Color(255, 0, 0)
        c2 = Color(0, 0, 255)
        mid = c1.lerp(c2, 0.5)
        self.assertAlmostEqual(mid.r, 127)
        self.assertAlmostEqual(mid.b, 127)

    def test_lerp_t_range(self):
        """测试插值 t 范围边界"""
        c1 = Color(255, 0, 0)
        c2 = Color(0, 0, 255)
        c_min = c1.lerp(c2, -1.0)
        c_max = c1.lerp(c2, 2.0)
        self.assertEqual(c_min.r, 255)
        self.assertEqual(c_max.b, 255)

    def test_to_hex(self):
        """测试十六进制转换"""
        c = Color(255, 0, 0, 255)
        self.assertEqual(c.to_hex(), "#ff0000ff")

    def test_equality(self):
        """测试颜色相等性"""
        c1 = Color(255, 0, 0)
        c2 = Color(255, 0, 0)
        c3 = Color(0, 0, 0)
        self.assertEqual(c1, c2)
        self.assertNotEqual(c1, c3)

    def test_predefined_colors(self):
        """测试预定义颜色"""
        self.assertEqual(Colors.BLACK.to_hex(), "#000000ff")
        self.assertEqual(Colors.WHITE.to_hex(), "#ffffffff")
        self.assertEqual(Colors.TRANSPARENT.a, 0)


class TestPaint(unittest.TestCase):
    """测试画笔"""

    def test_create_paint(self):
        """测试创建画笔"""
        p = Paint()
        self.assertEqual(p.color, Colors.WHITE)
        self.assertEqual(p.fill_style, FillStyle.FILL)
        self.assertEqual(p.stroke_width, 1.0)

    def test_set_color(self):
        """测试设置颜色"""
        p = Paint()
        p.color = Colors.RED
        self.assertEqual(p.color, Colors.RED)

    def test_set_fill_style(self):
        """测试设置填充样式"""
        p = Paint()
        p.fill_style = FillStyle.STROKE
        self.assertEqual(p.fill_style, FillStyle.STROKE)

    def test_with_color(self):
        """测试返回带新颜色的副本"""
        p = Paint()
        p2 = p.with_color(Colors.RED)
        self.assertEqual(p2.color, Colors.RED)
        self.assertNotEqual(p, p2)

    def test_to_dict(self):
        """测试序列化"""
        p = Paint()
        d = p.to_dict()
        self.assertIn("color", d)
        self.assertIn("fill_style", d)
        self.assertIn("stroke_width", d)


class TestRect(unittest.TestCase):
    """测试矩形"""

    def test_create_rect(self):
        """测试创建矩形"""
        r = Rect(10, 20, 100, 200)
        self.assertEqual(r.left, 10)
        self.assertEqual(r.top, 20)
        self.assertEqual(r.right, 100)
        self.assertEqual(r.bottom, 200)

    def test_dimensions(self):
        """测试尺寸计算"""
        r = Rect(0, 0, 100, 50)
        self.assertEqual(r.width, 100)
        self.assertEqual(r.height, 50)

    def test_center(self):
        """测试中心点计算"""
        r = Rect(0, 0, 100, 100)
        self.assertEqual(r.center_x, 50)
        self.assertEqual(r.center_y, 50)

    def test_centered_at(self):
        """测试居中创建"""
        r = Rect(0, 0, 100, 100).centered_at(200, 200)
        self.assertEqual(r.center_x, 200)
        self.assertEqual(r.center_y, 200)

    def test_intersects(self):
        """测试相交检测"""
        r1 = Rect(0, 0, 100, 100)
        r2 = Rect(50, 50, 150, 150)
        r3 = Rect(200, 200, 300, 300)
        self.assertTrue(r1.intersects(r2))
        self.assertFalse(r1.intersects(r3))

    def test_expanded(self):
        """测试扩展"""
        r = Rect(0, 0, 100, 100).expanded(10, 10)
        self.assertEqual(r.left, -10)
        self.assertEqual(r.right, 110)

    def test_from_sizes(self):
        """测试从尺寸创建"""
        r = Rect.from_sizes(0, 0, 100, 200)
        self.assertEqual(r.width, 100)
        self.assertEqual(r.height, 200)

    def test_to_dict(self):
        """测试序列化"""
        r = Rect(0, 0, 100, 50)
        d = r.to_dict()
        self.assertEqual(d["width"], 100)
        self.assertEqual(d["height"], 50)


class TestOffset(unittest.TestCase):
    """测试偏移量"""

    def test_create_offset(self):
        """测试创建偏移量"""
        o = Offset(10, 20)
        self.assertEqual(o.dx, 10)
        self.assertEqual(o.dy, 20)

    def test_distance_to(self):
        """测试距离计算"""
        o1 = Offset(0, 0)
        o2 = Offset(3, 4)
        self.assertAlmostEqual(o1.distance_to(o2), 5.0)

    def test_lerp(self):
        """测试线性插值"""
        o1 = Offset(0, 0)
        o2 = Offset(10, 10)
        mid = o1.lerp(o2, 0.5)
        self.assertAlmostEqual(mid.dx, 5.0)
        self.assertAlmostEqual(mid.dy, 5.0)

    def test_addition(self):
        """测试加法"""
        o1 = Offset(1, 2)
        o2 = Offset(3, 4)
        result = o1 + o2
        self.assertEqual(result.dx, 4)
        self.assertEqual(result.dy, 6)


class TestPath(unittest.TestCase):
    """测试路径"""

    def test_move_and_line(self):
        """测试移动和直线"""
        p = Path()
        p.move_to(0, 0).line_to(100, 100)
        self.assertEqual(p.to_dict()["commands"], 2)

    def test_add_rect(self):
        """测试添加矩形"""
        p = Path()
        rect = Rect(0, 0, 100, 50)
        p.add_rect(rect)
        self.assertEqual(p.to_dict()["subpaths"], 1)

    def test_add_circle(self):
        """测试添加圆形"""
        p = Path()
        p.add_circle(50, 50, 25)
        self.assertEqual(p.to_dict()["subpaths"], 1)

    def test_add_oval(self):
        """测试添加椭圆"""
        p = Path()
        p.add_oval(Rect(0, 0, 100, 50))
        self.assertEqual(p.to_dict()["subpaths"], 1)

    def test_close(self):
        """测试闭合路径"""
        p = Path()
        p.move_to(0, 0).line_to(100, 0).line_to(50, 100).close()
        d = p.to_dict()
        self.assertEqual(d["subpaths"], 1)
        self.assertEqual(d["commands"], 4)

    def test_bounds(self):
        """测试边界计算"""
        p = Path()
        p.add_rect(Rect(10, 20, 100, 200))
        bounds = p.compute_bounds()
        self.assertEqual(bounds.left, 10)
        self.assertEqual(bounds.top, 20)
        self.assertEqual(bounds.right, 100)
        self.assertEqual(bounds.bottom, 200)

    def test_repr(self):
        """测试字符串表示"""
        p = Path()
        self.assertIn("Path", repr(p))


class TestCanvas(unittest.TestCase):
    """测试画布"""

    def test_create_canvas(self):
        """测试创建画布"""
        c = Canvas(800, 600)
        self.assertEqual(c.size, (800, 600))

    def test_pixel_size(self):
        """测试像素尺寸计算"""
        c = Canvas(800, 600)
        expected = (2400, 1800)  # 800*3, 600*3
        self.assertEqual(c.pixel_size, expected)

    def test_draw_rect(self):
        """测试绘制矩形"""
        c = Canvas(800, 600)
        paint = Paint()
        paint.color = Colors.RED
        c.draw_rect(Rect(0, 0, 100, 100), paint)
        commands = c.draw_commands
        self.assertTrue(any(cmd['type'] == 'draw_rect' for cmd in commands))

    def test_draw_circle(self):
        """测试绘制圆形"""
        c = Canvas(800, 600)
        paint = Paint()
        paint.color = Colors.BLUE
        c.draw_circle(100, 100, 50, paint)
        commands = c.draw_commands
        self.assertTrue(any(cmd['type'] == 'draw_circle' for cmd in commands))

    def test_draw_text(self):
        """测试绘制文本"""
        c = Canvas(800, 600)
        paint = Paint()
        c.draw_text("Hello", 10, 20, paint, 16)
        commands = c.draw_commands
        self.assertTrue(any(cmd['type'] == 'draw_text' for cmd in commands))

    def test_clear(self):
        """测试清除画布"""
        c = Canvas(800, 600)
        c.clear(Colors.TRANSPARENT)
        commands = c.draw_commands
        self.assertTrue(any(cmd['type'] == 'clear' for cmd in commands))

    def test_get_scene(self):
        """测试获取场景"""
        c = Canvas(800, 600)
        scene = c.get_scene()
        self.assertEqual(scene.size, (800, 600))
        self.assertIsInstance(scene, Scene)

    def test_translate(self):
        """测试平移变换"""
        c = Canvas(800, 600)
        c.translate(10, 20)
        self.assertEqual(c._transform[0][2], 10)
        self.assertEqual(c._transform[1][2], 20)

    def test_scale(self):
        """测试缩放变换"""
        c = Canvas(800, 600)
        c.scale(2, 2)
        self.assertAlmostEqual(c._transform[0][0], 2.0)
        self.assertAlmostEqual(c._transform[1][1], 2.0)

    def test_rotate(self):
        """测试旋转变换"""
        c = Canvas(800, 600)
        c.rotate(90)
        # 90度旋转：cos=0, sin=1
        self.assertAlmostEqual(c._transform[0][0], 0.0, places=5)
        self.assertAlmostEqual(c._transform[0][1], 1.0, places=5)


class TestScene(unittest.TestCase):
    """测试渲染场景"""

    def test_create_scene(self):
        """测试创建场景"""
        commands = [{"type": "draw_rect"}]
        scene = Scene(commands, (800, 600))
        self.assertEqual(scene.size, (800, 600))
        self.assertEqual(scene.command_count, 1)

    def test_summary(self):
        """测试场景摘要"""
        commands = [
            {"type": "draw_rect"},
            {"type": "draw_rect"},
            {"type": "draw_text"},
        ]
        scene = Scene(commands, (800, 600))
        summary = scene.summary()
        self.assertEqual(summary["command_count"], 3)
        self.assertEqual(summary["command_types"]["draw_rect"], 2)
        self.assertEqual(summary["command_types"]["draw_text"], 1)


class TestLayer(unittest.TestCase):
    """测试图层"""

    def test_create_layer(self):
        """测试创建图层"""
        layer = Layer(LayerType.GROUP)
        self.assertEqual(layer.type, LayerType.GROUP)

    def test_add_child(self):
        """测试添加子图层"""
        parent = Layer(LayerType.GROUP)
        child = Layer(LayerType.GROUP)
        parent.add_child(child)
        self.assertEqual(len(parent.children), 1)

    def test_save_and_restore(self):
        """测试保存和恢复"""
        layer = Layer(LayerType.SAVE_LAYER)
        layer.save_layer(Rect(0, 0, 100, 100))
        self.assertTrue(layer._saved)
        layer.restore()
        self.assertFalse(layer._saved)

    def test_to_dict(self):
        """测试序列化"""
        layer = Layer(LayerType.GROUP)
        d = layer.to_dict()
        self.assertEqual(d["type"], "group")
        self.assertIn("children", d)


if __name__ == "__main__":
    unittest.main()

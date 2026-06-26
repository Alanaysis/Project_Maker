"""
跨平台框架原理 - 测试套件
测试 Widget 树、布局引擎和平台通道
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.widget_tree import (
    Widget, StatelessWidget, StatelessElement, StatefulElement,
    Element, RenderObject, RenderBox, RenderStack, RenderFlex,
    RenderObjectType
)
from src.layout_engine import (
    BoxConstraints, LayoutEngine, LayoutResult,
    LayoutStrategy, BoxLayoutStrategy, FlexLayoutStrategy,
    StackLayoutStrategy, LayoutDebugger
)
from src.platform_channel import (
    MethodChannel, EventChannel, BasicMessageChannel,
    PlatformChannelManager, StandardCodec, PlatformType
)
from src.rendering_engine import (
    Color, Colors, Rect, Offset, Paint, FillStyle
)
from src.composition import (
    LayerCompositor, FrameRenderer, RenderingPipeline,
    RasterCache, CompositingLayerType
)
from src.rendering_engine import Layer, LayerType


class TestWidgetTree(unittest.TestCase):
    """测试 Widget 树"""

    def test_create_widget(self):
        """测试创建 Widget"""
        w = StatelessWidget(key="test")
        self.assertEqual(w.key, "test")
        self.assertEqual(len(w.children), 0)

    def test_add_child(self):
        """测试添加子 Widget"""
        parent = StatelessWidget(key="parent")
        child = StatelessWidget(key="child")
        parent.append_child(child)
        self.assertEqual(len(parent.children), 1)

    def test_build_element(self):
        """测试构建 Element 树"""
        w = StatelessWidget(key="test")
        element = w.build()
        self.assertTrue(element.is_mounted)

    def test_element_tree_structure(self):
        """测试 Element 树结构"""
        parent = StatelessWidget(key="parent")
        child1 = StatelessWidget(key="child1")
        child2 = StatelessWidget(key="child2")
        parent.append_child(child1)
        parent.append_child(child2)

        element = parent.build()
        self.assertEqual(len(element.children), 2)

    def test_get_descendants(self):
        """测试获取后代"""
        grandchild = StatelessWidget(key="grandchild")
        child = StatelessWidget(key="child")
        parent = StatelessWidget(key="parent")
        child.append_child(grandchild)
        parent.append_child(child)

        element = parent.build()
        descendants = element.get_descendants()
        self.assertEqual(len(descendants), 2)

    def test_unmount(self):
        """测试卸载"""
        w = StatelessWidget(key="test")
        element = w.build()
        element.unmount()
        self.assertFalse(element.is_mounted)

    def test_to_dict(self):
        """测试序列化"""
        w = StatelessWidget(key="test")
        d = w.to_dict()
        self.assertEqual(d["type"], "stateless")
        self.assertEqual(d["key"], "test")

    def test_render_box(self):
        """测试 RenderBox"""
        box = RenderBox()
        box.mount()
        self.assertTrue(box._mounted)

    def test_render_box_layout(self):
        """测试 RenderBox 布局"""
        box = RenderBox()
        constraints = Rect(0, 0, 800, 600)
        box.layout(constraints)
        self.assertIsNotNone(box.size)

    def test_render_stack(self):
        """测试 RenderStack"""
        stack = RenderStack()
        stack.layout(Rect(0, 0, 400, 300))
        self.assertIsNotNone(stack.size)


class TestBoxConstraints(unittest.TestCase):
    """测试 BoxConstraints"""

    def test_default_constraints(self):
        """测试默认约束"""
        c = BoxConstraints()
        self.assertEqual(c.min_width, 0)
        self.assertEqual(c.max_width, float('inf'))

    def test_unconstrained(self):
        """测试无约束检测"""
        c = BoxConstraints()
        self.assertTrue(c.is_unconstrained)

    def test_tight(self):
        """测试固定大小检测"""
        c = BoxConstraints(100, 100, 50, 50)
        self.assertTrue(c.is_tight)

    def test_enforce(self):
        """测试强制执行"""
        c = BoxConstraints(0, 100, 0, 200)
        size = Rect(0, 0, 150, 300)
        enforced = c.enforce(size)
        self.assertEqual(enforced.width, 100)
        self.assertEqual(enforced.height, 200)

    def test_expand(self):
        """测试 expand"""
        c = BoxConstraints(0, 100, 0, 200)
        expanded = c.expand()
        self.assertTrue(expanded.is_unconstrained)

    def test_repr(self):
        """测试字符串表示"""
        c = BoxConstraints(0, 100, 0, 200)
        self.assertIn("100", repr(c))


class TestLayoutEngine(unittest.TestCase):
    """测试布局引擎"""

    def setUp(self):
        self.engine = LayoutEngine()

    def test_layout_basic(self):
        """测试基本布局"""
        widget = type('MockWidget', (), {
            'layout_type': 'box',
            'children': [],
            'preferred_size': Rect.from_sizes(0, 0, 100, 50)
        })()
        result = self.engine.layout(widget, (800, 600))
        self.assertIsNotNone(result.size)

    def test_layout_flex(self):
        """测试弹性布局"""
        widget = type('MockWidget', (), {
            'layout_type': 'flex',
            'direction': 'horizontal',
            'children': [],
            'preferred_size': None
        })()
        result = self.engine.layout(widget, (800, 600))
        self.assertIsNotNone(result.size)

    def test_layout_stack(self):
        """测试层叠布局"""
        widget = type('MockWidget', (), {
            'layout_type': 'stack',
            'children': [],
            'preferred_size': None
        })()
        result = self.engine.layout(widget, (400, 300))
        self.assertIsNotNone(result.size)

    def test_layout_log(self):
        """测试布局日志"""
        widget = type('MockWidget', (), {
            'layout_type': 'box',
            'children': [],
            'preferred_size': Rect.from_sizes(0, 0, 50, 50)
        })()
        self.engine.layout(widget, (800, 600))
        self.assertGreater(len(self.engine.layout_log), 0)

    def test_pass_count(self):
        """测试传递次数"""
        widget = type('MockWidget', (), {
            'layout_type': 'box',
            'children': [],
            'preferred_size': None
        })()
        self.engine.layout(widget, (800, 600))
        self.assertGreater(self.engine.pass_count, 0)


class TestLayoutDebugger(unittest.TestCase):
    """测试布局调试器"""

    def test_record_layout(self):
        """测试记录布局"""
        debugger = LayoutDebugger()
        c = BoxConstraints(0, 800, 0, 600)
        debugger.record_layout("Container", c, Rect.from_sizes(0, 0, 400, 300))
        self.assertEqual(len(debugger.get_tree()), 1)

    def test_to_text(self):
        """测试文本输出"""
        debugger = LayoutDebugger()
        c = BoxConstraints(0, 800, 0, 600)
        debugger.record_layout("Text", c, Rect.from_sizes(0, 0, 100, 30))
        text = debugger.to_text()
        self.assertIn("Text", text)

    def test_summary(self):
        """测试摘要"""
        debugger = LayoutDebugger()
        c = BoxConstraints(0, 800, 0, 600)
        debugger.record_layout("Widget1", c, Rect.from_sizes(0, 0, 100, 50))
        debugger.record_layout("Widget2", c, Rect.from_sizes(0, 0, 200, 100))
        summary = debugger.get_summary()
        self.assertEqual(summary["total_widgets"], 2)


class TestPlatformChannel(unittest.TestCase):
    """测试平台通道"""

    def test_method_channel_creation(self):
        """测试方法通道创建"""
        channel = MethodChannel("test_channel", PlatformType.ANDROID)
        self.assertEqual(channel.name, "test_channel")

    def test_method_channel_handler(self):
        """测试方法通道处理器"""
        channel = MethodChannel("test")
        called = []

        def handler(args):
            called.append(True)
            return {"result": "ok"}

        channel.register_handler("testMethod", handler)
        result = channel.invoke("testMethod")
        self.assertTrue(called)
        self.assertEqual(result["result"], "ok")

    def test_method_channel_not_found(self):
        """测试方法不存在"""
        channel = MethodChannel("test")
        result = channel.invoke("nonExistent")
        self.assertIn("error", result)

    def test_event_channel(self):
        """测试事件通道"""
        channel = EventChannel("location")
        events = []

        def listener(data, error):
            events.append(data)

        channel.add_listener(listener)
        channel.emit_event({"lat": 39.9, "lng": 116.4})
        self.assertEqual(len(events), 1)

    def test_basic_message_channel(self):
        """测试消息通道"""
        channel = BasicMessageChannel("messages")
        channel.send({"type": "test"})
        self.assertEqual(len(channel.get_message_queue()), 1)

    def test_platform_channel_manager(self):
        """测试平台通道管理器"""
        manager = PlatformChannelManager(PlatformType.IOS)
        mc = manager.register_method_channel("test")
        ec = manager.register_event_channel("events")
        self.assertIsNotNone(manager.get_method_channel("test"))
        self.assertIsNotNone(manager.get_event_channel("events"))

    def test_standard_codec_encode_decode(self):
        """测试编解码器"""
        codec = StandardCodec()
        data = {"key": "value", "num": 42, "list": [1, 2, 3]}
        encoded = codec.encode(data)
        decoded = codec.decode(encoded)
        self.assertEqual(decoded["key"], "value")
        self.assertEqual(decoded["num"], 42)
        self.assertEqual(decoded["list"], [1, 2, 3])

    def test_standard_codec_null(self):
        """测试 null 编解码"""
        codec = StandardCodec()
        encoded = codec.encode(None)
        decoded = codec.decode(encoded)
        self.assertIsNone(decoded)


class TestComposition(unittest.TestCase):
    """测试图层合成"""

    def test_layer_compositor(self):
        """测试图层合成器"""
        compositor = LayerCompositor()
        root = Layer(LayerType.GROUP)
        from src.rendering_engine import Canvas
        canvas = Canvas(800, 600)
        scene = compositor.composite(root, canvas)
        self.assertIsNotNone(scene)

    def test_frame_renderer(self):
        """测试帧渲染器"""
        renderer = FrameRenderer()
        renderer.begin_frame()
        renderer.end_frame({"test": True})
        stats = renderer.get_stats()
        self.assertEqual(stats["total_frames"], 1)

    def test_raster_cache(self):
        """测试光栅缓存"""
        cache = RasterCache()
        layer = Layer(LayerType.GROUP)
        cache.cache("key1", layer, Rect.from_sizes(0, 0, 100, 100))
        result = cache.get("key1")
        self.assertIsNotNone(result)
        self.assertEqual(cache.stats["hits"], 1)

    def test_rendering_pipeline(self):
        """测试渲染管线"""
        pipeline = RenderingPipeline()
        root = Layer(LayerType.GROUP)
        scene = pipeline.render(root, (800, 600))
        self.assertIsNotNone(scene)
        self.assertGreater(len(pipeline.pipeline_log), 0)

    def test_compositing_layer_types(self):
        """测试合成图层类型"""
        self.assertTrue(hasattr(CompositingLayerType, 'BITMAP'))
        self.assertTrue(hasattr(CompositingLayerType, 'GL'))
        self.assertTrue(hasattr(CompositingLayerType, 'TRANSFORM'))


class TestRenderFlex(unittest.TestCase):
    """测试 RenderFlex"""

    def test_horizontal_flex(self):
        """测试水平弹性布局"""
        flex = RenderFlex(direction="horizontal")
        flex.layout(Rect(0, 0, 800, 100))
        self.assertIsNotNone(flex.size)

    def test_vertical_flex(self):
        """测试垂直弹性布局"""
        flex = RenderFlex(direction="vertical")
        flex.layout(Rect(0, 0, 400, 600))
        self.assertIsNotNone(flex.size)

    def test_flex_paint(self):
        """测试 RenderFlex 绘制"""
        flex = RenderFlex(direction="horizontal")
        from src.rendering_engine import Canvas
        commands = flex.paint(Canvas(800, 600))
        self.assertIsInstance(commands, list)


if __name__ == "__main__":
    unittest.main()

"""
示例 1: Widget 树演示
演示 Flutter 的 Widget 树构建和 Element 树生成

跨平台原理：
Flutter 使用 Widget 树描述 UI 结构。
Widget 是不可变的，每次更新时创建新的 Widget 树。
Flutter 通过对比新旧树来高效更新 UI。

Widget Tree 示例：
    MaterialApp
    └── Scaffold
        ├── AppBar
        │   └── Text("Hello")
        ├── Body
        │   └── Column
        │       ├── Text("Item 1")
        │       ├── Text("Item 2")
        │       └── Text("Item 3")
        └── FloatingActionButton
            └── Icon(Icons.add)
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.widget_tree import (
    Widget, StatelessWidget, StatefulElement,
    StatelessElement, Element, RenderBox,
    RenderObjectType, RenderFlex, RenderStack
)
from src.rendering_engine import (
    Color, Colors, Rect, Offset, Paint, FillStyle
)
from src.layout_engine import BoxConstraints, LayoutEngine


def demo():
    """Widget 树构建演示"""
    print("=" * 60)
    print("Widget 树构建演示")
    print("Widget Tree Construction Demo")
    print("=" * 60)

    # 1. 创建 Widget 树
    print("\n1. 构建 Widget 树")
    print("-" * 40)

    # 模拟一个简单的 Flutter 应用结构
    app_bar = StatelessWidget(key="app_bar")
    app_bar.append_child(
        StatelessWidget(key="app_bar_title")
    )

    body = StatelessWidget(key="body")
    column = StatelessWidget(key="column")
    column.append_child(
        StatelessWidget(key="text_1")
    )
    column.append_child(
        StatelessWidget(key="text_2")
    )
    column.append_child(
        StatelessWidget(key="text_3")
    )
    body.append_child(column)

    scaffold = StatelessWidget(key="scaffold")
    scaffold.append_child(app_bar)
    scaffold.append_child(body)

    app = StatelessWidget(key="app_material")
    app.append_child(scaffold)

    # 2. 构建 Element 树
    print("\n2. 构建 Element 树")
    print("-" * 40)
    root_element = app.build()

    def print_element_tree(element: Element, indent: int = 0):
        prefix = "  " * indent
        render_info = ""
        if element.render_object:
            render_info = f" [Render: {type(element.render_object).__name__}]"
        print(f"{prefix}{element.__class__.__name__}({element._debug_name}){render_info}")
        for child in element.children:
            print_element_tree(child, indent + 1)

    print_element_tree(root_element)

    # 3. 布局计算
    print("\n3. 执行布局")
    print("-" * 40)
    engine = LayoutEngine()
    result = engine.layout(app, (800.0, 600.0))
    print(f"根节点大小: {result.size.width} x {result.size.height}")
    print(f"布局传递次数: {engine.pass_count}")
    print("\n布局日志:")
    for log in engine.layout_log:
        print(f"  {log}")

    # 4. 渲染
    print("\n4. 执行渲染")
    print("-" * 40)
    from src.rendering_engine import Canvas
    canvas = Canvas(800, 600)
    canvas.clear(Colors.BACKGROUND)

    # 绘制 AppBar
    paint = Paint()
    paint.color = Colors.BLUE
    paint.fill_style = FillStyle.FILL
    canvas.draw_rect(Rect(0, 0, 800, 56), paint)

    # 绘制内容区域
    paint.color = Colors.WHITE
    canvas.draw_rect(Rect(0, 56, 800, 600), paint)

    # 绘制文本行
    for i in range(3):
        y = 100 + i * 50
        paint.color = Colors.BLACK.with_alpha(200)
        canvas.draw_rect(Rect(20, y, 200, 30), paint)

    scene = canvas.get_scene()
    summary = scene.summary()
    print(f"渲染场景: {scene}")
    print(f"绘制命令: {summary['command_types']}")

    # 5. Widget 信息
    print("\n5. Widget 树信息")
    print("-" * 40)
    print(f"根 Widget: {app.to_dict()}")
    print(f"Element 数: {len(root_element.get_descendants()) + 1}")

    print("\n" + "=" * 60)
    print("演示完成！")
    print("Key concept: Widget 是不可变的配置描述，")
    print("Element 是 Widget 和 Render 对象之间的桥梁。")
    print("=" * 60)


if __name__ == "__main__":
    # Import src modules
    import src
    demo()

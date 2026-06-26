"""
示例 4: 跨平台布局演示
演示 Flutter 的跨平台布局系统

跨平台原理：
Flutter 的布局系统使用约束（Constraints）传递机制：
1. 父 Widget 传递约束给子 Widget
2. 子 Widget 在约束内选择大小
3. 父 Widget 设置子 Widget 的位置

布局策略：
- BoxConstraints: 盒模型约束
- FlexLayout: 弹性布局（Row/Column）
- StackLayout: 层叠布局（Stack）
- CustomLayout: 自定义布局
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.layout_engine import (
    BoxConstraints, LayoutEngine, LayoutStrategy,
    BoxLayoutStrategy, FlexLayoutStrategy, StackLayoutStrategy,
    LayoutDebugger
)
from src.widget_tree import (
    Widget, StatelessWidget, RenderBox, RenderFlex, RenderStack
)
from src.rendering_engine import (
    Color, Colors, Rect, Offset, Paint, FillStyle
)


class MockWidget:
    """模拟 Flutter Widget 用于布局演示"""

    def __init__(self, name: str, layout_type: str = "box",
                 preferred_size: Optional[Rect] = None,
                 children: Optional[list] = None,
                 direction: str = "horizontal"):
        self.name = name
        self.layout_type = layout_type
        self.preferred_size = preferred_size
        self.children = children or []
        self.direction = direction

    def __repr__(self):
        return f"MockWidget({self.name}, type={self.layout_type})"


from typing import Optional


def demo():
    """跨平台布局演示"""
    print("=" * 60)
    print("跨平台布局 (Cross-Platform Layout) 演示")
    print("Flutter Layout System Demo")
    print("=" * 60)

    # 1. BoxConstraints 演示
    print("\n1. 布局约束 (BoxConstraints)")
    print("-" * 40)

    # 无约束
    unconstrained = BoxConstraints(0, float('inf'), 0, float('inf'))
    print(f"无约束: {unconstrained}")
    print(f"  is_unconstrained: {unconstrained.is_unconstrained}")

    # 固定大小约束
    tight = BoxConstraints.tight(Rect.from_sizes(0, 0, 100, 50))
    print(f"固定约束: {tight}")
    print(f"  is_tight: {tight.is_tight}")

    # 弹性约束
    relaxed = BoxConstraints(0, 400, 0, 800)
    print(f"弹性约束: {relaxed}")

    # 强制执行
    size = Rect.from_sizes(0, 0, 200, 100)
    enforced = relaxed.enforce(size)
    print(f"执行 {size} 在 {relaxed} 内: {enforced}")

    # 2. 盒模型布局
    print("\n2. 盒模型布局 (Box Layout)")
    print("-" * 40)

    engine = LayoutEngine()

    # 模拟 Widget 树：Container → Text
    text_widget = MockWidget(
        "Text('Hello World')",
        layout_type="box",
        preferred_size=Rect.from_sizes(0, 0, 120, 30)
    )

    container_widget = MockWidget(
        "Container",
        layout_type="box",
        children=[text_widget]
    )

    result = engine.layout(container_widget, (800, 600))
    print(f"Container 布局结果: {result.size.width} x {result.size.height}")
    print(f"布局传递次数: {engine.pass_count}")

    # 3. 弹性布局 (Row)
    print("\n3. 弹性布局 - Row")
    print("-" * 40)

    row_engine = LayoutEngine()

    icon_widget = MockWidget(
        "Icon(Icons.add)",
        layout_type="box",
        preferred_size=Rect.from_sizes(0, 0, 48, 48)
    )

    text_widget_row = MockWidget(
        "Text('Add Item')",
        layout_type="box",
        preferred_size=Rect.from_sizes(0, 0, 100, 48)
    )

    row_widget = MockWidget(
        "Row",
        layout_type="flex",
        direction="horizontal",
        children=[icon_widget, text_widget_row]
    )

    row_result = row_engine.layout(row_widget, (800, 600))
    print(f"Row 布局结果: {row_result.size.width} x {row_result.size.height}")
    print(f"布局日志:")
    for log in row_engine.layout_log:
        print(f"  {log}")

    # 4. 弹性布局 (Column)
    print("\n4. 弹性布局 - Column")
    print("-" * 40)

    column_engine = LayoutEngine()

    list_items = [
        MockWidget(f"ListTile #{i+1}", layout_type="box",
                   preferred_size=Rect.from_sizes(0, 0, 80, 56))
        for i in range(5)
    ]

    column_widget = MockWidget(
        "Column",
        layout_type="flex",
        direction="vertical",
        children=list_items
    )

    column_result = column_engine.layout(column_widget, (400, 800))
    print(f"Column 布局结果: {column_result.size.width} x {column_result.size.height}")

    # 5. 层叠布局 (Stack)
    print("\n5. 层叠布局 - Stack")
    print("-" * 40)

    stack_engine = LayoutEngine()

    image_widget = MockWidget(
        "Image",
        layout_type="box",
        preferred_size=Rect.from_sizes(0, 0, 400, 250)
    )

    overlay_widget = MockWidget(
        "Overlay(Text)",
        layout_type="box",
        preferred_size=Rect.from_sizes(0, 0, 200, 30)
    )

    stack_widget = MockWidget(
        "Stack",
        layout_type="stack",
        children=[image_widget, overlay_widget]
    )

    stack_result = stack_engine.layout(stack_widget, (400, 300))
    print(f"Stack 布局结果: {stack_result.size.width} x {stack_result.size.height}")
    print(f"布局日志:")
    for log in stack_engine.layout_log:
        print(f"  {log}")

    # 6. 布局调试
    print("\n6. 布局调试 (Layout Debugger)")
    print("-" * 40)

    debugger = LayoutDebugger()

    # 记录布局树
    constraints1 = BoxConstraints(0, 800, 0, 600)
    debugger.record_layout("MaterialApp", constraints1,
                           Rect.from_sizes(0, 0, 800, 600))

    constraints2 = BoxConstraints(0, 800, 0, 600)
    debugger.record_layout("Scaffold", constraints2,
                           Rect.from_sizes(0, 0, 800, 600))

    constraints3 = BoxConstraints(0, 800, 0, 56)
    debugger.record_layout("AppBar", constraints3,
                           Rect.from_sizes(0, 0, 800, 56))

    constraints4 = BoxConstraints(0, 800, 56, 544)
    debugger.record_layout("Body", constraints4,
                           Rect.from_sizes(0, 56, 800, 600))

    print(debugger.to_text())

    # 7. 布局策略
    print("\n7. 布局策略 (Layout Strategy)")
    print("-" * 40)

    # 盒模型策略
    box_strategy = BoxLayoutStrategy(
        min_size=Rect.from_sizes(0, 0, 50, 50),
        max_size=Rect.from_sizes(0, 0, 200, 200)
    )
    constraints = BoxConstraints(0, float('inf'), 0, float('inf'))
    box_size = box_strategy.compute_layout(constraints)
    print(f"BoxLayout 结果: {box_size.width} x {box_size.height}")

    # 弹性布局策略
    flex_strategy = FlexLayoutStrategy(direction="horizontal", main_axis_spacing=8.0)
    flex_constraints = BoxConstraints(0, float('inf'), 0, float('inf'))
    flex_size = flex_strategy.compute_layout(flex_constraints)
    print(f"FlexLayout 结果: {flex_size.width} x {flex_size.height}")

    # 层叠布局策略
    stack_strategy = StackLayoutStrategy()
    stack_constraints = BoxConstraints(0, 400, 0, 300)
    stack_size = stack_strategy.compute_layout(stack_constraints)
    print(f"StackLayout 结果: {stack_size.width} x {stack_size.height}")

    # 8. 跨平台一致性验证
    print("\n8. 跨平台一致性验证")
    print("-" * 40)
    print("Flutter 布局在不同平台上的行为:")
    print("  Android: 使用 DIP (Density-independent Pixels)")
    print("  iOS:     使用 PT (Points)")
    print("  Web:     使用 PX (Pixels) + CSS")
    print("  Desktop: 使用 DIP + 高 DPI 支持")
    print()
    print("  Flutter 统一使用 Logical Pixel (DIP):")
    print("    1 DIP = 1 Logical Pixel")
    print("    Physical Pixel = DIP * DevicePixelRatio")
    print()
    print("  示例: 800 DIP x 600 DIP")
    print("    Android (3x): 2400 x 1800 physical pixels")
    print("    iOS (3x):     2400 x 1800 physical pixels")
    print("    Web (1x):     800 x 600 physical pixels")
    print("    Desktop (2x): 1600 x 1200 physical pixels")

    print("\n" + "=" * 60)
    print("演示完成！")
    print("Key concept: Flutter 使用约束传递模型实现跨平台一致布局。")
    print("=" * 60)


if __name__ == "__main__":
    demo()

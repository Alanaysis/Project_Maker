"""
示例 1: 基础 UI 布局演示
Basic UI Layout Demo

演示 iOS 视图层次、Auto Layout 和手势识别。
"""

import sys
sys.path.insert(0, "/home/siok/project_copyninja/projects/ios-app")

from src.ui import (
    UIView, UILabel, UIButton, UIImageView, UITextField,
    UIScrollView, UIGestureRecognizer, UITapGestureRecognizer,
    UIPanGestureRecognizer, UISwipeGestureRecognizer,
    NSLayoutConstraint, NSLayoutAttribute, UILayout,
    UIViewContentMode,
)
from src.core import RunLoop, MainThread


def demo_view_hierarchy():
    """演示视图层次结构"""
    print("=" * 60)
    print("1. 视图层次结构 (View Hierarchy)")
    print("=" * 60)

    # 创建窗口 (Window)
    window = UIView(frame=(0, 0, 375, 667))
    window.name = "Window"
    window._background_color = "#FFFFFF"
    print(f"创建窗口: {window}")

    # 创建容器视图
    container = UIView(frame=(20, 100, 335, 400))
    container.name = "Container"
    container._background_color = "#F0F0F0"
    container._cornerRadius = 10
    window.add_subview(container)

    # 创建标签
    label = UILabel(frame=(20, 20, 295, 40))
    label.name = "TitleLabel"
    label.text = "Hello iOS!"
    label._font_size = 24
    label._text_color = "#333333"
    container.add_subview(label)

    # 创建按钮
    button = UIButton(frame=(100, 200, 135, 44))
    button.name = "ActionBtn"
    button.set_title("点击我", state="normal")
    button._background_color_normal = "#007AFF"
    button.add_target(lambda btn: print(f"  [按钮] 按钮被点击!"), for_event="touchUpInside")
    container.add_subview(button)

    # 创建文本输入框
    textField = UITextField(frame=(20, 280, 295, 40))
    textField.name = "InputField"
    textField._placeholder = "请输入内容..."
    textField._border_style = "rounded"
    container.add_subview(textField)

    # 演示命中测试
    print("\n  --- 命中测试 (Hit Testing) ---")
    hit = window.hitTest((180, 222))  # 按钮中心
    print(f"  点击 (180, 222) -> 命中: {hit}")

    hit = window.hitTest((30, 130))  # 标签中心
    print(f"  点击 (30, 130) -> 命中: {hit}")

    # 通过 tag 查找视图
    button.tag = 100
    found = container.viewWithTag(100)
    print(f"  通过 tag=100 查找: {found}")

    # 演示视图顺序
    print("\n  --- 视图顺序 ---")
    print(f"  子视图顺序: {[sv.name or sv.__class__.__name__ for sv in container.subviews]}")
    container.bring_to_front()
    print(f"  移到最前面后: {[sv.name or sv.__class__.__name__ for sv in container.subviews]}")

    print(f"\n  视图树结构:")
    print(f"  Window (frame={window.frame})")
    print(f"    └── Container (frame={container.frame})")
    for sv in container.subviews:
        print(f"        └── {sv.name or sv.__class__.__name__} (frame={sv.frame})")

    return window, container


def demo_auto_layout():
    """演示 Auto Layout 约束系统"""
    print("\n" + "=" * 60)
    print("2. Auto Layout 约束系统")
    print("=" * 60)

    # 创建父视图
    parent = UIView(frame=(0, 0, 375, 667))
    parent.name = "ParentView"

    # 创建子视图
    label = UILabel(frame=(0, 0, 100, 30))
    label.name = "Label"
    label.text = "约束布局"

    button = UIButton(frame=(0, 0, 100, 40))
    button.name = "Button"
    button.set_title("按钮", state="normal")

    parent.add_subview(label)
    parent.add_subview(button)

    # 创建约束系统
    layout = UILayout()

    # 约束 1: label 居中于父视图
    center_x = NSLayoutConstraint(
        label, NSLayoutAttribute.CENTER_X, 1.0,
        parent, NSLayoutAttribute.CENTER_X, 0
    )
    center_x.identifier = "label_centerX"
    center_x.is_active = True
    layout.add_constraint(center_x)

    # 约束 2: label 距离顶部 100
    top = NSLayoutConstraint(
        label, NSLayoutAttribute.TOP, 1.0,
        None, NSLayoutAttribute.TOP, 100
    )
    top.identifier = "label_top"
    top.is_active = True
    layout.add_constraint(top)

    # 约束 3: button 在 label 下方 20
    button_top = NSLayoutConstraint(
        button, NSLayoutAttribute.TOP, 1.0,
        label, NSLayoutAttribute.BOTTOM, 20
    )
    button_top.identifier = "button_below_label"
    button_top.is_active = True
    layout.add_constraint(button_top)

    # 约束 4: button 水平居中
    button_center = NSLayoutConstraint(
        button, NSLayoutAttribute.CENTER_X, 1.0,
        parent, NSLayoutAttribute.CENTER_X, 0
    )
    button_center.identifier = "button_centerX"
    button_center.is_active = True
    layout.add_constraint(button_center)

    # 约束 5: label 宽度为 100
    label_width = NSLayoutConstraint(
        label, NSLayoutAttribute.WIDTH, 1.0,
        None, NSLayoutAttribute.WIDTH, 100
    )
    label_width.identifier = "label_width"
    label_width.is_active = True
    layout.add_constraint(label_width)

    # 解析约束
    print(f"\n  添加 {len(layout.constraints)} 个约束:")
    for c in layout.constraints:
        print(f"    - {c}")

    print("\n  解析约束...")
    layout.resolve_constraints(parent)

    print(f"\n  最终 frame:")
    print(f"    Label:  frame={label.frame}")
    print(f"    Button: frame={button.frame}")

    # 演示移除约束
    print("\n  移除约束: button_below_label")
    layout.remove_constraint(button_top)
    print(f"  剩余约束数: {len(layout.constraints)}")

    return parent, layout


def demo_gestures():
    """演示手势识别器"""
    print("\n" + "=" * 60)
    print("3. 手势识别器 (Gesture Recognizers)")
    print("=" * 60)

    view = UIView(frame=(50, 50, 275, 300))
    view.name = "GestureView"
    view._background_color = "#E8F4FD"
    print(f"创建视图: {view.name} (frame={view.frame})")

    tap_count = [0]  # 用列表避免闭包问题

    # 点击手势
    tap = UITapGestureRecognizer(
        callback=lambda recognizer, point: print(f"  [点击] 位置: {point} (点击次数: {tap_count[0] + 1})"),
        number_of_taps=1
    )
    tap.add_to_view(view)

    # 拖动手势
    pan = UIPanGestureRecognizer(
        callback=lambda recognizer, point: print(f"  [拖拽] 位置: {point}")
    )
    pan.add_to_view(view)

    # 滑动手势
    swipe = UISwipeGestureRecognizer(
        direction="right",
        callback=lambda recognizer, point: print(f"  [右滑] 位置: {point}")
    )
    swipe.add_to_view(view)

    print(f"  添加手势:")
    for g in view._gestures:
        print(f"    - {g}")

    # 模拟手势识别
    print("\n  模拟手势:")
    tap.recognize(view, (100, 100))
    tap_count[0] += 1
    tap.recognize(view, (100, 150))
    tap_count[0] += 1
    pan.recognize(view, (120, 120))
    pan.recognize(view, (150, 150))
    swipe.recognize(view, (200, 200))

    # 移除手势
    print("\n  移除点击手势")
    tap.remove_from_view()
    print(f"  剩余手势数: {len(view._gestures)}")

    return view


def demo_scroll_view():
    """演示 UIScrollView"""
    print("\n" + "=" * 60)
    print("4. UIScrollView 可滚动视图")
    print("=" * 60)

    # 创建滚动视图
    scrollView = UIScrollView(frame=(20, 100, 335, 200))
    scrollView.name = "ScrollView"
    scrollView._content_size = (335, 600)  # 内容比视图大
    scrollView._bounces = True
    scrollView._shows_scroll_indicator = True
    print(f"创建 UIScrollView: contentSize={scrollView.content_size}")

    # 添加子视图到滚动视图
    for i in range(5):
        item = UIView(frame=(10, i * 120 + 10, 315, 100))
        item.name = f"Item_{i}"
        item._background_color = "#F5F5F5" if i % 2 == 0 else "#E8E8E8"
        scrollView.add_subview(item)

    print(f"  添加 {len(scrollView.subviews)} 个子视图")
    print(f"  子视图:")
    for sv in scrollView.subviews:
        print(f"    - {sv.name}: frame={sv.frame}")

    # 模拟滚动
    print("\n  模拟滚动:")
    scrollView.content_offset = (0, 100)
    print(f"    滚动到 offset=(0, 100)")
    scrollView.content_offset = (0, 300)
    print(f"    滚动到 offset=(0, 300)")

    return scrollView


def main():
    """运行所有演示"""
    print("\n" + "=" * 60)
    print("  iOS 基础应用 - 基础 UI 布局演示")
    print("  iOS Basic Application - UI Layout Demo")
    print("=" * 60 + "\n")

    # 演示 1: 视图层次
    window, container = demo_view_hierarchy()

    # 演示 2: Auto Layout
    parent, layout = demo_auto_layout()

    # 演示 3: 手势识别
    gesture_view = demo_gestures()

    # 演示 4: UIScrollView
    scroll_view = demo_scroll_view()

    print("\n" + "=" * 60)
    print("  演示完成!")
    print("  Demo Complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

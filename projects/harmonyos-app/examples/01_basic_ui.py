"""
示例 1: 基础 UI 组件演示

演示鸿蒙 ArkUI 的基础组件：
- Text (文本)
- Button (按钮)
- Image (图片)
- TextInput (输入框)
- Column/Row/Stack (布局容器)

核心概念：
- 声明式 UI：UI = f(state)
- 组件树：父容器包含子组件
- 样式链式调用：.width(100).height(50)
"""

import sys
sys.path.insert(0, '.')

from src.component.text import Text
from src.component.button import Button
from src.component.image import Image
from src.component.input import TextInput
from src.component.container import Column, Row, Stack, Flex
from src.component.base import LifecyclePhase


def demo_text():
    """演示 Text 文本组件"""
    print("=" * 60)
    print("1. Text 文本组件演示")
    print("=" * 60)

    # 基础文本
    text = Text('Hello HarmonyOS!')
    text.font_size(24).font_weight('bold').font_color('#333333')

    # 富文本
    rich_text = Text()
    rich_text.append_text('Hello ', fontColor='#666666', fontSize=16)
    rich_text.append_text('HarmonyOS', fontColor='#007DFF', fontSize=20, fontWeight='bold')
    rich_text.append_text('!', fontColor='#FF6600', fontSize=16)

    # 文本溢出处理
    long_text = Text('这是一段非常长的文本内容，用于演示文本溢出处理功能，'
                     '当文本超出容器宽度时，可以显示省略号或裁剪')
    long_text.text_overflow('ellipsis').max_lines(2)

    print("\n--- 基础文本 ---")
    print(text.render())
    print("\n--- 富文本 ---")
    print(rich_text.render())
    print("\n--- 溢出文本 ---")
    print(long_text.render())


def demo_button():
    """演示 Button 按钮组件"""
    print("\n" + "=" * 60)
    print("2. Button 按钮组件演示")
    print("=" * 60)

    # 普通按钮
    submit_btn = Button('提交')
    submit_btn.background_color('#007DFF').font_color('#FFFFFF')
    submit_btn.on_click(lambda: print("[点击] 提交按钮被点击"))

    # 禁用按钮
    disabled_btn = Button('不可用')
    disabled_btn.set_disabled(True)

    # 按钮点击模拟
    print("\n--- 按钮渲染 ---")
    print(submit_btn.render())
    print(disabled_btn.render())

    print("\n--- 点击事件 ---")
    submit_btn.trigger_click()
    print("禁用按钮点击:", disabled_btn.trigger_click())


def demo_layout():
    """演示布局容器"""
    print("\n" + "=" * 60)
    print("3. 布局容器演示")
    print("=" * 60)

    # Column 垂直布局
    column = Column()
    column.gap(10).align_items('Center').justify_content('Center')
    column.add_child(Text('第一行').font_size(18))
    column.add_child(Text('第二行').font_size(14).font_color('#666666'))
    column.add_child(Text('第三行').font_size(12).font_color('#999999'))

    # Row 水平布局
    row = Row()
    row.gap(8).align_items('Center')
    row.add_child(Text('A').font_size(16))
    row.add_child(Text('B').font_size(16))
    row.add_child(Text('C').font_size(16))

    # Stack 堆栈布局
    stack = Stack().align_items('Center')
    stack.add_child(Text('底层').font_size(14).font_color('#CCCCCC'))
    stack.add_child(Text('中层').font_size(16).font_color('#666666'))
    stack.add_child(Text('顶层').font_size(18).font_weight('bold'))

    # Flex 弹性布局
    flex = Flex(direction='Row')
    flex.flex_wrap('Wrap').align_items('Center')
    for i in range(5):
        flex.add_child(Text(f'Item {i+1}').font_size(14))

    print("\n--- Column 垂直布局 ---")
    print(column.render())

    print("\n--- Row 水平布局 ---")
    print(row.render())

    print("\n--- Stack 堆栈布局 ---")
    print(stack.render())

    print("\n--- Flex 弹性布局 ---")
    print(flex.render())


def demo_complete_page():
    """演示完整页面结构"""
    print("\n" + "=" * 60)
    print("4. 完整页面结构演示")
    print("=" * 60)

    # 模拟一个用户信息页面
    page = Column().align_items('Center')
    page.gap(16)

    # 头像区域
    avatar_area = Stack().align_items('Center')
    avatar_area.add_child(Image('avatar_placeholder').image_size(80, 80).border_radius(40))
    avatar_area.add_child(Text('AI').font_size(20).font_color('#FFFFFF').font_weight('bold'))

    # 用户名
    username = Text('HarmonyOS Developer').font_size(20).font_weight('bold').font_color('#333333')

    # 描述
    desc = Text('探索鸿蒙世界的开发者').font_size(14).font_color('#999999')

    # 分隔线
    divider = Text('─' * 40).font_size(12).font_color('#E1E1E1')

    # 信息列表
    info_col = Column().align_items('Start')
    info_col.gap(8)
    info_col.add_child(Text('设备: Phone').font_size(14))
    info_col.add_child(Text('系统: HarmonyOS 4.0').font_size(14))
    info_col.add_child(Text('版本: 1.0.0').font_size(14))

    # 操作按钮
    btn_row = Row().align_items('Center').justify_content('Center')
    btn_row.gap(12)
    btn_row.add_child(Button('编辑资料').background_color('#007DFF').font_size(14))
    btn_row.add_child(Button('退出登录').background_color('#FF3B30').font_size(14))

    # 组装页面
    page.add_child(avatar_area)
    page.add_child(username)
    page.add_child(desc)
    page.add_child(divider)
    page.add_child(info_col)
    page.add_child(btn_row)

    print("\n--- 用户信息页面 ---")
    print(page.render())
    print(f"\n页面组件总数: {page.count_components()}")


if __name__ == '__main__':
    print("\n" + "#" * 60)
    print("# HarmonyOS ArkUI 基础组件演示")
    print("# 鸿蒙 ArkUI 基础组件学习示例")
    print("#" * 60)

    demo_text()
    demo_button()
    demo_layout()
    demo_complete_page()

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)

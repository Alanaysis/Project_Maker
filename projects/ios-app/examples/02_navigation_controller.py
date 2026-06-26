"""
示例 2: 导航控制器演示
Navigation Controller Demo

演示 UINavigationController 的页面导航机制。
"""

import sys
sys.path.insert(0, "/home/siok/project_copyninja/projects/ios-app")

from src.ui import (
    UIViewController, UINavigationController,
    UIView, UILabel, UIButton,
)


class HomeViewController(UIViewController):
    """首页视图控制器"""

    def __init__(self):
        super().__init__(title="首页")
        self.load_view()
        self.view._background_color = "#F8F8F8"

    def view_did_load(self):
        super().view_did_load()
        print("[HomeVC] viewDidLoad - 设置首页 UI")

        # 创建标题标签
        title_label = UILabel(frame=(0, 80, 375, 60))
        title_label.name = "TitleLabel"
        title_label.text = "欢迎来到 iOS 学习应用"
        title_label._font_size = 28
        title_label._text_color = "#333333"
        title_label._text_alignment = "center"
        self.view.add_subview(title_label)

        # 创建导航按钮
        nav_btn = UIButton(frame=(87, 200, 200, 50))
        nav_btn.name = "NavButton"
        nav_btn.set_title("进入详情页", state="normal")
        nav_btn._background_color_normal = "#007AFF"
        nav_btn.add_target(self._on_nav_click, for_event="touchUpInside")
        self.view.add_subview(nav_btn)

        # 创建列表项按钮
        for i, title in enumerate(["功能 A", "功能 B", "功能 C", "功能 D"]):
            btn = UIButton(frame=(20, 300 + i * 60, 335, 50))
            btn.name = f"ListItem_{i}"
            btn.set_title(f"  {title}  >", state="normal")
            btn._background_color_normal = "#FFFFFF"
            btn.add_target(lambda b, idx=i: self._on_list_click(idx), for_event="touchUpInside")
            self.view.add_subview(btn)

    def _on_nav_click(self, button):
        print("[HomeVC] 点击导航按钮")

    def _on_list_click(self, index):
        print(f"[HomeVC] 点击列表项 {index}")


class DetailViewController(UIViewController):
    """详情视图控制器"""

    def __init__(self, title: str, content: str):
        super().__init__(title=title)
        self._content = content
        self.load_view()
        self.view._background_color = "#FFFFFF"

    def view_did_load(self):
        super().view_did_load()
        print(f"[DetailVC] viewDidLoad: {self.title}")

        # 内容标签
        content_label = UILabel(frame=(20, 120, 335, 200))
        content_label.name = "ContentLabel"
        content_label.text = self._content
        content_label._font_size = 16
        content_label._text_color = "#666666"
        content_label._number_of_lines = 0
        self.view.add_subview(content_label)

        # 返回按钮
        back_btn = UIButton(frame=(137, 400, 100, 44))
        back_btn.name = "BackButton"
        back_btn.set_title("返回", state="normal")
        back_btn._background_color_normal = "#007AFF"
        back_btn.add_target(self._on_back_click, for_event="touchUpInside")
        self.view.add_subview(back_btn)

    def _on_back_click(self, button):
        if self._navigation_controller:
            self._navigation_controller.pop_view_controller()


class SettingsViewController(UIViewController):
    """设置视图控制器"""

    def __init__(self):
        super().__init__(title="设置")
        self.load_view()
        self.view._background_color = "#F2F2F7"

    def view_did_load(self):
        super().view_did_load()
        print("[SettingsVC] viewDidLoad")

        # 设置项
        items = [
            ("通知设置", "已开启"),
            ("隐私政策", "查看"),
            ("关于我们", "v1.0.0"),
            ("退出登录", ""),
        ]

        for i, (title, subtitle) in enumerate(items):
            cell = UIView(frame=(16, 100 + i * 60, 343, 55))
            cell._background_color = "#FFFFFF" if i < len(items) - 1 else "transparent"
            if i < len(items) - 1:
                cell._cornerRadius = 8

            label = UILabel(frame=(16, 18, 250, 20))
            label.text = title
            label._font_size = 16
            label._text_color = "#000000"
            cell.add_subview(label)

            subtitle_label = UILabel(frame=(250, 18, 77, 20))
            subtitle_label.text = subtitle
            subtitle_label._font_size = 14
            subtitle_label._text_color = "#999999"
            subtitle_label._text_alignment = "right"
            cell.add_subview(subtitle_label)

            self.view.add_subview(cell)


def demo_navigation():
    """演示导航控制器"""
    print("=" * 60)
    print("  导航控制器演示 (Navigation Controller Demo)")
    print("=" * 60 + "\n")

    # 1. 创建首页
    home_vc = HomeViewController()
    home_vc.view_did_load()

    # 2. 创建导航控制器
    nav_controller = UINavigationController(home_vc)
    print(f"\n[Navigation] 创建导航控制器, 根视图: {nav_controller.top_view_controller.title}")

    # 3. 压入详情页
    print("\n--- 压入详情页 ---")
    detail_vc = DetailViewController(
        title="详情",
        content="这是通过 UINavigationController 导航到的详情页。\n\n在 iOS 中，导航控制器管理视图控制器的栈，\n实现页面之间的push/pop操作。"
    )
    detail_vc.view_did_load()
    nav_controller.push_view_controller(detail_vc)

    # 4. 再压入一个页面
    print("\n--- 压入设置页 ---")
    settings_vc = SettingsViewController()
    settings_vc.view_did_load()
    nav_controller.push_view_controller(settings_vc)

    # 5. 显示当前栈
    print(f"\n[Navigation] 当前栈深度: {len(nav_controller.view_controller_stack)}")
    for i, vc in enumerate(nav_controller.view_controller_stack):
        print(f"  [{i}] {vc.title} ({vc.__class__.__name__})")

    # 6. 弹出到首页
    print("\n--- 弹出到首页 ---")
    nav_controller.pop_to_root_controller()
    print(f"[Navigation] 栈深度: {len(nav_controller.view_controller_stack)}")
    print(f"[Navigation] 当前视图: {nav_controller.top_view_controller.title}")

    # 7. 再次压入
    print("\n--- 再次压入 ---")
    nav_controller.push_view_controller(detail_vc)
    print(f"[Navigation] 栈深度: {len(nav_controller.view_controller_stack)}")

    return nav_controller


def main():
    """运行演示"""
    nav_controller = demo_navigation()

    print("\n" + "=" * 60)
    print("  演示完成!")
    print("  Demo Complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

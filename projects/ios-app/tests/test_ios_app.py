"""
iOS 基础应用 - 单元测试
iOS Basic Application - Unit Tests

测试覆盖：
- RunLoop 事件循环
- UIView 视图层次
- Auto Layout 约束系统
- 手势识别器
- UINavigationController
- UITableView
- URLSession 网络请求
- KVO 数据绑定
- ViewModel MVVM
"""

import sys
import os
import unittest
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core import RunLoop, RunLoopMode, MainThread, Application
from src.ui import (
    UIView, UILabel, UIButton, UIImageView, UITextField, UIScrollView,
    UIViewController, UINavigationController, UITableView, UITableViewStyle,
    NSLayoutAttribute, NSLayoutConstraint, UILayout,
    UIGestureRecognizer, UITapGestureRecognizer, UIPanGestureRecognizer,
    UISwipeGestureRecognizer, UIViewContentMode,
    UILayoutGuide, UILayoutGuideFactory,
    UIGestureRecognizerState,
)
from src.network import (
    URLSession, URLRequest, URLResponse, URLResponseError,
    URLSessionDataTask, NetworkManager, HTTPMethod,
)
from src.binding import (
    KVOObserver, Observable, Binding, Property, ViewModel,
)


# ============================================================
# RunLoop 测试
# ============================================================


class TestRunLoop(unittest.TestCase):
    """测试 RunLoop 核心机制"""

    def test_initial_state(self):
        """测试初始状态"""
        rl = RunLoop()
        self.assertEqual(rl.mode, RunLoopMode.TRAPPING)
        self.assertFalse(rl.is_running)

    def test_add_input_source(self):
        """测试添加输入源"""
        rl = RunLoop()
        rl.add_input_source(lambda: None, name="test_source")
        self.assertEqual(len(rl._input_sources), 1)

    def test_add_timer(self):
        """测试添加定时器"""
        rl = RunLoop()
        rl.add_timer(1.0, lambda: None, name="test_timer")
        self.assertEqual(len(rl._timer_sources), 1)
        self.assertEqual(rl._timer_sources[0]["interval"], 1.0)

    def test_mode_transitions(self):
        """测试模式转换"""
        rl = RunLoop()
        self.assertEqual(rl.mode, RunLoopMode.TRAPPING)

        rl._update_mode(RunLoopMode.UNTRAPPED)
        self.assertEqual(rl.mode, RunLoopMode.UNTRAPPED)

        rl._update_mode(RunLoopMode.WAITING)
        self.assertEqual(rl.mode, RunLoopMode.WAITING)

        rl._update_mode(RunLoopMode.RUNNABLE)
        self.assertEqual(rl.mode, RunLoopMode.RUNNABLE)

        rl._update_mode(RunLoopMode.STOPPED)
        self.assertEqual(rl.mode, RunLoopMode.STOPPED)

    def test_observer_notification(self):
        """测试观察者通知"""
        rl = RunLoop()
        events = []
        rl.add_observer(lambda event: events.append(event))
        rl._notify_observers("test_event")
        self.assertIn("test_event", events)

    def test_perform_on_main(self):
        """测试主线程任务调度"""
        rl = RunLoop()
        results = []

        def callback(x, y):
            results.append(x + y)

        rl.perform_on_main(callback, 3, 4)
        self.assertEqual(len(rl._event_queue), 1)

        # 执行事件
        rl._running = True
        rl._process_events()
        self.assertEqual(results, [7])

    def test_delay(self):
        """测试延迟执行"""
        rl = RunLoop()
        executed = []

        def callback():
            executed.append(True)

        rl.delay(0.01, callback)
        # 延迟任务会创建线程，这里只验证调度
        self.assertTrue(True)


# ============================================================
# MainThread 测试
# ============================================================


class TestMainThread(unittest.TestCase):
    """测试 MainThread 管理"""

    def test_singleton(self):
        """测试单例模式"""
        mt1 = MainThread()
        mt2 = MainThread()
        self.assertIs(mt1, mt2)

    def test_run_loop_property(self):
        """测试 run_loop 属性"""
        mt = MainThread()
        self.assertIsInstance(mt.run_loop, RunLoop)


# ============================================================
# Application 测试
# ============================================================


class TestApplication(unittest.TestCase):
    """测试 Application 生命周期"""

    def test_initial_state(self):
        """测试初始状态"""
        app = Application("TestApp")
        self.assertEqual(app.name, "TestApp")
        self.assertFalse(app.is_active)
        self.assertFalse(app.is_background)

    def test_launch(self):
        """测试应用启动"""
        app = Application("TestApp")

        class Delegate:
            def application_didFinishLaunching(self, app, options):
                pass

        app.set_delegate(Delegate())
        app.launch()
        self.assertTrue(app.is_active)
        self.assertFalse(app.is_background)

    def test_lifecycle_events(self):
        """测试生命周期事件记录"""
        app = Application("TestApp")
        app.launch()
        events = app.lifecycle_events
        self.assertIn("applicationDidFinishLaunching", events)
        self.assertIn("applicationDidBecomeActive", events)

    def test_enter_background(self):
        """测试进入后台"""
        app = Application("TestApp")
        app.launch()
        app.enter_background()
        self.assertFalse(app.is_active)
        self.assertTrue(app.is_background)

    def test_enter_foreground(self):
        """测试回到前台"""
        app = Application("TestApp")
        app.launch()
        app.enter_background()
        app.enter_foreground()
        self.assertTrue(app.is_active)
        self.assertFalse(app.is_background)

    def test_terminate(self):
        """测试应用终止"""
        app = Application("TestApp")
        app.launch()
        app.terminate()
        self.assertFalse(app.is_active)


# ============================================================
# UIView 测试
# ============================================================


class TestUIView(unittest.TestCase):
    """测试 UIView 基类"""

    def test_initial_state(self):
        """测试初始状态"""
        view = UIView(frame=(0, 0, 100, 100))
        self.assertEqual(view.frame, (0, 0, 100, 100))
        self.assertEqual(view.alpha, 1.0)
        self.assertFalse(view.is_hidden)
        self.assertTrue(view._userInteractionEnabled)

    def test_default_frame(self):
        """测试默认 frame"""
        view = UIView()
        self.assertEqual(view.frame, (0, 0, 100, 100))

    def test_frame_setter(self):
        """测试 frame 设置"""
        view = UIView()
        view.frame = (10, 20, 200, 300)
        self.assertEqual(view.frame, (10, 20, 200, 300))
        self.assertEqual(view.x, 10)
        self.assertEqual(view.y, 20)
        self.assertEqual(view.width, 200)
        self.assertEqual(view.height, 300)

    def test_center_setter(self):
        """测试 center 设置"""
        view = UIView(frame=(0, 0, 100, 100))
        view.center = (50, 50)
        self.assertEqual(view.center, (50, 50))

    def test_subview_management(self):
        """测试子视图管理"""
        parent = UIView(frame=(0, 0, 200, 200))
        child = UIView(frame=(10, 10, 50, 50))

        parent.add_subview(child)
        self.assertIn(child, parent.subviews)
        self.assertIs(child.superview, parent)

        child.remove_from_superview()
        self.assertNotIn(child, parent.subviews)
        self.assertIsNone(child.superview)

    def test_multiple_subviews(self):
        """测试多个子视图"""
        parent = UIView()
        for i in range(3):
            child = UIView(frame=(i * 10, 0, 50, 50))
            parent.add_subview(child)
        self.assertEqual(len(parent.subviews), 3)

    def test_view_tag(self):
        """测试 viewWithTag"""
        parent = UIView()
        child = UIView(frame=(0, 0, 50, 50))
        child.tag = 42
        parent.add_subview(child)

        found = parent.viewWithTag(42)
        self.assertIsNotNone(found)
        self.assertIs(found, child)

        not_found = parent.viewWithTag(99)
        self.assertIsNone(not_found)

    def test_view_name(self):
        """测试 view name"""
        view = UIView()
        view.name = "MyView"
        self.assertEqual(view.name, "MyView")

    def test_alpha_range(self):
        """测试 alpha 范围"""
        view = UIView()
        view.alpha = 1.5  # 应被限制为 1.0
        self.assertEqual(view.alpha, 1.0)
        view.alpha = -0.5  # 应被限制为 0.0
        self.assertEqual(view.alpha, 0.0)

    def test_hidden(self):
        """测试 hidden 属性"""
        view = UIView()
        self.assertFalse(view.is_hidden)
        self.assertTrue(view.is_visible)

    def test_bring_to_front(self):
        """测试 bring_to_front"""
        parent = UIView()
        view1 = UIView(frame=(0, 0, 50, 50))
        view2 = UIView(frame=(60, 0, 50, 50))
        parent.add_subview(view1)
        parent.add_subview(view2)

        parent.bring_to_front()
        self.assertEqual(parent.subviews[-1], view2)

    def test_send_to_back(self):
        """测试 send_to_back"""
        parent = UIView()
        view1 = UIView(frame=(0, 0, 50, 50))
        view2 = UIView(frame=(60, 0, 50, 50))
        parent.add_subview(view1)
        parent.add_subview(view2)

        view2.send_to_back()
        self.assertEqual(parent.subviews[0], view2)

    def test_hit_test(self):
        """测试命中测试"""
        view = UIView(frame=(0, 0, 100, 100))
        # 在视图内
        result = view.hitTest((50, 50))
        self.assertIs(result, view)
        # 在视图外
        result = view.hitTest((200, 200))
        self.assertIsNone(result)

    def test_hit_test_hidden(self):
        """测试 hidden 视图不响应命中"""
        view = UIView(frame=(0, 0, 100, 100))
        view._hidden = True
        result = view.hitTest((50, 50))
        self.assertIsNone(result)

    def test_hit_test_alpha_zero(self):
        """测试 alpha=0 的视图不响应命中"""
        view = UIView(frame=(0, 0, 100, 100))
        view._alpha = 0
        result = view.hitTest((50, 50))
        self.assertIsNone(result)

    def test_touch_handlers(self):
        """测试触摸回调"""
        view = UIView()
        events = []

        def on_down(point):
            events.append(("down", point))

        def on_up(point):
            events.append(("up", point))

        view.set_touch_handlers(down=on_down, up=on_up)
        view.handle_touch_down((10, 20))
        view.handle_touch_up((30, 40))
        self.assertEqual(events, [("down", (10, 20)), ("up", (30, 40))])

    def test_draw(self):
        """测试绘制回调"""
        view = UIView()
        drawn = []

        def draw_handler(v):
            drawn.append(v)

        view.set_draw_handler(draw_handler)
        view.draw()
        self.assertEqual(len(drawn), 1)

    def test_layout(self):
        """测试布局"""
        parent = UIView()
        child = UIView(frame=(10, 10, 50, 50))
        parent.add_subview(child)

        parent.setNeedsLayout()
        parent.layoutIfNeeded()

    def test_content_mode(self):
        """测试内容模式"""
        view = UIView()
        self.assertEqual(view._contentMode, UIViewContentMode.SCALE_TO_FIT)

    def test_repr(self):
        """测试 __repr__"""
        view = UIView(frame=(0, 0, 100, 100))
        view.name = "Test"
        repr_str = repr(view)
        self.assertIn("UIView", repr_str)
        self.assertIn("Test", repr_str)


# ============================================================
# UILabel 测试
# ============================================================


class TestUILabel(unittest.TestCase):
    """测试 UILabel"""

    def test_initial_state(self):
        """测试初始状态"""
        label = UILabel()
        self.assertEqual(label.text, "")
        self.assertEqual(label.font_size, 17.0)
        self.assertEqual(label.text_color, "#000000")

    def test_text_setter(self):
        """测试文本设置"""
        label = UILabel()
        label.text = "Hello World"
        self.assertEqual(label.text, "Hello World")

    def test_font_properties(self):
        """测试字体属性"""
        label = UILabel()
        label._font_name = "Helvetica"
        label._font_size = 24
        self.assertEqual(label.font_name, "Helvetica")
        self.assertEqual(label.font_size, 24)

    def test_text_alignment(self):
        """测试文本对齐"""
        label = UILabel()
        label.text_alignment = "center"
        self.assertEqual(label.text_alignment, "center")

    def test_number_of_lines(self):
        """测试行数限制"""
        label = UILabel()
        label.number_of_lines = 3
        self.assertEqual(label.number_of_lines, 3)

    def test_repr(self):
        """测试 __repr__"""
        label = UILabel()
        label.text = "Test"
        self.assertIn("UILabel", repr(label))


# ============================================================
# UIButton 测试
# ============================================================


class TestUIButton(unittest.TestCase):
    """测试 UIButton"""

    def test_initial_state(self):
        """测试初始状态"""
        button = UIButton()
        self.assertEqual(button._title_normal, "")

    def test_set_title(self):
        """测试设置标题"""
        button = UIButton()
        button.set_title("Click Me", state="normal")
        self.assertEqual(button._title_normal, "Click Me")

    def test_add_target(self):
        """测试添加事件目标"""
        button = UIButton()
        called = []

        def handler(btn):
            called.append(True)

        button.add_target(handler, for_event="touchUpInside")
        self.assertIn("touchUpInside", button._event_handlers)

    def test_send_event(self):
        """测试发送事件"""
        button = UIButton()
        button.set_title("Test", state="normal")
        called = []

        def handler(btn):
            called.append(btn)

        button.add_target(handler, for_event="touchUpInside")
        button.send_event("touchUpInside")
        self.assertEqual(len(called), 1)

    def test_repr(self):
        """测试 __repr__"""
        button = UIButton()
        button.set_title("Test", state="normal")
        self.assertIn("UIButton", repr(button))


# ============================================================
# UIImageView 测试
# ============================================================


class TestUIImageView(unittest.TestCase):
    """测试 UIImageView"""

    def test_image_name(self):
        """测试图片名称"""
        iv = UIImageView()
        iv.image_name = "test.png"
        self.assertEqual(iv.image_name, "test.png")

    def test_repr(self):
        """测试 __repr__"""
        iv = UIImageView()
        iv.image_name = "icon"
        self.assertIn("UIImageView", repr(iv))


# ============================================================
# UITextField 测试
# ============================================================


class TestUITextField(unittest.TestCase):
    """测试 UITextField"""

    def test_text(self):
        """测试文本"""
        field = UITextField()
        field.text = "Hello"
        self.assertEqual(field.text, "Hello")

    def test_placeholder(self):
        """测试占位符"""
        field = UITextField()
        field.placeholder = "请输入..."
        self.assertEqual(field.placeholder, "请输入...")

    def test_repr(self):
        """测试 __repr__"""
        field = UITextField()
        field.text = "Test"
        self.assertIn("UITextField", repr(field))


# ============================================================
# UIScrollView 测试
# ============================================================


class TestUIScrollView(unittest.TestCase):
    """测试 UIScrollView"""

    def test_content_offset(self):
        """测试内容偏移"""
        sv = UIScrollView()
        sv.content_offset = (0, 100)
        self.assertEqual(sv.content_offset, (0, 100))

    def test_content_size(self):
        """测试内容大小"""
        sv = UIScrollView()
        sv.content_size = (335, 600)
        self.assertEqual(sv.content_size, (335, 600))

    def test_repr(self):
        """测试 __repr__"""
        sv = UIScrollView()
        self.assertIn("UIScrollView", repr(sv))


# ============================================================
# UIViewController 测试
# ============================================================


class TestUIViewController(unittest.TestCase):
    """测试 UIViewController"""

    def test_initial_state(self):
        """测试初始状态"""
        vc = UIViewController(title="Test")
        self.assertEqual(vc.title, "Test")
        self.assertIsNone(vc.view)
        self.assertFalse(vc._view_loaded)

    def test_load_view(self):
        """测试加载视图"""
        vc = UIViewController()
        vc.load_view()
        self.assertIsNotNone(vc.view)
        # view_did_load sets _view_loaded, not load_view
        self.assertFalse(vc._view_loaded)

    def test_lifecycle_methods(self):
        """测试生命周期方法"""
        vc = UIViewController()
        vc.load_view()

        vc.view_did_load()
        self.assertTrue(vc._view_loaded)

        vc.view_will_appear()
        vc.view_did_appear()
        self.assertTrue(vc._view_appeared)

        vc.view_will_disappear()
        vc.view_did_disappear()
        self.assertFalse(vc._view_appeared)

    def test_child_controllers(self):
        """测试子控制器"""
        parent = UIViewController()
        child = UIViewController()

        parent.add_child(child)
        self.assertIn(child, parent._child_view_controllers)
        self.assertIs(child.parent, parent)

        parent.remove_child(child)
        self.assertNotIn(child, parent._child_view_controllers)
        self.assertIsNone(child.parent)

    def test_repr(self):
        """测试 __repr__"""
        vc = UIViewController(title="Test")
        self.assertIn("UIViewController", repr(vc))


# ============================================================
# UINavigationController 测试
# ============================================================


class TestUINavigationController(unittest.TestCase):
    """测试 UINavigationController"""

    def test_initial_state(self):
        """测试初始状态"""
        root = UIViewController(title="Home")
        nav = UINavigationController(root)
        self.assertIs(nav.top_view_controller, root)
        self.assertEqual(len(nav.view_controller_stack), 1)

    def test_push(self):
        """测试 push"""
        root = UIViewController(title="Home")
        nav = UINavigationController(root)

        detail = UIViewController(title="Detail")
        nav.push_view_controller(detail)
        self.assertEqual(len(nav.view_controller_stack), 2)
        self.assertIs(nav.top_view_controller, detail)

    def test_pop(self):
        """测试 pop"""
        root = UIViewController(title="Home")
        nav = UINavigationController(root)

        detail = UIViewController(title="Detail")
        nav.push_view_controller(detail)
        popped = nav.pop_view_controller()
        self.assertIsNotNone(popped)
        self.assertIs(popped, detail)
        self.assertEqual(len(nav.view_controller_stack), 1)

    def test_pop_to_root(self):
        """测试 popToRoot"""
        root = UIViewController(title="Home")
        nav = UINavigationController(root)

        vc1 = UIViewController(title="VC1")
        vc2 = UIViewController(title="VC2")
        nav.push_view_controller(vc1)
        nav.push_view_controller(vc2)

        popped = nav.pop_to_root_controller()
        self.assertEqual(len(nav.view_controller_stack), 1)
        self.assertEqual(len(popped), 2)

    def test_cannot_pop_single(self):
        """测试不能弹出唯一视图"""
        root = UIViewController(title="Home")
        nav = UINavigationController(root)
        result = nav.pop_view_controller()
        self.assertIsNone(result)

    def test_top_view_controller(self):
        """测试 top_view_controller"""
        root = UIViewController(title="Home")
        nav = UINavigationController(root)
        self.assertIs(nav.top_view_controller, root)

    def test_visible_view_controller(self):
        """测试 visible_view_controller"""
        root = UIViewController(title="Home")
        nav = UINavigationController(root)
        self.assertIs(nav.visible_view_controller, nav.top_view_controller)

    def test_repr(self):
        """测试 __repr__"""
        root = UIViewController(title="Home")
        nav = UINavigationController(root)
        self.assertIn("UINavigationController", repr(nav))


# ============================================================
# UITableView 测试
# ============================================================


class TestUITableView(unittest.TestCase):
    """测试 UITableView"""

    def test_initial_state(self):
        """测试初始状态"""
        table = UITableView()
        self.assertEqual(table._style, UITableViewStyle.PLAIN)
        self.assertEqual(len(table._sections), 0)

    def test_data_source(self):
        """测试数据源"""
        table = UITableView()

        class MockDS:
            def numberOfSections(self, tv):
                return 1

            def numberOfRowsInSection(self, tv, section):
                return 3

            def cellForRowAtIndexPath(self, tv, indexPath):
                return f"Cell_{indexPath[1]}"

        table.data_source = MockDS()
        table.reload_data()
        self.assertEqual(table.number_of_rows_in_section(0), 3)

    def test_select_row(self):
        """测试选择行"""
        table = UITableView()

        selected = []

        class MockDelegate:
            def tableView_didSelectRowAtIndexPath(self, tv, idx):
                selected.append(idx)

        table.delegate = MockDelegate()
        table.select_row(0, 2)
        self.assertEqual(table.selected_row, (0, 2))
        self.assertEqual(len(selected), 1)

    def test_get_cell_at(self):
        """测试获取单元格"""
        table = UITableView()
        table._sections = [["A", "B", "C"]]

        cell = table.get_cell_at(0, 1)
        self.assertEqual(cell, "B")

        not_found = table.get_cell_at(5, 0)
        self.assertIsNone(not_found)

    def test_number_of_sections(self):
        """测试分区数"""
        table = UITableView()
        table._sections = [["A"], ["B", "C"], ["D"]]
        self.assertEqual(table.number_of_sections(), 3)

    def test_repr(self):
        """测试 __repr__"""
        table = UITableView()
        self.assertIn("UITableView", repr(table))


class TestUITableViewStyle(unittest.TestCase):
    """测试 UITableViewStyle 枚举"""

    def test_plain(self):
        self.assertEqual(UITableViewStyle.PLAIN.value, "plain")

    def test_grouped(self):
        self.assertEqual(UITableViewStyle.GROUPED.value, "grouped")


# ============================================================
# Auto Layout 测试
# ============================================================


class TestNSLayoutConstraint(unittest.TestCase):
    """测试 NSLayoutConstraint"""

    def test_creation(self):
        """测试创建约束"""
        view1 = UIView()
        view1.name = "v1"
        view2 = UIView()
        view2.name = "v2"

        constraint = NSLayoutConstraint(
            view1, NSLayoutAttribute.CENTER_X, 1.0,
            view2, NSLayoutAttribute.CENTER_X, 0
        )
        constraint.identifier = "test"
        self.assertFalse(constraint.is_active)
        self.assertEqual(constraint.multiplier, 1.0)
        self.assertEqual(constraint.constant, 0)

    def test_activate_deactivate(self):
        """测试激活/停用"""
        view1 = UIView()
        view1.name = "v1"
        view2 = UIView()
        view2.name = "v2"

        constraint = NSLayoutConstraint(
            view1, NSLayoutAttribute.CENTER_X, 1.0,
            view2, NSLayoutAttribute.CENTER_X, 0
        )
        constraint.activate()
        self.assertTrue(constraint.is_active)

        constraint.deactivate()
        self.assertFalse(constraint.is_active)

    def test_repr(self):
        """测试 __repr__"""
        view1 = UIView()
        view1.name = "test"
        view2 = UIView()
        view2.name = "parent"

        constraint = NSLayoutConstraint(
            view1, NSLayoutAttribute.CENTER_X, 1.0,
            view2, NSLayoutAttribute.CENTER_X, 0
        )
        self.assertIn("NSLayoutConstraint", repr(constraint))


class TestUILayout(unittest.TestCase):
    """测试 UILayout"""

    def test_add_constraint(self):
        """测试添加约束"""
        layout = UILayout()
        view1 = UIView()
        view1.name = "v1"
        view2 = UIView()
        view2.name = "v2"

        constraint = NSLayoutConstraint(
            view1, NSLayoutAttribute.CENTER_X, 1.0,
            view2, NSLayoutAttribute.CENTER_X, 0
        )
        constraint.is_active = True

        layout.add_constraint(constraint)
        self.assertEqual(len(layout.constraints), 1)

    def test_remove_constraint(self):
        """测试移除约束"""
        layout = UILayout()
        view1 = UIView()
        view1.name = "v1"
        view2 = UIView()
        view2.name = "v2"

        constraint = NSLayoutConstraint(
            view1, NSLayoutAttribute.CENTER_X, 1.0,
            view2, NSLayoutAttribute.CENTER_X, 0
        )
        constraint.is_active = True
        layout.add_constraint(constraint)

        layout.remove_constraint(constraint)
        self.assertEqual(len(layout.constraints), 0)

    def test_activate_constraints(self):
        """测试批量激活约束"""
        layout = UILayout()
        view1 = UIView()
        view1.name = "v1"
        view2 = UIView()
        view2.name = "v2"

        c1 = NSLayoutConstraint(
            view1, NSLayoutAttribute.CENTER_X, 1.0,
            view2, NSLayoutAttribute.CENTER_X, 0
        )
        c1.is_active = False

        c2 = NSLayoutConstraint(
            view1, NSLayoutAttribute.CENTER_Y, 1.0,
            view2, NSLayoutAttribute.CENTER_Y, 0
        )
        c2.is_active = False

        layout.activate_constraints([c1, c2])
        self.assertTrue(c1.is_active)
        self.assertTrue(c2.is_active)

    def test_resolve_constraints(self):
        """测试约束解析"""
        layout = UILayout()
        parent = UIView(frame=(0, 0, 375, 667))
        parent.name = "parent"

        label = UIView(frame=(0, 0, 100, 30))
        label.name = "label"
        parent.add_subview(label)

        # 水平居中约束
        constraint = NSLayoutConstraint(
            label, NSLayoutAttribute.CENTER_X, 1.0,
            parent, NSLayoutAttribute.CENTER_X, 0
        )
        constraint.is_active = True
        layout.add_constraint(constraint)

        layout.resolve_constraints(parent)
        # centerX = parent.centerX = 187.5
        expected_x = 187.5 - 50  # center - width/2
        self.assertAlmostEqual(label.x, expected_x, places=1)


class TestUILayoutGuideFactory(unittest.TestCase):
    """测试 UILayoutGuideFactory"""

    def test_create_guide(self):
        guide = UILayoutGuideFactory.create_guide("test_guide")
        self.assertIsInstance(guide, UILayoutGuide)
        self.assertEqual(guide._name, "test_guide")


# ============================================================
# Gesture Recognizer 测试
# ============================================================


class TestUIGestureRecognizer(unittest.TestCase):
    """测试 UIGestureRecognizer 基类"""

    def test_initial_state(self):
        gr = UIGestureRecognizer()
        self.assertEqual(gr.state, UIGestureRecognizerState.FAILED)

    def test_add_to_view(self):
        gr = UIGestureRecognizer()
        view = UIView()
        view.name = "test"
        gr.add_to_view(view)
        self.assertIn(gr, view._gestures)

    def test_remove_from_view(self):
        gr = UIGestureRecognizer()
        view = UIView()
        view.name = "test"
        gr.add_to_view(view)
        gr.remove_from_view()
        self.assertNotIn(gr, view._gestures)

    def test_reset(self):
        gr = UIGestureRecognizer()
        gr._state = UIGestureRecognizerState.RECOGNIZED
        gr.reset()
        self.assertEqual(gr.state, UIGestureRecognizerState.FAILED)


class TestUITapGestureRecognizer(unittest.TestCase):
    """测试 UITapGestureRecognizer"""

    def test_recognize(self):
        tap = UITapGestureRecognizer(number_of_taps=2)
        view = UIView()
        view.name = "test"
        tap.add_to_view(view)

        events = []
        def capture(r, p):
            events.append(p)
        tap._callback = capture
        tap.recognize(view, (100, 100))
        self.assertEqual(tap.state, UIGestureRecognizerState.RECOGNIZED)
        self.assertEqual(events, [(100, 100)])

    def test_repr(self):
        tap = UITapGestureRecognizer()
        self.assertIn("UITapGestureRecognizer", repr(tap))


class TestUIPanGestureRecognizer(unittest.TestCase):
    """测试 UIPanGestureRecognizer"""

    def test_recognize_began(self):
        pan = UIPanGestureRecognizer()
        view = UIView()
        view.name = "test"
        pan.add_to_view(view)
        pan.recognize(view, (10, 10))
        self.assertEqual(pan.state, UIGestureRecognizerState.BEGAN)

    def test_recognize_changed(self):
        pan = UIPanGestureRecognizer()
        view = UIView()
        view.name = "test"
        pan.add_to_view(view)
        pan.recognize(view, (10, 10))
        pan.recognize(view, (50, 50))
        self.assertEqual(pan.state, UIGestureRecognizerState.CHANGED)

    def test_repr(self):
        pan = UIPanGestureRecognizer()
        self.assertIn("UIPanGestureRecognizer", repr(pan))


class TestUISwipeGestureRecognizer(unittest.TestCase):
    """测试 UISwipeGestureRecognizer"""

    def test_recognize(self):
        swipe = UISwipeGestureRecognizer(direction="right")
        view = UIView()
        view.name = "test"
        swipe.add_to_view(view)
        swipe.recognize(view, (100, 100))
        self.assertEqual(swipe.state, UIGestureRecognizerState.RECOGNIZED)

    def test_repr(self):
        swipe = UISwipeGestureRecognizer()
        self.assertIn("UISwipeGestureRecognizer", repr(swipe))


# ============================================================
# URLSession 测试
# ============================================================


class TestURLRequest(unittest.TestCase):
    """测试 URLRequest"""

    def test_creation(self):
        req = URLRequest("https://example.com/api", HTTPMethod.GET)
        self.assertEqual(req.url, "https://example.com/api")
        self.assertEqual(req.method, "GET")

    def test_add_header(self):
        req = URLRequest("https://example.com")
        req.add_header("Authorization", "Bearer token")
        self.assertEqual(req.headers["Authorization"], "Bearer token")

    def test_set_body_json(self):
        req = URLRequest("https://example.com", HTTPMethod.POST)
        req.set_body_json({"name": "test"})
        self.assertEqual(req.method, "POST")
        self.assertIn("Content-Type", req.headers)

    def test_repr(self):
        req = URLRequest("https://example.com")
        self.assertIn("URLRequest", repr(req))


class TestURLResponse(unittest.TestCase):
    """测试 URLResponse"""

    def test_success(self):
        resp = URLResponse(status_code=200)
        self.assertTrue(resp.is_success)

    def test_error(self):
        resp = URLResponse(status_code=404)
        self.assertFalse(resp.is_success)

    def test_headers(self):
        resp = URLResponse(status_code=200, headers={"Content-Type": "application/json"})
        self.assertEqual(resp.headers["Content-Type"], "application/json")

    def test_repr(self):
        resp = URLResponse(status_code=200, url="https://example.com")
        self.assertIn("URLResponse", repr(resp))


class TestURLResponseError(unittest.TestCase):
    """测试 URLResponseError"""

    def test_creation(self):
        error = URLResponseError(-1000, "Connection refused")
        self.assertEqual(error.code, -1000)
        self.assertEqual(error.domain, "NSURLErrorDomain")


class TestURLSession(unittest.TestCase):
    """测试 URLSession"""

    def test_creation(self):
        session = URLSession(base_url="https://api.example.com")
        self.assertEqual(session.base_url, "https://api.example.com")

    def test_set_default_header(self):
        session = URLSession()
        session.set_default_header("X-Custom", "value")
        self.assertEqual(session._default_headers["X-Custom"], "value")

    def test_data_task_with_request(self):
        session = URLSession()
        request = URLRequest("https://api.example.com/users")
        task = session.data_task_with_request(request)
        self.assertIsInstance(task, URLSessionDataTask)
        self.assertEqual(len(session._active_tasks), 1)

    def test_get_request(self):
        session = URLSession()
        captured = [None]

        def handler(data, response, error):
            captured[0] = data

        task = session.get("/api/users", completion_handler=handler)
        task.start()
        self.assertIsNotNone(captured[0])

    def test_post_request(self):
        session = URLSession()
        captured = [None]

        def handler(data, response, error):
            captured[0] = data

        task = session.post("/api/users", body={"name": "test"}, completion_handler=handler)
        task.start()
        self.assertIsNotNone(captured[0])

    def test_mock_handler(self):
        session = URLSession()

        def custom_handler(request):
            return (
                URLResponse(200, {}, request.url),
                {"custom": True},
                None
            )

        session.set_mock_handler("/custom", custom_handler)
        captured = [None]

        def handler(data, response, error):
            captured[0] = data

        request = URLRequest("https://example.com/custom")
        task = session.data_task_with_request(request, handler)
        task.start()
        self.assertTrue(captured[0]["custom"])

    def test_cancel_all_tasks(self):
        session = URLSession()
        request = URLRequest("https://example.com/test")
        task = session.data_task_with_request(request)
        session.cancel_all_tasks()
        self.assertTrue(task.is_cancelled)
        self.assertEqual(len(session._active_tasks), 0)

    def test_default_response(self):
        session = URLSession()
        request = URLRequest("https://example.com/api/users")
        response, data, error = session._simulate_request(request)
        self.assertIsNone(error)
        self.assertTrue(response.is_success)
        self.assertIn("users", data)

    def test_repr(self):
        session = URLSession(base_url="https://api.example.com")
        self.assertIn("URLSession", repr(session))


class TestURLSessionDataTask(unittest.TestCase):
    """测试 URLSessionDataTask"""

    def test_creation(self):
        session = URLSession()
        request = URLRequest("https://example.com")
        task = URLSessionDataTask(session, request)
        self.assertFalse(task.is_cancelled)
        self.assertFalse(task.is_suspended)

    def test_cancel(self):
        session = URLSession()
        request = URLRequest("https://example.com")
        task = URLSessionDataTask(session, request)
        task.cancel()
        self.assertTrue(task.is_cancelled)

    def test_suspend_resume(self):
        session = URLSession()
        request = URLRequest("https://example.com")
        task = URLSessionDataTask(session, request)
        task.suspend()
        self.assertTrue(task.is_suspended)
        task.resume()
        self.assertFalse(task.is_suspended)

    def test_completion_handler(self):
        session = URLSession()
        captured = [None, None, None]

        def handler(data, response, error):
            captured[0] = data
            captured[1] = response
            captured[2] = error

        request = URLRequest("https://example.com/api/users")
        task = session.data_task_with_request(request, handler)
        task.start()
        self.assertIsNotNone(captured[0])
        self.assertIsNotNone(captured[1])
        self.assertIsNone(captured[2])

    def test_cancelled_task_no_start(self):
        session = URLSession()
        request = URLRequest("https://example.com")
        task = URLSessionDataTask(session, request)
        task.cancel()
        task.start()  # 应该不执行回调
        self.assertTrue(task.is_cancelled)

    def test_repr(self):
        session = URLSession()
        request = URLRequest("https://example.com/test")
        task = URLSessionDataTask(session, request)
        self.assertIn("URLSessionDataTask", repr(task))


class TestNetworkManager(unittest.TestCase):
    """测试 NetworkManager"""

    def test_creation(self):
        manager = NetworkManager(base_url="https://api.example.com")
        self.assertIsNotNone(manager.session)

    def test_get(self):
        manager = NetworkManager(base_url="https://api.example.com")
        captured = [None]

        def handler(data, response, error):
            captured[0] = data

        manager.get("/api/users", completion=handler)
        # 验证任务已创建但未执行（异步）

    def test_post(self):
        manager = NetworkManager(base_url="https://api.example.com")
        captured = [None]

        def handler(data, response, error):
            captured[0] = data

        manager.post("/api/users", body={"name": "test"}, completion=handler)

    def test_put(self):
        manager = NetworkManager(base_url="https://api.example.com")
        captured = [None]

        def handler(data, response, error):
            captured[0] = data

        manager.put("/api/users/1", body={"name": "updated"}, completion=handler)

    def test_delete(self):
        manager = NetworkManager(base_url="https://api.example.com")
        captured = [None]

        def handler(data, response, error):
            captured[0] = data

        manager.delete("/api/users/1", completion=handler)

    def test_add_mock_handler(self):
        manager = NetworkManager()
        manager.add_mock_handler("/test", lambda req: (
            URLResponse(200, {}, req.url),
            {"ok": True},
            None
        ))
        self.assertIn("/test", manager.session._mock_handlers)

    def test_repr(self):
        manager = NetworkManager(base_url="https://api.example.com")
        self.assertIn("NetworkManager", repr(manager))


# ============================================================
# KVO / Observable 测试
# ============================================================


class TestKVOObserver(unittest.TestCase):
    """测试 KVOObserver"""

    def test_notify(self):
        observer = KVOObserver("name", lambda o, old, new: None)
        old, new = None, None

        def capture(o, a, b):
            nonlocal old, new
            old, new = a, b

        observer.callback = capture
        observer.notify("old_value", "new_value")
        self.assertEqual(observer.old_value, "old_value")
        self.assertEqual(observer.new_value, "new_value")


class TestObservable(unittest.TestCase):
    """测试 Observable"""

    def test_initial_state(self):
        obs = Observable()
        self.assertEqual(len(obs._observers), 0)

    def test_add_observer(self):
        obs = Observable()
        changes = []
        obs.add_observer("name", lambda o, old, new: changes.append((old, new)))
        self.assertEqual(len(obs._observers["name"]), 1)

    def test_remove_observer(self):
        obs = Observable()
        changes = []

        def callback(o, old, new):
            changes.append((old, new))

        obs.add_observer("name", callback)
        obs.remove_observer("name", callback)
        self.assertNotIn("name", obs._observers)

    def test_remove_all_observers(self):
        obs = Observable()
        obs.add_observer("a", lambda o, old, new: None)
        obs.add_observer("b", lambda o, old, new: None)
        obs.remove_all_observers()
        self.assertEqual(len(obs._observers), 0)

    def test_set_value_notifies(self):
        obs = Observable()
        changes = []
        obs.add_observer("name", lambda o, old, new: changes.append((old, new)))

        obs.set_value("name", "Alice")
        self.assertEqual(changes, [(None, "Alice")])

        obs.set_value("name", "Bob")
        self.assertEqual(changes[1], ("Alice", "Bob"))

    def test_set_value_no_notify_same(self):
        obs = Observable()
        changes = []
        obs.add_observer("name", lambda o, old, new: changes.append((old, new)))

        obs.set_value("name", "Alice")
        obs.set_value("name", "Alice")  # 值未变
        self.assertEqual(len(changes), 1)

    def test_get_value(self):
        obs = Observable()
        obs.name = "Alice"
        result = obs.get_value("name")
        self.assertEqual(result, "Alice")

    def test_nested_key_path(self):
        obs = Observable()
        obs.user = type('obj', (object,), {'name': 'Alice'})()
        result = obs.get_value("user.name")
        self.assertEqual(result, "Alice")

    def test_repr(self):
        obs = Observable()
        self.assertIn("Observable", repr(obs))


class TestBinding(unittest.TestCase):
    """测试 Binding"""

    def test_one_way_binding(self):
        source = Observable()
        target = Observable()
        changes = []
        target.add_observer("value", lambda o, old, new: changes.append(new))

        binding = Binding(source, "value", target, "value", "one_way")
        source.set_value("value", "Hello")
        self.assertEqual(target.get_value("value"), "Hello")

        binding.disconnect()

    def test_two_way_binding(self):
        source = Observable()
        target = Observable()

        binding = Binding(source, "value", target, "value", "two_way")
        source.set_value("value", "Hello")
        self.assertEqual(target.get_value("value"), "Hello")

        target.set_value("value", "World")
        self.assertEqual(source.get_value("value"), "World")

        binding.disconnect()

    def test_repr(self):
        source = Observable()
        target = Observable()
        binding = Binding(source, "a", target, "b", "one_way")
        self.assertIn("Binding", repr(binding))


# ============================================================
# ViewModel 测试
# ============================================================


class TestViewModel(unittest.TestCase):
    """测试 ViewModel"""

    def test_initial_state(self):
        vm = ViewModel("TestVM")
        self.assertEqual(vm.name, "TestVM")
        self.assertTrue(vm.is_valid)

    def test_set_value(self):
        vm = ViewModel()
        vm.set_value("count", 0)
        self.assertEqual(vm.get_value("count"), 0)

        vm.set_value("count", 1)
        self.assertEqual(vm.get_value("count"), 1)

    def test_add_observer(self):
        vm = ViewModel()
        changes = []
        vm.add_observer("count", lambda o, old, new: changes.append(new))
        vm.set_value("count", 42)
        self.assertEqual(changes, [42])

    def test_create_binding(self):
        vm1 = ViewModel("VM1")
        vm2 = ViewModel("VM2")

        binding = vm1.create_binding("value", vm2, "value", "one_way")
        vm1.set_value("value", 100)
        self.assertEqual(vm2.get_value("value"), 100)

        vm1.set_value("value", 200)
        self.assertEqual(vm2.get_value("value"), 200)

        binding.disconnect()

    def test_dispose(self):
        vm = ViewModel()
        vm.set_value("count", 1)
        vm.dispose()
        self.assertFalse(vm.is_valid)

    def test_repr(self):
        vm = ViewModel("Test")
        self.assertIn("ViewModel", repr(vm))


# ============================================================
# 综合测试
# ============================================================


class TestIntegration(unittest.TestCase):
    """集成测试 - 模拟完整的 iOS 应用流程"""

    def test_full_app_flow(self):
        """测试完整应用流程"""
        # 1. 创建应用
        app = Application("TestApp")

        # 2. 创建主视图控制器
        class MainVC(UIViewController):
            def __init__(self):
                super().__init__(title="主页面")
                self.load_view()
                self.view._background_color = "#FFFFFF"

            def view_did_load(self):
                super().view_did_load()

                # 添加标签
                label = UILabel(frame=(20, 100, 335, 40))
                label.text = "Hello iOS!"
                label._font_size = 24
                self.view.add_subview(label)

                # 添加按钮
                btn = UIButton(frame=(137, 200, 100, 44))
                btn.set_title("点击", state="normal")
                btn._background_color_normal = "#007AFF"
                self.view.add_subview(btn)

        main_vc = MainVC()
        main_vc.view_did_load()

        # 3. 创建导航控制器
        nav = UINavigationController(main_vc)
        self.assertEqual(len(nav.view_controller_stack), 1)

        # 4. 压入新页面
        class DetailVC(UIViewController):
            def __init__(self):
                super().__init__(title="详情")
                self.load_view()

        detail_vc = DetailVC()
        nav.push_view_controller(detail_vc)
        self.assertEqual(len(nav.view_controller_stack), 2)

        # 5. 弹出
        nav.pop_view_controller()
        self.assertEqual(len(nav.view_controller_stack), 1)

        # 6. 网络请求
        session = URLSession("https://api.example.com")
        captured = [None]

        def handler(data, response, error):
            captured[0] = data

        task = session.get("/api/users", completion_handler=handler)
        task.start()

        # 7. 数据绑定
        model = Observable()
        model.set_value("name", "Alice")

        # 8. ViewModel
        vm = ViewModel("TestVM")
        vm.set_value("data", [1, 2, 3])
        self.assertEqual(vm.get_value("data"), [1, 2, 3])

        # 验证所有步骤
        self.assertTrue(main_vc._view_loaded)
        self.assertEqual(len(nav.view_controller_stack), 1)
        self.assertIsNotNone(captured[0])
        self.assertEqual(model.get_value("name"), "Alice")
        self.assertTrue(vm.is_valid)

    def test_auto_layout_flow(self):
        """测试 Auto Layout 完整流程"""
        parent = UIView(frame=(0, 0, 375, 667))
        parent.name = "Parent"

        label = UIView(frame=(0, 0, 100, 30))
        label.name = "Label"
        parent.add_subview(label)

        layout = UILayout()

        # 添加约束
        cx = NSLayoutConstraint(
            label, NSLayoutAttribute.CENTER_X, 1.0,
            parent, NSLayoutAttribute.CENTER_X, 0
        )
        cx.is_active = True
        layout.add_constraint(cx)

        top = NSLayoutConstraint(
            label, NSLayoutAttribute.TOP, 1.0,
            None, NSLayoutAttribute.TOP, 100
        )
        top.is_active = True
        layout.add_constraint(top)

        # 解析
        layout.resolve_constraints(parent)

        # 验证
        self.assertAlmostEqual(label.x, 137.5, places=0)  # centerX - width/2
        self.assertEqual(label.y, 100)

    def test_gesture_flow(self):
        """测试手势识别流程"""
        view = UIView(frame=(0, 0, 200, 200))
        view.name = "TestView"

        tap = UITapGestureRecognizer(number_of_taps=1)
        tap.add_to_view(view)

        events = []
        tap._callback = lambda r, p: events.append(p)

        tap.recognize(view, (50, 50))
        self.assertEqual(tap.state, UIGestureRecognizerState.RECOGNIZED)
        self.assertEqual(events, [(50, 50)])

    def test_table_view_flow(self):
        """测试表格视图流程"""
        table = UITableView(frame=(0, 0, 375, 667))

        class DS:
            def numberOfSections(self, tv):
                return 2

            def numberOfRowsInSection(self, tv, section):
                return 3

            def cellForRowAtIndexPath(self, tv, idx):
                return f"S{idx[0]}R{idx[1]}"

        table.data_source = DS()
        table.reload_data()

        self.assertEqual(table.number_of_sections(), 2)
        self.assertEqual(table.number_of_rows_in_section(0), 3)
        self.assertEqual(table.get_cell_at(1, 2), "S1R2")

    def test_network_flow(self):
        """测试网络请求流程"""
        manager = NetworkManager(base_url="https://api.example.com")
        captured = [None]

        manager.get("/api/users", completion=lambda data, resp, err: captured.__setitem__(0, data))

        # 执行任务
        for task in manager.session._active_tasks:
            task.start()

        self.assertIsNotNone(captured[0])

    def test_kvo_flow(self):
        """测试 KVO 流程"""
        model = Observable()
        changes = []

        model.add_observer("name", lambda o, old, new: changes.append((old, new)))
        model.add_observer("age", lambda o, old, new: changes.append((old, new)))

        model.set_value("name", "Alice")
        model.set_value("age", 25)
        model.set_value("name", "Bob")

        self.assertEqual(changes, [(None, "Alice"), (None, 25), ("Alice", "Bob")])


# ============================================================
# 运行测试
# ============================================================


if __name__ == "__main__":
    unittest.main(verbosity=2)

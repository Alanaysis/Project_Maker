"""
示例 4: 页面导航演示

演示鸿蒙 ArkUI 的页面生命周期和导航：
- 页面生命周期 (onCreate/onAppear/onDisappear/onDestroy)
- 页面栈管理
- 页面导航 (push/pop/replace)
- 组件生命周期 (aboutToAppear/aboutToDisappear)
"""

import sys
sys.path.insert(0, '.')

from src.lifecycle.page_lifecycle import PageLifecycleManager
from src.lifecycle.component_lifecycle import ComponentLifecycle, AreaChangeTracker


def demo_page_lifecycle():
    """演示页面生命周期"""
    print("=" * 60)
    print("1. 页面生命周期演示")
    print("=" * 60)

    lifecycle_mgr = PageLifecycleManager()

    # 注册页面和生命周期回调
    def home_on_create(params):
        print(f"  [Home] onCreate - 初始化首页数据")

    def home_on_will_appear(params):
        print(f"  [Home] onWillAppear - 即将显示")

    def home_on_appear(params):
        print(f"  [Home] onAppear - 已显示，开始加载数据")

    def home_on_will_disappear():
        print(f"  [Home] onWillDisappear - 即将隐藏")

    def home_on_disappear():
        print(f"  [Home] onDisappear - 已隐藏，暂停更新")

    def home_on_destroy():
        print(f"  [Home] onDestroy - 销毁，清理资源")

    lifecycle_mgr.register_page('Home', {
        'onCreate': home_on_create,
        'onWillAppear': home_on_will_appear,
        'onAppear': home_on_appear,
        'onWillDisappear': home_on_will_disappear,
        'onDisappear': home_on_disappear,
        'onDestroy': home_on_destroy,
    })

    # 注册详情页面
    def detail_on_create(params):
        print(f"  [Detail] onCreate - 加载详情数据: {params}")

    def detail_on_appear(params):
        print(f"  [Detail] onAppear - 显示详情页面")

    def detail_on_disappear():
        print(f"  [Detail] onDisappear - 隐藏详情页面")

    def detail_on_destroy():
        print(f"  [Detail] onDestroy - 销毁详情页面")

    lifecycle_mgr.register_page('Detail', {
        'onCreate': detail_on_create,
        'onWillAppear': lambda p: print(f"  [Detail] onWillAppear"),
        'onAppear': detail_on_appear,
        'onWillDisappear': lambda: print(f"  [Detail] onWillDisappear"),
        'onDisappear': detail_on_disappear,
        'onDestroy': detail_on_destroy,
    })

    # 注册设置页面
    lifecycle_mgr.register_page('Settings', {
        'onCreate': lambda p: print(f"  [Settings] onCreate"),
        'onWillAppear': lambda p: print(f"  [Settings] onWillAppear"),
        'onAppear': lambda p: print(f"  [Settings] onAppear"),
        'onWillDisappear': lambda: print(f"  [Settings] onWillDisappear"),
        'onDisappear': lambda: print(f"  [Settings] onDisappear"),
        'onDestroy': lambda: print(f"  [Settings] onDestroy"),
    })

    # 模拟页面导航流程
    print("\n--- 页面导航流程 ---")

    # 1. 创建首页
    print("\n[1] 创建首页")
    lifecycle_mgr.create_page('Home')

    # 2. 显示首页
    print("\n[2] 显示首页")
    lifecycle_mgr.push_page('Home')

    # 3. 导航到详情页面
    print("\n[3] 导航到详情页面")
    lifecycle_mgr.navigate_to('Detail', {'itemId': 123, 'title': '鸿蒙入门'})

    # 4. 返回首页
    print("\n[4] 返回首页")
    lifecycle_mgr.navigate_to('Home')

    # 5. 进入设置页面
    print("\n[5] 进入设置页面")
    lifecycle_mgr.push_page('Settings')

    # 6. 返回并销毁
    print("\n[6] 销毁所有页面")
    lifecycle_mgr.pop_page('Settings')
    lifecycle_mgr.destroy_page('Home')
    lifecycle_mgr.destroy_page('Detail')

    # 页面栈状态
    print(f"\n--- 页面栈 ---")
    stack = lifecycle_mgr.get_page_stack()
    print(f"当前页面栈: {stack if stack else '空'}")

    # 生命周期日志
    log = lifecycle_mgr.get_lifecycle_log()
    print(f"\n--- 生命周期日志 ({len(log)} 条) ---")
    for entry in log:
        print(f"  [{entry['page']}] {entry['event']}")


def demo_component_lifecycle():
    """演示组件生命周期"""
    print("\n" + "=" * 60)
    print("2. 组件生命周期演示")
    print("=" * 60)

    comp_lifecycle = ComponentLifecycle()

    # 注册组件生命周期
    def on_about_to_appear(context):
        print(f"  [组件] aboutToAppear - 准备渲染")

    def on_about_to_disappear(context):
        print(f"  [组件] aboutToDisappear - 准备清理")

    comp_lifecycle.on_about_to_appear('text_001', on_about_to_appear)
    comp_lifecycle.on_about_to_disappear('text_001', on_about_to_disappear)
    comp_lifecycle.on_about_to_appear('button_001', on_about_to_appear)
    comp_lifecycle.on_about_to_disappear('button_001', on_about_to_disappear)

    # 触发组件生命周期
    print("\n--- 组件出现 ---")
    comp_lifecycle.trigger_appear('text_001', {'width': 100, 'height': 30})
    comp_lifecycle.trigger_appear('button_001', {'width': 80, 'height': 40})

    print("\n--- 组件消失 ---")
    comp_lifecycle.trigger_disappear('text_001')
    comp_lifecycle.trigger_disappear('button_001')

    # 组件生命周期日志
    log = comp_lifecycle.get_lifecycle_log()
    print(f"\n组件生命周期日志 ({len(log)} 条):")
    for entry in log:
        print(f"  [{entry['component']}] {entry['event']}")


def demo_area_change():
    """演示区域变化追踪"""
    print("\n" + "=" * 60)
    print("3. 区域变化追踪 (onAreaChange)")
    print("=" * 60)

    tracker = AreaChangeTracker()

    def on_area_change(old_area, new_area):
        print(f"  [区域变化] {old_area} -> {new_area}")

    tracker.register('column_001', on_area_change)

    # 模拟区域变化
    print("\n--- 模拟区域变化 ---")
    tracker.set_area('column_001', {'x': 0, 'y': 0, 'width': 300, 'height': 200})
    tracker.set_area('column_001', {'x': 0, 'y': 0, 'width': 400, 'height': 300})
    tracker.set_area('column_001', {'x': 10, 'y': 20, 'width': 350, 'height': 250})

    # 获取当前区域
    current = tracker.get_area('column_001')
    print(f"\n当前区域: {current}")


def demo_navigation_flow():
    """演示完整的导航流程"""
    print("\n" + "=" * 60)
    print("4. 完整导航流程演示")
    print("=" * 60)

    lifecycle_mgr = PageLifecycleManager()

    # 注册页面
    pages = {
        'Login': {
            'onCreate': lambda p: print(f"  [Login] 创建登录页"),
            'onAppear': lambda p: print(f"  [Login] 显示登录页"),
            'onDisappear': lambda: print(f"  [Login] 隐藏登录页"),
            'onDestroy': lambda: print(f"  [Login] 销毁登录页"),
        },
        'Home': {
            'onCreate': lambda p: print(f"  [Home] 创建首页"),
            'onAppear': lambda p: print(f"  [Home] 显示首页"),
            'onDisappear': lambda: print(f"  [Home] 隐藏首页"),
            'onDestroy': lambda: print(f"  [Home] 销毁首页"),
        },
        'Detail': {
            'onCreate': lambda p: print(f"  [Detail] 创建详情页"),
            'onAppear': lambda p: print(f"  [Detail] 显示详情页"),
            'onDisappear': lambda: print(f"  [Detail] 隐藏详情页"),
            'onDestroy': lambda: print(f"  [Detail] 销毁详情页"),
        },
        'Settings': {
            'onCreate': lambda p: print(f"  [Settings] 创建设置页"),
            'onAppear': lambda p: print(f"  [Settings] 显示设置页"),
            'onDisappear': lambda: print(f"  [Settings] 隐藏设置页"),
            'onDestroy': lambda: print(f"  [Settings] 销毁设置页"),
        },
    }

    for name, callbacks in pages.items():
        lifecycle_mgr.register_page(name, callbacks)

    # 模拟用户操作流程
    print("\n--- 模拟用户操作 ---")

    print("\n1. 启动应用 -> 显示登录页")
    lifecycle_mgr.create_page('Login')
    lifecycle_mgr.push_page('Login')

    print("\n2. 用户登录 -> 进入首页")
    lifecycle_mgr.navigate_to('Home')

    print("\n3. 点击项目 -> 查看详情")
    lifecycle_mgr.push_page('Detail', {'projectId': 42})

    print("\n4. 返回 -> 回到首页")
    lifecycle_mgr.pop_page('Detail')

    print("\n5. 点击设置 -> 打开设置")
    lifecycle_mgr.push_page('Settings')

    print("\n6. 退出登录 -> 回到登录页")
    lifecycle_mgr.pop_page('Settings')
    lifecycle_mgr.navigate_to('Login')

    print("\n7. 销毁应用")
    for page in lifecycle_mgr.get_page_stack():
        lifecycle_mgr.destroy_page(page)

    print(f"\n--- 最终页面栈 ---")
    stack = lifecycle_mgr.get_page_stack()
    print(f"  {stack if stack else '空 (应用已销毁)'}")

    # 生命周期总览
    log = lifecycle_mgr.get_lifecycle_log()
    print(f"\n--- 生命周期事件总计 ({len(log)} 条) ---")
    events = {}
    for entry in log:
        event = entry['event']
        events[event] = events.get(event, 0) + 1
    for event, count in sorted(events.items()):
        print(f"  {event}: {count}")


if __name__ == '__main__':
    print("\n" + "#" * 60)
    print("# HarmonyOS 页面导航演示")
    print("# 鸿蒙 ArkUI 页面生命周期与导航学习示例")
    print("#" * 60)

    demo_page_lifecycle()
    demo_component_lifecycle()
    demo_area_change()
    demo_navigation_flow()

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)

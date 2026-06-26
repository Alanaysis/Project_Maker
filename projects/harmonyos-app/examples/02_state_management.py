"""
示例 2: 状态管理演示

演示鸿蒙 ArkUI 的状态管理机制：
- @State 组件内部状态
- @Prop 单向数据绑定
- @Link 双向数据绑定
- @Provide/@Consume 跨层级状态传递
- @ObjectLink 对象引用绑定

核心概念：
- 状态变化 -> UI 自动重建
- UI = f(state)
- 数据驱动 UI
"""

import sys
sys.path.insert(0, '.')

from src.state.manager import StateManager, StateVariable
from src.state.decorators import PropBinding, LinkBinding, ProvideBinding, ConsumeBinding
from src.state.observable import Observable, ObjectLink


def demo_state():
    """演示 @State 组件内部状态"""
    print("=" * 60)
    print("1. @State 组件内部状态")
    print("=" * 60)

    # 创建状态管理器（模拟组件实例）
    manager = StateManager(owner='Counter')

    # 定义状态变量（模拟 @State count: number = 0）
    count_var = manager.define_state('count', 0)
    manager.define_state('title', '计数器')
    manager.define_state('isRunning', False)

    print(f"\n初始状态: {manager.get_all_states()}")

    # 订阅状态变化
    def on_count_change(key, old, new):
        print(f"  [状态变化] {key}: {old} -> {new}")

    manager.subscribe_to('count', on_count_change)

    # 更新状态
    print("\n--- 更新状态 ---")
    manager.set_state('count', 1)
    manager.set_state('count', 5)
    manager.set_state('count', 10)
    manager.set_state('title', '我的计数器')

    # 批量更新
    print("\n--- 批量更新 ---")
    manager.begin_batch()
    manager.set_state('count', 20)
    manager.set_state('isRunning', True)
    manager.end_batch()

    print(f"\n最终状态: {manager.get_all_states()}")
    print(f"变更记录数: {len(manager.get_change_log())}")


def demo_prop_binding():
    """演示 @Prop 单向数据绑定"""
    print("\n" + "=" * 60)
    print("2. @Prop 单向数据绑定")
    print("=" * 60)

    # 父组件状态
    parent_manager = StateManager(owner='Parent')
    parent_manager.define_state('parentCount', 100)
    parent_manager.define_state('parentName', 'ParentApp')

    # 子组件通过 @Prop 接收父组件数据
    prop_count = PropBinding(parent_manager, 'parentCount')
    prop_name = PropBinding(parent_manager, 'parentName')

    print(f"\n--- 父组件状态 ---")
    print(f"  parentCount = {parent_manager.get_state('parentCount')}")
    print(f"  parentName = {parent_manager.get_state('parentName')}")

    # 子组件读取 @Prop
    prop_count.update()
    prop_name.update()
    print(f"\n--- 子组件 @Prop 值 ---")
    print(f"  @Prop count = {prop_count.value}")
    print(f"  @Prop name = {prop_name.value}")

    # 父组件更新，子组件同步
    print(f"\n--- 父组件更新后 ---")
    parent_manager.set_state('parentCount', 200)
    parent_manager.set_state('parentName', 'UpdatedParent')
    prop_count.update()
    prop_name.update()
    print(f"  @Prop count = {prop_count.value}")
    print(f"  @Prop name = {prop_name.value}")


def demo_link_binding():
    """演示 @Link 双向数据绑定"""
    print("\n" + "=" * 60)
    print("3. @Link 双向数据绑定")
    print("=" * 60)

    # 共享状态源
    shared_manager = StateManager(owner='Shared')
    shared_manager.define_state('sharedValue', 0)

    # 父组件通过 @Link 绑定
    parent_link = LinkBinding(shared_manager, 'sharedValue')
    # 子组件也通过 @Link 绑定
    child_link = LinkBinding(shared_manager, 'sharedValue')

    print(f"\n初始值: {shared_manager.get_state('sharedValue')}")

    # 父组件修改
    print("\n--- 父组件修改 ---")
    parent_link.value = 10
    print(f"  父组件设置: {parent_link.value}")
    print(f"  子组件读取: {child_link.value}")

    # 子组件修改
    print("\n--- 子组件修改 ---")
    child_link.value = 25
    print(f"  子组件设置: {child_link.value}")
    print(f"  父组件读取: {parent_link.value}")
    print(f"  共享状态: {shared_manager.get_state('sharedValue')}")


def demo_provide_consume():
    """演示 @Provide/@Consume 跨层级状态传递"""
    print("\n" + "=" * 60)
    print("4. @Provide/@Consume 跨层级状态传递")
    print("=" * 60)

    # 祖先组件提供状态
    ancestor_manager = StateManager(owner='Ancestor')
    ancestor_manager.define_state('theme', 'dark')
    ancestor_manager.define_state('language', 'zh-CN')
    ancestor_manager.define_state('fontSize', 16)

    # 后代组件消费状态
    theme_provide = ProvideBinding(ancestor_manager, 'theme')
    theme_consume = ConsumeBinding(ancestor_manager, 'theme')
    lang_consume = ConsumeBinding(ancestor_manager, 'language')

    print(f"\n--- 祖先组件 @Provide ---")
    print(f"  theme = {theme_provide.get_value()}")
    print(f"  language = {ancestor_manager.get_state('language')}")

    print(f"\n--- 后代组件 @Consume ---")
    print(f"  theme = {theme_consume.value}")
    print(f"  language = {lang_consume.value}")

    # 祖先更新，后代自动感知
    print(f"\n--- 祖先更新后 ---")
    ancestor_manager.set_state('theme', 'light')
    ancestor_manager.set_state('fontSize', 18)
    theme_consume.value  # 重新消费
    print(f"  后代感知 theme = {theme_consume.value}")
    print(f"  fontSize = {ancestor_manager.get_state('fontSize')}")


def demo_observable():
    """演示 Observable 可观察对象"""
    print("\n" + "=" * 60)
    print("5. Observable 可观察对象")
    print("=" * 60)

    # 创建可观察对象
    user = Observable()
    user._target = {
        'name': 'HarmonyOS Dev',
        'age': 25,
        'role': 'Developer',
    }

    # 订阅变化
    def on_user_change(key, old, new):
        print(f"  [变化] {key}: {old} -> {new}")

    user.subscribe('name', on_user_change)
    user.subscribe('age', on_user_change)

    print(f"\n初始状态: {user.get_all()}")

    # 修改属性，自动触发通知
    print("\n--- 修改属性 ---")
    user.name = 'NewName'
    user.age = 30
    user.role = 'Architect'

    print(f"\n最终状态: {user.get_all()}")

    # 批量更新
    print("\n--- 批量更新 ---")
    user.set_all({'name': 'BatchUpdate', 'age': 35})
    print(f"批量更新后: {user.get_all()}")


def demo_object_link():
    """演示 @ObjectLink 对象引用绑定"""
    print("\n" + "=" * 60)
    print("6. @ObjectLink 对象引用绑定")
    print("=" * 60)

    # 创建源对象
    source = Observable()
    source._target = {
        'x': 0,
        'y': 0,
        'width': 100,
        'height': 50,
    }

    # 创建对象引用
    obj_link = ObjectLink(source)

    print(f"\n源对象: {source.get_all()}")
    print(f"对象引用: {obj_link.value}")

    # 通过引用修改，源对象同步
    print("\n--- 通过引用修改 ---")
    obj_link.set('x', 50)
    obj_link.set('y', 30)
    print(f"源对象: {source.get_all()}")
    print(f"对象引用: {obj_link.value}")


if __name__ == '__main__':
    print("\n" + "#" * 60)
    print("# HarmonyOS 状态管理演示")
    print("# 鸿蒙 ArkUI 状态管理机制学习示例")
    print("#" * 60)

    demo_state()
    demo_prop_binding()
    demo_link_binding()
    demo_provide_consume()
    demo_observable()
    demo_object_link()

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)

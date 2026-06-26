#!/usr/bin/env python3
"""
Activity 生命周期演示 - Activity Lifecycle Demo

演示 Android Activity 的完整生命周期。
Demonstrates the complete lifecycle of an Android Activity.

学习重点 / Learning Focus:
1. Activity 的六个生命周期状态
2. 状态之间的转换条件
3. Task Stack 的管理
4. 生命周期观察者模式
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.lifecycle import Activity, TaskStack, LifecycleObserver, ActivityState, LifecycleAwareWorker


def demo_basic_lifecycle():
    """演示基本 Activity 生命周期"""
    print("=" * 60)
    print("1. Activity 基本生命周期演示")
    print("=" * 60)

    # 创建一个 Activity
    activity = Activity("MainActivity", "standard")

    # 手动调用生命周期方法
    print("\n--- 创建 Activity ---")
    activity.on_create({"saved": False})
    print(f"状态: {activity.state}")

    print("\n--- 启动 Activity ---")
    activity.on_start()
    print(f"状态: {activity.state}")

    print("\n--- 恢复 Activity ---")
    activity.on_resume()
    print(f"状态: {activity.state}")
    print(f"是否可交互: {activity.is_interactive}")

    print("\n--- 暂停 Activity ---")
    activity.on_pause()
    print(f"状态: {activity.state}")

    print("\n--- 停止 Activity ---")
    activity.on_stop()
    print(f"状态: {activity.state}")

    print("\n--- 销毁 Activity ---")
    activity.on_destroy()
    print(f"状态: {activity.state}")
    print(f"存活时间: {activity.get_lifecycle_duration():.2f}s")


def demo_task_stack():
    """演示 Task Stack 管理"""
    print("\n" + "=" * 60)
    print("2. Task Stack 任务栈演示")
    print("=" * 60)

    stack = TaskStack("main_task")

    # 创建并压入 Activity
    activity_a = Activity("MainActivity", "standard")
    activity_b = Activity("SecondActivity", "standard")
    activity_c = Activity("ThirdActivity", "standard")

    print("\n--- 压入 MainActivity ---")
    stack.push(activity_a)
    print(f"栈: {stack}")

    print("\n--- 压入 SecondActivity ---")
    stack.push(activity_b)
    print(f"栈: {stack}")

    print("\n--- 压入 ThirdActivity ---")
    stack.push(activity_c)
    print(f"栈: {stack}")

    print(f"\n当前栈顶: {stack.top.name}")

    print("\n--- 返回（弹出 ThirdActivity）---")
    popped = stack.pop()
    print(f"弹出的 Activity: {popped.name}")
    print(f"栈: {stack}")

    print("\n--- 返回（弹出 SecondActivity）---")
    popped = stack.pop()
    print(f"弹出的 Activity: {popped.name}")
    print(f"栈: {stack}")


def demo_lifecycle_observer():
    """演示生命周期观察者"""
    print("\n" + "=" * 60)
    print("3. 生命周期观察者演示")
    print("=" * 60)

    activity = Activity("ObserverDemoActivity", "standard")

    # 创建观察者
    observer = LifecycleObserver("logging_observer")

    @observer.on_create
    def on_create():
        print("  [Observer] Activity created!")

    @observer.on_start
    def on_start():
        print("  [Observer] Activity started!")

    @observer.on_resume
    def on_resume():
        print("  [Observer] Activity resumed!")

    @observer.on_pause
    def on_pause():
        print("  [Observer] Activity paused!")

    @observer.on_stop
    def on_stop():
        print("  [Observer] Activity stopped!")

    @observer.on_destroy
    def on_destroy():
        print("  [Observer] Activity destroyed!")

    # 附加观察者
    activity.owner.add_observer(observer)

    # 触发生命周期
    print("\n--- 触发生命周期 ---")
    activity.on_create()
    activity.on_start()
    activity.on_resume()
    activity.on_pause()
    activity.on_stop()
    activity.on_destroy()


def demo_lifecycle_aware_worker():
    """演示生命周期感知型组件"""
    print("\n" + "=" * 60)
    print("4. 生命周期感知型组件演示")
    print("=" * 60)

    activity = Activity("AwareDemoActivity", "standard")

    # 创建生命周期感知型工作器
    worker = LifecycleAwareWorker("NetworkWorker")
    worker.attach_to(activity.owner)

    print("\n--- 在 resumed 状态工作 ---")
    activity.on_create()
    activity.on_start()
    activity.on_resume()

    print(f"  工作器活跃: {worker.is_active}")
    print(f"  工作结果: {worker.do_work('fetch_data')}")

    print("\n--- 在 paused 状态工作 ---")
    activity.on_pause()
    print(f"  工作器活跃: {worker.is_active}")
    print(f"  工作结果: {worker.do_work('fetch_data')}")

    print("\n--- 恢复后工作 ---")
    activity.on_resume()
    print(f"  工作器活跃: {worker.is_active}")
    print(f"  工作结果: {worker.do_work('fetch_data')}")

    print("\n--- 工作日志 ---")
    for log in worker.get_work_log():
        print(f"  {log}")


def demo_launch_modes():
    """演示不同的启动模式"""
    print("\n" + "=" * 60)
    print("5. 启动模式演示")
    print("=" * 60)

    stack = TaskStack("launch_mode_demo")

    # standard 模式
    print("\n--- standard 模式 ---")
    for i in range(3):
        activity = Activity("MainActivity", "standard")
        stack.push(activity)
    print(f"栈: {stack}")
    stack.clear()

    # singleTop 模式
    print("\n--- singleTop 模式 ---")
    activity1 = Activity("MainActivity", "singleTop")
    stack.push(activity1)
    print(f"第一次压入: {stack}")
    activity2 = Activity("MainActivity", "singleTop")
    stack.push(activity2)
    print(f"第二次压入 (singleTop, 复用): {stack}")
    stack.clear()

    # singleTask 模式
    print("\n--- singleTask 模式 ---")
    activity1 = Activity("MainActivity", "singleTask")
    stack.push(activity1)
    activity2 = Activity("SecondActivity", "standard")
    stack.push(activity2)
    activity3 = Activity("ThirdActivity", "standard")
    stack.push(activity3)
    print(f"栈: {stack}")
    activity4 = Activity("MainActivity", "singleTask")
    stack.push(activity4)
    print(f"压入 MainActivity (singleTask, 清除上面): {stack}")


def demo_save_restore_state():
    """演示状态保存和恢复"""
    print("\n" + "=" * 60)
    print("6. 状态保存和恢复演示")
    print("=" * 60)

    # 创建 Activity 并保存状态
    activity = Activity("StateDemoActivity", "standard")
    activity.on_create()
    activity.on_start()
    activity.on_resume()

    # 模拟保存状态
    saved_state = {
        "username": "john_doe",
        "score": 100,
        "is_premium": True,
        "last_position": 50,
    }
    activity._saved_state = saved_state

    print(f"保存的状态: {saved_state}")

    # Activity 被销毁后重新创建
    activity.on_pause()
    activity.on_stop()
    activity.on_destroy()

    # 重新创建 Activity，恢复状态
    print("\n--- 重新创建 Activity，恢复状态 ---")
    activity2 = Activity("StateDemoActivity", "standard")
    activity2.on_create(saved_state)
    print(f"恢复的状态: {activity2._saved_state}")
    print(f"username: {activity2._saved_state.get('username')}")
    print(f"score: {activity2._saved_state.get('score')}")
    print(f"is_premium: {activity2._saved_state.get('is_premium')}")


def main():
    """主函数"""
    print("\n" + "📱 Android Activity 生命周期演示".center(60))
    print("   Activity Lifecycle Simulation Demo\n")

    demo_basic_lifecycle()
    demo_task_stack()
    demo_lifecycle_observer()
    demo_lifecycle_aware_worker()
    demo_launch_modes()
    demo_save_restore_state()

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

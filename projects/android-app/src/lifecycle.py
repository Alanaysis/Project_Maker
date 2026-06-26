"""
Activity 生命周期模拟 - Activity Lifecycle Simulation

Android 中，Activity 是应用的四大组件之一（Activity, Service, BroadcastReceiver, ContentProvider）。
每个 Activity 代表一个屏幕，拥有自己的生命周期。

In Android, an Activity is one of the four main app components.
Each Activity represents a single screen with its own lifecycle.

Activity 生命周期状态机：
- Created: onCreate() 已调用
- Started: onStart() 已调用
- Resumed: onResume() 已调用，用户可交互
- Paused: onPause() 已调用，失去焦点但仍可见
- Stopped: onStop() 已调用，完全不可见
- Destroyed: onDestroy() 已调用

状态转换：
  onCreate -> onStart -> onResume
  onResume <-> onPause -> onStop -> onDestroy
"""

import time
import logging
from enum import Enum
from typing import Callable, Dict, List, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class ActivityState(Enum):
    """Activity 生命周期状态枚举"""
    CREATED = "created"
    STARTED = "started"
    RESUMED = "resumed"
    PAUSED = "paused"
    STOPPED = "stopped"
    DESTROYED = "destroyed"


class FragmentState(Enum):
    """Fragment 生命周期状态枚举"""
    DETACHED = "detached"
    CREATED = "created"
    CREATED_VIEW = "created_view"
    STARTED = "started"
    RESUMED = "resumed"
    PAUSED = "paused"
    STOPPED = "stopped"
    DESTROYED_VIEW = "destroyed_view"
    DESTROYED = "destroyed"


@dataclass
class LifecycleEvent:
    """记录一次生命周期事件"""
    activity_name: str
    event_name: str
    timestamp: float = field(default_factory=time.time)
    details: Optional[str] = None

    def __str__(self):
        return (f"[{time.strftime('%H:%M:%S', time.localtime(self.timestamp))}] "
                f"{self.activity_name}: {self.event_name}"
                f"{f' - {self.details}' if self.details else ''}")


class LifecycleObserver:
    """
    生命周期观察者 - LifecycleObserver

    Android 中，LifecycleObserver 可以感知 Activity/Fragment 的生命周期变化，
    并在特定事件时执行操作，而不需要直接在生命周期方法中调用。

    In Android, a LifecycleObserver can sense Activity/Fragment lifecycle changes
    and execute actions on specific events without direct calls in lifecycle methods.
    """

    def __init__(self, name: str):
        self.name = name
        self._callbacks: Dict[str, List[Callable]] = {}

    def on_event(self, event: str, callback: Callable) -> None:
        """注册生命周期事件回调"""
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)

    def on_create(self, callback: Callable) -> None:
        self.on_event("onCreate", callback)

    def on_start(self, callback: Callable) -> None:
        self.on_event("onStart", callback)

    def on_resume(self, callback: Callable) -> None:
        self.on_event("onResume", callback)

    def on_pause(self, callback: Callable) -> None:
        self.on_event("onPause", callback)

    def on_stop(self, callback: Callable) -> None:
        self.on_event("onStop", callback)

    def on_destroy(self, callback: Callable) -> None:
        self.on_event("onDestroy", callback)

    def trigger(self, event: str, *args: Any, **kwargs: Any) -> None:
        """触发生命周期事件"""
        if event in self._callbacks:
            for cb in self._callbacks[event]:
                cb(*args, **kwargs)


class LifecycleOwner:
    """
    生命周期持有者 - LifecycleOwner

    Android 中，所有生命周期组件（Activity, Fragment, Service）都实现
    LifecycleOwner 接口，允许其他组件观察其生命周期。

    In Android, all lifecycle components (Activity, Fragment, Service) implement
    LifecycleOwner, allowing other components to observe their lifecycle.
    """

    def __init__(self, name: str):
        self.name = name
        self._state: ActivityState = ActivityState.CREATED
        self._observers: List[LifecycleObserver] = []
        self._event_log: List[LifecycleEvent] = []

    def add_observer(self, observer: LifecycleObserver) -> None:
        """添加生命周期观察者"""
        self._observers.append(observer)

    def log_event(self, event: str, details: Optional[str] = None) -> LifecycleEvent:
        """记录生命周期事件"""
        event_obj = LifecycleEvent(self.name, event, time.time(), details)
        self._event_log.append(event_obj)
        # 触发所有观察者的回调
        for observer in self._observers:
            observer.trigger(event)
        logger.debug(str(event_obj))
        return event_obj

    @property
    def state(self) -> ActivityState:
        return self._state

    def get_event_log(self) -> List[LifecycleEvent]:
        """获取事件日志"""
        return list(self._event_log)


class Activity:
    """
    Activity 类 - 模拟 Android Activity

    Activity 是 Android 应用的核心组件，代表一个带有用户界面的屏幕。
    每个 Activity 都有完整的生命周期，从创建到销毁。

    Activity is the core component of an Android app, representing a screen
    with a user interface. Each Activity has a complete lifecycle from creation to destruction.

    生命周期方法：
    - onCreate(): 初始化 UI 和数据
    - onStart(): 使 Activity 可见
    - onResume(): 开始与用户交互
    - onPause(): 暂停交互，保存数据
    - onStop(): Activity 不再可见
    - onDestroy(): 清理资源
    """

    def __init__(self, name: str, launch_mode: str = "standard"):
        """
        初始化 Activity

        Args:
            name: Activity 名称
            launch_mode: 启动模式 (standard, singleTop, singleTask, singleInstance)
        """
        self.name = name
        self.launch_mode = launch_mode
        self.owner = LifecycleOwner(name)
        self._state: ActivityState = ActivityState.CREATED
        self._saved_state: Dict[str, Any] = {}
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
        self._extras: Dict[str, Any] = {}  # Intent 传递的数据
        self._result_code: Optional[int] = None
        self._result_data: Dict[str, Any] = {}

        # 生命周期钩子 - 允许子类覆盖
        self._on_create_called = False
        self._on_start_called = False
        self._on_resume_called = False
        self._on_pause_called = False
        self._on_stop_called = False
        self._on_destroy_called = False

    @property
    def state(self) -> ActivityState:
        """获取当前生命周期状态"""
        return self._state

    @property
    def is_created(self) -> bool:
        return self._state != ActivityState.CREATED

    @property
    def is_started(self) -> bool:
        return self._state in (ActivityState.STARTED, ActivityState.RESUMED,
                                ActivityState.PAUSED, ActivityState.STOPPED)

    @property
    def is_resumed(self) -> bool:
        return self._state == ActivityState.RESUMED

    @property
    def is_visible(self) -> bool:
        return self._state in (ActivityState.STARTED, ActivityState.RESUMED)

    @property
    def is_interactive(self) -> bool:
        return self._state == ActivityState.RESUMED

    @property
    def is_destroyed(self) -> bool:
        return self._state == ActivityState.DESTROYED

    def get_lifecycle_duration(self) -> float:
        """获取 Activity 存活时间（秒）"""
        if self._start_time and self._end_time:
            return self._end_time - self._start_time
        if self._start_time:
            return time.time() - self._start_time
        return 0.0

    def set_result(self, code: int, data: Dict[str, Any]) -> None:
        """设置 Activity 返回结果"""
        self._result_code = code
        self._result_data = data

    def get_result(self) -> tuple:
        """获取 Activity 返回结果"""
        return self._result_code, self._result_data

    # ---- 生命周期方法 ----

    def on_create(self, savedInstanceState: Optional[Dict] = None) -> None:
        """
        onCreate - Activity 创建时调用

        这是 Activity 生命周期的第一个回调。在这里：
        1. 设置用户界面 (setContentView)
        2. 初始化组件 (findViewById)
        3. 恢复保存的状态 (savedInstanceState)

        This is the first callback in the Activity lifecycle. Here we:
        1. Set up the user interface
        2. Initialize components
        3. Restore saved state
        """
        self._state = ActivityState.CREATED
        self.owner.log_event("onCreate",
                             f"savedInstanceState={savedInstanceState is not None}")
        self._on_create_called = True

        # 恢复保存的状态
        if savedInstanceState:
            self._saved_state.update(savedInstanceState)

        # 调用子类钩子
        self._hook_on_create(savedInstanceState)

    def on_start(self) -> None:
        """
        onStart - Activity 即将变为可见时调用

        紧随 onCreate 之后，或在 Activity 从停止状态恢复时调用。
        """
        self._state = ActivityState.STARTED
        self._start_time = time.time()
        self.owner.log_event("onStart")
        self._on_start_called = True
        self._hook_on_start()

    def on_resume(self) -> None:
        """
        onResume - Activity 开始与用户交互时调用

        此时 Activity 位于任务栈顶部，获得用户焦点。
        这是与用户交互的阶段。
        """
        self._state = ActivityState.RESUMED
        self.owner.log_event("onResume")
        self._on_resume_called = True
        self._hook_on_resume()

    def on_pause(self) -> None:
        """
        onPause - 系统准备启动或恢复另一个 Activity 时调用

        通常用于：
        1. 保存未提交的数据
        2. 停止动画
        3. 释放系统资源
        """
        self._state = ActivityState.PAUSED
        self.owner.log_event("onPause", "saving state...")
        self._on_pause_called = True

        # 保存状态
        self._saved_state = self._hook_on_save_state()

        self._hook_on_pause()

    def on_stop(self) -> None:
        """
        onStop - Activity 不再可见时调用

        此时 Activity 进入后台。可以释放大量资源。
        """
        self._state = ActivityState.STOPPED
        self.owner.log_event("onStop")
        self._on_stop_called = True
        self._hook_on_stop()

    def on_destroy(self) -> None:
        """
        onDestroy - Activity 被销毁前调用

        这是最后一个回调。在此之后，Activity 对象将被销毁。
        用于清理资源：关闭线程、注销广播接收器等。
        """
        self._state = ActivityState.DESTROYED
        self._end_time = time.time()
        self.owner.log_event("onDestroy",
                             f"lived for {self.get_lifecycle_duration():.2f}s")
        self._on_destroy_called = True
        self._hook_on_destroy()

    def on_restart(self) -> None:
        """onRestart - Activity 从停止状态重新启动时调用"""
        self.owner.log_event("onRestart")

    # ---- 生命周期转换 ----

    def resume(self) -> None:
        """将 Activity 恢复到前台"""
        if self._state == ActivityState.PAUSED:
            self.on_start()  # 从暂停恢复需要先 onStart
            self.on_resume()
        elif self._state == ActivityState.STOPPED:
            self.on_start()
            self.on_resume()
        elif self._state == ActivityState.RESUMED:
            pass  # 已经在 resumed 状态

    def pause(self) -> None:
        """将 Activity 暂停到后台"""
        if self._state == ActivityState.RESUMED:
            self.on_pause()

    def stop(self) -> None:
        """将 Activity 停止"""
        if self._state in (ActivityState.RESUMED, ActivityState.PAUSED):
            self.on_pause()
            self.on_stop()
        elif self._state == ActivityState.STARTED:
            self.on_stop()

    def destroy(self) -> None:
        """销毁 Activity"""
        if self._state in (ActivityState.RESUMED, ActivityState.PAUSED):
            self.on_pause()
            self.on_stop()
            self.on_destroy()
        elif self._state == ActivityState.STOPPED:
            self.on_destroy()
        elif self._state == ActivityState.STARTED:
            self.on_destroy()
        elif self._state == ActivityState.CREATED:
            self.on_destroy()

    # ---- 子类钩子 ----

    def _hook_on_create(self, savedInstanceState: Optional[Dict]) -> None:
        """子类可以覆盖此方法"""
        pass

    def _hook_on_start(self) -> None:
        pass

    def _hook_on_resume(self) -> None:
        pass

    def _hook_on_pause(self) -> None:
        pass

    def _hook_on_stop(self) -> None:
        pass

    def _hook_on_destroy(self) -> None:
        pass

    def _hook_on_save_state(self) -> Dict[str, Any]:
        """子类可以覆盖此方法以保存状态"""
        return {}

    def __str__(self) -> str:
        return (f"Activity({self.name}, state={self._state.value}, "
                f"mode={self.launch_mode})")

    def __repr__(self) -> str:
        return self.__str__()


class TaskStack:
    """
    任务栈模拟 - Task Stack Simulation

    Android 使用任务栈（Task Stack）管理 Activity。
    新的 Activity 被压入栈顶，返回时从栈顶弹出。

    Android uses a Task Stack to manage Activities.
    New Activities are pushed onto the top, and returned from the top.
    """

    def __init__(self, name: str = "main_task"):
        self.name = name
        self._stack: List[Activity] = []
        self._history: List[str] = []

    @property
    def size(self) -> int:
        return len(self._stack)

    @property
    def top(self) -> Optional[Activity]:
        return self._stack[-1] if self._stack else None

    @property
    def is_empty(self) -> bool:
        return len(self._stack) == 0

    def push(self, activity: Activity) -> None:
        """将 Activity 压入栈顶"""
        # 如果栈顶 Activity 已存在且不是 singleTask，则先 pause/stop 它
        if self._stack and self._stack[-1].name == activity.name:
            if activity.launch_mode == "singleTop":
                self._stack[-1].owner.log_event("onNewIntent", "singleTop reused")
                return
            if activity.launch_mode == "singleTask":
                # 清除上面的所有 Activity
                while self._stack and self._stack[-1].name != activity.name:
                    self._stack[-1].on_pause()
                    self._stack[-1].on_stop()
                    self._stack[-1].on_destroy()
                    self._stack.pop()
                if self._stack:
                    self._stack[-1].owner.log_event("onNewIntent", "singleTask reused")
                return

        # 如果当前栈顶 Activity 存在，先 pause 它
        if self._stack:
            self._stack[-1].on_pause()

        self._stack.append(activity)
        self._history.append(f"push {activity.name}")
        activity.on_create(activity._extras if hasattr(activity, '_extras') else None)
        activity.on_start()
        activity.on_resume()

        logger.info(f"TaskStack '{self.name}': pushed {activity.name}, "
                     f"size={len(self._stack)}")

    def pop(self) -> Optional[Activity]:
        """从栈顶弹出 Activity"""
        if not self._stack:
            return None

        activity = self._stack.pop()
        activity.on_pause()
        activity.on_stop()
        activity.on_destroy()

        # 恢复新的栈顶 Activity
        if self._stack:
            top = self._stack[-1]
            if top._state == ActivityState.PAUSED:
                top.on_resume()
            elif top._state == ActivityState.STOPPED:
                top.on_start()
                top.on_resume()

        self._history.append(f"pop {activity.name}")
        logger.info(f"TaskStack '{self.name}': popped {activity.name}, "
                     f"size={len(self._stack)}")
        return activity

    def peek(self) -> Optional[Activity]:
        """查看栈顶 Activity 但不移除"""
        return self.top

    def clear(self) -> List[Activity]:
        """清除所有 Activity"""
        destroyed = []
        while self._stack:
            activity = self._stack.pop()
            activity.on_pause()
            activity.on_stop()
            activity.on_destroy()
            destroyed.append(activity)
        return destroyed

    def __str__(self) -> str:
        names = [a.name for a in self._stack]
        return f"TaskStack({self.name}): [{', '.join(names)}]"

    def __repr__(self) -> str:
        return self.__str__()


# ---- 生命周期感知组件示例 ----

class LifecycleAwareWorker:
    """
    生命周期感知型工作器 - Lifecycle-aware Worker

    Android 中，可以使用 LifecycleObserver 来创建生命周期感知的组件。
    例如：网络请求、数据库操作、位置更新等。

    In Android, you can create lifecycle-aware components using LifecycleObserver.
    For example: network requests, database operations, location updates.
    """

    def __init__(self, name: str):
        self.name = name
        self._lifecycle: Optional[LifecycleOwner] = None
        self._is_active = False
        self._work_log: List[str] = []
        self._observer: Optional[LifecycleObserver] = None

    def attach_to(self, owner: LifecycleOwner) -> None:
        """将工作器附加到生命周期持有者"""
        self._lifecycle = owner

        # 创建观察者并绑定到生命周期事件
        self._observer = LifecycleObserver(f"{self.name}_observer")

        @self._observer.on_resume
        def on_resume():
            self._is_active = True
            self._work_log.append(f"{self.name}: started working")
            logger.info(f"{self.name}: started working (lifecycle-aware)")

        @self._observer.on_pause
        def on_pause():
            self._is_active = False
            self._work_log.append(f"{self.name}: paused work")
            logger.info(f"{self.name}: paused work (lifecycle-aware)")

        @self._observer.on_destroy
        def on_destroy():
            self._is_active = False
            self._work_log.append(f"{self.name}: cleaned up")
            logger.info(f"{self.name}: cleaned up (lifecycle-aware)")

        owner.add_observer(self._observer)

        # 如果已经 resumed，立即开始工作
        if owner.state == ActivityState.RESUMED:
            self._is_active = True

    @property
    def is_active(self) -> bool:
        return self._is_active

    def do_work(self, work_type: str) -> str:
        """执行工作（仅在工作器活跃时）"""
        if not self._is_active:
            return f"{self.name}: skipped work (inactive)"
        result = f"{self.name}: completed {work_type}"
        self._work_log.append(result)
        return result

    def get_work_log(self) -> List[str]:
        return list(self._work_log)

"""
核心架构模块 - Core Architecture Module

本模块模拟 iOS 核心架构组件：
- RunLoop: 事件循环机制
- MainThread: 主线程管理
- Event: 事件模型
- Application: 应用生命周期
"""

import time
import threading
from typing import Callable, List, Optional, Dict, Any
from enum import Enum
from collections import deque
import traceback


class RunLoopMode(Enum):
    """RunLoop 运行模式 - 类比 iOS 的 RunLoop mode"""
    TRAPPING = "trapping"          # 无事件处理，RunLoop 休眠
    UNTRAPPED = "untripped"        # 即将处理事件
    WAITING = "waiting"            # 等待事件
    RUNNABLE = "runnable"          # 有事件可处理
    STOPPED = "stopped"            # 已停止


class RunLoop:
    """
    RunLoop 模拟器 - 模拟 iOS RunLoop 核心机制

    iOS RunLoop 是事件处理的核心：
    - 每个线程有且仅有一个 RunLoop
    - 主线程的 RunLoop 默认运行在 NSRunLoopMode.DEFAULT
    - RunLoop 管理 Input Sources（触摸、网络等）和 Timer Sources

    在 Python 中，我们用线程和队列模拟这一机制。
    """

    def __init__(self):
        self._mode = RunLoopMode.TRAPPING
        self._running = False
        self._input_sources: List[Callable] = []
        self._timer_sources: List[Dict[str, Any]] = []
        self._event_queue: deque = deque()
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._observers: List[Callable] = []

    @property
    def mode(self) -> RunLoopMode:
        return self._mode

    @property
    def is_running(self) -> bool:
        return self._running

    def add_input_source(self, source: Callable, name: str = ""):
        """
        添加输入源 - 模拟 addInputSource:forMode:

        Input Source 是外部事件的来源：
        - RunLoop 事件（触摸、网络回调等）
        - 端口事件（线程间通信）
        """
        with self._lock:
            source_info = {"source": source, "name": name}
            self._input_sources.append(source_info)
            print(f"[RunLoop] 添加输入源: {name or source.__name__}")

    def add_timer(self, interval: float, handler: Callable, name: str = ""):
        """
        添加定时器 - 模拟 addTimer:forMode:

        Timer 在指定间隔后触发事件，用于延迟执行和周期性任务。
        """
        with self._lock:
            timer = {
                "interval": interval,
                "handler": handler,
                "name": name,
                "last_fire": time.time(),
                "fired": False,
            }
            self._timer_sources.append(timer)
            print(f"[RunLoop] 添加定时器: {name or handler.__name__} (间隔: {interval}s)")

    def add_observer(self, observer: Callable):
        """添加 RunLoop 状态变化观察者"""
        self._observers.append(observer)
        self._notify_observers("add_observer")

    def _notify_observers(self, event: str):
        """通知所有观察者"""
        for obs in self._observers:
            try:
                obs(event)
            except Exception:
                pass

    def _update_mode(self, new_mode: RunLoopMode):
        """更新 RunLoop 模式并通知观察者"""
        old_mode = self._mode
        self._mode = new_mode
        if old_mode != new_mode:
            self._notify_observers(f"mode_changed:{old_mode.value}->{new_mode.value}")

    def _process_timers(self):
        """处理所有到期的定时器"""
        now = time.time()
        expired = []
        for timer in self._timer_sources:
            if now - timer["last_fire"] >= timer["interval"]:
                try:
                    timer["handler"]()
                    timer["last_fire"] = now
                    timer["fired"] = True
                except Exception as e:
                    print(f"[RunLoop] 定时器执行错误 [{timer['name']}]: {e}")

    def _process_events(self):
        """处理事件队列中的事件"""
        while self._event_queue:
            event = self._event_queue.popleft()
            try:
                event["callback"](*event.get("args", ()), **event.get("kwargs", {}))
            except Exception as e:
                print(f"[RunLoop] 事件处理错误: {e}")
                traceback.print_exc()

    def _run_loop_iteration(self):
        """执行一次 RunLoop 迭代"""
        with self._lock:
            if not self._running:
                return False

            if self._event_queue:
                self._update_mode(RunLoopMode.RUNNABLE)
                self._process_events()
            elif self._input_sources:
                self._update_mode(RunLoopMode.UNTRAPPED)
                # 处理输入源
                for source in self._input_sources:
                    try:
                        source["source"]()
                    except Exception as e:
                        print(f"[RunLoop] 输入源错误 [{source['name']}]: {e}")
                self._update_mode(RunLoopMode.WAITING)
            else:
                self._update_mode(RunLoopMode.TRAPPING)

        # 处理定时器（在锁外执行）
        self._process_timers()
        return True

    def run(self):
        """
        启动 RunLoop - 模拟 [[NSRunLoop mainRunLoop] run]

        这是 iOS 应用的主循环，持续处理事件直到应用退出。
        """
        self._running = True
        self._update_mode(RunLoopMode.WAITING)
        self._notify_observers("run_loop_started")
        print("[RunLoop] 启动主运行循环")

        iteration = 0
        while self._running:
            self._run_loop_iteration()
            iteration += 1
            # 避免 CPU 空转
            if not self._event_queue and not self._input_sources:
                time.sleep(0.01)
            # 每 100 次迭代打印状态
            if iteration % 100 == 0:
                print(f"[RunLoop] 状态: mode={self._mode.value}, "
                      f"queue={len(self._event_queue)}, "
                      f"timers={len(self._timer_sources)}")

        self._update_mode(RunLoopMode.STOPPED)
        self._notify_observers("run_loop_stopped")
        print("[RunLoop] 运行循环已停止")

    def stop(self):
        """停止 RunLoop - 模拟 [[NSRunLoop mainRunLoop] stop]"""
        self._running = False
        self._notify_observers("run_loop_stop_requested")
        print("[RunLoop] 收到停止信号")

    def perform_on_main(self, callback: Callable, *args, **kwargs):
        """
        在主线程上执行回调 - 模拟 dispatch_async(dispatch_get_main_queue(), ...)

        iOS 中，UI 更新必须在主线程进行。
        这里我们将回调放入事件队列，由 RunLoop 处理。
        """
        with self._lock:
            self._event_queue.append({
                "callback": callback,
                "args": args,
                "kwargs": kwargs,
            })
        print(f"[RunLoop] 调度主线程任务: {callback.__name__}")

    def delay(self, seconds: float, callback: Callable, *args, **kwargs):
        """
        延迟执行 - 模拟 dispatch_after

        在指定秒数后执行回调。
        """
        def delayed_call():
            time.sleep(seconds)
            self.perform_on_main(callback, *args, **kwargs)

        thread = threading.Thread(target=delayed_call, daemon=True)
        thread.start()
        print(f"[RunLoop] 延迟任务: {callback.__name__} (延迟: {seconds}s)")


class MainThread:
    """
    MainThread 管理 - 模拟 iOS 主线程

    iOS 架构规则：
    - UI 更新必须在主线程
    - 主线程通过 RunLoop 处理事件
    - 其他线程可以通过 GCD (Grand Central Dispatch) 调度到主线程
    """

    _instance: Optional["MainThread"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._run_loop = RunLoop()
        self._thread: Optional[threading.Thread] = None
        self._is_main: bool = False

    @property
    def run_loop(self) -> RunLoop:
        return self._run_loop

    @property
    def is_main_thread(self) -> bool:
        """检查当前线程是否为主线程"""
        return self._is_main

    @property
    def current_thread_id(self) -> int:
        return threading.current_thread().ident or 0

    @property
    def main_thread_id(self) -> Optional[int]:
        return self._thread.ident if self._thread else None

    def execute_on_main(self, callback: Callable, *args, **kwargs):
        """
        确保在主线程执行回调

        如果当前已经在主线程，直接执行。
        否则，通过 RunLoop 调度。
        """
        if threading.current_thread() is self._thread:
            callback(*args, **kwargs)
        else:
            self._run_loop.perform_on_main(callback, *args, **kwargs)

    def start(self):
        """启动主线程"""
        self._is_main = True
        self._thread = threading.current_thread()
        print(f"[MainThread] 主线程已启动 (ID: {self.current_thread_id})")

    def stop(self):
        """停止主线程"""
        self._run_loop.stop()
        self._is_main = False
        print("[MainThread] 主线程已停止")


class Application:
    """
    Application 生命周期 - 模拟 UIApplication

    iOS 应用生命周期：
    - UIApplicationMain: 创建 application 和 delegate
    - application:didFinishLaunchingWithOptions: 启动完成
    - applicationDidBecomeActive: 应用激活
    - applicationWillResignActive: 应用失去焦点
    - applicationDidEnterBackground: 进入后台
    - applicationWillEnterForeground: 回到前台
    - applicationWillTerminate: 应用终止
    """

    def __init__(self, name: str = "IOSApp"):
        self.name = name
        self._delegate = None
        self._is_active = False
        self._is_background = False
        self._run_loop = RunLoop()
        self._launch_options: Dict[str, Any] = {}
        self._lifecycle_events: List[str] = []

    @property
    def is_active(self) -> bool:
        return self._is_active

    @property
    def is_background(self) -> bool:
        return self._is_background

    @property
    def lifecycle_events(self) -> List[str]:
        return self._lifecycle_events.copy()

    def set_delegate(self, delegate):
        """设置应用代理"""
        self._delegate = delegate
        print(f"[Application] 设置代理: {delegate.__class__.__name__}")

    def _record_event(self, event: str):
        """记录生命周期事件"""
        self._lifecycle_events.append(event)
        print(f"[Application] [{event}]")

    def _call_delegate(self, method: str, *args):
        """调用代理方法"""
        if self._delegate and hasattr(self._delegate, method):
            try:
                getattr(self._delegate, method)(*args)
            except Exception as e:
                print(f"[Application] 代理方法 {method} 错误: {e}")

    def launch(self, launch_options: Optional[Dict[str, Any]] = None):
        """
        启动应用 - 模拟 UIApplicationMain

        应用启动流程：
        1. 创建 UIApplication 实例
        2. 创建应用代理
        3. 调用 didFinishLaunching
        4. 启动 RunLoop
        """
        self._launch_options = launch_options or {}
        self._record_event("applicationWillFinishLaunching")

        if self._delegate and hasattr(self._delegate, "application_didFinishLaunching"):
            self._delegate.application_didFinishLaunching(self, self._launch_options)

        self._record_event("applicationDidFinishLaunching")
        self._record_event("applicationDidBecomeActive")
        self._is_active = True
        self._is_background = False

        if self._delegate and hasattr(self._delegate, "applicationDidBecomeActive"):
            self._delegate.applicationDidBecomeActive(self)

        print(f"[Application] 应用 '{self.name}' 已启动")

    def enter_background(self):
        """应用进入后台"""
        self._record_event("applicationDidEnterBackground")
        self._is_active = False
        self._is_background = True

        if self._delegate and hasattr(self._delegate, "applicationDidEnterBackground"):
            self._delegate.applicationDidEnterBackground(self)

        print("[Application] 应用进入后台")

    def enter_foreground(self):
        """应用回到前台"""
        self._record_event("applicationWillEnterForeground")
        self._is_background = False

        if self._delegate and hasattr(self._delegate, "applicationWillEnterForeground"):
            self._delegate.applicationWillEnterForeground(self)

        self._record_event("applicationDidBecomeActive")
        self._is_active = True

        if self._delegate and hasattr(self._delegate, "applicationDidBecomeActive"):
            self._delegate.applicationDidBecomeActive(self)

        print("[Application] 应用回到前台")

    def terminate(self):
        """终止应用"""
        self._record_event("applicationWillTerminate")

        if self._delegate and hasattr(self._delegate, "applicationWillTerminate"):
            self._delegate.applicationWillTerminate(self)

        self._is_active = False
        self._is_background = False
        self._run_loop.stop()
        print(f"[Application] 应用 '{self.name}' 已终止")

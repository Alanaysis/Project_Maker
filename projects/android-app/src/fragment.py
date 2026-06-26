"""
Fragment 生命周期模拟 - Fragment Lifecycle Simulation

Fragment 是 Activity 中的可复用行为或 UI 部分。
Fragment 有自己的生命周期，依赖于宿主 Activity 的生命周期。

A Fragment is a reusable behavior or UI portion within an Activity.
Fragments have their own lifecycle dependent on the host Activity's lifecycle.

Fragment 生命周期状态：
- Detached: Fragment 已创建但未附加到 Activity
- Created: Fragment 已创建，View 未创建
- CreatedView: Fragment 的 View 已创建
- Started: Fragment 可见
- Resumed: Fragment 可交互
- Paused: Fragment 暂停
- Stopped: Fragment 停止
- DestroyedView: Fragment 的 View 已销毁
- Destroyed: Fragment 已销毁

Fragment 与 Activity 的生命周期关系：
- Activity 的 onCreate 触发 Fragment 的 onCreate
- Activity 的 onStart 触发 Fragment 的 onStart
- Activity 的 onResume 触发 Fragment 的 onResume
- Activity 的 onPause 触发 Fragment 的 onPause
- Activity 的 onStop 触发 Fragment 的 onStop
- Activity 的 onDestroy 触发 Fragment 的 onDestroy
"""

import logging
from enum import Enum
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class FragmentState(Enum):
    """Fragment 生命周期状态"""
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
class FragmentTransaction:
    """
    Fragment 事务 - Fragment Transaction

    用于管理 Fragment 的添加、替换、移除等操作。
    支持事务的原子性（commit/rollback）。

    Manages Fragment add, replace, remove operations.
    Supports atomic transactions (commit/rollback).
    """

    operations: List[Dict[str, Any]] = field(default_factory=list)
    tag: Optional[str] = None
    name: Optional[str] = None
    is_committed: bool = False
    is_add_to_back_stack: bool = False
    enter_anim: Optional[str] = None
    exit_anim: Optional[str] = None
    pop_enter_anim: Optional[str] = None
    pop_exit_anim: Optional[str] = None

    def add(self, container_id: int, fragment: "Fragment",
            fragment_tag: Optional[str] = None) -> "FragmentTransaction":
        """添加 Fragment"""
        self.operations.append({
            "type": "add",
            "container_id": container_id,
            "fragment": fragment,
            "tag": fragment_tag,
        })
        return self

    def replace(self, container_id: int, fragment: "Fragment",
                fragment_tag: Optional[str] = None) -> "FragmentTransaction":
        """替换 container 中的 Fragment"""
        self.operations.append({
            "type": "replace",
            "container_id": container_id,
            "fragment": fragment,
            "tag": fragment_tag,
        })
        return self

    def remove(self, fragment: "Fragment") -> "FragmentTransaction":
        """移除 Fragment"""
        self.operations.append({
            "type": "remove",
            "fragment": fragment,
        })
        return self

    def detach(self, fragment: "Fragment") -> "FragmentTransaction":
        """分离 Fragment（保留实例但销毁 View）"""
        self.operations.append({
            "type": "detach",
            "fragment": fragment,
        })
        return self

    def attach(self, fragment: "Fragment") -> "FragmentTransaction":
        """重新附加 Fragment"""
        self.operations.append({
            "type": "attach",
            "fragment": fragment,
        })
        return self

    def set_animations(self, enter: str, exit: str,
                       pop_enter: str = None, pop_exit: str = None) -> "FragmentTransaction":
        """设置过渡动画"""
        self.enter_anim = enter
        self.exit_anim = exit
        self.pop_enter_anim = pop_enter
        self.pop_exit_anim = pop_exit
        return self

    def add_to_back_stack(self, name: Optional[str] = None) -> "FragmentTransaction":
        """添加到返回栈"""
        self.is_add_to_back_stack = True
        self.name = name or str(len(self.operations))
        return self

    def commit(self) -> str:
        """提交事务"""
        self.is_committed = True
        op_types = [op["type"] for op in self.operations]
        return f"FragmentTransaction committed: {op_types}"

    def __str__(self) -> str:
        ops = ", ".join(op["type"] for op in self.operations)
        return f"FragmentTransaction[{ops}] (committed={self.is_committed})"


class Fragment:
    """
    Fragment 类 - 模拟 Android Fragment

    Fragment 代表 Activity 中的可复用行为或 UI 片段。
    它可以独立于 Activity 管理自己的生命周期。

    A Fragment represents a reusable behavior or UI portion within an Activity.
    It can manage its own lifecycle independently of the Activity.

    Fragment 使用场景：
    1. 多窗格 UI（平板 vs 手机）
    2. 可复用 UI 组件
    3. 导航抽屉内容
    4. 动态 UI 变化
    """

    def __init__(self, name: str = "Fragment"):
        self.name = name
        self._state: FragmentState = FragmentState.DETACHED
        self._activity: Optional[Any] = None
        self._view: Optional[Any] = None
        self._tag: Optional[str] = None
        self._container_id: int = 0
        self._is_removed: bool = False
        self._is_detached: bool = False
        self._saved_state: Dict[str, Any] = {}
        self._arguments: Dict[str, Any] = {}
        self._event_log: List[str] = []
        self._start_time: Optional[float] = None

    @property
    def state(self) -> FragmentState:
        return self._state

    @property
    def is_detached(self) -> bool:
        return self._state == FragmentState.DETACHED

    @property
    def is_created(self) -> bool:
        return self._state not in (FragmentState.DETACHED, FragmentState.CREATED)

    @property
    def is_resumed(self) -> bool:
        return self._state == FragmentState.RESUMED

    @property
    def is_visible(self) -> bool:
        return self._state in (FragmentState.STARTED, FragmentState.RESUMED)

    @property
    def is_removed(self) -> bool:
        return self._is_removed

    def set_tag(self, tag: str) -> "Fragment":
        self._tag = tag
        return self

    def set_arguments(self, args: Dict[str, Any]) -> "Fragment":
        self._arguments.update(args)
        return self

    def get_argument(self, key: str, default: Any = None) -> Any:
        return self._arguments.get(key, default)

    def set_container(self, container_id: int) -> "Fragment":
        self._container_id = container_id
        return self

    # ---- 生命周期方法 ----

    def on_attach(self, activity: Any) -> None:
        """Fragment 附加到 Activity 时调用"""
        self._activity = activity
        self._state = FragmentState.DETACHED
        self._event_log.append("onAttach")
        self._hook_on_attach(activity)
        logger.debug(f"Fragment {self.name}: onAttach")

    def on_create(self, savedInstanceState: Optional[Dict] = None) -> None:
        """Fragment 创建时调用"""
        self._state = FragmentState.CREATED
        self._event_log.append("onCreate")
        if savedInstanceState:
            self._saved_state.update(savedInstanceState)
        self._hook_on_create(savedInstanceState)
        logger.debug(f"Fragment {self.name}: onCreate")

    def on_create_view(self, inflater: Any, container: Any,
                       savedInstanceState: Optional[Dict] = None) -> Any:
        """创建 Fragment 的 View"""
        self._state = FragmentState.CREATED_VIEW
        self._event_log.append("onCreateView")
        view = self._hook_on_create_view(inflater, container, savedInstanceState)
        self._view = view
        logger.debug(f"Fragment {self.name}: onCreateView")
        return view

    def on_start(self) -> None:
        """Fragment 变为可见时调用"""
        self._state = FragmentState.STARTED
        self._start_time = __import__('time').time()
        self._event_log.append("onStart")
        self._hook_on_start()
        logger.debug(f"Fragment {self.name}: onStart")

    def on_resume(self) -> None:
        """Fragment 可交互时调用"""
        self._state = FragmentState.RESUMED
        self._event_log.append("onResume")
        self._hook_on_resume()
        logger.debug(f"Fragment {self.name}: onResume")

    def on_pause(self) -> None:
        """Fragment 暂停时调用"""
        self._state = FragmentState.PAUSED
        self._event_log.append("onPause")
        self._hook_on_pause()
        logger.debug(f"Fragment {self.name}: onPause")

    def on_stop(self) -> None:
        """Fragment 不可见时调用"""
        self._state = FragmentState.STOPPED
        self._event_log.append("onStop")
        self._hook_on_stop()
        logger.debug(f"Fragment {self.name}: onStop")

    def on_destroy_view(self) -> None:
        """Fragment 的 View 被销毁时调用"""
        self._state = FragmentState.DESTROYED_VIEW
        self._event_log.append("onDestroyView")
        self._view = None
        self._hook_on_destroy_view()
        logger.debug(f"Fragment {self.name}: onDestroyView")

    def on_destroy(self) -> None:
        """Fragment 销毁时调用"""
        self._state = FragmentState.DESTROYED
        self._event_log.append("onDestroy")
        self._hook_on_destroy()
        logger.debug(f"Fragment {self.name}: onDestroy")

    def on_detach(self) -> None:
        """Fragment 从 Activity 分离时调用"""
        self._state = FragmentState.DETACHED
        self._activity = None
        self._event_log.append("onDetach")
        self._hook_on_detach()
        logger.debug(f"Fragment {self.name}: onDetach")

    def on_save_state(self) -> Dict[str, Any]:
        """保存 Fragment 状态"""
        self._saved_state = self._hook_on_save_state()
        return dict(self._saved_state)

    # ---- 事务处理 ----

    def handle_transaction(self, transaction: FragmentTransaction) -> str:
        """处理 Fragment 事务"""
        if not transaction.is_committed:
            transaction.commit()

        results = []
        for op in transaction.operations:
            op_type = op["type"]

            if op_type == "add":
                self._state = FragmentState.CREATED
                results.append(f"added fragment to container {op['container_id']}")

            elif op_type == "replace":
                # 先销毁当前 View
                if self._view:
                    self.on_destroy_view()
                self._state = FragmentState.CREATED
                self._container_id = op["container_id"]
                results.append(f"replaced fragment in container {op['container_id']}")

            elif op_type == "remove":
                self.on_destroy_view()
                self._is_removed = True
                results.append(f"removed fragment")

            elif op_type == "detach":
                self.on_destroy_view()
                self._is_detached = True
                results.append(f"detached fragment")

            elif op_type == "attach":
                self._is_detached = False
                self.on_create_view(None, None, None)
                self.on_start()
                self.on_resume()
                results.append(f"attached fragment")

        return "; ".join(results)

    # ---- 生命周期钩子 ----

    def _hook_on_attach(self, activity: Any) -> None:
        pass

    def _hook_on_create(self, savedInstanceState: Optional[Dict]) -> None:
        pass

    def _hook_on_create_view(self, inflater: Any, container: Any,
                              savedInstanceState: Optional[Dict]) -> Any:
        return None

    def _hook_on_start(self) -> None:
        pass

    def _hook_on_resume(self) -> None:
        pass

    def _hook_on_pause(self) -> None:
        pass

    def _hook_on_stop(self) -> None:
        pass

    def _hook_on_destroy_view(self) -> None:
        pass

    def _hook_on_destroy(self) -> None:
        pass

    def _hook_on_detach(self) -> None:
        pass

    def _hook_on_save_state(self) -> Dict[str, Any]:
        return {}

    def get_lifecycle_duration(self) -> float:
        """获取 Fragment 活跃时间"""
        if self._start_time:
            return __import__('time').time() - self._start_time
        return 0.0

    def get_event_log(self) -> List[str]:
        return list(self._event_log)

    def __str__(self) -> str:
        return (f"Fragment({self.name}, state={self._state.value}, "
                f"removed={self._is_removed}, detached={self._is_detached})")

    def __repr__(self) -> str:
        return self.__str__()


class FragmentManager:
    """
    Fragment 管理器 - Fragment Manager

    管理 Activity 中所有 Fragment 的生命周期和事务。

    Manages the lifecycle and transactions of all Fragments
    within an Activity.
    """

    def __init__(self, activity_name: str):
        self.activity_name = activity_name
        self._fragments: Dict[str, Fragment] = {}
        self._back_stack: List[List[FragmentTransaction]] = []
        self._container_id: int = 1

    def begin_transaction(self) -> FragmentTransaction:
        """开始新的 Fragment 事务"""
        return FragmentTransaction()

    def add_fragment(self, fragment: Fragment, tag: Optional[str] = None) -> str:
        """添加 Fragment"""
        fragment_tag = tag or f"frag_{len(self._fragments)}"
        fragment.set_tag(fragment_tag)
        self._fragments[fragment_tag] = fragment
        transaction = self.begin_transaction().add(self._container_id, fragment, fragment_tag)
        result = fragment.handle_transaction(transaction)
        return f"Added {fragment.name} as '{fragment_tag}': {result}"

    def replace_fragment(self, fragment: Fragment, tag: Optional[str] = None) -> str:
        """替换 Fragment"""
        # 保存当前栈状态
        if self._back_stack:
            self._back_stack.append([])

        fragment_tag = tag or f"frag_{len(self._fragments)}"
        fragment.set_tag(fragment_tag)
        self._fragments[fragment_tag] = fragment

        # 移除所有现有 Fragment
        for existing in list(self._fragments.values()):
            if existing is not fragment:
                existing.handle_transaction(self.begin_transaction().remove(existing))

        transaction = self.begin_transaction().replace(self._container_id, fragment, fragment_tag)
        result = fragment.handle_transaction(transaction)
        return f"Replaced with {fragment.name}: {result}"

    def remove_fragment(self, fragment: Fragment) -> str:
        """移除 Fragment"""
        transaction = self.begin_transaction().remove(fragment)
        result = fragment.handle_transaction(transaction)
        tag = fragment._tag or str(fragment.id)
        if fragment._tag in self._fragments:
            del self._fragments[fragment._tag]
        return f"Removed {fragment.name}: {result}"

    def find_fragment_by_tag(self, tag: str) -> Optional[Fragment]:
        """通过 tag 查找 Fragment"""
        return self._fragments.get(tag)

    def get_active_fragments(self) -> List[Fragment]:
        """获取所有活跃 Fragment"""
        return [f for f in self._fragments.values() if not f.is_removed]

    def pop_back_stack(self) -> Optional[str]:
        """弹出返回栈顶层"""
        if not self._back_stack:
            return None
        ops = self._back_stack.pop()
        return f"Popped back stack ({len(ops)} operations)"

    def get_fragment_count(self) -> int:
        return len(self._fragments)

    def __str__(self) -> str:
        names = [f.name for f in self._fragments.values()]
        return (f"FragmentManager(activity={self.activity_name}, "
                f"fragments={names}, back_stack={len(self._back_stack)})")

    def __repr__(self) -> str:
        return self.__str__()

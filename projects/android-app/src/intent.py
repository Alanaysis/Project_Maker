"""
Intent 和导航模拟 - Intent & Navigation Simulation

Intent 是 Android 中组件间通信的核心机制。它可以：
1. 启动 Activity
2. 启动 Service
3. 发送 Broadcast

Intent 分为两种类型：
- 显式 Intent: 指定目标组件名称
- 隐式 Intent: 通过 Action/Category/Data 匹配目标组件

Navigation（导航）管理应用内屏幕之间的过渡。
"""

import logging
import uuid
from enum import Enum
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """Intent 类型"""
    ACTIVITY = "activity"
    SERVICE = "service"
    BROADCAST = "broadcast"


class IntentAction(Enum):
    """常用 Intent Action"""
    VIEW = "android.intent.action.VIEW"
    EDIT = "android.intent.action.EDIT"
    MAIN = "android.intent.action.MAIN"
    LAUNCHER = "android.intent.action.LAUNCHER"
    PICK = "android.intent.action.PICK"
    SEARCH = "android.intent.action.SEARCH"
    DIAL = "android.intent.action.DIAL"
    CALL = "android.intent.action.CALL"
    SEND = "android.intent.action.SEND"


class DataScheme(Enum):
    """数据协议"""
    HTTP = "http"
    HTTPS = "https"
    TEL = "tel"
    MAILTO = "mailto"
    FILE = "file"
    CONTENT = "content"


@dataclass
class Intent:
    """
    Intent 类 - 模拟 Android Intent

    Intent 封装了组件间通信的信息。

    An Intent is a messaging object used to communicate between components.

    属性：
    - action: 动作描述（如 VIEW, EDIT）
    - component: 目标组件（显式 Intent 使用）
    - data: 数据 URI
    - category: 类别
    - extras: 额外数据（键值对）
    - flags: 标志位
    """

    action: Optional[str] = None
    component: Optional[str] = None
    data: Optional[str] = None
    data_scheme: Optional[str] = None
    category: Optional[str] = None
    extras: Dict[str, Any] = field(default_factory=dict)
    flags: List[str] = field(default_factory=list)
    request_code: Optional[int] = None
    source_activity: Optional[str] = None
    target_activity: Optional[str] = None
    intent_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def put_extra(self, key: str, value: Any) -> "Intent":
        """添加额外数据"""
        self.extras[key] = value
        return self

    def get_extra(self, key: str, default: Any = None) -> Any:
        """获取额外数据"""
        return self.extras.get(key, default)

    def has_extra(self, key: str) -> bool:
        """检查是否存在额外数据"""
        return key in self.extras

    def set_data(self, uri: str, scheme: Optional[str] = None) -> "Intent":
        """设置数据 URI"""
        self.data = uri
        if scheme:
            self.data_scheme = scheme
        return self

    def set_action(self, action: str) -> "Intent":
        """设置动作"""
        self.action = action
        return self

    def set_component(self, component: str) -> "Intent":
        """设置目标组件（显式 Intent）"""
        self.component = component
        return self

    def set_category(self, category: str) -> "Intent":
        """设置类别"""
        self.category = category
        return self

    def add_flag(self, flag: str) -> "Intent":
        """添加标志位"""
        if flag not in self.flags:
            self.flags.append(flag)
        return self

    @property
    def is_explicit(self) -> bool:
        """是否为显式 Intent（指定了目标组件）"""
        return self.component is not None

    @property
    def is_implicit(self) -> bool:
        """是否为隐式 Intent（未指定目标组件）"""
        return self.component is None

    def __str__(self) -> str:
        parts = [f"Intent(id={self.intent_id})"]
        if self.action:
            parts.append(f"action={self.action}")
        if self.component:
            parts.append(f"component={self.component}")
        if self.data:
            parts.append(f"data={self.data}")
        if self.category:
            parts.append(f"category={self.category}")
        if self.extras:
            parts.append(f"extras={self.extras}")
        if self.flags:
            parts.append(f"flags={self.flags}")
        return " ".join(parts)

    def __repr__(self) -> str:
        return self.__str__()


class Navigator:
    """
    导航器 - Navigator

    管理 Activity 之间的导航和过渡。

    Manages navigation and transitions between Activities.

    支持的导航操作：
    - navigate: 导航到目标 Activity
    - navigate_back: 返回
    - navigate_up: 向上导航
    - clear_stack: 清除导航栈
    """

    def __init__(self, name: str = "main"):
        self.name = name
        self._history: List[Intent] = []
        self._activity_stack: List[str] = []
        self._callbacks: Dict[str, List[Callable]] = {
            "on_navigate": [],
            "on_back": [],
            "on_up": [],
        }

    @property
    def current_activity(self) -> Optional[str]:
        return self._activity_stack[-1] if self._activity_stack else None

    @property
    def history_depth(self) -> int:
        return len(self._history)

    def navigate(self, intent: Intent) -> Dict[str, Any]:
        """
        导航到目标 Activity

        处理显式和隐式 Intent 的导航。

        Args:
            intent: 导航 Intent

        Returns:
            导航结果
        """
        result = {
            "success": False,
            "intent": intent,
            "details": "",
        }

        if intent.is_explicit:
            # 显式 Intent：直接导航到目标
            result["success"] = True
            result["details"] = f"navigate to {intent.component}"
            result["target"] = intent.component
            self._activity_stack.append(intent.component)
            self._history.append(intent)
            logger.info(f"[{self.name}] navigate ({intent.component})")

        else:
            # 隐式 Intent：通过 Action/Category/Data 匹配
            target = self._resolve_intent(intent)
            if target:
                result["success"] = True
                result["details"] = f"resolved to {target}"
                result["target"] = target
                self._activity_stack.append(target)
                self._history.append(intent)
                logger.info(f"[{self.name}] implicit intent -> {target}")
            else:
                result["details"] = "no matching component found"
                logger.warning(f"[{self.name}] implicit intent not resolved")

        # 触发导航回调
        for cb in self._callbacks.get("on_navigate", []):
            cb(intent)

        return result

    def navigate_back(self) -> Optional[str]:
        """
        返回到上一个 Activity

        Returns:
            返回的目标 Activity 名称
        """
        if len(self._activity_stack) <= 1:
            return None

        popped = self._activity_stack.pop()
        result = self._activity_stack[-1] if self._activity_stack else None

        for cb in self._callbacks.get("on_back", []):
            cb(popped)

        logger.info(f"[{self.name}] back: {popped} -> {result}")
        return result

    def navigate_up(self) -> Optional[str]:
        """
        向上导航（到父 Activity）

        Returns:
            父 Activity 名称
        """
        if len(self._activity_stack) <= 1:
            return None

        # 向上导航通常只弹出一层
        popped = self._activity_stack.pop()
        result = self._activity_stack[-1] if self._activity_stack else None

        for cb in self._callbacks.get("on_up", []):
            cb(popped)

        logger.info(f"[{self.name}] up: {popped} -> {result}")
        return result

    def clear_stack(self) -> List[str]:
        """清除导航栈"""
        cleared = list(self._activity_stack)
        self._activity_stack = []
        self._history = []
        logger.info(f"[{self.name}] stack cleared ({len(cleared)} activities)")
        return cleared

    def add_callback(self, event: str, callback: Callable) -> None:
        """添加导航回调"""
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)

    def _resolve_intent(self, intent: Intent) -> Optional[str]:
        """
        解析隐式 Intent 的目标组件

        通过 Action/Category/Data 匹配目标 Activity。

        In a real Android system, this would query the PackageManager
        to find matching components. Here we use a simple registry.
        """
        # 这个解析逻辑由 NavigatorRegistry 管理
        return None

    def get_history(self) -> List[Intent]:
        """获取导航历史"""
        return list(self._history)

    def __str__(self) -> str:
        return (f"Navigator({self.name}): "
                f"stack={[self._activity_stack[-1] if self._activity_stack else 'none']}, "
                f"history={len(self._history)}")


class NavigatorRegistry:
    """
    导航注册表 - Navigator Registry

    管理隐式 Intent 的 Action/Category/Data 到目标组件的映射。

    Manages the mapping of implicit Intent Actions/Categories/Data
    to target components.
    """

    def __init__(self):
        self._action_map: Dict[str, List[str]] = {}
        self._category_map: Dict[str, List[str]] = {}
        self._data_map: Dict[str, List[str]] = {}
        self._activity_map: Dict[str, str] = {}  # 组件名 -> 类名

    def register_activity(self, component: str, activity_class: str,
                          action: Optional[str] = None,
                          category: Optional[str] = None,
                          data_pattern: Optional[str] = None) -> None:
        """注册 Activity 到 Intent 过滤器"""
        self._activity_map[component] = activity_class
        if action:
            if action not in self._action_map:
                self._action_map[action] = []
            self._action_map[action].append(component)
        if category:
            if category not in self._category_map:
                self._category_map[category] = []
            self._category_map[category].append(component)
        if data_pattern:
            if data_pattern not in self._data_map:
                self._data_map[data_pattern] = []
            self._data_map[data_pattern].append(component)

    def resolve(self, intent: Intent) -> Optional[str]:
        """解析隐式 Intent"""
        candidates: List[str] = []

        if intent.action:
            candidates = self._action_map.get(intent.action, [])

        if not candidates:
            candidates = list(self._activity_map.keys())

        if intent.category and intent.category in self._category_map:
            category_targets = set(self._category_map[intent.category])
            candidates = [c for c in candidates if c in category_targets]

        if intent.data:
            for pattern, targets in self._data_map.items():
                if intent.data.startswith(pattern):
                    candidates = [c for c in candidates if c in targets]
                    break

        return candidates[0] if candidates else None

    def get_component_class(self, component: str) -> Optional[str]:
        """获取组件对应的类名"""
        return self._activity_map.get(component)

    def get_registered_activities(self) -> List[str]:
        """获取所有注册的 Activity"""
        return list(self._activity_map.keys())


class BackHandler:
    """
    返回键处理器 - Back Press Handler

    处理 Android 返回键事件。

    Handles Android back button events.
    """

    def __init__(self):
        self._handlers: List[Callable] = []
        self._default_handler: Optional[Callable] = None

    def register(self, handler: Callable) -> None:
        """注册返回键处理器"""
        self._handlers.append(handler)

    def set_default(self, handler: Callable) -> None:
        """设置默认返回键处理器"""
        self._default_handler = handler

    def on_back(self) -> bool:
        """
        处理返回键事件

        Returns:
            True 如果事件被消费（处理），False 否则
        """
        # 按注册顺序处理
        for handler in self._handlers:
            if handler():
                return True

        # 如果没有处理器消费，使用默认处理器
        if self._default_handler:
            return self._default_handler()

        return False

    def clear(self) -> None:
        """清除所有处理器"""
        self._handlers = []

"""
SharedPreferences 模拟 - SharedPreferences Simulation

SharedPreferences 是 Android 上简单的键值对存储机制，
主要用于存储应用配置和少量数据。

SharedPreferences is a simple key-value storage mechanism on Android,
primarily used for storing app configuration and small amounts of data.

特点：
- 持久化存储（数据保存在 XML 文件中）
- 线程安全
- 支持多种数据类型（String, int, boolean, float, long, Set<String>）
- 通过 Editor 进行写入操作
- 支持事务提交（commit/apply）

Usage patterns:
- App settings/preferences
- User session data
- Feature flags
- Last known state
"""

import json
import time
import logging
from typing import Optional, Dict, Any, Set, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SharedPreferenceEntry:
    """单个 SharedPreferences 条目"""
    key: str
    value: Any
    entry_type: str  # "string", "int", "boolean", "float", "long", "set"
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "type": self.entry_type,
            "timestamp": self.timestamp,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "SharedPreferenceEntry":
        return SharedPreferenceEntry(
            key=data["key"],
            value=data["value"],
            entry_type=data["type"],
            timestamp=data.get("timestamp", time.time()),
        )


class SharedPreferencesEditor:
    """
    SharedPreferences Editor - 编辑器

    用于修改 SharedPreferences 中的数据。
    支持链式调用。

    Used to modify data in SharedPreferences.
    Supports method chaining.
    """

    def __init__(self, prefs: "SharedPreferences"):
        self._prefs = prefs
        self._changes: Dict[str, Any] = {}
        self._remove_keys: List[str] = []
        self._clear = False
        self._committed = False

    def put_string(self, key: str, value: str) -> "SharedPreferencesEditor":
        """存储字符串值"""
        self._changes[key] = value
        return self

    def put_int(self, key: str, value: int) -> "SharedPreferencesEditor":
        """存储整数值"""
        self._changes[key] = value
        return self

    def put_boolean(self, key: str, value: bool) -> "SharedPreferencesEditor":
        """存储布尔值"""
        self._changes[key] = value
        return self

    def put_float(self, key: str, value: float) -> "SharedPreferencesEditor":
        """存储浮点数值"""
        self._changes[key] = value
        return self

    def put_long(self, key: str, value: int) -> "SharedPreferencesEditor":
        """存储长整数值"""
        self._changes[key] = value
        return self

    def put_string_set(self, key: str, value: Set[str]) -> "SharedPreferencesEditor":
        """存储字符串集合"""
        self._changes[key] = list(value)  # 列表存储
        return self

    def remove(self, key: str) -> "SharedPreferencesEditor":
        """移除指定键"""
        self._remove_keys.append(key)
        return self

    def clear(self) -> "SharedPreferencesEditor":
        """清除所有数据"""
        self._clear = True
        return self

    def commit(self) -> bool:
        """
        同步提交更改

        Returns:
            True 如果提交成功
        """
        if self._committed:
            return False

        if self._clear:
            self._prefs._data = {}
            logger.info(f"SharedPreferences: clear all data")
        else:
            for key, value in self._changes.items():
                self._prefs._set_entry(key, value)
            for key in self._remove_keys:
                self._prefs._remove_entry(key)

        self._committed = True
        logger.info(f"SharedPreferences: committed {len(self._changes)} changes, "
                     f"removed {len(self._remove_keys)} keys")
        return True

    def apply(self) -> None:
        """
        异步提交更改

        apply() 是 commit() 的异步版本：
        - commit() 同步写入，立即返回
        - apply() 异步写入，无返回值
        """
        # apply 最终也会调用 commit 的逻辑
        if self._clear:
            self._prefs._data = {}
            logger.info(f"SharedPreferences: apply clear all data")
        else:
            for key, value in self._changes.items():
                self._prefs._set_entry(key, value)
            for key in self._remove_keys:
                self._prefs._remove_entry(key)

        logger.info(f"SharedPreferences: applied {len(self._changes)} changes")


class SharedPreferences:
    """
    SharedPreferences 类 - 模拟 Android SharedPreferences

    提供简单的键值对持久化存储。

    Provides simple key-value persistent storage.

    使用示例：
        # 获取 SharedPreferences
        prefs = getSharedPreferences("settings", "MODE_PRIVATE")

        # 写入数据
        editor = prefs.edit()
        editor.put_string("username", "john")
        editor.put_int("age", 25)
        editor.put_boolean("is_premium", True)
        editor.commit()

        # 读取数据
        username = prefs.getString("username", "default")
        age = prefs.getInt("age", 0)
        is_premium = prefs.getBoolean("is_premium", False)
    """

    def __init__(self, name: str = "default_prefs", mode: str = "MODE_PRIVATE"):
        self.name = name
        self.mode = mode  # MODE_PRIVATE, MODE_WORLD_READABLE, MODE_WORLD_WRITEABLE
        self._data: Dict[str, SharedPreferenceEntry] = {}
        self._listeners: List["SharedPreferences.OnSharedPreferenceChangeListener"] = []

    def edit(self) -> SharedPreferencesEditor:
        """创建 Editor 以修改数据"""
        return SharedPreferencesEditor(self)

    def get_string(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """获取字符串值"""
        entry = self._data.get(key)
        if entry and entry.entry_type == "string":
            return entry.value
        return default

    def get_int(self, key: str, default: int = 0) -> int:
        """获取整数值"""
        entry = self._data.get(key)
        if entry and entry.entry_type in ("int", "long"):
            return int(entry.value)
        return default

    def get_boolean(self, key: str, default: bool = False) -> bool:
        """获取布尔值"""
        entry = self._data.get(key)
        if entry and entry.entry_type == "boolean":
            return bool(entry.value)
        return default

    def get_float(self, key: str, default: float = 0.0) -> float:
        """获取浮点数值"""
        entry = self._data.get(key)
        if entry and entry.entry_type == "float":
            return float(entry.value)
        return default

    def get_long(self, key: str, default: int = 0) -> int:
        """获取长整数值"""
        entry = self._data.get(key)
        if entry and entry.entry_type in ("int", "long"):
            return int(entry.value)
        return default

    def get_string_set(self, key: str, default: Optional[Set[str]] = None) -> Optional[Set[str]]:
        """获取字符串集合"""
        entry = self._data.get(key)
        if entry and entry.entry_type == "set":
            return set(entry.value)
        return default

    def contains(self, key: str) -> bool:
        """检查是否包含指定键"""
        return key in self._data

    def get_all(self) -> Dict[str, Any]:
        """获取所有数据"""
        result = {}
        for entry in self._data.values():
            result[entry.key] = entry.value
        return result

    def get_keys(self) -> Set[str]:
        """获取所有键"""
        return {entry.key for entry in self._data.values()}

    def get_entry_count(self) -> int:
        """获取条目数量"""
        return len(self._data)

    def _set_entry(self, key: str, value: Any) -> None:
        """内部方法：设置条目"""
        # 确定数据类型
        if isinstance(value, str):
            entry_type = "string"
        elif isinstance(value, bool):
            entry_type = "boolean"
        elif isinstance(value, float):
            entry_type = "float"
        elif isinstance(value, int):
            entry_type = "int"
        elif isinstance(value, list):
            entry_type = "set"
        else:
            entry_type = "string"

        self._data[key] = SharedPreferenceEntry(
            key=key, value=value, entry_type=entry_type
        )

        # 通知监听器
        for listener in self._listeners:
            listener.on_preference_changed(self.name, key)

    def _remove_entry(self, key: str) -> None:
        """内部方法：移除条目"""
        if key in self._data:
            del self._data[key]
            for listener in self._listeners:
                listener.on_preference_changed(self.name, key)

    def register_listener(self, listener: "SharedPreferences.OnSharedPreferenceChangeListener") -> None:
        """注册监听器"""
        self._listeners.append(listener)

    def unregister_listener(self, listener: "SharedPreferences.OnSharedPreferenceChangeListener") -> None:
        """注销监听器"""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def __str__(self) -> str:
        return (f"SharedPreferences(name='{self.name}', "
                f"entries={self.get_entry_count()}, "
                f"mode={self.mode})")

    def __repr__(self) -> str:
        return self.__str__()

    # 内部类：监听器接口
    class OnSharedPreferenceChangeListener:
        """SharedPreferences 变化监听器接口"""
        def on_preference_changed(self, prefs_name: str, key: str) -> None:
            """当偏好变化时调用"""
            pass


# ---- 便捷函数 ----

def get_shared_preferences(name: str = "default_prefs",
                           mode: str = "MODE_PRIVATE") -> SharedPreferences:
    """获取 SharedPreferences 的便捷函数"""
    return SharedPreferences(name, mode)

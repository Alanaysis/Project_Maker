"""
可观察对象 - Observable Object

实现 JavaScript/ArkTS 风格的响应式对象。
通过 Proxy 机制自动追踪属性的读写。

ArkTS 中，@State 装饰的对象会自动成为可观察的。
这里用 Python 模拟这个机制。
"""

from typing import Any, Callable, Dict, List, Optional, TypeVar
from .manager import StateManager

T = TypeVar('T')


class Observable:
    """
    可观察对象

    模拟 ArkTS 中 @State 装饰的类实例：
    - 所有属性变化自动通知订阅者
    - 支持嵌套对象追踪
    - 支持批量更新

    Python 模拟（因为 Python 3.7+ 支持 __setattr__ 拦截）：
    ```
    class Counter:
        def __init__(self):
            self.count = 0

    counter = Observable(Counter())
    counter.subscribe('count', lambda key, old, new: print(f'{key}: {old} -> {new}'))
    counter.count = 5  # 自动触发通知
    ```
    """

    def __init__(self, obj: Any = None):
        self._target = obj or {}
        self._observers: Dict[str, List[Callable]] = {}
        self._is_batching = False
        self._batched_changes: List[str] = []

    def __getattr__(self, name: str):
        if name.startswith('_'):
            raise AttributeError(name)
        return self._target.get(name)

    def __setattr__(self, name: str, value: Any):
        if name.startswith('_'):
            super().__setattr__(name, value)
            return

        old_value = self._target.get(name)
        self._target[name] = value

        # 通知观察者
        if name in self._observers:
            if self._is_batching and name not in self._batched_changes:
                self._batched_changes.append(name)
            else:
                for callback in self._observers[name]:
                    try:
                        callback(name, old_value, value)
                    except Exception as e:
                        print(f'[Observable Error] Observer callback failed: {e}')

    def __getattr__(self, name: str):
        if name in ('_target', '_observers', '_is_batching', '_batched_changes'):
            return super().__getattribute__(name)
        return self._target.get(name)

    def subscribe(self, key: str, callback: Callable):
        """订阅特定属性的变化"""
        if key not in self._observers:
            self._observers[key] = []
        self._observers[key].append(callback)

    def unsubscribe(self, key: str, callback: Callable):
        """取消订阅"""
        if key in self._observers:
            if callback in self._observers[key]:
                self._observers[key].remove(callback)

    def begin_batch(self):
        """开始批量更新"""
        self._is_batching = True
        self._batched_changes = []

    def end_batch(self):
        """结束批量更新"""
        self._is_batching = False
        for key in self._batched_changes:
            if key in self._observers:
                value = self._target.get(key)
                for callback in self._observers[key]:
                    try:
                        callback(key, None, value)
                    except Exception as e:
                        print(f'[Observable Error] Batch observer callback failed: {e}')
        self._batched_changes = []

    def get_all(self) -> Dict[str, Any]:
        """获取所有属性"""
        return dict(self._target)

    def set_all(self, data: Dict[str, Any]):
        """批量设置所有属性"""
        self.begin_batch()
        for key, value in data.items():
            self._target[key] = value
        self.end_batch()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return dict(self._target)

    def __repr__(self):
        return f'Observable({self._target})'


class ObjectLink:
    """
    @ObjectLink 对象引用绑定

    传递对象的引用而非值。
    子组件直接修改对象属性，父组件能感知变化。

    适用于复杂对象的状态共享。
    """

    def __init__(self, source: Observable):
        self._source = source
        self._proxy = Observable()
        self._sync()

    def _sync(self):
        """同步源对象的所有属性到代理"""
        for key, value in self._source._target.items():
            self._proxy._target[key] = value

    def get(self, key: str) -> Any:
        return self._proxy._target.get(key)

    def set(self, key: str, value: Any):
        self._proxy._target[key] = value
        # 同时更新源对象
        self._source._target[key] = value
        # 通知源对象的观察者
        if key in self._source._observers:
            for callback in self._source._observers[key]:
                callback(key, None, value)

    @property
    def value(self) -> Dict[str, Any]:
        return dict(self._proxy._target)

    def __repr__(self):
        return f'ObjectLink({self._proxy._target})'

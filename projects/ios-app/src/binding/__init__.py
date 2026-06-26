"""
数据绑定模块 - Data Binding Module

本模块模拟 iOS KVO (Key-Value Observing) 数据绑定机制：
- KVO: 观察属性变化
- Observable: 可观察对象
- Binding: 双向绑定
"""

import weakref
from typing import Any, Callable, Dict, List, Optional, Set, Type
from collections import defaultdict


class KVOObserver:
    """
    KVOObserver - KVO 观察者

    模拟 iOS KVO (Key-Value Observing) 机制。
    KVO 允许对象监听其他对象属性的变化。

    在 Python 中，我们使用装饰器和回调来实现类似功能。
    """

    def __init__(self, key_path: str, callback: Callable, options: Optional[Dict] = None):
        self.key_path = key_path
        self.callback = callback
        self.options = options or {}
        self._old_value: Any = None
        self._new_value: Any = None

    @property
    def old_value(self) -> Any:
        return self._old_value

    @property
    def new_value(self) -> Any:
        return self._new_value

    def notify(self, old_value: Any, new_value: Any):
        """通知观察者"""
        self._old_value = old_value
        self._new_value = new_value
        try:
            self.callback(self, old_value, new_value)
        except Exception as e:
            print(f"[KVO] 观察者回调错误: {e}")

    def __repr__(self):
        return f"<KVOObserver key='{self.key_path}'>"


class Observable:
    """
    Observable 基类 - 模拟 iOS 可观察对象

    提供 KVO-like 的属性观察功能。
    子类通过继承此类获得属性变化通知能力。
    """

    def __init__(self):
        self._observers: Dict[str, List[KVOObserver]] = defaultdict(list)
        self._object_id = id(self)

    def add_observer(self, key_path: str, callback: Callable,
                     options: Optional[Dict] = None):
        """
        添加观察者 - 模拟 addObserver:forKeyPath:options:context:

        Args:
            key_path: 观察的属性路径 (支持嵌套: "user.name")
            callback: 回调函数 (observer, old_value, new_value)
            options: 选项 (new: 是否传递新值, old: 是否传递旧值)
        """
        observer = KVOObserver(key_path, callback, options)
        self._observers[key_path].append(observer)
        print(f"[Observable] 添加观察者: {key_path} -> {callback.__name__}")

    def remove_observer(self, key_path: str, callback: Callable):
        """移除观察者"""
        if key_path in self._observers:
            self._observers[key_path] = [
                obs for obs in self._observers[key_path] if obs.callback != callback
            ]
            if not self._observers[key_path]:
                del self._observers[key_path]
            print(f"[Observable] 移除观察者: {key_path} -> {callback.__name__}")

    def remove_all_observers(self):
        """移除所有观察者"""
        count = sum(len(obs) for obs in self._observers.values())
        self._observers.clear()
        print(f"[Observable] 移除所有观察者 (共 {count} 个)")

    def set_value(self, key_path: str, new_value: Any):
        """
        设置属性值并通知观察者 - 模拟 setValue:forKey:

        这是 KVO 的核心：当属性变化时自动通知观察者。
        """
        # 通过 getattr/setattr 支持嵌套路径
        parts = key_path.split(".")
        obj = self
        for part in parts[:-1]:
            obj = getattr(obj, part, None)
            if obj is None:
                raise AttributeError(f"属性链断裂: {key_path}")

        old_value = getattr(obj, parts[-1], None)

        if old_value != new_value:
            # 先通知观察者
            for observer in self._observers.get(key_path, []):
                options = observer.options or {}
                if options.get("new", True):
                    observer.notify(old_value, new_value)
                else:
                    observer.notify(old_value, None)

            # 再设置值
            setattr(obj, parts[-1], new_value)
            print(f"[Observable] 属性变化: {key_path} = {old_value!r} -> {new_value!r}")
        else:
            print(f"[Observable] 属性未变化: {key_path} = {old_value!r}")

    def get_value(self, key_path: str) -> Any:
        """获取属性值 - 模拟 valueForKey:"""
        parts = key_path.split(".")
        obj = self
        for part in parts:
            obj = getattr(obj, part, None)
            if obj is None:
                return None
        return obj

    def __repr__(self):
        return f"<Observable id={self._object_id} observers={len(self._observers)}>"


class Binding:
    """
    Binding - 双向数据绑定

    连接两个可观察对象之间的属性。
    一方变化时自动同步到另一方。

    类比 SwiftUI 的 @Binding 或 MVVM 的数据绑定。
    """

    def __init__(self, source: Observable, source_key: str,
                 target: Observable, target_key: str,
                 mode: str = "one_way"):
        """
        Args:
            source: 源可观察对象
            source_key: 源属性路径
            target: 目标可观察对象
            target_key: 目标属性路径
            mode: 绑定模式 ("one_way" | "two_way")
        """
        self.source = source
        self.source_key = source_key
        self.target = target
        self.target_key = target_key
        self.mode = mode
        self._is_valid = True
        self._observer_ref = None

        # 建立绑定
        self._setup_binding()
        print(f"[Binding] 创建绑定: {source_key} <-> {target_key} ({mode})")

    def _setup_binding(self):
        """设置绑定"""
        # 源 -> 目标
        self._observer_ref = self.source.add_observer(
            self.source_key, self._on_source_change
        )

        # 双向绑定时，目标 -> 源
        if self.mode == "two_way":
            self.target.add_observer(
                self.target_key, self._on_target_change
            )

    def _on_source_change(self, observer, old_value, new_value):
        """源变化时同步到目标"""
        if self._is_valid:
            self.target.set_value(self.target_key, new_value)

    def _on_target_change(self, observer, old_value, new_value):
        """目标变化时同步到源"""
        if self._is_valid:
            self.source.set_value(self.source_key, new_value)

    def disconnect(self):
        """断开绑定"""
        self._is_valid = False
        print(f"[Binding] 断开绑定: {self.source_key} <-> {self.target_key}")

    def __repr__(self):
        return (f"<Binding {self.source_key} <-> {self.target_key} "
                f"mode={self.mode} valid={self._is_valid}>")


class Property:
    """
    Property - 可观察属性描述符

    使用 Python descriptor 协议实现 KVO-like 属性。
    类似 Swift 的 @Observable 属性。
    """

    def __init__(self, default_value: Any = None, name: str = ""):
        self.default_value = default_value
        self.name = name

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return obj.__dict__.get(f"_prop_{self.name}", self.default_value)

    def __set__(self, obj, value):
        old_value = obj.__dict__.get(f"_prop_{self.name}", self.default_value)
        if old_value != value:
            # 触发变化通知
            if hasattr(obj, "willChangeValueForKey"):
                obj.willChangeValueForKey(self.name)
            obj.__dict__[f"_prop_{self.name}"] = value
            if hasattr(obj, "didChangeValueForKey"):
                obj.didChangeValueForKey(self.name)
            print(f"[Property] 属性变化: {self.name} = {old_value!r} -> {value!r}")
        else:
            print(f"[Property] 属性未变化: {self.name} = {old_value!r}")


class ViewModel:
    """
    ViewModel - MVVM 架构中的 ViewModel

    ViewModel 是 Model 和 View 之间的桥梁：
    - 暴露 View 需要的数据
    - 处理用户交互逻辑
    - 发起网络请求

    类比 SwiftUI ViewModel 或 MVVM 模式。
    """

    def __init__(self, name: str = ""):
        self.name = name or self.__class__.__name__
        self._observable = Observable()
        self._is_valid = True
        self._bindings: List[Binding] = []

    @property
    def observable(self) -> Observable:
        return self._observable

    @property
    def is_valid(self) -> bool:
        return self._is_valid

    def add_observer(self, key_path: str, callback: Callable):
        """添加观察者"""
        return self._observable.add_observer(key_path, callback)

    def set_value(self, key_path: str, value: Any):
        """设置值并通知"""
        self._observable.set_value(key_path, value)

    def get_value(self, key_path: str) -> Any:
        """获取值"""
        return self._observable.get_value(key_path)

    def create_binding(self, source_key: str, target: "ViewModel",
                       target_key: str, mode: str = "one_way") -> Binding:
        """创建双向绑定"""
        binding = Binding(self._observable, source_key, target.observable, target_key, mode)
        self._bindings.append(binding)
        return binding

    def dispose(self):
        """清理资源"""
        self._is_valid = False
        for binding in self._bindings:
            binding.disconnect()
        self._bindings.clear()
        self._observable.remove_all_observers()
        print(f"[ViewModel] 清理: {self.name}")

    def __repr__(self):
        return f"<ViewModel name='{self.name}' valid={self._is_valid}>"

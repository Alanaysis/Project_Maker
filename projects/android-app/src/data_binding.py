"""
数据绑定模拟 - Data Binding Simulation

数据绑定将 UI 组件直接绑定到数据源。
当数据变化时，UI 自动更新。

Data Binding connects UI components directly to data sources.
When data changes, the UI updates automatically.

两种主要方式：
1. 传统数据绑定（XML + Binding class）
2. Jetpack Compose 状态驱动（推荐）

Two main approaches:
1. Traditional data binding (XML + Binding class)
2. Jetpack Compose state-driven (recommended)
"""

import logging
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class DataBindingExpression:
    """数据绑定表达式"""
    expression: str
    source_key: str
    target_property: str
    is_two_way: bool = False  # 双向绑定
    observers: List[Callable] = field(default_factory=list)

    def evaluate(self, data: Dict[str, Any]) -> Any:
        """求值表达式"""
        return data.get(self.source_key)

    def add_observer(self, observer: Callable) -> None:
        self.observers.append(observer)

    def notify_observers(self, value: Any) -> None:
        for observer in self.observers:
            observer(value)

    def __str__(self) -> str:
        two_way = "2-way" if self.is_two_way else "1-way"
        return f"Binding({two_way}: {self.source_key} -> {self.target_property})"


class DataObserver:
    """数据变化观察者"""

    def __init__(self, name: str, callback: Callable):
        self.name = name
        self.callback = callback
        self._call_count = 0

    def on_data_changed(self, key: str, value: Any) -> None:
        self._call_count += 1
        self.callback(key, value)
        logger.debug(f"DataObserver '{self.name}' triggered (#{self._call_count}): "
                      f"{key} = {value}")

    @property
    def call_count(self) -> int:
        return self._call_count


class ObservableField:
    """
    可观察字段 - Observable Field

    包装一个值，在值变化时通知所有观察者。

    Wraps a value and notifies observers when it changes.
    """

    def __init__(self, name: str, initial_value: Any = None):
        self.name = name
        self._value = initial_value
        self._observers: List[DataObserver] = []

    @property
    def value(self) -> Any:
        return self._value

    @value.setter
    def value(self, new_value: Any) -> None:
        if self._value != new_value:
            old_value = self._value
            self._value = new_value
            for observer in self._observers:
                observer.on_data_changed(self.name, new_value)

    def add_observer(self, observer: DataObserver) -> None:
        self._observers.append(observer)

    def remove_observer(self, observer: DataObserver) -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    def __str__(self) -> str:
        return f"ObservableField({self.name}={self._value})"


class DataBindingContext:
    """
    数据绑定上下文 - Data Binding Context

    管理数据源、绑定表达式和视图之间的关联。

    Manages the association between data sources, binding expressions, and views.
    """

    def __init__(self, name: str = "default"):
        self.name = name
        self._data: Dict[str, Any] = {}
        self._bindings: Dict[str, DataBindingExpression] = {}
        self._observers: Dict[str, DataObserver] = {}
        self._binding_log: List[str] = []

    def set_data(self, key: str, value: Any) -> None:
        """设置数据源"""
        self._data[key] = value
        # 触发相关绑定
        for binding_key, binding in self._bindings.items():
            if binding.source_key == key:
                result = binding.evaluate(self._data)
                self._binding_log.append(f"Binding '{binding_key}' updated: {binding} -> {result}")
                binding.notify_observers(result)

    def get_data(self, key: str, default: Any = None) -> Any:
        """获取数据源"""
        return self._data.get(key, default)

    def create_binding(self, key: str, source_key: str,
                       target_property: str, is_two_way: bool = False) -> DataBindingExpression:
        """创建数据绑定表达式"""
        binding = DataBindingExpression(
            expression=f"@{{{source_key}}}",
            source_key=source_key,
            target_property=target_property,
            is_two_way=is_two_way,
        )
        self._bindings[key] = binding

        # 自动创建观察者
        observer = DataObserver(f"binding_{key}", self._on_binding_changed)
        binding.add_observer(observer)
        self._observers[key] = observer

        return binding

    def _on_binding_changed(self, key: str, value: Any) -> None:
        """绑定变化回调"""
        self._binding_log.append(f"Data changed: {key} = {value}")
        logger.debug(f"DataBindingContext '{self.name}': {key} = {value}")

    def get_binding_result(self, binding_key: str) -> Any:
        """获取绑定表达式的求值结果"""
        binding = self._bindings.get(binding_key)
        if binding:
            return binding.evaluate(self._data)
        return None

    def get_binding_log(self) -> List[str]:
        return list(self._binding_log)

    def get_all_data(self) -> Dict[str, Any]:
        return dict(self._data)

    def __str__(self) -> str:
        return (f"DataBindingContext({self.name}, "
                f"data={len(self._data)}, bindings={len(self._bindings)})")

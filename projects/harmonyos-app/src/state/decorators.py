"""
状态管理装饰器 - State Decorators

模拟 ArkTS 中用于状态管理的装饰器：

1. @State - 组件内部状态
2. @Prop - 单向数据绑定
3. @Link - 双向数据绑定
4. @Provide - 提供状态给后代
5. @Consume - 消费祖先提供的状态
6. @ObjectLink - 对象引用绑定

ArkTS 示例：
```
@Entry
@Component
struct Counter {
  @State count: number = 0       // 组件内部状态
  @Prop parentValue: string      // 单向绑定
  @Link childValue: number       // 双向绑定

  build() {
    Column() {
      Text(String(this.count))
      Button('Add')
        .onClick(() => this.count++)
    }
  }
}
"""

from typing import Any, Callable, Dict, Optional
from .manager import StateManager


class PropBinding:
    """
    @Prop 单向数据绑定

    父组件 -> 子组件 的数据流
    父组件状态变化时，子组件自动更新
    子组件不能修改 @Prop 值

    ArkTS:
    ```
    @Prop count: number
    ```
    """

    def __init__(self, source_state: StateManager, source_key: str):
        self.source = source_state
        self.source_key = source_key
        self._value = None
        self._initialized = False

    def update(self):
        """从源状态同步值"""
        self._value = self.source.get_state(self.source_key)
        self._initialized = True

    @property
    def value(self) -> Any:
        if not self._initialized:
            self.update()
        return self._value

    def __repr__(self):
        return f'PropBinding(source={self.source_key}, value={self._value})'


class LinkBinding:
    """
    @Link 双向数据绑定

    父子组件共享同一个状态源
    任何一方修改，另一方自动同步

    ArkTS:
    ```
    @Link childCount: number
    // 父组件中：
    Child({ childCount: $parentCount })
    ```
    """

    def __init__(self, shared_state: StateManager, shared_key: str):
        self.state = shared_state
        self.key = shared_key
        self._version = 0

    @property
    def value(self) -> Any:
        # 检测版本变化
        var = self.state._variables.get(self.key)
        if var:
            self._version = var.get_version()
        return self.state.get_state(self.key)

    @value.setter
    def value(self, new_value: Any):
        self.state.set_state(self.key, new_value)

    def __repr__(self):
        return f'LinkBinding(key={self.key}, value={self.state.get_state(self.key)})'


class ProvideBinding:
    """
    @Provide 状态提供

    将状态提供给后代组件
    类似依赖注入模式

    ArkTS:
    ```
    @Provide theme: string = 'dark'
    ```
    """

    def __init__(self, state_manager: StateManager, key: str):
        self.state = state_manager
        self.key = key

    def get_value(self) -> Any:
        return self.state.get_state(self.key)

    def update(self, value: Any):
        self.state.set_state(self.key, value)

    def __repr__(self):
        return f'Provide(key={self.key}, value={self.state.get_state(self.key)})'


class ConsumeBinding:
    """
    @Consume 状态消费

    消费祖先组件提供的状态
    与 @Provide 配对使用

    ArkTS:
    ```
    @Consume theme: string
    ```
    """

    def __init__(self, source_state: StateManager, key: str):
        self.source = source_state
        self.key = key
        self._value = None

    @property
    def value(self) -> Any:
        self._value = self.source.get_state(self.key)
        return self._value

    def __repr__(self):
        return f'Consume(key={self.key}, value={self._value})'


# 装饰器函数 - 模拟 ArkTS 装饰器语法

def state(initial_value=None):
    """
    @State 装饰器

    标记一个属性为组件状态。
    状态变化时，UI 自动重建。

    ArkTS:
    ```
    @State count: number = 0
    ```
    """
    def decorator(func):
        manager = StateManager(owner=func.__name__)
        var = manager.define_state('value', initial_value)

        def wrapper(*args, **kwargs):
            return {'state': var, 'manager': manager}

        wrapper.manager = manager
        wrapper.var = var
        return wrapper

    if initial_value is not None:
        return decorator
    return decorator


def prop(source_manager: StateManager, source_key: str):
    """
    @Prop 装饰器工厂

    创建单向数据绑定。
    """
    def decorator(func):
        binding = PropBinding(source_manager, source_key)

        def wrapper(*args, **kwargs):
            return {'prop': binding, 'manager': source_manager}

        wrapper.binding = binding
        wrapper.manager = source_manager
        return wrapper

    return decorator


def link(shared_manager: StateManager, shared_key: str):
    """
    @Link 装饰器工厂

    创建双向数据绑定。
    """
    def decorator(func):
        binding = LinkBinding(shared_manager, shared_key)

        def wrapper(*args, **kwargs):
            return {'link': binding, 'manager': shared_manager}

        wrapper.binding = binding
        wrapper.manager = shared_manager
        return wrapper

    return decorator

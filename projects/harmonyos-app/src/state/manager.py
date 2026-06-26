"""
状态管理器核心 - State Manager Core

鸿蒙 ArkUI 使用装饰器实现响应式状态管理：

1. @State: 组件内部状态，变化时触发 UI 更新
2. @Prop: 单向数据绑定，父组件 -> 子组件
3. @Link: 双向数据绑定，父子组件共享状态
4. @Provide/@Consume: 跨层级状态传递
5. @ObjectLink: 对象引用绑定

核心机制：
- 状态变化通知 → UI 自动重建 → 渲染新状态
- 类似于 Vue 的响应式系统或 React 的 state
"""

import copy
from typing import Any, Callable, Dict, List, Optional, Set


class StateObserver:
    """
    状态观察者

    监听状态变化并触发回调。
    类似 JavaScript 的 Proxy 监听机制。
    """

    def __init__(self, key: str, callback: Callable):
        self.key = key
        self.callback = callback

    def notify(self, old_value: Any, new_value: Any):
        """通知观察者状态变化"""
        self.callback(self.key, old_value, new_value)


class StateVariable:
    """
    可观察的状态变量

    模拟 ArkTS 的 @State 装饰器：
    - 自动追踪读写操作
    - 变化时通知所有观察者
    - 支持初始值设置
    """

    def __init__(self, initial_value: Any = None, name: str = ''):
        self._value = initial_value
        self.name = name
        self._observers: List[StateObserver] = []
        self._version = 0  # 版本号，用于检测变化

    @property
    def value(self) -> Any:
        """获取值"""
        return self._value

    @value.setter
    def value(self, new_value: Any):
        """设置值，触发观察者通知"""
        old_value = self._value
        if old_value != new_value:
            self._value = new_value
            self._version += 1
            # 通知所有观察者
            for observer in self._observers:
                observer.notify(old_value, new_value)

    def subscribe(self, callback: Callable) -> StateObserver:
        """订阅状态变化"""
        observer = StateObserver(self.name, callback)
        self._observers.append(observer)
        return observer

    def unsubscribe(self, observer: StateObserver):
        """取消订阅"""
        if observer in self._observers:
            self._observers.remove(observer)

    def get_version(self) -> int:
        return self._version

    def __repr__(self):
        return f'StateVariable(name={self.name}, value={self._value}, version={self._version})'


class StateManager:
    """
    状态管理器 - 管理组件的所有状态变量

    模拟 ArkUI 的状态管理框架：
    - 注册状态变量
    - 批量更新
    - 状态快照/恢复
    - 状态变更追踪
    """

    def __init__(self, owner: Any = None):
        self.owner = owner
        self._variables: Dict[str, StateVariable] = {}
        self._change_log: List[Dict] = []  # 变更记录
        self._is_batching = False
        self._pending_changes: List[Dict] = []

    def define_state(self, name: str, initial_value: Any = None) -> StateVariable:
        """
        定义状态变量

        模拟 @State 装饰器：
        @State message: string = 'Hello'
        """
        var = StateVariable(initial_value, name)
        self._variables[name] = var
        return var

    def get_state(self, name: str) -> Any:
        """获取状态值"""
        var = self._variables.get(name)
        return var.value if var else None

    def set_state(self, name: str, value: Any):
        """设置状态值"""
        var = self._variables.get(name)
        if var:
            if self._is_batching:
                self._pending_changes.append({'name': name, 'value': value})
            else:
                var.value = value
                self._record_change(name, value)

    def get_all_states(self) -> Dict[str, Any]:
        """获取所有状态"""
        return {name: var.value for name, var in self._variables.items()}

    def snapshot(self) -> Dict[str, Any]:
        """创建状态快照"""
        return copy.deepcopy(self.get_all_states())

    def restore(self, snapshot: Dict[str, Any]):
        """从快照恢复状态"""
        for name, value in snapshot.items():
            self.set_state(name, value)

    def subscribe_to(self, name: str, callback: Callable) -> StateObserver:
        """订阅特定状态变量的变化"""
        var = self._variables.get(name)
        if var:
            return var.subscribe(callback)
        return None

    def begin_batch(self):
        """开始批量更新"""
        self._is_batching = True
        self._pending_changes = []

    def end_batch(self):
        """结束批量更新，应用所有待处理变更"""
        self._is_batching = False
        for change in self._pending_changes:
            var = self._variables.get(change['name'])
            if var:
                var.value = change['value']
                self._record_change(change['name'], change['value'])
        self._pending_changes = []

    def _record_change(self, name: str, value: Any):
        """记录状态变更"""
        self._change_log.append({
            'name': name,
            'value': value,
            'version': self._variables[name].get_version() if name in self._variables else 0,
        })
        # 限制日志长度
        if len(self._change_log) > 1000:
            self._change_log = self._change_log[-500:]

    def get_change_log(self) -> List[Dict]:
        return list(self._change_log)

    def get_state_count(self) -> int:
        return len(self._variables)

    def __repr__(self):
        return f'StateManager(owner={self.owner}, states={self.get_state_count()})'

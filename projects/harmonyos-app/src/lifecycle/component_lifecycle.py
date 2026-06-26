"""
组件生命周期 - Component Lifecycle

鸿蒙 ArkUI 组件的生命周期：

1. aboutToAppear: 组件即将出现
   - 组件已创建，但尚未渲染
   - 适合做数据初始化、网络请求

2. aboutToDisappear: 组件即将消失
   - 组件即将被销毁
   - 适合做资源清理、取消订阅

3. onAreaChange: 组件区域变化
   - 组件尺寸或位置变化时触发
   - 适合做自适应布局

ArkUI 组件生命周期与页面生命周期的关系：
- 页面创建时，其子组件也随之创建
- 页面销毁时，子组件也随之销毁
- 组件生命周期早于/晚于页面生命周期
"""

import time
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field


class ComponentLifecycle:
    """
    组件生命周期管理器

    管理组件的 aboutToAppear / aboutToDisappear 等生命周期。
    """

    def __init__(self):
        self._callbacks: Dict[str, Dict[str, Callable]] = {}
        self._lifecycle_log: List[Dict] = []

    def register(self, component_id: str, callbacks: Dict[str, Callable]):
        """注册组件生命周期回调"""
        self._callbacks[component_id] = callbacks

    def on_about_to_appear(self, component_id: str, callback: Callable):
        """注册 aboutToAppear 回调"""
        if component_id not in self._callbacks:
            self._callbacks[component_id] = {}
        self._callbacks[component_id]['aboutToAppear'] = callback

    def on_about_to_disappear(self, component_id: str, callback: Callable):
        """注册 aboutToDisappear 回调"""
        if component_id not in self._callbacks:
            self._callbacks[component_id] = {}
        self._callbacks[component_id]['aboutToDisappear'] = callback

    def trigger_appear(self, component_id: str, context: Optional[Dict] = None) -> bool:
        """触发生命周期：组件出现"""
        callbacks = self._callbacks.get(component_id)
        if not callbacks:
            return False

        if 'aboutToAppear' in callbacks:
            callbacks['aboutToAppear'](context or {})
            self._log_event(component_id, 'aboutToAppear')

        return True

    def trigger_disappear(self, component_id: str, context: Optional[Dict] = None) -> bool:
        """触发生命周期：组件消失"""
        callbacks = self._callbacks.get(component_id)
        if not callbacks:
            return False

        if 'aboutToDisappear' in callbacks:
            callbacks['aboutToDisappear'](context or {})
            self._log_event(component_id, 'aboutToDisappear')

        return True

    def get_lifecycle_log(self) -> List[Dict]:
        return list(self._lifecycle_log)

    def _log_event(self, component_id: str, event: str):
        self._lifecycle_log.append({
            'timestamp': time.time(),
            'component': component_id,
            'event': event,
        })

    def __repr__(self):
        return f'ComponentLifecycle(components={len(self._callbacks)})'


class AreaChangeTracker:
    """
    区域变化追踪器

    追踪组件尺寸和位置变化，触发 onAreaChange 回调。
    """

    def __init__(self):
        self._areas: Dict[str, Dict[str, float]] = {}
        self._callbacks: Dict[str, Callable] = {}

    def register(self, component_id: str, callback: Callable):
        """注册区域变化回调"""
        self._callbacks[component_id] = callback

    def set_area(self, component_id: str, area: Dict[str, float]):
        """
        设置组件区域

        area: { x, y, width, height }
        """
        old_area = self._areas.get(component_id)
        self._areas[component_id] = area

        # 如果区域发生变化，触发回调
        if old_area and old_area != area and component_id in self._callbacks:
            self._callbacks[component_id](old_area, area)

    def get_area(self, component_id: str) -> Optional[Dict[str, float]]:
        return self._areas.get(component_id)

    def __repr__(self):
        return f'AreaChangeTracker(tracking={len(self._areas)})'

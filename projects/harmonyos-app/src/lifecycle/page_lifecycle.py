"""
页面生命周期 - Page Lifecycle

鸿蒙 ArkUI 页面的生命周期：

1. onCreate: 页面创建，初始化
2. onWillAppear: 页面即将显示（入栈动画前）
3. onAppear: 页面已显示（入栈动画后）
4. onWillDisappear: 页面即将消失（出栈动画前）
5. onDisappear: 页面已消失（出栈动画后）
6. onDestroy: 页面销毁，清理资源

页面栈管理：
- 页面压栈 (push)
- 页面弹栈 (pop)
- 页面替换 (replace)
- 页面导航
"""

import time
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class PageState:
    """页面状态记录"""
    page_name: str
    state: str = 'created'  # created, willAppear, appear, willDisappear, disappear, destroyed
    timestamp: float = field(default_factory=time.time)
    params: Dict[str, Any] = field(default_factory=dict)


class PageLifecycleManager:
    """
    页面生命周期管理器

    管理页面从创建到销毁的完整生命周期。
    模拟鸿蒙 ArkUI 的页面生命周期回调机制。
    """

    def __init__(self):
        self._pages: Dict[str, Dict[str, Callable]] = {}
        self._page_states: Dict[str, PageState] = {}
        self._lifecycle_log: List[Dict] = []
        self._page_stack: List[str] = []  # 页面栈

    def register_page(self, page_name: str, callbacks: Dict[str, Callable]):
        """
        注册页面及其生命周期回调

        callbacks 包含：
        - onCreate: 页面创建
        - onWillAppear: 页面即将显示
        - onAppear: 页面已显示
        - onWillDisappear: 页面即将消失
        - onDisappear: 页面已消失
        - onDestroy: 页面销毁
        """
        self._pages[page_name] = callbacks
        self._page_states[page_name] = PageState(page_name=page_name, state='created')

    def create_page(self, page_name: str, params: Optional[Dict] = None) -> bool:
        """创建页面"""
        if page_name not in self._pages:
            return False

        self._page_states[page_name] = PageState(
            page_name=page_name,
            state='created',
            params=params or {},
        )

        # 触发 onCreate
        if 'onCreate' in self._pages[page_name]:
            self._pages[page_name]['onCreate'](params or {})

        self._log_event(page_name, 'onCreate')
        return True

    def push_page(self, page_name: str, params: Optional[Dict] = None) -> bool:
        """将页面压入页面栈（显示页面）"""
        if page_name not in self._pages:
            return False

        state = self._page_states.get(page_name)
        if not state:
            self.create_page(page_name, params)

        # 页面即将显示
        if 'onWillAppear' in self._pages[page_name]:
            self._pages[page_name]['onWillAppear'](params or {})
        self._log_event(page_name, 'onWillAppear')

        self._page_states[page_name].state = 'willAppear'

        # 入栈
        if page_name not in self._page_stack:
            self._page_stack.append(page_name)

        # 页面已显示
        if 'onAppear' in self._pages[page_name]:
            self._pages[page_name]['onAppear'](params or {})
        self._log_event(page_name, 'onAppear')

        self._page_states[page_name].state = 'appear'
        return True

    def pop_page(self, page_name: str) -> bool:
        """将页面从页面栈弹出（隐藏页面）"""
        if page_name not in self._page_stack:
            return False

        # 页面即将消失
        if 'onWillDisappear' in self._pages[page_name]:
            self._pages[page_name]['onWillDisappear']()
        self._log_event(page_name, 'onWillDisappear')

        self._page_states[page_name].state = 'willDisappear'

        # 出栈
        self._page_stack.remove(page_name)

        # 页面已消失
        if 'onDisappear' in self._pages[page_name]:
            self._pages[page_name]['onDisappear']()
        self._log_event(page_name, 'onDisappear')

        self._page_states[page_name].state = 'disappear'
        return True

    def destroy_page(self, page_name: str) -> bool:
        """销毁页面"""
        if page_name not in self._pages:
            return False

        # 先弹出页面栈
        self.pop_page(page_name)

        # 触发 onDestroy
        if 'onDestroy' in self._pages[page_name]:
            self._pages[page_name]['onDestroy']()
        self._log_event(page_name, 'onDestroy')

        self._page_states[page_name].state = 'destroyed'
        return True

    def navigate_to(self, page_name: str, params: Optional[Dict] = None) -> bool:
        """导航到页面"""
        # 先弹出当前页面
        if self._page_stack:
            current = self._page_stack[-1]
            self.pop_page(current)

        # 导航到目标页面
        return self.push_page(page_name, params)

    def get_current_page(self) -> Optional[str]:
        """获取当前活跃页面"""
        return self._page_stack[-1] if self._page_stack else None

    def get_page_stack(self) -> List[str]:
        """获取页面栈"""
        return list(self._page_stack)

    def get_page_state(self, page_name: str) -> Optional[PageState]:
        """获取页面状态"""
        return self._page_states.get(page_name)

    def get_lifecycle_log(self) -> List[Dict]:
        """获取生命周期日志"""
        return list(self._lifecycle_log)

    def _log_event(self, page_name: str, event: str):
        """记录生命周期事件"""
        self._lifecycle_log.append({
            'timestamp': time.time(),
            'page': page_name,
            'event': event,
        })

    def __repr__(self):
        stack = ' -> '.join(self._page_stack) if self._page_stack else 'empty'
        return f'PageLifecycleManager(stack=[{stack}])'

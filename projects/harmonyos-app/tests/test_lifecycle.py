"""
页面生命周期单元测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.lifecycle.page_lifecycle import PageLifecycleManager, PageState
from src.lifecycle.component_lifecycle import ComponentLifecycle, AreaChangeTracker


class TestPageLifecycleManager:
    """测试页面生命周期管理器"""

    def test_register_page(self):
        mgr = PageLifecycleManager()
        mgr.register_page('Home', {
            'onCreate': lambda p: None,
            'onAppear': lambda p: None,
            'onDisappear': lambda: None,
            'onDestroy': lambda: None,
        })
        assert mgr.get_page_state('Home') is not None

    def test_create_page(self):
        mgr = PageLifecycleManager()
        called = []
        mgr.register_page('Home', {
            'onCreate': lambda p: called.append('created'),
            'onAppear': lambda p: None,
            'onDisappear': lambda: None,
            'onDestroy': lambda: None,
        })
        result = mgr.create_page('Home', {'key': 'value'})
        assert result is True
        assert len(called) == 1

    def test_create_invalid_page(self):
        mgr = PageLifecycleManager()
        result = mgr.create_page('NonExistent')
        assert result is False

    def test_push_page(self):
        mgr = PageLifecycleManager()
        will_appear = []
        appear = []
        mgr.register_page('Home', {
            'onCreate': lambda p: None,
            'onWillAppear': lambda p: will_appear.append(True),
            'onAppear': lambda p: appear.append(True),
            'onDisappear': lambda: None,
            'onDestroy': lambda: None,
        })
        result = mgr.push_page('Home')
        assert result is True
        assert len(will_appear) == 1
        assert len(appear) == 1

    def test_page_stack(self):
        mgr = PageLifecycleManager()
        mgr.register_page('Home', {
            'onCreate': lambda p: None,
            'onAppear': lambda p: None,
            'onDisappear': lambda: None,
            'onDestroy': lambda: None,
        })
        mgr.register_page('Detail', {
            'onCreate': lambda p: None,
            'onAppear': lambda p: None,
            'onDisappear': lambda: None,
            'onDestroy': lambda: None,
        })

        mgr.push_page('Home')
        assert mgr.get_current_page() == 'Home'

        mgr.push_page('Detail')
        stack = mgr.get_page_stack()
        assert 'Home' in stack
        assert 'Detail' in stack

    def test_pop_page(self):
        mgr = PageLifecycleManager()
        will_disappear = []
        disappear = []
        mgr.register_page('Home', {
            'onCreate': lambda p: None,
            'onAppear': lambda p: None,
            'onWillDisappear': lambda: will_disappear.append(True),
            'onDisappear': lambda: disappear.append(True),
            'onDestroy': lambda: None,
        })

        mgr.push_page('Home')
        mgr.pop_page('Home')

        assert len(will_disappear) == 1
        assert len(disappear) == 1
        assert mgr.get_current_page() is None

    def test_navigate_to(self):
        mgr = PageLifecycleManager()
        mgr.register_page('Home', {
            'onCreate': lambda p: None,
            'onAppear': lambda p: None,
            'onDisappear': lambda: None,
            'onDestroy': lambda: None,
        })
        mgr.register_page('Detail', {
            'onCreate': lambda p: None,
            'onAppear': lambda p: None,
            'onDisappear': lambda: None,
            'onDestroy': lambda: None,
        })

        mgr.push_page('Home')
        mgr.navigate_to('Detail', {'id': 1})
        assert mgr.get_current_page() == 'Detail'

    def test_destroy_page(self):
        mgr = PageLifecycleManager()
        destroyed = []
        mgr.register_page('Home', {
            'onCreate': lambda p: None,
            'onAppear': lambda p: None,
            'onDisappear': lambda: None,
            'onDestroy': lambda: destroyed.append(True),
        })

        mgr.push_page('Home')
        mgr.destroy_page('Home')
        assert len(destroyed) == 1
        assert mgr.get_page_state('Home').state == 'destroyed'

    def test_lifecycle_log(self):
        mgr = PageLifecycleManager()
        mgr.register_page('Home', {
            'onCreate': lambda p: None,
            'onAppear': lambda p: None,
            'onDisappear': lambda: None,
            'onDestroy': lambda: None,
        })
        mgr.create_page('Home')
        mgr.push_page('Home')
        mgr.pop_page('Home')
        log = mgr.get_lifecycle_log()
        assert any(e['event'] == 'onCreate' for e in log)
        assert any(e['event'] == 'onAppear' for e in log)
        assert any(e['event'] == 'onDisappear' for e in log)


class TestComponentLifecycle:
    """测试组件生命周期"""

    def test_register_callbacks(self):
        comp = ComponentLifecycle()
        comp.on_about_to_appear('c1', lambda ctx: None)
        comp.on_about_to_disappear('c1', lambda ctx: None)
        assert 'c1' in comp._callbacks

    def test_trigger_appear(self):
        comp = ComponentLifecycle()
        called = []
        comp.on_about_to_appear('c1', lambda ctx: called.append(ctx))
        comp.trigger_appear('c1', {'width': 100})
        assert len(called) == 1
        assert called[0] == {'width': 100}

    def test_trigger_disappear(self):
        comp = ComponentLifecycle()
        called = []
        comp.on_about_to_disappear('c1', lambda ctx: called.append(True))
        comp.trigger_disappear('c1')
        assert len(called) == 1

    def test_lifecycle_log(self):
        comp = ComponentLifecycle()
        comp.on_about_to_appear('c1', lambda ctx: None)
        comp.trigger_appear('c1')
        log = comp.get_lifecycle_log()
        assert len(log) == 1
        assert log[0]['event'] == 'aboutToAppear'


class TestAreaChangeTracker:
    """测试区域变化追踪器"""

    def test_set_area(self):
        tracker = AreaChangeTracker()
        tracker.set_area('c1', {'x': 0, 'y': 0, 'width': 100, 'height': 50})
        area = tracker.get_area('c1')
        assert area['width'] == 100

    def test_area_change_callback(self):
        tracker = AreaChangeTracker()
        changes = []
        tracker.register('c1', lambda old, new: changes.append((old, new)))
        tracker.set_area('c1', {'x': 0, 'y': 0, 'width': 100, 'height': 50})
        tracker.set_area('c1', {'x': 0, 'y': 0, 'width': 200, 'height': 100})
        assert len(changes) == 1

    def test_no_callback_on_same_area(self):
        tracker = AreaChangeTracker()
        changes = []
        tracker.register('c1', lambda old, new: changes.append(1))
        tracker.set_area('c1', {'x': 0, 'y': 0, 'width': 100, 'height': 50})
        tracker.set_area('c1', {'x': 0, 'y': 0, 'width': 100, 'height': 50})
        assert len(changes) == 0


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])

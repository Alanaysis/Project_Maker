"""
状态管理单元测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.state.manager import StateManager, StateVariable
from src.state.decorators import PropBinding, LinkBinding
from src.state.observable import Observable, ObjectLink


class TestStateVariable:
    """测试 StateVariable"""

    def test_initial_value(self):
        var = StateVariable(42, 'count')
        assert var.value == 42
        assert var.name == 'count'

    def test_value_setter_triggers_observers(self):
        var = StateVariable(0, 'counter')
        calls = []
        var.subscribe(lambda k, old, new: calls.append((old, new)))
        var.value = 10
        assert len(calls) == 1
        assert calls[0] == (0, 10)

    def test_no_trigger_on_same_value(self):
        var = StateVariable(0, 'counter')
        calls = []
        var.subscribe(lambda k, old, new: calls.append((old, new)))
        var.value = 0  # 相同值不触发
        assert len(calls) == 0

    def test_version_increments(self):
        var = StateVariable(0, 'counter')
        assert var.get_version() == 0
        var.value = 1
        assert var.get_version() == 1
        var.value = 2
        assert var.get_version() == 2

    def test_unsubscribe(self):
        var = StateVariable(0, 'counter')
        calls = []
        observer = var.subscribe(lambda k, old, new: calls.append(1))
        var.unsubscribe(observer)
        var.value = 5
        assert len(calls) == 0


class TestStateManager:
    """测试 StateManager"""

    def test_define_state(self):
        mgr = StateManager('Test')
        var = mgr.define_state('count', 0)
        assert var.value == 0
        assert mgr.get_state_count() == 1

    def test_get_set_state(self):
        mgr = StateManager('Test')
        mgr.define_state('count', 0)
        mgr.set_state('count', 10)
        assert mgr.get_state('count') == 10

    def test_get_all_states(self):
        mgr = StateManager('Test')
        mgr.define_state('a', 1)
        mgr.define_state('b', 2)
        states = mgr.get_all_states()
        assert states['a'] == 1
        assert states['b'] == 2

    def test_snapshot_restore(self):
        mgr = StateManager('Test')
        mgr.define_state('count', 10)
        snap = mgr.snapshot()
        mgr.set_state('count', 20)
        mgr.restore(snap)
        assert mgr.get_state('count') == 10

    def test_subscribe_to(self):
        mgr = StateManager('Test')
        mgr.define_state('count', 0)
        calls = []
        mgr.subscribe_to('count', lambda k, old, new: calls.append(new))
        mgr.set_state('count', 5)
        assert len(calls) == 1
        assert calls[0] == 5

    def test_batch_update(self):
        mgr = StateManager('Test')
        mgr.define_state('a', 0)
        mgr.define_state('b', 0)
        calls = []
        mgr.subscribe_to('a', lambda k, old, new: calls.append(('a', new)))
        mgr.subscribe_to('b', lambda k, old, new: calls.append(('b', new)))

        mgr.begin_batch()
        mgr.set_state('a', 1)
        mgr.set_state('b', 2)
        mgr.end_batch()

        # 批量更新后应该只触发一次通知
        assert len(calls) == 2

    def test_change_log(self):
        mgr = StateManager('Test')
        mgr.define_state('count', 0)
        mgr.set_state('count', 1)
        mgr.set_state('count', 2)
        log = mgr.get_change_log()
        assert len(log) == 2
        assert log[0]['value'] == 1
        assert log[1]['value'] == 2


class TestPropBinding:
    """测试 @Prop 单向绑定"""

    def test_prop_initial_value(self):
        src = StateManager('Parent')
        src.define_state('value', 100)
        prop = PropBinding(src, 'value')
        prop.update()
        assert prop.value == 100

    def test_prop_sync(self):
        src = StateManager('Parent')
        src.define_state('value', 100)
        prop = PropBinding(src, 'value')
        prop.update()

        src.set_state('value', 200)
        prop.update()
        assert prop.value == 200


class TestLinkBinding:
    """测试 @Link 双向绑定"""

    def test_link_read(self):
        shared = StateManager('Shared')
        shared.define_state('value', 42)
        link = LinkBinding(shared, 'value')
        assert link.value == 42

    def test_link_write(self):
        shared = StateManager('Shared')
        shared.define_state('value', 0)
        link = LinkBinding(shared, 'value')
        link.value = 10
        assert shared.get_state('value') == 10

    def test_link_bidirectional(self):
        shared = StateManager('Shared')
        shared.define_state('value', 0)
        link1 = LinkBinding(shared, 'value')
        link2 = LinkBinding(shared, 'value')

        link1.value = 5
        assert link2.value == 5

        link2.value = 10
        assert link1.value == 10


class TestObservable:
    """测试 Observable"""

    def test_observe_change(self):
        obs = Observable()
        obs._target = {'count': 0}
        calls = []
        obs.subscribe('count', lambda k, old, new: calls.append(new))
        obs._target['count'] = 5
        # 直接修改 _target 不会触发，需要通过 setattr
        assert len(calls) == 0

    def test_setattr_triggers(self):
        obs = Observable()
        obs._target = {'count': 0}
        calls = []
        obs.subscribe('count', lambda k, old, new: calls.append((old, new)))
        # 使用 __setattr__ 绕过
        obs.__setattr__('count', 10)
        assert len(calls) == 1

    def test_get_all(self):
        obs = Observable()
        obs._target = {'a': 1, 'b': 2}
        result = obs.get_all()
        assert result == {'a': 1, 'b': 2}

    def test_to_dict(self):
        obs = Observable()
        obs._target = {'x': 10}
        d = obs.to_dict()
        assert d['x'] == 10

    def test_set_all_batch(self):
        obs = Observable()
        obs._target = {'a': 0, 'b': 0}
        # set_all does direct dict assignment, which bypasses __setattr__ hooks
        # so no callbacks are triggered in this simulation
        obs.set_all({'a': 1, 'b': 2})
        assert obs.get_all() == {'a': 1, 'b': 2}


class TestObjectLink:
    """测试 @ObjectLink"""

    def test_object_link_sync(self):
        source = Observable()
        source._target = {'x': 0, 'y': 0}
        link = ObjectLink(source)
        assert link.get('x') == 0

    def test_object_link_set(self):
        source = Observable()
        source._target = {'x': 0}
        link = ObjectLink(source)
        link.set('x', 10)
        assert source._target['x'] == 10
        assert link.get('x') == 10


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])

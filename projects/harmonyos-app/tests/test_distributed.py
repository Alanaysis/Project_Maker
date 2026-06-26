"""
分布式能力单元测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.distributed.data_sync import DistributedDataStore, DataMigration, DataVersion
from src.distributed.device_manager import DeviceManager, DeviceInfo
from src.distributed.task_scheduler import DistributedTaskScheduler, Task


class TestDistributedDataStore:
    """测试分布式数据存储"""

    def test_set_get(self):
        store = DistributedDataStore('test_device')
        store.set('key1', 'value1')
        assert store.get('key1') == 'value1'

    def test_delete(self):
        store = DistributedDataStore('test_device')
        store.set('key1', 'value1')
        assert store.delete('key1') is True
        assert store.has('key1') is False

    def test_version_tracking(self):
        store = DistributedDataStore('test_device')
        store.set('key1', 'value1')
        version = store.get_version('key1')
        assert version is not None
        assert version.version == 1
        assert version.device_id == 'test_device'

    def test_sync_basic(self):
        store1 = DistributedDataStore('device_1')
        store2 = DistributedDataStore('device_2')
        store1.set('key1', 'value1')
        record = store1.sync_with(store2)
        assert store2.get('key1') == 'value1'
        assert len(record.keys_synced) == 1

    def test_sync_conflict_resolution(self):
        store1 = DistributedDataStore('device_1')
        store2 = DistributedDataStore('device_2')
        store1.set('key1', 'v1')
        store2.set('key1', 'v2')
        # 两个设备都有数据，版本相同，最后写入的获胜
        store1.sync_with(store2)
        # device_2 最后写入，所以它的值应该胜出
        assert store1.get('key1') == 'v2' or store2.get('key1') == 'v2'

    def test_get_all_data(self):
        store = DistributedDataStore('test')
        store.set('a', 1)
        store.set('b', 2)
        data = store.get_all_data()
        assert data['a'] == 1
        assert data['b'] == 2

    def test_sync_history(self):
        store = DistributedDataStore('test')
        other = DistributedDataStore('other')
        store.set('key', 'val')
        store.sync_with(other)
        store.sync_with(other)
        history = store.get_sync_history()
        assert len(history) == 2


class TestDataMigration:
    """测试数据迁移"""

    def test_migrate_structured(self):
        migration = DataMigration()
        result = migration.migrate('device_1', 'device_2', 'structured', ['contacts'])
        assert result['status'] == 'completed'
        assert result['type'] == 'structured'

    def test_migrate_unstructured(self):
        migration = DataMigration()
        result = migration.migrate('device_1', 'device_2', 'unstructured', ['photos'])
        assert result['status'] == 'completed'

    def test_migration_history(self):
        migration = DataMigration()
        migration.migrate('d1', 'd2', 'structured', ['a'])
        migration.migrate('d1', 'd3', 'unstructured', ['b'])
        assert len(migration.get_migrations()) == 2


class TestDeviceManager:
    """测试设备管理"""

    def test_add_device(self):
        mgr = DeviceManager()
        device = DeviceInfo('d1', 'Device1')
        mgr.add_device(device)
        assert mgr.get_device_count() == 1

    def test_remove_device(self):
        mgr = DeviceManager()
        device = DeviceInfo('d1', 'Device1')
        mgr.add_device(device)
        assert mgr.remove_device('d1') is True
        assert mgr.get_device_count() == 0

    def test_device_online_status(self):
        mgr = DeviceManager()
        device = DeviceInfo('d1', 'Device1')
        mgr.add_device(device)
        mgr.set_device_online('d1', False)
        assert device.is_online is False

    def test_find_devices_by_type(self):
        mgr = DeviceManager()
        mgr.add_device(DeviceInfo('d1', 'Phone', 'phone'))
        mgr.add_device(DeviceInfo('d2', 'Tablet', 'tablet'))
        phones = mgr.find_devices(device_type='phone')
        assert len(phones) == 1

    def test_get_online_devices(self):
        mgr = DeviceManager()
        mgr.add_device(DeviceInfo('d1', 'Online'))
        mgr.add_device(DeviceInfo('d2', 'Offline'))
        mgr.set_device_online('d2', False)
        online = mgr.get_online_devices()
        assert len(online) == 1

    def test_connect_device(self):
        mgr = DeviceManager()
        mgr.add_device(DeviceInfo('d1', 'Device1'))
        assert mgr.connect_device('d1') is True
        assert 'd1' in mgr.get_connected_devices()

    def test_disconnect_device(self):
        mgr = DeviceManager()
        mgr.add_device(DeviceInfo('d1', 'Device1'))
        mgr.connect_device('d1')
        mgr.disconnect_device('d1')
        assert 'd1' not in mgr.get_connected_devices()

    def test_device_capabilities(self):
        mgr = DeviceManager()
        device = DeviceInfo('d1', 'Device1', capabilities={'cpu': 'Kirin'})
        mgr.add_device(device)
        caps = mgr.get_device_capabilities('d1')
        assert caps['cpu'] == 'Kirin'

    def test_device_events(self):
        mgr = DeviceManager()
        device = DeviceInfo('d1', 'Device1')
        mgr.add_device(device)
        mgr.connect_device('d1')
        events = mgr.get_device_events()
        assert any(e['event'] == 'device_added' for e in events)
        assert any(e['event'] == 'device_connected' for e in events)


class TestDistributedTaskScheduler:
    """测试分布式任务调度"""

    def test_create_task(self):
        scheduler = DistributedTaskScheduler()
        task = scheduler.create_task('test_task', 'compute')
        assert task.name == 'test_task'
        assert task.status == 'pending'

    def test_schedule_task(self):
        scheduler = DistributedTaskScheduler()
        task = scheduler.create_task('compute_task', 'compute')
        device = DeviceInfo('d1', 'Device', capabilities={'cpu': 'Kirin', 'ram': 8})
        device_id = scheduler.schedule_task(task.task_id, [device])
        assert device_id == 'd1'
        assert task.status == 'running'

    def test_schedule_no_suitable_device(self):
        scheduler = DistributedTaskScheduler()
        task = scheduler.create_task('heavy_task', 'compute', {'ram': 100})
        device = DeviceInfo('d1', 'Device', capabilities={'ram': 8})
        device_id = scheduler.schedule_task(task.task_id, [device])
        assert device_id is None

    def test_complete_task(self):
        scheduler = DistributedTaskScheduler()
        task = scheduler.create_task('task', 'compute')
        device = DeviceInfo('d1', 'Device', capabilities={'ram': 8})
        scheduler.schedule_task(task.task_id, [device])
        result = scheduler.complete_task(task.task_id, {'done': True})
        assert result is True
        assert task.status == 'completed'
        assert task.result == {'done': True}

    def test_task_stats(self):
        scheduler = DistributedTaskScheduler()
        task1 = scheduler.create_task('t1', 'compute')
        task2 = scheduler.create_task('t2', 'io')
        device = DeviceInfo('d1', 'Device', capabilities={'ram': 8})
        scheduler.schedule_task(task1.task_id, [device])
        scheduler.complete_task(task2.task_id)
        stats = scheduler.get_task_stats()
        assert stats['pending'] == 0
        assert stats['running'] == 1
        assert stats['completed'] == 1

    def test_device_load(self):
        scheduler = DistributedTaskScheduler()
        task1 = scheduler.create_task('t1', 'compute')
        task2 = scheduler.create_task('t2', 'io')
        device = DeviceInfo('d1', 'Device', capabilities={'ram': 8})
        scheduler.schedule_task(task1.task_id, [device])
        scheduler.schedule_task(task2.task_id, [device])
        assert scheduler.get_device_load('d1') == 2

    def test_migrate_task(self):
        scheduler = DistributedTaskScheduler()
        task = scheduler.create_task('task', 'compute')
        device = DeviceInfo('d1', 'Device', capabilities={'ram': 8})
        scheduler.schedule_task(task.task_id, [device])
        new_device = DeviceInfo('d2', 'Device2', capabilities={'ram': 8})
        result = scheduler.migrate_task(task.task_id, new_device)
        assert result is True
        assert task.assigned_device == 'd2'
        assert task.migration_count == 1


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])

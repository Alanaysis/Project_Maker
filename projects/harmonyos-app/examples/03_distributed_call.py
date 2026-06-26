"""
示例 3: 分布式调用模拟

演示鸿蒙的分布式能力：
- 分布式数据同步
- 设备发现与管理
- 分布式任务调度
- 跨设备协同

核心概念：
- 分布式软总线：设备间通信基础
- 分布式数据管理：多设备数据同步
- 分布式任务调度：跨设备任务分配
"""

import sys
sys.path.insert(0, '.')

from src.distributed.data_sync import DistributedDataStore, DataMigration
from src.distributed.device_manager import DeviceManager, DeviceInfo
from src.distributed.task_scheduler import DistributedTaskScheduler


def demo_device_discovery():
    """演示设备发现与管理"""
    print("=" * 60)
    print("1. 设备发现与管理")
    print("=" * 60)

    device_mgr = DeviceManager()

    # 模拟发现多台设备
    devices = [
        DeviceInfo('phone_001', '我的手机', 'phone', 'HarmonyOS 4.0',
                   {'cpu': 'Kirin 9000', 'ram': 8, 'screen': '6.7 inch'}),
        DeviceInfo('tablet_001', '平板', 'tablet', 'HarmonyOS 4.0',
                   {'cpu': 'Kirin 9000s', 'ram': 12, 'screen': '10.4 inch'}),
        DeviceInfo('watch_001', '手表', 'watch', 'HarmonyOS 4.0',
                   {'cpu': 'Kirin A1', 'ram': 1, 'screen': '1.43 inch'}),
        DeviceInfo('tv_001', '智慧屏', 'tv', 'HarmonyOS 4.0',
                   {'cpu': 'Kirin 990', 'ram': 4, 'screen': '55 inch'}),
    ]

    for device in devices:
        device_mgr.add_device(device)

    print(f"\n已注册设备: {device_mgr.get_device_count()} 台")
    print(f"在线设备: {device_mgr.get_online_count()} 台")

    # 设备筛选
    print("\n--- 筛选手机类型设备 ---")
    phones = device_mgr.find_devices(device_type='phone')
    for p in phones:
        print(f"  手机: {p.device_name} ({p.capabilities})")

    print("\n--- 筛选平板设备 ---")
    tablets = device_mgr.find_devices(device_type='tablet')
    for t in tablets:
        print(f"  平板: {t.device_name}")

    # 设备连接
    print("\n--- 连接设备 ---")
    device_mgr.connect_device('phone_001')
    device_mgr.connect_device('tablet_001')
    print(f"已连接: {device_mgr.get_connected_devices()}")

    # 设备离线
    print("\n--- 设备离线 ---")
    device_mgr.set_device_online('watch_001', False)
    print(f"在线设备: {device_mgr.get_online_count()} 台")

    # 设备事件日志
    events = device_mgr.get_device_events()
    print(f"\n设备事件 ({len(events)} 条):")
    for event in events[:5]:
        print(f"  [{event['event']}] {event.get('device_id', '')} {event.get('name', '')}")


def demo_data_sync():
    """演示分布式数据同步"""
    print("\n" + "=" * 60)
    print("2. 分布式数据同步")
    print("=" * 60)

    # 创建两台设备的存储
    phone_store = DistributedDataStore('phone_001')
    tablet_store = DistributedDataStore('tablet_001')

    # 在手机上写入数据
    print("\n--- 手机写入数据 ---")
    phone_store.set('note', '鸿蒙学习笔记')
    phone_store.set('theme', 'dark')
    phone_store.set('unread_count', 5)
    print(f"手机数据: {phone_store.get_all_data()}")

    # 同步到平板
    print("\n--- 数据同步到平板 ---")
    record = phone_store.sync_with(tablet_store)
    print(f"同步记录: {record.keys_synced} 个键已同步")
    print(f"平板数据: {tablet_store.get_all_data()}")

    # 平板修改数据
    print("\n--- 平板修改数据 ---")
    tablet_store.set('unread_count', 12)
    tablet_store.set('last_sync', '2024-01-01')

    # 双向同步
    print("\n--- 双向同步 ---")
    record2 = phone_store.sync_with(tablet_store)
    print(f"同步记录: {record2.keys_synced} 个键已同步")
    print(f"手机数据: {phone_store.get_all_data()}")
    print(f"平板数据: {tablet_store.get_all_data()}")

    # 数据版本检查
    print("\n--- 数据版本 ---")
    version = phone_store.get_version('note')
    if version:
        print(f"note 版本: v{version.version} (设备: {version.device_id})")


def demo_task_scheduler():
    """演示分布式任务调度"""
    print("\n" + "=" * 60)
    print("3. 分布式任务调度")
    print("=" * 60)

    scheduler = DistributedTaskScheduler()
    device_mgr = DeviceManager()

    # 添加设备
    devices = [
        DeviceInfo('phone_001', '我的手机', 'phone', 'HarmonyOS 4.0',
                   {'cpu': 'Kirin 9000', 'ram': 8, 'gpu_perf': 78}),
        DeviceInfo('tablet_001', '平板', 'tablet', 'HarmonyOS 4.0',
                   {'cpu': 'Kirin 9000s', 'ram': 12, 'gpu_perf': 78}),
        DeviceInfo('tv_001', '智慧屏', 'tv', 'HarmonyOS 4.0',
                   {'cpu': 'Kirin 990', 'ram': 4, 'gpu_perf': 68}),
    ]

    for device in devices:
        device_mgr.add_device(device)
        device_mgr.connect_device(device.device_id)

    # 创建任务
    print("\n--- 创建任务 ---")
    task1 = scheduler.create_task('图像识别', 'compute', {'ram': 4, 'gpu_perf': 1})
    task2 = scheduler.create_task('视频编码', 'compute', {'ram': 8, 'gpu_perf': 2})
    task3 = scheduler.create_task('文件下载', 'io')
    task4 = scheduler.create_task('音频播放', 'audio')

    # 调度任务
    print("\n--- 任务调度 ---")
    online_devices = device_mgr.get_online_devices()

    for task in scheduler.get_all_tasks():
        assigned = scheduler.schedule_task(task.task_id, online_devices)
        if assigned:
            print(f"  [{task.name}] -> 设备: {assigned} (负载: {scheduler.get_device_load(assigned)})")
        else:
            print(f"  [{task.name}] -> 无合适设备")

    # 完成任务
    print("\n--- 完成任务 ---")
    scheduler.complete_task(task1.task_id, result={'accuracy': 0.95})
    scheduler.complete_task(task3.task_id, result={'size': '10MB'})

    # 任务统计
    stats = scheduler.get_task_stats()
    print(f"\n任务统计: {stats}")


def demo_data_migration():
    """演示数据迁移"""
    print("\n" + "=" * 60)
    print("4. 跨设备数据迁移")
    print("=" * 60)

    migration = DataMigration()

    # 结构化数据迁移
    print("\n--- 结构化数据迁移 ---")
    result = migration.migrate(
        source_device='phone_001',
        target_device='tablet_001',
        data_type='structured',
        data_keys=['contacts', 'messages', 'calendar'],
    )
    print(f"迁移结果: {result['type']} 类型, "
          f"{result['bytes_transferred']} bytes, "
          f"状态: {result['status']}")

    # 非结构化数据迁移
    print("\n--- 非结构化数据迁移 ---")
    result2 = migration.migrate(
        source_device='phone_001',
        target_device='tv_001',
        data_type='unstructured',
        data_keys=['photos', 'videos'],
    )
    print(f"迁移结果: {result2['type']} 类型, "
          f"{result2['bytes_transferred']} bytes, "
          f"状态: {result2['status']}")

    # 迁移历史
    print(f"\n迁移历史: {len(migration.get_migrations())} 条记录")


def demo_full_distributed_flow():
    """演示完整的分布式流程"""
    print("\n" + "=" * 60)
    print("5. 完整分布式流程演示")
    print("=" * 60)

    # 1. 设备发现
    print("\n[步骤 1] 设备发现")
    device_mgr = DeviceManager()
    for i in range(3):
        device = DeviceInfo(
            f'device_{i}', f'设备-{i}',
            ['phone', 'tablet', 'watch'][i],
            'HarmonyOS 4.0',
            {'cpu': f'Kirin-{i}', 'ram': [8, 12, 1][i]},
        )
        device_mgr.add_device(device)
        device_mgr.connect_device(device.device_id)
    print(f"  发现并连接了 {device_mgr.get_online_count()} 台设备")

    # 2. 数据同步
    print("\n[步骤 2] 数据同步")
    stores = [DistributedDataStore(f'device_{i}') for i in range(3)]
    for i, store in enumerate(stores):
        store.set('app_data', f'device_{i}_data')
        store.set('sync_time', f'2024-01-0{i+1}')

    # 链式同步
    for i in range(len(stores) - 1):
        stores[i].sync_with(stores[i + 1])
    print(f"  设备 0 数据: {stores[0].get_all_data()}")
    print(f"  设备 1 数据: {stores[1].get_all_data()}")
    print(f"  设备 2 数据: {stores[2].get_all_data()}")

    # 3. 任务调度
    print("\n[步骤 3] 任务调度")
    scheduler = DistributedTaskScheduler()
    task = scheduler.create_task('分布式计算', 'compute', {'ram': 4})
    assigned = scheduler.schedule_task(task.task_id, device_mgr.get_online_devices())
    print(f"  任务 '{task.name}' -> 调度到: {assigned}")

    # 4. 任务完成
    scheduler.complete_task(task.task_id, result={'computed': True})
    print(f"  任务状态: {task.status}")

    print("\n" + "=" * 60)
    print("分布式流程演示完成！")
    print("=" * 60)


if __name__ == '__main__':
    print("\n" + "#" * 60)
    print("# HarmonyOS 分布式能力演示")
    print("# 鸿蒙分布式技术学习示例")
    print("#" * 60)

    demo_device_discovery()
    demo_data_sync()
    demo_task_scheduler()
    demo_data_migration()
    demo_full_distributed_flow()

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)

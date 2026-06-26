"""
分布式数据同步 - Distributed Data Sync

模拟 HarmonyOS 的分布式数据管理：
- 多设备间数据同步
- 数据一致性保证
- 冲突解决
- 离线缓存

鸿蒙分布式数据管理架构：
```
设备 A  ──[数据同步]──▶  分布式数据集群  ◀──[数据同步]──▶  设备 B
    │                              │                              │
[本地数据库]                  [分布式存储]                  [本地数据库]
```
"""

import time
import hashlib
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field


@dataclass
class DataVersion:
    """
    数据版本 - 用于冲突检测

    每个数据项都有版本号，用于检测变更。
    类似 Git 的版本控制。
    """
    data_key: str
    version: int = 0
    last_modified: float = field(default_factory=time.time)
    device_id: str = ''

    def is_newer_than(self, other: 'DataVersion') -> bool:
        """检查版本是否更新"""
        return self.version > other.version

    def increment(self):
        """增加版本号"""
        self.version += 1
        self.last_modified = time.time()


@dataclass
class SyncRecord:
    """同步记录 - 记录每次同步操作"""
    timestamp: float = field(default_factory=time.time)
    source_device: str = ''
    target_device: str = ''
    keys_synced: List[str] = field(default_factory=list)
    success: bool = True
    error: str = ''


class DistributedDataStore:
    """
    分布式数据存储

    模拟鸿蒙分布式数据管理核心：
    1. 本地数据缓存
    2. 数据版本管理
    3. 多设备同步
    4. 冲突解决
    """

    def __init__(self, device_id: str = 'device_001'):
        self.device_id = device_id
        self._local_data: Dict[str, Any] = {}
        self._versions: Dict[str, DataVersion] = {}
        self._sync_history: List[SyncRecord] = []

    def set(self, key: str, value: Any) -> bool:
        """
        设置数据

        鸿蒙分布式数据写入：
        1. 写入本地缓存
        2. 生成版本号
        3. 触发同步
        """
        self._local_data[key] = value

        if key not in self._versions:
            self._versions[key] = DataVersion(data_key=key, device_id=self.device_id)
        self._versions[key].increment()

        return True

    def get(self, key: str, default=None) -> Any:
        """获取数据"""
        return self._local_data.get(key, default)

    def delete(self, key: str) -> bool:
        """删除数据"""
        if key in self._local_data:
            del self._local_data[key]
            if key in self._versions:
                del self._versions[key]
            return True
        return False

    def has(self, key: str) -> bool:
        return key in self._local_data

    def get_version(self, key: str) -> Optional[DataVersion]:
        return self._versions.get(key)

    def get_all_data(self) -> Dict[str, Any]:
        return dict(self._local_data)

    def get_all_versions(self) -> Dict[str, DataVersion]:
        return dict(self._versions)

    def sync_with(self, other_store: 'DistributedDataStore') -> SyncRecord:
        """
        与其他设备的数据存储同步

        同步策略：
        1. 比较版本号
        2. 新版本覆盖旧版本
        3. 处理冲突（最后写入胜利）
        """
        record = SyncRecord(source_device=self.device_id, target_device=other_store.device_id)

        synced_keys = []

        # 本设备 -> 对方设备
        for key, value in self._local_data.items():
            local_version = self._versions.get(key)
            remote_version = other_store._versions.get(key)

            if remote_version is None or (local_version and local_version.is_newer_than(remote_version)):
                other_store._local_data[key] = value
                if key not in other_store._versions:
                    other_store._versions[key] = DataVersion(
                        data_key=key,
                        version=local_version.version if local_version else 0,
                        device_id=self.device_id,
                        last_modified=local_version.last_modified if local_version else time.time()
                    )
                synced_keys.append(key)

        # 对方设备 -> 本设备
        for key, value in other_store._local_data.items():
            remote_version = other_store._versions.get(key)
            local_version = self._versions.get(key)

            if remote_version and (local_version is None or remote_version.is_newer_than(local_version)):
                self._local_data[key] = value
                if key not in self._versions:
                    self._versions[key] = DataVersion(
                        data_key=key,
                        version=remote_version.version,
                        device_id=other_store.device_id,
                        last_modified=remote_version.last_modified
                    )
                else:
                    self._versions[key].version = remote_version.version
                    self._versions[key].last_modified = remote_version.last_modified
                    self._versions[key].device_id = other_store.device_id
                synced_keys.append(key)

        record.keys_synced = synced_keys
        record.success = True
        self._sync_history.append(record)
        return record

    def get_sync_history(self) -> List[SyncRecord]:
        return list(self._sync_history)

    def __repr__(self):
        return f'DistributedDataStore(device={self.device_id}, keys={len(self._local_data)})'


class DataMigration:
    """
    数据迁移 - 模拟鸿蒙的数据迁移能力

    在设备间迁移结构化/非结构化数据：
    - 结构化数据：关系型数据库、分布式数据库
    - 非结构化数据：文件、图片、视频
    """

    def __init__(self):
        self._migration_queue: List[Dict] = []
        self._completed: List[Dict] = []

    def migrate(self, source_device: str, target_device: str,
                data_type: str, data_keys: List[str]) -> Dict:
        """
        执行数据迁移

        data_type: 'structured' (结构化), 'unstructured' (非结构化)
        """
        migration = {
            'timestamp': time.time(),
            'source': source_device,
            'target': target_device,
            'type': data_type,
            'keys': data_keys,
            'status': 'completed',
            'bytes_transferred': sum(len(k) * 100 for k in data_keys),  # 模拟
        }
        self._migration_queue.append(migration)
        self._completed.append(migration)
        return migration

    def get_migrations(self) -> List[Dict]:
        return list(self._completed)

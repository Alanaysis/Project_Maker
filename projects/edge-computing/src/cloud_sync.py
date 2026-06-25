"""云端同步模块 - 数据上传和配置下发"""

import time
import json
import hashlib
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set
from collections import deque
import threading


class SyncStatus(Enum):
    """同步状态"""
    IDLE = "idle"
    SYNCING = "syncing"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class SyncDirection(Enum):
    """同步方向"""
    UPLOAD = "upload"      # 边缘到云端
    DOWNLOAD = "download"  # 云端到边缘
    BIDIRECTIONAL = "bidirectional"  # 双向同步


class ConflictResolution(Enum):
    """冲突解决策略"""
    LOCAL_WINS = "local_wins"      # 本地优先
    REMOTE_WINS = "remote_wins"    # 远程优先
    NEWEST_WINS = "newest_wins"    # 最新优先
    MANUAL = "manual"              # 手动解决


@dataclass
class SyncConfig:
    """同步配置"""
    sync_interval: float = 60.0      # 同步间隔（秒）
    batch_size: int = 100            # 批量大小
    max_retries: int = 3             # 最大重试次数
    retry_delay: float = 5.0         # 重试延迟（秒）
    timeout: float = 30.0            # 超时时间（秒）
    compression: bool = False        # 是否压缩
    encryption: bool = False         # 是否加密
    conflict_resolution: ConflictResolution = ConflictResolution.NEWEST_WINS


@dataclass
class SyncRecord:
    """同步记录"""
    record_id: str
    data_type: str
    data_id: str
    action: str  # create, update, delete
    data: Any
    timestamp: float
    checksum: str = ""
    synced: bool = False
    sync_time: Optional[float] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "data_type": self.data_type,
            "data_id": self.data_id,
            "action": self.action,
            "timestamp": self.timestamp,
            "checksum": self.checksum,
            "synced": self.synced,
            "sync_time": self.sync_time,
            "error": self.error,
        }


class CloudConnector(ABC):
    """云端连接器抽象基类

    定义与云端通信的标准接口。
    """

    @abstractmethod
    def connect(self) -> bool:
        """建立连接"""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """断开连接"""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """检查连接状态"""
        pass

    @abstractmethod
    def upload_data(self, data: Dict[str, Any]) -> bool:
        """上传数据到云端"""
        pass

    @abstractmethod
    def download_data(self, data_type: str, since: Optional[float] = None) -> List[Dict[str, Any]]:
        """从云端下载数据"""
        pass

    @abstractmethod
    def get_config(self, config_key: Optional[str] = None) -> Dict[str, Any]:
        """获取云端配置"""
        pass

    @abstractmethod
    def report_status(self, status: Dict[str, Any]) -> bool:
        """上报状态到云端"""
        pass


class MockCloudConnector(CloudConnector):
    """模拟云端连接器

    用于测试和演示，模拟云端通信行为。
    """

    def __init__(self, endpoint: str = "https://cloud.example.com"):
        self.endpoint = endpoint
        self._connected = False
        self._storage: Dict[str, Any] = {}
        self._configs: Dict[str, Any] = {
            "sync_interval": 60,
            "batch_size": 100,
            "log_level": "info",
        }
        self._upload_count = 0
        self._download_count = 0

    def connect(self) -> bool:
        """建立连接"""
        self._connected = True
        return True

    def disconnect(self) -> None:
        """断开连接"""
        self._connected = False

    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._connected

    def upload_data(self, data: Dict[str, Any]) -> bool:
        """上传数据到云端"""
        if not self._connected:
            return False

        data_id = data.get("id", str(time.time()))
        self._storage[data_id] = data
        self._upload_count += 1
        return True

    def download_data(self, data_type: str, since: Optional[float] = None) -> List[Dict[str, Any]]:
        """从云端下载数据"""
        if not self._connected:
            return []

        self._download_count += 1
        results = []
        for data in self._storage.values():
            if data.get("type") == data_type:
                if since is None or data.get("timestamp", 0) >= since:
                    results.append(data)
        return results

    def get_config(self, config_key: Optional[str] = None) -> Dict[str, Any]:
        """获取云端配置"""
        if not self._connected:
            return {}

        if config_key:
            return {config_key: self._configs.get(config_key)}
        return self._configs.copy()

    def report_status(self, status: Dict[str, Any]) -> bool:
        """上报状态到云端"""
        if not self._connected:
            return False

        self._storage[f"status_{time.time()}"] = status
        return True

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "connected": self._connected,
            "endpoint": self.endpoint,
            "storage_size": len(self._storage),
            "upload_count": self._upload_count,
            "download_count": self._download_count,
        }


class DataUploader:
    """数据上传器

    管理边缘数据的上传，支持批量上传、重试和进度跟踪。
    """

    def __init__(
        self,
        connector: CloudConnector,
        config: Optional[SyncConfig] = None,
    ):
        self.connector = connector
        self.config = config or SyncConfig()

        self._upload_queue: deque = deque()
        self._pending_records: Dict[str, SyncRecord] = {}
        self._completed_records: List[SyncRecord] = []
        self._callbacks: List[Callable] = []
        self._running = False
        self._lock = threading.Lock()

        self._stats = {
            "total_uploads": 0,
            "successful_uploads": 0,
            "failed_uploads": 0,
            "total_bytes": 0,
            "last_upload_time": None,
        }

    def queue_data(
        self,
        data_type: str,
        data_id: str,
        data: Any,
        action: str = "create",
    ) -> str:
        """将数据加入上传队列

        Args:
            data_type: 数据类型
            data_id: 数据 ID
            data: 数据内容
            action: 操作类型 (create/update/delete)

        Returns:
            记录 ID
        """
        record_id = f"{data_type}_{data_id}_{int(time.time() * 1000)}"
        checksum = self._calculate_checksum(data)

        record = SyncRecord(
            record_id=record_id,
            data_type=data_type,
            data_id=data_id,
            action=action,
            data=data,
            timestamp=time.time(),
            checksum=checksum,
        )

        with self._lock:
            self._upload_queue.append(record)
            self._pending_records[record_id] = record

        return record_id

    def upload_batch(self) -> Dict[str, Any]:
        """执行批量上传

        Returns:
            上传结果统计
        """
        if not self.connector.is_connected():
            return {"success": False, "error": "Not connected"}

        batch = []
        with self._lock:
            for _ in range(min(self.config.batch_size, len(self._upload_queue))):
                if self._upload_queue:
                    batch.append(self._upload_queue.popleft())

        if not batch:
            return {"success": True, "uploaded": 0}

        success_count = 0
        fail_count = 0

        for record in batch:
            upload_data = {
                "id": record.data_id,
                "type": record.data_type,
                "action": record.action,
                "data": record.data,
                "timestamp": record.timestamp,
                "checksum": record.checksum,
            }

            for attempt in range(self.config.max_retries):
                if self.connector.upload_data(upload_data):
                    record.synced = True
                    record.sync_time = time.time()
                    success_count += 1
                    self._stats["successful_uploads"] += 1
                    break
                else:
                    if attempt < self.config.max_retries - 1:
                        time.sleep(self.config.retry_delay)
                    else:
                        record.error = "Max retries exceeded"
                        fail_count += 1
                        self._stats["failed_uploads"] += 1

            with self._lock:
                if record.synced:
                    self._completed_records.append(record)
                    self._pending_records.pop(record.record_id, None)
                    # 触发回调
                    for callback in self._callbacks:
                        try:
                            callback(record)
                        except Exception:
                            pass

        self._stats["total_uploads"] += len(batch)
        self._stats["last_upload_time"] = time.time()

        return {
            "success": True,
            "uploaded": success_count,
            "failed": fail_count,
            "total": len(batch),
        }

    def register_callback(self, callback: Callable) -> None:
        """注册上传完成回调"""
        self._callbacks.append(callback)

    def _calculate_checksum(self, data: Any) -> str:
        """计算数据校验和"""
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(data_str.encode()).hexdigest()

    def get_pending_count(self) -> int:
        """获取待上传数量"""
        return len(self._upload_queue)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self._stats,
            "pending_count": len(self._upload_queue),
            "pending_records": len(self._pending_records),
            "completed_records": len(self._completed_records),
        }


class ConfigManager:
    """配置管理器

    管理边缘节点的配置，支持从云端下发配置和本地配置覆盖。
    """

    def __init__(
        self,
        connector: CloudConnector,
        node_id: str,
        default_config: Optional[Dict[str, Any]] = None,
    ):
        self.connector = connector
        self.node_id = node_id
        self._config: Dict[str, Any] = default_config or {}
        self._overrides: Dict[str, Any] = {}
        self._watchers: Dict[str, List[Callable]] = {}
        self._last_sync: Optional[float] = None
        self._version: int = 0

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值

        优先返回本地覆盖值，然后返回远程配置值，最后返回默认值。
        """
        # 检查本地覆盖
        if key in self._overrides:
            return self._overrides[key]

        # 检查远程配置
        if key in self._config:
            return self._config[key]

        return default

    def set_override(self, key: str, value: Any) -> None:
        """设置本地配置覆盖"""
        old_value = self.get(key)
        self._overrides[key] = value

        # 触发变更通知
        if old_value != value:
            self._notify_watchers(key, old_value, value)

    def remove_override(self, key: str) -> bool:
        """移除本地配置覆盖"""
        if key in self._overrides:
            old_value = self._overrides.pop(key)
            new_value = self._config.get(key)
            self._notify_watchers(key, old_value, new_value)
            return True
        return False

    def sync_from_cloud(self) -> Dict[str, Any]:
        """从云端同步配置

        Returns:
            同步结果
        """
        if not self.connector.is_connected():
            return {"success": False, "error": "Not connected"}

        try:
            cloud_config = self.connector.get_config()
            if not cloud_config:
                return {"success": True, "updated": 0}

            # 更新本地配置
            updated_keys = []
            for key, value in cloud_config.items():
                old_value = self._config.get(key)
                self._config[key] = value
                if old_value != value:
                    updated_keys.append(key)
                    self._notify_watchers(key, old_value, value)

            self._last_sync = time.time()
            self._version += 1

            return {
                "success": True,
                "updated": len(updated_keys),
                "keys": updated_keys,
                "version": self._version,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def watch(self, key: str, callback: Callable) -> None:
        """监视配置变更"""
        if key not in self._watchers:
            self._watchers[key] = []
        self._watchers[key].append(callback)

    def _notify_watchers(self, key: str, old_value: Any, new_value: Any) -> None:
        """通知配置变更观察者"""
        for callback in self._watchers.get(key, []):
            try:
                callback(key, old_value, new_value)
            except Exception:
                pass

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置（合并远程和本地覆盖）"""
        result = self._config.copy()
        result.update(self._overrides)
        return result

    def get_info(self) -> Dict[str, Any]:
        """获取配置管理器信息"""
        return {
            "node_id": self.node_id,
            "remote_config_count": len(self._config),
            "override_count": len(self._overrides),
            "version": self._version,
            "last_sync": self._last_sync,
            "watchers_count": sum(len(w) for w in self._watchers.values()),
        }


class CloudSyncManager:
    """云端同步管理器

    统一管理边缘节点与云端的数据同步，包括数据上传和配置下发。
    """

    def __init__(
        self,
        node_id: str,
        connector: CloudConnector,
        sync_config: Optional[SyncConfig] = None,
    ):
        self.node_id = node_id
        self.connector = connector
        self.config = sync_config or SyncConfig()

        self.uploader = DataUploader(connector, self.config)
        self.config_manager = ConfigManager(connector, node_id)

        self._status = SyncStatus.IDLE
        self._last_sync: Optional[float] = None
        self._sync_history: List[Dict[str, Any]] = []
        self._running = False

    def start(self) -> bool:
        """启动同步管理器"""
        if not self.connector.connect():
            return False

        self._running = True
        self._status = SyncStatus.IDLE

        # 同步配置
        self.config_manager.sync_from_cloud()

        return True

    def stop(self) -> None:
        """停止同步管理器"""
        self._running = False
        self.connector.disconnect()
        self._status = SyncStatus.IDLE

    def sync_data(self, data_type: str, data_id: str, data: Any) -> str:
        """同步数据到云端

        Args:
            data_type: 数据类型
            data_id: 数据 ID
            data: 数据内容

        Returns:
            记录 ID
        """
        return self.uploader.queue_data(data_type, data_id, data)

    def sync_batch(self) -> Dict[str, Any]:
        """执行批量同步

        Returns:
            同步结果
        """
        if not self._running:
            return {"success": False, "error": "Not running"}

        self._status = SyncStatus.SYNCING

        try:
            # 上传数据
            upload_result = self.uploader.upload_batch()

            # 同步配置
            config_result = self.config_manager.sync_from_cloud()

            self._last_sync = time.time()
            self._status = SyncStatus.SUCCESS if upload_result.get("success") else SyncStatus.FAILED

            result = {
                "success": upload_result.get("success", False),
                "upload": upload_result,
                "config": config_result,
                "timestamp": self._last_sync,
            }

            self._sync_history.append(result)
            return result

        except Exception as e:
            self._status = SyncStatus.FAILED
            return {"success": False, "error": str(e)}

    def report_status(self, status: Dict[str, Any]) -> bool:
        """上报节点状态到云端"""
        if not self._running or not self.connector.is_connected():
            return False

        full_status = {
            "node_id": self.node_id,
            "timestamp": time.time(),
            **status,
        }

        return self.connector.report_status(full_status)

    def get_status(self) -> Dict[str, Any]:
        """获取同步状态"""
        return {
            "node_id": self.node_id,
            "status": self._status.value,
            "connected": self.connector.is_connected(),
            "last_sync": self._last_sync,
            "uploader_stats": self.uploader.get_stats(),
            "config_info": self.config_manager.get_info(),
        }

    def get_sync_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取同步历史"""
        return self._sync_history[-limit:]

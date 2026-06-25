"""云端同步模块测试"""

import time
import pytest
from src.cloud_sync import (
    SyncStatus, SyncDirection, ConflictResolution,
    SyncConfig, SyncRecord, MockCloudConnector,
    DataUploader, ConfigManager, CloudSyncManager,
)


@pytest.fixture
def mock_connector():
    """创建模拟云端连接器"""
    connector = MockCloudConnector(endpoint="https://test.cloud.com")
    connector.connect()
    return connector


@pytest.fixture
def sync_config():
    """创建同步配置"""
    return SyncConfig(
        sync_interval=60,
        batch_size=10,
        max_retries=2,
        retry_delay=0.1,
    )


class TestMockCloudConnector:
    """模拟云端连接器测试"""

    def test_connect_disconnect(self):
        """测试连接和断开"""
        connector = MockCloudConnector()
        assert connector.is_connected() is False

        connector.connect()
        assert connector.is_connected() is True

        connector.disconnect()
        assert connector.is_connected() is False

    def test_upload_data(self, mock_connector):
        """测试上传数据"""
        data = {"id": "test-1", "type": "sensor", "value": 25.0}
        result = mock_connector.upload_data(data)

        assert result is True
        assert mock_connector.get_stats()["upload_count"] == 1

    def test_upload_when_disconnected(self):
        """测试断开时上传"""
        connector = MockCloudConnector()
        data = {"id": "test-1", "value": 25.0}

        result = connector.upload_data(data)
        assert result is False

    def test_download_data(self, mock_connector):
        """测试下载数据"""
        # 先上传一些数据
        mock_connector.upload_data({"id": "1", "type": "sensor", "value": 10})
        mock_connector.upload_data({"id": "2", "type": "config", "value": 20})
        mock_connector.upload_data({"id": "3", "type": "sensor", "value": 30})

        # 下载特定类型
        results = mock_connector.download_data("sensor")
        assert len(results) == 2

    def test_get_config(self, mock_connector):
        """测试获取配置"""
        config = mock_connector.get_config()
        assert "sync_interval" in config
        assert "batch_size" in config

        # 获取特定配置项
        value = mock_connector.get_config("sync_interval")
        assert value == {"sync_interval": 60}

    def test_report_status(self, mock_connector):
        """测试状态上报"""
        status = {"cpu": 50, "memory": 60}
        result = mock_connector.report_status(status)

        assert result is True


class TestDataUploader:
    """数据上传器测试"""

    def test_queue_data(self, mock_connector, sync_config):
        """测试数据入队"""
        uploader = DataUploader(mock_connector, sync_config)

        record_id = uploader.queue_data(
            data_type="sensor",
            data_id="sensor-1",
            data={"value": 25.0},
        )

        assert record_id is not None
        assert uploader.get_pending_count() == 1

    def test_upload_batch(self, mock_connector, sync_config):
        """测试批量上传"""
        uploader = DataUploader(mock_connector, sync_config)

        # 入队多个数据
        for i in range(5):
            uploader.queue_data(
                data_type="sensor",
                data_id=f"sensor-{i}",
                data={"value": i * 10.0},
            )

        # 执行批量上传
        result = uploader.upload_batch()

        assert result["success"] is True
        assert result["uploaded"] == 5
        assert uploader.get_pending_count() == 0

    def test_upload_batch_size_limit(self, mock_connector):
        """测试批量大小限制"""
        config = SyncConfig(batch_size=3)
        uploader = DataUploader(mock_connector, config)

        # 入队5个数据
        for i in range(5):
            uploader.queue_data("sensor", f"s-{i}", {"value": i})

        # 第一次上传只能上传3个
        result = uploader.upload_batch()
        assert result["uploaded"] == 3
        assert uploader.get_pending_count() == 2

    def test_upload_callback(self, mock_connector, sync_config):
        """测试上传回调"""
        uploader = DataUploader(mock_connector, sync_config)

        completed_records = []
        uploader.register_callback(lambda r: completed_records.append(r))

        uploader.queue_data("sensor", "s-1", {"value": 1})
        uploader.upload_batch()

        assert len(completed_records) == 1

    def test_upload_stats(self, mock_connector, sync_config):
        """测试上传统计"""
        uploader = DataUploader(mock_connector, sync_config)

        uploader.queue_data("sensor", "s-1", {"value": 1})
        uploader.queue_data("sensor", "s-2", {"value": 2})
        uploader.upload_batch()

        stats = uploader.get_stats()
        assert stats["total_uploads"] == 2
        assert stats["successful_uploads"] == 2
        assert stats["failed_uploads"] == 0


class TestConfigManager:
    """配置管理器测试"""

    def test_get_default(self, mock_connector):
        """测试获取默认配置"""
        manager = ConfigManager(mock_connector, "node-1", {"key1": "value1"})

        assert manager.get("key1") == "value1"
        assert manager.get("nonexistent", "default") == "default"

    def test_set_override(self, mock_connector):
        """测试设置本地覆盖"""
        manager = ConfigManager(mock_connector, "node-1", {"key1": "original"})

        manager.set_override("key1", "overridden")
        assert manager.get("key1") == "overridden"

    def test_remove_override(self, mock_connector):
        """测试移除本地覆盖"""
        manager = ConfigManager(mock_connector, "node-1", {"key1": "original"})

        manager.set_override("key1", "overridden")
        assert manager.get("key1") == "overridden"

        manager.remove_override("key1")
        assert manager.get("key1") == "original"

    def test_sync_from_cloud(self, mock_connector):
        """测试从云端同步配置"""
        manager = ConfigManager(mock_connector, "node-1")

        result = manager.sync_from_cloud()
        assert result["success"] is True
        assert manager.get("sync_interval") == 60

    def test_watch_config_changes(self, mock_connector):
        """测试配置变更监视"""
        manager = ConfigManager(mock_connector, "node-1", {"key1": "old"})

        changes = []
        manager.watch("key1", lambda k, o, n: changes.append((k, o, n)))

        manager.set_override("key1", "new")
        assert len(changes) == 1
        assert changes[0] == ("key1", "old", "new")

    def test_get_all(self, mock_connector):
        """测试获取所有配置"""
        manager = ConfigManager(mock_connector, "node-1", {"key1": "v1"})
        manager.set_override("key2", "v2")

        all_config = manager.get_all()
        assert all_config["key1"] == "v1"
        assert all_config["key2"] == "v2"

    def test_config_info(self, mock_connector):
        """测试配置信息"""
        manager = ConfigManager(mock_connector, "node-1", {"key1": "v1"})

        info = manager.get_info()
        assert info["node_id"] == "node-1"
        assert info["remote_config_count"] == 1
        assert info["override_count"] == 0


class TestCloudSyncManager:
    """云端同步管理器测试"""

    def test_start_stop(self, mock_connector, sync_config):
        """测试启动和停止"""
        manager = CloudSyncManager("node-1", mock_connector, sync_config)

        result = manager.start()
        assert result is True
        assert manager.get_status()["status"] == SyncStatus.IDLE.value

        manager.stop()
        assert manager.get_status()["status"] == SyncStatus.IDLE.value

    def test_sync_data(self, mock_connector, sync_config):
        """测试数据同步"""
        manager = CloudSyncManager("node-1", mock_connector, sync_config)
        manager.start()

        record_id = manager.sync_data("sensor", "s-1", {"value": 25.0})
        assert record_id is not None

    def test_sync_batch(self, mock_connector, sync_config):
        """测试批量同步"""
        manager = CloudSyncManager("node-1", mock_connector, sync_config)
        manager.start()

        # 同步多个数据
        for i in range(3):
            manager.sync_data("sensor", f"s-{i}", {"value": i * 10.0})

        result = manager.sync_batch()
        assert result["success"] is True
        assert result["upload"]["uploaded"] == 3

    def test_report_status(self, mock_connector, sync_config):
        """测试状态上报"""
        manager = CloudSyncManager("node-1", mock_connector, sync_config)
        manager.start()

        result = manager.report_status({"cpu": 50, "memory": 60})
        assert result is True

    def test_get_status(self, mock_connector, sync_config):
        """测试获取状态"""
        manager = CloudSyncManager("node-1", mock_connector, sync_config)
        manager.start()

        status = manager.get_status()
        assert status["node_id"] == "node-1"
        assert status["connected"] is True

    def test_sync_history(self, mock_connector, sync_config):
        """测试同步历史"""
        manager = CloudSyncManager("node-1", mock_connector, sync_config)
        manager.start()

        manager.sync_data("sensor", "s-1", {"value": 1})
        manager.sync_batch()

        history = manager.get_sync_history()
        assert len(history) == 1
        assert history[0]["success"] is True

    def test_config_sync(self, mock_connector, sync_config):
        """测试配置同步"""
        manager = CloudSyncManager("node-1", mock_connector, sync_config)
        manager.start()

        # 配置应该在启动时同步
        config_value = manager.config_manager.get("sync_interval")
        assert config_value == 60

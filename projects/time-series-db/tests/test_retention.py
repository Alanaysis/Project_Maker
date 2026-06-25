"""数据保留测试"""

import pytest
import tempfile
import shutil
import os
import time
from src.engine.storage import StorageEngine
from src.retention.ttl import TTLManager


class TestTTLManager:
    """TTL 管理器测试类"""

    def setup_method(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.temp_dir, 'data')
        self.engine = StorageEngine(self.data_dir)

    def teardown_method(self):
        """测试后清理"""
        self.engine.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_set_and_get_ttl(self):
        """测试设置和获取 TTL"""
        ttl_manager = TTLManager(self.engine)

        ttl_manager.set_ttl("cpu", 86400)
        assert ttl_manager.get_ttl("cpu") == 86400

    def test_default_ttl(self):
        """测试默认 TTL"""
        ttl_manager = TTLManager(self.engine, default_ttl=3600)

        assert ttl_manager.get_ttl("cpu") == 3600
        assert ttl_manager.get_ttl("mem") == 3600

    def test_metric_ttl_override(self):
        """测试 metric 级别 TTL 覆盖默认值"""
        ttl_manager = TTLManager(self.engine, default_ttl=3600)

        ttl_manager.set_ttl("cpu", 86400)
        assert ttl_manager.get_ttl("cpu") == 86400
        assert ttl_manager.get_ttl("mem") == 3600

    def test_remove_ttl(self):
        """测试移除 TTL"""
        ttl_manager = TTLManager(self.engine, default_ttl=3600)

        ttl_manager.set_ttl("cpu", 86400)
        ttl_manager.remove_ttl("cpu")
        assert ttl_manager.get_ttl("cpu") == 3600

    def test_list_configs(self):
        """测试列出配置"""
        ttl_manager = TTLManager(self.engine, default_ttl=3600)

        ttl_manager.set_ttl("cpu", 86400)
        ttl_manager.set_ttl("mem", 172800)

        configs = ttl_manager.list_configs()
        assert configs['__default__'] == 3600
        assert configs['cpu'] == 86400
        assert configs['mem'] == 172800

    def test_cleanup(self):
        """测试清理过期数据"""
        ttl_manager = TTLManager(self.engine, default_ttl=10)

        # 写入旧数据
        old_time = int(time.time()) - 100
        self.engine.write("cpu", {"host": "s1"}, old_time, 45.2)

        # 写入新数据
        new_time = int(time.time())
        self.engine.write("cpu", {"host": "s1"}, new_time, 55.2)

        # 清理
        cleaned = ttl_manager.cleanup()
        assert cleaned > 0

        # 查询应该只有新数据
        results = self.engine.query("cpu", 0, int(time.time()) + 100)
        assert len(results) == 1
        assert results[0][0] == new_time

    def test_stats(self):
        """测试统计信息"""
        ttl_manager = TTLManager(self.engine, default_ttl=3600)

        ttl_manager.set_ttl("cpu", 86400)

        stats = ttl_manager.get_stats()
        assert stats['default_ttl'] == 3600
        assert stats['metric_configs'] == 1
        assert stats['cleanup_interval'] == 3600


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

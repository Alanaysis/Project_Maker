"""存储引擎测试"""

import pytest
import tempfile
import shutil
import os
from src.engine.storage import StorageEngine


class TestStorageEngine:
    """存储引擎测试类"""

    def setup_method(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.temp_dir, 'data')
        self.engine = StorageEngine(self.data_dir)

    def teardown_method(self):
        """测试后清理"""
        self.engine.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_write_and_query(self):
        """测试写入和查询"""
        # 写入数据
        self.engine.write("cpu", {"host": "s1"}, 1000, 45.2)
        self.engine.write("cpu", {"host": "s1"}, 2000, 55.2)

        # 查询
        results = self.engine.query("cpu", 0, 3000)
        assert len(results) == 2
        assert results[0] == (1000, 45.2)
        assert results[1] == (2000, 55.2)

    def test_write_batch(self):
        """测试批量写入"""
        points = [
            {"metric": "cpu", "tags": {"host": "s1"}, "timestamp": i * 100, "value": float(i)}
            for i in range(100)
        ]

        count = self.engine.write_batch(points)
        assert count == 100

        results = self.engine.query("cpu", 0, 10000)
        assert len(results) == 100

    def test_query_with_tags(self):
        """测试带标签查询"""
        self.engine.write("cpu", {"host": "s1"}, 1000, 45.2)
        self.engine.write("cpu", {"host": "s2"}, 1000, 55.2)

        results = self.engine.query("cpu", 0, 2000, tags={"host": "s1"})
        assert len(results) == 1
        assert results[0][1] == 45.2

    def test_latest(self):
        """测试获取最新值"""
        self.engine.write("cpu", {"host": "s1"}, 1000, 45.2)
        self.engine.write("cpu", {"host": "s1"}, 2000, 55.2)

        result = self.engine.latest("cpu", {"host": "s1"})
        assert result == (2000, 55.2)

    def test_flush(self):
        """测试刷盘"""
        # 写入数据
        for i in range(100):
            self.engine.write("cpu", {"host": "s1"}, i * 100, float(i))

        # 手动刷盘
        self.engine.flush()

        # 检查 SSTable 是否创建
        assert len(self.engine.sstables.get("cpu", [])) > 0

    def test_query_after_flush(self):
        """测试刷盘后查询"""
        # 写入数据
        for i in range(100):
            self.engine.write("cpu", {"host": "s1"}, i * 100, float(i))

        # 刷盘
        self.engine.flush()

        # 查询
        results = self.engine.query("cpu", 0, 10000)
        assert len(results) == 100

    def test_delete_before(self):
        """测试删除旧数据"""
        for i in range(100):
            self.engine.write("cpu", {"host": "s1"}, i * 100, float(i))

        # 删除 5000 之前的数据
        deleted = self.engine.delete_before("cpu", 5000)
        assert deleted == 50

        # 查询剩余数据
        results = self.engine.query("cpu", 0, 10000)
        assert len(results) == 50

    def test_recover(self):
        """测试从 WAL 恢复"""
        # 写入数据
        self.engine.write("cpu", {"host": "s1"}, 1000, 45.2)
        self.engine.write("cpu", {"host": "s1"}, 2000, 55.2)

        # 关闭引擎
        self.engine.close()

        # 重新打开
        self.engine = StorageEngine(self.data_dir)

        # 查询
        results = self.engine.query("cpu", 0, 3000)
        assert len(results) == 2

    def test_stats(self):
        """测试统计信息"""
        self.engine.write("cpu", {}, 1000, 45.2)

        stats = self.engine.get_stats()
        assert 'memtable_size' in stats
        assert 'memtable_count' in stats
        assert 'wal_stats' in stats


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

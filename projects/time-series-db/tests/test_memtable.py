"""内存表测试"""

import pytest
import tempfile
import shutil
from src.engine.memtable import MemTable


class TestMemTable:
    """内存表测试类"""

    def setup_method(self):
        """测试前准备"""
        self.memtable = MemTable(max_size=1024 * 1024)  # 1MB

    def test_put_and_get(self):
        """测试写入和读取"""
        self.memtable.put("cpu", {"host": "s1"}, 1000, 45.2)
        result = self.memtable.get("cpu", {"host": "s1"}, 1000)
        assert result == 45.2

    def test_put_batch(self):
        """测试批量写入"""
        points = [
            {"metric": "cpu", "tags": {"host": "s1"}, "timestamp": i * 100, "value": float(i)}
            for i in range(100)
        ]
        count = self.memtable.put_batch(points)
        assert count == 100
        assert self.memtable.get_count() == 100

    def test_range_query(self):
        """测试范围查询"""
        # 写入数据
        for i in range(100):
            self.memtable.put("cpu", {"host": "s1"}, i * 100, float(i))

        # 查询范围
        results = self.memtable.range_query("cpu", 1000, 5000)
        assert len(results) == 41  # 1000, 1100, ..., 5000

    def test_range_query_with_tags(self):
        """测试带标签的范围查询"""
        self.memtable.put("cpu", {"host": "s1"}, 1000, 45.2)
        self.memtable.put("cpu", {"host": "s2"}, 1000, 55.2)

        results = self.memtable.range_query("cpu", 0, 2000, tags={"host": "s1"})
        assert len(results) == 1
        assert results[0] == (1000, 45.2)

    def test_latest(self):
        """测试获取最新值"""
        self.memtable.put("cpu", {"host": "s1"}, 1000, 45.2)
        self.memtable.put("cpu", {"host": "s1"}, 2000, 55.2)

        result = self.memtable.latest("cpu", {"host": "s1"})
        assert result == (2000, 55.2)

    def test_delete_before(self):
        """测试删除旧数据"""
        for i in range(100):
            self.memtable.put("cpu", {"host": "s1"}, i * 100, float(i))

        deleted = self.memtable.delete_before("cpu", 5000)
        assert deleted == 50
        assert self.memtable.get_count() == 50

    def test_is_full(self):
        """测试容量检查"""
        small_memtable = MemTable(max_size=100)
        small_memtable.put("cpu", {}, 1000, 45.2)
        assert small_memtable.is_full()

    def test_clear(self):
        """测试清空"""
        self.memtable.put("cpu", {}, 1000, 45.2)
        self.memtable.clear()
        assert self.memtable.get_count() == 0

    def test_get_all(self):
        """测试获取所有数据"""
        self.memtable.put("cpu", {"host": "s1"}, 1000, 45.2)
        self.memtable.put("mem", {"host": "s1"}, 1000, 8192)

        data = self.memtable.get_all()
        assert len(data) == 2

    def test_overwrite(self):
        """测试覆盖写入"""
        self.memtable.put("cpu", {"host": "s1"}, 1000, 45.2)
        self.memtable.put("cpu", {"host": "s1"}, 1000, 55.2)

        result = self.memtable.get("cpu", {"host": "s1"}, 1000)
        assert result == 55.2
        assert self.memtable.get_count() == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

"""WAL 测试"""

import pytest
import tempfile
import shutil
import os
from src.engine.wal import WAL, WALEntry


class TestWAL:
    """WAL 测试类"""

    def setup_method(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.wal_dir = os.path.join(self.temp_dir, 'wal')

    def teardown_method(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_write_and_recover(self):
        """测试写入和恢复"""
        wal = WAL(self.wal_dir)

        # 写入数据
        wal.write("cpu", {"host": "s1"}, 1000, 45.2)
        wal.write("cpu", {"host": "s1"}, 2000, 55.2)
        wal.write("mem", {"host": "s1"}, 1000, 8192)

        # 关闭 WAL
        wal.close()

        # 重新打开并恢复
        wal2 = WAL(self.wal_dir)
        entries = wal2.recover()

        assert len(entries) == 3
        assert entries[0].metric == "cpu"
        assert entries[0].timestamp == 1000
        assert entries[0].value == 45.2

    def test_write_batch(self):
        """测试批量写入"""
        wal = WAL(self.wal_dir)

        points = [
            {"metric": "cpu", "tags": {"host": "s1"}, "timestamp": i, "value": float(i)}
            for i in range(100)
        ]

        count = wal.write_batch(points)
        assert count == 100

        wal.close()

        # 恢复
        wal2 = WAL(self.wal_dir)
        entries = wal2.recover()
        assert len(entries) == 100

    def test_file_rotation(self):
        """测试文件轮转"""
        wal = WAL(self.wal_dir, max_file_size=1024)  # 1KB

        # 写入足够多的数据触发轮转
        for i in range(100):
            wal.write("cpu", {"host": "s1"}, i, float(i))

        wal.close()

        # 检查是否有多个 WAL 文件
        wal_files = [f for f in os.listdir(self.wal_dir) if f.endswith('.wal')]
        assert len(wal_files) > 1

    def test_cleanup(self):
        """测试清理旧文件"""
        wal = WAL(self.wal_dir, max_file_size=512)

        # 写入数据创建多个文件
        for i in range(50):
            wal.write("cpu", {}, i, float(i))

        wal.close()

        # 清理，保留 1 个文件
        wal2 = WAL(self.wal_dir)
        cleaned = wal2.cleanup(keep_files=1)

        wal_files = [f for f in os.listdir(self.wal_dir) if f.endswith('.wal')]
        assert len(wal_files) <= 1

    def test_entry_encode_decode(self):
        """测试条目编码解码"""
        entry = WALEntry("cpu", {"host": "s1", "region": "us"}, 1000, 45.2)

        # 编码
        data = entry.encode()

        # 解码
        decoded, _ = WALEntry.decode(data)

        assert decoded.metric == "cpu"
        assert decoded.tags == {"host": "s1", "region": "us"}
        assert decoded.timestamp == 1000
        assert decoded.value == 45.2

    def test_stats(self):
        """测试统计信息"""
        wal = WAL(self.wal_dir)
        wal.write("cpu", {}, 1000, 45.2)

        stats = wal.get_stats()
        assert stats['file_count'] >= 1
        assert stats['total_size'] > 0
        assert stats['current_size'] > 0

        wal.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

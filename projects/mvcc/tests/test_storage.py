"""存储引擎单元测试。"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from mvcc.storage import Storage
from mvcc.transaction import Transaction
from mvcc.snapshot import Snapshot


class TestStorage:
    """Storage 测试。"""

    def _make_txn(self, txn_id=1, start_ts=1):
        snapshot = Snapshot(start_ts, set())
        return Transaction(txn_id, start_ts, snapshot)

    def test_empty_storage(self):
        """测试空存储。"""
        storage = Storage()
        assert len(storage) == 0

    def test_write_and_read(self):
        """测试写入和读取。"""
        storage = Storage()
        txn = self._make_txn()

        storage.write("key1", 100, txn)
        # 写缓冲中的值可以被同一事务读取
        assert storage.read("key1", txn) == 100

    def test_read_nonexistent(self):
        """测试读取不存在的 key。"""
        storage = Storage()
        txn = self._make_txn()
        assert storage.read("nonexistent", txn) is None

    def test_write_buffer_isolation(self):
        """测试写缓冲隔离（其他事务看不到未提交的写入）。"""
        storage = Storage()
        txn1 = self._make_txn(txn_id=1, start_ts=1)
        txn2 = self._make_txn(txn_id=2, start_ts=2)

        storage.write("key1", 100, txn1)
        # txn2 看不到 txn1 未提交的写入
        assert storage.read("key1", txn2) is None

    def test_delete(self):
        """测试删除操作。"""
        storage = Storage()
        txn = self._make_txn()

        storage.write("key1", 100, txn)
        result = storage.delete("key1", txn)
        assert result is True
        assert storage.read("key1", txn) is None

    def test_delete_nonexistent(self):
        """测试删除不存在的 key。"""
        storage = Storage()
        txn = self._make_txn()
        result = storage.delete("nonexistent", txn)
        assert result is False

    def test_apply_commit(self):
        """测试提交时应用写缓冲。"""
        storage = Storage()
        txn = self._make_txn()

        storage.write("key1", 100, txn)
        storage.write("key2", 200, txn)

        ops = storage.apply_commit(txn, commit_ts=5)
        assert ops == 2
        assert "key1" in storage.data
        assert "key2" in storage.data

    def test_commit_then_read(self):
        """测试提交后其他事务可以读取。"""
        storage = Storage()
        txn1 = self._make_txn(txn_id=1, start_ts=1)
        storage.write("key1", 100, txn1)
        storage.apply_commit(txn1, commit_ts=2)

        # 新事务可以看到已提交的数据
        snap = Snapshot(3, set())
        txn2 = Transaction(2, 3, snap)
        assert storage.read("key1", txn2) == 100

    def test_overwrite(self):
        """测试覆盖写入。"""
        storage = Storage()
        txn = self._make_txn()

        storage.write("key1", 100, txn)
        storage.write("key1", 200, txn)
        # 写缓冲中是最新的值
        assert storage.read("key1", txn) == 200

    def test_version_chain_exists(self):
        """测试版本链在提交后存在。"""
        storage = Storage()
        txn = self._make_txn()
        storage.write("key1", 100, txn)
        storage.apply_commit(txn, commit_ts=2)

        chain = storage.get_version_chain("key1")
        assert chain is not None
        assert chain.length == 1

    def test_get_all_keys(self):
        """测试获取所有 key。"""
        storage = Storage()
        txn = self._make_txn()
        storage.write("key1", 100, txn)
        storage.write("key2", 200, txn)
        storage.apply_commit(txn, commit_ts=2)

        keys = storage.get_all_keys()
        assert "key1" in keys
        assert "key2" in keys


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

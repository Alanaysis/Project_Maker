"""事务管理器单元测试。"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from mvcc.transaction import Transaction, TransactionManager, TxnStatus
from mvcc.snapshot import Snapshot


class TestTransaction:
    """Transaction 对象测试。"""

    def _make_txn(self, txn_id=1, start_ts=1):
        snapshot = Snapshot(start_ts, set())
        return Transaction(txn_id, start_ts, snapshot)

    def test_create_transaction(self):
        """测试创建事务。"""
        txn = self._make_txn()
        assert txn.txn_id == 1
        assert txn.start_ts == 1
        assert txn.status == TxnStatus.ACTIVE
        assert txn.is_active
        assert len(txn.read_set) == 0
        assert len(txn.write_buffer) == 0
        assert len(txn.delete_set) == 0

    def test_add_read(self):
        """测试记录读操作。"""
        txn = self._make_txn()
        txn.add_read("key1")
        txn.add_read("key2")
        assert "key1" in txn.read_set
        assert "key2" in txn.read_set

    def test_add_write(self):
        """测试记录写操作。"""
        txn = self._make_txn()
        txn.add_write("key1", 100)
        assert txn.write_buffer["key1"] == 100

    def test_add_write_removes_delete(self):
        """测试写入取消之前的删除标记。"""
        txn = self._make_txn()
        txn.add_delete("key1")
        assert "key1" in txn.delete_set

        txn.add_write("key1", 100)
        assert "key1" not in txn.delete_set
        assert txn.write_buffer["key1"] == 100

    def test_add_delete(self):
        """测试记录删除操作。"""
        txn = self._make_txn()
        txn.add_write("key1", 100)
        txn.add_delete("key1")
        assert "key1" in txn.delete_set
        assert "key1" not in txn.write_buffer

    def test_get_write(self):
        """测试从写缓冲获取值。"""
        txn = self._make_txn()
        assert txn.get_write("key1") is None

        txn.add_write("key1", 100)
        assert txn.get_write("key1") == 100

    def test_is_write_buffered(self):
        """测试检查写缓冲状态。"""
        txn = self._make_txn()
        assert not txn.is_write_buffered("key1")

        txn.add_write("key1", 100)
        assert txn.is_write_buffered("key1")

    def test_commit(self):
        """测试提交事务。"""
        txn = self._make_txn()
        txn.commit(commit_ts=2)
        assert txn.status == TxnStatus.COMMITTED
        assert txn.is_committed
        assert txn.commit_ts == 2

    def test_abort(self):
        """测试中止事务。"""
        txn = self._make_txn()
        txn.add_write("key1", 100)
        txn.add_delete("key2")
        txn.abort()

        assert txn.status == TxnStatus.ABORTED
        assert txn.is_aborted
        assert len(txn.write_buffer) == 0
        assert len(txn.delete_set) == 0

    def test_double_commit_raises(self):
        """测试重复提交抛出异常。"""
        txn = self._make_txn()
        txn.commit(commit_ts=2)
        with pytest.raises(RuntimeError):
            txn.commit(commit_ts=3)

    def test_double_abort_raises(self):
        """测试重复中止抛出异常。"""
        txn = self._make_txn()
        txn.abort()
        with pytest.raises(RuntimeError):
            txn.abort()

    def test_repr(self):
        """测试字符串表示。"""
        txn = self._make_txn()
        assert "ACTIVE" in repr(txn)


class TestTransactionManager:
    """TransactionManager 测试。"""

    def test_begin(self):
        """测试开始事务。"""
        mgr = TransactionManager()
        snapshot = Snapshot(0, set())
        txn = mgr.begin(snapshot)

        assert txn.txn_id == 1
        assert mgr.active_count == 1

    def test_multiple_begins(self):
        """测试多个事务。"""
        mgr = TransactionManager()
        snapshot = Snapshot(0, set())

        txn1 = mgr.begin(snapshot)
        txn2 = mgr.begin(snapshot)
        txn3 = mgr.begin(snapshot)

        assert txn1.txn_id != txn2.txn_id != txn3.txn_id
        assert mgr.active_count == 3

    def test_commit(self):
        """测试提交事务。"""
        mgr = TransactionManager()
        snapshot = Snapshot(0, set())
        txn = mgr.begin(snapshot)

        commit_ts = mgr.advance_timestamp()
        mgr.commit(txn, commit_ts)

        assert mgr.active_count == 0
        assert mgr.committed_count == 1
        assert txn.is_committed

    def test_abort(self):
        """测试中止事务。"""
        mgr = TransactionManager()
        snapshot = Snapshot(0, set())
        txn = mgr.begin(snapshot)

        mgr.abort(txn)

        assert mgr.active_count == 0
        assert txn.is_aborted

    def test_get_active_txn_ids(self):
        """测试获取活跃事务 ID 集合。"""
        mgr = TransactionManager()
        snapshot = Snapshot(0, set())

        txn1 = mgr.begin(snapshot)
        txn2 = mgr.begin(snapshot)
        active = mgr.get_active_txn_ids()

        assert txn1.txn_id in active
        assert txn2.txn_id in active

    def test_advance_timestamp(self):
        """测试时间戳推进。"""
        mgr = TransactionManager()
        assert mgr.get_timestamp() == 0

        ts1 = mgr.advance_timestamp()
        ts2 = mgr.advance_timestamp()
        assert ts1 < ts2
        assert mgr.get_timestamp() == ts2

    def test_get_txn(self):
        """测试根据 ID 获取事务。"""
        mgr = TransactionManager()
        snapshot = Snapshot(0, set())
        txn = mgr.begin(snapshot)

        found = mgr.get_txn(txn.txn_id)
        assert found is txn

        assert mgr.get_txn(999) is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

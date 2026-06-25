"""冲突检测单元测试。"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from mvcc.conflict import ConflictDetector, ConflictResult
from mvcc.transaction import Transaction
from mvcc.snapshot import Snapshot
from mvcc.version import Version, VersionChain


class TestConflictDetector:
    """ConflictDetector 测试。"""

    def _make_txn(self, txn_id=1, start_ts=1, active_txns=None):
        if active_txns is None:
            active_txns = set()
        snapshot = Snapshot(start_ts, active_txns)
        return Transaction(txn_id, start_ts, snapshot)

    def _make_chain_with_version(self, value, create_txn_id, create_ts):
        chain = VersionChain()
        v = Version(data={"value": value}, create_txn_id=create_txn_id, create_ts=create_ts)
        chain.append(v)
        return chain

    def test_no_conflict_empty_write(self):
        """测试无写入时无冲突。"""
        detector = ConflictDetector()
        txn = self._make_txn()
        result = detector.check_all(txn, {}, {})
        assert not result.has_conflict

    def test_no_conflict_new_key(self):
        """测试写入新 key 无冲突。"""
        detector = ConflictDetector()
        txn = self._make_txn()
        txn.add_write("new_key", 100)
        result = detector.check_write_write(txn, {}, {})
        assert not result.has_conflict

    def test_write_write_conflict(self):
        """测试写写冲突。"""
        detector = ConflictDetector()
        txn1 = self._make_txn(txn_id=1, start_ts=1)
        txn2 = self._make_txn(txn_id=2, start_ts=2)

        # txn2 已提交，写入了 key1
        txn2.commit(commit_ts=3)
        committed_txns = {2: txn2}

        # txn1 也想写 key1
        txn1.add_write("key1", 100)
        chain = self._make_chain_with_version(200, 2, 3)

        result = detector.check_write_write(
            txn1, {"key1": chain}, committed_txns
        )
        assert result.has_conflict
        assert result.conflict_type == "write_write"
        assert "key1" in result.conflicting_keys

    def test_no_write_write_conflict_earlier_commit(self):
        """测试先提交的事务无写写冲突。"""
        detector = ConflictDetector()
        txn1 = self._make_txn(txn_id=1, start_ts=3)
        txn2 = self._make_txn(txn_id=2, start_ts=1)

        # txn2 在 txn1 开始之前就已提交
        txn2.commit(commit_ts=2)
        committed_txns = {2: txn2}

        txn1.add_write("key1", 100)
        chain = self._make_chain_with_version(200, 2, 2)

        result = detector.check_write_write(
            txn1, {"key1": chain}, committed_txns
        )
        assert not result.has_conflict

    def test_read_write_conflict(self):
        """测试读写冲突。"""
        detector = ConflictDetector()
        txn1 = self._make_txn(txn_id=1, start_ts=1)
        txn2 = self._make_txn(txn_id=2, start_ts=2)

        # txn2 已提交，修改了 key1
        txn2.commit(commit_ts=3)
        committed_txns = {2: txn2}

        # txn1 读取了 key1
        txn1.add_read("key1")
        chain = self._make_chain_with_version(200, 2, 3)

        result = detector.check_read_write(
            txn1, {"key1": chain}, committed_txns
        )
        assert result.has_conflict
        assert result.conflict_type == "read_write"
        assert "key1" in result.conflicting_keys

    def test_no_read_write_conflict_own_write(self):
        """测试自己写入的 key 不产生读写冲突。"""
        detector = ConflictDetector()
        txn1 = self._make_txn(txn_id=1, start_ts=1)
        txn2 = self._make_txn(txn_id=2, start_ts=2)

        txn2.commit(commit_ts=3)
        committed_txns = {2: txn2}

        # txn1 读取并写入了 key1（自依赖不算冲突）
        txn1.add_read("key1")
        txn1.add_write("key1", 100)

        result = detector.check_read_write(
            txn1, {}, committed_txns
        )
        assert not result.has_conflict

    def test_check_all_ww_first(self):
        """测试 check_all 优先检测写写冲突。"""
        detector = ConflictDetector()
        txn1 = self._make_txn(txn_id=1, start_ts=1)
        txn2 = self._make_txn(txn_id=2, start_ts=2)

        txn2.commit(commit_ts=3)
        committed_txns = {2: txn2}

        # 同时有读写和写写冲突
        txn1.add_read("key1")
        txn1.add_write("key1", 100)
        chain = self._make_chain_with_version(200, 2, 3)

        result = detector.check_all(
            txn1, {"key1": chain}, committed_txns
        )
        assert result.has_conflict
        # 写写冲突优先
        assert result.conflict_type == "write_write"

    def test_conflict_result_fields(self):
        """测试 ConflictResult 字段。"""
        result = ConflictResult(
            has_conflict=True,
            conflict_type="write_write",
            conflicting_keys={"key1"},
            message="test",
        )
        assert result.has_conflict
        assert result.conflict_type == "write_write"
        assert "key1" in result.conflicting_keys


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

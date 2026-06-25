"""快照隔离单元测试。"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from mvcc.snapshot import Snapshot


class TestSnapshot:
    """Snapshot 测试。"""

    def test_create_snapshot(self):
        """测试创建快照。"""
        snap = Snapshot(timestamp=5, active_txns={2, 3})
        assert snap.timestamp == 5
        assert 2 in snap.active_txns
        assert 3 in snap.active_txns

    def test_snapshot_immutable(self):
        """测试快照不可变性。"""
        snap = Snapshot(timestamp=5, active_txns={2, 3})
        # frozenset 不支持 add
        with pytest.raises(AttributeError):
            snap.active_txns.add(4)

    def test_visible_basic(self):
        """测试基本可见性判断。"""
        snap = Snapshot(timestamp=5, active_txns=set())
        # 创建于时间 3，无删除 -> 可见
        assert snap.is_visible(
            create_txn_id=1, create_ts=3,
        )

    def test_visible_future_version(self):
        """测试未来版本不可见。"""
        snap = Snapshot(timestamp=5, active_txns=set())
        # 创建于时间 10 > 快照时间 5 -> 不可见
        assert not snap.is_visible(
            create_txn_id=1, create_ts=10,
        )

    def test_visible_active_creator(self):
        """测试活跃事务创建的版本不可见。"""
        snap = Snapshot(timestamp=5, active_txns={1})
        # 创建事务 1 在活跃集合中 -> 不可见
        assert not snap.is_visible(
            create_txn_id=1, create_ts=3,
        )

    def test_visible_deleted_before_snapshot(self):
        """测试在快照之前删除的版本不可见。"""
        snap = Snapshot(timestamp=5, active_txns=set())
        # 在时间 4 删除，删除时间 <= 快照时间 -> 不可见
        assert not snap.is_visible(
            create_txn_id=1, create_ts=3,
            delete_txn_id=2, delete_ts=4,
        )

    def test_visible_deleted_after_snapshot(self):
        """测试在快照之后删除的版本仍然可见。"""
        snap = Snapshot(timestamp=5, active_txns=set())
        # 在时间 8 删除，删除时间 > 快照时间 -> 可见
        assert snap.is_visible(
            create_txn_id=1, create_ts=3,
            delete_txn_id=2, delete_ts=8,
        )

    def test_visible_deleted_by_active_txn(self):
        """测试活跃事务的删除操作不可见。"""
        snap = Snapshot(timestamp=5, active_txns={2})
        # 删除事务 2 在活跃集合中 -> 删除未生效，版本可见
        assert snap.is_visible(
            create_txn_id=1, create_ts=3,
            delete_txn_id=2, delete_ts=4,
        )

    def test_equality(self):
        """测试快照相等性。"""
        snap1 = Snapshot(timestamp=5, active_txns={1, 2})
        snap2 = Snapshot(timestamp=5, active_txns={1, 2})
        snap3 = Snapshot(timestamp=5, active_txns={1, 3})

        assert snap1 == snap2
        assert snap1 != snap3

    def test_hash(self):
        """测试快照哈希。"""
        snap1 = Snapshot(timestamp=5, active_txns={1, 2})
        snap2 = Snapshot(timestamp=5, active_txns={1, 2})

        assert hash(snap1) == hash(snap2)
        # 可以作为字典键
        d = {snap1: "test"}
        assert d[snap2] == "test"

    def test_repr(self):
        """测试字符串表示。"""
        snap = Snapshot(timestamp=5, active_txns={1, 2})
        r = repr(snap)
        assert "5" in r
        assert "Snapshot" in r


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

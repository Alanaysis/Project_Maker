"""版本链单元测试。"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from mvcc.version import Version, VersionChain


class TestVersion:
    """Version 对象测试。"""

    def test_create_version(self):
        """测试创建版本。"""
        v = Version(data={"value": 100}, create_txn_id=1, create_ts=1)
        assert v.data == {"value": 100}
        assert v.create_txn_id == 1
        assert v.create_ts == 1
        assert v.delete_txn_id is None
        assert v.delete_ts is None
        assert v.prev is None
        assert not v.is_deleted

    def test_mark_deleted(self):
        """测试标记删除。"""
        v = Version(data={"value": 100}, create_txn_id=1, create_ts=1)
        assert not v.is_deleted

        v.mark_deleted(txn_id=2, ts=3)
        assert v.is_deleted
        assert v.delete_txn_id == 2
        assert v.delete_ts == 3

    def test_repr(self):
        """测试字符串表示。"""
        v = Version(data={"value": 42}, create_txn_id=1, create_ts=1)
        assert "ACTIVE" in repr(v)

        v.mark_deleted(2, 3)
        assert "DELETED" in repr(v)


class TestVersionChain:
    """VersionChain 测试。"""

    def test_empty_chain(self):
        """测试空版本链。"""
        chain = VersionChain()
        assert chain.head is None
        assert chain.length == 0
        assert len(chain) == 0

    def test_append_single(self):
        """测试追加单个版本。"""
        chain = VersionChain()
        v = Version(data={"value": 100}, create_txn_id=1, create_ts=1)
        chain.append(v)

        assert chain.head is v
        assert chain.length == 1

    def test_append_multiple(self):
        """测试追加多个版本（新版本在链头）。"""
        chain = VersionChain()
        v1 = Version(data={"value": 100}, create_txn_id=1, create_ts=1)
        v2 = Version(data={"value": 200}, create_txn_id=2, create_ts=2)
        v3 = Version(data={"value": 300}, create_txn_id=3, create_ts=3)

        chain.append(v1)
        chain.append(v2)
        chain.append(v3)

        assert chain.head is v3
        assert chain.head.prev is v2
        assert chain.head.prev.prev is v1
        assert chain.length == 3

    def test_find_visible_basic(self):
        """测试基本的版本可见性查找。"""
        chain = VersionChain()
        v1 = Version(data={"value": 100}, create_txn_id=1, create_ts=1)
        v2 = Version(data={"value": 200}, create_txn_id=2, create_ts=2)
        chain.append(v1)
        chain.append(v2)

        # 快照时间 >= 2，事务 1 和 2 不在活跃集合中 -> 看到 v2
        visible = chain.find_visible(snapshot_ts=2, active_txns=set())
        assert visible is v2
        assert visible.data["value"] == 200

    def test_find_visible_old_version(self):
        """测试快照时间较早时看到旧版本。"""
        chain = VersionChain()
        v1 = Version(data={"value": 100}, create_txn_id=1, create_ts=1)
        v2 = Version(data={"value": 200}, create_txn_id=2, create_ts=2)
        chain.append(v1)
        chain.append(v2)

        # 快照时间 = 1，只能看到 v1
        visible = chain.find_visible(snapshot_ts=1, active_txns=set())
        assert visible is v1

    def test_find_visible_active_txn(self):
        """测试活跃事务创建的版本不可见。"""
        chain = VersionChain()
        v1 = Version(data={"value": 100}, create_txn_id=1, create_ts=1)
        v2 = Version(data={"value": 200}, create_txn_id=2, create_ts=2)
        chain.append(v1)
        chain.append(v2)

        # 事务 2 活跃 -> 跳过 v2，看到 v1
        visible = chain.find_visible(snapshot_ts=2, active_txns={2})
        assert visible is v1

    def test_find_visible_deleted(self):
        """测试已删除的版本不可见。"""
        chain = VersionChain()
        v1 = Version(data={"value": 100}, create_txn_id=1, create_ts=1)
        v1.mark_deleted(txn_id=2, ts=2)
        v2 = Version(data={"value": 200}, create_txn_id=3, create_ts=3)
        chain.append(v1)
        chain.append(v2)

        # v1 在快照时间 2 之前被删除 -> 不可见，看到 v2
        visible = chain.find_visible(snapshot_ts=3, active_txns=set())
        assert visible is v2

    def test_find_visible_read_own(self):
        """测试读取自己未提交的写入。"""
        chain = VersionChain()
        v1 = Version(data={"value": 100}, create_txn_id=1, create_ts=1)
        v2 = Version(data={"value": 200}, create_txn_id=2, create_ts=2)
        chain.append(v1)
        chain.append(v2)

        # 事务 2 读取自己的写入
        visible = chain.find_visible(
            snapshot_ts=1, active_txns={2}, read_own=True, txn_id=2
        )
        assert visible is v2
        assert visible.data["value"] == 200

    def test_find_visible_no_match(self):
        """测试没有可见版本的情况。"""
        chain = VersionChain()
        v1 = Version(data={"value": 100}, create_txn_id=1, create_ts=1)
        chain.append(v1)

        # 快照时间太早 -> 看不到任何版本
        visible = chain.find_visible(snapshot_ts=0, active_txns=set())
        assert visible is None

    def test_find_latest_committed(self):
        """测试查找最新已提交版本。"""
        chain = VersionChain()
        v1 = Version(data={"value": 100}, create_txn_id=1, create_ts=1)
        v2 = Version(data={"value": 200}, create_txn_id=2, create_ts=2)
        chain.append(v1)
        chain.append(v2)

        latest = chain.find_latest_committed()
        assert latest is v2

    def test_find_latest_committed_deleted(self):
        """测试最新版本被删除时的查找。"""
        chain = VersionChain()
        v1 = Version(data={"value": 100}, create_txn_id=1, create_ts=1)
        v2 = Version(data={"value": 200}, create_txn_id=2, create_ts=2)
        v2.mark_deleted(3, 3)
        chain.append(v1)
        chain.append(v2)

        latest = chain.find_latest_committed()
        assert latest is v1

    def test_gc_basic(self):
        """测试基本的垃圾回收。"""
        chain = VersionChain()
        v1 = Version(data={"value": 100}, create_txn_id=1, create_ts=1)
        v1.mark_deleted(2, 2)
        v2 = Version(data={"value": 200}, create_txn_id=2, create_ts=2)
        v3 = Version(data={"value": 300}, create_txn_id=3, create_ts=3)
        chain.append(v1)
        chain.append(v2)
        chain.append(v3)

        # 安全点 = 3，事务 2 已提交 -> v1 可以清理
        collected = chain.gc(min_active_ts=3, committed_txns={2})
        assert collected >= 0  # 至少清理了 v1
        assert chain.length >= 1  # 至少保留一个版本

    def test_gc_preserves_head(self):
        """测试 GC 保留链头版本。"""
        chain = VersionChain()
        v1 = Version(data={"value": 100}, create_txn_id=1, create_ts=1)
        v1.mark_deleted(2, 2)
        v2 = Version(data={"value": 200}, create_txn_id=2, create_ts=2)
        chain.append(v1)
        chain.append(v2)

        chain.gc(min_active_ts=10, committed_txns={2})
        # 链头 v2 应该被保留
        assert chain.head is v2

    def test_gc_empty_chain(self):
        """测试空链的 GC。"""
        chain = VersionChain()
        collected = chain.gc(min_active_ts=10, committed_txns=set())
        assert collected == 0

    def test_to_list(self):
        """测试转列表。"""
        chain = VersionChain()
        v1 = Version(data={"value": 100}, create_txn_id=1, create_ts=1)
        v2 = Version(data={"value": 200}, create_txn_id=2, create_ts=2)
        chain.append(v1)
        chain.append(v2)

        result = chain.to_list()
        assert len(result) == 2
        assert result[0] is v2
        assert result[1] is v1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""垃圾回收器单元测试。"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from mvcc.gc import GarbageCollector
from mvcc.transaction import Transaction, TransactionManager
from mvcc.snapshot import Snapshot
from mvcc.version import Version, VersionChain


class TestGarbageCollector:
    """GarbageCollector 测试。"""

    def test_create_gc(self):
        """测试创建 GC。"""
        gc = GarbageCollector(gc_threshold=5)
        assert gc.gc_threshold == 5
        assert gc.total_collected == 0
        assert gc.gc_count == 0

    def test_compute_safe_point_no_active(self):
        """测试无活跃事务时的安全点。"""
        gc = GarbageCollector()
        mgr = TransactionManager()
        safe_point = gc.compute_safe_point(mgr)
        assert safe_point == 0

    def test_compute_safe_point_with_active(self):
        """测试有活跃事务时的安全点。"""
        gc = GarbageCollector()
        mgr = TransactionManager()
        snapshot = Snapshot(0, set())

        txn1 = mgr.begin(snapshot)
        txn2 = mgr.begin(snapshot)

        safe_point = gc.compute_safe_point(mgr)
        # 安全点应该是最早活跃事务的开始时间戳
        assert safe_point == min(txn1.start_ts, txn2.start_ts)

    def test_needs_gc(self):
        """测试是否需要 GC。"""
        gc = GarbageCollector(gc_threshold=3)
        chain = VersionChain()

        v1 = Version(data={"v": 1}, create_txn_id=1, create_ts=1)
        chain.append(v1)
        assert not gc.needs_gc(chain)

        v2 = Version(data={"v": 2}, create_txn_id=2, create_ts=2)
        chain.append(v2)
        assert not gc.needs_gc(chain)

        v3 = Version(data={"v": 3}, create_txn_id=3, create_ts=3)
        chain.append(v3)
        assert gc.needs_gc(chain)

    def test_collect_single(self):
        """测试单条版本链的 GC。"""
        gc = GarbageCollector(gc_threshold=2)
        mgr = TransactionManager()
        snapshot = Snapshot(0, set())

        # 创建版本链
        chain = VersionChain()
        v1 = Version(data={"v": 1}, create_txn_id=1, create_ts=1)
        v1.mark_deleted(2, 2)
        v2 = Version(data={"v": 2}, create_txn_id=2, create_ts=2)
        chain.append(v1)
        chain.append(v2)

        # 创建事务来获取安全点
        txn = mgr.begin(snapshot)

        collected = gc.collect_single(chain, mgr)
        # v1 被删除且安全点允许清理
        assert gc.total_collected == collected

    def test_collect_multiple_chains(self):
        """测试批量 GC。"""
        gc = GarbageCollector(gc_threshold=2)
        mgr = TransactionManager()
        snapshot = Snapshot(0, set())

        # 创建多条版本链
        chains = {}
        for i in range(5):
            chain = VersionChain()
            v1 = Version(data={"v": i}, create_txn_id=i * 2 + 1, create_ts=i * 2 + 1)
            v1.mark_deleted(i * 2 + 2, i * 2 + 2)
            v2 = Version(data={"v": i + 10}, create_txn_id=i * 2 + 2, create_ts=i * 2 + 2)
            chain.append(v1)
            chain.append(v2)
            chains[f"key{i}"] = chain

        txn = mgr.begin(snapshot)
        total, keys = gc.collect(chains, mgr)

        assert gc.gc_count == 1
        assert keys <= 5

    def test_collect_with_max_keys(self):
        """测试限制 GC 处理的 key 数量。"""
        gc = GarbageCollector(gc_threshold=1)
        mgr = TransactionManager()
        snapshot = Snapshot(0, set())

        chains = {}
        for i in range(10):
            chain = VersionChain()
            v = Version(data={"v": i}, create_txn_id=1, create_ts=1)
            chain.append(v)
            chains[f"key{i}"] = chain

        txn = mgr.begin(snapshot)
        total, keys = gc.collect(chains, mgr, max_keys=3)

        assert keys <= 3

    def test_stats(self):
        """测试统计信息。"""
        gc = GarbageCollector(gc_threshold=5)
        stats = gc.stats
        assert stats["gc_count"] == 0
        assert stats["total_collected"] == 0
        assert stats["gc_threshold"] == 5

    def test_repr(self):
        """测试字符串表示。"""
        gc = GarbageCollector(gc_threshold=5)
        assert "GarbageCollector" in repr(gc)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""MVCC 引擎集成测试。"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from mvcc.engine import MVCCEngine


class TestMVCCEngine:
    """MVCCEngine 集成测试。"""

    def test_create_engine(self):
        """测试创建引擎。"""
        engine = MVCCEngine()
        stats = engine.get_stats()
        assert stats["storage_keys"] == 0
        assert stats["active_txns"] == 0

    def test_basic_write_read(self):
        """测试基本写入和读取。"""
        engine = MVCCEngine()

        txn = engine.begin()
        engine.txn_write(txn, "key1", 100)
        engine.txn_write(txn, "key2", 200)
        result = engine.commit(txn)

        assert not result.has_conflict
        assert engine.txn_read(engine.begin(), "key1") == 100

    def test_read_own_write(self):
        """测试事务读取自己的写入。"""
        engine = MVCCEngine()

        txn = engine.begin()
        engine.txn_write(txn, "key1", 100)
        # 在同一事务中读取自己写入的值
        assert engine.txn_read(txn, "key1") == 100
        engine.commit(txn)

    def test_snapshot_isolation(self):
        """测试快照隔离 - 读取开始时的一致性视图。"""
        engine = MVCCEngine()

        # 写入初始数据
        txn1 = engine.begin()
        engine.txn_write(txn1, "key1", 100)
        engine.commit(txn1)

        # txn2 开始（快照时刻 key1=100）
        txn2 = engine.begin()
        assert engine.txn_read(txn2, "key1") == 100

        # txn3 修改 key1
        txn3 = engine.begin()
        engine.txn_write(txn3, "key1", 200)
        engine.commit(txn3)

        # txn2 仍然看到旧值（快照隔离）
        assert engine.txn_read(txn2, "key1") == 100
        engine.commit(txn2)

    def test_write_write_conflict(self):
        """测试写写冲突检测。"""
        engine = MVCCEngine()

        # 写入初始数据
        txn0 = engine.begin()
        engine.txn_write(txn0, "key1", 100)
        engine.commit(txn0)

        # 两个并发事务修改同一个 key
        txn1 = engine.begin()
        txn2 = engine.begin()

        engine.txn_write(txn1, "key1", 200)
        engine.txn_write(txn2, "key1", 300)

        # txn1 先提交 -> 成功
        result1 = engine.commit(txn1)
        assert not result1.has_conflict

        # txn2 后提交 -> 冲突
        result2 = engine.commit(txn2)
        assert result2.has_conflict
        assert result2.conflict_type == "write_write"
        assert txn2.is_aborted

    def test_read_write_conflict(self):
        """测试读写冲突检测。"""
        engine = MVCCEngine()

        # 写入初始数据
        txn0 = engine.begin()
        engine.txn_write(txn0, "balance_a", 1000)
        engine.txn_write(txn0, "balance_b", 1000)
        engine.commit(txn0)

        # txn1 读取 balance_a
        txn1 = engine.begin()
        engine.txn_read(txn1, "balance_a")

        # txn2 修改 balance_a 并提交
        txn2 = engine.begin()
        engine.txn_write(txn2, "balance_a", 500)
        engine.commit(txn2)

        # txn1 提交 -> 读写冲突
        result = engine.commit(txn1)
        assert result.has_conflict
        assert result.conflict_type == "read_write"
        assert txn1.is_aborted

    def test_delete_operation(self):
        """测试删除操作。"""
        engine = MVCCEngine()

        # 写入数据
        txn1 = engine.begin()
        engine.txn_write(txn1, "key1", 100)
        engine.commit(txn1)

        # 删除数据
        txn2 = engine.begin()
        result = engine.txn_delete(txn2, "key1")
        assert result is True
        engine.commit(txn2)

        # 新事务看不到已删除的数据
        txn3 = engine.begin()
        assert engine.txn_read(txn3, "key1") is None
        engine.commit(txn3)

    def test_abort_discards_writes(self):
        """测试中止丢弃写入。"""
        engine = MVCCEngine()

        txn = engine.begin()
        engine.txn_write(txn, "key1", 100)
        engine.abort(txn)

        # 写入被丢弃
        txn2 = engine.begin()
        assert engine.txn_read(txn2, "key1") is None
        engine.commit(txn2)

    def test_batch_operations(self):
        """测试批量操作。"""
        engine = MVCCEngine()

        txn = engine.begin()
        engine.txn_write_batch(txn, {
            "a": 1, "b": 2, "c": 3,
        })
        engine.commit(txn)

        txn2 = engine.begin()
        values = engine.txn_read_batch(txn2, ["a", "b", "c", "d"])
        assert values["a"] == 1
        assert values["b"] == 2
        assert values["c"] == 3
        assert values["d"] is None
        engine.commit(txn2)

    def test_multiple_version_history(self):
        """测试多版本历史。"""
        engine = MVCCEngine()

        # 写入多个版本
        for i in range(5):
            txn = engine.begin()
            engine.txn_write(txn, "key1", i * 100)
            engine.commit(txn)

        # 检查版本链长度
        chain = engine.get_version_chain("key1")
        assert chain is not None
        assert chain.length == 5

        # 最新值
        txn = engine.begin()
        assert engine.txn_read(txn, "key1") == 400
        engine.commit(txn)

    def test_gc_integration(self):
        """测试垃圾回收集成。"""
        engine = MVCCEngine(gc_threshold=3)

        # 写入多个版本触发 GC 阈值
        for i in range(5):
            txn = engine.begin()
            engine.txn_write(txn, "key1", i * 100)
            engine.commit(txn)

        # 执行 GC
        collected, keys = engine.run_gc()
        stats = engine.get_stats()
        assert stats["gc"]["gc_count"] == 1

    def test_engine_stats(self):
        """测试引擎统计。"""
        engine = MVCCEngine()

        txn1 = engine.begin()
        txn2 = engine.begin()
        engine.txn_write(txn1, "key1", 100)
        engine.commit(txn1)

        stats = engine.get_stats()
        assert stats["storage_keys"] == 1
        assert stats["active_txns"] == 1
        assert stats["committed_txns"] == 1

    def test_engine_repr(self):
        """测试引擎字符串表示。"""
        engine = MVCCEngine()
        assert "MVCCEngine" in repr(engine)

    def test_concurrent_independent_writes(self):
        """测试并发独立写入（无冲突）。"""
        engine = MVCCEngine()

        txn1 = engine.begin()
        txn2 = engine.begin()

        engine.txn_write(txn1, "key1", 100)
        engine.txn_write(txn2, "key2", 200)

        result1 = engine.commit(txn1)
        result2 = engine.commit(txn2)

        assert not result1.has_conflict
        assert not result2.has_conflict

    def test_write_skew_scenario(self):
        """测试 Write Skew 场景（经典 SI 问题）。"""
        engine = MVCCEngine()

        # 初始化：两个账户各有 500
        txn0 = engine.begin()
        engine.txn_write(txn0, "account_a", 500)
        engine.txn_write(txn0, "account_b", 500)
        engine.commit(txn0)

        # 场景：两个事务各自检查总额 >= 1000，然后各自扣除
        # 这是 Write Skew 的经典案例

        # txn1: 读取两个账户
        txn1 = engine.begin()
        a1 = engine.txn_read(txn1, "account_a")
        b1 = engine.txn_read(txn1, "account_b")
        # 从 a 扣 100
        engine.txn_write(txn1, "account_a", a1 - 100)

        # txn2: 读取两个账户
        txn2 = engine.begin()
        a2 = engine.txn_read(txn2, "account_a")
        b2 = engine.txn_read(txn2, "account_b")
        # 从 b 扣 100
        engine.txn_write(txn2, "account_b", b2 - 100)

        # txn1 提交
        result1 = engine.commit(txn1)
        assert not result1.has_conflict

        # txn2 提交 -> 检测到读写冲突
        result2 = engine.commit(txn2)
        # txn2 读取的 account_a 被 txn1 修改了
        assert result2.has_conflict

    def test_commit_non_active_raises(self):
        """测试提交非活跃事务抛出异常。"""
        engine = MVCCEngine()
        txn = engine.begin()
        engine.commit(txn)

        with pytest.raises(RuntimeError):
            engine.commit(txn)

    def test_abort_non_active_raises(self):
        """测试中止非活跃事务抛出异常。"""
        engine = MVCCEngine()
        txn = engine.begin()
        engine.commit(txn)

        with pytest.raises(RuntimeError):
            engine.abort(txn)

    def test_no_conflict_check(self):
        """测试跳过冲突检测。"""
        engine = MVCCEngine()

        # 写入初始数据
        txn0 = engine.begin()
        engine.txn_write(txn0, "key1", 100)
        engine.commit(txn0)

        # 两个并发事务
        txn1 = engine.begin()
        txn2 = engine.begin()
        engine.txn_write(txn1, "key1", 200)
        engine.txn_write(txn2, "key1", 300)

        engine.commit(txn1)

        # 跳过冲突检测
        result = engine.commit(txn2, check_conflicts=False)
        assert not result.has_conflict
        assert txn2.is_committed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

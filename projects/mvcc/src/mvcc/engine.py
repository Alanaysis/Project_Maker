"""
MVCC 引擎 - 事务存储引擎的顶层接口。

MVCCEngine 整合了所有组件:
    - TransactionManager: 事务生命周期管理
    - Storage: 版本链存储
    - ConflictDetector: 冲突检测
    - GarbageCollector: 垃圾回收

使用方式:
    engine = MVCCEngine()

    # 事务 1: 写入数据
    txn1 = engine.begin()
    engine.txn_write(txn1, "account_a", 1000)
    engine.txn_write(txn1, "account_b", 2000)
    engine.commit(txn1)

    # 事务 2: 读取数据（快照隔离）
    txn2 = engine.begin()
    value = engine.txn_read(txn2, "account_a")  # 返回 1000
    engine.commit(txn2)

    # 并发冲突示例
    txn3 = engine.begin()
    txn4 = engine.begin()
    engine.txn_write(txn3, "account_a", 900)
    engine.txn_write(txn4, "account_a", 800)
    engine.commit(txn3)   # 成功
    engine.commit(txn4)   # 冲突！txn4 被中止

设计要点:
    1. 提供高级事务接口，隐藏底层实现细节
    2. 支持自动冲突检测和事务中止
    3. 支持手动和自动垃圾回收
    4. 线程安全设计（通过锁保护共享状态）
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

from .transaction import Transaction, TransactionManager, TxnStatus
from .snapshot import Snapshot
from .storage import Storage
from .conflict import ConflictDetector, ConflictResult
from .gc import GarbageCollector
from .version import VersionChain


class MVCCEngine:
    """
    MVCC 事务存储引擎。

    这是 MVCC 系统的主入口，提供完整的事务操作接口。

    属性:
        txn_manager:    事务管理器
        storage:        存储引擎
        conflict:       冲突检测器
        gc:             垃圾回收器
        gc_threshold:   GC 触发阈值
    """

    def __init__(self, gc_threshold: int = 10):
        self.txn_manager = TransactionManager()
        self.storage = Storage()
        self.conflict = ConflictDetector()
        self.gc = GarbageCollector(gc_threshold=gc_threshold)

    # ==================== 事务操作 ====================

    def begin(self) -> Transaction:
        """
        开始一个新事务。

        创建一个快照并返回新事务。该事务将看到快照时刻的一致性数据。

        Returns:
            新的事务对象
        """
        # 创建快照：捕获当前时间戳和活跃事务集合
        active_txns = self.txn_manager.get_active_txn_ids()
        snapshot_ts = self.txn_manager.advance_timestamp()
        snapshot = Snapshot(snapshot_ts, active_txns)

        return self.txn_manager.begin(snapshot)

    def commit(self, txn: Transaction, check_conflicts: bool = True) -> ConflictResult:
        """
        提交事务。

        流程:
            1. 检查事务状态
            2. 执行冲突检测（可选）
            3. 获取提交时间戳
            4. 将写缓冲应用到主存储
            5. 提交事务

        Args:
            txn: 要提交的事务
            check_conflicts: 是否执行冲突检测

        Returns:
            冲突检测结果（如果无冲突则 has_conflict=False）

        Raises:
            RuntimeError: 事务不在活跃状态
        """
        if not txn.is_active:
            raise RuntimeError(
                f"Transaction {txn.txn_id} is not active "
                f"(status: {txn.status.name})"
            )

        # 冲突检测（有读操作时检测读写冲突，有写操作时检测写写冲突）
        if check_conflicts and (txn.write_buffer or txn.delete_set or txn.read_set):
            result = self.conflict.check_all(
                txn,
                self.storage.data,
                self.txn_manager.get_committed_txns(),
            )
            if result.has_conflict:
                self.txn_manager.abort(txn)
                return result

        # 获取提交时间戳并应用写入
        commit_ts = self.txn_manager.advance_timestamp()
        self.storage.apply_commit(txn, commit_ts)
        self.txn_manager.commit(txn, commit_ts)

        return ConflictResult(
            has_conflict=False,
            conflict_type="none",
            conflicting_keys=set(),
            message="Transaction committed successfully.",
        )

    def abort(self, txn: Transaction) -> None:
        """
        中止事务。

        清理事务的写缓冲和删除集合。

        Args:
            txn: 要中止的事务
        """
        if not txn.is_active:
            raise RuntimeError(
                f"Transaction {txn.txn_id} is not active "
                f"(status: {txn.status.name})"
            )
        self.txn_manager.abort(txn)

    # ==================== 数据操作 ====================

    def txn_read(self, txn: Transaction, key: str) -> Optional[Any]:
        """
        事务读取数据。

        基于事务的快照读取 key 的可见版本。
        先检查写缓冲，再查找版本链。

        Args:
            txn: 当前事务
            key: 要读取的键

        Returns:
            读取的值，不存在则返回 None
        """
        return self.storage.read(key, txn)

    def txn_write(self, txn: Transaction, key: str, value: Any) -> None:
        """
        事务写入数据。

        写入先缓存到事务的写缓冲中，提交时才应用到主存储。

        Args:
            txn: 当前事务
            key: 要写入的键
            value: 要写入的值
        """
        self.storage.write(key, value, txn)

    def txn_delete(self, txn: Transaction, key: str) -> bool:
        """
        事务删除数据。

        删除先标记到事务的删除集合中，提交时才生效。

        Args:
            txn: 当前事务
            key: 要删除的键

        Returns:
            是否成功标记删除
        """
        return self.storage.delete(key, txn)

    # ==================== 批量操作 ====================

    def txn_read_batch(
        self, txn: Transaction, keys: List[str]
    ) -> Dict[str, Optional[Any]]:
        """批量读取多个 key。"""
        return {key: self.storage.read(key, txn) for key in keys}

    def txn_write_batch(
        self, txn: Transaction, kvs: Dict[str, Any]
    ) -> None:
        """批量写入多个 key-value 对。"""
        for key, value in kvs.items():
            self.storage.write(key, value, txn)

    # ==================== 垃圾回收 ====================

    def run_gc(self, max_keys: int = 0) -> Tuple[int, int]:
        """
        执行垃圾回收。

        Args:
            max_keys: 最多处理的 key 数量（0 = 全部）

        Returns:
            (清理的版本数, 处理的 key 数)
        """
        return self.gc.collect(self.storage.data, self.txn_manager, max_keys)

    # ==================== 查询接口 ====================

    def get_version_chain(self, key: str) -> Optional[VersionChain]:
        """获取 key 的版本链（调试用）。"""
        return self.storage.get_version_chain(key)

    def get_stats(self) -> Dict[str, Any]:
        """
        获取引擎统计信息。

        Returns:
            包含各项统计数据的字典
        """
        return {
            "storage_keys": len(self.storage),
            "active_txns": self.txn_manager.active_count,
            "committed_txns": self.txn_manager.committed_count,
            "current_timestamp": self.txn_manager.get_timestamp(),
            "gc": self.gc.stats,
        }

    def __repr__(self) -> str:
        return (
            f"MVCCEngine(keys={len(self.storage)}, "
            f"active={self.txn_manager.active_count}, "
            f"ts={self.txn_manager.get_timestamp()})"
        )

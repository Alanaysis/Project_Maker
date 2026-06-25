"""
冲突检测器 - MVCC 并发控制的核心组件。

冲突类型:
    1. 写写冲突 (Write-Write Conflict):
       两个并发事务同时写入同一个 key。
       检测时机: 事务提交时
       处理策略: First-Writer-Wins (FWW) - 先提交者获胜

    2. 读写冲突 (Read-Write Conflict / Write Skew):
       一个事务读取的数据被另一个并发事务修改。
       检测时机: 事务提交时
       处理策略: 检查读集合是否被并发提交的事务修改

设计要点:
    1. 采用乐观并发控制(OCC)策略
    2. 冲突检测在提交阶段进行，而非操作阶段
    3. 写写冲突使用 First-Writer-Wins 策略
    4. 读写冲突通过检查读集合的版本变化来检测
"""

from __future__ import annotations
from typing import Dict, Set
from dataclasses import dataclass

from .transaction import Transaction
from .version import VersionChain


@dataclass
class ConflictResult:
    """冲突检测结果。"""
    has_conflict: bool
    conflict_type: str  # "write_write", "read_write", "none"
    conflicting_keys: Set[str]
    message: str


class ConflictDetector:
    """
    冲突检测器 - 在事务提交时检测并发冲突。

    使用方法:
        detector = ConflictDetector()
        result = detector.check_conflict(txn, storage, committed_txns)
        if result.has_conflict:
            # 中止事务
            txn.abort()
    """

    def check_write_write(
        self,
        txn: Transaction,
        version_chains: Dict[str, VersionChain],
        committed_txns: Dict[int, Transaction],
    ) -> ConflictResult:
        """
        检测写写冲突。

        规则: 如果在本事务活跃期间，有其他已提交事务写入了同一个 key，
        则存在写写冲突。

        Args:
            txn: 要检测的事务
            version_chains: 存储中所有 key 的版本链
            committed_txns: 已提交的事务集合

        Returns:
            冲突检测结果
        """
        conflicting = set()

        for key in txn.write_buffer:
            chain = version_chains.get(key)
            if chain is None or chain.head is None:
                continue

            # 检查版本链头部是否有并发事务的写入
            current = chain.head
            while current is not None:
                # 跳过自己创建的版本
                if current.create_txn_id == txn.txn_id:
                    current = current.prev
                    continue

                # 检查是否有在本事务开始之后提交的版本
                other_txn = committed_txns.get(current.create_txn_id)
                if (other_txn is not None
                        and other_txn.commit_ts is not None
                        and other_txn.commit_ts > txn.start_ts):
                    conflicting.add(key)
                    break

                # 只检查最新的非自身版本
                break

        if conflicting:
            return ConflictResult(
                has_conflict=True,
                conflict_type="write_write",
                conflicting_keys=conflicting,
                message=(
                    f"Write-write conflict on keys: {conflicting}. "
                    f"Another transaction committed writes after "
                    f"txn {txn.txn_id} started."
                ),
            )

        return ConflictResult(
            has_conflict=False,
            conflict_type="none",
            conflicting_keys=set(),
            message="No write-write conflict.",
        )

    def check_read_write(
        self,
        txn: Transaction,
        version_chains: Dict[str, VersionChain],
        committed_txns: Dict[int, Transaction],
    ) -> ConflictResult:
        """
        检测读写冲突（Write Skew 检测）。

        规则: 如果在本事务活跃期间，有其他已提交事务修改了本事务读取过的 key，
        则存在读写冲突。

        这是 Snapshot Isolation 下经典的 Write Skew 问题。
        例如: 两个事务同时读取账户余额，然后各自扣除金额，
        可能导致余额变为负数。

        Args:
            txn: 要检测的事务
            version_chains: 存储中所有 key 的版本链
            committed_txns: 已提交的事务集合

        Returns:
            冲突检测结果
        """
        conflicting = set()

        for key in txn.read_set:
            # 跳过自己写入的 key（自依赖不算冲突）
            if key in txn.write_buffer or key in txn.delete_set:
                continue

            chain = version_chains.get(key)
            if chain is None or chain.head is None:
                continue

            # 检查是否有在本事务开始之后提交的新版本
            current = chain.head
            while current is not None:
                if current.create_txn_id == txn.txn_id:
                    current = current.prev
                    continue

                other_txn = committed_txns.get(current.create_txn_id)
                if (other_txn is not None
                        and other_txn.commit_ts is not None
                        and other_txn.commit_ts > txn.start_ts):
                    conflicting.add(key)
                    break

                break

        if conflicting:
            return ConflictResult(
                has_conflict=True,
                conflict_type="read_write",
                conflicting_keys=conflicting,
                message=(
                    f"Read-write conflict on keys: {conflicting}. "
                    f"Data read by txn {txn.txn_id} was modified by "
                    f"another committed transaction."
                ),
            )

        return ConflictResult(
            has_conflict=False,
            conflict_type="none",
            conflicting_keys=set(),
            message="No read-write conflict.",
        )

    def check_all(
        self,
        txn: Transaction,
        version_chains: Dict[str, VersionChain],
        committed_txns: Dict[int, Transaction],
    ) -> ConflictResult:
        """
        执行所有冲突检测。

        优先检测写写冲突，其次检测读写冲突。

        Args:
            txn: 要检测的事务
            version_chains: 存储中所有 key 的版本链
            committed_txns: 已提交的事务集合

        Returns:
            冲突检测结果（第一个检测到的冲突）
        """
        # 写写冲突优先
        ww_result = self.check_write_write(
            txn, version_chains, committed_txns
        )
        if ww_result.has_conflict:
            return ww_result

        # 读写冲突
        rw_result = self.check_read_write(
            txn, version_chains, committed_txns
        )
        return rw_result

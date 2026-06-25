"""
垃圾回收器 - 清理不再需要的旧版本数据。

GC 策略:
    1. 安全点 (Safe Point) 计算:
       安全点 = 所有活跃事务中最早的开始时间戳
       安全点之前的版本如果不再被任何事务引用，可以安全清理

    2. 清理规则:
       - 保留最新版本（不管是否可见）
       - 保留安全点之后创建的版本
       - 清理安全点之前创建且已被删除的旧版本
       - 每条版本链至少保留 1 个版本

    3. 触发条件:
       - 定时触发（基于时间间隔）
       - 版本链过长触发（基于版本数量阈值）
       - 手动触发

设计要点:
    1. GC 是异步的，不阻塞正常的读写操作
    2. 安全点的计算考虑所有活跃事务，确保不会误删
    3. 支持增量 GC，每次只清理部分版本链
"""

from __future__ import annotations
from typing import Dict, List, Tuple

from .transaction import Transaction, TransactionManager
from .version import VersionChain


class GarbageCollector:
    """
    垃圾回收器 - 清理不可见的旧版本。

    属性:
        gc_threshold: 触发 GC 的版本链长度阈值
        total_collected: 累计清理的版本数量
        gc_count: GC 执行次数
    """

    def __init__(self, gc_threshold: int = 10):
        self.gc_threshold = gc_threshold
        self.total_collected: int = 0
        self.gc_count: int = 0

    def compute_safe_point(
        self, txn_manager: TransactionManager
    ) -> int:
        """
        计算 GC 安全点。

        安全点 = 所有活跃事务中最早的开始时间戳。
        如果没有活跃事务，安全点 = 当前全局时间戳。

        Args:
            txn_manager: 事务管理器

        Returns:
            安全点时间戳
        """
        active_txns = txn_manager.get_active_txns()

        if not active_txns:
            # 没有活跃事务，安全点为当前时间戳
            return txn_manager.get_timestamp()

        # 取所有活跃事务中最早的开始时间戳
        min_ts = min(txn.start_ts for txn in active_txns.values())
        return min_ts

    def collect(
        self,
        version_chains: Dict[str, VersionChain],
        txn_manager: TransactionManager,
        max_keys: int = 0,
    ) -> Tuple[int, int]:
        """
        执行垃圾回收。

        遍历所有版本链，清理不可见的旧版本。

        Args:
            version_chains: 存储中所有 key 的版本链
            txn_manager: 事务管理器
            max_keys: 最多处理的 key 数量（0 = 全部）

        Returns:
            (清理的版本数, 处理的 key 数)
        """
        safe_point = self.compute_safe_point(txn_manager)
        committed_ids = txn_manager.get_committed_txn_ids()

        total_collected = 0
        keys_processed = 0

        # 收集需要清理的 key（版本链过长的优先清理）
        candidates: List[Tuple[str, VersionChain, int]] = []
        for key, chain in version_chains.items():
            if chain.length >= self.gc_threshold:
                candidates.append((key, chain, chain.length))

        # 按版本链长度降序排列
        candidates.sort(key=lambda x: x[2], reverse=True)

        # 限制处理数量
        if max_keys > 0:
            candidates = candidates[:max_keys]

        # 执行清理
        for key, chain, _ in candidates:
            collected = chain.gc(safe_point, committed_ids)
            total_collected += collected
            keys_processed += 1

        self.total_collected += total_collected
        self.gc_count += 1

        return total_collected, keys_processed

    def collect_single(
        self,
        chain: VersionChain,
        txn_manager: TransactionManager,
    ) -> int:
        """
        对单条版本链执行垃圾回收。

        Args:
            chain: 版本链
            txn_manager: 事务管理器

        Returns:
            清理的版本数
        """
        safe_point = self.compute_safe_point(txn_manager)
        committed_ids = txn_manager.get_committed_txn_ids()

        collected = chain.gc(safe_point, committed_ids)
        self.total_collected += collected
        return collected

    def needs_gc(self, chain: VersionChain) -> bool:
        """检查版本链是否需要 GC。"""
        return chain.length >= self.gc_threshold

    @property
    def stats(self) -> Dict[str, int]:
        """获取 GC 统计信息。"""
        return {
            "gc_count": self.gc_count,
            "total_collected": self.total_collected,
            "gc_threshold": self.gc_threshold,
        }

    def __repr__(self) -> str:
        return (
            f"GarbageCollector(threshold={self.gc_threshold}, "
            f"collected={self.total_collected}, "
            f"runs={self.gc_count})"
        )

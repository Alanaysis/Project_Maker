"""
快照隔离 - MVCC 的核心隔离机制。

快照隔离保证每个事务看到数据库在某个时间点的一致性视图。

快照包含:
    - timestamp: 快照时间戳（事务开始时的全局时间戳）
    - active_txns: 快照时刻活跃的事务 ID 集合

可见性判断:
    一个版本对快照可见，当且仅当:
    1. 创建该版本的事务已提交，且提交时间 <= 快照时间戳
    2. 创建该版本的事务不在快照的活跃事务集合中
    3. 该版本未被已提交事务在快照时间戳之前删除

设计要点:
    1. 快照是不可变的，创建后不会改变
    2. 快照捕获了创建时刻的事务状态，用于后续所有读操作
    3. 通过 active_txns 过滤掉"未来"的提交，实现真正的快照语义
"""

from __future__ import annotations
from typing import Set


class Snapshot:
    """
    数据库快照 - 某个时间点的一致性视图。

    快照是 MVCC 读操作的基础。每个事务在开始时获取一个快照，
    该事务的所有读操作都基于这个快照进行。

    属性:
        timestamp:   快照时间戳
        active_txns: 快照时刻活跃的事务 ID 集合
    """

    __slots__ = ("timestamp", "active_txns")

    def __init__(self, timestamp: int, active_txns: Set[int]):
        self.timestamp = timestamp
        self.active_txns = frozenset(active_txns)

    def is_visible(
        self,
        create_txn_id: int,
        create_ts: int,
        delete_txn_id: int | None = None,
        delete_ts: int | None = None,
    ) -> bool:
        """
        判断一个版本是否对当前快照可见。

        Args:
            create_txn_id: 创建版本的事务 ID
            create_ts: 创建时间戳
            delete_txn_id: 删除版本的事务 ID（None 表示未删除）
            delete_ts: 删除时间戳（None 表示未删除）

        Returns:
            该版本是否可见
        """
        # 创建事务在快照时刻仍活跃 -> 不可见
        if create_txn_id in self.active_txns:
            return False

        # 创建时间 > 快照时间 -> 不可见
        if create_ts > self.timestamp:
            return False

        # 检查删除状态
        if delete_txn_id is not None:
            # 删除事务在快照时刻仍活跃 -> 删除未生效，版本可见
            if delete_txn_id in self.active_txns:
                return True
            # 删除时间 <= 快照时间 -> 已删除，不可见
            if delete_ts is not None and delete_ts <= self.timestamp:
                return False

        return True

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Snapshot):
            return NotImplemented
        return (self.timestamp == other.timestamp
                and self.active_txns == other.active_txns)

    def __hash__(self) -> int:
        return hash((self.timestamp, self.active_txns))

    def __repr__(self) -> str:
        return (
            f"Snapshot(ts={self.timestamp}, "
            f"active_txns={set(self.active_txns)})"
        )

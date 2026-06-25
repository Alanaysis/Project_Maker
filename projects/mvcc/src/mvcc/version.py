"""
版本链管理 - Multi-Version Concurrency Control 的核心数据结构。

每个数据记录维护一条版本链(Version Chain)，记录该数据的所有历史版本。
版本链按时间倒序排列，最新的版本在链头。

版本结构:
    Version
    ├── data: dict          -- 版本数据内容
    ├── create_txn_id: int  -- 创建该版本的事务 ID
    ├── create_ts: int      -- 创建时间戳
    ├── delete_txn_id: int  -- 删除该版本的事务 ID（None 表示未删除）
    ├── delete_ts: int      -- 删除时间戳（None 表示未删除）
    └── prev: Version       -- 指向前一个版本的指针

设计要点:
    1. 版本链采用单链表结构，新版本插入链头 O(1)
    2. 每个版本记录创建/删除信息，支持快照读取
    3. 版本链支持 GC 清理不可见的旧版本
"""

from __future__ import annotations
from typing import Any, Dict, Optional


class Version:
    """数据版本 - 版本链中的一个节点。"""

    __slots__ = ("data", "create_txn_id", "create_ts",
                 "delete_txn_id", "delete_ts", "prev")

    def __init__(
        self,
        data: Dict[str, Any],
        create_txn_id: int,
        create_ts: int,
        delete_txn_id: Optional[int] = None,
        delete_ts: Optional[int] = None,
        prev: Optional[Version] = None,
    ):
        self.data = data
        self.create_txn_id = create_txn_id
        self.create_ts = create_ts
        self.delete_txn_id = delete_txn_id
        self.delete_ts = delete_ts
        self.prev = prev

    @property
    def is_deleted(self) -> bool:
        """该版本是否已被标记删除。"""
        return self.delete_txn_id is not None

    def mark_deleted(self, txn_id: int, ts: int) -> None:
        """标记该版本被删除。"""
        self.delete_txn_id = txn_id
        self.delete_ts = ts

    def __repr__(self) -> str:
        status = "DELETED" if self.is_deleted else "ACTIVE"
        return (
            f"Version(data={self.data}, "
            f"create=(txn={self.create_txn_id}, ts={self.create_ts}), "
            f"delete=(txn={self.delete_txn_id}, ts={self.delete_ts}), "
            f"status={status})"
        )


class VersionChain:
    """
    版本链 - 管理单条数据记录的所有历史版本。

    版本链按创建时间倒序排列（最新版本在链头），
    支持按快照时间戳查找可见版本。

    典型操作:
        - append(): 追加新版本到链头
        - find_visible(): 根据快照查找可见版本
        - gc(): 清理不可见的旧版本
    """

    def __init__(self):
        self.head: Optional[Version] = None
        self._length: int = 0

    @property
    def length(self) -> int:
        """版本链长度。"""
        return self._length

    def append(self, version: Version) -> None:
        """将新版本插入链头（最新版本在前）。"""
        version.prev = self.head
        self.head = version
        self._length += 1

    def find_visible(
        self,
        snapshot_ts: int,
        active_txns: set,
        read_own: bool = False,
        txn_id: Optional[int] = None,
    ) -> Optional[Version]:
        """
        根据快照查找可见版本。

        可见性规则:
        1. 版本的创建事务必须已提交，且创建时间 <= 快照时间
        2. 版本不能被在快照之前已提交的事务删除
        3. 如果 read_own=True，可以读取自己事务创建的未提交版本

        Args:
            snapshot_ts: 快照时间戳
            active_txns: 快照时刻活跃的事务 ID 集合
            read_own: 是否允许读取自己事务的未提交写入
            txn_id: 当前事务 ID（read_own=True 时使用）

        Returns:
            可见的版本，如果不可见则返回 None
        """
        current = self.head
        while current is not None:
            # 规则 3: 读取自己的写入
            if read_own and txn_id is not None and current.create_txn_id == txn_id:
                if current.is_deleted and current.delete_txn_id == txn_id:
                    # 自己创建又自己删除的版本不可见
                    current = current.prev
                    continue
                return current

            # 规则 1: 创建事务已提交且创建时间 <= 快照时间
            if (current.create_txn_id not in active_txns
                    and current.create_ts <= snapshot_ts):
                # 规则 2: 检查删除状态
                if current.is_deleted:
                    # 删除事务已提交且删除时间 <= 快照时间
                    if (current.delete_txn_id not in active_txns
                            and current.delete_ts <= snapshot_ts):
                        # 在快照之前已删除，不可见
                        current = current.prev
                        continue
                return current

            current = current.prev

        return None

    def find_latest_committed(self) -> Optional[Version]:
        """查找最新已提交的版本（用于写冲突检测）。"""
        current = self.head
        while current is not None:
            if not current.is_deleted:
                return current
            current = current.prev
        return None

    def gc(
        self,
        min_active_ts: int,
        committed_txns: set,
    ) -> int:
        """
        垃圾回收 - 清理不可见的旧版本。

        清理策略:
        - 保留最新版本（不管是否可见）
        - 保留所有活跃事务可能看到的版本
        - 清理创建时间 < min_active_ts 且已被删除的旧版本

        Args:
            min_active_ts: 最早活跃事务的时间戳（安全点）
            committed_txns: 已提交事务 ID 集合

        Returns:
            清理的版本数量
        """
        if self.head is None:
            return 0

        collected = 0
        # 至少保留两个版本：最新版本 + 一个安全版本
        current = self.head
        prev_node = None

        while current is not None:
            next_node = current.prev

            # 保留最新版本
            if current is self.head:
                prev_node = current
                current = next_node
                continue

            # 判断是否可以清理
            can_collect = (
                # 创建时间在安全点之前
                current.create_ts < min_active_ts
                # 该版本已被标记删除
                and current.is_deleted
                # 删除事务已提交
                and current.delete_txn_id in committed_txns
            )

            if can_collect and next_node is not None:
                # 断开链接，清理该版本
                if prev_node is not None:
                    prev_node.prev = next_node
                current.prev = None
                collected += 1
                current = next_node
            else:
                prev_node = current
                current = next_node

        self._length -= collected
        return collected

    def to_list(self) -> list:
        """将版本链转换为列表（调试用）。"""
        result = []
        current = self.head
        while current is not None:
            result.append(current)
            current = current.prev
        return result

    def __len__(self) -> int:
        return self._length

    def __repr__(self) -> str:
        return f"VersionChain(length={self._length})"

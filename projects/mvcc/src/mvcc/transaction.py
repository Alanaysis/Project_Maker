"""
事务管理器 - MVCC 事务的生命周期管理。

事务状态机:
    ACTIVE  ──commit()──>  COMMITTED
    ACTIVE  ──abort()───>  ABORTED

每个事务维护:
    - 读集合 (read_set): 事务读取过的 key 集合
    - 写缓冲 (write_buffer): 事务写入的 key -> value 映射
    - 删除集合 (delete_set): 事务删除的 key 集合
    - 快照 (snapshot): 事务开始时的数据库快照

设计要点:
    1. 事务 ID 全局唯一，由 TransactionManager 统一分配
    2. 事务采用乐观并发控制：写入先缓存，提交时才检测冲突
    3. 支持事务隔离级别: Snapshot Isolation (SI)
"""

from __future__ import annotations
from enum import Enum, auto
from typing import Any, Dict, Optional, Set
from .snapshot import Snapshot


class TxnStatus(Enum):
    """事务状态枚举。"""
    ACTIVE = auto()      # 活跃中
    COMMITTED = auto()   # 已提交
    ABORTED = auto()     # 已中止


class Transaction:
    """
    事务对象 - 代表一个 MVCC 事务。

    属性:
        txn_id:         事务唯一 ID
        start_ts:       事务开始时间戳
        status:         事务状态
        snapshot:       事务快照（开始时的数据库状态）
        read_set:       读集合（用于冲突检测）
        write_buffer:   写缓冲（暂存写入，提交时批量应用）
        delete_set:     删除集合
    """

    def __init__(self, txn_id: int, start_ts: int, snapshot: Snapshot):
        self.txn_id = txn_id
        self.start_ts = start_ts
        self.status = TxnStatus.ACTIVE
        self.snapshot = snapshot
        self.read_set: Set[str] = set()
        self.write_buffer: Dict[str, Any] = {}
        self.delete_set: Set[str] = set()

    def add_read(self, key: str) -> None:
        """记录读操作。"""
        self.read_set.add(key)

    def add_write(self, key: str, value: Any) -> None:
        """记录写操作到写缓冲。"""
        self.write_buffer[key] = value
        # 如果之前标记过删除，取消删除
        self.delete_set.discard(key)

    def add_delete(self, key: str) -> None:
        """记录删除操作。"""
        self.delete_set.add(key)
        # 如果之前有写缓冲，清除
        self.write_buffer.pop(key, None)

    def get_write(self, key: str) -> Optional[Any]:
        """从写缓冲中获取值。"""
        return self.write_buffer.get(key)

    def is_write_buffered(self, key: str) -> bool:
        """检查 key 是否在写缓冲中。"""
        return key in self.write_buffer or key in self.delete_set

    def commit(self, commit_ts: int) -> None:
        """提交事务。"""
        if self.status != TxnStatus.ACTIVE:
            raise RuntimeError(
                f"Cannot commit transaction {self.txn_id}: "
                f"status is {self.status.name}"
            )
        self.status = TxnStatus.COMMITTED
        self._commit_ts = commit_ts

    def abort(self) -> None:
        """中止事务。"""
        if self.status != TxnStatus.ACTIVE:
            raise RuntimeError(
                f"Cannot abort transaction {self.txn_id}: "
                f"status is {self.status.name}"
            )
        self.status = TxnStatus.ABORTED
        # 清理写缓冲
        self.write_buffer.clear()
        self.delete_set.clear()

    @property
    def commit_ts(self) -> Optional[int]:
        """获取提交时间戳（仅已提交事务有值）。"""
        return getattr(self, "_commit_ts", None)

    @property
    def is_active(self) -> bool:
        return self.status == TxnStatus.ACTIVE

    @property
    def is_committed(self) -> bool:
        return self.status == TxnStatus.COMMITTED

    @property
    def is_aborted(self) -> bool:
        return self.status == TxnStatus.ABORTED

    def __repr__(self) -> str:
        return (
            f"Transaction(id={self.txn_id}, "
            f"start_ts={self.start_ts}, "
            f"status={self.status.name}, "
            f"reads={len(self.read_set)}, "
            f"writes={len(self.write_buffer)})"
        )


class TransactionManager:
    """
    事务管理器 - 负责事务的创建、提交、中止和状态查询。

    职责:
        1. 分配全局唯一事务 ID
        2. 维护全局时间戳
        3. 管理活跃事务集合
        4. 查询事务状态
    """

    def __init__(self):
        self._next_txn_id: int = 1
        self._timestamp: int = 0
        self._active_txns: Dict[int, Transaction] = {}
        self._committed_txns: Dict[int, Transaction] = {}
        self._aborted_txns: Dict[int, Transaction] = {}

    def begin(self, snapshot: Snapshot) -> Transaction:
        """
        开始一个新事务。

        Args:
            snapshot: 事务开始时的数据库快照

        Returns:
            新的事务对象
        """
        txn_id = self._next_txn_id
        self._next_txn_id += 1

        start_ts = self.advance_timestamp()
        txn = Transaction(txn_id, start_ts, snapshot)
        self._active_txns[txn_id] = txn
        return txn

    def commit(self, txn: Transaction, commit_ts: int) -> None:
        """提交事务。"""
        txn.commit(commit_ts)
        self._active_txns.pop(txn.txn_id, None)
        self._committed_txns[txn.txn_id] = txn

    def abort(self, txn: Transaction) -> None:
        """中止事务。"""
        txn.abort()
        self._active_txns.pop(txn.txn_id, None)
        self._aborted_txns[txn.txn_id] = txn

    def advance_timestamp(self) -> int:
        """推进全局时间戳并返回新值。"""
        self._timestamp += 1
        return self._timestamp

    def get_timestamp(self) -> int:
        """获取当前时间戳（不推进）。"""
        return self._timestamp

    def get_active_txn_ids(self) -> set:
        """获取所有活跃事务的 ID 集合。"""
        return set(self._active_txns.keys())

    def get_active_txns(self) -> Dict[int, Transaction]:
        """获取所有活跃事务。"""
        return dict(self._active_txns)

    def get_committed_txns(self) -> Dict[int, Transaction]:
        """获取所有已提交事务。"""
        return dict(self._committed_txns)

    def get_committed_txn_ids(self) -> set:
        """获取所有已提交事务的 ID 集合。"""
        return set(self._committed_txns.keys())

    def get_txn(self, txn_id: int) -> Optional[Transaction]:
        """根据 ID 获取事务。"""
        if txn_id in self._active_txns:
            return self._active_txns[txn_id]
        if txn_id in self._committed_txns:
            return self._committed_txns[txn_id]
        if txn_id in self._aborted_txns:
            return self._aborted_txns[txn_id]
        return None

    @property
    def active_count(self) -> int:
        """活跃事务数量。"""
        return len(self._active_txns)

    @property
    def committed_count(self) -> int:
        """已提交事务数量。"""
        return len(self._committed_txns)

    def __repr__(self) -> str:
        return (
            f"TransactionManager(ts={self._timestamp}, "
            f"active={self.active_count}, "
            f"committed={self.committed_count})"
        )

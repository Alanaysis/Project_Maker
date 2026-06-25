"""Acceptor 恢复器"""

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ProposalID:
    """提案ID"""
    number: int
    node_id: str


@dataclass
class AcceptorState:
    """Acceptor 状态快照"""
    promised_id: Optional[ProposalID] = None
    accepted_id: Optional[ProposalID] = None
    accepted_value: Any = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class LogEntry:
    """恢复日志条目"""
    timestamp: float
    operation: str
    data: Any


class RecoveryLog:
    """恢复日志"""

    def __init__(self):
        self._lock = threading.RLock()
        self._entries: List[LogEntry] = []

    def append(self, entry: LogEntry) -> None:
        """追加日志条目"""
        with self._lock:
            self._entries.append(entry)

    def get_entries(self, after: float) -> List[LogEntry]:
        """获取指定时间之后的日志条目"""
        with self._lock:
            return [e for e in self._entries if e.timestamp > after]

    def clear(self) -> None:
        """清空日志"""
        with self._lock:
            self._entries.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)


class AcceptorRecovery:
    """Acceptor 恢复器

    负责 Acceptor 的状态快照和故障恢复。
    """

    def __init__(self, acceptor_id: str):
        self._acceptor_id = acceptor_id
        self._lock = threading.Lock()
        self._snapshot: Optional[AcceptorState] = None
        self._log = RecoveryLog()

        # 配置
        self._snapshot_interval = 60.0  # 60s
        self._max_log_size = 1000

        # 回调
        self._on_recovery_start: Optional[Callable[[str], None]] = None
        self._on_recovery_end: Optional[Callable[[str, bool], None]] = None

    def save_snapshot(self, state: AcceptorState) -> None:
        """保存快照"""
        with self._lock:
            self._snapshot = state
            logger.info(f"[Recovery {self._acceptor_id}] Saved snapshot")

    def append_log(self, operation: str, data: Any) -> None:
        """追加日志"""
        entry = LogEntry(
            timestamp=time.time(),
            operation=operation,
            data=data,
        )
        self._log.append(entry)

    def recover(self) -> Optional[AcceptorState]:
        """恢复状态"""
        with self._lock:
            logger.info(f"[Recovery {self._acceptor_id}] Starting recovery")

            if self._on_recovery_start:
                self._on_recovery_start(self._acceptor_id)

            # 1. 从快照恢复
            if self._snapshot is None:
                logger.info(f"[Recovery {self._acceptor_id}] No snapshot found, starting fresh")
                self._notify_recovery_end(False)
                return None

            state = AcceptorState(
                promised_id=self._snapshot.promised_id,
                accepted_id=self._snapshot.accepted_id,
                accepted_value=self._snapshot.accepted_value,
                timestamp=self._snapshot.timestamp,
            )

            # 2. 回放日志
            entries = self._log.get_entries(self._snapshot.timestamp)
            logger.info(f"[Recovery {self._acceptor_id}] Replaying {len(entries)} log entries")

            for entry in entries:
                self._apply_entry(state, entry)

            logger.info(f"[Recovery {self._acceptor_id}] Recovery complete")
            self._notify_recovery_end(True)

            return state

    def _apply_entry(self, state: AcceptorState, entry: LogEntry) -> None:
        """应用日志条目"""
        if entry.operation == "promise":
            if isinstance(entry.data, ProposalID):
                state.promised_id = entry.data
        elif entry.operation == "accept":
            if isinstance(entry.data, dict):
                state.accepted_id = entry.data.get('proposal_id')
                state.accepted_value = entry.data.get('value')

    def _notify_recovery_end(self, success: bool) -> None:
        """触发恢复结束回调"""
        if self._on_recovery_end:
            self._on_recovery_end(self._acceptor_id, success)

    @property
    def snapshot(self) -> Optional[AcceptorState]:
        """获取快照"""
        return self._snapshot

    @property
    def log(self) -> RecoveryLog:
        """获取日志"""
        return self._log

    def set_on_recovery_start(self, callback: Callable[[str], None]) -> None:
        """设置恢复开始回调"""
        self._on_recovery_start = callback

    def set_on_recovery_end(self, callback: Callable[[str, bool], None]) -> None:
        """设置恢复结束回调"""
        self._on_recovery_end = callback

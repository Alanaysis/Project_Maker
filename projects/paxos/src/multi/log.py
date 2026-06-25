"""Paxos 日志结构"""

import logging
import threading
from typing import Dict, List, Optional

from .types import LogEntry

logger = logging.getLogger(__name__)


class PaxosLog:
    """Paxos 日志

    管理日志条目的追加、查询和提交。
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._entries: Dict[int, LogEntry] = {}
        self._commit_index = 0

    def append(self, entry: LogEntry) -> None:
        """追加日志条目"""
        with self._lock:
            self._entries[entry.slot_id] = entry
            logger.debug(f"[Log] Appended entry at slot {entry.slot_id}")

    def get(self, slot_id: int) -> Optional[LogEntry]:
        """获取日志条目"""
        with self._lock:
            return self._entries.get(slot_id)

    def commit(self, slot_id: int) -> None:
        """提交日志条目"""
        with self._lock:
            if slot_id in self._entries:
                self._entries[slot_id].committed = True
                if slot_id > self._commit_index:
                    self._commit_index = slot_id
                logger.debug(f"[Log] Committed entry at slot {slot_id}")

    @property
    def commit_index(self) -> int:
        """获取提交索引"""
        with self._lock:
            return self._commit_index

    def get_entries(self, start: int, end: int) -> List[LogEntry]:
        """获取指定范围的日志条目"""
        with self._lock:
            return [self._entries[i] for i in range(start, end + 1)
                    if i in self._entries]

    @property
    def last_index(self) -> int:
        """获取最后的日志索引"""
        with self._lock:
            if not self._entries:
                return 0
            return max(self._entries.keys())

    @property
    def last_term(self) -> int:
        """获取最后的日志任期"""
        with self._lock:
            if not self._entries:
                return 0
            return max(e.proposal_id.number for e in self._entries.values())

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)

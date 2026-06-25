"""Multi Paxos 类型定义"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Optional
import time


@dataclass(order=True)
class ProposalID:
    """提案ID"""
    number: int
    node_id: str = field(compare=False)

    def __str__(self) -> str:
        return f"{self.number}-{self.node_id}"

    def is_greater_than(self, other: 'ProposalID') -> bool:
        """比较提案ID大小"""
        if self.number != other.number:
            return self.number > other.number
        return self.node_id > other.node_id


class LeaderState(IntEnum):
    """Leader 状态"""
    FOLLOWER = 0
    CANDIDATE = 1
    LEADER = 2

    def __str__(self) -> str:
        return self.name


@dataclass
class LogEntry:
    """日志条目"""
    slot_id: int
    proposal_id: ProposalID
    value: Any
    committed: bool = False
    timestamp: float = field(default_factory=time.time)


@dataclass
class VoteRequest:
    """投票请求"""
    term: int
    candidate_id: str
    last_log_index: int = 0
    last_log_term: int = 0


@dataclass
class VoteResponse:
    """投票响应"""
    term: int
    vote_granted: bool
    node_id: str


@dataclass
class HeartbeatRequest:
    """心跳请求"""
    term: int
    leader_id: str


@dataclass
class HeartbeatResponse:
    """心跳响应"""
    term: int
    success: bool
    node_id: str


@dataclass
class AppendEntriesRequest:
    """追加条目请求"""
    term: int
    leader_id: str
    prev_log_index: int
    prev_log_term: int
    entries: list
    leader_commit: int


@dataclass
class AppendEntriesResponse:
    """追加条目响应"""
    term: int
    success: bool
    node_id: str
    match_index: int = 0

"""Paxos 类型定义"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(order=True)
class ProposalID:
    """提案ID，由编号和节点ID组成"""
    number: int
    node_id: str = field(compare=False)

    def __str__(self) -> str:
        return f"{self.number}-{self.node_id}"

    def is_greater_than(self, other: 'ProposalID') -> bool:
        """比较提案ID大小"""
        if self.number != other.number:
            return self.number > other.number
        return self.node_id > other.node_id


@dataclass
class PrepareArgs:
    """Prepare 请求参数"""
    proposal_id: ProposalID
    to: str


@dataclass
class PrepareReply:
    """Prepare 响应"""
    promise: bool
    proposal_id: ProposalID
    accepted_id: Optional[ProposalID] = None
    accepted_value: Any = None
    from_id: str = ""


@dataclass
class AcceptArgs:
    """Accept 请求参数"""
    proposal_id: ProposalID
    value: Any
    to: str


@dataclass
class AcceptReply:
    """Accept 响应"""
    accepted: bool
    proposal_id: ProposalID
    from_id: str = ""


@dataclass
class AcceptedArgs:
    """Accepted 通知参数"""
    proposal_id: ProposalID
    value: Any
    from_id: str
    to: str = ""

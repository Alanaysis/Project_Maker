"""
投票合约模块
实现投票活动的创建、提案管理、投票执行和结果统计
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any
from .blockchain import Blockchain, Transaction


class VoteStatus(Enum):
    """投票状态枚举"""
    NOT_STARTED = "not_started"
    ACTIVE = "active"
    ENDED = "ended"


@dataclass
class Proposal:
    """提案数据结构"""
    id: int
    name: str
    description: str
    vote_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "vote_count": self.vote_count,
        }


@dataclass
class VoteSession:
    """投票活动数据结构"""
    id: int
    title: str
    description: str
    creator: str
    start_time: float
    end_time: float
    status: VoteStatus = VoteStatus.NOT_STARTED
    proposals: List[Proposal] = field(default_factory=list)
    has_voted: Dict[str, bool] = field(default_factory=dict)
    voted_proposal: Dict[str, int] = field(default_factory=dict)
    total_votes: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "creator": self.creator,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": self.status.value,
            "proposals": [p.to_dict() for p in self.proposals],
            "total_votes": self.total_votes,
        }


class VotingContract:
    """投票合约实现"""

    def __init__(self, blockchain: Optional[Blockchain] = None):
        self.blockchain = blockchain or Blockchain(difficulty=2)
        self.vote_sessions: Dict[int, VoteSession] = {}
        self.session_counter: int = 0
        self.events: List[Dict[str, Any]] = []

    def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """触发事件"""
        event = {
            "type": event_type,
            "timestamp": time.time(),
            "data": data,
        }
        self.events.append(event)

    def create_vote_session(
        self,
        title: str,
        description: str,
        start_time: float,
        end_time: float,
        creator: str,
    ) -> int:
        """
        创建投票活动

        Args:
            title: 投票标题
            description: 投票描述
            start_time: 开始时间
            end_time: 结束时间
            creator: 创建者地址

        Returns:
            投票活动ID
        """
        if start_time >= end_time:
            raise ValueError("开始时间必须早于结束时间")

        session_id = self.session_counter
        self.session_counter += 1

        session = VoteSession(
            id=session_id,
            title=title,
            description=description,
            creator=creator,
            start_time=start_time,
            end_time=end_time,
        )

        self.vote_sessions[session_id] = session

        self._emit_event("VoteSessionCreated", {
            "session_id": session_id,
            "title": title,
            "creator": creator,
            "start_time": start_time,
            "end_time": end_time,
        })

        # 记录到区块链
        tx = Transaction(
            sender=creator,
            receiver="voting_contract",
            data={
                "action": "create_session",
                "session_id": session_id,
                "title": title,
            },
        )
        self.blockchain.add_transaction(tx)

        return session_id

    def add_proposal(
        self,
        session_id: int,
        name: str,
        description: str,
        caller: str,
    ) -> int:
        """
        添加提案

        Args:
            session_id: 投票活动ID
            name: 提案名称
            description: 提案描述
            caller: 调用者地址

        Returns:
            提案ID
        """
        if session_id not in self.vote_sessions:
            raise ValueError("投票活动不存在")

        session = self.vote_sessions[session_id]

        if session.creator != caller:
            raise PermissionError("只有创建者可以添加提案")

        if session.status != VoteStatus.NOT_STARTED:
            raise ValueError("只能在投票开始前添加提案")

        proposal_id = len(session.proposals)
        proposal = Proposal(
            id=proposal_id,
            name=name,
            description=description,
        )

        session.proposals.append(proposal)

        self._emit_event("ProposalAdded", {
            "session_id": session_id,
            "proposal_id": proposal_id,
            "name": name,
        })

        return proposal_id

    def start_voting(self, session_id: int, caller: str) -> None:
        """
        开始投票

        Args:
            session_id: 投票活动ID
            caller: 调用者地址
        """
        if session_id not in self.vote_sessions:
            raise ValueError("投票活动不存在")

        session = self.vote_sessions[session_id]

        if session.creator != caller:
            raise PermissionError("只有创建者可以开始投票")

        if session.status != VoteStatus.NOT_STARTED:
            raise ValueError("投票活动已经开始或已结束")

        if len(session.proposals) == 0:
            raise ValueError("至少需要一个提案")

        current_time = time.time()
        if current_time < session.start_time:
            raise ValueError("尚未到达开始时间")

        session.status = VoteStatus.ACTIVE

        self._emit_event("VotingStarted", {
            "session_id": session_id,
        })

    def vote(
        self,
        session_id: int,
        proposal_id: int,
        voter_address: str,
    ) -> None:
        """
        进行投票

        Args:
            session_id: 投票活动ID
            proposal_id: 提案ID
            voter_address: 投票者地址
        """
        if session_id not in self.vote_sessions:
            raise ValueError("投票活动不存在")

        session = self.vote_sessions[session_id]

        # 验证投票状态
        if session.status != VoteStatus.ACTIVE:
            raise ValueError("投票活动未处于进行中状态")

        current_time = time.time()
        if current_time < session.start_time:
            raise ValueError("投票尚未开始")
        if current_time > session.end_time:
            raise ValueError("投票已结束")

        # 验证提案
        if proposal_id >= len(session.proposals) or proposal_id < 0:
            raise ValueError("提案不存在")

        # 验证是否已投票
        if session.has_voted.get(voter_address, False):
            raise ValueError("您已经投过票了")

        # 记录投票
        session.proposals[proposal_id].vote_count += 1
        session.has_voted[voter_address] = True
        session.voted_proposal[voter_address] = proposal_id
        session.total_votes += 1

        self._emit_event("VoteCast", {
            "session_id": session_id,
            "voter": voter_address,
            "proposal_id": proposal_id,
        })

        # 记录到区块链
        tx = Transaction(
            sender=voter_address,
            receiver="voting_contract",
            data={
                "action": "vote",
                "session_id": session_id,
                "proposal_id": proposal_id,
            },
        )
        self.blockchain.add_transaction(tx)

    def end_voting(self, session_id: int, caller: str) -> None:
        """
        结束投票

        Args:
            session_id: 投票活动ID
            caller: 调用者地址
        """
        if session_id not in self.vote_sessions:
            raise ValueError("投票活动不存在")

        session = self.vote_sessions[session_id]

        if session.creator != caller:
            raise PermissionError("只有创建者可以结束投票")

        if session.status != VoteStatus.ACTIVE:
            raise ValueError("投票活动未处于进行中状态")

        session.status = VoteStatus.ENDED

        # 挖掘区块记录投票结果
        self.blockchain.mine_pending_transactions()

        self._emit_event("VoteSessionEnded", {
            "session_id": session_id,
            "total_votes": session.total_votes,
        })

    def get_session(self, session_id: int) -> Optional[VoteSession]:
        """获取投票活动详情"""
        return self.vote_sessions.get(session_id)

    def get_proposal(self, session_id: int, proposal_id: int) -> Optional[Proposal]:
        """获取提案详情"""
        if session_id not in self.vote_sessions:
            return None

        session = self.vote_sessions[session_id]
        if proposal_id >= len(session.proposals) or proposal_id < 0:
            return None

        return session.proposals[proposal_id]

    def has_voted(self, session_id: int, voter_address: str) -> bool:
        """检查用户是否已投票"""
        if session_id not in self.vote_sessions:
            return False
        return self.vote_sessions[session_id].has_voted.get(voter_address, False)

    def get_voted_proposal(self, session_id: int, voter_address: str) -> Optional[int]:
        """获取用户的投票选择"""
        if session_id not in self.vote_sessions:
            return None

        session = self.vote_sessions[session_id]
        if not session.has_voted.get(voter_address, False):
            return None

        return session.voted_proposal.get(voter_address)

    def get_results(self, session_id: int) -> Dict[str, Any]:
        """获取投票结果"""
        if session_id not in self.vote_sessions:
            raise ValueError("投票活动不存在")

        session = self.vote_sessions[session_id]

        results = {
            "session_id": session_id,
            "title": session.title,
            "total_votes": session.total_votes,
            "status": session.status.value,
            "proposals": [],
        }

        for proposal in session.proposals:
            percentage = (
                (proposal.vote_count / session.total_votes * 100)
                if session.total_votes > 0
                else 0
            )
            results["proposals"].append({
                "id": proposal.id,
                "name": proposal.name,
                "votes": proposal.vote_count,
                "percentage": round(percentage, 2),
            })

        # 按票数排序
        results["proposals"].sort(key=lambda x: x["votes"], reverse=True)

        # 确定获胜者
        if results["proposals"]:
            results["winner"] = results["proposals"][0]

        return results

    def get_all_sessions(self) -> List[VoteSession]:
        """获取所有投票活动"""
        return list(self.vote_sessions.values())

    def get_events(self) -> List[Dict[str, Any]]:
        """获取所有事件"""
        return self.events.copy()

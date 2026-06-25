"""
投票规则模块
实现一人一票、投票截止、多数决等投票规则
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable


class VotingMethod(Enum):
    """投票方式枚举"""
    SIMPLE_MAJORITY = "simple_majority"  # 简单多数
    ABSOLUTE_MAJORITY = "absolute_majority"  # 绝对多数
    SUPER_MAJORITY = "super_majority"  # 超级多数
    PLURALITY = "plurality"  # 相对多数
    RANKED_CHOICE = "ranked_choice"  # 排序选择


class QuorumType(Enum):
    """法定人数类型"""
    NONE = "none"  # 无法定人数要求
    PERCENTAGE = "percentage"  # 百分比
    ABSOLUTE = "absolute"  # 绝对数量


@dataclass
class VotingRules:
    """投票规则配置"""
    voting_method: VotingMethod = VotingMethod.SIMPLE_MAJORITY
    quorum_type: QuorumType = QuorumType.NONE
    quorum_value: float = 0  # 法定人数要求（百分比或绝对数量）
    majority_threshold: float = 0.5  # 多数决阈值（0-1）
    allow_abstention: bool = True  # 是否允许弃权
    require_all_proposals_voted: bool = False  # 是否必须对所有提案投票
    max_selections: int = 1  # 最大选择数
    min_selections: int = 1  # 最小选择数

    def to_dict(self) -> Dict[str, Any]:
        return {
            "voting_method": self.voting_method.value,
            "quorum_type": self.quorum_type.value,
            "quorum_value": self.quorum_value,
            "majority_threshold": self.majority_threshold,
            "allow_abstention": self.allow_abstention,
            "require_all_proposals_voted": self.require_all_proposals_voted,
            "max_selections": self.max_selections,
            "min_selections": self.min_selections,
        }


@dataclass
class VoteResult:
    """投票结果"""
    session_id: int
    total_eligible_voters: int
    total_votes_cast: int
    participation_rate: float
    quorum_met: bool
    winner: Optional[Dict[str, Any]] = None
    proposals: List[Dict[str, Any]] = field(default_factory=list)
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "total_eligible_voters": self.total_eligible_voters,
            "total_votes_cast": self.total_votes_cast,
            "participation_rate": self.participation_rate,
            "quorum_met": self.quorum_met,
            "winner": self.winner,
            "proposals": self.proposals,
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors,
        }


class VotingEngine:
    """投票规则引擎"""

    def __init__(self, rules: Optional[VotingRules] = None):
        self.rules = rules or VotingRules()

    def validate_vote(
        self,
        voter_address: str,
        proposal_ids: List[int],
        total_proposals: int,
        has_voted: bool,
    ) -> tuple[bool, List[str]]:
        """
        验证投票是否符合规则

        Args:
            voter_address: 投票者地址
            proposal_ids: 选择的提案ID列表
            total_proposals: 总提案数
            has_voted: 是否已投票

        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []

        # 检查是否已投票
        if has_voted:
            errors.append("该选民已经投过票")
            return False, errors

        # 检查选择数量
        if len(proposal_ids) < self.rules.min_selections:
            errors.append(f"至少需要选择 {self.rules.min_selections} 个提案")

        if len(proposal_ids) > self.rules.max_selections:
            errors.append(f"最多只能选择 {self.rules.max_selections} 个提案")

        # 检查提案ID有效性
        for pid in proposal_ids:
            if pid < 0 or pid >= total_proposals:
                errors.append(f"提案ID {pid} 无效")

        # 检查重复选择
        if len(proposal_ids) != len(set(proposal_ids)):
            errors.append("不能重复选择同一提案")

        return len(errors) == 0, errors

    def check_quorum(
        self,
        total_votes: int,
        total_eligible_voters: int,
    ) -> tuple[bool, float]:
        """
        检查是否达到法定人数

        Args:
            total_votes: 总投票数
            total_eligible_voters: 总合格选民数

        Returns:
            (是否达到法定人数, 参与率)
        """
        if total_eligible_voters == 0:
            return False, 0.0

        participation_rate = total_votes / total_eligible_voters

        if self.rules.quorum_type == QuorumType.NONE:
            return True, participation_rate
        elif self.rules.quorum_type == QuorumType.PERCENTAGE:
            return participation_rate >= self.rules.quorum_value, participation_rate
        elif self.rules.quorum_type == QuorumType.ABSOLUTE:
            return total_votes >= self.rules.quorum_value, participation_rate

        return False, participation_rate

    def determine_winner(
        self,
        proposals: List[Dict[str, Any]],
        total_votes: int,
    ) -> Optional[Dict[str, Any]]:
        """
        确定获胜者

        Args:
            proposals: 提案列表（包含投票数）
            total_votes: 总投票数

        Returns:
            获胜提案或None
        """
        if not proposals:
            return None

        if self.rules.voting_method == VotingMethod.SIMPLE_MAJORITY:
            return self._simple_majority(proposals, total_votes)
        elif self.rules.voting_method == VotingMethod.ABSOLUTE_MAJORITY:
            return self._absolute_majority(proposals, total_votes)
        elif self.rules.voting_method == VotingMethod.SUPER_MAJORITY:
            return self._super_majority(proposals, total_votes)
        elif self.rules.voting_method == VotingMethod.PLURALITY:
            return self._plurality(proposals)
        elif self.rules.voting_method == VotingMethod.RANKED_CHOICE:
            return self._ranked_choice(proposals, total_votes)

        return None

    def _simple_majority(
        self,
        proposals: List[Dict[str, Any]],
        total_votes: int,
    ) -> Optional[Dict[str, Any]]:
        """简单多数决"""
        if not proposals:
            return None

        # 按票数排序
        sorted_proposals = sorted(proposals, key=lambda x: x.get("votes", 0), reverse=True)

        winner = sorted_proposals[0]
        winner_votes = winner.get("votes", 0)

        # 检查是否超过阈值
        if total_votes > 0:
            vote_ratio = winner_votes / total_votes
            if vote_ratio >= self.rules.majority_threshold:
                return winner

        return winner

    def _absolute_majority(
        self,
        proposals: List[Dict[str, Any]],
        total_votes: int,
    ) -> Optional[Dict[str, Any]]:
        """绝对多数决（需要超过50%）"""
        if not proposals:
            return None

        sorted_proposals = sorted(proposals, key=lambda x: x.get("votes", 0), reverse=True)
        winner = sorted_proposals[0]
        winner_votes = winner.get("votes", 0)

        # 绝对多数要求超过总票数的50%
        if total_votes > 0 and winner_votes > total_votes / 2:
            return winner

        return None

    def _super_majority(
        self,
        proposals: List[Dict[str, Any]],
        total_votes: int,
    ) -> Optional[Dict[str, Any]]:
        """超级多数决（需要超过2/3）"""
        if not proposals:
            return None

        sorted_proposals = sorted(proposals, key=lambda x: x.get("votes", 0), reverse=True)
        winner = sorted_proposals[0]
        winner_votes = winner.get("votes", 0)

        # 超级多数要求超过总票数的2/3
        if total_votes > 0 and winner_votes > total_votes * 2 / 3:
            return winner

        return None

    def _plurality(
        self,
        proposals: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """相对多数决（最高票获胜）"""
        if not proposals:
            return None

        return max(proposals, key=lambda x: x.get("votes", 0))

    def _ranked_choice(
        self,
        proposals: List[Dict[str, Any]],
        total_votes: int,
    ) -> Optional[Dict[str, Any]]:
        """排序选择投票（简化实现）"""
        # 简化实现：直接返回最高票
        return self._plurality(proposals)

    def calculate_results(
        self,
        session_id: int,
        proposals: List[Dict[str, Any]],
        total_eligible_voters: int,
    ) -> VoteResult:
        """
        计算投票结果

        Args:
            session_id: 投票活动ID
            proposals: 提案列表
            total_eligible_voters: 总合格选民数

        Returns:
            投票结果
        """
        total_votes = sum(p.get("votes", 0) for p in proposals)

        # 检查法定人数
        quorum_met, participation_rate = self.check_quorum(
            total_votes, total_eligible_voters
        )

        # 计算百分比
        for proposal in proposals:
            votes = proposal.get("votes", 0)
            proposal["percentage"] = (
                round(votes / total_votes * 100, 2) if total_votes > 0 else 0
            )

        # 按票数排序
        sorted_proposals = sorted(
            proposals, key=lambda x: x.get("votes", 0), reverse=True
        )

        # 确定获胜者
        winner = self.determine_winner(proposals, total_votes)

        # 验证结果有效性
        is_valid = True
        validation_errors = []

        if not quorum_met:
            is_valid = False
            validation_errors.append("未达到法定人数要求")

        if winner is None and total_votes > 0:
            is_valid = False
            validation_errors.append("无法确定获胜者")

        return VoteResult(
            session_id=session_id,
            total_eligible_voters=total_eligible_voters,
            total_votes_cast=total_votes,
            participation_rate=participation_rate,
            quorum_met=quorum_met,
            winner=winner,
            proposals=sorted_proposals,
            is_valid=is_valid,
            validation_errors=validation_errors,
        )


class OnePersonOneVote:
    """一人一投票规则验证器"""

    def __init__(self):
        self.voted_sessions: Dict[int, Dict[str, bool]] = {}

    def can_vote(self, session_id: int, voter_address: str) -> bool:
        """检查是否可以投票"""
        if session_id not in self.voted_sessions:
            return True
        return not self.voted_sessions[session_id].get(voter_address, False)

    def record_vote(self, session_id: int, voter_address: str) -> None:
        """记录投票"""
        if session_id not in self.voted_sessions:
            self.voted_sessions[session_id] = {}
        self.voted_sessions[session_id][voter_address] = True

    def has_voted(self, session_id: int, voter_address: str) -> bool:
        """检查是否已投票"""
        if session_id not in self.voted_sessions:
            return False
        return self.voted_sessions[session_id].get(voter_address, False)

    def get_voter_count(self, session_id: int) -> int:
        """获取投票人数"""
        if session_id not in self.voted_sessions:
            return 0
        return sum(1 for v in self.voted_sessions[session_id].values() if v)

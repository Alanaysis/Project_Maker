"""
透明性模块
实现投票记录、结果公示和审计追踪
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from .blockchain import Blockchain, Transaction


@dataclass
class VoteRecord:
    """投票记录"""
    session_id: int
    voter_address: str
    proposal_id: int
    timestamp: float
    transaction_hash: str = ""
    block_number: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "voter_address": self.voter_address,
            "proposal_id": self.proposal_id,
            "timestamp": self.timestamp,
            "transaction_hash": self.transaction_hash,
            "block_number": self.block_number,
        }

    def compute_hash(self) -> str:
        # 只使用核心数据计算哈希，不包含交易哈希和区块号
        core_data = {
            "session_id": self.session_id,
            "voter_address": self.voter_address,
            "proposal_id": self.proposal_id,
            "timestamp": self.timestamp,
        }
        record_string = json.dumps(core_data, sort_keys=True)
        return hashlib.sha256(record_string.encode()).hexdigest()


@dataclass
class AuditEntry:
    """审计条目"""
    action: str
    actor: str
    details: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    previous_hash: str = ""
    hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "actor": self.actor,
            "details": self.details,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "hash": self.hash,
        }

    def compute_hash(self) -> str:
        entry_string = json.dumps(
            {
                "action": self.action,
                "actor": self.actor,
                "details": self.details,
                "timestamp": self.timestamp,
                "previous_hash": self.previous_hash,
            },
            sort_keys=True,
        )
        return hashlib.sha256(entry_string.encode()).hexdigest()


class VoteLedger:
    """投票账本 - 记录所有投票交易"""

    def __init__(self, blockchain: Optional[Blockchain] = None):
        self.blockchain = blockchain or Blockchain(difficulty=2)
        self.vote_records: List[VoteRecord] = []
        self.session_records: Dict[int, List[VoteRecord]] = {}

    def record_vote(
        self,
        session_id: int,
        voter_address: str,
        proposal_id: int,
    ) -> VoteRecord:
        """
        记录投票

        Args:
            session_id: 投票活动ID
            voter_address: 投票者地址
            proposal_id: 提案ID

        Returns:
            投票记录
        """
        record = VoteRecord(
            session_id=session_id,
            voter_address=voter_address,
            proposal_id=proposal_id,
            timestamp=time.time(),
        )

        # 记录到区块链
        tx = Transaction(
            sender=voter_address,
            receiver="vote_ledger",
            data={
                "action": "vote",
                "session_id": session_id,
                "proposal_id": proposal_id,
                "record_hash": record.compute_hash(),
            },
        )
        self.blockchain.add_transaction(tx)

        # 挖掘区块
        block = self.blockchain.mine_pending_transactions()
        if block:
            record.block_number = block.index
            record.transaction_hash = block.hash

        self.vote_records.append(record)

        if session_id not in self.session_records:
            self.session_records[session_id] = []
        self.session_records[session_id].append(record)

        return record

    def get_session_records(self, session_id: int) -> List[VoteRecord]:
        """获取投票活动的所有记录"""
        return self.session_records.get(session_id, [])

    def get_voter_records(self, voter_address: str) -> List[VoteRecord]:
        """获取选民的所有投票记录"""
        return [
            record for record in self.vote_records
            if record.voter_address == voter_address
        ]

    def verify_record(self, record: VoteRecord) -> bool:
        """验证投票记录"""
        # 检查记录哈希
        expected_hash = record.compute_hash()

        # 检查区块链中的交易
        for block in self.blockchain.chain:
            for tx in block.transactions:
                if tx.data.get("record_hash") == expected_hash:
                    return True

        return False

    def get_record_count(self) -> int:
        """获取记录总数"""
        return len(self.vote_records)

    def export_records(self, session_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """导出投票记录"""
        if session_id is not None:
            records = self.get_session_records(session_id)
        else:
            records = self.vote_records

        return [record.to_dict() for record in records]


class AuditTrail:
    """审计追踪"""

    def __init__(self):
        self.entries: List[AuditEntry] = []
        self.chain_hash: str = ""

    def add_entry(
        self,
        action: str,
        actor: str,
        details: Dict[str, Any],
    ) -> AuditEntry:
        """
        添加审计条目

        Args:
            action: 操作类型
            actor: 操作者
            details: 操作详情

        Returns:
            审计条目
        """
        previous_hash = self.chain_hash if self.chain_hash else "0" * 64

        entry = AuditEntry(
            action=action,
            actor=actor,
            details=details,
            previous_hash=previous_hash,
        )

        entry.hash = entry.compute_hash()
        self.chain_hash = entry.hash

        self.entries.append(entry)

        return entry

    def verify_chain(self) -> bool:
        """验证审计链完整性"""
        for i in range(1, len(self.entries)):
            current = self.entries[i]
            previous = self.entries[i - 1]

            # 验证哈希链
            if current.previous_hash != previous.hash:
                return False

            # 验证当前条目哈希
            if current.hash != current.compute_hash():
                return False

        return True

    def get_entries_by_action(self, action: str) -> List[AuditEntry]:
        """按操作类型获取条目"""
        return [entry for entry in self.entries if entry.action == action]

    def get_entries_by_actor(self, actor: str) -> List[AuditEntry]:
        """按操作者获取条目"""
        return [entry for entry in self.entries if entry.actor == actor]

    def get_entries_in_time_range(
        self,
        start_time: float,
        end_time: float,
    ) -> List[AuditEntry]:
        """获取时间范围内的条目"""
        return [
            entry for entry in self.entries
            if start_time <= entry.timestamp <= end_time
        ]

    def export_audit_trail(self) -> List[Dict[str, Any]]:
        """导出审计追踪"""
        return [entry.to_dict() for entry in self.entries]

    def get_statistics(self) -> Dict[str, Any]:
        """获取审计统计"""
        action_counts: Dict[str, int] = {}
        actor_counts: Dict[str, int] = {}

        for entry in self.entries:
            action_counts[entry.action] = action_counts.get(entry.action, 0) + 1
            actor_counts[entry.actor] = actor_counts.get(entry.actor, 0) + 1

        return {
            "total_entries": len(self.entries),
            "action_counts": action_counts,
            "actor_counts": actor_counts,
            "chain_valid": self.verify_chain(),
        }


class TransparencyReport:
    """透明度报告生成器"""

    def __init__(
        self,
        vote_ledger: VoteLedger,
        audit_trail: AuditTrail,
    ):
        self.vote_ledger = vote_ledger
        self.audit_trail = audit_trail

    def generate_session_report(self, session_id: int) -> Dict[str, Any]:
        """
        生成投票活动报告

        Args:
            session_id: 投票活动ID

        Returns:
            报告数据
        """
        records = self.vote_ledger.get_session_records(session_id)

        # 统计投票分布
        vote_distribution: Dict[int, int] = {}
        for record in records:
            proposal_id = record.proposal_id
            vote_distribution[proposal_id] = vote_distribution.get(proposal_id, 0) + 1

        # 生成时间线
        timeline = []
        for record in records:
            timeline.append({
                "timestamp": record.timestamp,
                "voter": record.voter_address,
                "proposal": record.proposal_id,
            })

        timeline.sort(key=lambda x: x["timestamp"])

        return {
            "session_id": session_id,
            "total_votes": len(records),
            "vote_distribution": vote_distribution,
            "timeline": timeline,
            "audit_trail_valid": self.audit_trail.verify_chain(),
        }

    def generate_voter_report(self, voter_address: str) -> Dict[str, Any]:
        """
        生成选民报告

        Args:
            voter_address: 选民地址

        Returns:
            报告数据
        """
        records = self.vote_ledger.get_voter_records(voter_address)
        audit_entries = self.audit_trail.get_entries_by_actor(voter_address)

        return {
            "voter_address": voter_address,
            "total_votes": len(records),
            "sessions_participated": list(set(r.session_id for r in records)),
            "vote_history": [r.to_dict() for r in records],
            "audit_entries": [e.to_dict() for e in audit_entries],
        }

    def generate_full_report(self) -> Dict[str, Any]:
        """
        生成完整报告

        Returns:
            完整报告数据
        """
        return {
            "total_records": self.vote_ledger.get_record_count(),
            "blockchain_height": len(self.vote_ledger.blockchain.chain),
            "blockchain_valid": self.vote_ledger.blockchain.is_chain_valid(),
            "audit_trail_stats": self.audit_trail.get_statistics(),
            "audit_trail_valid": self.audit_trail.verify_chain(),
        }

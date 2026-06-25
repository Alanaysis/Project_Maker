"""
DAO 投票示例
演示去中心化自治组织的投票治理
"""

import time
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.blockchain import Blockchain
from src.voting import VotingContract
from src.identity import VoterRegistry
from src.consensus import (
    VotingEngine,
    VotingRules,
    VotingMethod,
    QuorumType,
)
from src.transparency import VoteLedger, AuditTrail, TransparencyReport


class DAOGovernance:
    """DAO 治理系统"""

    def __init__(self, name: str):
        self.name = name
        self.blockchain = Blockchain(difficulty=2)
        self.voting_contract = VotingContract(self.blockchain)
        self.voter_registry = VoterRegistry()
        self.vote_ledger = VoteLedger(self.blockchain)
        self.audit_trail = AuditTrail()

        # DAO 特定规则：绝对多数 + 50%法定人数
        self.rules = VotingRules(
            voting_method=VotingMethod.ABSOLUTE_MAJORITY,
            quorum_type=QuorumType.PERCENTAGE,
            quorum_value=0.5,
            majority_threshold=0.5,
        )
        self.voting_engine = VotingEngine(self.rules)

        self.members = []
        self.proposals_history = []

    def add_member(self, address: str, name: str, voting_power: int = 1):
        """添加 DAO 成员"""
        self.voter_registry.register_voter(address, name, f"{name}@dao.com")
        self.voter_registry.verify_voter(address)
        self.voter_registry.issue_credential(address)
        self.members.append({"address": address, "name": name, "voting_power": voting_power})

        self.audit_trail.add_entry(
            action="add_member",
            actor="governance",
            details={"address": address, "name": name},
        )

    def create_proposal(
        self,
        title: str,
        description: str,
        proposer: str,
        duration: float = 3600,
    ) -> int:
        """创建提案"""
        session_id = self.voting_contract.create_vote_session(
            title=title,
            description=description,
            start_time=time.time(),
            end_time=time.time() + duration,
            creator=proposer,
        )

        self.audit_trail.add_entry(
            action="create_proposal",
            actor=proposer,
            details={"session_id": session_id, "title": title},
        )

        return session_id

    def add_option(self, session_id: int, name: str, description: str, caller: str):
        """添加投票选项"""
        self.voting_contract.add_proposal(session_id, name, description, caller)

    def start_vote(self, session_id: int, caller: str):
        """开始投票"""
        self.voting_contract.start_voting(session_id, caller)

    def cast_vote(self, session_id: int, proposal_id: int, voter: str):
        """投票"""
        # 验证资格
        if not self.voter_registry.is_eligible(voter):
            raise PermissionError(f"选民 {voter} 无投票资格")

        # 执行投票
        self.voting_contract.vote(session_id, proposal_id, voter)

        # 记录到账本
        self.vote_ledger.record_vote(session_id, voter, proposal_id)

        # 审计
        self.audit_trail.add_entry(
            action="cast_vote",
            actor=voter,
            details={"session_id": session_id, "proposal_id": proposal_id},
        )

    def end_vote(self, session_id: int, caller: str):
        """结束投票"""
        self.voting_contract.end_voting(session_id, caller)

        self.audit_trail.add_entry(
            action="end_vote",
            actor=caller,
            details={"session_id": session_id},
        )

    def get_results(self, session_id: int):
        """获取结果"""
        raw_results = self.voting_contract.get_results(session_id)

        # 使用规则引擎计算
        proposals = raw_results["proposals"]
        total_eligible = len(self.members)

        vote_result = self.voting_engine.calculate_results(
            session_id=session_id,
            proposals=proposals,
            total_eligible_voters=total_eligible,
        )

        return {
            "raw_results": raw_results,
            "vote_result": vote_result.to_dict(),
        }

    def get_governance_report(self):
        """获取治理报告"""
        report_gen = TransparencyReport(self.vote_ledger, self.audit_trail)
        full_report = report_gen.generate_full_report()

        return {
            "dao_name": self.name,
            "total_members": len(self.members),
            "members": self.members,
            "blockchain": {
                "height": len(self.blockchain.chain),
                "valid": self.blockchain.is_chain_valid(),
            },
            "audit_trail": self.audit_trail.get_statistics(),
            "transparency_report": full_report,
        }


def main():
    print("=" * 60)
    print("DAO 治理投票示例")
    print("=" * 60)

    # 创建 DAO
    dao = DAOGovernance("示例DAO")

    # 1. 添加成员
    print("\n[1] 添加 DAO 成员...")
    members = [
        ("0xMember1", "Alice", 10),
        ("0xMember2", "Bob", 8),
        ("0xMember3", "Charlie", 6),
        ("0xMember4", "David", 4),
        ("0xMember5", "Eve", 2),
    ]

    for address, name, power in members:
        dao.add_member(address, name, power)
        print(f"  添加成员: {name} (投票权重: {power})")

    # 2. 创建提案
    print("\n[2] 创建提案...")
    session_id = dao.create_proposal(
        title="资金分配提案",
        description="决定如何分配本季度的资金",
        proposer="0xMember1",
    )
    print(f"  创建提案: ID={session_id}")

    # 3. 添加选项
    print("\n[3] 添加投票选项...")
    options = [
        ("选项A: 研发投入", "将60%资金投入研发"),
        ("选项B: 市场推广", "将60%资金投入市场推广"),
        ("选项C: 社区建设", "将60%资金投入社区建设"),
    ]

    for name, description in options:
        dao.add_option(session_id, name, description, "0xMember1")
        print(f"  添加选项: {name}")

    # 4. 开始投票
    print("\n[4] 开始投票...")
    dao.start_vote(session_id, "0xMember1")

    # 5. 成员投票
    print("\n[5] 成员投票...")
    votes = [
        ("0xMember1", 0),  # Alice 投选项A
        ("0xMember2", 0),  # Bob 投选项A
        ("0xMember3", 1),  # Charlie 投选项B
        ("0xMember4", 2),  # David 投选项C
        ("0xMember5", 0),  # Eve 投选项A
    ]

    for voter, option in votes:
        try:
            dao.cast_vote(session_id, option, voter)
            member = next(m for m in members if m[0] == voter)
            print(f"  {member[1]} 投票给选项 {option}")
        except Exception as e:
            print(f"  投票失败: {e}")

    # 6. 结束投票
    print("\n[6] 结束投票...")
    dao.end_vote(session_id, "0xMember1")

    # 7. 查看结果
    print("\n[7] 投票结果:")
    print("-" * 60)
    results = dao.get_results(session_id)

    print(f"投票标题: {results['raw_results']['title']}")
    print(f"总投票数: {results['raw_results']['total_votes']}")
    print(f"法定人数: {'达到' if results['vote_result']['quorum_met'] else '未达到'}")
    print(f"参与率: {results['vote_result']['participation_rate']:.2%}")

    print("\n提案得票情况:")
    for proposal in results['raw_results']['proposals']:
        print(f"  {proposal['name']}: {proposal['votes']} 票 ({proposal['percentage']}%)")

    if results['vote_result']['winner']:
        print(f"\n获胜提案: {results['vote_result']['winner']['name']}")

    if not results['vote_result']['is_valid']:
        print(f"\n投票无效原因: {results['vote_result']['validation_errors']}")

    # 8. 治理报告
    print("\n[8] 治理报告:")
    print("-" * 60)
    report = dao.get_governance_report()

    print(f"DAO 名称: {report['dao_name']}")
    print(f"成员数量: {report['total_members']}")
    print(f"区块链高度: {report['blockchain']['height']}")
    print(f"区块链有效: {report['blockchain']['valid']}")
    print(f"审计条目数: {report['audit_trail']['total_entries']}")
    print(f"审计链有效: {report['audit_trail']['chain_valid']}")

    print("\n" + "=" * 60)
    print("DAO 治理示例完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()

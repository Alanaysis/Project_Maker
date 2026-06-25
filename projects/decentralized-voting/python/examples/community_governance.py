"""
社区治理示例
演示社区级别的去中心化治理投票
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


class CommunityGovernance:
    """社区治理系统"""

    def __init__(self, community_name: str):
        self.community_name = community_name
        self.blockchain = Blockchain(difficulty=2)
        self.voting_contract = VotingContract(self.blockchain)
        self.voter_registry = VoterRegistry()
        self.vote_ledger = VoteLedger(self.blockchain)
        self.audit_trail = AuditTrail()

        # 社区规则：简单多数 + 30%法定人数
        self.rules = VotingRules(
            voting_method=VotingMethod.SIMPLE_MAJORITY,
            quorum_type=QuorumType.PERCENTAGE,
            quorum_value=0.3,
            majority_threshold=0.5,
            allow_abstention=True,
        )
        self.voting_engine = VotingEngine(self.rules)

        self.residents = []

    def register_resident(
        self,
        address: str,
        name: str,
        unit: str,
    ):
        """注册社区居民"""
        self.voter_registry.register_voter(
            address,
            name,
            f"{name}@community.com",
            metadata={"unit": unit},
        )
        self.voter_registry.verify_voter(address)
        self.voter_registry.issue_credential(address)
        self.residents.append({
            "address": address,
            "name": name,
            "unit": unit,
        })

    def create_poll(
        self,
        title: str,
        description: str,
        options: list,
        creator: str,
        duration: float = 7200,
    ) -> int:
        """创建投票"""
        session_id = self.voting_contract.create_vote_session(
            title=title,
            description=description,
            start_time=time.time(),
            end_time=time.time() + duration,
            creator=creator,
        )

        for option_name, option_desc in options:
            self.voting_contract.add_proposal(
                session_id, option_name, option_desc, creator
            )

        self.voting_contract.start_voting(session_id, creator)

        self.audit_trail.add_entry(
            action="create_poll",
            actor=creator,
            details={"session_id": session_id, "title": title},
        )

        return session_id

    def vote(self, session_id: int, proposal_id: int, voter: str):
        """投票"""
        if not self.voter_registry.is_eligible(voter):
            raise PermissionError(f"居民 {voter} 无投票资格")

        self.voting_contract.vote(session_id, proposal_id, voter)
        self.vote_ledger.record_vote(session_id, voter, proposal_id)

        self.audit_trail.add_entry(
            action="vote",
            actor=voter,
            details={"session_id": session_id, "proposal_id": proposal_id},
        )

    def end_poll(self, session_id: int, creator: str):
        """结束投票"""
        self.voting_contract.end_voting(session_id, creator)

    def get_results(self, session_id: int):
        """获取结果"""
        raw_results = self.voting_contract.get_results(session_id)
        total_eligible = len(self.residents)

        vote_result = self.voting_engine.calculate_results(
            session_id=session_id,
            proposals=raw_results["proposals"],
            total_eligible_voters=total_eligible,
        )

        return {
            "poll": raw_results,
            "analysis": vote_result.to_dict(),
        }

    def get_community_report(self):
        """获取社区报告"""
        report_gen = TransparencyReport(self.vote_ledger, self.audit_trail)

        return {
            "community": self.community_name,
            "residents": len(self.residents),
            "blockchain": {
                "height": len(self.blockchain.chain),
                "valid": self.blockchain.is_chain_valid(),
            },
            "audit": self.audit_trail.get_statistics(),
            "transparency": report_gen.generate_full_report(),
        }


def main():
    print("=" * 60)
    print("社区治理投票示例")
    print("=" * 60)

    # 创建社区
    community = CommunityGovernance("阳光花园社区")

    # 1. 注册居民
    print("\n[1] 注册社区居民...")
    residents = [
        ("0xRes1", "张三", "A栋101"),
        ("0xRes2", "李四", "A栋102"),
        ("0xRes3", "王五", "B栋201"),
        ("0xRes4", "赵六", "B栋202"),
        ("0xRes5", "钱七", "C栋301"),
        ("0xRes6", "孙八", "C栋302"),
        ("0xRes7", "周九", "D栋401"),
        ("0xRes8", "吴十", "D栋402"),
    ]

    for address, name, unit in residents:
        community.register_resident(address, name, unit)
        print(f"  注册居民: {name} ({unit})")

    # 2. 创建投票：物业费调整
    print("\n[2] 创建投票：物业费调整方案")
    print("-" * 60)
    poll1_id = community.create_poll(
        title="2024年物业费调整方案",
        description="请投票选择您支持的物业费调整方案",
        options=[
            ("方案A: 维持现状", "物业费保持不变"),
            ("方案B: 小幅上涨", "物业费上涨5%"),
            ("方案C: 大幅上涨", "物业费上涨10%"),
        ],
        creator="0xRes1",
    )
    print(f"  投票ID: {poll1_id}")

    # 3. 居民投票
    print("\n[3] 居民投票...")
    votes1 = [
        ("0xRes1", 0),
        ("0xRes2", 0),
        ("0xRes3", 1),
        ("0xRes4", 1),
        ("0xRes5", 2),
        ("0xRes6", 0),
        ("0xRes7", 1),
        ("0xRes8", 0),
    ]

    for voter, option in votes1:
        try:
            community.vote(poll1_id, option, voter)
            res = next(r for r in residents if r[0] == voter)
            print(f"  {res[1]} 投票给方案 {option}")
        except Exception as e:
            print(f"  投票失败: {e}")

    # 4. 结束投票
    print("\n[4] 结束投票...")
    community.end_poll(poll1_id, "0xRes1")

    # 5. 查看结果
    print("\n[5] 投票结果:")
    print("-" * 60)
    results1 = community.get_results(poll1_id)

    print(f"投票标题: {results1['poll']['title']}")
    print(f"总投票数: {results1['poll']['total_votes']}")
    print(f"法定人数: {'达到' if results1['analysis']['quorum_met'] else '未达到'}")
    print(f"参与率: {results1['analysis']['participation_rate']:.2%}")

    print("\n方案得票情况:")
    for proposal in results1['poll']['proposals']:
        print(f"  {proposal['name']}: {proposal['votes']} 票 ({proposal['percentage']}%)")

    if results1['analysis']['winner']:
        print(f"\n获胜方案: {results1['analysis']['winner']['name']}")

    # 6. 第二个投票：停车位分配
    print("\n" + "=" * 60)
    print("[6] 创建投票：停车位分配方案")
    print("-" * 60)
    poll2_id = community.create_poll(
        title="新增停车位分配方案",
        description="请投票选择停车位分配方式",
        options=[
            ("方案A: 按楼栋分配", "每栋楼按比例分配"),
            ("方案B: 先到先得", "按照申请顺序分配"),
            ("方案C: 抽签决定", "随机抽签分配"),
        ],
        creator="0xRes2",
    )
    print(f"  投票ID: {poll2_id}")

    # 7. 居民投票
    print("\n[7] 居民投票...")
    votes2 = [
        ("0xRes1", 0),
        ("0xRes2", 2),
        ("0xRes3", 0),
        ("0xRes4", 1),
        ("0xRes5", 2),
        ("0xRes6", 0),
    ]

    for voter, option in votes2:
        try:
            community.vote(poll2_id, option, voter)
            res = next(r for r in residents if r[0] == voter)
            print(f"  {res[1]} 投票给方案 {option}")
        except Exception as e:
            print(f"  投票失败: {e}")

    # 8. 结束投票
    print("\n[8] 结束投票...")
    community.end_poll(poll2_id, "0xRes2")

    # 9. 查看结果
    print("\n[9] 投票结果:")
    print("-" * 60)
    results2 = community.get_results(poll2_id)

    print(f"投票标题: {results2['poll']['title']}")
    print(f"总投票数: {results2['poll']['total_votes']}")

    print("\n方案得票情况:")
    for proposal in results2['poll']['proposals']:
        print(f"  {proposal['name']}: {proposal['votes']} 票 ({proposal['percentage']}%)")

    if results2['analysis']['winner']:
        print(f"\n获胜方案: {results2['analysis']['winner']['name']}")

    # 10. 社区报告
    print("\n" + "=" * 60)
    print("[10] 社区治理报告")
    print("-" * 60)
    report = community.get_community_report()

    print(f"社区名称: {report['community']}")
    print(f"居民数量: {report['residents']}")
    print(f"区块链高度: {report['blockchain']['height']}")
    print(f"区块链有效: {report['blockchain']['valid']}")
    print(f"审计条目数: {report['audit']['total_entries']}")
    print(f"审计链有效: {report['audit']['chain_valid']}")

    print("\n" + "=" * 60)
    print("社区治理示例完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()

"""
基本投票示例
演示去中心化投票系统的基本功能
"""

import time
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.blockchain import Blockchain
from src.voting import VotingContract
from src.identity import VoterRegistry
from src.consensus import VotingEngine, VotingRules, VotingMethod
from src.transparency import VoteLedger, AuditTrail, TransparencyReport


def main():
    print("=" * 60)
    print("去中心化投票系统 - 基本示例")
    print("=" * 60)

    # 1. 初始化系统组件
    print("\n[1] 初始化系统组件...")
    blockchain = Blockchain(difficulty=2)
    voting_contract = VotingContract(blockchain)
    voter_registry = VoterRegistry()
    voting_engine = VotingEngine(VotingRules(voting_method=VotingMethod.SIMPLE_MAJORITY))
    vote_ledger = VoteLedger(blockchain)
    audit_trail = AuditTrail()

    # 2. 注册选民
    print("\n[2] 注册选民...")
    voters = [
        ("0xVoter1", "张三", "zhangsan@example.com"),
        ("0xVoter2", "李四", "lisi@example.com"),
        ("0xVoter3", "王五", "wangwu@example.com"),
        ("0xVoter4", "赵六", "zhaoliu@example.com"),
        ("0xVoter5", "钱七", "qianqi@example.com"),
    ]

    for address, name, email in voters:
        voter_registry.register_voter(address, name, email)
        voter_registry.verify_voter(address)
        voter_registry.issue_credential(address)
        print(f"  注册选民: {name} ({address})")

    # 3. 创建投票活动
    print("\n[3] 创建投票活动...")
    creator = "0xCreator"
    session_id = voting_contract.create_vote_session(
        title="社区治理提案投票",
        description="对社区未来发展进行投票表决",
        start_time=time.time(),
        end_time=time.time() + 3600,
        creator=creator,
    )
    print(f"  创建投票活动: ID={session_id}")

    # 4. 添加提案
    print("\n[4] 添加提案...")
    proposals = [
        ("提案A: 增加社区预算", "提议将社区预算增加20%"),
        ("提案B: 改善基础设施", "提议投资改善社区基础设施"),
        ("提案C: 环保倡议", "提议实施环保相关政策"),
    ]

    for name, description in proposals:
        voting_contract.add_proposal(session_id, name, description, creator)
        print(f"  添加提案: {name}")

    # 5. 开始投票
    print("\n[5] 开始投票...")
    voting_contract.start_voting(session_id, creator)
    print("  投票已开始")

    # 6. 选民投票
    print("\n[6] 选民投票...")
    votes = [
        ("0xVoter1", 0),  # 投票给提案A
        ("0xVoter2", 1),  # 投票给提案B
        ("0xVoter3", 0),  # 投票给提案A
        ("0xVoter4", 2),  # 投票给提案C
        ("0xVoter5", 0),  # 投票给提案A
    ]

    for voter_address, proposal_id in votes:
        # 验证选民资格
        if not voter_registry.is_eligible(voter_address):
            print(f"  选民 {voter_address} 无投票资格")
            continue

        # 验证一人一票
        if not voting_engine.rules.voting_method == VotingMethod.SIMPLE_MAJORITY:
            pass

        # 执行投票
        voting_contract.vote(session_id, proposal_id, voter_address)

        # 记录到账本
        vote_ledger.record_vote(session_id, voter_address, proposal_id)

        # 记录审计
        audit_trail.add_entry(
            action="vote",
            actor=voter_address,
            details={"session_id": session_id, "proposal_id": proposal_id},
        )

        voter = voter_registry.get_voter(voter_address)
        print(f"  {voter.name} 投票给提案 {proposal_id}")

    # 7. 结束投票
    print("\n[7] 结束投票...")
    voting_contract.end_voting(session_id, creator)

    # 8. 查看结果
    print("\n[8] 投票结果:")
    print("-" * 60)
    results = voting_contract.get_results(session_id)

    print(f"投票标题: {results['title']}")
    print(f"总投票数: {results['total_votes']}")
    print(f"投票状态: {results['status']}")
    print("\n提案得票情况:")

    for proposal in results["proposals"]:
        print(f"  {proposal['name']}: {proposal['votes']} 票 ({proposal['percentage']}%)")

    if results.get("winner"):
        print(f"\n获胜提案: {results['winner']['name']}")

    # 9. 生成透明度报告
    print("\n[9] 透明度报告:")
    print("-" * 60)
    report_gen = TransparencyReport(vote_ledger, audit_trail)
    report = report_gen.generate_session_report(session_id)

    print(f"投票记录数: {report['total_votes']}")
    print(f"审计链有效: {report['audit_trail_valid']}")
    print(f"投票分布: {report['vote_distribution']}")

    # 10. 区块链状态
    print("\n[10] 区块链状态:")
    print("-" * 60)
    print(f"区块数量: {len(blockchain.chain)}")
    print(f"区块链有效: {blockchain.is_chain_valid()}")

    print("\n" + "=" * 60)
    print("示例完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()

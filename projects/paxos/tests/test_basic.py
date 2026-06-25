"""Basic Paxos 测试"""

import concurrent.futures
import threading
import time
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.basic.types import ProposalID, PrepareArgs, AcceptArgs, AcceptedArgs
from src.basic.acceptor import Acceptor
from src.basic.proposer import Proposer
from src.basic.learner import Learner
from src.basic.node import Node


class MockAcceptor:
    """模拟 Acceptor，用于测试"""

    def __init__(self, acceptor_id: str, should_fail: bool = False, delay: float = 0):
        self.id = acceptor_id
        self._should_fail = should_fail
        self._delay = delay
        self._acceptor = Acceptor(acceptor_id)

    def handle_prepare(self, args: PrepareArgs):
        if self._delay > 0:
            time.sleep(self._delay)
        if self._should_fail:
            from src.basic.types import PrepareReply
            return PrepareReply(promise=False, proposal_id=args.proposal_id, from_id=self.id)
        return self._acceptor.handle_prepare(args)

    def handle_accept(self, args: AcceptArgs):
        if self._delay > 0:
            time.sleep(self._delay)
        if self._should_fail:
            from src.basic.types import AcceptReply
            return AcceptReply(accepted=False, proposal_id=args.proposal_id, from_id=self.id)
        return self._acceptor.handle_accept(args)

    @property
    def accepted_value(self):
        return self._acceptor.accepted_value


def test_single_value_consensus():
    """测试单值共识"""
    # 创建 3 个 Mock Acceptor
    acceptors = [MockAcceptor(f"acceptor-{i}") for i in range(3)]

    # 创建 Proposer
    proposer = Proposer("proposer-1", acceptors)

    # 提议一个值
    result = proposer.propose("value-1")

    # 验证
    assert result == "value-1", f"Expected 'value-1', got {result}"

    # 验证所有 Acceptor 都接受了
    for i, a in enumerate(acceptors):
        assert a.accepted_value == "value-1", f"Acceptor {i} expected 'value-1', got {a.accepted_value}"


def test_multiple_value_consensus():
    """测试多值共识"""
    # 创建 3 个 Mock Acceptor
    acceptors = [MockAcceptor(f"acceptor-{i}") for i in range(3)]

    # 并发提议多个值
    results = [None] * 5
    errors = [None] * 5

    def propose_value(idx):
        proposer = Proposer(f"proposer-{idx}", acceptors)
        try:
            results[idx] = proposer.propose(f"value-{idx}")
        except Exception as e:
            errors[idx] = e

    threads = [threading.Thread(target=propose_value, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # 验证所有 Proposer 学习到相同的值
    first_result = None
    for i, result in enumerate(results):
        if result is not None:
            if first_result is None:
                first_result = result
            assert result == first_result, f"Proposer {i} got {result}, expected {first_result}"


def test_acceptor_failure():
    """测试 Acceptor 故障"""
    # 创建 5 个 Mock Acceptor
    acceptors = [MockAcceptor(f"acceptor-{i}") for i in range(5)]

    # 模拟 2 个 Acceptor 故障
    acceptors[3]._should_fail = True
    acceptors[4]._should_fail = True

    # 尝试达成共识
    proposer = Proposer("proposer-1", acceptors)
    result = proposer.propose("value-1")

    # 应该能达成共识（3 个存活 > 5/2）
    assert result == "value-1", f"Expected 'value-1', got {result}"


def test_majority_failure():
    """测试多数派故障"""
    # 创建 5 个 Mock Acceptor
    acceptors = [MockAcceptor(f"acceptor-{i}") for i in range(5)]

    # 模拟 3 个 Acceptor 故障
    acceptors[2]._should_fail = True
    acceptors[3]._should_fail = True
    acceptors[4]._should_fail = True

    # 尝试达成共识
    proposer = Proposer("proposer-1", acceptors)

    try:
        proposer.propose("value-1")
        assert False, "Expected RuntimeError"
    except RuntimeError as e:
        assert "Not enough" in str(e)


def test_concurrent_proposers():
    """测试并发 Proposer"""
    # 创建 5 个 Mock Acceptor
    acceptors = [MockAcceptor(f"acceptor-{i}") for i in range(5)]

    # 启动 10 个并发 Proposer
    results = [None] * 10
    errors = [None] * 10

    def propose_value(idx):
        proposer = Proposer(f"proposer-{idx}", acceptors)
        try:
            results[idx] = proposer.propose(f"value-{idx}")
        except Exception as e:
            errors[idx] = e

    threads = [threading.Thread(target=propose_value, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # 验证至少有一些 Proposer 成功
    success_count = sum(1 for r in results if r is not None)
    assert success_count > 0, "Expected at least one proposer to succeed"

    # 验证所有成功的 Proposer 学习到相同的值
    first_result = None
    for i, result in enumerate(results):
        if result is not None:
            if first_result is None:
                first_result = result
            assert result == first_result, f"Proposer {i} got {result}, expected {first_result}"


def test_proposer_with_delay():
    """测试带延迟的 Proposer"""
    # 创建 3 个 Mock Acceptor，其中一个有延迟
    acceptors = [MockAcceptor(f"acceptor-{i}") for i in range(3)]
    acceptors[2]._delay = 0.1  # 100ms

    # 创建 Proposer
    proposer = Proposer("proposer-1", acceptors)

    # 提议一个值
    start = time.time()
    result = proposer.propose("value-1")
    elapsed = time.time() - start

    # 验证
    assert result == "value-1", f"Expected 'value-1', got {result}"
    assert elapsed >= 0.1, f"Expected at least 100ms delay, got {elapsed}s"


def test_learner():
    """测试 Learner"""
    # 创建 Learner
    learner = Learner("learner-1", quorum_size=3)

    # 模拟 Accepted 通知
    proposal_id = ProposalID(number=1, node_id="proposer-1")

    # 发送 3 个 Accepted 通知
    for i in range(3):
        learner.handle_accepted(AcceptedArgs(
            proposal_id=proposal_id,
            value="value-1",
            from_id=f"acceptor-{i}",
        ))

    # 验证已学习
    assert learner.is_learned(proposal_id), "Expected learner to have learned the value"

    # 验证学习的值
    value = learner.get_learned_value(proposal_id)
    assert value == "value-1", f"Expected 'value-1', got {value}"


def test_proposal_id_comparison():
    """测试 ProposalID 比较"""
    id1 = ProposalID(number=1, node_id="node-1")
    id2 = ProposalID(number=2, node_id="node-1")
    id3 = ProposalID(number=1, node_id="node-2")

    assert id2.is_greater_than(id1), "Expected id2 > id1"
    assert not id1.is_greater_than(id2), "Expected id1 < id2"
    assert id3.is_greater_than(id1), "Expected id3 > id1 (same number, different node)"


def test_node_integration():
    """测试 Node 集成"""
    # 创建 3 个节点
    nodes = []
    acceptors = []

    for i in range(3):
        node_id = f"node-{i}"
        node = Node(node_id, [], 3)
        nodes.append(node)
        acceptors.append(node)

    # 更新 Proposer 的 Acceptor 列表
    for node in nodes:
        node._proposer = Proposer(node.id, acceptors)

    # 启动所有节点
    for node in nodes:
        node.start()

    # 提议一个值
    result = nodes[0].propose("Hello, Paxos!")
    assert result == "Hello, Paxos!", f"Expected 'Hello, Paxos!', got {result}"

    # 停止所有节点
    for node in nodes:
        node.stop()


def test_proposer_performance():
    """性能测试"""
    acceptors = [MockAcceptor(f"acceptor-{i}") for i in range(3)]
    proposer = Proposer("proposer-1", acceptors)

    start = time.time()
    count = 100
    for i in range(count):
        proposer.propose(f"value-{i}")
    elapsed = time.time() - start

    print(f"\nProposer performance: {count} proposals in {elapsed:.3f}s ({count/elapsed:.0f} ops/s)")


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])

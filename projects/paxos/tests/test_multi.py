"""Multi Paxos 测试"""

import time
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.multi.types import ProposalID, LogEntry, LeaderState
from src.multi.log import PaxosLog
from src.multi.leader import LeaderNode
from src.multi.replicator import Replicator


def test_leader_election():
    """测试 Leader 选举"""
    # 创建 3 个节点
    peers = ["node-0", "node-1", "node-2"]
    nodes = [LeaderNode(f"node-{i}", peers) for i in range(3)]

    # 启动所有节点
    for node in nodes:
        node.start()

    # 节点 0 开始选举
    leader = nodes[0].start_election()

    # 验证选举结果
    assert leader, "Expected node 0 to win election"
    assert nodes[0].is_leader, "Expected node 0 to be leader"

    # 停止所有节点
    for node in nodes:
        node.stop()


def test_leader_failover():
    """测试 Leader 故障转移"""
    # 创建 5 个节点
    peers = ["node-0", "node-1", "node-2", "node-3", "node-4"]
    nodes = [LeaderNode(f"node-{i}", peers) for i in range(5)]

    # 启动所有节点
    for node in nodes:
        node.start()

    # 节点 0 成为 Leader
    nodes[0].start_election()
    assert nodes[0].is_leader, "Expected node 0 to be leader"

    # 模拟 Leader 故障
    nodes[0].stop()

    # 等待超时
    time.sleep(0.2)

    # 节点 1 开始选举
    nodes[1].start_election()

    # 验证新 Leader
    assert nodes[1].is_leader, "Expected node 1 to become leader"

    # 停止所有节点
    for node in nodes:
        node.stop()


def test_log_append():
    """测试日志追加"""
    log = PaxosLog()

    # 追加日志条目
    entry = LogEntry(
        slot_id=1,
        proposal_id=ProposalID(number=1, node_id="node-1"),
        value="value-1",
    )
    log.append(entry)

    # 验证
    retrieved = log.get(1)
    assert retrieved is not None, "Expected to get log entry"
    assert retrieved.value == "value-1", f"Expected 'value-1', got {retrieved.value}"


def test_log_commit():
    """测试日志提交"""
    log = PaxosLog()

    # 追加日志条目
    entry = LogEntry(
        slot_id=1,
        proposal_id=ProposalID(number=1, node_id="node-1"),
        value="value-1",
    )
    log.append(entry)

    # 提交
    log.commit(1)

    # 验证
    retrieved = log.get(1)
    assert retrieved.committed, "Expected entry to be committed"
    assert log.commit_index == 1, f"Expected commit index 1, got {log.commit_index}"


def test_log_entries():
    """测试日志条目获取"""
    log = PaxosLog()

    # 追加多个日志条目
    for i in range(1, 6):
        entry = LogEntry(
            slot_id=i,
            proposal_id=ProposalID(number=1, node_id="node-1"),
            value=f"value-{i}",
        )
        log.append(entry)

    # 获取范围内的条目
    entries = log.get_entries(2, 4)
    assert len(entries) == 3, f"Expected 3 entries, got {len(entries)}"


def test_replicator():
    """测试复制器"""
    log = PaxosLog()
    peers = ["node-1", "node-2"]

    replicator = Replicator("node-0", peers, log)
    replicator.start()

    # 创建日志条目
    entries = [
        LogEntry(
            slot_id=i,
            proposal_id=ProposalID(number=1, node_id="node-0"),
            value=f"value-{i}",
        )
        for i in range(1, 3)
    ]

    # 复制
    replicator.replicate(entries)

    # 等待复制完成
    time.sleep(0.1)

    # 验证
    assert log.last_index == 2, f"Expected last index 2, got {log.last_index}"

    replicator.stop()


def test_concurrent_log_append():
    """测试并发日志追加"""
    import threading

    log = PaxosLog()

    def append_entry(idx):
        entry = LogEntry(
            slot_id=idx,
            proposal_id=ProposalID(number=1, node_id="node-1"),
            value=f"value-{idx}",
        )
        log.append(entry)

    # 并发追加
    threads = [threading.Thread(target=append_entry, args=(i,)) for i in range(100)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # 验证
    assert log.last_index == 99, f"Expected last index 99, got {log.last_index}"


def test_leader_state():
    """测试 Leader 状态"""
    peers = ["node-1", "node-2"]
    node = LeaderNode("node-0", peers)

    # 初始状态应该是 Follower
    assert node.state == LeaderState.FOLLOWER, f"Expected FOLLOWER, got {node.state}"

    # 开始选举
    node.start_election()

    # 应该成为 Leader
    assert node.is_leader, "Expected to be leader"


def test_leader_term():
    """测试 Leader 任期"""
    peers = ["node-1", "node-2"]
    node = LeaderNode("node-0", peers)

    # 初始任期应该是 0
    assert node.term == 0, f"Expected term 0, got {node.term}"

    # 开始选举
    node.start_election()

    # 任期应该增加
    assert node.term >= 1, f"Expected term >= 1, got {node.term}"


def test_proposal_id_comparison():
    """测试 ProposalID 比较"""
    id1 = ProposalID(number=1, node_id="node-1")
    id2 = ProposalID(number=2, node_id="node-1")
    id3 = ProposalID(number=1, node_id="node-2")

    assert id2.is_greater_than(id1), "Expected id2 > id1"
    assert not id1.is_greater_than(id2), "Expected id1 < id2"
    assert id3.is_greater_than(id1), "Expected id3 > id1 (same number, different node)"


def test_log_performance():
    """性能测试"""
    log = PaxosLog()

    start = time.time()
    count = 1000
    for i in range(count):
        entry = LogEntry(
            slot_id=i,
            proposal_id=ProposalID(number=1, node_id="node-1"),
            value=f"value-{i}",
        )
        log.append(entry)
    elapsed = time.time() - start

    print(f"\nLog append performance: {count} entries in {elapsed:.3f}s ({count/elapsed:.0f} ops/s)")


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])

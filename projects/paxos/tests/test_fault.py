"""故障处理测试"""

import time
import threading
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fault.health import ProposerHealthChecker
from src.fault.recovery import AcceptorRecovery, ProposalID, AcceptorState
from src.fault.partition import PartitionDetector, NetworkSimulator


def test_proposer_health_checker():
    """测试 Proposer 健康检查"""
    checker = ProposerHealthChecker(timeout=0.1)

    # 设置故障回调来跟踪
    failed_proposers = []
    checker.set_on_failure(lambda pid: failed_proposers.append(pid))

    # 注册 Proposer
    checker.register_proposer("proposer-1")
    checker.register_proposer("proposer-2")
    checker.register_proposer("proposer-3")

    # 启动检查器
    checker.start()

    # 发送心跳
    checker.heartbeat("proposer-1")
    checker.heartbeat("proposer-2")

    # 等待足够长让检查触发并标记无心跳的 proposer-3 为死
    time.sleep(0.3)

    # 验证 proposer-3 被检测为故障
    assert "proposer-3" in failed_proposers, "Expected proposer-3 to be detected as failed"
    assert not checker.is_alive("proposer-3"), "Expected proposer-3 to be dead"

    checker.stop()

    checker.stop()


def test_proposer_health_checker_recovery():
    """测试 Proposer 恢复"""
    checker = ProposerHealthChecker(timeout=0.1)

    # 设置回调
    failure_detected = threading.Event()
    recovery_detected = threading.Event()

    checker.set_on_failure(lambda _: failure_detected.set())
    checker.set_on_recover(lambda _: recovery_detected.set())

    # 注册 Proposer
    checker.register_proposer("proposer-1")

    # 启动检查器
    checker.start()

    # 发送心跳
    checker.heartbeat("proposer-1")

    # 等待故障检测
    failure_detected.wait(timeout=0.3)
    assert failure_detected.is_set(), "Expected failure to be detected"

    # 发送心跳恢复
    checker.heartbeat("proposer-1")

    # 验证恢复
    recovery_detected.wait(timeout=0.1)
    assert recovery_detected.is_set(), "Expected recovery to be detected"

    checker.stop()


def test_acceptor_recovery():
    """测试 Acceptor 恢复"""
    recovery = AcceptorRecovery("acceptor-1")

    # 设置恢复回调
    recovery_start = threading.Event()
    recovery_end = threading.Event()

    recovery.set_on_recovery_start(lambda _: recovery_start.set())
    recovery.set_on_recovery_end(lambda _, __: recovery_end.set())

    # 保存快照
    proposal_id = ProposalID(number=1, node_id="node-1")
    state = AcceptorState(
        promised_id=proposal_id,
        accepted_id=proposal_id,
        accepted_value="value-1",
    )
    recovery.save_snapshot(state)

    # 追加日志
    recovery.append_log("promise", ProposalID(number=2, node_id="node-2"))
    recovery.append_log("accept", {
        "proposal_id": ProposalID(number=2, node_id="node-2"),
        "value": "value-2",
    })

    # 恢复
    recovered_state = recovery.recover()

    # 验证恢复结果
    assert recovered_state is not None, "Expected recovered state"
    assert recovered_state.accepted_value == "value-2", f"Expected 'value-2', got {recovered_state.accepted_value}"

    # 验证回调
    assert recovery_start.is_set(), "Expected recovery start callback"
    assert recovery_end.is_set(), "Expected recovery end callback"


def test_acceptor_recovery_no_snapshot():
    """测试无快照恢复"""
    recovery = AcceptorRecovery("acceptor-1")

    # 恢复（无快照）
    recovered_state = recovery.recover()

    # 应该返回 None
    assert recovered_state is None, "Expected None state"


def test_recovery_log():
    """测试恢复日志"""
    from src.fault.recovery import RecoveryLog, LogEntry

    log = RecoveryLog()

    # 追加日志
    now = time.time()
    log.append(LogEntry(timestamp=now, operation="promise", data="data-1"))
    log.append(LogEntry(timestamp=now + 1, operation="accept", data="data-2"))
    log.append(LogEntry(timestamp=now + 2, operation="promise", data="data-3"))

    # 获取指定时间之后的日志
    entries = log.get_entries(now + 0.5)
    assert len(entries) == 2, f"Expected 2 entries, got {len(entries)}"

    # 清空日志
    log.clear()
    entries = log.get_entries(0)
    assert len(entries) == 0, f"Expected 0 entries after clear, got {len(entries)}"


def test_partition_detector():
    """测试分区检测"""
    peers = ["node-1", "node-2", "node-3"]
    detector = PartitionDetector("node-0", peers)

    # 设置回调
    partition_detected = threading.Event()
    partition_resolved = threading.Event()
    partitioned_nodes = []
    resolved_nodes = []

    detector.set_on_partition_detected(lambda nodes: (
        partition_detected.set(),
        partitioned_nodes.extend(nodes)
    ))
    detector.set_on_partition_resolved(lambda nodes: (
        partition_resolved.set(),
        resolved_nodes.extend(nodes)
    ))

    # 启动检测器
    detector.start()

    # 发送心跳
    detector.heartbeat("node-1")
    detector.heartbeat("node-2")

    # 模拟分区
    detector.simulate_partition("node-3")

    # 等待检测
    time.sleep(0.1)

    # 验证分区
    assert "node-3" in detector.get_partitioned_nodes(), "Expected node-3 to be partitioned"

    # 解除分区
    detector.resolve_partition("node-3")

    # 验证分区恢复
    assert not detector.has_partition, "Expected no partition"

    detector.stop()


def test_partition_detector_methods():
    """测试分区检测器方法"""
    peers = ["node-1", "node-2", "node-3"]
    detector = PartitionDetector("node-0", peers)

    detector.start()

    # 发送心跳
    for peer in peers:
        detector.heartbeat(peer)

    # 模拟分区
    detector.simulate_partition("node-2")
    detector.simulate_partition("node-3")

    # 验证方法
    assert detector.is_partitioned("node-2"), "Expected node-2 to be partitioned"
    assert detector.is_partitioned("node-3"), "Expected node-3 to be partitioned"
    assert not detector.is_partitioned("node-1"), "Expected node-1 to not be partitioned"

    # 验证计数
    assert detector.partition_count == 2, f"Expected 2 partitions, got {detector.partition_count}"

    # 验证节点列表
    assert len(detector.get_partitioned_nodes()) == 2, "Expected 2 partitioned nodes"
    assert len(detector.get_connected_nodes()) == 1, "Expected 1 connected node"

    # 验证 has_partition
    assert detector.has_partition, "Expected to have partition"

    detector.stop()


def test_network_simulator():
    """测试网络模拟器"""
    simulator = NetworkSimulator()

    # 设置延迟
    simulator.set_latency("node-1", 0.05)

    # 模拟分区
    simulator.simulate_partition("node-3")

    # 验证延迟
    assert simulator.get_latency("node-1") == 0.05, "Expected 50ms latency"

    # 验证分区
    assert simulator.should_drop("node-3"), "Expected node-3 to be dropped"

    # 解除分区
    simulator.resolve_partition("node-3")
    assert not simulator.should_drop("node-3"), "Expected node-3 to not be dropped"


def test_network_simulator_delay():
    """测试网络延迟模拟"""
    simulator = NetworkSimulator()
    simulator.set_latency("node-1", 0.05)

    start = time.time()
    simulator.simulate_delay("node-1")
    elapsed = time.time() - start

    assert elapsed >= 0.05, f"Expected at least 50ms delay, got {elapsed}s"


def test_concurrent_health_checker():
    """测试并发健康检查"""
    checker = ProposerHealthChecker(timeout=0.1)

    # 注册多个 Proposer
    for i in range(10):
        checker.register_proposer(f"proposer-{i}")

    checker.start()

    # 并发发送心跳
    def send_heartbeats(idx):
        for _ in range(10):
            checker.heartbeat(f"proposer-{idx}")
            time.sleep(0.01)

    threads = [threading.Thread(target=send_heartbeats, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # 验证所有 Proposer 都存活
    assert checker.alive_count == 10, f"Expected 10 alive, got {checker.alive_count}"

    checker.stop()


def test_concurrent_partition_detection():
    """测试并发分区检测"""
    peers = ["node-1", "node-2", "node-3", "node-4", "node-5"]
    detector = PartitionDetector("node-0", peers)

    detector.start()

    # 并发发送心跳
    def send_heartbeats(peer):
        for _ in range(10):
            detector.heartbeat(peer)
            time.sleep(0.01)

    threads = [threading.Thread(target=send_heartbeats, args=(p,)) for p in peers]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    detector.stop()


def test_health_checker_performance():
    """性能测试"""
    checker = ProposerHealthChecker(timeout=0.1)

    for i in range(100):
        checker.register_proposer(f"proposer-{i}")

    checker.start()

    start = time.time()
    count = 1000
    for i in range(count):
        checker.heartbeat(f"proposer-{i % 100}")
    elapsed = time.time() - start

    print(f"\nHealth checker performance: {count} heartbeats in {elapsed:.3f}s ({count/elapsed:.0f} ops/s)")

    checker.stop()


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])

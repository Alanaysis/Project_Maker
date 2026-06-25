"""网络分区检测和模拟"""

import logging
import random
import threading
import time
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class PartitionDetector:
    """网络分区检测器

    通过心跳检测网络分区。
    """

    def __init__(self, node_id: str, peers: List[str]):
        self._node_id = node_id
        self._peers = peers

        self._lock = threading.RLock()
        self._heartbeats: Dict[str, float] = {}
        self._partitions: Dict[str, bool] = {}

        # 配置
        self._heartbeat_timeout = 2.0  # 2s
        self._check_interval = 0.5  # 500ms

        # 控制
        self._running = False
        self._stop_event = threading.Event()

        # 回调
        self._on_partition_detected: Optional[Callable[[List[str]], None]] = None
        self._on_partition_resolved: Optional[Callable[[List[str]], None]] = None

    def start(self) -> None:
        """启动分区检测器"""
        self._running = True
        self._stop_event.clear()
        logger.info(f"[PartitionDetector {self._node_id}] Started")

        # 初始化心跳记录
        for peer in self._peers:
            self._heartbeats[peer] = time.time()
            self._partitions[peer] = False

        # 启动检测循环
        t = threading.Thread(target=self._check_loop, daemon=True)
        t.start()

    def stop(self) -> None:
        """停止分区检测器"""
        self._running = False
        self._stop_event.set()
        logger.info(f"[PartitionDetector {self._node_id}] Stopped")

    def heartbeat(self, peer_id: str) -> None:
        """接收心跳"""
        with self._lock:
            was_partitioned = self._partitions.get(peer_id, False)
            self._heartbeats[peer_id] = time.time()
            self._partitions[peer_id] = False

            if was_partitioned:
                logger.info(f"[PartitionDetector {self._node_id}] Partition resolved with {peer_id}")
                if self._on_partition_resolved:
                    self._on_partition_resolved([peer_id])

    def _check_loop(self) -> None:
        """检查循环"""
        while self._running:
            self._stop_event.wait(timeout=self._check_interval)
            if self._stop_event.is_set():
                return
            self._check_partitions()

    def _check_partitions(self) -> None:
        """检查分区"""
        with self._lock:
            now = time.time()
            partitioned = []
            resolved = []

            for peer in self._peers:
                last_heartbeat = self._heartbeats.get(peer, 0)
                is_partitioned = now - last_heartbeat > self._heartbeat_timeout

                if is_partitioned and not self._partitions.get(peer, False):
                    # 检测到新分区
                    self._partitions[peer] = True
                    partitioned.append(peer)
                    logger.info(f"[PartitionDetector {self._node_id}] Partition detected with {peer}")
                elif not is_partitioned and self._partitions.get(peer, False):
                    # 分区恢复
                    self._partitions[peer] = False
                    resolved.append(peer)
                    logger.info(f"[PartitionDetector {self._node_id}] Partition resolved with {peer}")

            # 触发回调
            if partitioned and self._on_partition_detected:
                self._on_partition_detected(partitioned)
            if resolved and self._on_partition_resolved:
                self._on_partition_resolved(resolved)

    def is_partitioned(self, peer_id: str) -> bool:
        """检查是否与指定节点分区"""
        with self._lock:
            return self._partitions.get(peer_id, False)

    def get_partitioned_nodes(self) -> List[str]:
        """获取分区的节点"""
        with self._lock:
            return [p for p, is_p in self._partitions.items() if is_p]

    def get_connected_nodes(self) -> List[str]:
        """获取连接的节点"""
        with self._lock:
            return [p for p, is_p in self._partitions.items() if not is_p]

    @property
    def has_partition(self) -> bool:
        """检查是否有分区"""
        with self._lock:
            return any(self._partitions.values())

    @property
    def partition_count(self) -> int:
        """获取分区数量"""
        with self._lock:
            return sum(1 for v in self._partitions.values() if v)

    def simulate_partition(self, peer_id: str) -> None:
        """模拟分区"""
        with self._lock:
            self._partitions[peer_id] = True
            logger.info(f"[PartitionDetector {self._node_id}] Simulated partition with {peer_id}")

    def resolve_partition(self, peer_id: str) -> None:
        """解除分区"""
        with self._lock:
            self._partitions[peer_id] = False
            self._heartbeats[peer_id] = time.time()
            logger.info(f"[PartitionDetector {self._node_id}] Resolved partition with {peer_id}")

    def set_on_partition_detected(self, callback: Callable[[List[str]], None]) -> None:
        """设置分区检测回调"""
        self._on_partition_detected = callback

    def set_on_partition_resolved(self, callback: Callable[[List[str]], None]) -> None:
        """设置分区恢复回调"""
        self._on_partition_resolved = callback


class NetworkSimulator:
    """网络模拟器

    模拟网络延迟、丢包和分区。
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._latency: Dict[str, float] = {}
        self._loss_rate: Dict[str, float] = {}
        self._partitions: Dict[str, bool] = {}

    def set_latency(self, peer_id: str, latency: float) -> None:
        """设置延迟（秒）"""
        with self._lock:
            self._latency[peer_id] = latency

    def set_loss_rate(self, peer_id: str, rate: float) -> None:
        """设置丢包率（0-1）"""
        with self._lock:
            self._loss_rate[peer_id] = rate

    def simulate_partition(self, peer_id: str) -> None:
        """模拟分区"""
        with self._lock:
            self._partitions[peer_id] = True

    def resolve_partition(self, peer_id: str) -> None:
        """解除分区"""
        with self._lock:
            self._partitions.pop(peer_id, None)

    def should_drop(self, peer_id: str) -> bool:
        """检查是否应该丢包"""
        with self._lock:
            # 检查分区
            if self._partitions.get(peer_id, False):
                return True

            # 检查丢包率
            rate = self._loss_rate.get(peer_id, 0)
            return random.random() < rate

    def get_latency(self, peer_id: str) -> float:
        """获取延迟"""
        with self._lock:
            return self._latency.get(peer_id, 0)

    def simulate_delay(self, peer_id: str) -> None:
        """模拟网络延迟"""
        latency = self.get_latency(peer_id)
        if latency > 0:
            time.sleep(latency)

"""Leader 选举实现"""

import logging
import random
import threading
import time
from typing import Callable, Dict, List, Optional

from .types import (
    ProposalID, LogEntry, LeaderState,
    VoteRequest, VoteResponse,
    HeartbeatRequest, HeartbeatResponse,
    AppendEntriesRequest, AppendEntriesResponse,
)
from .log import PaxosLog

logger = logging.getLogger(__name__)


class LeaderNode:
    """Leader 节点

    实现 Leader 选举和心跳机制。
    """

    def __init__(self, node_id: str, peers: List[str]):
        self.id = node_id
        self._lock = threading.Lock()
        self._state = LeaderState.FOLLOWER
        self._term = 0

        self._peers = peers
        self._votes: Dict[str, bool] = {}
        self._heartbeats: Dict[str, float] = {}

        self._log = PaxosLog()

        # 配置
        self._election_timeout = 0.15  # 150ms
        self._heartbeat_timeout = 0.05  # 50ms

        # 回调
        self._on_state_change: Optional[Callable] = None
        self._on_leader_elected: Optional[Callable] = None

        # 控制
        self._running = False
        self._stop_event = threading.Event()
        self._election_thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """启动节点"""
        self._running = True
        self._stop_event.clear()
        logger.info(f"[Leader {self.id}] Started as {self._state}")

        # 启动选举超时检测
        self._election_thread = threading.Thread(target=self._election_timeout_loop, daemon=True)
        self._election_thread.start()

    def stop(self) -> None:
        """停止节点"""
        self._running = False
        self._stop_event.set()
        logger.info(f"[Leader {self.id}] Stopped")

    def start_election(self) -> bool:
        """开始选举"""
        with self._lock:
            # 转换为 Candidate 状态
            old_state = self._state
            self._state = LeaderState.CANDIDATE
            self._term += 1
            self._votes = {self.id: True}  # 投票给自己

            logger.info(f"[Leader {self.id}] Starting election for term {self._term}")

            if self._on_state_change:
                self._on_state_change(old_state, LeaderState.CANDIDATE)

            term = self._term

        # 请求其他节点投票（模拟）
        for peer in self._peers:
            self._request_vote(peer, term)

        # 等待投票结果
        time.sleep(self._election_timeout)

        with self._lock:
            # 检查是否获得多数派投票
            vote_count = len(self._votes)
            quorum_size = (len(self._peers) + 1) // 2 + 1

            if vote_count >= quorum_size:
                old_state = self._state
                self._state = LeaderState.LEADER
                logger.info(f"[Leader {self.id}] Won election with {vote_count} votes "
                           f"(needed {quorum_size})")

                if self._on_state_change:
                    self._on_state_change(old_state, LeaderState.LEADER)

                if self._on_leader_elected:
                    self._on_leader_elected(self.id)

                # 开始发送心跳
                self._start_heartbeat()
                return True

            # 选举失败
            old_state = self._state
            self._state = LeaderState.FOLLOWER
            logger.info(f"[Leader {self.id}] Lost election with {vote_count} votes "
                       f"(needed {quorum_size})")

            if self._on_state_change:
                self._on_state_change(old_state, LeaderState.FOLLOWER)

            return False

    def _request_vote(self, peer: str, term: int) -> None:
        """请求投票（模拟）"""
        # 在实际实现中，这里会发送 RPC 请求
        with self._lock:
            self._votes[peer] = True

    def handle_vote_request(self, args: VoteRequest) -> VoteResponse:
        """处理投票请求"""
        with self._lock:
            reply = VoteResponse(term=self._term, vote_granted=False, node_id=self.id)

            # 如果请求的任期小于当前任期，拒绝投票
            if args.term < self._term:
                return reply

            # 如果请求的任期大于当前任期，更新任期并转为 Follower
            if args.term > self._term:
                self._term = args.term
                self._state = LeaderState.FOLLOWER

            # 检查日志是否至少一样新
            last_index = self._log.last_index
            last_term = self._log.last_term

            log_is_up_to_date = (
                args.last_log_term > last_term or
                (args.last_log_term == last_term and args.last_log_index >= last_index)
            )

            # 投票给候选人
            reply.vote_granted = log_is_up_to_date
            reply.term = self._term

            if reply.vote_granted:
                logger.info(f"[Leader {self.id}] Voted for {args.candidate_id} in term {args.term}")

            return reply

    def _start_heartbeat(self) -> None:
        """开始发送心跳"""
        def heartbeat_loop():
            while self._running and self._state == LeaderState.LEADER:
                self._send_heartbeats()
                time.sleep(self._heartbeat_timeout)

        t = threading.Thread(target=heartbeat_loop, daemon=True)
        t.start()

    def _send_heartbeats(self) -> None:
        """发送心跳"""
        with self._lock:
            if self._state != LeaderState.LEADER:
                return
            term = self._term

        for peer in self._peers:
            self._send_heartbeat(peer, term)

    def _send_heartbeat(self, peer: str, term: int) -> None:
        """发送心跳到指定节点"""
        # 模拟心跳
        with self._lock:
            self._heartbeats[peer] = time.time()

    def handle_heartbeat(self, args: HeartbeatRequest) -> HeartbeatResponse:
        """处理心跳"""
        with self._lock:
            reply = HeartbeatResponse(term=self._term, success=False, node_id=self.id)

            # 如果心跳的任期小于当前任期，拒绝
            if args.term < self._term:
                return reply

            # 更新任期并转为 Follower
            self._term = args.term
            self._state = LeaderState.FOLLOWER
            reply.success = True
            reply.term = self._term

            logger.info(f"[Leader {self.id}] Received heartbeat from {args.leader_id}, "
                       f"becoming Follower")

            return reply

    def append_entries(self, entries: List[LogEntry]) -> None:
        """追加日志条目"""
        with self._lock:
            if self._state != LeaderState.LEADER:
                raise RuntimeError("Not leader")

        # 追加到本地日志
        for entry in entries:
            self._log.append(entry)

        logger.info(f"[Leader {self.id}] Appended {len(entries)} entries")

    def _election_timeout_loop(self) -> None:
        """选举超时检测循环"""
        while self._running:
            self._stop_event.wait(timeout=self._election_timeout)
            if self._stop_event.is_set():
                return

            with self._lock:
                if self._state == LeaderState.FOLLOWER:
                    # 检查是否收到心跳
                    if self.id not in self._heartbeats:
                        self._lock.release()
                        self.start_election()
                        self._lock.acquire()
                    elif time.time() - self._heartbeats[self.id] > self._election_timeout:
                        self._lock.release()
                        self.start_election()
                        self._lock.acquire()

    @property
    def state(self) -> LeaderState:
        """获取节点状态"""
        with self._lock:
            return self._state

    @property
    def term(self) -> int:
        """获取当前任期"""
        with self._lock:
            return self._term

    @property
    def is_leader(self) -> bool:
        """检查是否是 Leader"""
        with self._lock:
            return self._state == LeaderState.LEADER

    @property
    def log(self) -> PaxosLog:
        """获取日志"""
        return self._log

    def set_on_state_change(self, callback: Callable) -> None:
        """设置状态变化回调"""
        self._on_state_change = callback

    def set_on_leader_elected(self, callback: Callable) -> None:
        """设置 Leader 选举回调"""
        self._on_leader_elected = callback


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    print("=== Multi Paxos Leader Election Example ===")

    # 创建 3 个节点
    peers = ["node-0", "node-1", "node-2"]
    nodes = [LeaderNode(f"node-{i}", peers) for i in range(3)]

    # 启动所有节点
    for node in nodes:
        node.start()

    # 节点 0 开始选举
    leader = nodes[0].start_election()
    if leader:
        print(f"Node {nodes[0].id} became leader")

    # 验证其他节点状态
    for node in nodes[1:]:
        print(f"Node {node.id}: {node.state} (term {node.term})")

    # 停止所有节点
    for node in nodes:
        node.stop()

    print("\n=== Example Complete ===")

"""日志复制器实现"""

import logging
import threading
import time
from typing import Dict, List, Optional

from .types import LogEntry, AppendEntriesRequest, AppendEntriesResponse
from .log import PaxosLog

logger = logging.getLogger(__name__)


class Replicator:
    """日志复制器

    负责将 Leader 的日志复制到其他节点。
    """

    def __init__(self, leader_id: str, peers: List[str], log: PaxosLog):
        self._leader_id = leader_id
        self._peers = peers
        self._log = log

        self._lock = threading.Lock()
        self._match_index: Dict[str, int] = {p: 0 for p in peers}
        self._next_index: Dict[str, int] = {p: 1 for p in peers}

        # 配置
        self._replication_timeout = 0.1  # 100ms
        self._max_entries_per_batch = 100

        # 控制
        self._running = False
        self._stop_event = threading.Event()
        self._replication_thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """启动复制器"""
        self._running = True
        self._stop_event.clear()
        logger.info(f"[Replicator {self._leader_id}] Started")

        # 启动复制循环
        self._replication_thread = threading.Thread(target=self._replication_loop, daemon=True)
        self._replication_thread.start()

    def stop(self) -> None:
        """停止复制器"""
        self._running = False
        self._stop_event.set()
        logger.info(f"[Replicator {self._leader_id}] Stopped")

    def replicate(self, entries: List[LogEntry]) -> None:
        """复制日志条目"""
        if not self._running:
            raise RuntimeError("Replicator stopped")

        # 追加到本地日志
        for entry in entries:
            self._log.append(entry)

        # 复制到其他节点
        self._replicate_to_all(entries)

    def _replicate_to_all(self, entries: List[LogEntry]) -> None:
        """复制到所有节点"""
        threads = []
        for peer in self._peers:
            t = threading.Thread(target=self._replicate_to_peer, args=(peer, entries))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

    def _replicate_to_peer(self, peer: str, entries: List[LogEntry]) -> None:
        """复制到指定节点"""
        with self._lock:
            next_idx = self._next_index[peer]
            prev_log_index = next_idx - 1

        # 准备请求
        args = AppendEntriesRequest(
            term=self._log.last_term,
            leader_id=self._leader_id,
            prev_log_index=prev_log_index,
            prev_log_term=self._log.last_term,
            entries=entries,
            leader_commit=self._log.commit_index,
        )

        # 发送请求（模拟）
        reply = self._handle_append_entries(peer, args)

        with self._lock:
            if reply.success:
                self._match_index[peer] = reply.match_index
                self._next_index[peer] = reply.match_index + 1
                logger.debug(f"[Replicator {self._leader_id}] Replicated to {peer}, "
                            f"matchIndex={reply.match_index}")
            else:
                # 复制失败，减少下一个索引
                if self._next_index[peer] > 1:
                    self._next_index[peer] -= 1
                logger.debug(f"[Replicator {self._leader_id}] Failed to replicate to {peer}, "
                            f"nextIndex={self._next_index[peer]}")

    def _handle_append_entries(self, peer: str, args: AppendEntriesRequest) -> AppendEntriesResponse:
        """模拟追加条目请求"""
        # 在实际实现中，这里会发送 RPC 请求
        return AppendEntriesResponse(
            term=args.term,
            success=True,
            node_id=peer,
            match_index=args.prev_log_index + len(args.entries),
        )

    def _replication_loop(self) -> None:
        """复制循环"""
        while self._running:
            self._stop_event.wait(timeout=self._replication_timeout)
            if self._stop_event.is_set():
                return

            # 检查是否需要复制
            self._check_and_replicate()

    def _check_and_replicate(self) -> None:
        """检查并复制"""
        with self._lock:
            last_index = self._log.last_index

            for peer in self._peers:
                next_idx = self._next_index[peer]
                if next_idx <= last_index:
                    # 需要复制
                    entries = self._log.get_entries(next_idx, last_index)
                    if entries:
                        t = threading.Thread(target=self._replicate_to_peer, args=(peer, entries))
                        t.start()

    def get_match_index(self, peer: str) -> int:
        """获取匹配索引"""
        with self._lock:
            return self._match_index[peer]

    def get_next_index(self, peer: str) -> int:
        """获取下一个索引"""
        with self._lock:
            return self._next_index[peer]

    def update_commit_index(self) -> int:
        """更新提交索引"""
        with self._lock:
            # 找到多数派匹配的索引
            majority_index = 0
            for peer in self._peers:
                match_idx = self._match_index[peer]
                count = 1  # 包括自己
                for other_peer in self._peers:
                    if other_peer != peer and self._match_index[other_peer] >= match_idx:
                        count += 1
                quorum_size = (len(self._peers) + 1) // 2 + 1
                if count >= quorum_size and match_idx > majority_index:
                    majority_index = match_idx

            # 更新提交索引
            if majority_index > self._log.commit_index:
                for i in range(self._log.commit_index + 1, majority_index + 1):
                    self._log.commit(i)
                logger.info(f"[Replicator {self._leader_id}] Updated commit index to {majority_index}")

            return majority_index

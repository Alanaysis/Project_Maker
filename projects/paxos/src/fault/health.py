"""Proposer 健康检查器"""

import logging
import threading
import time
from typing import Callable, Dict, Optional

logger = logging.getLogger(__name__)


class ProposerStatus:
    """Proposer 状态"""

    def __init__(self, proposer_id: str):
        self.id = proposer_id
        self.last_active = time.time()
        self.is_alive = True
        self.failures = 0


class ProposerHealthChecker:
    """Proposer 健康检查器

    定期检查 Proposer 的心跳，检测故障和恢复。
    """

    def __init__(self, timeout: float = 0.1):
        self._lock = threading.RLock()
        self._proposers: Dict[str, ProposerStatus] = {}
        self._timeout = timeout

        # 控制
        self._running = False
        self._stop_event = threading.Event()
        self._check_thread: Optional[threading.Thread] = None

        # 回调
        self._on_failure: Optional[Callable[[str], None]] = None
        self._on_recover: Optional[Callable[[str], None]] = None

    def register_proposer(self, proposer_id: str) -> None:
        """注册 Proposer"""
        with self._lock:
            self._proposers[proposer_id] = ProposerStatus(proposer_id)
            logger.info(f"[HealthChecker] Registered proposer {proposer_id}")

    def unregister_proposer(self, proposer_id: str) -> None:
        """注销 Proposer"""
        with self._lock:
            self._proposers.pop(proposer_id, None)
            logger.info(f"[HealthChecker] Unregistered proposer {proposer_id}")

    def heartbeat(self, proposer_id: str) -> None:
        """接收心跳"""
        with self._lock:
            if proposer_id in self._proposers:
                status = self._proposers[proposer_id]
                was_alive = status.is_alive
                status.last_active = time.time()
                status.is_alive = True
                status.failures = 0

                if not was_alive:
                    logger.info(f"[HealthChecker] Proposer {proposer_id} recovered")
                    if self._on_recover:
                        self._on_recover(proposer_id)

    def start(self) -> None:
        """启动健康检查"""
        self._running = True
        self._stop_event.clear()
        logger.info(f"[HealthChecker] Started with timeout {self._timeout}")

        self._check_thread = threading.Thread(target=self._check_loop, daemon=True)
        self._check_thread.start()

    def stop(self) -> None:
        """停止健康检查"""
        self._running = False
        self._stop_event.set()
        logger.info(f"[HealthChecker] Stopped")

    def _check_loop(self) -> None:
        """检查循环"""
        while self._running:
            self._stop_event.wait(timeout=self._timeout)
            if self._stop_event.is_set():
                return
            self._check_all()

    def _check_all(self) -> None:
        """检查所有 Proposer"""
        with self._lock:
            now = time.time()
            for proposer_id, status in self._proposers.items():
                if status.is_alive and now - status.last_active > self._timeout:
                    status.is_alive = False
                    status.failures += 1
                    logger.info(f"[HealthChecker] Proposer {proposer_id} is down "
                               f"(failures: {status.failures})")

                    if self._on_failure:
                        self._on_failure(proposer_id)

    def get_status(self, proposer_id: str) -> Optional[ProposerStatus]:
        """获取 Proposer 状态"""
        with self._lock:
            return self._proposers.get(proposer_id)

    def get_all_status(self) -> Dict[str, ProposerStatus]:
        """获取所有 Proposer 状态"""
        with self._lock:
            return dict(self._proposers)

    def is_alive(self, proposer_id: str) -> bool:
        """检查 Proposer 是否存活"""
        with self._lock:
            status = self._proposers.get(proposer_id)
            return status.is_alive if status else False

    @property
    def alive_count(self) -> int:
        """获取存活的 Proposer 数量"""
        with self._lock:
            return sum(1 for s in self._proposers.values() if s.is_alive)

    @property
    def dead_count(self) -> int:
        """获取死亡的 Proposer 数量"""
        with self._lock:
            return sum(1 for s in self._proposers.values() if not s.is_alive)

    def set_on_failure(self, callback: Callable[[str], None]) -> None:
        """设置故障回调"""
        self._on_failure = callback

    def set_on_recover(self, callback: Callable[[str], None]) -> None:
        """设置恢复回调"""
        self._on_recover = callback

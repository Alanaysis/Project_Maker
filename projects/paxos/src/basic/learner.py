"""Learner 学习者实现"""

import logging
import threading
from typing import Any, Callable, Dict, Optional

from .types import ProposalID, AcceptedArgs

logger = logging.getLogger(__name__)


class Learner:
    """Learner 学习者角色

    职责：
    - 接收 Acceptor 的 Accepted 通知
    - 学习已达成共识的值
    """

    def __init__(self, node_id: str, quorum_size: int):
        self.id = node_id
        self._lock = threading.RLock()
        self._quorum_size = quorum_size

        # proposal_id_str -> {acceptor_id -> AcceptedArgs}
        self._accepted: Dict[str, Dict[str, AcceptedArgs]] = {}
        # proposal_id_str -> value
        self._learned: Dict[str, Any] = {}
        self._on_learned: Optional[Callable[[ProposalID, Any], None]] = None

    def set_on_learned(self, callback: Callable[[ProposalID, Any], None]) -> None:
        """设置学习回调"""
        self._on_learned = callback

    def handle_accepted(self, args: AcceptedArgs) -> None:
        """处理 Accepted 通知"""
        with self._lock:
            pid_str = str(args.proposal_id)
            logger.info(f"[Learner {self.id}] Received Accepted notification "
                       f"for proposal {args.proposal_id} from {args.from_id}")

            # 初始化 map
            if pid_str not in self._accepted:
                self._accepted[pid_str] = {}

            # 记录接受信息
            self._accepted[pid_str][args.from_id] = args

            # 检查是否有多数派接受同一值
            accept_count = len(self._accepted[pid_str])

            if accept_count >= self._quorum_size:
                # 检查是否已经学习过
                if pid_str not in self._learned:
                    self._learned[pid_str] = args.value
                    logger.info(f"[Learner {self.id}] Learned value {args.value} "
                               f"for proposal {args.proposal_id} "
                               f"(acceptors: {accept_count}/{self._quorum_size})")

                    # 触发回调
                    if self._on_learned:
                        self._on_learned(args.proposal_id, args.value)

    def get_learned_value(self, proposal_id: ProposalID) -> Optional[Any]:
        """获取已学习的值"""
        with self._lock:
            return self._learned.get(str(proposal_id))

    def get_all_learned(self) -> Dict[str, Any]:
        """获取所有已学习的值"""
        with self._lock:
            return dict(self._learned)

    def get_accept_count(self, proposal_id: ProposalID) -> int:
        """获取接受计数"""
        with self._lock:
            pid_str = str(proposal_id)
            if pid_str not in self._accepted:
                return 0
            return len(self._accepted[pid_str])

    def is_learned(self, proposal_id: ProposalID) -> bool:
        """检查是否已学习"""
        with self._lock:
            return str(proposal_id) in self._learned

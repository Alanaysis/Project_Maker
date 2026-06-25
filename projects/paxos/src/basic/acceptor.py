"""Acceptor 接受者实现"""

import logging
import threading
from typing import Any, Callable, Optional

from .types import ProposalID, PrepareArgs, PrepareReply, AcceptArgs, AcceptReply, AcceptedArgs

logger = logging.getLogger(__name__)


class Acceptor:
    """Acceptor 接受者角色

    职责：
    - 接收 Prepare 请求，承诺不接受编号更小的提案
    - 接收 Accept 请求，接受或拒绝提案
    - 通知 Learner 已接受的提案
    """

    def __init__(self, node_id: str):
        self.id = node_id
        self._lock = threading.RLock()
        self._promised_id: Optional[ProposalID] = None
        self._accepted_id: Optional[ProposalID] = None
        self._accepted_value: Any = None
        self._on_accepted: Optional[Callable[[AcceptedArgs], None]] = None

    def set_on_accepted(self, callback: Callable[[AcceptedArgs], None]) -> None:
        """设置接受回调"""
        self._on_accepted = callback

    def handle_prepare(self, args: PrepareArgs) -> PrepareReply:
        """处理 Prepare 请求

        如果提案号大于已承诺的提案号，承诺不再接受编号更小的提案。
        """
        with self._lock:
            logger.info(f"[Acceptor {self.id}] Received Prepare with proposal {args.proposal_id}")

            reply = PrepareReply(
                promise=False,
                proposal_id=args.proposal_id,
                from_id=self.id
            )

            # 如果提案号大于已承诺的提案号，承诺
            if self._promised_id is None or args.proposal_id.is_greater_than(self._promised_id):
                self._promised_id = args.proposal_id
                reply.promise = True
                reply.accepted_id = self._accepted_id
                reply.accepted_value = self._accepted_value
                logger.info(f"[Acceptor {self.id}] Promised proposal {args.proposal_id}")
            else:
                logger.info(f"[Acceptor {self.id}] Rejected proposal {args.proposal_id} "
                           f"(already promised {self._promised_id})")

            return reply

    def handle_accept(self, args: AcceptArgs) -> AcceptReply:
        """处理 Accept 请求

        如果提案号 >= 已承诺的提案号，接受提案。
        """
        with self._lock:
            logger.info(f"[Acceptor {self.id}] Received Accept with proposal {args.proposal_id}")

            reply = AcceptReply(
                accepted=False,
                proposal_id=args.proposal_id,
                from_id=self.id
            )

            # 如果提案号 >= 已承诺的提案号，接受
            if self._promised_id is None or not self._promised_id.is_greater_than(args.proposal_id):
                self._promised_id = args.proposal_id
                self._accepted_id = args.proposal_id
                self._accepted_value = args.value
                reply.accepted = True
                logger.info(f"[Acceptor {self.id}] Accepted proposal {args.proposal_id} "
                           f"with value {args.value}")

                # 通知 Learner
                if self._on_accepted:
                    self._on_accepted(AcceptedArgs(
                        proposal_id=args.proposal_id,
                        value=args.value,
                        from_id=self.id
                    ))
            else:
                logger.info(f"[Acceptor {self.id}] Rejected proposal {args.proposal_id} "
                           f"(already promised {self._promised_id})")

            return reply

    def get_state(self) -> dict:
        """获取当前状态（用于快照）"""
        with self._lock:
            return {
                'promised_id': self._promised_id,
                'accepted_id': self._accepted_id,
                'accepted_value': self._accepted_value,
            }

    def restore_state(self, state: dict) -> None:
        """恢复状态"""
        with self._lock:
            self._promised_id = state.get('promised_id')
            self._accepted_id = state.get('accepted_id')
            self._accepted_value = state.get('accepted_value')

    @property
    def accepted_value(self) -> Any:
        """获取已接受的值"""
        with self._lock:
            return self._accepted_value

    @property
    def promised_id(self) -> Optional[ProposalID]:
        """获取已承诺的提案ID"""
        with self._lock:
            return self._promised_id

    @property
    def accepted_id(self) -> Optional[ProposalID]:
        """获取已接受的提案ID"""
        with self._lock:
            return self._accepted_id

"""Proposer 提议者实现"""

import logging
import threading
from typing import Any, List, Protocol

from .types import ProposalID, PrepareArgs, PrepareReply, AcceptArgs, AcceptReply

logger = logging.getLogger(__name__)


class AcceptorClient(Protocol):
    """Acceptor 客户端接口"""

    @property
    def id(self) -> str: ...

    def handle_prepare(self, args: PrepareArgs) -> PrepareReply: ...

    def handle_accept(self, args: AcceptArgs) -> AcceptReply: ...


class Proposer:
    """Proposer 提议者角色

    职责：
    - 提出提案
    - 发送 Prepare 和 Accept 请求
    - 处理冲突和重试
    """

    def __init__(self, node_id: str, acceptors: List[AcceptorClient]):
        self.id = node_id
        self._lock = threading.Lock()
        self._proposal_num = 0
        self._acceptors = acceptors
        self._quorum_size = len(acceptors) // 2 + 1

    def propose(self, value: Any) -> Any:
        """提议一个值

        执行两阶段提交：
        1. Prepare 阶段：获取多数派承诺
        2. Accept 阶段：请求多数派接受
        """
        with self._lock:
            self._proposal_num += 1
            proposal_id = ProposalID(number=self._proposal_num, node_id=self.id)

        logger.info(f"[Proposer {self.id}] Starting proposal {proposal_id} with value {value}")

        # Phase 1: Prepare
        promises = self._prepare(proposal_id)

        # 检查是否有多数派 Promise
        if len(promises) < self._quorum_size:
            logger.warning(f"[Proposer {self.id}] Not enough promises: "
                          f"{len(promises)}/{self._quorum_size}")
            raise RuntimeError("Not enough promises")

        # 选择值：如果有已接受的值，选择编号最大的
        value_to_accept = value
        max_accepted_id = ProposalID(number=0, node_id="")
        for promise in promises:
            if (promise.accepted_id is not None and
                    promise.accepted_id.is_greater_than(max_accepted_id)):
                max_accepted_id = promise.accepted_id
                value_to_accept = promise.accepted_value

        logger.info(f"[Proposer {self.id}] Phase 1 complete, "
                    f"proceeding to Accept with value {value_to_accept}")

        # Phase 2: Accept
        accepted_count = self._accept(proposal_id, value_to_accept)

        if accepted_count < self._quorum_size:
            logger.warning(f"[Proposer {self.id}] Not enough accepts: "
                          f"{accepted_count}/{self._quorum_size}")
            raise RuntimeError("Not enough accepts")

        logger.info(f"[Proposer {self.id}] Proposal {proposal_id} accepted "
                    f"with value {value_to_accept}")
        return value_to_accept

    def _prepare(self, proposal_id: ProposalID) -> List[PrepareReply]:
        """执行 Prepare 阶段"""
        promises: List[PrepareReply] = []
        lock = threading.Lock()

        def send_prepare(acceptor: AcceptorClient):
            args = PrepareArgs(proposal_id=proposal_id, to=acceptor.id)
            reply = acceptor.handle_prepare(args)
            if reply.promise:
                with lock:
                    promises.append(reply)

        threads = []
        for acceptor in self._acceptors:
            t = threading.Thread(target=send_prepare, args=(acceptor,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        return promises

    def _accept(self, proposal_id: ProposalID, value: Any) -> int:
        """执行 Accept 阶段"""
        accepted_count = 0
        lock = threading.Lock()

        def send_accept(acceptor: AcceptorClient):
            nonlocal accepted_count
            args = AcceptArgs(proposal_id=proposal_id, value=value, to=acceptor.id)
            reply = acceptor.handle_accept(args)
            if reply.accepted:
                with lock:
                    accepted_count += 1

        threads = []
        for acceptor in self._acceptors:
            t = threading.Thread(target=send_accept, args=(acceptor,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        return accepted_count

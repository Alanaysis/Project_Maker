"""Node 节点实现，组合 Proposer、Acceptor 和 Learner"""

import logging
import threading
from typing import Any, Dict, Optional

from .types import ProposalID, PrepareArgs, PrepareReply, AcceptArgs, AcceptReply, AcceptedArgs
from .acceptor import Acceptor
from .proposer import Proposer
from .learner import Learner

logger = logging.getLogger(__name__)


class Node:
    """Paxos 节点，包含 Proposer、Acceptor 和 Learner 三个角色"""

    def __init__(self, node_id: str, acceptors: list, quorum_size: int):
        self.id = node_id
        self._lock = threading.RLock()
        self._running = False

        # 创建 Acceptor
        self._acceptor = Acceptor(node_id)

        # 创建 Proposer
        self._proposer = Proposer(node_id, acceptors)

        # 创建 Learner
        self._learner = Learner(node_id, quorum_size)

        # 设置 Acceptor 回调，通知 Learner
        self._acceptor.set_on_accepted(self._learner.handle_accepted)

    def propose(self, value: Any) -> Any:
        """提议一个值"""
        return self._proposer.propose(value)

    def handle_prepare(self, args: PrepareArgs) -> PrepareReply:
        """处理 Prepare 请求"""
        return self._acceptor.handle_prepare(args)

    def handle_accept(self, args: AcceptArgs) -> AcceptReply:
        """处理 Accept 请求"""
        return self._acceptor.handle_accept(args)

    def handle_accepted(self, args: AcceptedArgs) -> None:
        """处理 Accepted 通知"""
        self._learner.handle_accepted(args)

    def get_learned_value(self, proposal_id: ProposalID) -> Optional[Any]:
        """获取已学习的值"""
        return self._learner.get_learned_value(proposal_id)

    def get_all_learned(self) -> Dict[str, Any]:
        """获取所有已学习的值"""
        return self._learner.get_all_learned()

    @property
    def acceptor(self) -> Acceptor:
        """获取 Acceptor"""
        return self._acceptor

    @property
    def proposer(self) -> Proposer:
        """获取 Proposer"""
        return self._proposer

    @property
    def learner(self) -> Learner:
        """获取 Learner"""
        return self._learner

    def start(self) -> None:
        """启动节点"""
        with self._lock:
            self._running = True
            logger.info(f"[Node {self.id}] Started")

    def stop(self) -> None:
        """停止节点"""
        with self._lock:
            self._running = False
            logger.info(f"[Node {self.id}] Stopped")

    @property
    def is_running(self) -> bool:
        """检查节点是否运行中"""
        with self._lock:
            return self._running

    def get_state(self) -> Dict[str, Any]:
        """获取节点状态"""
        with self._lock:
            return {
                'id': self.id,
                'running': self._running,
                'acceptor_state': self._acceptor.get_state(),
                'learned': self._learner.get_all_learned(),
            }


if __name__ == '__main__':
    # 示例用法
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    print("=== Basic Paxos Example ===")

    # 创建 3 个 Acceptor
    acceptors = []
    nodes = []
    for i in range(3):
        node_id = f"node-{i}"
        # 先创建空的 Node，后面更新
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
    print(f"Consensus: {result}")

    # 并发提议
    import concurrent.futures

    print("\n--- Concurrent Proposals ---")
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for i in range(3):
            f = executor.submit(nodes[i].propose, f"value-{i}")
            futures.append(f)

        for i, f in enumerate(concurrent.futures.as_completed(futures)):
            try:
                result = f.result()
                print(f"  Proposal {i}: {result}")
            except Exception as e:
                print(f"  Proposal {i} failed: {e}")

    # 停止所有节点
    for node in nodes:
        node.stop()

    print("\n=== Example Complete ===")

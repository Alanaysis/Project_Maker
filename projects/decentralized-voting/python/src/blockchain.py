"""
区块链核心模块
实现简单的区块链数据结构，用于记录投票交易
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class Transaction:
    """交易数据结构"""
    sender: str
    receiver: str
    data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    signature: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "data": self.data,
            "timestamp": self.timestamp,
            "signature": self.signature,
        }

    def compute_hash(self) -> str:
        tx_string = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(tx_string.encode()).hexdigest()


@dataclass
class Block:
    """区块数据结构"""
    index: int
    transactions: List[Transaction]
    timestamp: float = field(default_factory=time.time)
    previous_hash: str = ""
    nonce: int = 0
    hash: str = ""

    def compute_hash(self) -> str:
        block_data = {
            "index": self.index,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
        }
        block_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()


class Blockchain:
    """区块链实现"""

    def __init__(self, difficulty: int = 4):
        self.chain: List[Block] = []
        self.pending_transactions: List[Transaction] = []
        self.difficulty = difficulty
        self.mining_reward = 0  # 投票系统不需要挖矿奖励

        # 创建创世区块
        self._create_genesis_block()

    def _create_genesis_block(self) -> None:
        genesis_block = Block(
            index=0,
            transactions=[],
            timestamp=time.time(),
            previous_hash="0" * 64,
        )
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    @property
    def last_block(self) -> Block:
        return self.chain[-1]

    def add_transaction(self, transaction: Transaction) -> bool:
        """添加交易到待处理池"""
        if not transaction.sender or not transaction.receiver:
            return False

        self.pending_transactions.append(transaction)
        return True

    def proof_of_work(self, block: Block) -> str:
        """工作量证明"""
        block.nonce = 0
        computed_hash = block.compute_hash()

        while not computed_hash.startswith("0" * self.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()

        return computed_hash

    def mine_pending_transactions(self, miner_address: str = "system") -> Optional[Block]:
        """挖掘待处理交易"""
        if not self.pending_transactions:
            return None

        block = Block(
            index=len(self.chain),
            transactions=self.pending_transactions.copy(),
            timestamp=time.time(),
            previous_hash=self.last_block.hash,
        )

        block.hash = self.proof_of_work(block)
        self.chain.append(block)
        self.pending_transactions = []

        return block

    def is_chain_valid(self) -> bool:
        """验证区块链有效性"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            # 验证当前区块哈希
            if current_block.hash != current_block.compute_hash():
                return False

            # 验证链的连续性
            if current_block.previous_hash != previous_block.hash:
                return False

        return True

    def get_transactions_by_address(self, address: str) -> List[Transaction]:
        """获取指定地址的所有交易"""
        transactions = []
        for block in self.chain:
            for tx in block.transactions:
                if tx.sender == address or tx.receiver == address:
                    transactions.append(tx)
        return transactions

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chain": [
                {
                    "index": block.index,
                    "transactions": [tx.to_dict() for tx in block.transactions],
                    "timestamp": block.timestamp,
                    "previous_hash": block.previous_hash,
                    "nonce": block.nonce,
                    "hash": block.hash,
                }
                for block in self.chain
            ],
            "difficulty": self.difficulty,
            "pending_transactions": [tx.to_dict() for tx in self.pending_transactions],
        }

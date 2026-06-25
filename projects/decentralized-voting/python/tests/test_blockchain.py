"""
区块链模块测试
"""

import pytest
import time
from src.blockchain import Block, Blockchain, Transaction


class TestTransaction:
    """交易测试"""

    def test_create_transaction(self):
        tx = Transaction(
            sender="addr1",
            receiver="addr2",
            data={"action": "vote", "proposal": 1},
        )
        assert tx.sender == "addr1"
        assert tx.receiver == "addr2"
        assert tx.data["action"] == "vote"

    def test_transaction_hash(self):
        tx = Transaction(
            sender="addr1",
            receiver="addr2",
            data={"action": "vote"},
        )
        hash1 = tx.compute_hash()
        hash2 = tx.compute_hash()
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256

    def test_transaction_to_dict(self):
        tx = Transaction(
            sender="addr1",
            receiver="addr2",
            data={"action": "vote"},
        )
        tx_dict = tx.to_dict()
        assert "sender" in tx_dict
        assert "receiver" in tx_dict
        assert "data" in tx_dict
        assert "timestamp" in tx_dict


class TestBlock:
    """区块测试"""

    def test_create_block(self):
        block = Block(
            index=1,
            transactions=[],
            timestamp=time.time(),
            previous_hash="0" * 64,
        )
        assert block.index == 1
        assert len(block.transactions) == 0

    def test_block_hash(self):
        block = Block(
            index=1,
            transactions=[],
            timestamp=time.time(),
            previous_hash="0" * 64,
        )
        hash1 = block.compute_hash()
        hash2 = block.compute_hash()
        assert hash1 == hash2
        assert len(hash1) == 64

    def test_block_with_transactions(self):
        tx = Transaction(
            sender="addr1",
            receiver="addr2",
            data={"action": "vote"},
        )
        block = Block(
            index=1,
            transactions=[tx],
            timestamp=time.time(),
            previous_hash="0" * 64,
        )
        assert len(block.transactions) == 1


class TestBlockchain:
    """区块链测试"""

    def test_create_blockchain(self):
        chain = Blockchain(difficulty=2)
        assert len(chain.chain) == 1  # 创世区块
        assert chain.difficulty == 2

    def test_genesis_block(self):
        chain = Blockchain(difficulty=2)
        genesis = chain.chain[0]
        assert genesis.index == 0
        assert genesis.previous_hash == "0" * 64

    def test_add_transaction(self):
        chain = Blockchain(difficulty=2)
        tx = Transaction(
            sender="addr1",
            receiver="addr2",
            data={"action": "vote"},
        )
        result = chain.add_transaction(tx)
        assert result is True
        assert len(chain.pending_transactions) == 1

    def test_mine_block(self):
        chain = Blockchain(difficulty=2)
        tx = Transaction(
            sender="addr1",
            receiver="addr2",
            data={"action": "vote"},
        )
        chain.add_transaction(tx)
        block = chain.mine_pending_transactions()
        assert block is not None
        assert len(chain.chain) == 2
        assert len(chain.pending_transactions) == 0

    def test_chain_validity(self):
        chain = Blockchain(difficulty=2)
        tx = Transaction(
            sender="addr1",
            receiver="addr2",
            data={"action": "vote"},
        )
        chain.add_transaction(tx)
        chain.mine_pending_transactions()
        assert chain.is_chain_valid() is True

    def test_get_transactions_by_address(self):
        chain = Blockchain(difficulty=2)
        tx = Transaction(
            sender="addr1",
            receiver="addr2",
            data={"action": "vote"},
        )
        chain.add_transaction(tx)
        chain.mine_pending_transactions()

        txs = chain.get_transactions_by_address("addr1")
        assert len(txs) == 1

    def test_proof_of_work(self):
        chain = Blockchain(difficulty=2)
        block = Block(
            index=1,
            transactions=[],
            timestamp=time.time(),
            previous_hash="0" * 64,
        )
        hash_result = chain.proof_of_work(block)
        assert hash_result.startswith("0" * chain.difficulty)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# 04 - 测试说明

## 测试策略

### 4.1 测试层次

```
┌─────────────────────────────────────┐
│         端到端测试 (E2E)            │
│    完整业务流程测试                  │
├─────────────────────────────────────┤
│         集成测试                     │
│    模块间交互测试                    │
├─────────────────────────────────────┤
│         单元测试                     │
│    单个函数/方法测试                 │
└─────────────────────────────────────┘
```

### 4.2 测试覆盖率目标

- 语句覆盖率: > 90%
- 分支覆盖率: > 80%
- 函数覆盖率: 100%

## 单元测试

### 4.3 区块链模块测试

#### 4.3.1 交易测试

```python
class TestTransaction:
    def test_create_transaction(self):
        """测试创建交易"""
        tx = Transaction(
            sender="addr1",
            receiver="addr2",
            data={"action": "vote"},
        )
        assert tx.sender == "addr1"
        assert tx.receiver == "addr2"

    def test_transaction_hash(self):
        """测试交易哈希计算"""
        tx = Transaction(
            sender="addr1",
            receiver="addr2",
            data={"action": "vote"},
        )
        hash1 = tx.compute_hash()
        hash2 = tx.compute_hash()
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256
```

#### 4.3.2 区块测试

```python
class TestBlock:
    def test_create_block(self):
        """测试创建区块"""
        block = Block(
            index=1,
            transactions=[],
            timestamp=time.time(),
            previous_hash="0" * 64,
        )
        assert block.index == 1

    def test_block_hash(self):
        """测试区块哈希计算"""
        block = Block(
            index=1,
            transactions=[],
            timestamp=time.time(),
            previous_hash="0" * 64,
        )
        hash1 = block.compute_hash()
        hash2 = block.compute_hash()
        assert hash1 == hash2
```

#### 4.3.3 区块链测试

```python
class TestBlockchain:
    def test_create_blockchain(self):
        """测试创建区块链"""
        chain = Blockchain(difficulty=2)
        assert len(chain.chain) == 1  # 创世区块

    def test_mine_block(self):
        """测试挖矿"""
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

    def test_chain_validity(self):
        """测试区块链有效性"""
        chain = Blockchain(difficulty=2)
        # 添加交易并挖矿
        tx = Transaction(
            sender="addr1",
            receiver="addr2",
            data={"action": "vote"},
        )
        chain.add_transaction(tx)
        chain.mine_pending_transactions()
        assert chain.is_chain_valid() is True
```

### 4.4 投票模块测试

#### 4.4.1 投票活动测试

```python
class TestVotingContract:
    def test_create_vote_session(self):
        """测试创建投票活动"""
        contract = VotingContract()
        session_id = contract.create_vote_session(
            title="测试投票",
            description="这是一个测试",
            start_time=time.time(),
            end_time=time.time() + 3600,
            creator="0xCreator",
        )
        assert session_id == 0

    def test_add_proposal(self):
        """测试添加提案"""
        contract = VotingContract()
        session_id = contract.create_vote_session(
            title="测试投票",
            description="这是一个测试",
            start_time=time.time(),
            end_time=time.time() + 3600,
            creator="0xCreator",
        )
        proposal_id = contract.add_proposal(
            session_id=session_id,
            name="提案A",
            description="提案A描述",
            caller="0xCreator",
        )
        assert proposal_id == 0
```

#### 4.4.2 投票执行测试

```python
    def test_vote(self):
        """测试投票"""
        contract = VotingContract()
        # 创建投票活动并添加提案
        session_id = contract.create_vote_session(
            title="测试投票",
            description="这是一个测试",
            start_time=time.time(),
            end_time=time.time() + 3600,
            creator="0xCreator",
        )
        contract.add_proposal(session_id, "提案A", "描述", "0xCreator")
        contract.start_voting(session_id, "0xCreator")

        # 执行投票
        contract.vote(session_id, 0, "0xVoter1")
        assert contract.has_voted(session_id, "0xVoter1") is True

    def test_vote_twice(self):
        """测试重复投票"""
        contract = VotingContract()
        # 创建投票活动并添加提案
        session_id = contract.create_vote_session(
            title="测试投票",
            description="这是一个测试",
            start_time=time.time(),
            end_time=time.time() + 3600,
            creator="0xCreator",
        )
        contract.add_proposal(session_id, "提案A", "描述", "0xCreator")
        contract.start_voting(session_id, "0xCreator")

        # 第一次投票
        contract.vote(session_id, 0, "0xVoter1")

        # 第二次投票应该失败
        with pytest.raises(ValueError):
            contract.vote(session_id, 0, "0xVoter1")
```

### 4.5 身份模块测试

#### 4.5.1 选民注册测试

```python
class TestVoterRegistry:
    def test_register_voter(self):
        """测试注册选民"""
        registry = VoterRegistry()
        voter = registry.register_voter(
            address="0xVoter1",
            name="张三",
            email="zhangsan@example.com",
        )
        assert voter.address == "0xVoter1"
        assert voter.name == "张三"

    def test_register_duplicate_voter(self):
        """测试重复注册"""
        registry = VoterRegistry()
        registry.register_voter("0xVoter1", "张三", "zhangsan@example.com")

        with pytest.raises(ValueError):
            registry.register_voter("0xVoter1", "张三", "zhangsan@example.com")
```

#### 4.5.2 身份验证测试

```python
    def test_verify_voter(self):
        """测试验证选民"""
        registry = VoterRegistry()
        registry.register_voter("0xVoter1", "张三", "zhangsan@example.com")

        result = registry.verify_voter("0xVoter1")
        assert result is True

        voter = registry.get_voter("0xVoter1")
        assert voter.status == VoterStatus.VERIFIED

    def test_is_eligible(self):
        """测试投票资格检查"""
        registry = VoterRegistry()
        registry.register_voter("0xVoter1", "张三", "zhangsan@example.com")
        registry.verify_voter("0xVoter1")
        registry.issue_credential("0xVoter1")

        assert registry.is_eligible("0xVoter1") is True
```

### 4.6 规则模块测试

#### 4.6.1 投票规则测试

```python
class TestVotingEngine:
    def test_validate_vote_valid(self):
        """测试有效投票验证"""
        engine = VotingEngine()
        is_valid, errors = engine.validate_vote(
            voter_address="0xVoter1",
            proposal_ids=[0],
            total_proposals=3,
            has_voted=False,
        )
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_vote_already_voted(self):
        """测试已投票验证"""
        engine = VotingEngine()
        is_valid, errors = engine.validate_vote(
            voter_address="0xVoter1",
            proposal_ids=[0],
            total_proposals=3,
            has_voted=True,
        )
        assert is_valid is False
        assert "该选民已经投过票" in errors[0]
```

#### 4.6.2 法定人数测试

```python
    def test_check_quorum_percentage(self):
        """测试百分比法定人数"""
        rules = VotingRules(
            quorum_type=QuorumType.PERCENTAGE,
            quorum_value=0.5,
        )
        engine = VotingEngine(rules)

        met, rate = engine.check_quorum(60, 100)
        assert met is True
        assert rate == 0.6

        met, rate = engine.check_quorum(40, 100)
        assert met is False
        assert rate == 0.4
```

#### 4.6.3 投票方式测试

```python
    def test_simple_majority(self):
        """测试简单多数决"""
        engine = VotingEngine()
        proposals = [
            {"id": 0, "name": "A", "votes": 60},
            {"id": 1, "name": "B", "votes": 40},
        ]
        winner = engine.determine_winner(proposals, 100)
        assert winner["name"] == "A"

    def test_absolute_majority(self):
        """测试绝对多数决"""
        rules = VotingRules(voting_method=VotingMethod.ABSOLUTE_MAJORITY)
        engine = VotingEngine(rules)

        proposals = [
            {"id": 0, "name": "A", "votes": 60},
            {"id": 1, "name": "B", "votes": 40},
        ]
        winner = engine.determine_winner(proposals, 100)
        assert winner["name"] == "A"

        proposals = [
            {"id": 0, "name": "A", "votes": 40},
            {"id": 1, "name": "B", "votes": 30},
            {"id": 2, "name": "C", "votes": 30},
        ]
        winner = engine.determine_winner(proposals, 100)
        assert winner is None
```

### 4.7 透明性模块测试

#### 4.7.1 投票账本测试

```python
class TestVoteLedger:
    def test_record_vote(self):
        """测试记录投票"""
        ledger = VoteLedger()
        record = ledger.record_vote(
            session_id=1,
            voter_address="0xVoter1",
            proposal_id=0,
        )
        assert record.session_id == 1
        assert record.voter_address == "0xVoter1"

    def test_verify_record(self):
        """测试验证记录"""
        ledger = VoteLedger()
        record = ledger.record_vote(1, "0xVoter1", 0)
        assert ledger.verify_record(record) is True
```

#### 4.7.2 审计追踪测试

```python
class TestAuditTrail:
    def test_add_entry(self):
        """测试添加审计条目"""
        trail = AuditTrail()
        entry = trail.add_entry(
            action="create_session",
            actor="0xCreator",
            details={"session_id": 1},
        )
        assert entry.action == "create_session"

    def test_chain_integrity(self):
        """测试审计链完整性"""
        trail = AuditTrail()
        trail.add_entry("action1", "actor1", {"data": 1})
        trail.add_entry("action2", "actor2", {"data": 2})
        trail.add_entry("action3", "actor3", {"data": 3})

        assert trail.verify_chain() is True
```

## 集成测试

### 4.8 完整投票流程测试

```python
class TestIntegrationVoting:
    def test_complete_voting_flow(self):
        """测试完整投票流程"""
        # 1. 初始化系统
        blockchain = Blockchain(difficulty=2)
        contract = VotingContract(blockchain)
        registry = VoterRegistry()

        # 2. 注册选民
        registry.register_voter("0xVoter1", "张三", "zhangsan@example.com")
        registry.verify_voter("0xVoter1")
        registry.issue_credential("0xVoter1")

        # 3. 创建投票
        session_id = contract.create_vote_session(
            title="测试投票",
            description="这是一个测试",
            start_time=time.time(),
            end_time=time.time() + 3600,
            creator="0xCreator",
        )

        # 4. 添加提案
        contract.add_proposal(session_id, "提案A", "描述A", "0xCreator")
        contract.add_proposal(session_id, "提案B", "描述B", "0xCreator")

        # 5. 开始投票
        contract.start_voting(session_id, "0xCreator")

        # 6. 执行投票
        contract.vote(session_id, 0, "0xVoter1")

        # 7. 验证结果
        assert contract.has_voted(session_id, "0xVoter1") is True
        results = contract.get_results(session_id)
        assert results["total_votes"] == 1

        # 8. 结束投票
        contract.end_voting(session_id, "0xCreator")

        # 9. 验证最终状态
        session = contract.get_session(session_id)
        assert session.status == VoteStatus.ENDED
```

## 运行测试

### 4.9 测试命令

```bash
# 运行所有测试
pytest

# 运行特定模块测试
pytest tests/test_blockchain.py
pytest tests/test_voting.py
pytest tests/test_identity.py

# 运行带覆盖率的测试
pytest --cov=src --cov-report=html

# 运行详细输出
pytest -v

# 运行特定测试类
pytest tests/test_voting.py::TestVotingContract

# 运行特定测试方法
pytest tests/test_voting.py::TestVotingContract::test_vote
```

### 4.10 测试配置

```python
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

## 测试报告

### 4.11 生成测试报告

```bash
# 生成 HTML 覆盖率报告
pytest --cov=src --cov-report=html

# 生成 XML 报告（用于 CI/CD）
pytest --cov=src --cov-report=xml

# 生成终端报告
pytest --cov=src --cov-report=term-missing
```

### 4.12 测试最佳实践

1. **测试命名**: 使用描述性的测试名称
2. **测试隔离**: 每个测试独立运行
3. **测试数据**: 使用有意义的测试数据
4. **断言清晰**: 使用明确的断言
5. **测试覆盖**: 覆盖正常和异常路径
6. **测试维护**: 定期更新测试用例

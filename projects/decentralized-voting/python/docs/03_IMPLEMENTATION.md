# 03 - 实现细节

## 核心模块实现

### 3.1 区块链模块实现

#### 3.1.1 交易数据结构

```python
@dataclass
class Transaction:
    sender: str          # 发送者地址
    receiver: str        # 接收者地址
    data: Dict[str, Any] # 交易数据
    timestamp: float     # 时间戳
    signature: str       # 签名

    def compute_hash(self) -> str:
        """计算交易哈希"""
        tx_string = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(tx_string.encode()).hexdigest()
```

**实现要点：**
- 使用 `dataclass` 简化数据类定义
- 使用 SHA-256 计算哈希
- 支持 JSON 序列化

#### 3.1.2 区块数据结构

```python
@dataclass
class Block:
    index: int                    # 区块索引
    transactions: List[Transaction] # 交易列表
    timestamp: float              # 时间戳
    previous_hash: str            # 前一区块哈希
    nonce: int                    # 工作量证明随机数
    hash: str                     # 当前区块哈希

    def compute_hash(self) -> str:
        """计算区块哈希"""
        block_data = {
            "index": self.index,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
        }
        block_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
```

**实现要点：**
- 包含所有区块元数据
- 支持交易列表
- 计算哈希时包含所有字段

#### 3.1.3 工作量证明

```python
def proof_of_work(self, block: Block) -> str:
    """工作量证明算法"""
    block.nonce = 0
    computed_hash = block.compute_hash()

    # 不断增加 nonce 直到找到满足难度要求的哈希
    while not computed_hash.startswith("0" * self.difficulty):
        block.nonce += 1
        computed_hash = block.compute_hash()

    return computed_hash
```

**实现要点：**
- 通过调整 nonce 寻找满足条件的哈希
- 难度由前导零的数量决定
- 计算密集型操作

### 3.2 投票合约实现

#### 3.2.1 投票活动管理

```python
class VotingContract:
    def create_vote_session(
        self,
        title: str,
        description: str,
        start_time: float,
        end_time: float,
        creator: str,
    ) -> int:
        """创建投票活动"""
        # 验证时间参数
        if start_time >= end_time:
            raise ValueError("开始时间必须早于结束时间")

        # 创建投票活动
        session_id = self.session_counter
        self.session_counter += 1

        session = VoteSession(
            id=session_id,
            title=title,
            description=description,
            creator=creator,
            start_time=start_time,
            end_time=end_time,
        )

        self.vote_sessions[session_id] = session

        # 触发事件
        self._emit_event("VoteSessionCreated", {...})

        # 记录到区块链
        tx = Transaction(
            sender=creator,
            receiver="voting_contract",
            data={"action": "create_session", "session_id": session_id},
        )
        self.blockchain.add_transaction(tx)

        return session_id
```

#### 3.2.2 投票执行

```python
def vote(
    self,
    session_id: int,
    proposal_id: int,
    voter_address: str,
) -> None:
    """执行投票"""
    session = self.vote_sessions[session_id]

    # 验证投票状态
    if session.status != VoteStatus.ACTIVE:
        raise ValueError("投票活动未处于进行中状态")

    # 验证时间
    current_time = time.time()
    if current_time < session.start_time:
        raise ValueError("投票尚未开始")
    if current_time > session.end_time:
        raise ValueError("投票已结束")

    # 验证提案
    if proposal_id >= len(session.proposals):
        raise ValueError("提案不存在")

    # 验证是否已投票（一人一票）
    if session.has_voted.get(voter_address, False):
        raise ValueError("您已经投过票了")

    # 记录投票
    session.proposals[proposal_id].vote_count += 1
    session.has_voted[voter_address] = True
    session.voted_proposal[voter_address] = proposal_id
    session.total_votes += 1

    # 记录到区块链
    tx = Transaction(
        sender=voter_address,
        receiver="voting_contract",
        data={
            "action": "vote",
            "session_id": session_id,
            "proposal_id": proposal_id,
        },
    )
    self.blockchain.add_transaction(tx)
```

### 3.3 身份验证实现

#### 3.3.1 选民注册

```python
class VoterRegistry:
    def register_voter(
        self,
        address: str,
        name: str,
        email: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Voter:
        """注册选民"""
        # 检查是否已注册
        if address in self.voters:
            raise ValueError(f"选民 {address} 已注册")

        # 检查黑名单
        if address in self.blacklist:
            raise PermissionError(f"选民 {address} 已被列入黑名单")

        # 创建选民记录
        voter = Voter(
            address=address,
            name=name,
            email=email,
            metadata=metadata or {},
        )

        self.voters[address] = voter

        # 记录事件
        self.registration_events.append({
            "action": "register",
            "address": address,
            "name": name,
            "timestamp": time.time(),
        })

        return voter
```

#### 3.3.2 凭证管理

```python
def issue_credential(
    self,
    address: str,
    validity_duration: float = 86400,
) -> VoterCredential:
    """发行选民凭证"""
    # 验证选民状态
    voter = self.voters[address]
    if voter.status != VoterStatus.VERIFIED:
        raise ValueError(f"选民 {address} 未验证")

    # 生成凭证哈希
    credential_data = f"{address}:{voter.name}:{time.time()}"
    credential_hash = hashlib.sha256(credential_data.encode()).hexdigest()

    # 创建凭证
    credential = VoterCredential(
        voter_address=address,
        credential_hash=credential_hash,
        expires_at=time.time() + validity_duration,
    )

    self.credentials[address] = credential
    return credential
```

### 3.4 规则引擎实现

#### 3.4.1 投票验证

```python
class VotingEngine:
    def validate_vote(
        self,
        voter_address: str,
        proposal_ids: List[int],
        total_proposals: int,
        has_voted: bool,
    ) -> tuple[bool, List[str]]:
        """验证投票是否符合规则"""
        errors = []

        # 检查是否已投票
        if has_voted:
            errors.append("该选民已经投过票")
            return False, errors

        # 检查选择数量
        if len(proposal_ids) < self.rules.min_selections:
            errors.append(f"至少需要选择 {self.rules.min_selections} 个提案")

        if len(proposal_ids) > self.rules.max_selections:
            errors.append(f"最多只能选择 {self.rules.max_selections} 个提案")

        # 检查提案ID有效性
        for pid in proposal_ids:
            if pid < 0 or pid >= total_proposals:
                errors.append(f"提案ID {pid} 无效")

        return len(errors) == 0, errors
```

#### 3.4.2 法定人数检查

```python
def check_quorum(
    self,
    total_votes: int,
    total_eligible_voters: int,
) -> tuple[bool, float]:
    """检查是否达到法定人数"""
    if total_eligible_voters == 0:
        return False, 0.0

    participation_rate = total_votes / total_eligible_voters

    if self.rules.quorum_type == QuorumType.NONE:
        return True, participation_rate
    elif self.rules.quorum_type == QuorumType.PERCENTAGE:
        return participation_rate >= self.rules.quorum_value, participation_rate
    elif self.rules.quorum_type == QuorumType.ABSOLUTE:
        return total_votes >= self.rules.quorum_value, participation_rate

    return False, participation_rate
```

#### 3.4.3 多种投票方式

```python
def determine_winner(
    self,
    proposals: List[Dict[str, Any]],
    total_votes: int,
) -> Optional[Dict[str, Any]]:
    """确定获胜者"""
    if self.rules.voting_method == VotingMethod.SIMPLE_MAJORITY:
        return self._simple_majority(proposals, total_votes)
    elif self.rules.voting_method == VotingMethod.ABSOLUTE_MAJORITY:
        return self._absolute_majority(proposals, total_votes)
    elif self.rules.voting_method == VotingMethod.SUPER_MAJORITY:
        return self._super_majority(proposals, total_votes)
    elif self.rules.voting_method == VotingMethod.PLURALITY:
        return self._plurality(proposals)

def _simple_majority(self, proposals, total_votes):
    """简单多数决"""
    sorted_proposals = sorted(proposals, key=lambda x: x["votes"], reverse=True)
    winner = sorted_proposals[0]
    if winner["votes"] / total_votes >= self.rules.majority_threshold:
        return winner
    return None

def _absolute_majority(self, proposals, total_votes):
    """绝对多数决（超过50%）"""
    sorted_proposals = sorted(proposals, key=lambda x: x["votes"], reverse=True)
    winner = sorted_proposals[0]
    if winner["votes"] > total_votes / 2:
        return winner
    return None
```

### 3.5 透明性实现

#### 3.5.1 投票记录

```python
class VoteLedger:
    def record_vote(
        self,
        session_id: int,
        voter_address: str,
        proposal_id: int,
    ) -> VoteRecord:
        """记录投票"""
        record = VoteRecord(
            session_id=session_id,
            voter_address=voter_address,
            proposal_id=proposal_id,
            timestamp=time.time(),
        )

        # 记录到区块链
        tx = Transaction(
            sender=voter_address,
            receiver="vote_ledger",
            data={
                "action": "vote",
                "session_id": session_id,
                "proposal_id": proposal_id,
                "record_hash": record.compute_hash(),
            },
        )
        self.blockchain.add_transaction(tx)

        # 挖掘区块
        block = self.blockchain.mine_pending_transactions()
        if block:
            record.block_number = block.index
            record.transaction_hash = block.hash

        self.vote_records.append(record)
        return record
```

#### 3.5.2 审计追踪

```python
class AuditTrail:
    def add_entry(
        self,
        action: str,
        actor: str,
        details: Dict[str, Any],
    ) -> AuditEntry:
        """添加审计条目"""
        previous_hash = self.chain_hash if self.chain_hash else "0" * 64

        entry = AuditEntry(
            action=action,
            actor=actor,
            details=details,
            previous_hash=previous_hash,
        )

        entry.hash = entry.compute_hash()
        self.chain_hash = entry.hash

        self.entries.append(entry)
        return entry

    def verify_chain(self) -> bool:
        """验证审计链完整性"""
        for i in range(1, len(self.entries)):
            current = self.entries[i]
            previous = self.entries[i - 1]

            if current.previous_hash != previous.hash:
                return False

            if current.hash != current.compute_hash():
                return False

        return True
```

### 3.6 关键算法

#### 3.6.1 哈希计算

```python
import hashlib
import json

def compute_hash(data: Any) -> str:
    """计算数据的 SHA-256 哈希"""
    data_string = json.dumps(data, sort_keys=True)
    return hashlib.sha256(data_string.encode()).hexdigest()
```

#### 3.6.2 时间验证

```python
def is_within_voting_period(start_time: float, end_time: float) -> bool:
    """检查是否在投票时间内"""
    current_time = time.time()
    return start_time <= current_time <= end_time
```

### 3.7 性能优化

#### 3.7.1 缓存策略

```python
from functools import lru_cache

class VotingContract:
    @lru_cache(maxsize=128)
    def get_session(self, session_id: int) -> Optional[VoteSession]:
        """获取投票活动（带缓存）"""
        return self.vote_sessions.get(session_id)
```

#### 3.7.2 批量处理

```python
def batch_vote(
    self,
    session_id: int,
    votes: List[Tuple[int, str]],  # (proposal_id, voter_address)
) -> List[VoteRecord]:
    """批量投票"""
    records = []
    for proposal_id, voter_address in votes:
        self.vote(session_id, proposal_id, voter_address)
        record = self.vote_ledger.record_vote(
            session_id, voter_address, proposal_id
        )
        records.append(record)
    return records
```

### 3.8 错误处理

#### 3.8.1 自定义异常

```python
class VotingSystemError(Exception):
    """投票系统基础异常"""
    pass

class VoterNotRegisteredError(VotingSystemError):
    """选民未注册"""
    pass

class DuplicateVoteError(VotingSystemError):
    """重复投票"""
    pass

class SessionNotFoundError(VotingSystemError):
    """投票活动不存在"""
    pass

class PermissionDeniedError(VotingSystemError):
    """权限不足"""
    pass
```

#### 3.8.2 错误处理模式

```python
def safe_vote(session_id, proposal_id, voter_address):
    """安全投票（带错误处理）"""
    try:
        contract.vote(session_id, proposal_id, voter_address)
        return {"success": True, "message": "投票成功"}
    except VoterNotRegisteredError as e:
        return {"success": False, "message": f"选民未注册: {e}"}
    except DuplicateVoteError as e:
        return {"success": False, "message": f"重复投票: {e}"}
    except SessionNotFoundError as e:
        return {"success": False, "message": f"投票活动不存在: {e}"}
    except Exception as e:
        return {"success": False, "message": f"未知错误: {e}"}
```

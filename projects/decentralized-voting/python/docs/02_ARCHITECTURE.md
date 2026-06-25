# 02 - 架构设计

## 系统架构概述

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      用户接口层                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  命令行界面  │  │   REST API  │  │   Web UI    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      业务逻辑层                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  投票管理    │  │  身份验证    │  │  规则引擎    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      核心服务层                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  区块链      │  │  投票账本    │  │  审计追踪    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      数据存储层                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  内存存储    │  │  文件存储    │  │  区块链存储  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 模块设计

#### 2.2.1 区块链模块 (`blockchain.py`)

**职责：**
- 区块创建和管理
- 交易记录
- 工作量证明
- 链完整性验证

**核心类：**
- `Transaction`: 交易数据结构
- `Block`: 区块数据结构
- `Blockchain`: 区块链管理

**关键方法：**
```python
class Blockchain:
    def add_transaction(transaction: Transaction) -> bool
    def mine_pending_transactions(miner_address: str) -> Block
    def is_chain_valid() -> bool
    def get_transactions_by_address(address: str) -> List[Transaction]
```

#### 2.2.2 投票模块 (`voting.py`)

**职责：**
- 投票活动管理
- 提案管理
- 投票执行
- 结果统计

**核心类：**
- `Proposal`: 提案数据结构
- `VoteSession`: 投票活动
- `VotingContract`: 投票合约

**关键方法：**
```python
class VotingContract:
    def create_vote_session(...) -> int
    def add_proposal(...) -> int
    def start_voting(session_id: int, caller: str) -> None
    def vote(session_id: int, proposal_id: int, voter: str) -> None
    def end_voting(session_id: int, caller: str) -> None
    def get_results(session_id: int) -> Dict
```

#### 2.2.3 身份模块 (`identity.py`)

**职责：**
- 选民注册
- 身份验证
- 凭证管理
- 黑白名单管理

**核心类：**
- `Voter`: 选民数据结构
- `VoterCredential`: 选民凭证
- `VoterRegistry`: 选民注册表

**关键方法：**
```python
class VoterRegistry:
    def register_voter(address, name, email) -> Voter
    def verify_voter(address: str) -> bool
    def issue_credential(address, validity_duration) -> VoterCredential
    def is_eligible(address: str) -> bool
```

#### 2.2.4 规则模块 (`consensus.py`)

**职责：**
- 投票规则配置
- 投票验证
- 结果计算
- 法定人数检查

**核心类：**
- `VotingRules`: 投票规则配置
- `VoteResult`: 投票结果
- `VotingEngine`: 投票引擎
- `OnePersonOneVote`: 一人一票验证器

**关键方法：**
```python
class VotingEngine:
    def validate_vote(...) -> tuple[bool, List[str]]
    def check_quorum(...) -> tuple[bool, float]
    def determine_winner(...) -> Optional[Dict]
    def calculate_results(...) -> VoteResult
```

#### 2.2.5 透明性模块 (`transparency.py`)

**职责：**
- 投票记录管理
- 审计追踪
- 透明度报告

**核心类：**
- `VoteRecord`: 投票记录
- `AuditEntry`: 审计条目
- `VoteLedger`: 投票账本
- `AuditTrail`: 审计追踪
- `TransparencyReport`: 透明度报告

**关键方法：**
```python
class VoteLedger:
    def record_vote(session_id, voter, proposal_id) -> VoteRecord
    def verify_record(record: VoteRecord) -> bool

class AuditTrail:
    def add_entry(action, actor, details) -> AuditEntry
    def verify_chain() -> bool
```

### 2.3 数据流

#### 2.3.1 投票流程

```
用户投票请求
    │
    ▼
身份验证 (VoterRegistry)
    │
    ▼
资格检查 (is_eligible)
    │
    ▼
规则验证 (VotingEngine.validate_vote)
    │
    ▼
执行投票 (VotingContract.vote)
    │
    ▼
记录到账本 (VoteLedger.record_vote)
    │
    ▼
审计记录 (AuditTrail.add_entry)
    │
    ▼
返回结果
```

#### 2.3.2 结果计算流程

```
获取投票数据
    │
    ▼
检查法定人数 (check_quorum)
    │
    ▼
计算各提案得票
    │
    ▼
应用投票规则 (determine_winner)
    │
    ▼
生成结果报告 (VoteResult)
    │
    ▼
返回结果
```

### 2.4 接口设计

#### 2.4.1 投票接口

```python
# 创建投票
session_id = contract.create_vote_session(
    title="投票标题",
    description="投票描述",
    start_time=time.time(),
    end_time=time.time() + 3600,
    creator="0xCreator",
)

# 添加提案
proposal_id = contract.add_proposal(
    session_id=session_id,
    name="提案名称",
    description="提案描述",
    caller="0xCreator",
)

# 投票
contract.vote(
    session_id=session_id,
    proposal_id=proposal_id,
    voter_address="0xVoter",
)

# 获取结果
results = contract.get_results(session_id)
```

#### 2.4.2 身份接口

```python
# 注册选民
voter = registry.register_voter(
    address="0xVoter",
    name="姓名",
    email="email@example.com",
)

# 验证选民
registry.verify_voter("0xVoter")

# 发行凭证
credential = registry.issue_credential("0xVoter")

# 检查资格
is_eligible = registry.is_eligible("0xVoter")
```

### 2.5 错误处理

#### 2.5.1 异常类型

```python
class VotingError(Exception):
    """投票系统基础异常"""
    pass

class VoterNotRegistered(VotingError):
    """选民未注册"""
    pass

class VoterAlreadyVoted(VotingError):
    """选民已投票"""
    pass

class SessionNotActive(VotingError):
    """投票活动未激活"""
    pass

class InvalidProposal(VotingError):
    """无效提案"""
    pass
```

#### 2.5.2 错误处理策略

1. **输入验证**: 在执行前验证所有输入
2. **权限检查**: 验证操作权限
3. **状态检查**: 验证系统状态
4. **事务回滚**: 失败时回滚操作

### 2.6 扩展性设计

#### 2.6.1 可扩展点

1. **存储后端**: 支持多种存储方式
2. **共识算法**: 可替换共识机制
3. **投票方式**: 可添加新的投票方式
4. **身份验证**: 支持多种身份验证方式

#### 2.6.2 插件机制

```python
# 自定义投票方式
class CustomVotingMethod:
    def determine_winner(self, proposals, total_votes):
        # 自定义逻辑
        pass

# 注册插件
engine.register_voting_method("custom", CustomVotingMethod())
```

### 2.7 部署架构

#### 2.7.1 单机部署

```
┌─────────────────────────────────┐
│         单机部署                 │
│  ┌───────────────────────────┐  │
│  │     Python 应用           │  │
│  │  ┌─────┐ ┌─────┐ ┌─────┐ │  │
│  │  │Vote │ │ID   │ │Audit│ │  │
│  │  └─────┘ └─────┘ └─────┘ │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │     数据存储              │  │
│  │  ┌─────┐ ┌─────┐         │  │
│  │  │Memory│ │File │         │  │
│  │  └─────┘ └─────┘         │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

#### 2.7.2 分布式部署

```
┌─────────────────────────────────────────────┐
│              分布式部署                      │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐    │
│  │ Node 1  │  │ Node 2  │  │ Node 3  │    │
│  │ ┌─────┐ │  │ ┌─────┐ │  │ ┌─────┐ │    │
│  │ │App  │ │  │ │App  │ │  │ │App  │ │    │
│  │ └─────┘ │  │ └─────┘ │  │ └─────┘ │    │
│  │ ┌─────┐ │  │ ┌─────┐ │  │ ┌─────┐ │    │
│  │ │Chain│ │  │ │Chain│ │  │ │Chain│ │    │
│  │ └─────┘ │  │ └─────┘ │  │ └─────┘ │    │
│  └─────────┘  └─────────┘  └─────────┘    │
│         │           │           │          │
│         └───────────┼───────────┘          │
│                     │                      │
│              ┌──────┴──────┐               │
│              │  P2P Network │               │
│              └─────────────┘               │
└─────────────────────────────────────────────┘
```

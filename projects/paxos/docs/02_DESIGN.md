# Paxos 算法设计文档

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                      Client Layer                        │
├─────────────────────────────────────────────────────────┤
│                    Proposer Service                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │Proposer 1│  │Proposer 2│  │Proposer 3│             │
│  └──────────┘  └──────────┘  └──────────┘             │
├─────────────────────────────────────────────────────────┤
│                    Acceptor Service                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │Acceptor 1│  │Acceptor 2│  │Acceptor 3│             │
│  └──────────┘  └──────────┘  └──────────┘             │
├─────────────────────────────────────────────────────────┤
│                    Learner Service                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │Learner 1 │  │Learner 2 │  │Learner 3 │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└─────────────────────────────────────────────────────────┘
```

## 2. 模块设计

### 2.1 核心模块

#### 2.1.1 Types 模块
```python
@dataclass(order=True)
class ProposalID:
    number: int
    node_id: str

@dataclass
class PrepareArgs:
    proposal_id: ProposalID
    to: str

@dataclass
class PrepareReply:
    promise: bool
    proposal_id: ProposalID
    accepted_id: Optional[ProposalID]
    accepted_value: Any
```

### 2.2 Proposer 设计

```python
class Proposer:
    def __init__(self, node_id: str, acceptors: List[AcceptorClient]):
        self.id = node_id
        self._proposal_num = 0
        self._acceptors = acceptors
        self._quorum_size = len(acceptors) // 2 + 1

    def propose(self, value: Any) -> Any:
        # Phase 1: Prepare
        promises = self._prepare(proposal_id)
        # Phase 2: Accept
        accepted_count = self._accept(proposal_id, value)
```

### 2.3 Acceptor 设计

```python
class Acceptor:
    def handle_prepare(self, args: PrepareArgs) -> PrepareReply:
        # 如果提案号大于已承诺的提案号，承诺
        if self._promised_id is None or args.proposal_id.is_greater_than(self._promised_id):
            self._promised_id = args.proposal_id
            return PrepareReply(promise=True, ...)

    def handle_accept(self, args: AcceptArgs) -> AcceptReply:
        # 如果提案号 >= 已承诺的提案号，接受
        if not self._promised_id.is_greater_than(args.proposal_id):
            self._accepted_value = args.value
            return AcceptReply(accepted=True, ...)
```

### 2.4 Learner 设计

```python
class Learner:
    def handle_accepted(self, args: AcceptedArgs) -> None:
        # 记录接受信息
        self._accepted[pid_str][args.from_id] = args

        # 检查是否有多数派接受同一值
        if accept_count >= self._quorum_size:
            self._learned[pid_str] = args.value
```

## 3. Multi Paxos 设计

### 3.1 日志结构

```python
@dataclass
class LogEntry:
    slot_id: int
    proposal_id: ProposalID
    value: Any
    committed: bool = False

class PaxosLog:
    def append(self, entry: LogEntry) -> None: ...
    def commit(self, slot_id: int) -> None: ...
```

### 3.2 Leader 选举

```python
class LeaderNode:
    def start_election(self) -> bool:
        # 转换为 Candidate 状态
        self._state = LeaderState.CANDIDATE
        self._term += 1

        # 请求投票
        for peer in self._peers:
            self._request_vote(peer, term)

        # 检查是否获得多数派投票
        if vote_count >= quorum_size:
            self._state = LeaderState.LEADER
            return True
```

## 4. 故障处理设计

### 4.1 Proposer 故障检测

```python
class ProposerHealthChecker:
    def heartbeat(self, proposer_id: str) -> None:
        status.last_active = time.time()
        status.is_alive = True

    def _check_all(self) -> None:
        if now - status.last_active > self._timeout:
            status.is_alive = False
```

### 4.2 Acceptor 故障恢复

```python
class AcceptorRecovery:
    def save_snapshot(self, state: AcceptorState) -> None: ...
    def append_log(self, operation: str, data: Any) -> None: ...
    def recover(self) -> Optional[AcceptorState]:
        # 1. 从快照恢复
        # 2. 回放日志
```

### 4.3 网络分区处理

```python
class PartitionDetector:
    def _check_partitions(self) -> None:
        if now - last_heartbeat > self._heartbeat_timeout:
            # 检测到分区
            self._partitions[peer] = True
```

## 5. 并发控制

### 5.1 锁策略

```python
class Acceptor:
    def __init__(self):
        self._lock = threading.RLock()

    def handle_prepare(self, args):
        with self._lock:
            # 操作共享状态
```

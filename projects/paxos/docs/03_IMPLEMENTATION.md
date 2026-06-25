# Paxos 算法实现文档

## 1. 实现概述

本项目使用 Python 实现 Paxos 共识算法，包括 Basic Paxos 和 Multi Paxos。

## 2. 核心实现

### 2.1 Basic Paxos 实现

#### 2.1.1 Proposer 实现

```python
class Proposer:
    def propose(self, value: Any) -> Any:
        # Phase 1: Prepare
        promises = self._prepare(proposal_id)

        # 检查是否有多数派 Promise
        if len(promises) < self._quorum_size:
            raise RuntimeError("Not enough promises")

        # 选择值：如果有已接受的值，选择编号最大的
        value_to_accept = value
        for promise in promises:
            if promise.accepted_id.is_greater_than(max_accepted_id):
                value_to_accept = promise.accepted_value

        # Phase 2: Accept
        accepted_count = self._accept(proposal_id, value_to_accept)

        if accepted_count < self._quorum_size:
            raise RuntimeError("Not enough accepts")

        return value_to_accept
```

#### 2.1.2 Acceptor 实现

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

#### 2.1.3 Learner 实现

```python
class Learner:
    def handle_accepted(self, args: AcceptedArgs) -> None:
        # 记录接受信息
        self._accepted[pid_str][args.from_id] = args

        # 检查是否有多数派接受同一值
        if accept_count >= self._quorum_size:
            self._learned[pid_str] = args.value
```

### 2.2 Multi Paxos 实现

#### 2.2.1 日志结构

```python
class PaxosLog:
    def append(self, entry: LogEntry) -> None:
        self._entries[entry.slot_id] = entry

    def commit(self, slot_id: int) -> None:
        self._entries[slot_id].committed = True
        self._commit_index = max(self._commit_index, slot_id)
```

#### 2.2.2 Leader 选举

```python
class LeaderNode:
    def start_election(self) -> bool:
        self._state = LeaderState.CANDIDATE
        self._term += 1
        self._votes = {self.id: True}  # 投票给自己

        # 请求其他节点投票
        for peer in self._peers:
            self._request_vote(peer, term)

        # 检查是否获得多数派投票
        if vote_count >= quorum_size:
            self._state = LeaderState.LEADER
            return True
        return False
```

### 2.3 故障处理实现

#### 2.3.1 Proposer 故障检测

```python
class ProposerHealthChecker:
    def _check_all(self) -> None:
        now = time.time()
        for proposer_id, status in self._proposers.items():
            if status.is_alive and now - status.last_active > self._timeout:
                status.is_alive = False
                status.failures += 1
```

#### 2.3.2 Acceptor 故障恢复

```python
class AcceptorRecovery:
    def recover(self) -> Optional[AcceptorState]:
        # 1. 从快照恢复
        state = AcceptorState(
            promised_id=self._snapshot.promised_id,
            accepted_id=self._snapshot.accepted_id,
            accepted_value=self._snapshot.accepted_value,
        )

        # 2. 回放日志
        entries = self._log.get_entries(self._snapshot.timestamp)
        for entry in entries:
            self._apply_entry(state, entry)

        return state
```

## 3. 并发实现

### 3.1 线程安全

使用 `threading.RLock()` 保护共享状态：

```python
class Acceptor:
    def __init__(self):
        self._lock = threading.RLock()

    def handle_prepare(self, args):
        with self._lock:
            # 操作共享状态
```

### 3.2 并发 Proposer

使用 `threading.Thread` 并发发送请求：

```python
def _prepare(self, proposal_id):
    promises = []
    threads = []

    for acceptor in self._acceptors:
        t = threading.Thread(target=send_prepare, args=(acceptor,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    return promises
```

## 4. 配置管理

```python
# 超时配置
election_timeout = 0.15  # 150ms
heartbeat_timeout = 0.05  # 50ms

# 集群配置
peers = ["node-0", "node-1", "node-2"]
quorum_size = len(peers) // 2 + 1
```

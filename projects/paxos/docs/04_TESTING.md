# Paxos 算法测试文档

## 1. 测试策略

### 1.1 测试类型

1. **单元测试**: 测试各个组件的独立功能
2. **集成测试**: 测试组件间的交互
3. **故障测试**: 测试故障场景下的行为
4. **并发测试**: 测试并发场景下的正确性

### 1.2 测试覆盖目标

- 代码覆盖率 > 80%
- 核心逻辑覆盖率 100%

## 2. 共识达成测试

### 2.1 单值共识测试

```python
def test_single_value_consensus():
    acceptors = [MockAcceptor(f"acceptor-{i}") for i in range(3)]
    proposer = Proposer("proposer-1", acceptors)
    result = proposer.propose("value-1")
    assert result == "value-1"
```

### 2.2 多值共识测试

```python
def test_multiple_value_consensus():
    acceptors = [MockAcceptor(f"acceptor-{i}") for i in range(3)]

    # 并发提议多个值
    threads = [threading.Thread(target=propose_value, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # 验证所有 Proposer 学习到相同的值
```

## 3. 故障恢复测试

### 3.1 Acceptor 故障测试

```python
def test_acceptor_failure():
    acceptors = [MockAcceptor(f"acceptor-{i}") for i in range(5)]

    # 模拟 2 个 Acceptor 故障
    acceptors[3]._should_fail = True
    acceptors[4]._should_fail = True

    # 尝试达成共识
    proposer = Proposer("proposer-1", acceptors)
    result = proposer.propose("value-1")
    assert result == "value-1"
```

### 3.2 多数派故障测试

```python
def test_majority_failure():
    acceptors = [MockAcceptor(f"acceptor-{i}") for i in range(5)]

    # 模拟 3 个 Acceptor 故障
    acceptors[2]._should_fail = True
    acceptors[3]._should_fail = True
    acceptors[4]._should_fail = True

    # 尝试达成共识
    proposer = Proposer("proposer-1", acceptors)
    try:
        proposer.propose("value-1")
        assert False, "Expected RuntimeError"
    except RuntimeError:
        pass
```

## 4. 并发测试

### 4.1 并发 Proposer 测试

```python
def test_concurrent_proposers():
    acceptors = [MockAcceptor(f"acceptor-{i}") for i in range(5)]

    # 启动 10 个并发 Proposer
    threads = [threading.Thread(target=propose_value, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # 验证所有成功的 Proposer 学习到相同的值
```

### 4.2 并发日志追加测试

```python
def test_concurrent_log_append():
    log = PaxosLog()

    # 并发追加
    threads = [threading.Thread(target=append_entry, args=(i,)) for i in range(100)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert log.last_index == 99
```

## 5. Leader 选举测试

### 5.1 选举成功测试

```python
def test_leader_election():
    peers = ["node-0", "node-1", "node-2"]
    nodes = [LeaderNode(f"node-{i}", peers) for i in range(3)]

    for node in nodes:
        node.start()

    leader = nodes[0].start_election()
    assert leader
    assert nodes[0].is_leader
```

### 5.2 Leader 故障转移测试

```python
def test_leader_failover():
    peers = ["node-0", "node-1", "node-2", "node-3", "node-4"]
    nodes = [LeaderNode(f"node-{i}", peers) for i in range(5)]

    # 选举 Leader
    nodes[0].start_election()
    assert nodes[0].is_leader

    # Leader 故障
    nodes[0].stop()

    # 新的选举
    nodes[1].start_election()
    assert nodes[1].is_leader
```

## 6. 性能测试

### 6.1 Proposer 性能测试

```python
def test_proposer_performance():
    acceptors = [MockAcceptor(f"acceptor-{i}") for i in range(3)]
    proposer = Proposer("proposer-1", acceptors)

    start = time.time()
    for i in range(100):
        proposer.propose(f"value-{i}")
    elapsed = time.time() - start

    print(f"Performance: {100/elapsed:.0f} ops/s")
```

## 7. 测试运行

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/test_basic.py -v

# 运行性能测试
python -m pytest tests/ -v -k "performance"
```

# Paxos 算法开发文档

## 1. 开发环境

### 1.1 环境要求

- Python 3.12+
- pytest (测试)

### 1.2 项目初始化

```bash
# 克隆项目
cd /home/siok/project_copyninja/projects/paxos

# 安装依赖（可选）
pip install pytest
```

## 2. 代码规范

### 2.1 命名规范

- 模块名: 小写下划线，如 `acceptor.py`, `proposer.py`
- 类名: PascalCase，如 `Proposer`, `Acceptor`
- 函数名: 小写下划线，如 `handle_prepare`, `propose`
- 常量: 大写下划线，如 `FOLLOWER`, `CANDIDATE`

### 2.2 注释规范

```python
class Proposer:
    """Proposer 提议者角色

    职责：
    - 提出提案
    - 发送 Prepare 和 Accept 请求
    - 处理冲突和重试
    """

    def propose(self, value: Any) -> Any:
        """提议一个值

        执行两阶段提交：
        1. Prepare 阶段：获取多数派承诺
        2. Accept 阶段：请求多数派接受
        """
```

### 2.3 类型注解

```python
from typing import Any, Optional, List

class Acceptor:
    def handle_prepare(self, args: PrepareArgs) -> PrepareReply:
        ...
```

## 3. 模块开发

### 3.1 Basic Paxos 模块

**文件结构**:
```
src/basic/
├── __init__.py
├── types.py      # 类型定义
├── acceptor.py   # Acceptor 实现
├── proposer.py   # Proposer 实现
├── learner.py    # Learner 实现
└── node.py       # Node 组合角色
```

**开发步骤**:
1. 定义核心类型（ProposalID, PrepareArgs 等）
2. 实现 Acceptor（handle_prepare, handle_accept）
3. 实现 Proposer（propose）
4. 实现 Learner（handle_accepted）
5. 实现 Node 组合
6. 编写测试

### 3.2 Multi Paxos 模块

**文件结构**:
```
src/multi/
├── __init__.py
├── types.py      # 类型定义
├── log.py        # 日志结构
├── leader.py     # Leader 选举
└── replicator.py # 日志复制
```

**开发步骤**:
1. 实现日志结构（LogEntry, PaxosLog）
2. 实现 Leader 选举
3. 实现日志复制
4. 编写测试

### 3.3 故障处理模块

**文件结构**:
```
src/fault/
├── __init__.py
├── health.py     # Proposer 健康检查
├── recovery.py   # Acceptor 恢复
└── partition.py  # 网络分区处理
```

**开发步骤**:
1. 实现 Proposer 故障检测
2. 实现 Acceptor 故障恢复
3. 实现网络分区检测
4. 编写测试

## 4. 构建与运行

### 4.1 运行示例

```bash
# 运行 Basic Paxos 示例
python -m src.basic.node

# 运行 Multi Paxos 示例
python -m src.multi.leader
```

### 4.2 运行测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/test_basic.py -v
```

## 5. 调试技巧

### 5.1 日志输出

```python
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

logger.info(f"[Acceptor {self.id}] Received Prepare with proposal {args.proposal_id}")
```

### 5.2 使用断言

```python
assert result == "value-1", f"Expected 'value-1', got {result}"
assert len(promises) >= quorum_size, "Not enough promises"
```

## 6. 性能优化

### 6.1 锁优化

```python
# 使用可重入锁
self._lock = threading.RLock()

# 最小化锁范围
with self._lock:
    # 只保护必要的操作
```

### 6.2 批量处理

```python
def append_entries(self, entries: List[LogEntry]) -> None:
    for entry in entries:
        self._log.append(entry)
```

### 6.3 并发请求

```python
def _prepare(self, proposal_id):
    threads = []
    for acceptor in self._acceptors:
        t = threading.Thread(target=send_prepare, args=(acceptor,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
```

## 7. 常见问题

### 7.1 活锁问题

**问题**: 多个 Proposer 交替提出提案，导致无法达成共识。

**解决**:
- 引入随机退避时间
- 使用 Leader 选举
- Multi Paxos 优化

### 7.2 网络分区

**问题**: 网络分区导致无法达成共识。

**解决**:
- 检测网络分区
- 只有多数派分区能达成共识
- 分区恢复后同步状态

### 7.3 性能瓶颈

**问题**: 高并发下性能下降。

**解决**:
- 使用线程池
- 批量处理
- 异步提交

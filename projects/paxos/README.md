# Paxos 共识算法实现

## 项目概述

Paxos 是一种分布式共识算法，用于在分布式系统中达成一致。本项目使用 Python 实现了完整的 Paxos 算法，包括 Basic Paxos 和 Multi Paxos。

## 目录结构

```
paxos/
├── README.md
├── docs/
│   ├── 01_RESEARCH.md
│   ├── 02_DESIGN.md
│   ├── 03_IMPLEMENTATION.md
│   ├── 04_TESTING.md
│   └── 05_DEVELOPMENT.md
├── src/
│   ├── basic/          # Basic Paxos 实现
│   │   ├── __init__.py
│   │   ├── types.py    # 类型定义
│   │   ├── acceptor.py # Acceptor 实现
│   │   ├── proposer.py # Proposer 实现
│   │   ├── learner.py  # Learner 实现
│   │   └── node.py     # Node 组合角色
│   ├── multi/          # Multi Paxos 实现
│   │   ├── __init__.py
│   │   ├── types.py    # 类型定义
│   │   ├── log.py      # 日志结构
│   │   ├── leader.py   # Leader 选举
│   │   └── replicator.py # 日志复制
│   └── fault/          # 故障处理
│       ├── __init__.py
│       ├── health.py   # Proposer 健康检查
│       ├── recovery.py # Acceptor 恢复
│       └── partition.py # 网络分区
└── tests/
    ├── __init__.py
    ├── test_basic.py   # Basic Paxos 测试
    ├── test_multi.py   # Multi Paxos 测试
    └── test_fault.py   # 故障处理测试
```

## 核心功能

### 1. Basic Paxos
- **Prepare 阶段**: Proposer 发送 Prepare 请求，承诺不接受编号更小的提案
- **Accept 阶段**: Proposer 发送 Accept 请求，请求接受者接受提案
- **Learn 阶段**: Learner 学习已达成共识的值

### 2. Multi Paxos
- 优化日志复制
- Leader 选举机制
- 减少消息往返次数

### 3. 故障处理
- Proposer 故障检测与恢复
- Acceptor 故障容错
- 网络分区处理

## 快速开始

```bash
# 运行 Basic Paxos 示例
python -m src.basic.node

# 运行 Multi Paxos 示例
python -m src.multi.leader

# 运行测试
python -m pytest tests/ -v
```

## 算法流程

```
Proposer                    Acceptor                    Learner
    |                           |                           |
    |------ Prepare(n) -------->|                           |
    |                           |                           |
    |<--- Promise(n, v) --------|                           |
    |                           |                           |
    |------ Accept(n, v) ------>|                           |
    |                           |                           |
    |<--- Accepted(n, v) -------|------ Notify(n, v) ------>|
    |                           |                           |
```

## 技术栈

- **语言**: Python 3.12+
- **并发**: threading
- **测试**: pytest

## 参考资料

- [Paxos Made Simple](https://lamport.azurewebsites.net/pubs/paxos-simple.pdf)
- [The Part-Time Parliament](https://lamport.azurewebsites.net/pubs/lamport-paxos.pdf)

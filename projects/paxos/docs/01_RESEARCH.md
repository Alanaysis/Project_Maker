# Paxos 算法研究文档

## 1. 算法背景

### 1.1 共识问题

在分布式系统中，共识问题是指多个节点需要就某个值达成一致。这是分布式系统中最基本的问题之一。

### 1.2 Paxos 的起源

Paxos 算法由 Leslie Lamport 在 1989 年提出，论文《The Part-Time Parliament》描述了该算法。

## 2. 算法角色

### 2.1 Proposer（提议者）
- 提出提案
- 发送 Prepare 和 Accept 请求
- 处理冲突和重试

### 2.2 Acceptor（接受者）
- 接收 Prepare 请求
- 接受或拒绝 Accept 请求
- 承诺不接受编号更小的提案

### 2.3 Learner（学习者）
- 学习已达成共识的值
- 不参与共识过程

## 3. Basic Paxos 流程

### 3.1 Prepare 阶段
1. Proposer 生成全局唯一且递增的提案号 n
2. Proposer 向多数派 Acceptor 发送 Prepare(n)
3. Acceptor 收到 Prepare(n)：
   - 如果 n > 已承诺的最大提案号，承诺不再接受编号 < n 的提案
   - 返回已接受的最大编号提案（如果有）

### 3.2 Accept 阶段
1. Proposer 收到多数派 Promise
2. 如果所有返回的提案中已有被接受的，选择编号最大的值
3. 向多数派 Acceptor 发送 Accept(n, value)
4. Acceptor 接受请求（如果 n >= 已承诺的提案号）

### 3.3 Learn 阶段
1. Acceptor 接受提案后通知 Learner
2. Learner 学习达成共识的值

## 4. Multi Paxos 优化

### 4.1 Leader 选举
- 选出稳定的 Leader
- Leader 跳过 Prepare 阶段
- 减少消息往返

### 4.2 日志复制
- 连续的槽位（Slot）
- 每个槽位独立运行 Paxos
- 保证日志顺序一致性

## 5. 故障场景

### 5.1 Proposer 故障
- 提案未完成即故障
- 其他 Proposer 可以继续
- 需要重新生成提案号

### 5.2 Acceptor 故障
- 少数派故障：不影响共识
- 多数派故障：无法达成共识
- 恢复后需要同步状态

### 5.3 网络分区
- 分区两侧可能选出不同 Leader
- 只有多数派分区能达成共识
- 分区恢复后需要合并

## 6. 关键特性

### 6.1 安全性（Safety）
- 不会达成错误的共识
- 已达成的共识不会被改变

### 6.2 活性（Liveness）
- 在多数派存活时能达成共识
- 需要解决活锁问题

### 6.3 容错性
- 容忍 f 个节点故障（需要 2f+1 个节点）
- 异步网络模型

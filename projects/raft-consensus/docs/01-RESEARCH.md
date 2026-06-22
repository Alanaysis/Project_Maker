# 01 - 市场调研：Raft 共识算法

## 1. Raft 算法概述

Raft 是一种分布式共识算法，由 Diego Ongaro 和 John Ousterhout 在 2014 年提出。它的设计目标是比 Paxos 更易于理解，同时提供相同的安全性和活性保证。

### 1.1 核心概念

Raft 将共识问题分解为三个相对独立的子问题：

1. **领导者选举（Leader Election）**
   - 节点通过选举产生领导者
   - 领导者负责处理所有客户端请求
   - 通过心跳机制维持领导地位

2. **日志复制（Log Replication）**
   - 领导者接收客户端请求并追加到日志
   - 领导者将日志条目复制到所有跟随者
   - 当大多数节点确认后，日志被提交

3. **安全性（Safety）**
   - 确保所有节点以相同顺序应用相同的命令
   - 选举限制：只有包含所有已提交日志的节点才能成为领导者

### 1.2 节点状态

Raft 中的每个节点处于以下三种状态之一：

- **跟随者（Follower）**：被动响应请求，不主动发起通信
- **候选人（Candidate）**：发起选举，请求其他节点投票
- **领导者（Leader）**：处理客户端请求，管理日志复制

### 1.3 时间概念

- **任期（Term）**：逻辑时钟，每次选举增加
- **选举超时（Election Timeout）**：跟随者等待心跳的时间
- **心跳间隔（Heartbeat Interval）**：领导者发送心跳的频率

## 2. 现有实现分析

### 2.1 Go 语言实现

| 项目 | Stars | 特点 |
|------|-------|------|
| etcd/raft | 5k+ | 生产级实现，etcd 核心组件 |
| hashicorp/raft | 7k+ | 完整实现，支持多种存储后端 |
| cockroachdb/raft | 2k+ | 针对 CockroachDB 优化 |

### 2.2 etcd/raft 架构

```
┌─────────────────────────────────────┐
│           Application               │
├─────────────────────────────────────┤
│           raft.Node                 │
├─────────────────────────────────────┤
│  ┌─────────┐ ┌─────────┐ ┌───────┐ │
│  │ Storage │ │ Network │ │ State │ │
│  └─────────┘ └─────────┘ └───────┘ │
└─────────────────────────────────────┘
```

### 2.3 关键设计决策

1. **状态机分离**：Raft 核心与状态机解耦
2. **存储抽象**：支持不同的存储后端
3. **网络抽象**：支持不同的传输协议
4. **日志压缩**：支持快照机制

## 3. gRPC 在 Raft 中的应用

### 3.1 RPC 定义

```protobuf
service RaftService {
  rpc RequestVote(RequestVoteRequest) returns (RequestVoteResponse);
  rpc AppendEntries(AppendEntriesRequest) returns (AppendEntriesResponse);
}
```

### 3.2 消息类型

1. **RequestVote**：候选人请求投票
2. **AppendEntries**：领导者复制日志/心跳
3. **InstallSnapshot**：领导者安装快照

## 4. 学习资源

### 4.1 官方资源
- [Raft 论文](https://raft.github.io/raft.pdf)
- [Raft 可视化](http://raft.github.io/)
- [Raft 作者讲解](https://www.youtube.com/watch?v=YbZ3zDzDnrw)

### 4.2 Go 实现参考
- [etcd/raft 源码](https://github.com/etcd-io/raft)
- [hashicorp/raft 源码](https://github.com/hashicorp/raft)

### 4.3 中文资源
- [Raft 一致性算法](https://www.cnblogs.com/mindwind/p/5231986.html)
- [Raft 算法详解](https://zhuanlan.zhihu.com/p/27207160)

## 5. 项目定位

本项目是一个学习型项目，目标是：

1. **理解原理**：通过实现深入理解 Raft 算法
2. **掌握核心**：实现领导者选举和日志复制
3. **实践技能**：使用 Go 和 gRPC 构建分布式系统
4. **可扩展性**：为后续扩展（快照、成员变更）打下基础

## 6. 技术选型

| 组件 | 选择 | 理由 |
|------|------|------|
| 语言 | Go | 并发模型适合分布式系统 |
| RPC | gRPC | 高性能，支持流式通信 |
| 存储 | 内存/BoltDB | 简单实现，可扩展 |
| 配置 | TOML/YAML | 简洁易读 |
| 测试 | Go testing | 标准库，功能完善 |

## 7. 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 网络分区 | 高 | 实现超时重试机制 |
| 并发问题 | 高 | 使用 mutex 保护共享状态 |
| 日志不一致 | 中 | 实现日志修复机制 |
| 性能瓶颈 | 低 | 优化序列化和网络传输 |

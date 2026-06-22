# Raft 共识算法实现

## 项目概述

这是一个学习型的 Raft 共识算法实现项目，旨在深入理解分布式一致性算法的核心原理。通过实际编码实现领导者选举、日志复制和状态机应用等核心功能。

## 学习目标

- **理解 Raft 原理**：掌握 Raft 算法的核心概念和设计思想
- **掌握领导者选举**：实现完整的选举流程，包括任期管理、投票机制
- **学会日志复制**：实现日志的一致性复制和提交机制
- **实践分布式系统**：使用 Go 和 gRPC 构建分布式系统

## 技术栈

- **主语言**：Go 1.22+
- **RPC 框架**：gRPC
- **序列化**：Protocol Buffers
- **存储**：内存存储（可扩展）
- **测试**：Go testing + testify

## 项目结构

```
raft-consensus/
├── cmd/
│   └── server/
│       └── main.go              # 服务器入口
├── internal/
│   ├── raft/
│   │   ├── raft.go              # Raft 核心实现
│   │   ├── election.go          # 领导者选举
│   │   ├── log_replication.go   # 日志复制
│   │   └── state.go             # 状态管理
│   ├── pb/
│   │   ├── raft.proto           # gRPC 服务定义
│   │   └── raft.pb.go           # 生成的代码
│   ├── statemachine/
│   │   └── kv.go                # KV 状态机实现
│   └── storage/
│       └── memory.go            # 内存存储实现
├── configs/
│   └── config.toml              # 配置文件
├── test/
│   ├── election_test.go         # 选举测试
│   ├── log_replication_test.go  # 日志复制测试
│   └── integration_test.go      # 集成测试
├── docs/
│   ├── 01-RESEARCH.md           # 市场调研
│   ├── 02-ARCHITECTURE.md       # 架构设计
│   ├── 03-IMPLEMENTATION.md     # 实现细节
│   ├── 04-TESTING.md            # 测试策略
│   └── 05-DEVELOPMENT.md        # 开发日志
├── LEARNING_NOTES.md            # 学习笔记
├── go.mod                       # Go 模块文件
└── README.md                    # 项目说明
```

## 快速开始

### 环境要求

- Go 1.22+
- Protocol Buffers 编译器
- gRPC 工具

### 安装依赖

```bash
# 安装 Go 依赖
go mod tidy

# 安装 protobuf 编译器
# macOS
brew install protobuf

# Linux
apt-get install -y protobuf-compiler

# 安装 Go protobuf 插件
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
```

### 生成 gRPC 代码

```bash
protoc --go_out=. --go-grpc_out=. internal/pb/raft.proto
```

### 运行测试

```bash
# 运行所有测试
go test ./...

# 运行特定测试
go test ./internal/raft/ -v -run TestElection

# 运行集成测试
go test ./test/ -v -run TestCluster
```

### 启动服务器

```bash
# 启动单个节点
go run cmd/server/main.go -id 1 -port 50051

# 启动集群（需要多个终端）
go run cmd/server/main.go -id 1 -port 50051 -peers "localhost:50052,localhost:50053"
go run cmd/server/main.go -id 2 -port 50052 -peers "localhost:50051,localhost:50053"
go run cmd/server/main.go -id 3 -port 50053 -peers "localhost:50051,localhost:50052"
```

## 核心概念

### 1. 领导者选举

Raft 使用随机化的选举超时来避免选票分割。当跟随者在超时时间内没有收到领导者的心跳时，它会转变为候选人并发起选举。

### 2. 日志复制

领导者接收客户端请求，将命令追加到日志中，然后并行地将日志条目复制到所有跟随者。当大多数节点确认后，日志被提交。

### 3. 安全性

- **选举限制**：只有包含所有已提交日志的候选人才能赢得选举
- **日志匹配**：如果两个日志在某个索引处有相同的任期号，那么它们在该索引之前的所有条目都相同
- **领导者完整性**：如果一个日志条目在某个任期被提交，那么该条目会出现在所有更高任期的领导者日志中

## API 接口

### gRPC 服务

```protobuf
service RaftService {
    rpc RequestVote(RequestVoteRequest) returns (RequestVoteResponse);
    rpc AppendEntries(AppendEntriesRequest) returns (AppendEntriesResponse);
}
```

### 客户端命令

```bash
# 设置键值对
grpcurl -plaintext -d '{"key": "name", "value": "raft"}' localhost:50051 raft.RaftService.Put

# 获取值
grpcurl -plaintext -d '{"key": "name"}' localhost:50051 raft.RaftService.Get
```

## 配置说明

配置文件 `configs/config.toml` 示例：

```toml
[node]
id = 1
address = "localhost:50051"

[election]
timeout_min = 150      # 最小选举超时（毫秒）
timeout_max = 300      # 最大选举超时（毫秒）
heartbeat_interval = 50 # 心跳间隔（毫秒）

[log]
max_entries = 10000    # 最大日志条目数
```

## 学习路径

1. **第一阶段**：理解 Raft 论文和核心概念
2. **第二阶段**：实现领导者选举
3. **第三阶段**：实现日志复制
4. **第四阶段**：实现状态机应用
5. **第五阶段**：测试和优化

## 参考资源

- [Raft 论文](https://raft.github.io/raft.pdf)
- [Raft 可视化](http://raft.github.io/)
- [etcd/raft 实现](https://github.com/etcd-io/raft)
- [hashicorp/raft 实现](https://github.com/hashicorp/raft)

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
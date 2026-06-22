# 简易区块链实现

从零实现一个简易的区块链，理解区块链核心原理。

## 项目概述

本项目是一个用 Go 语言实现的简易区块链系统，包含以下核心功能：

- 区块结构实现
- 工作量证明（PoW）共识算法
- 简单的 P2P 网络
- 命令行钱包

## 学习目标

- 理解区块链数据结构
- 掌握共识算法
- 学会加密哈希

## 技术栈

- 主语言：Go
- 框架：无
- 其他：crypto 库

## 核心循环

```
交易发起 → 交易验证 → 打包成块 → 共识确认 → 链上存储
```

## 项目结构

```
simple-blockchain/
├── docs/                    # 文档
│   ├── 01-RESEARCH.md      # 市场调研
│   ├── 02-ARCHITECTURE.md  # 架构设计
│   ├── 03-IMPLEMENTATION.md # 实现细节
│   ├── 04-TESTING.md       # 测试策略
│   └── 05-DEVELOPMENT.md   # 开发指南
├── main.go                 # 入口文件
├── block.go                # 区块结构
├── blockchain.go           # 区块链管理
├── transaction.go          # 交易处理
├── pow.go                  # 工作量证明
├── wallet.go               # 钱包功能
├── network.go              # P2P 网络
├── crypto.go               # 密码学工具
├── storage.go              # 存储引擎
├── utils.go                # 工具函数
├── *_test.go               # 测试文件
├── go.mod                  # 依赖管理
├── README.md               # 项目说明
└── LEARNING_NOTES.md       # 学习笔记
```

## 快速开始

### 环境要求

- Go 1.21+
- Git

### 安装

```bash
# 克隆项目
git clone <repository-url>
cd simple-blockchain

# 安装依赖
go mod tidy

# 编译项目
go build -o blockchain .
```

### 使用

```bash
# 创建钱包
./blockchain createwallet

# 查询余额
./blockchain getbalance -address <address>

# 发送交易
./blockchain send -from <from> -to <to> -amount <amount>

# 挖矿
./blockchain mine

# 打印区块链
./blockchain printchain

# 启动节点
./blockchain startnode -port 3000
```

## 核心功能

### 1. 区块结构

```go
type Block struct {
    Header       BlockHeader
    Transactions []*Transaction
    Hash         [32]byte
}
```

### 2. 工作量证明

```go
type ProofOfWork struct {
    Block     *Block
    Target    *big.Int
    Difficulty uint32
}
```

### 3. 交易结构

```go
type Transaction struct {
    ID        [32]byte
    Inputs    []*TxInput
    Outputs   []*TxOutput
    Timestamp int64
}
```

### 4. 钱包功能

```go
type Wallet struct {
    PrivateKey *ecdsa.PrivateKey
    PublicKey  []byte
    Address    string
}
```

## 参考项目

- [go-ethereum](https://github.com/ethereum/go-ethereum)
- [bitcoinbook](https://github.com/bitcoinbook/bitcoinbook)
- [blockchain-tutorial](https://github.com/liuchengxu/blockchain-tutorial)

## 文档

- [市场调研](docs/01-RESEARCH.md)
- [架构设计](docs/02-ARCHITECTURE.md)
- [实现细节](docs/03-IMPLEMENTATION.md)
- [测试策略](docs/04-TESTING.md)
- [开发指南](docs/05-DEVELOPMENT.md)
- [学习笔记](LEARNING_NOTES.md)

## 贡献

欢迎提交 Issue 和 Pull Request。

## 许可证

MIT License

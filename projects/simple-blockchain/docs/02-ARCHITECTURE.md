# 02-ARCHITECTURE.md - 项目架构设计

## 1. 系统架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                      命令行界面 (CLI)                        │
├─────────────────────────────────────────────────────────────┤
│                      业务逻辑层                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ 钱包模块 │  │ 交易模块 │  │ 区块模块 │  │ 网络模块 │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
├─────────────────────────────────────────────────────────────┤
│                      核心层                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ 密码学   │  │ 共识算法 │  │ 存储引擎 │  │ P2P通信  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
├─────────────────────────────────────────────────────────────┤
│                      基础设施层                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ 配置管理 │  │ 日志系统 │  │ 工具函数 │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

## 2. 模块划分

### 2.1 核心模块

#### 2.1.1 区块模块 (block.go)
- Block 结构体定义
- 区块序列化/反序列化
- 区块哈希计算
- 默克尔树计算

#### 2.1.2 区块链模块 (blockchain.go)
- Blockchain 结构体
- 区块链初始化
- 添加区块
- 验证区块链完整性
- 区块链持久化

#### 2.1.3 交易模块 (transaction.go)
- Transaction 结构体
- 交易输入/输出
- 交易签名/验证
- 交易序列化

#### 2.1.4 工作量证明模块 (pow.go)
- PoW 结构体
- 难度调整算法
- 挖矿算法
- 验证证明

### 2.2 功能模块

#### 2.2.1 钱包模块 (wallet.go)
- Wallet 结构体
- 密钥对生成
- 地址生成
- 余额查询

#### 2.2.2 网络模块 (network.go)
- P2P 网络管理
- 节点发现
- 消息广播
- 区块同步

### 2.3 工具模块

#### 2.3.1 密码学工具 (crypto.go)
- SHA-256 哈希
- ECDSA 签名
- Base58 编码
- 默克尔树计算

#### 2.3.2 存储工具 (storage.go)
- 文件存储
- 数据库接口
- 缓存管理

## 3. 数据流设计

### 3.1 交易流程
```
用户发起交易
    ↓
创建交易对象
    ↓
钱包签名
    ↓
交易验证
    ↓
广播到网络
    ↓
节点验证
    ↓
进入交易池
    ↓
挖矿打包
    ↓
创建新区块
    ↓
广播区块
    ↓
节点验证区块
    ↓
添加到区块链
```

### 3.2 区块创建流程
```
从交易池获取交易
    ↓
创建区块头
    ↓
计算默克尔树根
    ↓
设置时间戳
    ↓
设置难度值
    ↓
开始挖矿 (PoW)
    ↓
找到满足条件的 Nonce
    ↓
计算区块哈希
    ↓
创建完整区块
    ↓
广播区块
```

## 4. 接口设计

### 4.1 区块接口
```go
type BlockInterface interface {
    Hash() [32]byte
    Serialize() ([]byte, error)
    Deserialize(data []byte) error
    Validate() error
}
```

### 4.2 交易接口
```go
type TransactionInterface interface {
    Hash() [32]byte
    Sign(privKey *ecdsa.PrivateKey) error
    Verify() error
    Serialize() ([]byte, error)
}
```

### 4.3 区块链接口
```go
type BlockchainInterface interface {
    AddBlock(block *Block) error
    GetBlock(hash [32]byte) (*Block, error)
    GetLatestBlock() *Block
    ValidateChain() error
    Save() error
    Load() error
}
```

## 5. 文件结构

```
simple-blockchain/
├── docs/
│   ├── 01-RESEARCH.md
│   ├── 02-ARCHITECTURE.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── src/
│   ├── main.go
│   ├── block.go
│   ├── blockchain.go
│   ├── transaction.go
│   ├── pow.go
│   ├── wallet.go
│   ├── network.go
│   ├── crypto.go
│   ├── storage.go
│   └── utils.go
├── test/
│   ├── block_test.go
│   ├── blockchain_test.go
│   ├── transaction_test.go
│   ├── pow_test.go
│   └── wallet_test.go
├── go.mod
├── README.md
└── LEARNING_NOTES.md
```

## 6. 关键技术点

### 6.1 哈希算法
- 使用 SHA-256 计算区块哈希
- 默克尔树使用双重 SHA-256

### 6.2 签名算法
- 使用 ECDSA (secp256k1 曲线)
- 私钥签名，公钥验证

### 6.3 共识算法
- PoW 难度值动态调整
- 目标哈希前导零个数

### 6.4 网络通信
- TCP 协议
- 自定义消息格式
- 节点发现机制

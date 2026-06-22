# ⛓️ 区块链模块

> 5 个深度学习项目，涵盖区块链、智能合约、DeFi、DApp

---

## 📋 项目列表

| 项目 | 描述 | 技术栈 | 难度 | 状态 |
|------|------|--------|------|------|
| [simple-blockchain](simple-blockchain/) | 简易区块链实现 | Go | ⭐⭐⭐ | ✅ |
| [smart-contract-vm](smart-contract-vm/) | 智能合约虚拟机 | Rust | ⭐⭐⭐⭐⭐⭐ | ✅ |
| [erc20-token](erc20-token/) | ERC20 代币合约 | Solidity, Hardhat | ⭐⭐⭐ | ✅ |
| [decentralized-voting](decentralized-voting/) | 去中心化投票系统 | Solidity, Next.js | ⭐⭐⭐⭐ | ✅ |

---

## 🎯 学习路径

```
区块链基础 → 智能合约 → 代币标准 → DApp 开发
    ↓           ↓           ↓           ↓
  区块结构      EVM        ERC20       前端交互
  共识算法      操作码      代币发行     钱包集成
  P2P网络       Gas计算     代币交易     合约部署
```

### 推荐学习顺序

1. **simple-blockchain** (区块链基础)
   - 学习区块结构和链式存储
   - 理解工作量证明（PoW）共识
   - 掌握 UTXO 交易模型
   - 实现 P2P 网络通信

2. **smart-contract-vm** (智能合约)
   - 学习 EVM 架构和字节码
   - 理解操作码执行流程
   - 掌握 Gas 计算机制
   - 实现栈和内存管理

3. **erc20-token** (代币标准)
   - 学习 ERC20 标准接口
   - 理解代币发行和交易
   - 掌握 Solidity 编程
   - 使用 Hardhat 开发和测试

4. **decentralized-voting** (DApp)
   - 学习去中心化应用架构
   - 理解智能合约设计
   - 掌握前端与合约交互
   - 集成 MetaMask 钱包

---

## 🔧 技术栈

| 技术 | 用途 | 学习资源 |
|------|------|----------|
| **Go** | 区块链实现 | [Go 官方文档](https://go.dev/doc/) |
| **Rust** | 智能合约 VM | [Rust 官方文档](https://doc.rust-lang.org/) |
| **Solidity** | 智能合约语言 | [Solidity 官方文档](https://docs.soliditylang.org/) |
| **Hardhat** | 开发框架 | [Hardhat 官方文档](https://hardhat.org/docs) |
| **ethers.js** | 区块链交互 | [ethers.js 文档](https://docs.ethers.org/) |
| **Next.js** | 前端框架 | [Next.js 文档](https://nextjs.org/docs) |

---

## 📊 项目详情

### 1. simple-blockchain (区块链基础)

**核心功能**：
- 区块结构和 Merkle 树
- 工作量证明（PoW）共识
- UTXO 交易模型
- ECDSA 钱包和签名
- P2P 网络通信

**代码量**：约 2000 行

**快速开始**：
```bash
cd simple-blockchain
go build -o blockchain
./blockchain createwallet
./blockchain mine
./blockchain printchain
```

---

### 2. smart-contract-vm (智能合约 VM)

**核心功能**：
- VM 引擎（fetch-decode-execute 循环）
- 操作码定义（ADD, SUB, MUL, DIV, PUSH, POP, JUMP 等）
- 栈管理（1024 元素 LIFO）
- 线性内存（动态扩展）
- Gas 计算

**代码量**：约 1500 行

**快速开始**：
```bash
cd smart-contract-vm
cargo build
cargo test
```

---

### 3. erc20-token (代币标准)

**核心功能**：
- 两个 Solidity 合约（学习版 + 生产版）
- 38 个测试用例
- 部署和交互脚本
- Hardhat 3.9.0 配置

**代码量**：约 1000 行

**快速开始**：
```bash
cd erc20-token
npm install
npx hardhat test
npx hardhat run scripts/deploy-learning-token.js --network localhost
```

---

### 4. decentralized-voting (DApp)

**核心功能**：
- 投票智能合约（创建、提案、投票、计票、结束）
- Next.js 前端界面
- MetaMask 钱包集成
- 完整测试

**代码量**：约 2000 行

**快速开始**：
```bash
cd decentralized-voting
npm install
npx hardhat node
npx hardhat run scripts/deploy.ts --network localhost
cd frontend && npm run dev
```

---

## 📚 学习资源

### 书籍
- 《Mastering Bitcoin》
- 《Mastering Ethereum》
- 《Solidity 编程》

### 课程
- [CryptoZombies](https://cryptozombies.io/)
- [Ethereum Smart Contract Security](https://www.udemy.com/course/ethereum-smart-contract-security/)

### 开源项目
- [go-ethereum](https://github.com/ethereum/go-ethereum)
- [OpenZeppelin](https://github.com/OpenZeppelin/openzeppelin-contracts)
- [scaffold-eth](https://github.com/scaffold-eth/scaffold-eth)

---

## 🔗 相关链接

- [返回主 README](../README.md)
- [学习路径图](../LEARNING_PATHS.md)
- [项目索引](../PROJECT_INDEX.md)

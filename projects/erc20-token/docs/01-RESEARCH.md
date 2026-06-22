# 市场调研报告

## 1. 问题定义

### 要解决的问题
在以太坊区块链上创建可互换的（fungible）数字代币，使其可以在钱包之间自由转移，并能与 DeFi 协议集成。

### 为什么这个问题重要
- ERC20 是以太坊上最广泛使用的代币标准
- 截至 2025 年，以太坊上有超过 50 万个 ERC20 代币
- 几乎所有 DeFi 协议（Uniswap, Aave, Compound）都基于 ERC20
- 理解 ERC20 是进入 Web3 开发的第一步

## 2. 同类型项目概览

| 项目 | GitHub Stars | 核心特点 | 技术栈 | 最后更新 | 链接 |
|------|-------------|----------|--------|----------|------|
| OpenZeppelin Contracts | 25k+ | 经过审计、生产级 | Solidity | 持续更新 | [GitHub](https://github.com/OpenZeppelin/openzeppelin-contracts) |
| Solmate | 1.5k+ | Gas 优化、极简 | Solidity | 2024 | [GitHub](https://github.com/transmissions11/solmate) |
| ERC20 (Solmate) | - | 高性能实现 | Solidity | 2024 | [GitHub](https://github.com/transmissions11/solmate) |
| WTF-Solidity | 5k+ | 中文教学、循序渐进 | Solidity | 2024 | [GitHub](https://github.com/AmazingAng/WTF-Solidity) |
| Solidity by Example | 3k+ | 示例驱动、易于理解 | Solidity | 2024 | [网站](https://solidity-by-example.org/) |

## 3. 技术变体分析

### 核心循环的变体

**基础版本**：
```
部署合约 → 铸造代币 → 转账 → 查询余额
```

**变体1：带销毁功能的 ERC20**
```
部署合约 → 铸造代币 → 转账 → 销毁代币 → 查询余额
```
- 发力方向：减少流通量，可能提升代币价值
- 为什么这么做：某些场景需要通缩机制
- 适用场景：治理代币、回购销毁机制

**变体2：带许可功能的 ERC20 (EIP-2612)**
```
部署合约 → 铸造代币 → 签名许可 → 无 Gas 授权 → 转账
```
- 发力方向：改善用户体验，减少一次交易
- 为什么这么做：传统 approve 需要单独一笔交易
- 适用场景：DeFi 协议、需要 gasless 体验的应用

**变体3：可暂停的 ERC20**
```
部署合约 → 铸造代币 → 转账 → [紧急暂停] → 恢复 → 转账
```
- 发力方向：安全控制，应对紧急情况
- 为什么这么做：某些场景需要暂停合约功能
- 适用场景：ICO 合约、需要管理控制的代币

## 4. 技术演进路径

```
ERC20 基础 → ERC20 + Burn → ERC20 + Permit → ERC20 + Votes → ERC20 + Flash Mint
    ↓              ↓              ↓                ↓              ↓
  标准转账      通缩机制      无 Gas 授权       治理投票       闪电贷
```

## 5. 各项目的发力方向

| 项目 | 主要发力方向 | 为什么选择这个方向 |
|------|-------------|-------------------|
| OpenZeppelin | 安全性 + 功能全面 | 企业级应用需要最高安全标准 |
| Solmate | Gas 优化 | 高频交易场景需要低成本 |
| WTF-Solidity | 教学友好 | 中文开发者学习需求大 |
| Solidity by Example | 示例驱动 | 快速理解核心概念 |

## 6. 我们的选择

基于调研，我们选择**从零实现 + OpenZeppelin 对比**的方案：

### 选择理由
1. **学习价值**：从零实现能深入理解每一行代码
2. **对比学习**：与 OpenZeppelin 实现对比，理解最佳实践
3. **循序渐进**：先学原理，再用工具

### 学习价值
- 覆盖 ERC20 标准的所有核心概念
- 理解 Solidity 安全编程模式
- 掌握 Hardhat 开发工作流
- 为学习更复杂的 DeFi 协议打下基础

## 7. 延伸阅读

- [ERC20 标准原文 (EIP-20)](https://eips.ethereum.org/EIPS/eip-20)
- [OpenZeppelin ERC20 文档](https://docs.openzeppelin.com/contracts/5.x/erc20)
- [Solidity 官方文档](https://docs.soliditylang.org/)
- [Ethereum 开发者文档](https://ethereum.org/en/developers/docs/)
- [DeFi Pulse](https://defipulse.com/) - 了解 DeFi 生态

# ERC20 代币合约

## 学习目标

通过这个项目，你将掌握：
- [ ] 理解 ERC20 标准的核心接口和设计思想
- [ ] 掌握 Solidity 编程语言的基础语法和最佳实践
- [ ] 学会使用 Hardhat 框架进行合约编译、测试和部署
- [ ] 理解 approve/transferFrom 授权模式的工作原理
- [ ] 学会使用 OpenZeppelin 构建生产级合约

## 技术栈

| 技术 | 用途 | 学习难度 | 官方文档 |
|------|------|----------|----------|
| Solidity 0.8.28 | 智能合约语言 | ⭐⭐⭐ | [docs](https://docs.soliditylang.org/) |
| Hardhat 3.x | 开发框架 | ⭐⭐ | [docs](https://hardhat.org/docs) |
| ethers.js 6.x | 以太坊交互库 | ⭐⭐ | [docs](https://docs.ethers.org/) |
| OpenZeppelin | 合约库 | ⭐⭐ | [docs](https://docs.openzeppelin.com/) |
| Chai | 测试断言库 | ⭐ | [docs](https://www.chaijs.com/) |

## 重点难点

### 重点1：ERC20 标准接口
**为什么重要**：ERC20 是以太坊上最基础的代币标准，理解它是学习 DeFi 的基础。
**关键代码**：`contracts/LearningToken.sol`
**理解要点**：
- 6 个核心函数：`name`, `symbol`, `decimals`, `totalSupply`, `balanceOf`, `transfer`
- 3 个可选函数：`approve`, `transferFrom`, `allowance`
- 2 个事件：`Transfer`, `Approval`

### 重点2：approve/transferFrom 授权模式
**为什么重要**：这是 DEX、借贷协议等 DeFi 应用的核心机制。
**关键代码**：`contracts/LearningToken.sol:130-165`
**理解要点**：
- Owner 先调用 `approve(spender, amount)` 授权
- Spender 再调用 `transferFrom(owner, to, amount)` 转账
- 授权额度在转账后自动减少

### 重点3：Solidity 安全性
**为什么重要**：智能合约一旦部署不可修改，安全性至关重要。
**关键代码**：`contracts/LearningToken.sol` 中的 `require` 语句
**理解要点**：
- Solidity 0.8+ 内置溢出保护，不需要 SafeMath
- 必须检查零地址
- 必须检查余额和授权额度

## 值得思考

### 1. 为什么选择从零实现而不是直接用 OpenZeppelin？
**背景**：OpenZeppelin 提供了经过审计的 ERC20 实现
**权衡**：
- 从零实现：学习价值高，理解每一行代码
- 使用 OpenZeppelin：生产级安全，节省开发时间
**结论**：本项目同时提供两种实现，先学原理再用工具

### 2. 为什么 Solidity 0.8+ 不需要 SafeMath？
**背景**：早期 Solidity 版本需要 SafeMath 防止溢出
**原因**：Solidity 0.8+ 在算术运算时自动检查溢出/下溢，溢出时会 revert
**结论**：使用旧版本代码时要注意 SafeMath，新版本可以省略

### 3. 为什么需要 increaseAllowance 而不只是 approve？
**背景**：直接调用 approve 存在前端攻击风险
**原因**：如果用户先授权 100，想改成 150，攻击者可以在两次 approve 之间使用旧的 100 额度
**结论**：`increaseAllowance` 和 `decreaseAllowance` 是更安全的做法

## 快速开始

### 环境要求
- Node.js 18+
- npm 或 yarn

### 安装
```bash
cd projects/erc20-token

# 安装依赖
npm install
```

### 编译合约
```bash
npx hardhat compile
```

### 运行测试
```bash
npx hardhat test
```

### 运行示例
```bash
npx hardhat run examples/basic-usage.js
```

### 部署合约
```bash
# 部署 LearningToken（自定义实现）
npx hardhat run scripts/deploy-learning-token.js

# 部署 MyToken（OpenZeppelin 实现）
npx hardhat run scripts/deploy-my-token.js
```

## 项目结构

```
erc20-token/
├── contracts/
│   ├── LearningToken.sol    # 自定义 ERC20 实现（学习用）
│   └── MyToken.sol          # OpenZeppelin 实现（生产用）
├── test/
│   ├── LearningToken.test.js # LearningToken 测试（26 个用例）
│   └── MyToken.test.js       # MyToken 测试（12 个用例）
├── scripts/
│   ├── deploy-learning-token.js  # LearningToken 部署脚本
│   ├── deploy-my-token.js        # MyToken 部署脚本
│   └── interact.js               # 合约交互脚本
├── examples/
│   └── basic-usage.js       # 基础使用示例
├── docs/                    # 项目文档
├── hardhat.config.js        # Hardhat 配置
└── package.json
```

## 相关资源

- [ERC20 标准 (EIP-20)](https://eips.ethereum.org/EIPS/eip-20)
- [OpenZeppelin ERC20 文档](https://docs.openzeppelin.com/contracts/5.x/erc20)
- [Solidity by Example - ERC20](https://solidity-by-example.org/app/erc20/)
- [WTF Solidity 教程](https://github.com/AmazingAng/WTF-Solidity)
- [Hardhat 文档](https://hardhat.org/docs)

## 学习路径

建议学习顺序：
1. 阅读 [01-RESEARCH.md](docs/01-RESEARCH.md) 了解 ERC20 的背景和生态
2. 阅读 [02-REQUIREMENTS.md](docs/02-REQUIREMENTS.md) 理解功能需求
3. 阅读 [03-DESIGN.md](docs/03-DESIGN.md) 学习合约设计
4. 阅读 [04-PRODUCT.md](docs/04-PRODUCT.md) 理解产品思维
5. 阅读 [05-DEVELOPMENT.md](docs/05-DEVELOPMENT.md) 开始开发
6. 运行 `examples/basic-usage.js` 看效果
7. 阅读源代码，重点关注注释中的 ⭐ 标记
8. 运行测试 `npx hardhat test`，理解测试用例
9. 完成 [LEARNING_NOTES.md](LEARNING_NOTES.md) 中的练习

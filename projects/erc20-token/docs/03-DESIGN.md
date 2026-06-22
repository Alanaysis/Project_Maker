# 技术设计文档

## 1. 架构概述

### 整体架构

```
                    +------------------+
                    |   User/Frontend  |
                    +--------+---------+
                             |
                    +--------v---------+
                    |   Hardhat CLI    |
                    | (compile/test/   |
                    |  deploy/run)     |
                    +--------+---------+
                             |
              +--------------+--------------+
              |                             |
     +--------v--------+          +--------v--------+
     |  Solidity       |          |  JavaScript     |
     |  Contracts      |          |  Tests/Scripts  |
     +-----------------+          +-----------------+
     | LearningToken   |          | test/           |
     | MyToken (OZ)    |          | scripts/        |
     +-----------------+          | examples/       |
              |                   +-----------------+
     +--------v--------+
     | OpenZeppelin    |
     | Contracts       |
     +-----------------+
```

### 模块划分

| 模块 | 职责 | 文件位置 |
|------|------|----------|
| LearningToken | 自定义 ERC20 实现（学习用） | `contracts/LearningToken.sol` |
| MyToken | OpenZeppelin 实现（生产用） | `contracts/MyToken.sol` |
| 测试模块 | 验证合约功能 | `test/` |
| 部署模块 | 部署合约到网络 | `scripts/` |
| 示例模块 | 展示使用方式 | `examples/` |

## 2. 核心流程

### ERC20 转账流程

```
用户调用 transfer(to, amount)
         |
         v
    检查 to != 零地址
         |
         v
    检查 balance[msg.sender] >= amount
         |
         v
    扣除发送者余额
    增加接收者余额
         |
         v
    发射 Transfer 事件
         |
         v
      返回 true
```

### 授权转账流程 (approve + transferFrom)

```
步骤1: Owner 调用 approve(spender, amount)
         |
         v
    记录 allowance[owner][spender] = amount
    发射 Approval 事件

步骤2: Spender 调用 transferFrom(owner, to, amount)
         |
         v
    检查 to != 零地址
         |
         v
    检查 balance[owner] >= amount
         |
         v
    检查 allowance[owner][spender] >= amount
         |
         v
    减少 allowance[owner][spender]
    扣除 owner 余额
    增加 to 余额
         |
         v
    发射 Transfer 事件
```

## 3. 数据设计

### 核心数据结构

```solidity
// 代币基本信息
string public name;          // 代币名称，如 "Learning Token"
string public symbol;        // 代币符号，如 "LT"
uint8  public decimals;      // 小数位数，通常为 18
uint256 public totalSupply;  // 总供应量

// ⭐ 核心映射
mapping(address => uint256) private _balances;
// 地址 => 余额

mapping(address => mapping(address => uint256)) private _allowances;
// 授权人 => (被授权人 => 授权额度)
```

### 为什么使用 mapping 而不是数组？

| 维度 | mapping | array |
|------|---------|-------|
| 查询效率 | O(1) | O(n) |
| Gas 消耗 | 固定 | 随大小增长 |
| 迭代能力 | 不支持 | 支持 |
| 适用场景 | 地址 -> 值的映射 | 需要遍历的场景 |

**结论**：ERC20 的余额和授权是典型的 key-value 查询场景，使用 mapping 最合适。

## 4. 接口设计

### ERC20 标准接口

```solidity
// 必须实现的函数
function name() external view returns (string memory);
function symbol() external view returns (string memory);
function decimals() external view returns (uint8);
function totalSupply() external view returns (uint256);
function balanceOf(address account) external view returns (uint256);
function transfer(address to, uint256 amount) external returns (bool);

// 授权相关函数
function approve(address spender, uint256 amount) external returns (bool);
function allowance(address owner, address spender) external view returns (uint256);
function transferFrom(address from, address to, uint256 amount) external returns (bool);

// 必须发射的事件
event Transfer(address indexed from, address indexed to, uint256 value);
event Approval(address indexed owner, address indexed spender, uint256 value);
```

### 扩展接口（我们的实现额外提供）

```solidity
function increaseAllowance(address spender, uint256 addedValue) external returns (bool);
function decreaseAllowance(address spender, uint256 subtractedValue) external returns (bool);
```

## 5. 技术选型

### 选型决策

| 决策点 | 选项A | 选项B | 最终选择 |
|--------|-------|-------|----------|
| 合约语言 | Solidity | Vyper | Solidity |
| 开发框架 | Hardhat | Foundry | Hardhat |
| 合约库 | OpenZeppelin | 自实现 | 两者都用 |
| 测试框架 | Mocha/Chai | Forge Test | Mocha/Chai |
| 网络 | 本地 Hardhat | 测试网 | 本地优先 |

### 选择理由

**选择 Solidity 而不是 Vyper**：
1. 生态系统更成熟
2. 学习资源更丰富
3. 大多数项目使用 Solidity

**选择 Hardhat 而不是 Foundry**：
1. JavaScript 生态，对 Web 开发者更友好
2. 插件生态丰富
3. 调试工具更好

## 6. 设计决策与权衡

### 决策1：是否使用 SafeMath？

**背景**：Solidity 0.7 及之前版本，整数运算可能溢出

**方案对比**：

| 维度 | 使用 SafeMath | 不使用 SafeMath |
|------|--------------|----------------|
| 安全性 | 高 | 高（Solidity 0.8+） |
| Gas 消耗 | 更高 | 更低 |
| 代码量 | 更多 | 更少 |
| 兼容性 | 全版本 | 仅 0.8+ |

**最终选择**：不使用 SafeMath

**理由**：
1. Solidity 0.8+ 内置溢出检查
2. 溢出时自动 revert
3. 节省 Gas 消耗

### 决策2：是否实现 ERC165 接口检查？

**背景**：ERC165 允许合约声明自己支持哪些接口

**最终选择**：暂不实现

**理由**：
1. ERC20 标准不要求 ERC165
2. 增加复杂度
3. 可以后续扩展

### 决策3：是否实现 EIP-2612 Permit？

**背景**：Permit 允许通过签名授权，无需单独的 approve 交易

**最终选择**：在 MyToken 中实现，LearningToken 中不实现

**理由**：
1. Permit 增加复杂度（需要 EIP-712 签名）
2. 学习项目先掌握基础
3. OpenZeppelin 提供了 Permit 的实现

## 7. 扩展性设计

### 预留的扩展点

1. **铸造功能**：可以添加 `mint` 函数，仅 owner 可调用
2. **销毁功能**：可以添加 `burn` 函数，持有者可销毁自己的代币
3. **暂停功能**：可以继承 `ERC20Pausable` 实现紧急暂停
4. **投票功能**：可以继承 `ERC20Votes` 实现治理投票

### 如何扩展

```solidity
// 示例：添加铸造功能
contract MyToken is ERC20, Ownable {
    constructor() ERC20("MyToken", "MTK") Ownable(msg.sender) {}

    function mint(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
    }
}
```

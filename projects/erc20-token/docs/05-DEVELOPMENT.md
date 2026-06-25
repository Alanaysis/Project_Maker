# 开发手册

## 1. 环境搭建

### 系统要求

- 操作系统：Windows/macOS/Linux
- Node.js：18+ (Solidity 实现)
- Python：3.8+ (Python 实现)
- npm：9+

### Solidity 实现 - 安装步骤

```bash
# 1. 进入项目目录
cd projects/erc20-token

# 2. 安装依赖
npm install

# 3. 验证安装
npx hardhat --version
# 应该显示 Hardhat 3.x.x

# 4. 编译合约
npx hardhat compile

# 5. 运行测试
npx hardhat test
```

### Python 实现 - 安装步骤

```bash
# 1. 进入 Python 目录
cd projects/erc20-token/python

# 2. 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行测试（67 个用例）
python3 -m pytest tests/ -v

# 5. 运行示例
python3 examples/basic_usage.py
```

## 2. 项目结构

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

## 3. 核心模块解析

### 模块1：LearningToken.sol

**文件位置**：`contracts/LearningToken.sol`

**职责**：从零实现 ERC20 标准，用于学习

**核心代码**：

```solidity
// ⭐ 核心数据结构
mapping(address => uint256) private _balances;
mapping(address => mapping(address => uint256)) private _allowances;

// ⭐ 核心函数 - transfer
function transfer(address to, uint256 amount) public returns (bool) {
    require(to != address(0), "LearningToken: transfer to the zero address");
    require(_balances[msg.sender] >= amount, "LearningToken: insufficient balance");

    _balances[msg.sender] -= amount;
    _balances[to] += amount;

    emit Transfer(msg.sender, to, amount);
    return true;
}
```

**理解要点**：
- mapping 是 Solidity 中的哈希表，查询复杂度 O(1)
- require 语句用于输入验证，失败时 revert
- emit 用于发射事件，供前端和索引器监听

### 模块2：Python ERC20 实现

**文件位置**：`python/src/erc20.py`

**职责**：用 Python 实现完整的 ERC20 标准，包含 Mint/Burn/Pause 扩展

**核心代码**：

```python
@dataclass
class ERC20Token:
    name: str
    symbol: str
    decimals: int = 18
    owner: str = ""
    max_supply: int = 0  # 0 means unlimited

    _total_supply: int = field(default=0)
    _balances: dict[str, int] = field(default_factory=dict)
    _allowances: dict[str, dict[str, int]] = field(default_factory=dict)
    _paused: bool = field(default=False)
```

**Python 实现特点**：
- 使用 `@dataclass` 简化数据类定义
- 类型提示 (Type Hints) 提高代码可读性
- 自定义异常类提供清晰的错误信息
- 事件系统模拟区块链事件日志

**Python 测试覆盖**：
- 67 个测试用例，覆盖所有功能
- 包含安全测试、边界测试、集成测试

### 模块3：MyToken.sol

**文件位置**：`contracts/MyToken.sol`

**职责**：使用 OpenZeppelin 实现生产级 ERC20

**核心代码**：

```solidity
// ⭐ 继承 OpenZeppelin 的 ERC20 基础合约
contract MyToken is ERC20, ERC20Burnable, ERC20Permit, Ownable {
    constructor(uint256 initialSupply)
        ERC20("MyToken", "MTK")
        ERC20Permit("MyToken")
        Ownable(msg.sender)
    {
        _mint(msg.sender, initialSupply * 10 ** decimals());
    }

    // 仅 owner 可以铸造
    function mint(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
    }
}
```

**理解要点**：
- 继承是 Solidity 的核心特性，可以复用代码
- OpenZeppelin 提供了经过审计的安全实现
- onlyOwner 是权限控制修饰符

## 4. 重点难点攻克

### 难点1：approve/transferFrom 授权机制

**问题描述**：为什么需要 approve + transferFrom 两步操作？

**解决方案**：
1. Owner 调用 approve 授权 Spender 可以使用的额度
2. Spender 调用 transferFrom 使用授权额度进行转账
3. 授权额度在转账后自动减少

**关键代码**：
```solidity
// ⭐ 授权函数
function approve(address spender, uint256 amount) public returns (bool) {
    _allowances[msg.sender][spender] = amount;
    emit Approval(msg.sender, spender, amount);
    return true;
}

// ⭐ 使用授权转账
function transferFrom(address from, address to, uint256 amount) public returns (bool) {
    if (msg.sender != from) {
        uint256 currentAllowance = _allowances[from][msg.sender];
        require(currentAllowance >= amount, "LearningToken: insufficient allowance");
        _allowances[from][msg.sender] = currentAllowance - amount;
    }
    // ... 执行转账
}
```

**学习要点**：
- 这是 DEX（如 Uniswap）的核心机制
- 用户先授权 DEX 合约使用其代币
- DEX 再调用 transferFrom 完成交易

### 难点2：Solidity 0.8+ 的溢出保护

**问题描述**：早期 Solidity 版本需要 SafeMath 防止整数溢出

**解决方案**：
- Solidity 0.8+ 内置溢出检查
- 溢出时自动 revert
- 不需要额外的 SafeMath 库

**关键代码**：
```solidity
// Solidity 0.8+：自动检查溢出
_balances[msg.sender] -= amount;  // 如果 underflow，自动 revert
_balances[to] += amount;          // 如果 overflow，自动 revert
```

**学习要点**：
- 使用 Solidity 0.8+ 可以省略 SafeMath
- 但在处理外部合约返回值时仍需小心

## 5. 调试技巧

### 常用调试方法

1. **Hardhat Console**
   ```bash
   npx hardhat console
   ```

2. **事件日志**
   ```javascript
   const tx = await token.transfer(addr1, amount);
   const receipt = await tx.wait();
   console.log(receipt.logs);
   ```

3. **require 错误信息**
   ```solidity
   require(condition, "Error message here");
   ```

### 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| "insufficient balance" | 余额不足 | 检查发送者余额 |
| "insufficient allowance" | 授权额度不足 | 先调用 approve |
| "transfer to the zero address" | 转账到零地址 | 检查接收地址 |
| 编译失败 | Solidity 版本不匹配 | 检查 pragma 和 hardhat.config.js |

## 6. 性能优化

### Gas 优化技巧

1. **使用 mapping 而不是 array**
   - mapping 查询 O(1)，array 查询 O(n)

2. **减少 storage 操作**
   - storage 读写比 memory 贵很多

3. **使用 Solidity 0.8+**
   - 内置溢出检查，省略 SafeMath 调用

4. **启用 optimizer**
   ```javascript
   // hardhat.config.js
   solidity: {
     settings: {
       optimizer: {
         enabled: true,
         runs: 200
       }
     }
   }
   ```

## 7. 扩展指南

### 如何添加新功能

1. **添加铸造功能**
   ```solidity
   function mint(address to, uint256 amount) public onlyOwner {
       _mint(to, amount);
   }
   ```

2. **添加销毁功能**
   ```solidity
   function burn(uint256 amount) public {
       _burn(msg.sender, amount);
   }
   ```

3. **添加暂停功能**
   ```solidity
   import "@openzeppelin/contracts/utils/Pausable.sol";

   contract MyToken is ERC20, Pausable {
       function pause() public onlyOwner {
           _pause();
       }

       function unpause() public onlyOwner {
           _unpause();
       }
   }
   ```

### 代码规范

- 遵循 [Solidity 风格指南](https://docs.soliditylang.org/en/latest/style-guide.html)
- 添加 NatSpec 注释
- 使用有意义的变量名
- 编写全面的测试

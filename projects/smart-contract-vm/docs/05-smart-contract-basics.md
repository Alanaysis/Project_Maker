# 智能合约基础

## 什么是智能合约？

智能合约是运行在区块链上的程序，当满足预定条件时自动执行。它由 Nick Szabo 在 1990 年代提出，以太坊是第一个实现智能合约的区块链平台。

## 智能合约的特点

### 1. 自动执行
一旦部署，合约代码会按照预设逻辑自动执行，无需人工干预。

### 2. 不可篡改
部署后代码无法修改，确保了执行的确定性和可信赖性。

### 3. 去中心化
合约运行在分布式网络上，不存在单点故障。

### 4. 透明性
所有交易和状态变化都是公开可验证的。

## 智能合约生命周期

```
┌─────────────┐
│  编写代码    │  (Solidity, Vyper, etc.)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  编译字节码  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  部署合约    │  (发送部署交易)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  执行合约    │  (调用合约函数)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  状态更新    │  (更新区块链状态)
└─────────────┘
```

## 合约执行模型

### 调用栈

EVM 使用调用栈管理合约调用：
- 每个调用有自己的栈、内存和存储视图
- 调用深度限制为 1024
- CALL 指令创建新的执行上下文

### 消息调用

```
CALL:
- 调用另一个合约
- 可以传递 ETH
- 创建新的执行上下文
- 返回值通过栈传递

DELEGATECALL:
- 使用当前合约的存储
- 使用目标合约的代码
- 用于代理模式

STATICCALL:
- 只读调用
- 不能修改状态
```

## 简单合约示例

### 存储合约

```solidity
// Solidity 代码
contract SimpleStorage {
    uint256 storedValue;

    function store(uint256 value) public {
        storedValue = value;
    }

    function retrieve() public view returns (uint256) {
        return storedValue;
    }
}
```

对应的简化字节码：

```
// store 函数
PUSH1 value    // 压入要存储的值
PUSH1 0        // 存储键
SSTORE         // 存储到区块链

// retrieve 函数
PUSH1 0        // 存储键
SLOAD          // 从存储读取
```

### 计数器合约

```solidity
contract Counter {
    uint256 public count;

    function increment() public {
        count += 1;
    }

    function decrement() public {
        require(count > 0);
        count -= 1;
    }
}
```

## 合约安全

### 常见漏洞

1. **重入攻击 (Reentrancy)**
   - 在状态更新前进行外部调用
   - 解决方案：使用检查-生效-交互模式

2. **整数溢出/下溢**
   - 算术运算超出范围
   - 解决方案：使用 SafeMath 库

3. **访问控制**
   - 缺少权限检查
   - 解决方案：使用 onlyOwner 修饰符

4. **Gas 限制**
   - 循环消耗过多 Gas
   - 解决方案：限制循环次数

### 安全最佳实践

```solidity
// 使用检查-生效-交互模式
function withdraw() public {
    uint256 balance = balances[msg.sender];
    require(balance > 0);

    // 先更新状态
    balances[msg.sender] = 0;

    // 再进行外部调用
    (bool success, ) = msg.sender.call{value: balance}("");
    require(success);
}
```

## 在本项目中的实现

本项目实现了一个简化的智能合约虚拟机，支持：

1. **基本操作码**: 算术、比较、位运算
2. **栈操作**: PUSH、POP、DUP、SWAP
3. **内存操作**: MLOAD、MSTORE
4. **存储操作**: SLOAD、SSTORE
5. **跳转操作**: JUMP、JUMPI
6. **Gas 计量**: 防止无限循环

### 示例合约

```rust
// 使用汇编器构建合约
let code = Assembler::new()
    .push1(42)       // 要存储的值
    .push1(0)        // 存储键
    .sstore()        // 存储
    .push1(0)        // 存储键
    .sload()         // 读取
    .stop()          // 停止
    .build();
```

# Gas 计算

## Gas 的作用

Gas 是 EVM 中的执行成本单位，用于：
1. **防止资源滥用**: 限制单笔交易的计算量
2. **经济激励**: 矿工/验证者获得 Gas 费用作为报酬
3. **安全机制**: 防止无限循环和恶意代码

## Gas 定价

### 基本操作码 Gas 成本

| 操作码 | Gas 成本 | 说明 |
|--------|----------|------|
| ADD, SUB, MUL, DIV | 3 | 算术运算 |
| LT, GT, EQ | 3 | 比较运算 |
| AND, OR, XOR, NOT | 3 | 位运算 |
| PUSH, DUP, SWAP | 3 | 栈操作 |
| MLOAD, MSTORE | 3 | 内存操作 |
| SLOAD | 200 | 存储读取 |
| SSTORE | 20000 | 存储写入 |
| JUMP | 8 | 跳转 |
| JUMPI | 10 | 条件跳转 |

### 内存扩展成本

内存扩展按以下公式计算：

```
memory_cost = words * 3

其中 words = ceil(new_size / 32) - ceil(old_size / 32)
```

### 存储操作成本

存储操作的成本取决于状态变化：

```
SSTORE:
- 从 0 写入非 0: 20000 gas (首次写入)
- 从非 0 写入非 0: 5000 gas (更新)
- 从非 0 写入 0: 5000 gas + 15000 gas 退款

SLOAD: 200 gas
```

## Gas 计量器实现

```rust
pub struct GasMeter {
    used: u64,   // 已使用 Gas
    limit: u64,  // Gas 上限
}

impl GasMeter {
    pub fn consume(&mut self, amount: u64) -> Result<(), VmError> {
        if self.used + amount > self.limit {
            return Err(VmError::OutOfGas);
        }
        self.used += amount;
        Ok(())
    }
}
```

## Gas 优化技巧

### 1. 减少内存使用

```rust
// 不好的做法：频繁扩展内存
for i in 0..100 {
    mstore(i * 32, value);  // 每次扩展
}

// 好的做法：预先分配
// 先计算需要的内存大小，一次性扩展
```

### 2. 使用栈而非内存

```rust
// 不好的做法：使用内存存储临时值
PUSH 1
PUSH 0
MSTORE
PUSH 0
MLOAD

// 好的做法：直接使用栈
PUSH 1
DUP1
```

### 3. 减少存储操作

```rust
// 不好的做法：频繁写入存储
SSTORE key1 value1  // 20000 gas
SSTORE key2 value2  // 20000 gas

// 好的做法：批量操作或使用内存缓存
```

## Gas 估算

在执行前估算 Gas 需求：

```rust
fn estimate_gas(code: &[u8]) -> u64 {
    let mut gas = 0;
    let mut pc = 0;

    while pc < code.len() {
        let opcode = code[pc];
        gas += get_opcode_gas(opcode);
        pc += 1 + get_extra_bytes(opcode);
    }

    gas
}
```

## 实际 Gas 限制

以太坊网络的 Gas 限制：
- **区块 Gas 限制**: ~30,000,000 gas
- **单笔交易**: 通常 21,000 - 500,000 gas
- **Gas 价格**: 由市场决定 (Gwei)

## 在本项目中的实现

本项目简化了 Gas 计算：

1. **固定成本**: 每个操作码有固定 Gas 成本
2. **简化内存成本**: 按字计算，每字 3 gas
3. **简化存储成本**: SLOAD 200 gas，SSTORE 20000 gas
4. **无退款机制**: 简化实现不包含 Gas 退款

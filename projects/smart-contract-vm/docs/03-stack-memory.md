# 栈和内存管理

## 栈 (Stack)

### 概述

栈是 EVM 中最重要的数据结构，用于临时存储计算值。

### 特性

- **大小**: 最多 1024 个元素
- **元素大小**: 256 位（本实现使用 64 位简化）
- **操作**: 后进先出 (LIFO)
- **访问**: 只能访问栈顶元素，或通过 DUP/SWAP 访问其他元素

### 基本操作

```
PUSH x  : 将 x 压入栈顶
POP     : 弹出栈顶元素
DUP n   : 复制第 n 个元素到栈顶
SWAP n  : 交换栈顶和第 n 个元素
```

### 栈操作示例

```
初始栈: []

PUSH 1:  [1]
PUSH 2:  [1, 2]
PUSH 3:  [1, 2, 3]

DUP1:    [1, 2, 3, 3]
SWAP2:   [1, 3, 2, 3]

ADD:     [1, 3, 5]      (2 + 3 = 5)
POP:     [1, 3]
```

### 栈深度检查

执行栈操作时必须检查栈深度：
- PUSH 操作前检查是否已满 (1024)
- POP/DUP/SWAP 操作前检查是否有足够元素

## 内存 (Memory)

### 概述

内存是线性字节数组，用于存储临时数据。

### 特性

- **寻址**: 按字节寻址
- **大小**: 动态扩展，最大 1MB（本实现）
- **初始化**: 全部为 0
- **成本**: 按扩展大小收费

### 内存操作

```
MLOAD offset   : 从 offset 读取 32 字节
MSTORE offset  : 向 offset 写入 32 字节
MSIZE          : 返回当前内存大小
```

### 内存扩展

当访问超出当前内存大小的地址时，内存会自动扩展：

```rust
// 伪代码
fn expand_memory(new_size: usize) {
    if new_size > current_size {
        // 扩展内存并填充 0
        memory.resize(new_size, 0);
        // 计算并收取 Gas
        gas_cost = calculate_memory_gas(current_size, new_size);
        consume_gas(gas_cost);
    }
}
```

### 内存成本计算

内存成本按 32 字节（一个字）计算：

```
memory_cost = words * 3

其中 words = ceil(memory_size / 32)
```

## 存储 (Storage)

### 概述

存储是持久化的键值对，存储在区块链上。

### 特性

- **持久性**: 数据永久存储在区块链上
- **键值对**: 256 位键 -> 256 位值
- **成本**: 读写成本很高

### 存储操作

```
SLOAD key    : 读取键 key 对应的值
SSTORE key value : 将 value 存储到键 key
```

### Gas 成本

存储操作的 Gas 成本很高：
- SLOAD: 200 gas
- SSTORE: 20000 gas (首次写入)
- SSTORE: 5000 gas (更新已有值)

## 数据流示例

```
// 将两个数相加并存储结果

PUSH1 10     // 栈: [10]
PUSH1 20     // 栈: [10, 20]
ADD          // 栈: [30]
PUSH1 0      // 栈: [30, 0]
MSTORE       // 内存[0..32] = 30, 栈: []

PUSH1 0      // 栈: [0]
MLOAD        // 栈: [30] (从内存读取)
PUSH1 1      // 栈: [30, 1]
SSTORE       // 存储[1] = 30, 栈: []
```

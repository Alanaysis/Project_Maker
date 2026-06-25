# 智能合约虚拟机

一个使用 Rust 实现的简易智能合约虚拟机，支持基本的合约执行。该项目用于学习 EVM 原理、字节码执行和 Gas 计算。

## 特性

- **基本操作码支持**: 算术运算、比较、位运算
- **栈和内存管理**: 完整的栈操作和动态内存扩展
- **Gas 计算**: 防止无限循环和资源滥用
- **合约功能**: 状态存储、函数调用、事件触发
- **环境操作码**: ADDRESS、CALLER、CALLVALUE、CALLDATALOAD、CALLDATASIZE、CALLDATACOPY
- **日志操作**: LOG0-LOG4 事件触发
- **汇编器**: 提供高级接口构建字节码
- **代币合约示例**: ERC20 风格的代币合约实现
- **完整的错误处理**: 支持各种异常情况

## 项目结构

```
smart-contract-vm/
├── Cargo.toml
├── README.md
├── LEARNING_NOTES.md
├── docs/
│   ├── 01-RESEARCH.md
│   ├── 01-evm-overview.md
│   ├── 02-bytecode-execution.md
│   ├── 03-stack-memory.md
│   ├── 04-gas-calculation.md
│   ├── 05-DEVELOPMENT.md
│   └── 05-smart-contract-basics.md
├── examples/
│   ├── simple_add.rs
│   ├── fibonacci.rs
│   ├── storage_contract.rs
│   ├── loop_counter.rs
│   ├── conditional.rs
│   └── memory_operations.rs
├── src/
│   ├── lib.rs
│   ├── vm.rs
│   ├── opcodes.rs
│   ├── stack.rs
│   ├── memory.rs
│   ├── storage.rs
│   ├── gas.rs
│   ├── error.rs
│   └── assembler.rs
└── tests/
    └── integration_test.rs
```

## 核心组件

### 1. 虚拟机 (VM)

主执行引擎，负责执行字节码：

```rust
let context = ExecutionContext {
    code: bytecode,
    calldata: Vec::new(),
    caller: 0,
    address: 0,
    value: 0,
};

let mut vm = Vm::new(context, 10000);
let result = vm.execute();
```

### 2. 栈 (Stack)

1024 个元素的后进先出栈：

```rust
let mut stack = Stack::new();
stack.push(42)?;
stack.dup(1)?;
stack.swap(1)?;
```

### 3. 内存 (Memory)

线性字节数组，支持动态扩展：

```rust
let mut memory = Memory::new();
memory.write_u256(0, 42)?;
let value = memory.read_u256(0)?;
```

### 4. 存储 (Storage)

持久化键值存储：

```rust
let mut storage = Storage::new();
storage.store(1, 100);
let value = storage.load(1);
```

### 5. Gas 计量器 (GasMeter)

跟踪和限制执行成本：

```rust
let mut gas = GasMeter::new(1000);
gas.consume(100)?;
gas.consume_opcode(&Opcode::Add)?;
```

### 6. 汇编器 (Assembler)

高级接口构建字节码：

```rust
let code = Assembler::new()
    .push1(10)
    .push1(20)
    .add()
    .stop()
    .build();
```

## 支持的操作码

### 算术操作
- `ADD` (0x01) - 加法
- `MUL` (0x02) - 乘法
- `SUB` (0x03) - 减法
- `DIV` (0x04) - 除法
- `MOD` (0x05) - 取模
- `ADDMOD` (0x06) - 加法取模
- `MULMOD` (0x07) - 乘法取模
- `EXP` (0x08) - 幂运算

### 比较操作
- `LT` (0x10) - 小于
- `GT` (0x11) - 大于
- `EQ` (0x12) - 等于
- `ISZERO` (0x13) - 是否为零

### 位运算
- `AND` (0x16) - 按位与
- `OR` (0x17) - 按位或
- `XOR` (0x18) - 按位异或
- `NOT` (0x19) - 按位取反
- `SHL` (0x1b) - 左移
- `SHR` (0x1c) - 右移

### 环境操作
- `ADDRESS` (0x30) - 获取合约地址
- `CALLER` (0x33) - 获取调用者地址
- `CALLVALUE` (0x34) - 获取转账金额
- `CALLDATALOAD` (0x35) - 读取调用数据
- `CALLDATASIZE` (0x36) - 获取调用数据大小
- `CALLDATACOPY` (0x37) - 复制调用数据到内存

### 栈操作
- `POP` (0x50) - 弹出栈顶
- `DUP1-DUP4` (0x80-0x83) - 复制栈元素
- `SWAP1-SWAP4` (0x90-0x93) - 交换栈元素

### 内存操作
- `MLOAD` (0x51) - 从内存加载
- `MSTORE` (0x52) - 存储到内存
- `MSIZE` (0x59) - 获取内存大小

### 存储操作
- `SLOAD` (0x54) - 从存储加载
- `SSTORE` (0x55) - 存储到存储

### 跳转操作
- `JUMP` (0x56) - 无条件跳转
- `JUMPI` (0x57) - 条件跳转
- `PC` (0x58) - 获取程序计数器
- `JUMPDEST` (0x5b) - 跳转目标标记

### 日志操作
- `LOG0` (0xa0) - 无主题日志
- `LOG1` (0xa1) - 1个主题日志
- `LOG2` (0xa2) - 2个主题日志
- `LOG3` (0xa3) - 3个主题日志
- `LOG4` (0xa4) - 4个主题日志

### Push 操作
- `PUSH1-PUSH32` (0x60-0x7f) - 将数据压入栈

### 系统操作
- `RETURN` (0xf3) - 返回数据
- `REVERT` (0xfd) - 回滚执行

## 使用示例

### 简单加法

```rust
use smart_contract_vm::{Vm, ExecutionContext, Assembler};

// 使用汇编器构建字节码
let code = Assembler::new()
    .push1(10)
    .push1(20)
    .add()
    .stop()
    .build();

// 创建执行上下文
let context = ExecutionContext {
    code,
    calldata: Vec::new(),
    caller: 0,
    address: 0,
    value: 0,
};

// 执行
let mut vm = Vm::new(context, 1000);
let result = vm.execute();

println!("Gas used: {}", vm.gas_used());
```

### 循环示例

```rust
// 计算 1+2+...+10
let code = Assembler::new()
    .push1(0)      // sum = 0
    .push1(10)     // counter = 10

    // 循环开始
    .jumpdest()
    .dup1()
    .iszero()
    .push1(20)     // 结束位置
    .jumpi()

    // sum += counter
    .dup2()
    .dup2()
    .add()
    .swap2()
    .pop()

    // counter--
    .push1(1)
    .swap1()
    .sub()

    // 跳转回循环
    .push1(5)      // 循环开始位置
    .jump()

    // 结束
    .jumpdest()
    .pop()
    .stop()
    .build();
```

## 运行测试

```bash
# 运行所有测试
cargo test

# 运行集成测试
cargo test --test integration_test

# 运行特定测试
cargo test test_simple_add
```

## Gas 成本

| 操作码 | Gas 成本 |
|--------|----------|
| 算术运算 (ADD, SUB, MUL, DIV) | 3 |
| 比较运算 (LT, GT, EQ) | 3 |
| 位运算 (AND, OR, XOR) | 3 |
| 栈操作 (PUSH, POP, DUP, SWAP) | 3 |
| 内存操作 (MLOAD, MSTORE) | 3 |
| 存储读取 (SLOAD) | 200 |
| 存储写入 (SSTORE) | 20000 |
| 跳转 (JUMP) | 8 |
| 条件跳转 (JUMPI) | 10 |

## 文档

- [市场调研](docs/01-RESEARCH.md) - 智能合约虚拟机市场调研和技术对比
- [需求分析](docs/02-REQUIREMENTS.md) - 功能需求和非功能需求
- [系统设计](docs/02-DESIGN.md) - 整体架构和组件设计
- [实现细节](docs/03-IMPLEMENTATION.md) - 模块结构和关键实现
- [EVM 概述](docs/01-evm-overview.md) - EVM 核心概念和架构
- [字节码执行](docs/02-bytecode-execution.md) - 取指-译码-执行循环
- [栈和内存管理](docs/03-stack-memory.md) - 栈、内存和存储模型
- [Gas 计算](docs/04-gas-calculation.md) - Gas 定价和优化策略
- [开发手册](docs/05-DEVELOPMENT.md) - 开发环境配置和贡献指南
- [智能合约基础](docs/05-smart-contract-basics.md) - 智能合约原理和安全
- [学习笔记](LEARNING_NOTES.md) - 开发过程中的学习心得

## 使用示例

项目提供了多个示例，可以通过以下命令运行：

```bash
# 简单加法
cargo run --example simple_add

# 斐波那契数列
cargo run --example fibonacci

# 存储合约
cargo run --example storage_contract

# 循环计数器
cargo run --example loop_counter

# 条件执行
cargo run --example conditional

# 内存操作
cargo run --example memory_operations

# 代币合约 (ERC20)
cargo run --example token_contract
```

示例代码位于 `examples/` 目录，展示了虚拟机的各种功能：

- **simple_add.rs**: 基本算术运算（PUSH、ADD、STOP）
- **fibonacci.rs**: 循环和跳转（JUMP、JUMPI、JUMPDEST）
- **storage_contract.rs**: 持久化存储（SSTORE、SLOAD）
- **loop_counter.rs**: 计数器循环和累加
- **conditional.rs**: 条件分支和比较运算
- **memory_operations.rs**: 内存读写操作（MSTORE、MLOAD）
- **token_contract.rs**: ERC20 代币合约（部署、转账、事件日志）

## 依赖

- `thiserror` - 错误处理

## 未来改进

- [ ] 支持完整 256 位整数
- [ ] 实现完整的系统调用 (CALL, DELEGATECALL, STATICCALL)
- [ ] 支持合约间调用
- [ ] 实现 CREATE 操作码
- [ ] 添加调试功能
- [ ] 性能优化
- [ ] 支持更复杂的合约 ABI

## 许可证

MIT

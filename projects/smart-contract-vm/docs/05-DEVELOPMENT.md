# 智能合约虚拟机开发手册

## 开发环境配置

### 前置要求

- Rust 1.70 或更高版本
- Cargo（随 Rust 一起安装）
- Git

### 安装 Rust

```bash
# 安装 Rust 工具链
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 配置环境变量
source $HOME/.cargo/env

# 验证安装
rustc --version
cargo --version
```

### 克隆和构建

```bash
# 克隆项目
git clone <repository-url>
cd smart-contract-vm

# 构建项目
cargo build

# 运行测试
cargo test

# 构建发布版本
cargo build --release
```

### IDE 配置

推荐使用 VS Code，安装以下扩展：

- rust-analyzer - Rust 语言服务器
- Even Better TOML - TOML 文件支持
- Error Lens - 内联错误显示
- CodeLLDB - 调试器

## 项目结构

```
smart-contract-vm/
├── Cargo.toml              # 项目配置和依赖
├── Cargo.lock              # 依赖版本锁定
├── README.md               # 项目说明
├── LEARNING_NOTES.md       # 学习笔记
├── docs/                   # 文档目录
│   ├── 01-RESEARCH.md      # 市场调研
│   ├── 01-evm-overview.md  # EVM 概述
│   ├── 02-bytecode-execution.md  # 字节码执行
│   ├── 03-stack-memory.md  # 栈和内存
│   ├── 04-gas-calculation.md  # Gas 计算
│   ├── 05-DEVELOPMENT.md   # 开发手册（本文档）
│   └── 05-smart-contract-basics.md  # 智能合约基础
├── examples/               # 使用示例
├── src/                    # 源代码
│   ├── lib.rs              # 库入口
│   ├── vm.rs               # 虚拟机核心
│   ├── opcodes.rs          # 操作码定义
│   ├── stack.rs            # 栈实现
│   ├── memory.rs           # 内存实现
│   ├── storage.rs          # 存储实现
│   ├── gas.rs              # Gas 计量
│   ├── error.rs            # 错误类型
│   └── assembler.rs        # 汇编器
└── tests/                  # 集成测试
    └── integration_test.rs
```

## 核心模块说明

### 1. 虚拟机核心 (`src/vm.rs`)

虚拟机的核心执行引擎，包含：

- `VmConfig`: 虚拟机配置（最大调用深度、代码大小限制）
- `ExecutionContext`: 执行上下文（代码、调用数据、调用者地址等）
- `Vm`: 虚拟机主结构体

关键方法：
```rust
// 创建虚拟机
let mut vm = Vm::new(context, gas_limit);

// 执行字节码
let result = vm.execute();

// 访问执行状态
vm.gas_used();      // 已消耗 Gas
vm.stack_size();    // 栈大小
vm.memory_size();   // 内存大小
vm.pc();            // 程序计数器
```

### 2. 操作码 (`src/opcodes.rs`)

定义所有支持的操作码及其 Gas 成本：

```rust
// 操作码枚举
pub enum Opcode {
    Stop = 0x00,
    Add = 0x01,
    Mul = 0x02,
    // ... 更多操作码
}

// 获取操作码 Gas 成本
let gas_cost = opcode.gas_cost();

// 从字节解码操作码
let opcode = Opcode::from_byte(byte)?;
```

### 3. 栈 (`src/stack.rs`)

1024 个元素的后进先出栈：

```rust
let mut stack = Stack::new();

stack.push(42)?;        // 压入元素
let val = stack.pop()?; // 弹出元素
stack.dup(1)?;          // 复制栈顶元素
stack.swap(1)?;         // 交换栈顶元素
let val = stack.peek()?; // 查看栈顶元素
```

### 4. 内存 (`src/memory.rs`)

线性字节寻址内存，最大 1MB：

```rust
let mut memory = Memory::new();

memory.write_byte(0, 0xFF)?;           // 写入单字节
let byte = memory.read_byte(0)?;       // 读取单字节
memory.write_u256(0, 42)?;             // 写入 256 位值
let val = memory.read_u256(0)?;        // 读取 256 位值
memory.write_range(0, &[1, 2, 3])?;   // 写入字节范围
let data = memory.read_range(0, 3)?;   // 读取字节范围
```

### 5. 存储 (`src/storage.rs`)

持久化键值存储：

```rust
let mut storage = Storage::new();

storage.store(1, 100);          // 存储值
let val = storage.load(1);      // 加载值（不存在返回 0）
storage.store(1, 0);            // 删除（存储 0 等同于删除）
let exists = storage.contains_key(1);  // 检查键是否存在
```

### 6. Gas 计量 (`src/gas.rs`)

跟踪和限制执行成本：

```rust
let mut gas = GasMeter::new(10000);

gas.consume(100)?;                      // 消耗 Gas
gas.consume_opcode(&Opcode::Add)?;      // 按操作码消耗 Gas
gas.consume_memory(old_size, new_size)?; // 按内存扩展消耗 Gas
let remaining = gas.remaining();         // 剩余 Gas
let used = gas.used();                   // 已用 Gas
```

### 7. 汇编器 (`src/assembler.rs`)

Builder 模式的字节码构建器：

```rust
let code = Assembler::new()
    .push1(10)      // PUSH1 0x0a
    .push1(20)      // PUSH1 0x14
    .add()          // ADD
    .stop()         // STOP
    .build();       // 返回 Vec<u8>

// 获取当前位置（用于计算跳转目标）
let pos = assembler.position();
```

### 8. 错误处理 (`src/error.rs`)

三态结果类型：

```rust
// 执行结果
pub enum VmResult {
    Success(Vec<u8>),    // 执行成功，返回数据
    Revert(Vec<u8>),     // 执行回滚，返回数据
    Error(VmError),      // 执行错误
}

// 错误类型
pub enum VmError {
    StackOverflow,
    StackUnderflow,
    OutOfGas,
    OutOfMemory,
    InvalidOpcode(u8),
    InvalidJumpDestination,
    // ... 更多错误类型
}
```

## 开发工作流

### 1. 修改代码

根据需要修改相应模块：
- `src/vm.rs`: 虚拟机执行逻辑
- `src/opcodes.rs`: 添加新操作码
- `src/stack.rs`: 栈操作
- `src/memory.rs`: 内存操作
- `src/storage.rs`: 存储操作
- `src/gas.rs`: Gas 计算
- `src/assembler.rs`: 汇编器方法

### 2. 运行测试

```bash
# 运行所有测试
cargo test

# 运行特定测试
cargo test test_simple_add

# 运行集成测试
cargo test --test integration_test

# 显示测试输出
cargo test -- --nocapture

# 运行测试并显示详细信息
cargo test -- --show-output
```

### 3. 代码检查

```bash
# 格式化代码
cargo fmt

# 检查代码风格
cargo clippy

# 检查编译
cargo check
```

### 4. 构建和运行

```bash
# 调试构建
cargo build

# 发布构建
cargo build --release

# 运行示例
cargo run --example simple_add
```

## 添加新功能

### 添加新操作码

1. 在 `src/opcodes.rs` 中添加操作码枚举：

```rust
pub enum Opcode {
    // ... 现有操作码
    NewOp = 0xXX,  // 新操作码
}
```

2. 在 `from_byte` 方法中添加映射：

```rust
0xXX => Opcode::NewOp,
```

3. 在 `gas_cost` 方法中设置 Gas 成本：

```rust
Opcode::NewOp => 3,
```

4. 在 `src/vm.rs` 中添加执行逻辑：

```rust
fn op_new_op(&mut self) -> VmResult<()> {
    // 从栈中获取操作数
    let a = self.stack.pop()?;
    let b = self.stack.pop()?;

    // 执行操作
    let result = /* 计算 */;

    // 将结果压入栈
    self.stack.push(result)?;
    Ok(())
}
```

5. 在 `step` 方法中添加分发：

```rust
Opcode::NewOp => self.op_new_op()?,
```

6. 在 `src/assembler.rs` 中添加汇编器方法：

```rust
pub fn new_op(&mut self) -> &mut Self {
    self.code.push(Opcode::NewOp as u8);
    self
}
```

7. 添加测试：

```rust
#[test]
fn test_new_op() {
    let code = Assembler::new()
        .push1(10)
        .push1(20)
        .new_op()
        .stop()
        .build();

    let context = ExecutionContext {
        code,
        calldata: Vec::new(),
        caller: 0,
        address: 0,
        value: 0,
    };

    let mut vm = Vm::new(context, 1000);
    let result = vm.execute();

    match result {
        VmResult::Success(data) => {
            // 验证结果
        }
        _ => panic!("Expected success"),
    }
}
```

### 添加新的汇编器方法

在 `src/assembler.rs` 中添加方法：

```rust
/// 新操作的汇编方法
pub fn new_operation(&mut self, param: u8) -> &mut Self {
    self.code.push(Opcode::NewOp as u8);
    self.code.push(param);
    self
}
```

### 扩展 Gas 计算

在 `src/gas.rs` 中添加新的 Gas 计算逻辑：

```rust
/// 计算特定操作的 Gas 成本
pub fn calculate_special_gas(&self, param: u64) -> u64 {
    // 自定义计算逻辑
    param * 3
}
```

## 调试技巧

### 1. 使用日志

在代码中添加日志输出：

```rust
println!("PC: {}, Opcode: {:?}", self.pc, opcode);
println!("Stack: {:?}", self.stack);
println!("Gas used: {}", self.gas.used());
```

### 2. 单步调试

使用 CodeLLDB 调试器：

1. 在 VS Code 中设置断点
2. 按 F5 启动调试
3. 使用调试控制台查看变量

### 3. 测试驱动开发

先编写测试，再实现功能：

```rust
#[test]
fn test_new_feature() {
    // 1. 准备测试数据
    let code = Assembler::new()
        .push1(10)
        .new_feature()
        .stop()
        .build();

    // 2. 执行测试
    let result = execute_bytecode(code, 1000);

    // 3. 验证结果
    assert!(matches!(result, VmResult::Success(_)));
}
```

### 4. 边界条件测试

测试各种边界情况：

```rust
#[test]
fn test_edge_cases() {
    // 测试栈溢出
    let mut stack = Stack::new();
    for i in 0..1024 {
        assert!(stack.push(i).is_ok());
    }
    assert!(stack.push(1024).is_err());  // 应该溢出

    // 测试 Gas 耗尽
    let mut gas = GasMeter::new(100);
    assert!(gas.consume(50).is_ok());
    assert!(gas.consume(60).is_err());  // 应该耗尽

    // 测试内存越界
    let mut memory = Memory::new();
    assert!(memory.read_byte(0).is_ok());
    assert!(memory.read_byte(1024 * 1024 + 1).is_err());  // 超出限制
}
```

## 性能优化

### 1. 避免不必要的内存分配

```rust
// 不好：每次调用都分配新 Vec
fn bad_example(&self) -> Vec<u8> {
    vec![0; 32]
}

// 好：复用缓冲区
fn good_example(&self, buf: &mut Vec<u8>) {
    buf.clear();
    buf.resize(32, 0);
}
```

### 2. 使用高效的栈操作

```rust
// 不好：多次 pop/push
let a = stack.pop()?;
let b = stack.pop()?;
stack.push(b)?;
stack.push(a)?;

// 好：使用 swap
stack.swap(1)?;
```

### 3. 预分配内存

```rust
// 不好：动态增长
let mut vec = Vec::new();

// 好：预分配
let mut vec = Vec::with_capacity(1024);
```

## 常见问题

### Q: 如何添加新的测试？

在 `tests/integration_test.rs` 中添加新的测试函数：

```rust
#[test]
fn test_my_new_feature() {
    let code = Assembler::new()
        .push1(10)
        .push1(20)
        .add()
        .stop()
        .build();

    let context = ExecutionContext {
        code,
        calldata: Vec::new(),
        caller: 0,
        address: 0,
        value: 0,
    };

    let mut vm = Vm::new(context, 1000);
    let result = vm.execute();

    match result {
        VmResult::Success(data) => {
            assert_eq!(data.len(), 32);
            // 更多断言...
        }
        _ => panic!("Expected success"),
    }
}
```

### Q: 如何调试 Gas 消耗？

```bash
# 运行测试并显示输出
cargo test test_gas_tracking -- --nocapture
```

在代码中添加 Gas 追踪：

```rust
println!("Gas used: {}", vm.gas_used());
println!("Gas remaining: {}", vm.gas_remaining());
```

### Q: 如何处理栈溢出错误？

```rust
match stack.push(value) {
    Ok(()) => {
        // 成功
    }
    Err(VmError::StackOverflow) => {
        // 处理栈溢出
        return Err(VmError::StackOverflow);
    }
    Err(e) => {
        // 其他错误
        return Err(e);
    }
}
```

### Q: 如何扩展内存限制？

在 `src/memory.rs` 中修改常量：

```rust
const MAX_MEMORY_SIZE: usize = 1024 * 1024;  // 1 MB
// 修改为更大的值
const MAX_MEMORY_SIZE: usize = 2 * 1024 * 1024;  // 2 MB
```

## 贡献指南

### 代码风格

- 使用 `cargo fmt` 格式化代码
- 使用 `cargo clippy` 检查代码质量
- 遵循 Rust 命名规范：
  - 模块名: snake_case
  - 类型名: CamelCase
  - 函数名: snake_case
  - 常量: SCREAMING_SNAKE_CASE

### 提交规范

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

类型：
- feat: 新功能
- fix: 修复 bug
- docs: 文档更新
- style: 代码格式
- refactor: 重构
- test: 测试
- chore: 构建/工具

示例：
```
feat(vm): 添加 EXP 操作码支持

实现指数运算操作码，支持栈顶两个元素的指数计算。

Closes #123
```

### Pull Request 流程

1. Fork 项目
2. 创建功能分支: `git checkout -b feature/my-feature`
3. 提交更改: `git commit -m "feat: 添加新功能"`
4. 推送分支: `git push origin feature/my-feature`
5. 创建 Pull Request
6. 等待代码审查
7. 合并到主分支

## 资源链接

- [Rust 官方文档](https://doc.rust-lang.org/)
- [Rust Book](https://doc.rust-lang.org/book/)
- [EVM 操作码参考](https://www.evm.codes/)
- [以太坊黄皮书](https://ethereum.github.io/yellowpaper/paper.pdf)

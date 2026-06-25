# 实现细节

## 模块结构

```
src/
├── lib.rs          # 模块导出
├── opcodes.rs      # 操作码定义
├── stack.rs        # 栈实现
├── memory.rs       # 内存实现
├── storage.rs      # 存储实现
├── gas.rs          # Gas 计量
├── error.rs        # 错误类型
├── vm.rs           # 虚拟机主逻辑
└── assembler.rs    # 汇编器
```

## 操作码实现

### 新增环境操作码

```rust
// 环境操作
Address = 0x30,      // 获取合约地址
Caller = 0x33,       // 获取调用者地址
CallValue = 0x34,    // 获取转账金额
CallDataLoad = 0x35, // 读取 calldata
CallDataSize = 0x36, // 获取 calldata 大小
CallDataCopy = 0x37, // 复制 calldata 到内存
```

### 日志操作码实现

```rust
fn op_log(&mut self, num_topics: usize) -> Result<(), VmError> {
    let offset = self.stack.pop()? as usize;
    let size = self.stack.pop()? as usize;

    // 读取日志数据
    let data = if size > 0 {
        self.memory.read_range(offset, size)?
    } else {
        Vec::new()
    };

    // 读取主题
    let mut topics = Vec::with_capacity(num_topics);
    for _ in 0..num_topics {
        topics.push(self.stack.pop()?);
    }

    self.logs.push(LogEntry { topics, data });
    Ok(())
}
```

## 栈实现

使用 Vec 作为底层存储，栈顶在末尾：

```rust
pub struct Stack {
    data: Vec<u64>,
}

impl Stack {
    pub fn push(&mut self, value: u64) -> Result<(), VmError> {
        if self.data.len() >= MAX_STACK_SIZE {
            return Err(VmError::StackOverflow);
        }
        self.data.push(value);
        Ok(())
    }

    pub fn pop(&mut self) -> Result<u64, VmError> {
        self.data.pop().ok_or(VmError::StackUnderflow)
    }
}
```

## 内存实现

线性字节数组，支持动态扩展：

```rust
pub struct Memory {
    data: Vec<u8>,
}

impl Memory {
    pub fn expand(&mut self, min_size: usize) -> Result<(), VmError> {
        if min_size > MAX_MEMORY_SIZE {
            return Err(VmError::OutOfMemory);
        }
        if min_size > self.data.len() {
            self.data.resize(min_size, 0);
        }
        Ok(())
    }
}
```

## 存储实现

使用 HashMap 实现键值存储：

```rust
pub struct Storage {
    data: HashMap<u64, u64>,
}

impl Storage {
    pub fn store(&mut self, key: u64, value: u64) {
        if value == 0 {
            self.data.remove(&key);
        } else {
            self.data.insert(key, value);
        }
    }
}
```

## Gas 计算

每个操作码有固定的 Gas 成本：

| 操作类型 | Gas 成本 |
|---------|---------|
| 算术运算 | 3 |
| 比较运算 | 3 |
| 栈操作 | 2-3 |
| 内存操作 | 3 |
| 存储读取 | 200 |
| 存储写入 | 20000 |
| 跳转 | 8-10 |
| 日志 | 375+ |

## 函数选择器

简化版函数选择器计算：

```rust
pub fn from_name(name: &str) -> u32 {
    let mut hash: u32 = 0;
    for byte in name.bytes() {
        hash = hash.wrapping_mul(31).wrapping_add(byte as u32);
    }
    hash
}
```

## 错误处理

定义统一的错误类型：

```rust
pub enum VmError {
    StackOverflow,
    StackUnderflow,
    OutOfGas,
    OutOfMemory,
    MemoryAccessOutOfBounds,
    InvalidOpcode(u8),
    InvalidJumpDestination,
    Revert,
    Stop,
    InvalidState,
    DivisionByZero,
    CallDepthExceeded,
}
```

/// 智能合约虚拟机
///
/// 实现一个简易的智能合约虚拟机，支持基本的合约执行
/// 参考 EVM 原理设计，用于学习字节码执行和 Gas 计算

pub mod opcodes;
pub mod stack;
pub mod memory;
pub mod storage;
pub mod gas;
pub mod error;
pub mod vm;
pub mod assembler;

pub use error::{VmError, VmResult};
pub use vm::{Vm, ExecutionContext, VmConfig, LogEntry};
pub use opcodes::Opcode;
pub use assembler::{Assembler, FunctionSelector};

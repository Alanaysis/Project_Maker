use thiserror::Error;

/// 虚拟机错误类型
#[derive(Error, Debug, Clone, PartialEq, Eq)]
pub enum VmError {
    #[error("Stack overflow")]
    StackOverflow,

    #[error("Stack underflow")]
    StackUnderflow,

    #[error("Out of gas")]
    OutOfGas,

    #[error("Out of memory")]
    OutOfMemory,

    #[error("Memory access out of bounds")]
    MemoryAccessOutOfBounds,

    #[error("Invalid opcode: {0:#x}")]
    InvalidOpcode(u8),

    #[error("Invalid jump destination")]
    InvalidJumpDestination,

    #[error("Execution reverted")]
    Revert,

    #[error("Stop execution")]
    Stop,

    #[error("Invalid state")]
    InvalidState,

    #[error("Division by zero")]
    DivisionByZero,

    #[error("Call depth exceeded")]
    CallDepthExceeded,
}

/// 虚拟机执行结果
#[derive(Debug, Clone)]
pub enum VmResult {
    /// 成功执行，返回输出数据
    Success(Vec<u8>),
    /// 执行被 revert
    Revert(Vec<u8>),
    /// 执行失败
    Error(VmError),
}

/// 操作码定义
/// 定义虚拟机支持的所有指令
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum Opcode {
    // 停止和算术操作
    Stop = 0x00,
    Add = 0x01,
    Mul = 0x02,
    Sub = 0x03,
    Div = 0x04,
    Mod = 0x05,
    AddMod = 0x06,
    MulMod = 0x07,
    Exp = 0x08,

    // 比较和位运算
    Lt = 0x10,
    Gt = 0x11,
    Eq = 0x12,
    IsZero = 0x13,
    And = 0x16,
    Or = 0x17,
    Xor = 0x18,
    Not = 0x19,
    Byte = 0x1a,
    Shl = 0x1b,
    Shr = 0x1c,

    // 栈操作
    Pop = 0x50,
    Mload = 0x51,
    Mstore = 0x52,
    Sload = 0x54,
    Sstore = 0x55,
    Jump = 0x56,
    JumpI = 0x57,
    Pc = 0x58,
    Msize = 0x59,
    JumpDest = 0x5b,

    // Push 操作 (PUSH1-PUSH32)
    Push1 = 0x60,
    Push2 = 0x61,
    Push4 = 0x63,
    Push8 = 0x67,
    Push16 = 0x6f,
    Push32 = 0x7f,

    // Dup 操作 (DUP1-DUP16)
    Dup1 = 0x80,
    Dup2 = 0x81,
    Dup3 = 0x82,
    Dup4 = 0x83,

    // Swap 操作 (SWAP1-SWAP16)
    Swap1 = 0x90,
    Swap2 = 0x91,
    Swap3 = 0x92,
    Swap4 = 0x93,

    // 日志操作
    Log0 = 0xa0,
    Log1 = 0xa1,
    Log2 = 0xa2,
    Log3 = 0xa3,
    Log4 = 0xa4,

    // 系统操作
    Create = 0xf0,
    Call = 0xf1,
    Return = 0xf3,
    DelegateCall = 0xf4,
    StaticCall = 0xfa,
    Revert = 0xfd,
    Invalid = 0xfe,
    SelfDestruct = 0xff,
}

impl Opcode {
    /// 从字节转换为操作码
    pub fn from_byte(byte: u8) -> Option<Opcode> {
        match byte {
            0x00 => Some(Opcode::Stop),
            0x01 => Some(Opcode::Add),
            0x02 => Some(Opcode::Mul),
            0x03 => Some(Opcode::Sub),
            0x04 => Some(Opcode::Div),
            0x05 => Some(Opcode::Mod),
            0x06 => Some(Opcode::AddMod),
            0x07 => Some(Opcode::MulMod),
            0x08 => Some(Opcode::Exp),
            0x10 => Some(Opcode::Lt),
            0x11 => Some(Opcode::Gt),
            0x12 => Some(Opcode::Eq),
            0x13 => Some(Opcode::IsZero),
            0x16 => Some(Opcode::And),
            0x17 => Some(Opcode::Or),
            0x18 => Some(Opcode::Xor),
            0x19 => Some(Opcode::Not),
            0x1a => Some(Opcode::Byte),
            0x1b => Some(Opcode::Shl),
            0x1c => Some(Opcode::Shr),
            0x50 => Some(Opcode::Pop),
            0x51 => Some(Opcode::Mload),
            0x52 => Some(Opcode::Mstore),
            0x54 => Some(Opcode::Sload),
            0x55 => Some(Opcode::Sstore),
            0x56 => Some(Opcode::Jump),
            0x57 => Some(Opcode::JumpI),
            0x58 => Some(Opcode::Pc),
            0x59 => Some(Opcode::Msize),
            0x5b => Some(Opcode::JumpDest),
            0x60 => Some(Opcode::Push1),
            0x61 => Some(Opcode::Push2),
            0x63 => Some(Opcode::Push4),
            0x67 => Some(Opcode::Push8),
            0x6f => Some(Opcode::Push16),
            0x7f => Some(Opcode::Push32),
            0x80 => Some(Opcode::Dup1),
            0x81 => Some(Opcode::Dup2),
            0x82 => Some(Opcode::Dup3),
            0x83 => Some(Opcode::Dup4),
            0x90 => Some(Opcode::Swap1),
            0x91 => Some(Opcode::Swap2),
            0x92 => Some(Opcode::Swap3),
            0x93 => Some(Opcode::Swap4),
            0xa0 => Some(Opcode::Log0),
            0xa1 => Some(Opcode::Log1),
            0xa2 => Some(Opcode::Log2),
            0xa3 => Some(Opcode::Log3),
            0xa4 => Some(Opcode::Log4),
            0xf0 => Some(Opcode::Create),
            0xf1 => Some(Opcode::Call),
            0xf3 => Some(Opcode::Return),
            0xf4 => Some(Opcode::DelegateCall),
            0xfa => Some(Opcode::StaticCall),
            0xfd => Some(Opcode::Revert),
            0xfe => Some(Opcode::Invalid),
            0xff => Some(Opcode::SelfDestruct),
            _ => None,
        }
    }

    /// 获取操作码的 Gas 成本
    pub fn gas_cost(&self) -> u64 {
        match self {
            // 基本算术操作 - 3 gas
            Opcode::Add | Opcode::Sub | Opcode::Mul | Opcode::Div |
            Opcode::Mod | Opcode::AddMod | Opcode::MulMod | Opcode::Exp |
            Opcode::Lt | Opcode::Gt | Opcode::Eq | Opcode::IsZero |
            Opcode::And | Opcode::Or | Opcode::Xor | Opcode::Not |
            Opcode::Byte | Opcode::Shl | Opcode::Shr => 3,

            // 栈操作 - 2 gas
            Opcode::Pop => 2,
            Opcode::Dup1 | Opcode::Dup2 | Opcode::Dup3 | Opcode::Dup4 => 3,
            Opcode::Swap1 | Opcode::Swap2 | Opcode::Swap3 | Opcode::Swap4 => 3,

            // 内存操作 - 3 gas
            Opcode::Mload | Opcode::Mstore => 3,
            Opcode::Msize => 2,

            // 存储操作 - 更高 gas
            Opcode::Sload => 200,
            Opcode::Sstore => 20000,

            // Push 操作 - 3 gas
            Opcode::Push1 | Opcode::Push2 | Opcode::Push4 |
            Opcode::Push8 | Opcode::Push16 | Opcode::Push32 => 3,

            // 跳转操作
            Opcode::Jump => 8,
            Opcode::JumpI => 10,
            Opcode::JumpDest => 1,
            Opcode::Pc => 2,

            // 日志操作
            Opcode::Log0 => 375,
            Opcode::Log1 => 750,
            Opcode::Log2 => 1125,
            Opcode::Log3 => 1500,
            Opcode::Log4 => 1875,

            // 系统操作
            Opcode::Create => 32000,
            Opcode::Call => 700,
            Opcode::Return => 0,
            Opcode::DelegateCall => 700,
            Opcode::StaticCall => 700,
            Opcode::Revert => 0,
            Opcode::Invalid => 0,
            Opcode::SelfDestruct => 5000,
            Opcode::Stop => 0,
        }
    }

    /// 获取操作码需要的额外操作数字节数
    pub fn extra_bytes(&self) -> usize {
        match self {
            Opcode::Push1 => 1,
            Opcode::Push2 => 2,
            Opcode::Push4 => 4,
            Opcode::Push8 => 8,
            Opcode::Push16 => 16,
            Opcode::Push32 => 32,
            _ => 0,
        }
    }
}

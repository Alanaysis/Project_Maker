use crate::opcodes::Opcode;

/// 字节码汇编器
/// 提供高级接口来构建字节码
pub struct Assembler {
    code: Vec<u8>,
}

impl Assembler {
    /// 创建新的汇编器
    pub fn new() -> Self {
        Assembler { code: Vec::new() }
    }

    /// 添加停止指令
    pub fn stop(mut self) -> Self {
        self.code.push(Opcode::Stop as u8);
        self
    }

    /// 添加加法指令
    pub fn add(mut self) -> Self {
        self.code.push(Opcode::Add as u8);
        self
    }

    /// 添加减法指令
    pub fn sub(mut self) -> Self {
        self.code.push(Opcode::Sub as u8);
        self
    }

    /// 添加乘法指令
    pub fn mul(mut self) -> Self {
        self.code.push(Opcode::Mul as u8);
        self
    }

    /// 添加除法指令
    pub fn div(mut self) -> Self {
        self.code.push(Opcode::Div as u8);
        self
    }

    /// 添加取模指令
    pub fn modulo(mut self) -> Self {
        self.code.push(Opcode::Mod as u8);
        self
    }

    /// 添加比较指令
    pub fn lt(mut self) -> Self {
        self.code.push(Opcode::Lt as u8);
        self
    }

    pub fn gt(mut self) -> Self {
        self.code.push(Opcode::Gt as u8);
        self
    }

    pub fn eq(mut self) -> Self {
        self.code.push(Opcode::Eq as u8);
        self
    }

    pub fn iszero(mut self) -> Self {
        self.code.push(Opcode::IsZero as u8);
        self
    }

    /// 添加位运算指令
    pub fn and(mut self) -> Self {
        self.code.push(Opcode::And as u8);
        self
    }

    pub fn or(mut self) -> Self {
        self.code.push(Opcode::Or as u8);
        self
    }

    pub fn xor(mut self) -> Self {
        self.code.push(Opcode::Xor as u8);
        self
    }

    pub fn not(mut self) -> Self {
        self.code.push(Opcode::Not as u8);
        self
    }

    /// 添加环境操作指令
    pub fn address(mut self) -> Self {
        self.code.push(Opcode::Address as u8);
        self
    }

    pub fn caller(mut self) -> Self {
        self.code.push(Opcode::Caller as u8);
        self
    }

    pub fn callvalue(mut self) -> Self {
        self.code.push(Opcode::CallValue as u8);
        self
    }

    pub fn calldataload(mut self) -> Self {
        self.code.push(Opcode::CallDataLoad as u8);
        self
    }

    pub fn calldatasize(mut self) -> Self {
        self.code.push(Opcode::CallDataSize as u8);
        self
    }

    pub fn calldatacopy(mut self) -> Self {
        self.code.push(Opcode::CallDataCopy as u8);
        self
    }

    /// 添加栈操作指令
    pub fn pop(mut self) -> Self {
        self.code.push(Opcode::Pop as u8);
        self
    }

    pub fn dup1(mut self) -> Self {
        self.code.push(Opcode::Dup1 as u8);
        self
    }

    pub fn dup2(mut self) -> Self {
        self.code.push(Opcode::Dup2 as u8);
        self
    }

    pub fn dup3(mut self) -> Self {
        self.code.push(Opcode::Dup3 as u8);
        self
    }

    pub fn dup4(mut self) -> Self {
        self.code.push(Opcode::Dup4 as u8);
        self
    }

    pub fn swap1(mut self) -> Self {
        self.code.push(Opcode::Swap1 as u8);
        self
    }

    pub fn swap2(mut self) -> Self {
        self.code.push(Opcode::Swap2 as u8);
        self
    }

    pub fn swap3(mut self) -> Self {
        self.code.push(Opcode::Swap3 as u8);
        self
    }

    pub fn swap4(mut self) -> Self {
        self.code.push(Opcode::Swap4 as u8);
        self
    }

    /// 添加内存操作指令
    pub fn mload(mut self) -> Self {
        self.code.push(Opcode::Mload as u8);
        self
    }

    pub fn mstore(mut self) -> Self {
        self.code.push(Opcode::Mstore as u8);
        self
    }

    /// 添加存储操作指令
    pub fn sload(mut self) -> Self {
        self.code.push(Opcode::Sload as u8);
        self
    }

    pub fn sstore(mut self) -> Self {
        self.code.push(Opcode::Sstore as u8);
        self
    }

    /// 添加跳转指令
    pub fn jump(mut self) -> Self {
        self.code.push(Opcode::Jump as u8);
        self
    }

    pub fn jumpi(mut self) -> Self {
        self.code.push(Opcode::JumpI as u8);
        self
    }

    pub fn jumpdest(mut self) -> Self {
        self.code.push(Opcode::JumpDest as u8);
        self
    }

    pub fn pc(mut self) -> Self {
        self.code.push(Opcode::Pc as u8);
        self
    }

    /// 添加日志指令
    pub fn log0(mut self) -> Self {
        self.code.push(Opcode::Log0 as u8);
        self
    }

    pub fn log1(mut self) -> Self {
        self.code.push(Opcode::Log1 as u8);
        self
    }

    pub fn log2(mut self) -> Self {
        self.code.push(Opcode::Log2 as u8);
        self
    }

    pub fn log3(mut self) -> Self {
        self.code.push(Opcode::Log3 as u8);
        self
    }

    pub fn log4(mut self) -> Self {
        self.code.push(Opcode::Log4 as u8);
        self
    }

    /// 添加 PUSH 指令
    pub fn push1(mut self, value: u8) -> Self {
        self.code.push(Opcode::Push1 as u8);
        self.code.push(value);
        self
    }

    pub fn push2(mut self, value: u16) -> Self {
        self.code.push(Opcode::Push2 as u8);
        self.code.push((value >> 8) as u8);
        self.code.push(value as u8);
        self
    }

    pub fn push4(mut self, value: u32) -> Self {
        self.code.push(Opcode::Push4 as u8);
        for i in (0..4).rev() {
            self.code.push((value >> (i * 8)) as u8);
        }
        self
    }

    pub fn push8(mut self, value: u64) -> Self {
        self.code.push(Opcode::Push8 as u8);
        for i in (0..8).rev() {
            self.code.push((value >> (i * 8)) as u8);
        }
        self
    }

    /// 添加 RETURN 指令
    pub fn return_op(mut self) -> Self {
        self.code.push(Opcode::Return as u8);
        self
    }

    /// 添加 REVERT 指令
    pub fn revert(mut self) -> Self {
        self.code.push(Opcode::Revert as u8);
        self
    }

    /// 获取当前位置（用于跳转）
    pub fn position(&self) -> usize {
        self.code.len()
    }

    /// 获取生成的字节码
    pub fn build(self) -> Vec<u8> {
        self.code
    }
}

impl Default for Assembler {
    fn default() -> Self {
        Self::new()
    }
}

/// 函数选择器工具
/// 计算 Solidity 风格的函数选择器（简化版：使用 u32）
pub struct FunctionSelector;

impl FunctionSelector {
    /// 简化的函数选择器计算
    /// 实际 EVM 使用 keccak256(sig)[0:4]
    /// 这里使用简单的哈希作为演示
    pub fn from_name(name: &str) -> u32 {
        let mut hash: u32 = 0;
        for byte in name.bytes() {
            hash = hash.wrapping_mul(31).wrapping_add(byte as u32);
        }
        hash
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_assembler_basic() {
        let code = Assembler::new()
            .push1(10)
            .push1(20)
            .add()
            .stop()
            .build();

        assert_eq!(code.len(), 6);
        assert_eq!(code[0], Opcode::Push1 as u8);
        assert_eq!(code[1], 10);
        assert_eq!(code[2], Opcode::Push1 as u8);
        assert_eq!(code[3], 20);
        assert_eq!(code[4], Opcode::Add as u8);
        assert_eq!(code[5], Opcode::Stop as u8);
    }

    #[test]
    fn test_assembler_position() {
        let mut asm = Assembler::new();
        assert_eq!(asm.position(), 0);

        asm = asm.push1(1);
        assert_eq!(asm.position(), 2);

        asm = asm.push1(2);
        assert_eq!(asm.position(), 4);
    }

    #[test]
    fn test_assembler_push2() {
        let code = Assembler::new()
            .push2(0x1234)
            .stop()
            .build();

        assert_eq!(code[0], Opcode::Push2 as u8);
        assert_eq!(code[1], 0x12);
        assert_eq!(code[2], 0x34);
    }

    #[test]
    fn test_function_selector() {
        let selector = FunctionSelector::from_name("transfer(address,uint256)");
        assert_ne!(selector, 0);
        // 同样的名字应该产生同样的选择器
        assert_eq!(selector, FunctionSelector::from_name("transfer(address,uint256)"));
    }
}

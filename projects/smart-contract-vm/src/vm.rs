use crate::error::{VmError, VmResult};
use crate::gas::GasMeter;
use crate::memory::Memory;
use crate::opcodes::Opcode;
use crate::stack::Stack;
use crate::storage::Storage;

/// 虚拟机配置
#[derive(Debug, Clone)]
pub struct VmConfig {
    /// 最大调用深度
    pub max_call_depth: usize,
    /// 最大代码大小
    pub max_code_size: usize,
}

impl Default for VmConfig {
    fn default() -> Self {
        VmConfig {
            max_call_depth: 1024,
            max_code_size: 24576,
        }
    }
}

/// 虚拟机执行上下文
pub struct ExecutionContext {
    /// 合约代码
    pub code: Vec<u8>,
    /// 调用数据
    pub calldata: Vec<u8>,
    /// 调用者地址（简化为 u64）
    pub caller: u64,
    /// 合约地址（简化为 u64）
    pub address: u64,
    /// 转账金额
    pub value: u64,
}

/// 虚拟机主结构
pub struct Vm {
    /// 栈
    stack: Stack,
    /// 内存
    memory: Memory,
    /// 存储
    storage: Storage,
    /// Gas 计量器
    gas: GasMeter,
    /// 程序计数器
    pc: usize,
    /// 执行上下文
    context: ExecutionContext,
    /// 是否停止
    stopped: bool,
    /// 输出数据
    output: Vec<u8>,
}

impl Vm {
    /// 创建新的虚拟机实例
    pub fn new(context: ExecutionContext, gas_limit: u64) -> Self {
        Vm {
            stack: Stack::new(),
            memory: Memory::new(),
            storage: Storage::new(),
            gas: GasMeter::new(gas_limit),
            pc: 0,
            context,
            stopped: false,
            output: Vec::new(),
        }
    }

    /// 执行字节码
    pub fn execute(&mut self) -> VmResult {
        loop {
            if self.stopped {
                return VmResult::Success(self.output.clone());
            }

            if self.pc >= self.context.code.len() {
                return VmResult::Success(self.output.clone());
            }

            match self.step() {
                Ok(advance) => {
                    if advance {
                        self.pc += 1;
                    }
                }
                Err(VmError::Stop) => {
                    return VmResult::Success(self.output.clone());
                }
                Err(VmError::Revert) => {
                    return VmResult::Revert(self.output.clone());
                }
                Err(e) => {
                    return VmResult::Error(e);
                }
            }
        }
    }

    /// 执行单步，返回 Ok(true) 表示需要推进 PC，Ok(false) 表示 PC 已由指令设置
    fn step(&mut self) -> Result<bool, VmError> {
        if self.pc >= self.context.code.len() {
            return Err(VmError::Stop);
        }

        let byte = self.context.code[self.pc];
        let opcode = Opcode::from_byte(byte)
            .ok_or(VmError::InvalidOpcode(byte))?;

        // 消耗 gas
        self.gas.consume_opcode(&opcode)?;

        // 执行操作码，返回是否需要推进 PC
        let advance_pc = match opcode {
            Opcode::Stop => {
                self.stopped = true;
                return Err(VmError::Stop);
            }

            // 算术操作
            Opcode::Add => { self.op_add()?; true }
            Opcode::Mul => { self.op_mul()?; true }
            Opcode::Sub => { self.op_sub()?; true }
            Opcode::Div => { self.op_div()?; true }
            Opcode::Mod => { self.op_mod()?; true }
            Opcode::AddMod => { self.op_addmod()?; true }
            Opcode::MulMod => { self.op_mulmod()?; true }
            Opcode::Exp => { self.op_exp()?; true }

            // 比较操作
            Opcode::Lt => { self.op_lt()?; true }
            Opcode::Gt => { self.op_gt()?; true }
            Opcode::Eq => { self.op_eq()?; true }
            Opcode::IsZero => { self.op_iszero()?; true }

            // 位运算
            Opcode::And => { self.op_and()?; true }
            Opcode::Or => { self.op_or()?; true }
            Opcode::Xor => { self.op_xor()?; true }
            Opcode::Not => { self.op_not()?; true }
            Opcode::Shl => { self.op_shl()?; true }
            Opcode::Shr => { self.op_shr()?; true }

            // 栈操作
            Opcode::Pop => { self.stack.pop()?; true }
            Opcode::Dup1 => { self.stack.dup(1)?; true }
            Opcode::Dup2 => { self.stack.dup(2)?; true }
            Opcode::Dup3 => { self.stack.dup(3)?; true }
            Opcode::Dup4 => { self.stack.dup(4)?; true }
            Opcode::Swap1 => { self.stack.swap(1)?; true }
            Opcode::Swap2 => { self.stack.swap(2)?; true }
            Opcode::Swap3 => { self.stack.swap(3)?; true }
            Opcode::Swap4 => { self.stack.swap(4)?; true }

            // 内存操作
            Opcode::Mload => { self.op_mload()?; true }
            Opcode::Mstore => { self.op_mstore()?; true }
            Opcode::Msize => { self.op_msize()?; true }

            // 存储操作
            Opcode::Sload => { self.op_sload()?; true }
            Opcode::Sstore => { self.op_sstore()?; true }

            // 跳转操作 - JUMP 设置 PC，不需要推进
            Opcode::Jump => { self.op_jump()?; false }
            // JUMPI: 如果跳转则返回 false，否则返回 true
            Opcode::JumpI => { self.op_jumpi()? }
            Opcode::Pc => { self.op_pc()?; true }
            Opcode::JumpDest => { true }

            // Push 操作 - PC 已在 op_push 中推进了额外字节数
            Opcode::Push1 => { self.op_push(1)?; true }
            Opcode::Push2 => { self.op_push(2)?; true }
            Opcode::Push4 => { self.op_push(4)?; true }
            Opcode::Push8 => { self.op_push(8)?; true }
            Opcode::Push16 => { self.op_push(16)?; true }
            Opcode::Push32 => { self.op_push(32)?; true }

            // Return
            Opcode::Return => { self.op_return()?; true }
            Opcode::Revert => { self.op_revert()?; true }

            _ => return Err(VmError::InvalidOpcode(byte)),
        };

        Ok(advance_pc)
    }

    // ===== 算术操作 =====

    fn op_add(&mut self) -> Result<(), VmError> {
        let a = self.stack.pop()?;
        let b = self.stack.pop()?;
        self.stack.push(a.wrapping_add(b))?;
        Ok(())
    }

    fn op_mul(&mut self) -> Result<(), VmError> {
        let a = self.stack.pop()?;
        let b = self.stack.pop()?;
        self.stack.push(a.wrapping_mul(b))?;
        Ok(())
    }

    fn op_sub(&mut self) -> Result<(), VmError> {
        let a = self.stack.pop()?;
        let b = self.stack.pop()?;
        self.stack.push(a.wrapping_sub(b))?;
        Ok(())
    }

    fn op_div(&mut self) -> Result<(), VmError> {
        let a = self.stack.pop()?;
        let b = self.stack.pop()?;
        if b == 0 {
            self.stack.push(0)?;
        } else {
            self.stack.push(a / b)?;
        }
        Ok(())
    }

    fn op_mod(&mut self) -> Result<(), VmError> {
        let a = self.stack.pop()?;
        let b = self.stack.pop()?;
        if b == 0 {
            self.stack.push(0)?;
        } else {
            self.stack.push(a % b)?;
        }
        Ok(())
    }

    fn op_addmod(&mut self) -> Result<(), VmError> {
        let a = self.stack.pop()?;
        let b = self.stack.pop()?;
        let n = self.stack.pop()?;
        if n == 0 {
            self.stack.push(0)?;
        } else {
            self.stack.push((a.wrapping_add(b)) % n)?;
        }
        Ok(())
    }

    fn op_mulmod(&mut self) -> Result<(), VmError> {
        let a = self.stack.pop()?;
        let b = self.stack.pop()?;
        let n = self.stack.pop()?;
        if n == 0 {
            self.stack.push(0)?;
        } else {
            self.stack.push((a.wrapping_mul(b)) % n)?;
        }
        Ok(())
    }

    fn op_exp(&mut self) -> Result<(), VmError> {
        let base = self.stack.pop()?;
        let exponent = self.stack.pop()?;
        self.stack.push(base.wrapping_pow(exponent as u32))?;
        Ok(())
    }

    // ===== 比较操作 =====

    fn op_lt(&mut self) -> Result<(), VmError> {
        let a = self.stack.pop()?;
        let b = self.stack.pop()?;
        self.stack.push(if a < b { 1 } else { 0 })?;
        Ok(())
    }

    fn op_gt(&mut self) -> Result<(), VmError> {
        let a = self.stack.pop()?;
        let b = self.stack.pop()?;
        self.stack.push(if a > b { 1 } else { 0 })?;
        Ok(())
    }

    fn op_eq(&mut self) -> Result<(), VmError> {
        let a = self.stack.pop()?;
        let b = self.stack.pop()?;
        self.stack.push(if a == b { 1 } else { 0 })?;
        Ok(())
    }

    fn op_iszero(&mut self) -> Result<(), VmError> {
        let a = self.stack.pop()?;
        self.stack.push(if a == 0 { 1 } else { 0 })?;
        Ok(())
    }

    // ===== 位运算 =====

    fn op_and(&mut self) -> Result<(), VmError> {
        let a = self.stack.pop()?;
        let b = self.stack.pop()?;
        self.stack.push(a & b)?;
        Ok(())
    }

    fn op_or(&mut self) -> Result<(), VmError> {
        let a = self.stack.pop()?;
        let b = self.stack.pop()?;
        self.stack.push(a | b)?;
        Ok(())
    }

    fn op_xor(&mut self) -> Result<(), VmError> {
        let a = self.stack.pop()?;
        let b = self.stack.pop()?;
        self.stack.push(a ^ b)?;
        Ok(())
    }

    fn op_not(&mut self) -> Result<(), VmError> {
        let a = self.stack.pop()?;
        self.stack.push(!a)?;
        Ok(())
    }

    fn op_shl(&mut self) -> Result<(), VmError> {
        let shift = self.stack.pop()?;
        let value = self.stack.pop()?;
        self.stack.push(value.wrapping_shl(shift as u32))?;
        Ok(())
    }

    fn op_shr(&mut self) -> Result<(), VmError> {
        let shift = self.stack.pop()?;
        let value = self.stack.pop()?;
        self.stack.push(value.wrapping_shr(shift as u32))?;
        Ok(())
    }

    // ===== 内存操作 =====

    fn op_mload(&mut self) -> Result<(), VmError> {
        let offset = self.stack.pop()?;
        let value = self.memory.read_u256(offset as usize)?;
        self.stack.push(value)?;
        Ok(())
    }

    fn op_mstore(&mut self) -> Result<(), VmError> {
        let offset = self.stack.pop()?;
        let value = self.stack.pop()?;
        self.memory.write_u256(offset as usize, value)?;
        Ok(())
    }

    fn op_msize(&mut self) -> Result<(), VmError> {
        self.stack.push(self.memory.size() as u64)?;
        Ok(())
    }

    // ===== 存储操作 =====

    fn op_sload(&mut self) -> Result<(), VmError> {
        let key = self.stack.pop()?;
        let value = self.storage.load(key);
        self.stack.push(value)?;
        Ok(())
    }

    fn op_sstore(&mut self) -> Result<(), VmError> {
        let key = self.stack.pop()?;
        let value = self.stack.pop()?;
        self.storage.store(key, value);
        Ok(())
    }

    // ===== 跳转操作 =====

    fn op_jump(&mut self) -> Result<(), VmError> {
        let dest = self.stack.pop()? as usize;
        if dest >= self.context.code.len() {
            return Err(VmError::InvalidJumpDestination);
        }
        if self.context.code[dest] != Opcode::JumpDest as u8 {
            return Err(VmError::InvalidJumpDestination);
        }
        self.pc = dest;
        Ok(())
    }

    fn op_jumpi(&mut self) -> Result<bool, VmError> {
        let dest = self.stack.pop()? as usize;
        let condition = self.stack.pop()?;
        if condition != 0 {
            if dest >= self.context.code.len() {
                return Err(VmError::InvalidJumpDestination);
            }
            if self.context.code[dest] != Opcode::JumpDest as u8 {
                return Err(VmError::InvalidJumpDestination);
            }
            self.pc = dest;
            Ok(false) // PC 已设置，不需要推进
        } else {
            Ok(true) // 未跳转，正常推进 PC
        }
    }

    fn op_pc(&mut self) -> Result<(), VmError> {
        self.stack.push(self.pc as u64)?;
        Ok(())
    }

    // ===== Push 操作 =====

    fn op_push(&mut self, size: usize) -> Result<(), VmError> {
        let mut value: u64 = 0;
        for i in 0..size {
            let pos = self.pc + 1 + i;
            if pos >= self.context.code.len() {
                return Err(VmError::InvalidState);
            }
            value = (value << 8) | self.context.code[pos] as u64;
        }
        self.stack.push(value)?;
        self.pc += size;
        Ok(())
    }

    // ===== 返回操作 =====

    fn op_return(&mut self) -> Result<(), VmError> {
        let offset = self.stack.pop()? as usize;
        let size = self.stack.pop()? as usize;
        self.output = self.memory.read_range(offset, size)?;
        self.stopped = true;
        Ok(())
    }

    fn op_revert(&mut self) -> Result<(), VmError> {
        let offset = self.stack.pop()? as usize;
        let size = self.stack.pop()? as usize;
        self.output = self.memory.read_range(offset, size)?;
        self.stopped = true;
        Err(VmError::Revert)
    }

    /// 获取当前栈大小
    pub fn stack_size(&self) -> usize {
        self.stack.size()
    }

    /// 获取当前内存大小
    pub fn memory_size(&self) -> usize {
        self.memory.size()
    }

    /// 获取已使用的 gas
    pub fn gas_used(&self) -> u64 {
        self.gas.used()
    }

    /// 获取剩余 gas
    pub fn gas_remaining(&self) -> u64 {
        self.gas.remaining()
    }

    /// 获取程序计数器
    pub fn pc(&self) -> usize {
        self.pc
    }

    /// 获取存储引用
    pub fn storage(&self) -> &Storage {
        &self.storage
    }

    /// 获取输出数据
    pub fn output(&self) -> &[u8] {
        &self.output
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_vm(code: Vec<u8>, gas_limit: u64) -> Vm {
        let context = ExecutionContext {
            code,
            calldata: Vec::new(),
            caller: 0,
            address: 0,
            value: 0,
        };
        Vm::new(context, gas_limit)
    }

    #[test]
    fn test_simple_add() {
        // PUSH1 3 PUSH1 2 ADD STOP
        let code = vec![
            Opcode::Push1 as u8, 0x03,
            Opcode::Push1 as u8, 0x02,
            Opcode::Add as u8,
            Opcode::Stop as u8,
        ];
        let mut vm = create_vm(code, 1000);
        let result = vm.execute();
        assert!(matches!(result, VmResult::Success(_)));
        assert_eq!(vm.stack_size(), 1);
    }

    #[test]
    fn test_arithmetic() {
        // Test: 10 - 3 = 7
        let code = vec![
            Opcode::Push1 as u8, 10,
            Opcode::Push1 as u8, 3,
            Opcode::Sub as u8,
            Opcode::Stop as u8,
        ];
        let mut vm = create_vm(code, 1000);
        vm.execute();
        assert_eq!(vm.stack_size(), 1);
    }

    #[test]
    fn test_out_of_gas() {
        let code = vec![
            Opcode::Push1 as u8, 1,
            Opcode::Push1 as u8, 2,
            Opcode::Add as u8,
            Opcode::Stop as u8,
        ];
        // 只给 5 gas，不够执行完
        let mut vm = create_vm(code, 5);
        let result = vm.execute();
        assert!(matches!(result, VmResult::Error(VmError::OutOfGas)));
    }

    #[test]
    fn test_jump() {
        // Byte layout:
        //   0: PUSH1 (0x60)
        //   1: 0x05  (jump target = position 5)
        //   2: JUMP (0x56)
        //   3: PUSH1 (0x60)  -- should be skipped
        //   4: 99
        //   5: JUMPDEST (0x5b)
        //   6: PUSH1 (0x60)
        //   7: 42
        //   8: STOP (0x00)
        let code = vec![
            Opcode::Push1 as u8, 0x05,
            Opcode::Jump as u8,
            Opcode::Push1 as u8, 99,  // skipped
            Opcode::JumpDest as u8,    // position 5
            Opcode::Push1 as u8, 42,
            Opcode::Stop as u8,
        ];
        let mut vm = create_vm(code, 1000);
        vm.execute();
        assert_eq!(vm.stack_size(), 1);
    }

    #[test]
    fn test_conditional_jump() {
        // Byte layout (each PUSH1 = 2 bytes):
        //   0: PUSH1 (0x60)
        //   1: 0x01 (condition = true)
        //   2: PUSH1 (0x60)
        //   3: 0x0c (jump target = position 12)
        //   4: JUMPI (0x57)
        //   5: PUSH1 (0x60) -- should be skipped
        //   6: 99
        //   7: STOP (0x00)
        //   8: PUSH1 (0x60) -- padding
        //   9: 0
        //  10: PUSH1 (0x60) -- padding
        //  11: 0
        //  12: JUMPDEST (0x5b)
        //  13: PUSH1 (0x60)
        //  14: 42
        //  15: STOP (0x00)
        let code = vec![
            Opcode::Push1 as u8, 0x01,  // condition = 1 (true)
            Opcode::Push1 as u8, 0x0c,  // jump target = position 12
            Opcode::JumpI as u8,
            Opcode::Push1 as u8, 99,    // should be skipped
            Opcode::Stop as u8,
            // padding to reach position 12
            Opcode::Push1 as u8, 0,
            Opcode::Push1 as u8, 0,
            Opcode::JumpDest as u8,     // position 12
            Opcode::Push1 as u8, 42,
            Opcode::Stop as u8,
        ];

        // Debug: verify bytecode layout
        assert_eq!(code[0], Opcode::Push1 as u8);
        assert_eq!(code[1], 0x01);
        assert_eq!(code[2], Opcode::Push1 as u8);
        assert_eq!(code[3], 0x0c);
        assert_eq!(code[4], Opcode::JumpI as u8);
        assert_eq!(code[12], Opcode::JumpDest as u8);

        let mut vm = create_vm(code, 1000);
        let result = vm.execute();
        assert!(matches!(result, VmResult::Success(_)), "Expected success but got {:?}", result);
        assert_eq!(vm.stack_size(), 1, "Stack should have 1 element (42), but has {}", vm.stack_size());
    }

    #[test]
    fn test_memory_operations() {
        // PUSH1 42 PUSH1 0 MSTORE PUSH1 0 MLOAD
        let code = vec![
            Opcode::Push1 as u8, 42,
            Opcode::Push1 as u8, 0,
            Opcode::Mstore as u8,
            Opcode::Push1 as u8, 0,
            Opcode::Mload as u8,
            Opcode::Stop as u8,
        ];
        let mut vm = create_vm(code, 1000);
        vm.execute();
        assert_eq!(vm.stack_size(), 1);
    }

    #[test]
    fn test_storage_operations() {
        // PUSH1 100 PUSH1 1 SSTORE PUSH1 1 SLOAD
        let code = vec![
            Opcode::Push1 as u8, 100,
            Opcode::Push1 as u8, 1,
            Opcode::Sstore as u8,
            Opcode::Push1 as u8, 1,
            Opcode::Sload as u8,
            Opcode::Stop as u8,
        ];
        let mut vm = create_vm(code, 50000);
        vm.execute();
        assert_eq!(vm.stack_size(), 1);
    }

    #[test]
    fn test_dup_operations() {
        // PUSH1 5 DUP1 ADD (5 + 5 = 10)
        let code = vec![
            Opcode::Push1 as u8, 5,
            Opcode::Dup1 as u8,
            Opcode::Add as u8,
            Opcode::Stop as u8,
        ];
        let mut vm = create_vm(code, 1000);
        vm.execute();
        assert_eq!(vm.stack_size(), 1);
    }

    #[test]
    fn test_swap_operations() {
        // PUSH1 1 PUSH1 2 SWAP1 SUB (1 - 2 = -1)
        let code = vec![
            Opcode::Push1 as u8, 1,
            Opcode::Push1 as u8, 2,
            Opcode::Swap1 as u8,
            Opcode::Sub as u8,
            Opcode::Stop as u8,
        ];
        let mut vm = create_vm(code, 1000);
        vm.execute();
        assert_eq!(vm.stack_size(), 1);
    }
}

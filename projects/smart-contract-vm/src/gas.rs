use crate::error::VmError;
use crate::opcodes::Opcode;

/// Gas 计量器
/// 跟踪和限制计算资源消耗
pub struct GasMeter {
    /// 已消耗的 gas
    used: u64,
    /// gas 上限
    limit: u64,
}

impl GasMeter {
    /// 创建新的 gas 计量器
    pub fn new(limit: u64) -> Self {
        GasMeter { used: 0, limit }
    }

    /// 获取已使用的 gas
    pub fn used(&self) -> u64 {
        self.used
    }

    /// 获取剩余 gas
    pub fn remaining(&self) -> u64 {
        self.limit.saturating_sub(self.used)
    }

    /// 获取 gas 上限
    pub fn limit(&self) -> u64 {
        self.limit
    }

    /// 消耗指定数量的 gas
    pub fn consume(&mut self, amount: u64) -> Result<(), VmError> {
        if self.used + amount > self.limit {
            return Err(VmError::OutOfGas);
        }
        self.used += amount;
        Ok(())
    }

    /// 根据操作码消耗 gas
    pub fn consume_opcode(&mut self, opcode: &Opcode) -> Result<(), VmError> {
        self.consume(opcode.gas_cost())
    }

    /// 计算内存扩展的 gas 成本
    pub fn memory_gas_cost(&self, current_size: usize, new_size: usize) -> u64 {
        if new_size <= current_size {
            return 0;
        }

        // 简化的内存成本计算
        // 实际 EVM 使用更复杂的公式
        let words = (new_size + 31) / 32;
        let cost = words as u64 * 3;
        cost
    }

    /// 消耗内存扩展的 gas
    pub fn consume_memory(&mut self, current_size: usize, new_size: usize) -> Result<(), VmError> {
        let cost = self.memory_gas_cost(current_size, new_size);
        self.consume(cost)
    }

    /// 重置 gas 计量器
    pub fn reset(&mut self, limit: u64) {
        self.used = 0;
        self.limit = limit;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_gas_basic() {
        let mut gas = GasMeter::new(1000);
        assert_eq!(gas.used(), 0);
        assert_eq!(gas.remaining(), 1000);

        gas.consume(100).unwrap();
        assert_eq!(gas.used(), 100);
        assert_eq!(gas.remaining(), 900);
    }

    #[test]
    fn test_gas_out_of_gas() {
        let mut gas = GasMeter::new(100);
        gas.consume(50).unwrap();
        assert!(gas.consume(60).is_err());
    }

    #[test]
    fn test_gas_opcode() {
        let mut gas = GasMeter::new(1000);
        gas.consume_opcode(&Opcode::Add).unwrap();
        assert_eq!(gas.used(), 3);
    }

    #[test]
    fn test_gas_memory() {
        let mut gas = GasMeter::new(1000);
        gas.consume_memory(0, 32).unwrap();
        assert_eq!(gas.used(), 3); // 1 word = 32 bytes = 3 gas
    }

    #[test]
    fn test_gas_reset() {
        let mut gas = GasMeter::new(100);
        gas.consume(50).unwrap();
        gas.reset(200);
        assert_eq!(gas.used(), 0);
        assert_eq!(gas.limit(), 200);
    }
}

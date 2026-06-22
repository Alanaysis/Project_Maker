use crate::error::VmError;

/// 最大内存大小（字节）
pub const MAX_MEMORY_SIZE: usize = 1024 * 1024; // 1MB

/// 内存实现
/// 线性内存，按字节寻址
pub struct Memory {
    data: Vec<u8>,
}

impl Memory {
    /// 创建新的空内存
    pub fn new() -> Self {
        Memory {
            data: Vec::with_capacity(4096),
        }
    }

    /// 获取内存大小（字节）
    pub fn size(&self) -> usize {
        self.data.len()
    }

    /// 确保内存至少有指定大小
    pub fn expand(&mut self, min_size: usize) -> Result<(), VmError> {
        if min_size > MAX_MEMORY_SIZE {
            return Err(VmError::OutOfMemory);
        }
        if min_size > self.data.len() {
            self.data.resize(min_size, 0);
        }
        Ok(())
    }

    /// 读取指定位置的字节
    pub fn read_byte(&self, offset: usize) -> Result<u8, VmError> {
        if offset >= self.data.len() {
            return Err(VmError::MemoryAccessOutOfBounds);
        }
        Ok(self.data[offset])
    }

    /// 写入单个字节
    pub fn write_byte(&mut self, offset: usize, value: u8) -> Result<(), VmError> {
        self.expand(offset + 1)?;
        self.data[offset] = value;
        Ok(())
    }

    /// 读取 32 字节（256 位）的值
    pub fn read_u256(&self, offset: usize) -> Result<u64, VmError> {
        if offset + 32 > self.data.len() {
            return Err(VmError::MemoryAccessOutOfBounds);
        }
        // 简化实现：只读取最后 8 字节（实际 EVM 使用完整 256 位）
        let mut bytes = [0u8; 8];
        bytes.copy_from_slice(&self.data[offset + 24..offset + 32]);
        Ok(u64::from_be_bytes(bytes))
    }

    /// 写入 32 字节（256 位）的值
    pub fn write_u256(&mut self, offset: usize, value: u64) -> Result<(), VmError> {
        self.expand(offset + 32)?;
        // 简化实现：只写入最后 8 字节，前面填充 0
        for i in 0..24 {
            self.data[offset + i] = 0;
        }
        let bytes = value.to_be_bytes();
        self.data[offset + 24..offset + 32].copy_from_slice(&bytes);
        Ok(())
    }

    /// 读取指定范围的数据
    pub fn read_range(&self, offset: usize, size: usize) -> Result<Vec<u8>, VmError> {
        if offset + size > self.data.len() {
            return Err(VmError::MemoryAccessOutOfBounds);
        }
        Ok(self.data[offset..offset + size].to_vec())
    }

    /// 写入数据到指定位置
    pub fn write_range(&mut self, offset: usize, data: &[u8]) -> Result<(), VmError> {
        self.expand(offset + data.len())?;
        self.data[offset..offset + data.len()].copy_from_slice(data);
        Ok(())
    }

    /// 清空内存
    pub fn clear(&mut self) {
        self.data.clear();
    }
}

impl Default for Memory {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_memory_basic() {
        let mut memory = Memory::new();
        assert_eq!(memory.size(), 0);

        memory.write_byte(0, 0x42).unwrap();
        assert_eq!(memory.read_byte(0).unwrap(), 0x42);
        assert_eq!(memory.size(), 1);
    }

    #[test]
    fn test_memory_expand() {
        let mut memory = Memory::new();
        memory.expand(100).unwrap();
        assert_eq!(memory.size(), 100);
        assert_eq!(memory.read_byte(50).unwrap(), 0);
    }

    #[test]
    fn test_memory_read_write_u256() {
        let mut memory = Memory::new();
        memory.write_u256(0, 42).unwrap();
        assert_eq!(memory.read_u256(0).unwrap(), 42);
    }

    #[test]
    fn test_memory_out_of_bounds() {
        let memory = Memory::new();
        assert!(memory.read_byte(0).is_err());
    }

    #[test]
    fn test_memory_range_operations() {
        let mut memory = Memory::new();
        let data = vec![1, 2, 3, 4, 5];
        memory.write_range(10, &data).unwrap();
        let read_data = memory.read_range(10, 5).unwrap();
        assert_eq!(read_data, data);
    }
}

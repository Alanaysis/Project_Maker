use crate::error::VmError;

/// 最大栈深度
pub const MAX_STACK_SIZE: usize = 1024;

/// 栈实现
/// 使用 Vec 作为底层存储，栈顶在末尾
pub struct Stack {
    data: Vec<u64>,
}

impl Stack {
    /// 创建新的空栈
    pub fn new() -> Self {
        Stack {
            data: Vec::with_capacity(256),
        }
    }

    /// 获取栈大小
    pub fn size(&self) -> usize {
        self.data.len()
    }

    /// 检查栈是否为空
    pub fn is_empty(&self) -> bool {
        self.data.is_empty()
    }

    /// 压入值到栈顶
    pub fn push(&mut self, value: u64) -> Result<(), VmError> {
        if self.data.len() >= MAX_STACK_SIZE {
            return Err(VmError::StackOverflow);
        }
        self.data.push(value);
        Ok(())
    }

    /// 弹出栈顶值
    pub fn pop(&mut self) -> Result<u64, VmError> {
        self.data.pop().ok_or(VmError::StackUnderflow)
    }

    /// 查看栈顶值但不弹出
    pub fn peek(&self) -> Result<u64, VmError> {
        self.data.last().copied().ok_or(VmError::StackUnderflow)
    }

    /// 获取栈中指定位置的值（从栈顶开始计数，0 为栈顶）
    pub fn get(&self, index: usize) -> Result<u64, VmError> {
        if index >= self.data.len() {
            return Err(VmError::StackUnderflow);
        }
        let pos = self.data.len() - 1 - index;
        Ok(self.data[pos])
    }

    /// 交换栈顶和指定位置的值
    pub fn swap(&mut self, index: usize) -> Result<(), VmError> {
        if self.data.len() <= index {
            return Err(VmError::StackUnderflow);
        }
        let len = self.data.len();
        self.data.swap(len - 1, len - 1 - index);
        Ok(())
    }

    /// 复制栈顶值并压入
    pub fn dup(&mut self, depth: usize) -> Result<(), VmError> {
        if depth == 0 || depth > self.data.len() {
            return Err(VmError::StackUnderflow);
        }
        let value = self.get(depth - 1)?;
        self.push(value)?;
        Ok(())
    }

    /// 清空栈
    pub fn clear(&mut self) {
        self.data.clear();
    }
}

impl Default for Stack {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_stack_basic_operations() {
        let mut stack = Stack::new();
        assert!(stack.is_empty());

        stack.push(10).unwrap();
        stack.push(20).unwrap();
        stack.push(30).unwrap();

        assert_eq!(stack.size(), 3);
        assert_eq!(stack.peek().unwrap(), 30);
        assert_eq!(stack.pop().unwrap(), 30);
        assert_eq!(stack.pop().unwrap(), 20);
        assert_eq!(stack.pop().unwrap(), 10);
        assert!(stack.is_empty());
    }

    #[test]
    fn test_stack_underflow() {
        let mut stack = Stack::new();
        assert!(stack.pop().is_err());
        assert!(stack.peek().is_err());
    }

    #[test]
    fn test_stack_overflow() {
        let mut stack = Stack::new();
        for i in 0..MAX_STACK_SIZE {
            stack.push(i as u64).unwrap();
        }
        assert!(stack.push(0).is_err());
    }

    #[test]
    fn test_stack_dup() {
        let mut stack = Stack::new();
        stack.push(10).unwrap();
        stack.push(20).unwrap();
        stack.dup(2).unwrap();

        assert_eq!(stack.pop().unwrap(), 10);
        assert_eq!(stack.pop().unwrap(), 20);
        assert_eq!(stack.pop().unwrap(), 10);
    }

    #[test]
    fn test_stack_swap() {
        let mut stack = Stack::new();
        stack.push(10).unwrap();
        stack.push(20).unwrap();
        stack.push(30).unwrap();

        stack.swap(2).unwrap();
        assert_eq!(stack.pop().unwrap(), 10);
        assert_eq!(stack.pop().unwrap(), 20);
        assert_eq!(stack.pop().unwrap(), 30);
    }
}

use std::collections::HashMap;

/// 存储实现
/// 使用 HashMap 模拟键值存储
pub struct Storage {
    data: HashMap<u64, u64>,
}

impl Storage {
    /// 创建新的空存储
    pub fn new() -> Self {
        Storage {
            data: HashMap::new(),
        }
    }

    /// 读取存储中的值
    pub fn load(&self, key: u64) -> u64 {
        self.data.get(&key).copied().unwrap_or(0)
    }

    /// 写入值到存储
    pub fn store(&mut self, key: u64, value: u64) {
        if value == 0 {
            self.data.remove(&key);
        } else {
            self.data.insert(key, value);
        }
    }

    /// 获取存储中的条目数
    pub fn len(&self) -> usize {
        self.data.len()
    }

    /// 检查存储是否为空
    pub fn is_empty(&self) -> bool {
        self.data.is_empty()
    }

    /// 清空存储
    pub fn clear(&mut self) {
        self.data.clear();
    }

    /// 检查键是否存在
    pub fn contains_key(&self, key: u64) -> bool {
        self.data.contains_key(&key)
    }
}

impl Default for Storage {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_storage_basic() {
        let mut storage = Storage::new();
        assert!(storage.is_empty());

        storage.store(1, 100);
        assert_eq!(storage.load(1), 100);
        assert_eq!(storage.len(), 1);
    }

    #[test]
    fn test_storage_default_value() {
        let storage = Storage::new();
        assert_eq!(storage.load(999), 0);
    }

    #[test]
    fn test_storage_overwrite() {
        let mut storage = Storage::new();
        storage.store(1, 100);
        storage.store(1, 200);
        assert_eq!(storage.load(1), 200);
    }

    #[test]
    fn test_storage_delete_on_zero() {
        let mut storage = Storage::new();
        storage.store(1, 100);
        assert!(storage.contains_key(1));

        storage.store(1, 0);
        assert!(!storage.contains_key(1));
        assert_eq!(storage.len(), 0);
    }
}

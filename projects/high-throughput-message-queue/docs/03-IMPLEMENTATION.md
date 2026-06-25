# 实现细节

## 1. 消息序列化

使用紧凑二进制格式，每个字段使用固定长度编码。

### 关键代码
```rust
pub fn serialize(&self) -> Vec<u8> {
    let mut buf = Vec::with_capacity(self.size());
    buf.extend_from_slice(&self.id.to_le_bytes());
    buf.extend_from_slice(&(topic_bytes.len() as u32).to_le_bytes());
    buf.extend_from_slice(topic_bytes);
    // ...
    buf
}
```

## 2. 分段存储

每 64MB 自动轮转新文件，避免单文件过大。

## 3. 崩溃恢复

启动时回放日志文件恢复所有消息到内存。

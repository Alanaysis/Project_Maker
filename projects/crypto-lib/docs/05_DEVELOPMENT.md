# 密码学库开发文档

## 1. 开发环境

### 1.1 环境要求
- Python 3.7+
- 操作系统：Windows/Linux/macOS
- 无外部依赖（纯Python实现）

### 1.2 开发工具
- 编辑器：VS Code / PyCharm
- 版本控制：Git
- 测试框架：unittest

### 1.3 项目设置

```bash
# 克隆项目
git clone <repository-url>
cd crypto-lib

# 创建虚拟环境（可选）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# 运行测试
python -m pytest tests/
```

## 2. 代码规范

### 2.1 命名规范
- 类名：PascalCase（如`SHA256`、`AES`）
- 函数名：snake_case（如`encrypt_block`）
- 常量：UPPER_CASE（如`SBOX`）
- 私有成员：前缀下划线（如`_process_block`）

### 2.2 文档规范
- 每个模块必须有模块文档字符串
- 每个类必须有类文档字符串
- 公共方法必须有方法文档字符串
- 使用中文文档字符串

### 2.3 类型注解
```python
def encrypt(self, plaintext: bytes, mode: str = 'cbc',
            iv: bytes = None) -> Tuple[bytes, bytes]:
    """加密方法"""
    pass
```

## 3. 模块开发指南

### 3.1 添加新的哈希算法

1. 在`src/hash/`目录创建新文件
2. 实现哈希类：
```python
class NewHash:
    def __init__(self):
        self._reset()

    def _reset(self):
        """重置状态"""
        pass

    def update(self, data: Union[str, bytes]) -> 'NewHash':
        """更新哈希"""
        pass

    def digest(self) -> bytes:
        """返回二进制哈希"""
        pass

    def hexdigest(self) -> str:
        """返回十六进制哈希"""
        pass

    @staticmethod
    def hash(data: Union[str, bytes]) -> str:
        """一次性计算"""
        pass
```

3. 更新`src/hash/__init__.py`
4. 添加测试`tests/test_hash.py`
5. 添加示例`examples/hash_example.py`

### 3.2 添加新的对称加密算法

1. 在`src/symmetric/`目录创建新文件
2. 实现加密类：
```python
class NewCipher:
    def __init__(self, key: bytes):
        """初始化"""
        pass

    def encrypt_block(self, plaintext: bytes) -> bytes:
        """加密单块"""
        pass

    def decrypt_block(self, ciphertext: bytes) -> bytes:
        """解密单块"""
        pass

    def encrypt(self, plaintext: bytes, mode: str = 'cbc',
                iv: bytes = None) -> Tuple[bytes, bytes]:
        """加密"""
        pass

    def decrypt(self, ciphertext: bytes, mode: str = 'cbc',
                iv: bytes = None) -> bytes:
        """解密"""
        pass
```

3. 更新`src/symmetric/__init__.py`
4. 添加测试和示例

### 3.3 添加新的非对称加密算法

1. 在`src/asymmetric/`目录创建新文件
2. 实现算法类
3. 更新`src/asymmetric/__init__.py`
4. 添加测试和示例

## 4. 测试指南

### 4.1 测试结构
```
tests/
├── test_hash.py          # 哈希算法测试
├── test_symmetric.py     # 对称加密测试
├── test_asymmetric.py    # 非对称加密测试
└── test_encoding.py      # 编码测试
```

### 4.2 编写测试

```python
import unittest
from src.hash import SHA256

class TestSHA256(unittest.TestCase):
    def test_known_values(self):
        """测试已知的哈希值"""
        self.assertEqual(
            SHA256.hash("abc"),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        )

    def test_empty_string(self):
        """测试空字符串"""
        result = SHA256.hash("")
        self.assertEqual(len(result), 64)

    def test_consistency(self):
        """测试一致性"""
        data = "test"
        self.assertEqual(SHA256.hash(data), SHA256.hash(data))

if __name__ == '__main__':
    unittest.main()
```

### 4.3 运行测试

```bash
# 运行所有测试
python -m unittest discover tests/

# 运行特定测试
python -m unittest tests.test_hash

# 运行特定测试方法
python -m unittest tests.test_hash.TestSHA256.test_known_values
```

## 5. 性能优化

### 5.1 优化策略
- 使用内置函数（如`int.from_bytes`）
- 减少内存分配
- 使用位运算代替乘除
- 缓存计算结果

### 5.2 性能测试

```python
import time

def benchmark():
    data = b"x" * 1000000  # 1MB

    start = time.time()
    for _ in range(10):
        SHA256.hash(data)
    elapsed = time.time() - start

    print(f"SHA-256: {10 / elapsed:.2f} MB/s")

benchmark()
```

## 6. 调试技巧

### 6.1 中间值输出
```python
def encrypt_block(self, plaintext: bytes) -> bytes:
    state = list(plaintext)
    print(f"Initial state: {state}")  # 调试输出

    state = self._sub_bytes(state)
    print(f"After SubBytes: {state}")  # 调试输出

    # ...
```

### 6.2 使用标准库验证
```python
import hashlib

# 验证我们的实现
our_hash = SHA256.hash("test")
std_hash = hashlib.sha256(b"test").hexdigest()
assert our_hash == std_hash
```

## 7. 发布流程

### 7.1 版本号
- 主版本号：重大变更
- 次版本号：新功能
- 修订号：bug修复

### 7.2 发布检查清单
- [ ] 所有测试通过
- [ ] 文档更新
- [ ] 版本号更新
- [ ] CHANGELOG更新

## 8. 常见问题

### 8.1 为什么我的实现与标准库结果不同？
- 检查字节序（大端/小端）
- 检查填充方式
- 检查输入编码

### 8.2 如何调试加密算法？
- 使用已知的测试向量
- 输出中间值
- 与标准库对比

### 8.3 性能太差怎么办？
- 使用C扩展
- 使用NumPy
- 使用并行处理

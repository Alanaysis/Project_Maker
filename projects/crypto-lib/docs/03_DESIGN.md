# 密码学库设计文档

## 1. 架构设计

### 1.1 模块结构

```
crypto-lib/
├── src/
│   ├── __init__.py          # 包入口
│   ├── hash/                # 哈希算法模块
│   │   ├── __init__.py
│   │   ├── md5.py          # MD5实现
│   │   ├── sha1.py         # SHA-1实现
│   │   ├── sha256.py       # SHA-256实现
│   │   └── hmac_alg.py     # HMAC实现
│   ├── symmetric/           # 对称加密模块
│   │   ├── __init__.py
│   │   ├── aes.py          # AES实现
│   │   ├── des.py          # DES实现
│   │   └── modes.py        # 分组模式
│   ├── asymmetric/          # 非对称加密模块
│   │   ├── __init__.py
│   │   ├── rsa.py          # RSA实现
│   │   ├── ecdh.py         # ECDH实现
│   │   └── signature.py    # 数字签名
│   ├── encoding/            # 编码模块
│   │   ├── __init__.py
│   │   ├── base64_codec.py # Base64实现
│   │   └── hex_codec.py    # Hex实现
│   └── utils/               # 实用工具
│       ├── __init__.py
│       ├── password.py      # 密码存储
│       ├── data_encrypt.py  # 数据加密
│       └── digital_signature_util.py
├── examples/                # 使用示例
├── tests/                   # 测试代码
└── docs/                    # 文档
```

### 1.2 依赖关系

```
utils
  ├── symmetric (AES, DES)
  ├── asymmetric (RSA, ECDH)
  ├── hash (SHA256)
  └── encoding (Base64, Hex)

asymmetric
  └── hash (SHA256, for signatures)

symmetric
  └── modes (ECB, CBC, CTR)
```

## 2. 类设计

### 2.1 哈希算法类

```python
class SHA256:
    def __init__(self):
        """初始化哈希器"""
        pass

    def update(self, data: Union[str, bytes]) -> 'SHA256':
        """更新哈希计算"""
        pass

    def digest(self) -> bytes:
        """返回二进制哈希值"""
        pass

    def hexdigest(self) -> str:
        """返回十六进制哈希值"""
        pass

    @staticmethod
    def hash(data: Union[str, bytes]) -> str:
        """一次性计算哈希值"""
        pass
```

### 2.2 对称加密类

```python
class AES:
    def __init__(self, key: bytes):
        """初始化AES加密器"""
        pass

    def encrypt_block(self, plaintext: bytes) -> bytes:
        """加密单个块"""
        pass

    def decrypt_block(self, ciphertext: bytes) -> bytes:
        """解密单个块"""
        pass

    def encrypt(self, plaintext: bytes, mode: str = 'cbc',
                iv: bytes = None, nonce: bytes = None) -> Tuple[bytes, bytes]:
        """AES加密"""
        pass

    def decrypt(self, ciphertext: bytes, mode: str = 'cbc',
                iv: bytes = None, nonce: bytes = None) -> bytes:
        """AES解密"""
        pass
```

### 2.3 非对称加密类

```python
class RSA:
    def __init__(self, key_size: int = 2048):
        """初始化RSA"""
        pass

    def generate_keys(self) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """生成密钥对"""
        pass

    def encrypt(self, plaintext: bytes, public_key=None) -> bytes:
        """RSA加密"""
        pass

    def decrypt(self, ciphertext: bytes, private_key=None) -> bytes:
        """RSA解密"""
        pass

    def sign(self, message: bytes, private_key=None) -> bytes:
        """RSA签名"""
        pass

    def verify(self, message: bytes, signature: bytes,
               public_key=None) -> bool:
        """验证签名"""
        pass
```

### 2.4 工具类

```python
class PasswordManager:
    def __init__(self, algorithm='sha256', iterations=100000):
        pass

    def hash_password(self, password: str, salt: bytes = None) -> Tuple[bytes, bytes]:
        pass

    def verify_password(self, password: str, hash_value: bytes, salt: bytes) -> bool:
        pass

    def store_password(self, password: str) -> dict:
        pass

    def check_password(self, password: str, stored: dict) -> bool:
        pass
```

## 3. 算法设计

### 3.1 MD5算法流程

```
输入: 消息M
输出: 128位哈希值

1. 填充消息到512位倍数
2. 初始化缓冲区 (A, B, C, D)
3. 对每个512位块:
   a. 分解为16个32位字
   b. 执行4轮运算，每轮16步
   c. 更新缓冲区
4. 输出 (A || B || C || D)
```

### 3.2 AES加密流程

```
输入: 明文P, 密钥K
输出: 密文C

1. 密钥扩展
2. 初始轮: AddRoundKey
3. 主轮 (N-1次):
   - SubBytes
   - ShiftRows
   - MixColumns
   - AddRoundKey
4. 最终轮:
   - SubBytes
   - ShiftRows
   - AddRoundKey
```

### 3.3 RSA密钥生成

```
1. 选择大素数 p, q
2. 计算 n = p × q
3. 计算 φ(n) = (p-1)(q-1)
4. 选择 e，满足 gcd(e, φ(n)) = 1
5. 计算 d = e^(-1) mod φ(n)

公钥: (e, n)
私钥: (d, n)
```

### 3.4 ECDH密钥交换

```
1. 选择椭圆曲线和基点G
2. Alice: 私钥a, 公钥A = aG
3. Bob: 私钥b, 公钥B = bG
4. 共享密钥: S = aB = bA = abG
```

## 4. 安全设计

### 4.1 随机数生成
- 使用`os.urandom()`生成密码学安全的随机数
- 用于密钥、IV、盐值生成

### 4.2 时序攻击防护
- 使用`hmac.compare_digest()`进行常量时间比较
- 避免泄露比较时间信息

### 4.3 内存安全
- 敏感数据使用后尽快释放
- 避免在日志中输出密钥

### 4.4 输入验证
- 验证密钥长度
- 验证数据长度
- 验证参数范围

## 5. 错误处理

### 5.1 异常类型
```python
class CryptoError(Exception):
    """密码学错误基类"""
    pass

class InvalidKeyError(CryptoError):
    """无效密钥错误"""
    pass

class InvalidDataError(CryptoError):
    """无效数据错误"""
    pass
```

### 5.2 错误处理策略
- 输入验证失败: 抛出ValueError
- 加密/解密失败: 抛出CryptoError
- 不支持的算法: 抛出ValueError

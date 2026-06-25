# 密码学库 (Crypto Library)

一个用Python实现的密码学学习库，支持哈希算法、对称加密、非对称加密和编码工具。

## 功能特性

### 哈希算法
- **MD5**：128位散列值（已不安全，仅用于学习）
- **SHA-1**：160位散列值（已不安全，仅用于学习）
- **SHA-256**：256位散列值（目前安全）
- **HMAC**：基于哈希的消息认证码

### 对称加密
- **AES**：支持128/192/256位密钥
- **DES**：64位密钥（已不安全，仅用于学习）
- **分组模式**：ECB、CBC、CTR

### 非对称加密
- **RSA**：支持512-4096位密钥
- **ECDH**：椭圆曲线密钥交换
- **数字签名**：RSA签名、ECDSA签名

### 编码工具
- **Base64**：标准和URL安全编码
- **Hex**：十六进制编码

### 实用工具
- **密码存储**：PBKDF2密钥派生
- **数据加密**：简单加密接口
- **数字签名**：文件和消息签名

## 快速开始

### 基本使用

```python
from src.hash import SHA256, HMAC
from src.symmetric import AES
from src.asymmetric import RSA
import os

# SHA-256哈希
hash_value = SHA256.hash("Hello, World!")
print(f"SHA-256: {hash_value}")

# HMAC消息认证
key = "my_secret_key"
mac = HMAC.compute(key, "Hello", 'sha256')
is_valid = HMAC.verify(key, "Hello", mac, 'sha256')

# AES加密
key = os.urandom(32)
aes = AES(key)
ciphertext, iv = aes.encrypt(b"Secret message", 'cbc')
decrypted = aes.decrypt(ciphertext, 'cbc', iv)

# RSA加密
rsa = RSA(2048)
public_key, private_key = rsa.generate_keys()
ciphertext = rsa.encrypt(b"Hello")
decrypted = rsa.decrypt(ciphertext)
```

### 密码存储

```python
from src.utils import PasswordManager

pm = PasswordManager()

# 存储密码
stored = pm.store_password("user_password")

# 验证密码
is_valid = pm.check_password("user_password", stored)
```

### 数字签名

```python
from src.utils import SignatureUtil

sig = SignatureUtil('ecdsa')

# 签名消息
signature_info = sig.sign_message(b"Important document")

# 验证签名
is_valid = sig.verify_message(b"Important document", signature_info)
```

## 运行示例

```bash
# 哈希算法示例
python examples/hash_example.py

# 加密示例
python examples/encryption_example.py

# 非对称加密示例
python examples/asymmetric_example.py

# 实际应用示例
python examples/practical_example.py
```

## 运行测试

```bash
# 运行所有测试
python -m unittest discover tests/

# 运行特定模块测试
python -m unittest tests.test_hash
python -m unittest tests.test_symmetric
python -m unittest tests.test_asymmetric
python -m unittest tests.test_encoding
```

## 项目结构

```
crypto-lib/
├── src/
│   ├── __init__.py
│   ├── hash/                    # 哈希算法
│   │   ├── __init__.py
│   │   ├── md5.py              # MD5实现
│   │   ├── sha1.py             # SHA-1实现
│   │   ├── sha256.py           # SHA-256实现
│   │   └── hmac_alg.py         # HMAC实现
│   ├── symmetric/               # 对称加密
│   │   ├── __init__.py
│   │   ├── aes.py              # AES实现
│   │   ├── des.py              # DES实现
│   │   └── modes.py            # 分组模式
│   ├── asymmetric/              # 非对称加密
│   │   ├── __init__.py
│   │   ├── rsa.py              # RSA实现
│   │   ├── ecdh.py             # ECDH实现
│   │   └── signature.py        # 数字签名
│   ├── encoding/                # 编码工具
│   │   ├── __init__.py
│   │   ├── base64_codec.py     # Base64实现
│   │   └── hex_codec.py        # Hex实现
│   └── utils/                   # 实用工具
│       ├── __init__.py
│       ├── password.py          # 密码存储
│       ├── data_encrypt.py      # 数据加密
│       └── digital_signature_util.py
├── examples/                    # 使用示例
│   ├── hash_example.py
│   ├── encryption_example.py
│   ├── asymmetric_example.py
│   └── practical_example.py
├── tests/                       # 测试代码
│   ├── test_hash.py
│   ├── test_symmetric.py
│   ├── test_asymmetric.py
│   └── test_encoding.py
├── docs/                        # 文档
│   ├── 01_RESEARCH.md
│   ├── 02_REQUIREMENTS.md
│   ├── 03_DESIGN.md
│   ├── 04_PRODUCT.md
│   └── 05_DEVELOPMENT.md
├── README.md
├── requirements.txt
└── setup.py
```

## 算法说明

### AES加密流程

```
明文 → PKCS7填充 → 分块 → CBC模式加密 → 密文

每块加密过程：
1. 与前一块密文异或（CBC模式）
2. SubBytes字节替换
3. ShiftRows行移位
4. MixColumns列混合
5. AddRoundKey轮密钥加
```

### RSA加密流程

```
密钥生成：
1. 选择大素数p, q
2. 计算n = p × q
3. 计算φ(n) = (p-1)(q-1)
4. 选择e，计算d = e⁻¹ mod φ(n)

加密：c = mᵉ mod n
解密：m = cᵈ mod n
```

### ECDH密钥交换流程

```
Alice: 生成私钥a，计算公钥A = aG
Bob: 生成私钥b，计算公钥B = bG

共享密钥：S = aB = bA = abG
```

## 安全说明

**警告：此库仅用于学习目的，不建议用于生产环境。**

生产环境建议使用：
- [cryptography](https://cryptography.io/) - Python密码学库
- [PyCryptodome](https://pycryptodome.readthedocs.io/) - Python密码学库
- [OpenSSL](https://www.openssl.org/) - 通用密码学库

## 学习资源

- [Crypto101](https://www.crypto101.io/) - 密码学入门
- [Cryptopals](https://cryptopals.com/) - 密码学挑战
- [NIST密码标准](https://csrc.nist.gov/projects/cryptographic-standards-and-guidelines)

## 许可证

MIT License

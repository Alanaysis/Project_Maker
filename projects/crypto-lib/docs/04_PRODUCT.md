# 密码学库产品文档

## 1. 产品概述

密码学库是一个用Python实现的密码学学习库，旨在帮助开发者理解密码学算法的原理和实现。

### 1.1 产品定位
- **目标用户**：密码学学习者、安全开发者
- **使用场景**：学习、教学、原型开发
- **核心价值**：清晰的实现、完整的文档、易于理解

### 1.2 主要功能
1. 哈希算法：MD5、SHA-1、SHA-256、HMAC
2. 对称加密：AES、DES、分组模式
3. 非对称加密：RSA、ECDH、数字签名
4. 编码工具：Base64、Hex
5. 实用工具：密码存储、数据加密、签名工具

## 2. 快速开始

### 2.1 安装

```bash
# 克隆项目
git clone <repository-url>
cd crypto-lib

# 安装依赖（本项目无外部依赖）
pip install -r requirements.txt
```

### 2.2 基本使用

#### 哈希计算

```python
from src.hash import SHA256, HMAC

# SHA-256哈希
hash_value = SHA256.hash("Hello, World!")
print(f"SHA-256: {hash_value}")

# HMAC消息认证
key = "my_secret_key"
mac = HMAC.compute(key, "Hello", 'sha256')
is_valid = HMAC.verify(key, "Hello", mac, 'sha256')
```

#### 数据加密

```python
from src.symmetric import AES
import os

# AES加密
key = os.urandom(32)  # AES-256
aes = AES(key)

# CBC模式加密
plaintext = b"Secret message"
ciphertext, iv = aes.encrypt(plaintext, 'cbc')
decrypted = aes.decrypt(ciphertext, 'cbc', iv)
```

#### 非对称加密

```python
from src.asymmetric import RSA, ECDH

# RSA加密
rsa = RSA(2048)
public_key, private_key = rsa.generate_keys()
ciphertext = rsa.encrypt(b"Hello")
decrypted = rsa.decrypt(ciphertext)

# ECDH密钥交换
alice = ECDH()
bob = ECDH()
alice_priv, alice_pub = alice.generate_keypair()
bob_priv, bob_pub = bob.generate_keypair()
shared = alice.compute_shared_secret(alice_priv, bob_pub)
```

#### 数字签名

```python
from src.utils import SignatureUtil

# ECDSA签名
sig = SignatureUtil('ecdsa')
signature_info = sig.sign_message(b"Important document")
is_valid = sig.verify_message(b"Important document", signature_info)
```

## 3. API参考

### 3.1 哈希模块

#### MD5
```python
from src.hash import MD5

# 一次性计算
hash_value = MD5.hash(data)

# 分块计算
hasher = MD5()
hasher.update("part1")
hasher.update("part2")
hash_value = hasher.hexdigest()
```

#### SHA-1
```python
from src.hash import SHA1

hash_value = SHA1.hash(data)
```

#### SHA-256
```python
from src.hash import SHA256

hash_value = SHA256.hash(data)
```

#### HMAC
```python
from src.hash import HMAC

# 计算HMAC
mac = HMAC.compute(key, data, 'sha256')

# 验证HMAC
is_valid = HMAC.verify(key, data, expected_mac, 'sha256')
```

### 3.2 对称加密模块

#### AES
```python
from src.symmetric import AES

# 初始化
aes = AES(key)  # key: 16/24/32字节

# 加密
ciphertext, iv = aes.encrypt(plaintext, 'cbc')

# 解密
plaintext = aes.decrypt(ciphertext, 'cbc', iv)

# 单块加密
block_cipher = aes.encrypt_block(block)
block_plain = aes.decrypt_block(block_cipher)
```

#### DES
```python
from src.symmetric import DES

des = DES(key)  # key: 8字节
ciphertext, iv = des.encrypt(plaintext, 'cbc')
plaintext = des.decrypt(ciphertext, 'cbc', iv)
```

### 3.3 非对称加密模块

#### RSA
```python
from src.asymmetric import RSA

rsa = RSA(key_size=2048)
public_key, private_key = rsa.generate_keys()

# 加密
ciphertext = rsa.encrypt(plaintext, public_key)

# 解密
plaintext = rsa.decrypt(ciphertext, private_key)

# 签名
signature = rsa.sign(message, private_key)

# 验证
is_valid = rsa.verify(message, signature, public_key)
```

#### ECDH
```python
from src.asymmetric import ECDH

ecdh = ECDH()
private_key, public_key = ecdh.generate_keypair()
shared_secret = ecdh.compute_shared_secret(private_key, other_public_key)
```

### 3.4 编码模块

#### Base64
```python
from src.encoding import Base64Codec

encoded = Base64Codec.encode(data)
decoded = Base64Codec.decode(encoded)

# URL安全编码
encoded = Base64Codec.url_encode(data)
decoded = Base64Codec.url_decode(encoded)
```

#### Hex
```python
from src.encoding import HexCodec

encoded = HexCodec.encode(data)
decoded = HexCodec.decode(encoded)

# 格式化输出
formatted = HexCodec.format_hex(data, ':', 1)
```

### 3.5 工具模块

#### PasswordManager
```python
from src.utils import PasswordManager

pm = PasswordManager(iterations=100000)

# 存储密码
stored = pm.store_password(password)

# 验证密码
is_valid = pm.check_password(password, stored)
```

#### DataEncryptor
```python
from src.utils import DataEncryptor

encryptor = DataEncryptor('aes', 256, 'cbc')

# 加密
encrypted = encryptor.encrypt(data)

# 解密
decrypted = encryptor.decrypt(encrypted)

# 字符串加密
encoded = encryptor.encrypt_string(text)
text = encryptor.decrypt_string(encoded)
```

#### SignatureUtil
```python
from src.utils import SignatureUtil

sig = SignatureUtil('ecdsa')

# 签名消息
signature_info = sig.sign_message(message)

# 验证消息
is_valid = sig.verify_message(message, signature_info)

# 签名文件
signature_info = sig.sign_file(filepath)

# 验证文件
is_valid = sig.verify_file(filepath, signature_info)
```

## 4. 使用示例

### 4.1 密码存储系统

```python
from src.utils import PasswordManager

pm = PasswordManager()

# 用户注册
password = "user_password"
stored = pm.store_password(password)
# 将stored存储到数据库

# 用户登录
input_password = "user_password"
if pm.check_password(input_password, stored):
    print("登录成功")
else:
    print("密码错误")
```

### 4.2 文件加密

```python
from src.utils import DataEncryptor

# 加密文件
encryptor = DataEncryptor('aes', 256, 'cbc')
with open('secret.txt', 'rb') as f:
    data = f.read()

encrypted = encryptor.encrypt(data)
with open('secret.enc', 'w') as f:
    import json
    json.dump(encrypted, f)

# 解密文件
with open('secret.enc', 'r') as f:
    encrypted = json.load(f)

decrypted = encryptor.decrypt(encrypted)
with open('secret_decrypted.txt', 'wb') as f:
    f.write(decrypted)
```

### 4.3 文档签名

```python
from src.utils import SignatureUtil

sig = SignatureUtil('ecdsa')

# 签名文档
signature_info = sig.sign_file('document.pdf')

# 发送文档和签名...

# 验证文档
if sig.verify_file('document.pdf', signature_info):
    print("文档未被篡改")
else:
    print("文档已被篡改")
```

## 5. 安全警告

### 5.1 学习用途
本库仅用于学习和教学目的，不建议用于生产环境。

### 5.2 生产环境建议
- 使用成熟的密码学库（如`cryptography`）
- 遵循安全最佳实践
- 定期更新依赖
- 进行安全审计

### 5.3 已知限制
- 不支持硬件加速
- 性能不如C实现
- 部分算法已被破解（MD5、DES）

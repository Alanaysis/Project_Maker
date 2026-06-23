# 02 - 设计文档

## 系统架构

```
crypto-lib/
├── src/
│   ├── lib.rs          # 库入口，错误类型定义
│   ├── aes.rs          # AES对称加密实现
│   ├── rsa.rs          # RSA非对称加密实现
│   └── ecc.rs          # 椭圆曲线密码学实现
├── tests/
│   └── integration.rs  # 集成测试
├── examples/
│   ├── aes_example.rs  # AES使用示例
│   ├── rsa_example.rs  # RSA使用示例
│   └── ecc_example.rs  # ECC使用示例
└── Cargo.toml
```

## 模块设计

### 1. AES模块 (aes.rs)

**核心结构体：**
```rust
pub struct AesKey {
    key: Vec<u8>,
    size: AesKeySize,
}

pub struct AesCipher {
    key: AesKey,
    round_keys: Vec<[u8; 4]>,
}
```

**主要功能：**
- `AesKey::generate(bit_size)` - 生成随机密钥
- `AesCipher::encrypt(plaintext)` - CBC模式加密
- `AesCipher::decrypt(ciphertext)` - CBC模式解密

**内部实现：**
- S-box查找表
- 轮密钥生成
- SubBytes/ShiftRows/MixColumns变换
- PKCS7填充

### 2. RSA模块 (rsa.rs)

**核心结构体：**
```rust
pub struct RsaKeyPair {
    public_key: RsaPublicKey,
    private_key: RsaPrivateKey,
}
```

**主要功能：**
- `RsaKeyPair::generate(bits)` - 生成密钥对
- `encrypt(message)` - 公钥加密
- `decrypt(ciphertext)` - 私钥解密
- `encrypt_oaep/decrypt_oaep` - OAEP填充加密

**数学工具：**
- Miller-Rabin素性测试
- 模逆运算（扩展欧几里得算法）
- 模幂运算

### 3. ECC模块 (ecc.rs)

**核心结构体：**
```rust
pub enum EcPoint {
    Infinity,
    Point { x: BigUint, y: BigUint },
}

pub struct EllipticCurve { ... }
pub struct EcdhKeyExchange { ... }
pub struct Ecdsa { ... }
```

**主要功能：**
- 椭圆曲线点运算（加法、倍点、标量乘法）
- ECDH密钥交换
- ECDSA签名/验证

**支持的曲线：**
- secp256k1（比特币使用）
- P-256（NIST标准）

## 数据流

### AES加密流程
```
明文 → PKCS7填充 → 分块 → 每块异或IV → AES加密 → 密文
```

### RSA加密流程
```
消息 → 数值转换 → 模幂运算 → 密文
```

### ECDH密钥交换流程
```
Alice生成私钥a → A = aG → 发送A给Bob
Bob生成私钥b → B = bG → 发送给Alice
共享密钥 = aB = bA
```

## 错误处理

```rust
pub enum CryptoError {
    InvalidKeySize,
    InvalidBlockSize,
    DecryptionFailed,
    InvalidInput,
    KeyGenerationFailed,
}
```

## 安全设计原则

1. **密钥生成**: 使用密码学安全的随机数生成器
2. **常量时间操作**: 避免时序攻击（在实际生产环境中）
3. **输入验证**: 验证所有输入参数
4. **错误处理**: 不泄漏敏感信息

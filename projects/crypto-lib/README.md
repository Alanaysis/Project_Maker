# 密码学库 (Crypto Library)

一个用Rust实现的密码学库，支持AES对称加密、RSA非对称加密和椭圆曲线密码学（ECC）。

## 功能特性

### AES对称加密
- 支持AES-128、AES-192、AES-256
- CBC模式加密
- PKCS7填充
- 随机IV生成

### RSA非对称加密
- RSA-512到RSA-4096密钥生成
- 公钥加密/私钥解密
- OAEP填充支持
- Miller-Rabin素性测试

### 椭圆曲线密码学
- secp256k1曲线（比特币使用）
- P-256曲线（NIST标准）
- ECDH密钥交换
- ECDSA数字签名

## 快速开始

### 添加依赖

在`Cargo.toml`中添加：
```toml
[dependencies]
crypto-lib = { path = "../crypto-lib" }
```

### AES加密示例

```rust
use crypto_lib::aes::{AesKey, AesCipher};

fn main() {
    // 生成256位AES密钥
    let key = AesKey::generate(256);
    let cipher = AesCipher::new(key);

    // 加密
    let plaintext = b"Hello, World!";
    let ciphertext = cipher.encrypt(plaintext);

    // 解密
    let decrypted = cipher.decrypt(&ciphertext);
    assert_eq!(decrypted, plaintext);
}
```

### RSA加密示例

```rust
use crypto_lib::rsa::RsaKeyPair;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // 生成RSA密钥对
    let keypair = RsaKeyPair::generate(2048)?;

    // 加密
    let message = b"Secret message";
    let ciphertext = keypair.encrypt(message);

    // 解密
    let decrypted = keypair.decrypt(&ciphertext);
    assert_eq!(decrypted, message);

    Ok(())
}
```

### ECDH密钥交换示例

```rust
use crypto_lib::ecc::{EllipticCurve, EcdhKeyExchange};

fn main() {
    let curve = EllipticCurve::secp256k1();
    let ecdh = EcdhKeyExchange::new(curve);

    // Alice生成密钥对
    let (alice_private, alice_public) = ecdh.generate_keypair();

    // Bob生成密钥对
    let (bob_private, bob_public) = ecdh.generate_keypair();

    // 计算共享密钥
    let alice_shared = ecdh.compute_shared_secret(&alice_private, &bob_public);
    let bob_shared = ecdh.compute_shared_secret(&bob_private, &alice_public);

    assert_eq!(alice_shared, bob_shared);
}
```

## 运行示例

```bash
# AES示例
cargo run --example aes_example

# RSA示例
cargo run --example rsa_example

# ECC示例
cargo run --example ecc_example
```

## 运行测试

```bash
# 运行所有测试
cargo test

# 运行特定模块测试
cargo test aes
cargo test rsa
cargo test ecc

# 运行集成测试
cargo test --test integration
```

## 项目结构

```
crypto-lib/
├── src/
│   ├── lib.rs          # 库入口
│   ├── aes.rs          # AES实现
│   ├── rsa.rs          # RSA实现
│   └── ecc.rs          # ECC实现
├── tests/
│   └── integration_test.rs
├── examples/
│   ├── aes_example.rs
│   ├── rsa_example.rs
│   └── ecc_example.rs
└── docs/
    ├── 01-RESEARCH.md
    ├── 02-DESIGN.md
    ├── 03-IMPLEMENTATION.md
    ├── 04-TESTING.md
    └── 05-DEVELOPMENT.md
```

## 算法说明

### AES加密流程

```
明文 → PKCS7填充 → 分块 → CBC模式加密 → 密文

每块加密过程：
1. 与前一块密文异或
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

⚠️ **警告：此库仅用于学习目的，不建议用于生产环境。**

生产环境建议使用：
- [RustCrypto](https://github.com/RustCrypto) 项目
- [ring](https://github.com/briansmith/ring)
- [OpenSSL](https://www.openssl.org/)

## 学习资源

- [AES标准 (FIPS 197)](https://csrc.nist.gov/publications/detail/fips/197/final)
- [RSA论文](https://people.csail.mit.edu/rivest/Rsapaper.pdf)
- [椭圆曲线密码学介绍](https://blog.cloudflare.com/a-relatively-easy-to-understand-primer-on-elliptic-curve-cryptography/)

## 许可证

MIT License

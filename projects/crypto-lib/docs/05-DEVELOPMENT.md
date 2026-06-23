# 05 - 开发指南

## 环境准备

### 安装Rust

```bash
# 安装rustup
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 配置环境变量
source $HOME/.cargo/env

# 验证安装
rustc --version
cargo --version
```

### 项目依赖

```toml
[dependencies]
rand = "0.8"
num-bigint = "0.4"
num-traits = "0.2"
num-integer = "0.1"
```

## 构建项目

### 编译
```bash
cd projects/crypto-lib
cargo build
```

### 发布构建
```bash
cargo build --release
```

### 检查代码
```bash
cargo check
```

## 运行示例

### AES示例
```bash
cargo run --example aes_example
```

### RSA示例
```bash
cargo run --example rsa_example
```

### ECC示例
```bash
cargo run --example ecc_example
```

## 测试

### 运行所有测试
```bash
cargo test
```

### 运行特定测试
```bash
cargo test test_aes
cargo test test_rsa
cargo test test_ecc
```

### 显示测试输出
```bash
cargo test -- --nocapture
```

## 代码质量

### 格式化
```bash
cargo fmt
```

### Lint检查
```bash
cargo clippy
```

### 文档生成
```bash
cargo doc --open
```

## 项目结构

```
crypto-lib/
├── Cargo.toml              # 项目配置
├── src/
│   ├── lib.rs              # 库入口
│   ├── aes.rs              # AES实现
│   ├── rsa.rs              # RSA实现
│   └── ecc.rs              # ECC实现
├── tests/
│   └── integration_test.rs # 集成测试
├── examples/
│   ├── aes_example.rs      # AES示例
│   ├── rsa_example.rs      # RSA示例
│   └── ecc_example.rs      # ECC示例
└── docs/
    ├── 01-RESEARCH.md      # 研究笔记
    ├── 02-DESIGN.md        # 设计文档
    ├── 03-IMPLEMENTATION.md # 实现细节
    ├── 04-TESTING.md       # 测试文档
    └── 05-DEVELOPMENT.md   # 开发指南
```

## 使用示例

### AES加密

```rust
use crypto_lib::aes::{AesKey, AesCipher};

// 生成密钥
let key = AesKey::generate(256);
let cipher = AesCipher::new(key);

// 加密
let plaintext = b"Secret message";
let ciphertext = cipher.encrypt(plaintext);

// 解密
let decrypted = cipher.decrypt(&ciphertext);
assert_eq!(decrypted, plaintext);
```

### RSA加密

```rust
use crypto_lib::rsa::RsaKeyPair;

// 生成密钥对
let keypair = RsaKeyPair::generate(2048)?;

// 加密
let message = b"Hello RSA!";
let ciphertext = keypair.encrypt(message);

// 解密
let decrypted = keypair.decrypt(&ciphertext);
assert_eq!(decrypted, message);
```

### ECDH密钥交换

```rust
use crypto_lib::ecc::{EllipticCurve, EcdhKeyExchange};

let curve = EllipticCurve::secp256k1();
let ecdh = EcdhKeyExchange::new(curve);

// Alice
let (alice_priv, alice_pub) = ecdh.generate_keypair();

// Bob
let (bob_priv, bob_pub) = ecdh.generate_keypair();

// 共享密钥
let alice_shared = ecdh.compute_shared_secret(&alice_priv, &bob_pub);
let bob_shared = ecdh.compute_shared_secret(&bob_priv, &alice_pub);
assert_eq!(alice_shared, bob_shared);
```

## 扩展开发

### 添加新算法

1. 在`src/`下创建新模块
2. 在`lib.rs`中导出模块
3. 实现核心功能
4. 添加单元测试
5. 创建示例程序
6. 更新文档

### 性能优化

1. 使用`criterion`进行基准测试
2. 优化热路径代码
3. 考虑使用汇编优化关键操作

### 安全增强

1. 实现常量时间操作
2. 添加内存安全保护
3. 实现安全的密钥存储

## 故障排除

### 编译错误

**问题：** 找不到依赖
```bash
# 解决：更新依赖
cargo update
```

**问题：** 版本不兼容
```bash
# 解决：检查Cargo.toml中的版本
cargo check
```

### 测试失败

**问题：** 随机数导致测试不稳定
```bash
# 解决：使用固定种子或多次运行
cargo test -- --test-threads=1
```

## 下一步

1. 实现更多椭圆曲线（Ed25519等）
2. 添加数字签名标准（DSA）
3. 实现密钥派生函数（KDF）
4. 添加消息认证码（HMAC）
5. 实现TLS握手协议

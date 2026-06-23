# 04 - 测试文档

## 测试策略

### 单元测试

#### AES测试

```rust
#[test]
fn test_aes128_encrypt_decrypt() {
    let key = AesKey::generate(128);
    let cipher = AesCipher::new(key);
    let plaintext = b"Hello, World!";
    let ciphertext = cipher.encrypt(plaintext);
    let decrypted = cipher.decrypt(&ciphertext);
    assert_eq!(decrypted, plaintext);
}
```

**测试覆盖：**
- AES-128/192/256所有密钥长度
- 空输入
- 精确块大小输入
- 多块输入
- GF(2^8)乘法
- S-box查找

#### RSA测试

```rust
#[test]
fn test_rsa_encrypt_decrypt() {
    let keypair = RsaKeyPair::generate(1024).unwrap();
    let message = b"Hello RSA!";
    let ciphertext = keypair.encrypt(message);
    let decrypted = keypair.decrypt(&ciphertext);
    assert_eq!(decrypted, message);
}
```

**测试覆盖：**
- 密钥生成
- 加密/解密
- 不同消息长度
- GCD运算
- 模逆运算
- Miller-Rabin素性测试

#### ECC测试

```rust
#[test]
fn test_point_on_curve() {
    let curve = EllipticCurve::test_curve();
    assert!(curve.is_on_curve(&curve.g));
}
```

**测试覆盖：**
- 曲线点验证
- 点加法单位元
- 点倍加
- 标量乘法
- ECDH密钥交换
- ECDSA签名/验证
- secp256k1和P-256曲线

### 集成测试

```rust
#[test]
fn test_combined_encryption_workflow() {
    // RSA + AES混合加密
    let keypair = RsaKeyPair::generate(1024).unwrap();
    let aes_key = AesKey::generate(256);
    let cipher = AesCipher::new(aes_key.clone());

    // 用AES加密数据
    let encrypted_data = cipher.encrypt(plaintext);

    // 用RSA加密AES密钥
    let encrypted_aes_key = keypair.encrypt(&aes_key.key);

    // 解密流程...
}
```

**测试场景：**
1. 完整加密/解密流程
2. 多方密钥交换
3. 不同密钥大小组合
4. 错误输入处理

## 运行测试

### 运行所有测试
```bash
cargo test
```

### 运行特定模块测试
```bash
cargo test aes
cargo test rsa
cargo test ecc
```

### 运行集成测试
```bash
cargo test --test integration
```

### 显示测试输出
```bash
cargo test -- --nocapture
```

## 测试结果

### 单元测试结果

```
running 22 tests
test aes::tests::test_aes128_encrypt_decrypt ... ok
test aes::tests::test_aes192_encrypt_decrypt ... ok
test aes::tests::test_aes256_encrypt_decrypt ... ok
test aes::tests::test_aes_empty_input ... ok
test aes::tests::test_aes_exact_block_size ... ok
test aes::tests::test_gmul ... ok
test aes::tests::test_s_box ... ok
test rsa::tests::test_rsa_key_generation ... ok
test rsa::tests::test_rsa_encrypt_decrypt ... ok
test rsa::tests::test_rsa_different_messages ... ok
test rsa::tests::test_gcd ... ok
test rsa::tests::test_mod_inverse ... ok
test rsa::tests::test_miller_rabin ... ok
test ecc::tests::test_point_on_curve ... ok
test ecc::tests::test_point_add_identity ... ok
test ecc::tests::test_point_double ... ok
test ecc::tests::test_scalar_mul ... ok
test ecc::tests::test_ecdh_key_exchange ... ok
test ecc::tests::test_ecdh_on_secp256k1 ... ok
test ecc::tests::test_ecdsa_sign_verify ... ok
test ecc::tests::test_secp256k1_curve_params ... ok
test ecc::tests::test_p256_curve_params ... ok

test result: ok. 22 passed; 0 failed
```

### 集成测试结果

```
running 6 tests
test test_aes_all_key_sizes ... ok
test test_rsa_workflow ... ok
test test_ecc_key_exchange_workflow ... ok
test test_ecc_digital_signature ... ok
test test_combined_encryption_workflow ... ok
test test_multi_party_key_exchange ... ok

test result: ok. 6 passed; 0 failed
```

### 文档测试结果

```
running 1 test
test src/lib.rs - (line 14) ... ok

test result: ok. 1 passed; 0 failed
```

## 测试覆盖率

| 模块 | 函数数 | 测试数 | 覆盖率 |
|------|--------|--------|--------|
| AES | 12 | 7 | ~85% |
| RSA | 8 | 6 | ~85% |
| ECC | 10 | 9 | ~85% |

## 边界条件测试

### AES边界
- 空明文
- 单块明文（16字节）
- 多块明文
- 不同密钥长度

### RSA边界
- 小素数（512位）
- 大素数（2048位）
- 特殊消息值

### ECC边界
- 无穷远点
- 同一点相加
- 负数坐标

# Embedded Security Framework / 嵌入式安全框架

> **Educational implementation of embedded security concepts in C**

---

## 📖 项目描述 / Project Description

### 中文
本项目是一个嵌入式安全框架的学习实现，涵盖嵌入式系统中的核心安全机制。通过从零实现密码学算法和安全协议，深入理解嵌入式安全的底层原理。

核心安全循环：**安全启动 → 身份认证 → 数据加密 → 安全通信**

### English
This project is an educational implementation of embedded security frameworks, covering core security mechanisms in embedded systems. By implementing cryptographic algorithms and security protocols from scratch, gain deep understanding of embedded security fundamentals.

Core security loop: **Secure Boot → Authentication → Encryption → Secure Communication**

---

## 🎯 学习目标 / Learning Objectives

### 中文
- [x] 理解嵌入式安全启动机制（信任链、固件验证）
- [x] 掌握安全密钥存储（加密存储、密钥派生）
- [x] 学会挑战-响应认证和 HMAC 消息认证
- [x] 实现 AES-128 块密码加密
- [x] 实现 SHA-256 哈希函数
- [x] 模拟 TLS/DTLS 握手协议
- [x] 理解安全通道管理

### English
- [x] Understand embedded secure boot mechanisms (chain of trust, firmware verification)
- [x] Master secure key storage (encrypted storage, key derivation)
- [x] Learn challenge-response authentication and HMAC message authentication
- [x] Implement AES-128 block cipher encryption
- [x] Implement SHA-256 hash function
- [x] Simulate TLS/DTLS handshake protocol
- [x] Understand secure channel management

---

## 🏗️ 安全架构 / Security Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Application Layer                      │
│              (Secure Channel Communication)              │
├─────────────────────────────────────────────────────────┤
│                    TLS/DTLS Layer                        │
│         (Handshake, Key Derivation, Encryption)          │
├─────────────────────────────────────────────────────────┤
│                    Security Modules                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ Secure   │ │ Auth     │ │ AES      │ │ SHA-256  │  │
│  │ Boot     │ │ Module   │ │ Cipher   │ │ Hash     │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
├─────────────────────────────────────────────────────────┤
│                  Key Storage Layer                       │
│         (Master Key → Derived Keys → Encrypted Keys)     │
├─────────────────────────────────────────────────────────┤
│                    Hardware Layer                        │
│         (TRNG, Secure Element, Flash)                    │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 项目结构 / Project Structure

```
embedded-security/
├── include/                    # Header files
│   ├── sha256.h               # SHA-256 hash function
│   ├── aes.h                  # AES-128 block cipher
│   ├── secure_boot.h          # Secure boot module
│   ├── key_storage.h          # Secure key storage
│   ├── authentication.h       # Authentication (HMAC, challenge-response)
│   ├── tls_sim.h              # TLS/DTLS handshake simulation
│   ├── secure_channel.h       # Secure channel management
│   └── rng.h                  # Random number generation
├── src/                        # Implementation files
│   ├── sha256.c
│   ├── aes.c
│   ├── secure_boot.c
│   ├── key_storage.c
│   ├── authentication.c
│   ├── tls_sim.c
│   ├── secure_channel.c
│   └── rng.c
├── examples/                   # Demo programs
│   ├── secure_boot_demo.c     # Secure boot demonstration
│   ├── key_exchange_demo.c    # Key storage and derivation demo
│   ├── auth_demo.c            # Authentication demo
│   └── encrypted_comm_demo.c  # Encrypted communication demo
├── tests/                      # Unit tests
│   ├── test_sha256.c
│   ├── test_aes.c
│   ├── test_authentication.c
│   ├── test_key_storage.c
│   └── test_tls_sim.c
├── Makefile
└── README.md
```

---

## 🔧 构建和运行 / Build and Run

### 构建项目 / Build
```bash
make all          # Build all examples and tests
make examples     # Build examples only
make tests        # Build tests only
```

### 运行测试 / Run Tests
```bash
make test-run     # Run all unit tests
```

### 运行示例 / Run Examples
```bash
make run-all      # Run all demo programs
./build/secure_boot_demo    # Secure boot demo
./build/key_exchange_demo   # Key exchange demo
./build/auth_demo           # Authentication demo
./build/encrypted_comm_demo # Encrypted communication demo
```

### 清理 / Clean
```bash
make clean
```

---

## 📚 核心模块说明 / Core Modules

### 1. SHA-256 哈希函数
- **文件**: `src/sha256.c`
- **功能**: 实现 FIPS 180-4 标准的 SHA-256 算法
- **特性**:
  - 增量哈希计算（支持流式数据）
  - 雪崩效应验证
  - 确定性输出

### 2. AES-128 加密
- **文件**: `src/aes.c`
- **功能**: 实现 NIST FIPS 197 标准的 AES-128 块密码
- **特性**:
  - 支持 AES-128/192/256
  - S-box 替换和逆替换
  - ShiftRows 和 MixColumns 变换
  - ECB 模式加密/解密

### 3. 安全启动
- **文件**: `src/secure_boot.c`
- **功能**: 实现信任链启动过程
- **特性**:
  - 多阶段引导链（ROM → Bootloader → Firmware → App）
  - 固件哈希验证
  - 签名验证（简化 RSA 风格）
  - 篡改检测

### 4. 安全密钥存储
- **文件**: `src/key_storage.c`
- **功能**: 安全存储和检索加密密钥
- **特性**:
  - 主密钥加密存储
  - 密钥派生（KDF）
  - 密钥轮换
  - 安全擦除

### 5. 认证模块
- **文件**: `src/authentication.c`
- **功能**: 挑战-响应认证和 HMAC
- **特性**:
  - HMAC-SHA256 消息认证
  - 挑战-响应认证流程
  - 会话管理
  - 重放攻击防护

### 6. TLS/DTLS 握手模拟
- **文件**: `src/tls_sim.c`
- **功能**: 模拟 TLS 1.2 握手协议
- **特性**:
  - ClientHello / ServerHello
  - DH 密钥交换模拟
  - PRF 密钥派生
  - 密码套件协商

### 7. 安全通道管理
- **文件**: `src/secure_channel.c`
- **功能**: 管理安全通信通道
- **特性**:
  - 通道生命周期管理
  - 加密发送/接收
  - 通道复用

### 8. 随机数生成
- **文件**: `src/rng.c`
- **功能**: 密码学安全随机数生成
- **特性**:
  - CSPRNG 实现
  - 熵池管理
  - 定期重播种

---

## 🔐 安全概念 / Security Concepts

### 信任链（Chain of Trust）
```
ROM Bootstrap (信任根)
    ↓ 验证
Secondary Bootloader
    ↓ 验证
Application Firmware
    ↓ 验证
Application Code
```

### 密钥层次（Key Hierarchy）
```
Master Key (信任根)
    ↓ KDF
Session Keys
    ↓
Encryption Keys + MAC Keys
```

### 认证流程
```
Client:  生成随机挑战 C
Server:  用共享密钥计算 HMAC(K, C) = R
Client:  发送 R 给 Server
Server:  验证 R 是否正确
```

---

## 📊 项目统计 / Statistics

| 指标 | 数值 |
|------|------|
| 源代码文件 | 8 |
| 头文件 | 8 |
| 示例程序 | 4 |
| 测试文件 | 5 |
| 总代码行数 | ~3000 |
| 支持算法 | SHA-256, AES-128/192/256, HMAC-SHA256 |

---

## 📝 参考 / References

- NIST FIPS 180-4: Secure Hash Standard
- NIST FIPS 197: Advanced Encryption Standard
- RFC 5246: TLS 1.2 Protocol
- mbedTLS (reference implementation)
- Embedded Security textbooks

---

## 📄 许可证 / License

MIT License

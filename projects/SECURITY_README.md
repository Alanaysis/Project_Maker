# 🔐 安全 & 工具模块

> 4 个深度学习项目，涵盖密码学、沙箱隔离、解释器、倒排索引

---

## 📋 项目列表

| 项目 | 描述 | 技术栈 | 难度 | 状态 |
|------|------|--------|------|------|
| [crypto-lib](crypto-lib/) | 密码学库 | C | ⭐⭐⭐⭐ | ✅ |
| [sandbox](sandbox/) | 沙箱隔离 | C | ⭐⭐⭐⭐ | ✅ |
| [interpreter](interpreter/) | 解释器 | Python | ⭐⭐⭐⭐ | ✅ |
| [inverted-index](inverted-index/) | 倒排索引 | Go | ⭐⭐⭐⭐ | ✅ |

---

## 🎯 学习路径

```
密码学基础 → 沙箱隔离 → 解释器 → 倒排索引
    ↓           ↓          ↓          ↓
  加密算法    进程隔离    词法分析    索引构建
  密钥管理    资源限制    语法分析    查询优化
  数字签名    安全策略    语义分析    相关性排序
```

### 推荐学习顺序

1. **crypto-lib** (密码学库)
   - 学习对称加密（AES）和非对称加密（RSA）
   - 理解椭圆曲线密码学（ECC）
   - 掌握数字签名和哈希算法

2. **sandbox** (沙箱隔离)
   - 学习进程隔离技术
   - 理解资源限制和权限控制
   - 掌握安全策略设计

3. **interpreter** (解释器)
   - 学习词法分析和语法分析
   - 理解抽象语法树（AST）
   - 掌握语义分析和代码执行

4. **inverted-index** (倒排索引)
   - 学习索引构建原理
   - 理解查询优化技术
   - 掌握相关性排序算法

---

## 🔧 技术栈

| 技术 | 用途 | 学习资源 |
|------|------|----------|
| **C** | 密码学库、沙箱 | [C 官方文档](https://en.cppreference.com/w/c) |
| **Python** | 解释器 | [Python 官方文档](https://docs.python.org/3/) |
| **Go** | 倒排索引 | [Go 官方文档](https://go.dev/doc/) |
| **OpenSSL** | 加密算法 | [OpenSSL 文档](https://www.openssl.org/docs/) |

---

## 📊 项目详情

### 1. crypto-lib (密码学库)

**核心功能**：
- AES 对称加密（ECB、CBC、CTR 模式）
- RSA 非对称加密（密钥生成、加密、解密）
- 椭圆曲线密码学（ECC、ECDSA）
- 哈希算法（SHA-256、SHA-512）
- 数字签名和验证

**代码量**：约 2000 行

**快速开始**：
```bash
cd crypto-lib
make
./crypto_demo
```

---

### 2. sandbox (沙箱隔离)

**核心功能**：
- 进程隔离（Namespace、Cgroups）
- 资源限制（CPU、内存、磁盘）
- 文件系统隔离（chroot、pivot_root）
- 网络隔离（Network Namespace）
- 安全策略（Seccomp、AppArmor）

**代码量**：约 1500 行

**快速开始**：
```bash
cd sandbox
make
./sandbox_demo
```

---

### 3. interpreter (解释器)

**核心功能**：
- 词法分析器（Tokenizer）
- 语法分析器（Parser）
- 抽象语法树（AST）
- 语义分析
- 代码执行引擎

**代码量**：约 2500 行

**快速开始**：
```bash
cd interpreter
python main.py examples/hello.lang
```

---

### 4. inverted-index (倒排索引)

**核心功能**：
- 文档索引构建
- 倒排索引数据结构
- 查询解析和执行
- 相关性排序（TF-IDF）
- 索引压缩和优化

**代码量**：约 1800 行

**快速开始**：
```bash
cd inverted-index
go build -o indexer ./cmd/indexer
./indexer --build --input docs/ --output index.db
./indexer --query "search term"
```

---

## 📚 学习资源

### 书籍
- 《应用密码学》
- 《深入理解计算机系统》
- 《编译原理》

### 课程
- [Stanford CS255](https://crypto.stanford.edu/~dabo/cs255/)
- [MIT 6.035](https://css.csail.mit.edu/6.035/)

### 开源项目
- [OpenSSL](https://github.com/openssl/openssl)
- [gVisor](https://github.com/google/gvisor)
- [V8](https://github.com/v8/v8)

---

## 🔗 相关链接

- [返回主 README](../README.md)
- [学习路径图](../LEARNING_PATHS.md)
- [项目索引](../PROJECT_INDEX.md)

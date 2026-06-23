# 🤖 NLP & 机器学习模块

> **9 个深度学习项目** | 涵盖自然语言处理、机器学习算法、数据结构、边缘计算等领域

---

## 📋 模块概述

本模块包含自然语言处理和机器学习相关的学习项目，从基础算法到实际应用，帮助理解 NLP 和 ML 的核心原理。

---

## 🎯 项目列表

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [tokenizer](tokenizer/) | 中文分词器 | Python | ⭐⭐⭐ |
| [language-model](language-model/) | N-gram 语言模型 | Python | ⭐⭐⭐ |
| [random-forest](random-forest/) | 随机森林分类器 | Python | ⭐⭐⭐⭐ |
| [svm](svm/) | 支持向量机 | Python | ⭐⭐⭐⭐ |
| [dht](dht/) | 分布式哈希表 | Go | ⭐⭐⭐⭐ |
| [dns-server](dns-server/) | DNS 服务器 | Go | ⭐⭐⭐⭐ |
| [distributed-transaction](distributed-transaction/) | 分布式事务 | Go | ⭐⭐⭐⭐⭐ |
| [matching-engine](matching-engine/) | 撮合引擎 | C++ | ⭐⭐⭐⭐⭐ |
| [query-parser](query-parser/) | 查询解析器 | Go | ⭐⭐⭐⭐ |
| [edge-computing](edge-computing/) | 边缘计算框架 | Python | ⭐⭐⭐⭐ |

---

## 📖 详细说明

### 🗣️ 中文分词器 (tokenizer)

**项目路径**: `projects/tokenizer/`

**学习目标**:
- 理解分词算法
- 掌握词典构建
- 学会 HMM/CRF

**核心功能**:
- 正向最大匹配 (FMM)
- 逆向最大匹配 (BMM)
- HMM 分词
- 词典管理

**技术栈**: Python

**快速开始**:
```bash
cd projects/tokenizer
python3 example.py
```

---

### 🗣️ 语言模型 (language-model)

**项目路径**: `projects/language-model/`

**学习目标**:
- 理解语言模型的基本概念
- 掌握 N-gram 统计方法
- 学会困惑度 (Perplexity) 评估

**核心功能**:
- N-gram 模型 (Unigram, Bigram, Trigram)
- Add-k 平滑
- 文本生成（温度控制）
- 困惑度评估

**技术栈**: Python

**快速开始**:
```bash
cd projects/language-model
python3 -m pytest tests/ -v
```

---

### 🌲 随机森林 (random-forest)

**项目路径**: `projects/random-forest/`

**学习目标**:
- 理解 Bagging 原理
- 掌握随机特征选择
- 学会集成学习

**核心功能**:
- 决策树实现
- 随机森林集成
- 特征重要性评估

**技术栈**: Python

---

### 📊 支持向量机 (svm)

**项目路径**: `projects/svm/`

**学习目标**:
- 理解 SVM 的数学原理
- 掌握核函数的作用
- 学会 SMO 优化算法

**核心功能**:
- 线性 SVM
- 核函数 SVM
- SMO 优化算法

**技术栈**: Python

---

### 🔗 分布式哈希表 (dht)

**项目路径**: `projects/dht/`

**学习目标**:
- 理解 DHT 原理
- 掌握 Chord 协议
- 学会分布式系统设计

**核心功能**:
- Chord 协议实现
- 节点管理
- 键值存储

**技术栈**: Go

---

### 🌐 DNS 服务器 (dns-server)

**项目路径**: `projects/dns-server/`

**学习目标**:
- 理解 DNS 协议
- 掌握 UDP 编程
- 学会协议解析

**核心功能**:
- DNS 协议解析
- 域名解析
- 缓存管理

**技术栈**: Go

---

### 💰 分布式事务 (distributed-transaction)

**项目路径**: `projects/distributed-transaction/`

**学习目标**:
- 理解分布式事务原理
- 掌握 2PC/3PC 协议
- 学会 Saga 模式

**核心功能**:
- 两阶段提交
- Saga 模式
- 事务协调器

**技术栈**: Go

---

### 📈 撮合引擎 (matching-engine)

**项目路径**: `projects/matching-engine/`

**学习目标**:
- 理解订单簿原理
- 掌握撮合算法
- 学会高性能计算

**核心功能**:
- 订单簿管理
- 价格优先撮合
- 时间优先撮合

**技术栈**: C++

---

### 🔍 查询解析器 (query-parser)

**项目路径**: `projects/query-parser/`

**学习目标**:
- 理解查询解析
- 掌握布尔查询
- 学会相关性排序

**核心功能**:
- 查询字符串解析（词法分析、语法分析）
- 布尔查询支持（AND、OR、NOT）
- 短语查询（精确短语匹配）
- 相关性排序（TF-IDF 算法）
- 倒排索引

**技术栈**: Go

**快速开始**:
```bash
cd projects/query-parser
go run cmd/parser/main.go "hello AND world"
```

---

### 🌐 边缘计算 (edge-computing)

**项目路径**: `projects/edge-computing/`

**学习目标**:
- 理解边缘计算的核心概念
- 掌握任务卸载策略
- 学会资源调度和负载均衡

**核心功能**:
- 边缘节点管理
- 任务分发和调度
- 结果收集和聚合
- 多种负载均衡算法

**技术栈**: Python

**快速开始**:
```bash
cd projects/edge-computing
python3 -m pytest tests/ -v
```

---

## 🛤️ 学习路径

### 推荐学习顺序

1. **基础算法** (1-2 周)
   - [tokenizer](tokenizer/) - 中文分词器
   - [language-model](language-model/) - N-gram 语言模型
   - [random-forest](random-forest/) - 随机森林

2. **进阶算法** (2-3 周)
   - [svm](svm/) - 支持向量机

3. **分布式系统** (3-4 周)
   - [dht](dht/) - 分布式哈希表
   - [dns-server](dns-server/) - DNS 服务器

4. **搜索引擎** (2-3 周)
   - [query-parser](query-parser/) - 查询解析器

5. **高级应用** (4-5 周)
   - [distributed-transaction](distributed-transaction/) - 分布式事务
   - [matching-engine](matching-engine/) - 撮合引擎

6. **边缘计算** (2-3 周)
   - [edge-computing](edge-computing/) - 边缘计算框架

---

## 📊 学习成果

完成本模块后，你将掌握：

- **NLP 基础**: 分词算法、词典管理、HMM 模型、语言模型
- **机器学习**: 决策树、集成学习、SVM 原理
- **分布式系统**: DHT、DNS、分布式事务
- **搜索引擎**: 查询解析、布尔查询、相关性排序
- **高性能计算**: 撮合引擎、订单簿管理
- **边缘计算**: 任务卸载、资源调度、负载均衡

---

## 🔗 相关资源

- [NLP 学习笔记](tokenizer/LEARNING_NOTES.md) - 中文分词器学习笔记
- [语言模型学习笔记](language-model/LEARNING_NOTES.md) - N-gram 语言模型学习笔记
- [机器学习笔记](random-forest/LEARNING_NOTES.md) - 随机森林学习笔记
- [SVM 学习笔记](svm/LEARNING_NOTES.md) - SVM 学习笔记
- [查询解析器学习笔记](query-parser/LEARNING_NOTES.md) - 查询解析器学习笔记
- [边缘计算学习笔记](edge-computing/LEARNING_NOTES.md) - 边缘计算学习笔记

---

## 📈 项目统计

| 维度 | 数量 |
|------|------|
| **总项目数** | 9 |
| **技术栈** | 3 (Python, Go, C++) |
| **总代码行数** | 15,000+ |
| **文档数量** | 35+ |

---

## 🎯 快速开始

### 1. 选择一个项目

```bash
# 查看所有项目
ls projects/

# 进入感兴趣的项目
cd projects/tokenizer
```

### 2. 查看项目说明

```bash
# 查看项目 README
cat README.md

# 查看学习笔记
cat LEARNING_NOTES.md
```

### 3. 开始学习

```bash
# 安装依赖
pip install -r requirements.txt

# 运行示例
python3 example.py

# 运行测试
pytest tests/
```

---

## 🤝 贡献

欢迎贡献！请查看 [贡献指南](../CONTRIBUTING.md)。

---

## 📄 许可证

MIT License

---

[返回主目录](../README.md)

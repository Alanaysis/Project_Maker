# 🤖 NLP & 机器学习模块

> **13 个深度学习项目** | 涵盖自然语言处理、机器学习算法、数据结构、边缘计算、概率算法等领域

---

## 📋 模块概述

本模块包含自然语言处理和机器学习相关的学习项目，从基础算法到实际应用，帮助理解 NLP 和 ML 的核心原理。

---

## 🎯 项目列表

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [tokenizer](tokenizer/) | 中文分词器 | Python | ⭐⭐⭐ |
| [language-model](language-model/) | N-gram 语言模型 | Python | ⭐⭐⭐ |
| [text-classification](text-classification/) | 文本分类系统 | Python, NumPy | ⭐⭐⭐⭐ |
| [word2vec](word2vec/) | 词向量 Word2Vec | Python, NumPy | ⭐⭐⭐⭐ |
| [random-forest](random-forest/) | 随机森林分类+回归+评估 | Python, NumPy | ⭐⭐⭐⭐ |
| [svm](svm/) | 支持向量机 | Python | ⭐⭐⭐⭐ |
| [hyperloglog](hyperloglog/) | HyperLogLog 基数估计 | Go | ⭐⭐⭐⭐ |
| [dht](dht/) | 分布式哈希表 | Go | ⭐⭐⭐⭐ |
| [dns-server](dns-server/) | DNS 服务器 | C++ | ⭐⭐⭐⭐ |
| [distributed-transaction](distributed-transaction/) | 分布式事务 | Go | ⭐⭐⭐⭐⭐ |
| [matching-engine](matching-engine/) | 撮合引擎 | C++ | ⭐⭐⭐⭐⭐ |
| [query-parser](query-parser/) | 查询解析器 | Go | ⭐⭐⭐⭐ |
| [edge-computing](edge-computing/) | 边缘计算框架 | Python | ⭐⭐⭐⭐ |
| [pagerank](pagerank/) | PageRank 算法 | Python | ⭐⭐⭐ |

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
- 理解语言模型的基本概念和概率链式法则
- 掌握 N-gram 统计方法 (Unigram, Bigram, Trigram)
- 学会拉普拉斯、Good-Turing、Kneser-Ney 平滑技术
- 实现前馈神经网络、RNN、LSTM 语言模型
- 掌握困惑度和交叉熵评估
- 实现拼写纠错和输入法等应用

**核心功能**:
- N-gram 模型 (Unigram, Bigram, Trigram)
- 平滑技术 (拉普拉斯、Good-Turing、Kneser-Ney)
- 神经语言模型 (FFNN、RNN、LSTM)
- 评估指标 (困惑度、交叉熵、BLEU、WER)
- 文本生成（温度控制、多样生成）
- 拼写纠错（编辑距离 + 语言模型排序）
- 输入法（前缀补全 + 语言模型排序）

**技术栈**: Python, NumPy

**测试**: 155 个测试用例

**快速开始**:
```bash
cd projects/language-model
pip install -r requirements.txt
python3 -m pytest tests/ -v
```

---

### 📝 文本分类 (text-classification)

**项目路径**: `projects/text-classification/`

**学习目标**:
- 理解文本表示方法（词袋、TF-IDF、N-gram）
- 掌握传统分类器（朴素贝叶斯、逻辑回归、SVM）
- 学会深度学习模型（TextCNN、LSTM、BiLSTM+Attention）
- 掌握评估指标（准确率、精确率、召回率、F1、混淆矩阵）

**核心功能**:
- 特征提取: BagOfWords、TF-IDF、N-gram
- 传统分类器: 朴素贝叶斯、逻辑回归、SVM
- 深度学习: TextCNN、LSTM、BiLSTM+Attention
- 评估指标: 准确率、精确率、召回率、F1、混淆矩阵
- 实际应用: 情感分析、新闻分类、垃圾邮件检测

**技术栈**: Python, NumPy

**测试**: 185 个测试用例

**快速开始**:
```bash
cd projects/text-classification
python3 -m pytest tests/ -v
```

---

### 📝 词向量 Word2Vec (word2vec)

**项目路径**: `projects/word2vec/`

**学习目标**:
- 理解词向量原理和分布式假设
- 掌握 CBOW 和 Skip-gram 模型架构
- 学会负采样和层次 Softmax 优化技术
- 理解降采样对训练的影响

**核心功能**:
- Skip-gram 模型（给定中心词预测上下文）
- CBOW 模型（给定上下文预测中心词）
- 负采样优化（词频的 3/4 次方噪声分布）
- 层次 Softmax（Huffman 树加速）
- 降采样（高频词随机丢弃）
- 词相似度评估（Spearman 相关系数）
- 词类比（king - man + woman = queen）
- t-SNE 可视化（PCA/t-SNE 降维）
- 文本分类、情感分析、词聚类

**技术栈**: Python, NumPy

**测试**: 97 个测试用例

**快速开始**:
```bash
cd projects/word2vec
python3 -m pytest tests/ -v
python3 examples/train_example.py
```

---

### 🌲 随机森林 (random-forest)

**项目路径**: `projects/random-forest/`

**学习目标**:
- 理解 Bagging 原理
- 掌握随机特征选择
- 学会集成学习（分类与回归）
- 掌握特征重要性分析（不纯度 vs 排列）
- 理解袋外估计 (OOB)

**核心功能**:
- 决策树分类器 (Gini/Entropy)
- 随机森林分类器 (多数投票)
- 决策树回归器 (MSE)
- 随机森林回归器 (平均预测)
- 特征重要性 (不纯度 + 排列)
- 袋外估计 (OOB Score)
- 评估指标 (Accuracy, Precision, Recall, F1, MSE, R2)
- 实战示例 (鸢尾花分类, 房价预测, 特征重要性分析)

**技术栈**: Python, NumPy

**测试**: 103 个测试用例

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

### 📊 HyperLogLog 基数估计 (hyperloglog)

**项目路径**: `projects/hyperloglog/`

**学习目标**:
- 理解 HyperLogLog 原理
- 掌握概率计数
- 学会精度调优

**核心功能**:
- HyperLogLog 算法实现
- 基数估计
- 精度分析
- 合并操作

**技术栈**: Go

**快速开始**:
```bash
cd projects/hyperloglog
go run cmd/hyperloglog/main.go demo
```

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

### 🌐 PageRank 算法 (pagerank)

**项目路径**: `projects/pagerank/`

**学习目标**:
- 理解 PageRank 算法原理
- 掌握图算法和稀疏矩阵
- 学会网页排名计算

**核心功能**:
- PageRank 算法实现
- 阻尼因子配置
- 稀疏矩阵优化
- 多种求解方法（迭代法、幂迭代法、代数法）
- 可视化展示

**技术栈**: Python, SciPy

**快速开始**:
```bash
cd projects/pagerank
pip install -r requirements.txt
python examples/basic_usage.py
```

---

## 🛤️ 学习路径

### 推荐学习顺序

1. **基础算法** (1-2 周)
   - [tokenizer](tokenizer/) - 中文分词器
   - [language-model](language-model/) - N-gram 语言模型
   - [word2vec](word2vec/) - 词向量 Word2Vec
   - [text-classification](text-classification/) - 文本分类系统
   - [random-forest](random-forest/) - 随机森林

2. **进阶算法** (2-3 周)
   - [svm](svm/) - 支持向量机
   - [hyperloglog](hyperloglog/) - HyperLogLog 基数估计

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

7. **图算法** (1-2 周)
   - [pagerank](pagerank/) - PageRank 算法

---

## 📊 学习成果

完成本模块后，你将掌握：

- **NLP 基础**: 分词算法、词典管理、HMM 模型、语言模型、词向量、文本分类
- **机器学习**: 决策树、集成学习、SVM 原理、逻辑回归、朴素贝叶斯
- **深度学习**: TextCNN、LSTM、BiLSTM+Attention
- **分布式系统**: DHT、DNS、分布式事务
- **搜索引擎**: 查询解析、布尔查询、相关性排序
- **高性能计算**: 撮合引擎、订单簿管理
- **边缘计算**: 任务卸载、资源调度、负载均衡
- **图算法**: PageRank、稀疏矩阵、网页排名

---

## 🔗 相关资源

- [NLP 学习笔记](tokenizer/LEARNING_NOTES.md) - 中文分词器学习笔记
- [语言模型学习笔记](language-model/LEARNING_NOTES.md) - N-gram 语言模型学习笔记
- [词向量学习笔记](word2vec/LEARNING_NOTES.md) - Word2Vec 学习笔记
- [文本分类学习笔记](text-classification/LEARNING_NOTES.md) - 文本分类系统学习笔记
- [机器学习笔记](random-forest/LEARNING_NOTES.md) - 随机森林学习笔记
- [SVM 学习笔记](svm/LEARNING_NOTES.md) - SVM 学习笔记
- [查询解析器学习笔记](query-parser/LEARNING_NOTES.md) - 查询解析器学习笔记
- [边缘计算学习笔记](edge-computing/LEARNING_NOTES.md) - 边缘计算学习笔记
- [PageRank 学习笔记](pagerank/LEARNING_NOTES.md) - PageRank 算法学习笔记

---

## 📈 项目统计

| 维度 | 数量 |
|------|------|
| **总项目数** | 12 |
| **技术栈** | 3 (Python, Go, C++) |
| **总代码行数** | 18,000+ |
| **文档数量** | 50+ |

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
